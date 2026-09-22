#!/usr/bin/env python3
"""Validate tensor depth against a pileup-derived real-read oracle.

The oracle deliberately uses pysam's pileup traversal rather than
``AlignedSegment.get_aligned_pairs``, which is used by tensorization. Windows
are deterministic and independent of truth labels. This is a representation
diagnostic, not a performance benchmark.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pysam

from alignssl.tensorize import Q_DEPTH, build_tensor


def eligible_alignment(read):
    """Mirror the tensorizer's whole-read eligibility policy."""
    return not (read.is_unmapped or read.is_secondary or read.is_supplementary)


def pileup_base_depth(columns, start, span):
    """Count aligned query bases at each reference base from pileup columns."""
    depth = np.zeros(span, dtype=np.float32)
    end = start + span
    for column in columns:
        pos = int(column.reference_pos)
        if pos < start or pos >= end:
            continue
        count = 0
        for item in column.pileups:
            read = item.alignment
            if (not eligible_alignment(read) or read.query_sequence is None
                    or item.query_position is None):
                continue
            count += 1
        depth[pos - start] = count
    return depth


def oracle_binned_depth(bam, chrom, start, width, bin_size, depth_norm):
    span = width * bin_size
    columns = bam.pileup(
        chrom, start, start + span, truncate=True, stepper="nofilter",
        min_base_quality=0, max_depth=1_000_000, ignore_overlaps=False,
    )
    per_base = pileup_base_depth(columns, start, span)
    binned = per_base.reshape(width, bin_size).sum(axis=1)
    return np.clip(binned / (depth_norm * bin_size), 0.0, 1.0)


def parse_regions(values):
    regions = []
    for value in values:
        chrom, interval = value.split(":")
        start, end = map(int, interval.split("-"))
        if start < 0 or end <= start:
            raise ValueError(f"Invalid region: {value}")
        regions.append((chrom, start, end))
    return regions


def deterministic_starts(region_start, region_end, span, n):
    if span > region_end - region_start:
        raise ValueError("Tensor span exceeds validation region")
    if n < 1:
        raise ValueError("windows-per-bin must be positive")
    maximum = region_end - span
    if n == 1:
        return [(region_start + maximum) // 2]
    return np.linspace(region_start, maximum, n, dtype=np.int64).tolist()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bam", required=True)
    parser.add_argument("--fasta", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--regions", nargs="+", default=[
        "1:10000000-11000000", "10:10000000-11000000",
        "20:10000000-11000000",
    ])
    parser.add_argument("--bin-sizes", default="1,2,4,8,16,32,64")
    parser.add_argument("--width", type=int, default=256)
    parser.add_argument("--windows-per-bin", type=int, default=3)
    parser.add_argument("--depth-norm", type=float, default=60.0)
    parser.add_argument("--atol", type=float, default=1e-7)
    args = parser.parse_args()

    regions = parse_regions(args.regions)
    bin_sizes = [int(x) for x in args.bin_sizes.split(",")]
    if any(x < 1 for x in bin_sizes):
        raise ValueError("bin sizes must be positive")

    records = []
    with pysam.AlignmentFile(args.bam, "rb") as bam, pysam.FastaFile(args.fasta) as fasta:
        for chrom, region_start, region_end in regions:
            if chrom not in bam.references or chrom not in fasta.references:
                raise ValueError(f"Missing contig {chrom} in BAM or reference")
            for bin_size in bin_sizes:
                span = args.width * bin_size
                for start in deterministic_starts(
                        region_start, region_end, span, args.windows_per_bin):
                    end = start + span
                    reads = list(bam.fetch(chrom, start, end))
                    reference = fasta.fetch(chrom, start, end)
                    corrected = build_tensor(
                        reads, reference, start, args.width,
                        depth_norm=args.depth_norm, bin_size=bin_size,
                        depth_mode="mean_base_coverage",
                    )[Q_DEPTH, 0]
                    legacy = build_tensor(
                        reads, reference, start, args.width,
                        depth_norm=args.depth_norm, bin_size=bin_size,
                        depth_mode="legacy",
                    )[Q_DEPTH, 0]
                    oracle = oracle_binned_depth(
                        bam, chrom, start, args.width, bin_size, args.depth_norm)
                    corrected_error = np.abs(corrected - oracle)
                    legacy_error = np.abs(legacy - oracle)
                    records.append({
                        "chrom": chrom,
                        "start": int(start),
                        "end": int(end),
                        "bin_size": int(bin_size),
                        "n_overlapping_records": len(reads),
                        "corrected_max_abs_error": float(corrected_error.max()),
                        "corrected_mean_abs_error": float(corrected_error.mean()),
                        "corrected_mismatched_columns": int(
                            np.count_nonzero(corrected_error > args.atol)),
                        "legacy_mean_abs_error": float(legacy_error.mean()),
                    })

    summary = {
        "purpose": "real_read_representation_diagnostic",
        "bam": str(Path(args.bam)),
        "fasta": str(Path(args.fasta)),
        "regions_0based_halfopen": regions,
        "width": args.width,
        "bin_sizes": bin_sizes,
        "windows_per_bin": args.windows_per_bin,
        "depth_norm": args.depth_norm,
        "atol": args.atol,
        "n_windows": len(records),
        "corrected_max_abs_error": max(
            x["corrected_max_abs_error"] for x in records),
        "corrected_mismatched_columns": sum(
            x["corrected_mismatched_columns"] for x in records),
        "legacy_mean_abs_error": float(np.mean([
            x["legacy_mean_abs_error"] for x in records])),
        "records": records,
    }
    summary["passed"] = summary["corrected_mismatched_columns"] == 0
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(summary, indent=2) + "\n")
    temporary.replace(output)
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2))
    if not summary["passed"]:
        raise SystemExit("Corrected depth differs from pileup oracle")


if __name__ == "__main__":
    main()
