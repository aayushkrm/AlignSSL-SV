#!/usr/bin/env python3
"""Compare BND-only, site-only copies of a pinned public VCF with Truvari."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

import pysam
import truvari

from analysis.colo829_contig_alias_diagnostic import EXPECTED, normalized_copy
from analysis.verify_colo829_case_diff import inspect


def sha(data):
    return hashlib.sha256(data).hexdigest()


def site_only_bnds(content):
    out = []
    count = 0
    for line in content.splitlines():
        if line.startswith(b"##"):
            out.append(line + b"\n")
        elif line.startswith(b"#CHROM\t"):
            out.append(b"\t".join(line.split(b"\t")[:8]) + b"\n")
        elif not line.startswith(b"#"):
            fields = line.split(b"\t")
            if len(fields) < 8:
                raise ValueError("malformed source record")
            if b"SVTYPE=BND" in fields[7].split(b";"):
                out.append(b"\t".join(fields[:8]) + b"\n")
                count += 1
    return b"".join(out), count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-gzip", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if importlib.metadata.version("truvari") != "5.4.0":
        raise ValueError("This diagnostic requires Truvari 5.4.0")
    compressed = args.source_gzip.read_bytes()
    if sha(compressed) != EXPECTED:
        raise ValueError("public source hash differs")
    source = gzip.decompress(compressed)
    adjusted, counts, changes = normalized_copy(source)
    originals = {"original": site_only_bnds(source), "normalized": site_only_bnds(adjusted)}
    if any(n != 66 for _, n in originals.values()):
        raise ValueError("unexpected BND count; refusing to run")
    out, workspace = args.output.resolve(), args.workspace.resolve()
    out.mkdir(parents=True, exist_ok=False)
    workspace.mkdir(parents=True, exist_ok=False)
    for name, (contents, _) in originals.items():
        plain = workspace / f"{name}.vcf"
        plain.write_bytes(contents)
        bgzf = workspace / f"{name}.vcf.gz"
        pysam.tabix_compress(str(plain), str(bgzf), force=False)
        pysam.tabix_index(str(bgzf), preset="vcf", force=False)
    diff = inspect(workspace / "original.vcf", workspace / "normalized.vcf")
    if diff["changed_lines"] != 66:
        raise ValueError("unexpected non-case changes; refusing to run")
    manifest = {"source_url": "https://ont-open-data.s3.amazonaws.com/colo829_2024.03/wf_somatic_variation/sup/COLO829.wf-somatic-sv.vcf.gz",
                "source_gzip_sha256": sha(compressed), "source_counts": counts,
                "site_only_projection": "all BND records and FILTER values; retain first eight columns, remove samples",
                "normalized_scope": "ALT mate-contig case only; INFO/ANN remains unchanged",
                "original_case_changes": changes, "independent_byte_diff": diff,
                "workspace_files_sha256": {p.name: sha(p.read_bytes()) for p in sorted(workspace.iterdir()) if p.is_file()}}
    (out / "input-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    cases = [("original_self", "original", "original"), ("normalized_self", "normalized", "normalized"),
             ("original_to_normalized", "original", "normalized"),
             ("normalized_to_original", "normalized", "original")]
    flags = ["--bnddist", "1", "--refdist", "1", "--sizemin", "0", "--sizefilt", "0", "--pctseq", "0"]

    def execute(case):
        name, base, comp = case
        cmd = [sys.executable, "-m", "truvari", "bench", "--base", str(workspace / f"{base}.vcf.gz"),
               "--comp", str(workspace / f"{comp}.vcf.gz"), "--output", str(out / name)] + flags
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
        result = subprocess.run(cmd, text=True, capture_output=True, env=env)
        (out / f"{name}.stdout.txt").write_text(result.stdout)
        (out / f"{name}.stderr.txt").write_text(result.stderr)
        report = out / name / "summary.json"
        return {"case": name, "argv": cmd, "exit_code": result.returncode,
                "summary": json.loads(report.read_text()) if report.exists() else None}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(execute, cases))
    (out / "comparison.json").write_text(json.dumps(results, indent=2) + "\n")
    package = Path(truvari.__file__).parent
    receipt = {"python": sys.version, "truvari": importlib.metadata.version("truvari"),
               "pysam": pysam.__version__,
               "dependencies": sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()),
               "script_sha256": sha(Path(__file__).resolve().read_bytes()),
               "source_sha256": {n: sha((package / n).read_bytes()) for n in ["variant_record.py", "matching.py", "bench.py"]},
               "cases": results,
               "files_sha256": {str(p.relative_to(out)): sha(p.read_bytes()) for p in sorted(out.rglob("*")) if p.is_file()}}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps([{k: r[k] for k in ("case", "exit_code", "summary")} for r in results], indent=2))
    if any(r["exit_code"] != 0 or r["summary"] is None for r in results):
        raise SystemExit("one or more native commands failed; full output retained")


if __name__ == "__main__":
    main()
