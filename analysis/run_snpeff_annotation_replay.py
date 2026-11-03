#!/usr/bin/env python3
"""Run two native SnpEff annotation builds on the same tiny synthetic genome."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


EXPECTED = {
    "5.1d": "802383117ce2b414d44b98d9ee385209ca4d164b58b640183f46e843e47ce42f",
    "5.4c": "5e8f75cbf908a33c6fb2e65c81e66fe31236cb21bb0195541c4703d8202c22b3",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path):
    result = {}
    for line in path.read_text().splitlines():
        if not line.startswith("#"):
            f = line.split("\t")
            if len(f) < 8 or f[2] in result:
                raise ValueError("invalid or duplicate VCF record")
            result[f[2]] = {"chrom": f[0], "pos": f[1], "ref": f[3], "alt": f[4]}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar-51d", type=Path, required=True)
    parser.add_argument("--jar-54c", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    jars = {"5.1d": args.jar_51d.resolve(), "5.4c": args.jar_54c.resolve()}
    for name, jar in jars.items():
        if sha(jar) != EXPECTED[name]:
            raise ValueError(f"{name} JAR SHA256 does not match the pinned package")
    out, workspace = args.output.resolve(), args.workspace.resolve()
    out.mkdir(parents=True, exist_ok=False)
    workspace.mkdir(parents=True, exist_ok=False)
    ref = out / "synthetic.fa"
    ref.write_text(">chrA\n" + "A" * 100 + "\n>chrB\n" + "C" * 100 + "\n")
    gff = out / "synthetic.gff3"
    lines = ["##gff-version 3"]
    for chrom, name in [("chrA", "A"), ("chrB", "B")]:
        lines += [f"{chrom}\tsynthetic\tgene\t1\t90\t.\t+\t.\tID=gene{name};Name=gene{name}",
                  f"{chrom}\tsynthetic\tmRNA\t1\t90\t.\t+\t.\tID=tx{name};Parent=gene{name}",
                  f"{chrom}\tsynthetic\texon\t1\t90\t.\t+\t.\tID=exon{name};Parent=tx{name}",
                  f"{chrom}\tsynthetic\tCDS\t1\t90\t.\t+\t0\tID=cds{name};Parent=tx{name}"]
    gff.write_text("\n".join(lines) + "\n")
    vcf = out / "input.vcf"
    vcf.write_text("\n".join([
        "##fileformat=VCFv4.3", "##contig=<ID=chrA,length=100>",
        "##contig=<ID=chrB,length=100>",
        '##INFO=<ID=SVTYPE,Number=1,Type=String,Description="SV type">',
        '##INFO=<ID=MATEID,Number=.,Type=String,Description="Mate ID">',
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO",
        "chrA\t10\ta\tA\tA[chrB:20[\t.\tPASS\tSVTYPE=BND;MATEID=b",
        "chrA\t11\tsnv\tA\tG\t.\tPASS\t.",
        "chrB\t20\tb\tC\t]chrA:10]C\t.\tPASS\tSVTYPE=BND;MATEID=a", ""]))
    initial = records(vcf)

    def run_version(item):
        name, jar = item
        local = workspace / name
        data = local / "data" / "synthetic"
        data.mkdir(parents=True)
        shutil.copyfile(ref, data / "sequences.fa")
        shutil.copyfile(gff, data / "genes.gff")
        config = local / "snpEff.config"
        config.write_text(f"data.dir = {local / 'data'}\nsynthetic.genome : synthetic\n")
        commands = {
            "version": ["java", "-jar", str(jar), "-version"],
            "build": ["java", "-Xmx512m", "-jar", str(jar), "build", "-gff3", "-noCheckCds",
                      "-noCheckProtein", "-nodownload", "-noLog", "-c", str(config), "synthetic"],
            "annotate": ["java", "-Xmx512m", "-jar", str(jar), "-noStats", "-nodownload",
                         "-noLog", "-c", str(config), "synthetic", str(vcf)],
        }
        steps = {}
        for step in ("version", "build", "annotate"):
            if step == "annotate" and steps["build"]["exit_code"] != 0:
                steps[step] = {"argv": commands[step], "exit_code": None, "skipped": "build failed"}
                continue
            result = subprocess.run(commands[step], text=True, capture_output=True, cwd=local)
            stdout_name = f"{name}.{step}.vcf" if step == "annotate" else f"{name}.{step}.stdout.txt"
            (out / stdout_name).write_text(result.stdout)
            (out / f"{name}.{step}.stderr.txt").write_text(result.stderr)
            steps[step] = {"argv": commands[step], "exit_code": result.returncode}
        observed = None
        if steps["annotate"]["exit_code"] == 0:
            try:
                final = records(out / f"{name}.annotate.vcf")
                observed = {"input": initial, "output": final,
                            "same_record_ids": set(initial) == set(final)}
            except (IndexError, ValueError) as exc:
                observed = {"parse_error": str(exc)}
        return {"jar": str(jar), "jar_sha256": sha(jar), "steps": steps, "records": observed}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = dict(zip(jars, pool.map(run_version, jars.items())))
    (out / "comparison.json").write_text(json.dumps(results, indent=2) + "\n")
    receipt = {"python": sys.version, "script_sha256": sha(Path(__file__).resolve()),
               "results": results,
               "files_sha256": {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob("*")) if p.is_file()}}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({name: {"steps": {k: v["exit_code"] for k, v in result["steps"].items()},
                             "records": result["records"]} for name, result in results.items()}, indent=2))
    if any(r["steps"]["build"]["exit_code"] != 0 or r["steps"]["annotate"]["exit_code"] != 0
           for r in results.values()):
        raise SystemExit("one or more native commands failed; full output retained")


if __name__ == "__main__":
    main()
