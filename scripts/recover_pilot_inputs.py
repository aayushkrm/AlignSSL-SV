#!/usr/bin/env python3
"""Recover public GIAB inputs and a coordinate-selected BAM slice.

This is an infrastructure diagnostic, never a confirmatory benchmark. Coordinates
are selected before truth labels are read. Run on a compute node. Existing final
outputs are refused to avoid silently mixing attempts; use a fresh run directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import time
import urllib.request

import pysam

GIAB = "https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab"
BAM_BASE = (GIAB + "/data/AshkenazimTrio/HG002_NA24385_son/"
            "NIST_HiSeq_HG002_Homogeneity-10953946/"
            "NHGRI_Illumina300X_AJtrio_novoalign_bams")
BAM_URL = BAM_BASE + "/HG002.hs37d5.60x.1.bam"
TRUTH_BASE = GIAB + "/release/AshkenazimTrio/HG002_NA24385_son/NIST_SV_v0.6"
REF_URL = ("https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/"
           "phase2_reference_assembly_sequence/hs37d5.fa.gz")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url, path):
    if path.exists() or path.with_suffix(path.suffix + ".part").exists():
        raise FileExistsError(f"Refusing to overwrite {path}; use a fresh run")
    temporary = path.with_suffix(path.suffix + ".part")
    print(f"Downloading {url}", flush=True)
    with urllib.request.urlopen(url, timeout=90) as response, temporary.open("xb") as out:
        expected = response.headers.get("Content-Length")
        while chunk := response.read(4 * 1024 * 1024):
            out.write(chunk)
    if expected is not None and temporary.stat().st_size != int(expected):
        raise IOError(f"Incomplete download: {url}")
    temporary.rename(path)
    return {"url": url, "file": path.name, "bytes": path.stat().st_size,
            "sha256": digest(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--regions", nargs="+", default=[
        "1:10000000-11000000", "10:10000000-11000000", "20:10000000-11000000"],
        help="0-based half-open intervals, selected independently of labels")
    parser.add_argument("--reference", action="store_true",
                        help="also download full 851-MiB compressed hs37d5 reference")
    args = parser.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise FileExistsError("Output directory must be empty; interrupted runs remain inspectable")
    regions = []
    for region in args.regions:
        chrom, interval = region.split(":")
        start, end = map(int, interval.split("-"))
        if start < 0 or end <= start:
            raise ValueError(f"Invalid interval: {region}")
        if chrom in {r[0] for r in regions}:
            raise ValueError("This pilot supports one interval per chromosome to avoid duplicate reads")
        regions.append((chrom, start, end))
    manifest = {"status": "started", "purpose": "development_infrastructure_only",
                "sample": "HG002", "assembly": "hs37d5", "regions_0based_halfopen": regions,
                "source_bam": BAM_URL, "pysam": pysam.__version__,
                "python": platform.python_version(), "started_unix": time.time(), "files": []}
    manifest_path = out / "manifest.json"

    def save():
        temporary = out / "manifest.json.tmp"
        temporary.write_text(json.dumps(manifest, indent=2) + "\n")
        temporary.replace(manifest_path)

    save()
    try:
        bai = out / "HG002.hs37d5.60x.1.bam.bai"
        manifest["files"].append(fetch(BAM_URL + ".bai", bai))
        for name in ["HG002_SVs_Tier1_v0.6.vcf.gz", "HG002_SVs_Tier1_v0.6.vcf.gz.tbi",
                     "HG002_SVs_Tier1_v0.6.bed", "README_SV_v0.6.txt"]:
            manifest["files"].append(fetch(TRUTH_BASE + "/" + name, out / name))
            save()
        bam_path = out / "HG002.pilot.bam"
        count = 0
        with pysam.AlignmentFile(BAM_URL, "rb", index_filename=str(bai)) as source:
            ordered = sorted(regions, key=lambda r: (source.get_tid(r[0]), r[1]))
            for i, (chrom, start, end) in enumerate(ordered):
                if source.get_tid(chrom) < 0 or end > source.get_reference_length(chrom):
                    raise ValueError(f"Region outside reference: {chrom}:{start}-{end}")
                if i and chrom == ordered[i-1][0] and start < ordered[i-1][2]:
                    raise ValueError("Overlapping intervals would duplicate reads")
            partial = out / "HG002.pilot.partial.bam"
            with pysam.AlignmentFile(str(partial), "wb", template=source) as target:
                for chrom, start, end in ordered:
                    before = count
                    for read in source.fetch(chrom, start, end):
                        target.write(read)
                        count += 1
                    print(f"{chrom}:{start}-{end}: {count-before} reads", flush=True)
            if count == 0:
                raise ValueError("No reads retrieved")
            pysam.quickcheck(str(partial))
            # One interval per chromosome prevents duplicate retrieval of long reads.
            pysam.sort("-@", "2", "-o", str(bam_path), str(partial))
            pysam.index(str(bam_path))
            manifest["bam_header"] = source.header.to_dict()
        for path in [bam_path, Path(str(bam_path) + ".bai")]:
            manifest["files"].append({"file": path.name, "bytes": path.stat().st_size,
                                      "sha256": digest(path)})
        manifest["n_reads"] = count
        save()
        if args.reference:
            for suffix in ["", ".fai", ".gzi"]:
                manifest["files"].append(fetch(REF_URL + suffix, out / ("hs37d5.fa.gz" + suffix)))
                save()
            with pysam.FastaFile(str(out / "hs37d5.fa.gz")) as reference:
                for chrom, start, end in regions:
                    if len(reference.fetch(chrom, start, min(start+100, end))) != min(100, end-start):
                        raise ValueError("Reference indexing sanity check failed")
        manifest["status"] = "complete"
        manifest["completed_unix"] = time.time()
        save()
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        save()
        raise


if __name__ == "__main__":
    main()
