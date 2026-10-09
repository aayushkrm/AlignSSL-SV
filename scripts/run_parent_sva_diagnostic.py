"""One immutable regional parent diagnostic. Preserve partial outputs on error."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def acceptance_fields(filters, genotypes):
    return {"native_filter_pass": list(filters) == ["PASS"],
            "has_nonreference_gt": any(any(a is not None and a > 0
                for a in (fields.get("GT") or ())) for fields in genotypes.values())}


def native_records(path):
    import pysam
    result = []
    with pysam.VariantFile(str(path)) as vcf:
        samples = list(vcf.header.samples)
        for record in vcf:
            info = dict(record.info)
            length = info.get("SVLEN")
            if isinstance(length, tuple):
                length = length[0] if len(length) == 1 else None
            genotypes = {s: dict(record.samples[s]) for s in samples}
            alt = record.alts or ()
            result.append({"chrom": record.chrom, "pos1": record.pos,
                "id": record.id, "qual": record.qual, "filter": list(record.filter),
                "info": info, "samples": genotypes,
                "alt_lengths": [len(a) for a in alt],
                "alt_sha256": [hashlib.sha256(a.encode()).hexdigest() for a in alt],
                "explicit_sequence_alt": [not a.startswith("<") for a in alt],
                "compatible_by_location_length": record.chrom == "chr3"
                    and abs(record.pos - 1 - 71589909) <= 500
                    and info.get("SVTYPE") == "INS" and length is not None
                    and 2726 <= abs(length) <= 4088,
                **acceptance_fields(record.filter, genotypes)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samtools", required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    sniffles = Path(sys.executable).parent / "sniffles"
    start = time.time()
    manifest = {"started_unix": start, "state": "started", "commands": {},
                "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                "limits": {"genomic_http_body_bytes": 4 * 1024**3,
                           "cpu_seconds": 1800}, "source_code": {}}
    for p in (Path(__file__), root / "scripts/acquire_parent_sva_region.py",
              root / "analysis/parent_sva_census.py"):
        manifest["source_code"][str(p.relative_to(root))] = sha(p)

    def save():
        (args.output / "run.json").write_text(json.dumps(manifest, indent=2) + "\n")

    def command(name, argv):
        then = time.time()
        with (args.output / f"{name}.stdout.txt").open("xb") as out, (args.output / f"{name}.stderr.txt").open("xb") as err:
            rc = subprocess.run([str(a) for a in argv], stdout=out, stderr=err, timeout=540).returncode
        return {"argv": [str(a) for a in argv], "exit_code": rc, "wall_seconds": time.time() - then}

    save()
    try:
        manifest["runtime"] = {
            "python": sys.version,
            "freeze": subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True).splitlines(),
            "sniffles_version": subprocess.check_output([str(sniffles), "--version"], text=True).strip()}
        acq = command("acquire", [sys.executable, root / "scripts/acquire_parent_sva_region.py",
            "--samtools", args.samtools, "--output", args.output / "source"])
        manifest["commands"]["acquire"] = acq
        save()
        if acq["exit_code"]:
            raise RuntimeError("Acquisition incomplete; native calls not run")
        bam = args.output / "source/regional.bam"
        if not bam.is_file() or not Path(str(bam) + ".bai").is_file():
            raise RuntimeError("Missing regional BAM/index")
        core = args.output / "core.bed"
        core.write_text("chr3\t71579909\t71603317\n")
        base = [sniffles, "--input", bam, "--regions", core, "--threads", "1", "--output-rnames"]
        commands = {
            "germline": [*base, "--vcf", args.output / "parent.germline.vcf"],
            "mosaic": [*base, "--vcf", args.output / "parent.mosaic.vcf", "--mosaic"],
            "census": [sys.executable, root / "analysis/parent_sva_census.py",
                       "--bam", bam, "--output", args.output / "census"]}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {name: pool.submit(command, name, argv) for name, argv in commands.items()}
            for name, future in futures.items():
                manifest["commands"][name] = future.result()
                save()
        if any(manifest["commands"][name]["exit_code"] for name in commands):
            raise RuntimeError("One or more diagnostic commands failed")
        manifest["native_records"] = {mode: native_records(args.output / f"parent.{mode}.vcf")
                                      for mode in ("germline", "mosaic")}
        manifest["census"] = json.loads((args.output / "census/census.json").read_text())
        manifest["state"] = "completed_regional_diagnostic"
        manifest["claim_scope"] = "Compatible parental evidence, not exact child truth, prevalence or novelty"
        manifest["acceptance_distinction"] = "FILTER PASS, allele evidence and GT are separate. Germline reference-only GT is not nonreference success; intended mosaic visibility does not require invented diploid heterozygosity."
    except Exception as error:
        manifest["state"] = "incomplete"
        manifest["error"] = f"{type(error).__name__}: {error}"
    finally:
        manifest["artifacts"] = {str(p.relative_to(args.output)): {"bytes": p.stat().st_size,
                                 "sha256": sha(p)} for p in args.output.rglob("*")
                                 if p.is_file() and p.name != "run.json"}
        own = resource.getrusage(resource.RUSAGE_SELF)
        child = resource.getrusage(resource.RUSAGE_CHILDREN)
        manifest["cpu_seconds"] = own.ru_utime + own.ru_stime + child.ru_utime + child.ru_stime
        manifest["wall_seconds"] = time.time() - start
        save()
    print(json.dumps({"state": manifest["state"], "error": manifest.get("error"),
                      "cpu_seconds": manifest["cpu_seconds"], "wall_seconds": manifest["wall_seconds"]}))
    return 0 if manifest["state"] == "completed_regional_diagnostic" else 1


if __name__ == "__main__":
    sys.exit(main())
