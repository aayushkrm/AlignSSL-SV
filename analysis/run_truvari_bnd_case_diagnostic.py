#!/usr/bin/env python3
"""Compare two artificial BND VCFs that differ only in remote contig case."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

import pysam
import truvari


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if importlib.metadata.version("truvari") != "5.4.0":
        raise ValueError("This diagnostic requires Truvari 5.4.0")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    header = "\n".join([
        "##fileformat=VCFv4.3", "##contig=<ID=chrA,length=100>", "##contig=<ID=chrB,length=100>",
        '##INFO=<ID=SVTYPE,Number=1,Type=String,Description="SV type">',
        '##INFO=<ID=MATEID,Number=.,Type=String,Description="Mate ID">',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTHETIC", ""])
    rows = [
        ["chrA", "10", "a", "A", "A[chrB:20[", ".", "PASS", "SVTYPE=BND;MATEID=b", "GT", "0/1"],
        ["chrB", "20", "b", "C", "]chrA:10]C", ".", "PASS", "SVTYPE=BND;MATEID=a", "GT", "0/1"],
    ]
    for name, upper in [("header_case", False), ("upper_case", True)]:
        adjusted = [row.copy() for row in rows]
        if upper:
            adjusted[0][4] = adjusted[0][4].replace("chrB", "CHRB")
            adjusted[1][4] = adjusted[1][4].replace("chrA", "CHRA")
        plain = out / f"{name}.vcf"
        plain.write_text(header + "".join("\t".join(row) + "\n" for row in adjusted))
        bgzf = out / f"{name}.vcf.gz"
        pysam.tabix_compress(str(plain), str(bgzf), force=False)
        pysam.tabix_index(str(bgzf), preset="vcf", force=False)
    cases = [("header_self", "header_case", "header_case"),
             ("upper_self", "upper_case", "upper_case"),
             ("header_to_upper", "header_case", "upper_case"),
             ("upper_to_header", "upper_case", "header_case")]
    flags = ["--bnddist", "1", "--refdist", "1", "--sizemin", "0", "--sizefilt", "0",
             "--pctseq", "0", "--passonly"]

    def execute(case):
        name, base, comp = case
        command = [sys.executable, "-m", "truvari", "bench", "--base", str(out / f"{base}.vcf.gz"),
                   "--comp", str(out / f"{comp}.vcf.gz"), "--output", str(out / name)] + flags
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
        result = subprocess.run(command, text=True, capture_output=True, env=env)
        (out / f"{name}.stdout.txt").write_text(result.stdout)
        (out / f"{name}.stderr.txt").write_text(result.stderr)
        report = out / name / "summary.json"
        return {"case": name, "argv": command, "exit_code": result.returncode,
                "summary": json.loads(report.read_text()) if report.exists() else None}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(execute, cases))
    (out / "comparison.json").write_text(json.dumps(results, indent=2) + "\n")
    source = Path(truvari.__file__).parent
    metadata = {"python": sys.version, "truvari": importlib.metadata.version("truvari"),
                "pysam": pysam.__version__,
                "dependencies": sorted(f"{d.metadata['Name']}=={d.version}"
                                       for d in importlib.metadata.distributions()),
                "script_sha256": sha(Path(__file__).resolve()),
                "source_sha256": {name: sha(source / name) for name in ["variant_record.py", "matching.py", "bench.py"]},
                "cases": results,
                "files_sha256": {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob("*")) if p.is_file()}}
    (out / "receipt.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps([{k: r[k] for k in ("case", "exit_code", "summary")} for r in results], indent=2))
    if any(r["exit_code"] != 0 or r["summary"] is None for r in results):
        raise SystemExit("one or more native comparisons failed; outputs retained")


if __name__ == "__main__":
    main()
