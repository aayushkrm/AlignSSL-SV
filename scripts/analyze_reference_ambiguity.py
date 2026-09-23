"""Quantify HGSVC/IGSR non-ACGT territory against the unequal-base map.

The joint BED is reference-ambiguity territory, not a donor-callability mask.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
from collections import defaultdict
from pathlib import Path

if __package__:
    from .verify_reference_difference_map import verify as verify_differences
else:
    from verify_reference_difference_map import verify as verify_differences


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_mask(bed_path: Path, json_path: Path, selected: set[str]) -> tuple[dict, dict]:
    meta = json.loads(json_path.read_text())
    if file_sha256(bed_path) != meta["bed_sha256"]:
        raise ValueError(f"{bed_path}: SHA-256 differs from JSON")
    intervals = defaultdict(list)
    counts = defaultdict(lambda: [0, 0])
    last_end = {}
    with bed_path.open() as bed:
        for line in bed:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 3:
                raise ValueError(f"{bed_path}: malformed BED3 row")
            name, start_str, end_str = fields
            start, end = int(start_str), int(end_str)
            if name not in meta["contigs"] or not (0 <= start < end <= meta["contigs"][name]["length"]):
                raise ValueError(f"{bed_path}: invalid contig or coordinates")
            if start <= last_end.get(name, -1):
                raise ValueError(f"{bed_path}: unsorted or unmerged intervals")
            last_end[name] = end
            counts[name][0] += end - start
            counts[name][1] += 1
            if name in selected:
                intervals[name].append((start, end))
    for name, record in meta["contigs"].items():
        if counts[name] != [record["n_ambiguous_bases"], record["n_ambiguous_intervals"]]:
            raise ValueError(f"{bed_path}: {name} BED and JSON counts differ")
    if sum(value[0] for value in counts.values()) != meta["n_ambiguous_bases"]:
        raise ValueError(f"{bed_path}: global ambiguous-base count differs")
    if sum(value[1] for value in counts.values()) != meta["n_ambiguous_intervals"]:
        raise ValueError(f"{bed_path}: global interval count differs")
    return meta, intervals


def union_intervals(left: list[tuple[int, int]], right: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged = []
    for start, end in heapq.merge(left, right):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def interval_length(intervals: list[tuple[int, int]]) -> int:
    return sum(end - start for start, end in intervals)


def intersection_length(left: list[tuple[int, int]], right: list[tuple[int, int]]) -> int:
    result = i = j = 0
    while i < len(left) and j < len(right):
        a_start, a_end = left[i]
        b_start, b_end = right[j]
        result += max(0, min(a_end, b_end) - max(a_start, b_start))
        if a_end <= b_end:
            i += 1
        else:
            j += 1
    return result


def analyze(hgsvc_bed: Path, hgsvc_json: Path, igsr_bed: Path, igsr_json: Path,
            m5_audit: Path, differences: Path, out_bed: Path) -> dict:
    audit = json.loads(m5_audit.read_text())["contigs"]
    selected = set(audit)
    h_meta, h_intervals = read_mask(hgsvc_bed, hgsvc_json, selected)
    i_meta, i_intervals = read_mask(igsr_bed, igsr_json, selected)
    if set(h_meta["contigs"]) != selected or not selected <= set(i_meta["contigs"]):
        raise ValueError("Shared contigs do not match the 194-contig M5 audit")
    verify_differences(differences)
    summary = {}
    digest = hashlib.sha256()
    total_union = total_shared = total_mismatch_outside = total_length = 0
    total_intervals = 0
    out_bed.parent.mkdir(parents=True, exist_ok=True)
    with out_bed.open("w", encoding="ascii", newline="\n") as bed:
        for name in sorted(selected):
            audit_record = audit[name]
            h_record = h_meta["contigs"][name]
            i_record = i_meta["contigs"][name]
            if (h_record["length"], h_record["canonical_m5"]) != (
                audit_record["length"], audit_record["canonical_m5"]
            ) or (i_record["length"], i_record["canonical_m5"]) != (
                audit_record["dict_length"], audit_record["dict_m5"]
            ):
                raise ValueError(f"{name}: FASTA M5 does not match prior reference audit")
            left, right = h_intervals[name], i_intervals[name]
            union = union_intervals(left, right)
            joint = interval_length(union)
            shared = interval_length(left) + interval_length(right) - joint
            mismatch_path = differences / f"{name}_base_differences.bed"
            mismatch = []
            if mismatch_path.exists():
                for line in mismatch_path.read_text().splitlines():
                    row_name, start, end = line.split("\t")
                    if row_name != name:
                        raise ValueError(f"{mismatch_path}: unexpected contig")
                    mismatch.append((int(start), int(end)))
            mismatch_bases = interval_length(mismatch)
            outside = mismatch_bases - intersection_length(mismatch, union)
            for start, end in union:
                row = f"{name}\t{start}\t{end}\n"
                bed.write(row)
                digest.update(row.encode("ascii"))
            summary[name] = {
                "length": h_record["length"],
                "hgsvc_non_acgt_bases": interval_length(left),
                "igsr_non_acgt_bases": interval_length(right),
                "joint_non_acgt_bases": joint,
                "shared_non_acgt_bases": shared,
                "n_joint_intervals": len(union),
                "unequal_bases": mismatch_bases,
                "unequal_bases_outside_joint_non_acgt": outside,
            }
            total_union += joint
            total_shared += shared
            total_mismatch_outside += outside
            total_length += h_record["length"]
            total_intervals += len(union)
    return {
        "interpretation": "Reference non-ACGT territory only; not donor callability or a safe SV exclusion mask",
        "n_shared_contigs": len(selected), "n_shared_bases": total_length,
        "n_joint_non_acgt_bases": total_union,
        "n_shared_non_acgt_bases": total_shared,
        "n_joint_intervals": total_intervals,
        "n_unequal_bases_outside_joint_non_acgt": total_mismatch_outside,
        "joint_bed_sha256": digest.hexdigest(),
        "hgsvc_fasta_sha256": h_meta["fasta_sha256"],
        "igsr_fasta_sha256": i_meta["fasta_sha256"],
        "contigs": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hgsvc-bed", type=Path, required=True)
    parser.add_argument("--hgsvc-json", type=Path, required=True)
    parser.add_argument("--igsr-bed", type=Path, required=True)
    parser.add_argument("--igsr-json", type=Path, required=True)
    parser.add_argument("--m5-audit", type=Path, required=True)
    parser.add_argument("--differences", type=Path, required=True)
    parser.add_argument("--out-bed", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args()
    if args.out_bed.resolve() == args.out_json.resolve():
        parser.error("--out-bed and --out-json must differ")
    result = analyze(args.hgsvc_bed, args.hgsvc_json, args.igsr_bed, args.igsr_json,
                     args.m5_audit, args.differences, args.out_bed)
    args.out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"{result['n_joint_non_acgt_bases']} bases in "
          f"{result['n_joint_intervals']} joint non-ACGT intervals; "
          f"{result['n_shared_non_acgt_bases']} shared non-ACGT bases")


if __name__ == "__main__":
    main()
