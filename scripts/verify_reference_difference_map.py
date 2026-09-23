"""Verify the complete HGSVC-versus-IGSR reference-difference map bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CONTIGS = (
    "chr1", "chr2", "chr3", "chr5", "chr6", "chr7", "chr9", "chr10",
    "chr12", "chr13", "chr14", "chr16", "chr17", "chr19", "chr21",
    "chr22", "chrX", "chrY",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(directory: Path) -> dict:
    observed = {
        path.name.removesuffix("_base_differences_full.json")
        for path in directory.glob("*_base_differences_full.json")
    }
    if observed != set(CONTIGS):
        raise ValueError(f"Expected {set(CONTIGS) - observed}; unexpected {observed - set(CONTIGS)}")

    files = []
    total_bases = total_length = total_intervals = 0
    for contig in CONTIGS:
        old_path = directory / f"{contig}_base_differences.json"
        full_path = directory / f"{contig}_base_differences_full.json"
        bed_path = directory / f"{contig}_base_differences.bed"
        old = json.loads(old_path.read_text())
        full = json.loads(full_path.read_text())
        for field in ("length", "n_different_bases", "difference_types", "first_differences",
                      "left_fasta", "right_fasta", "contig"):
            if old[field] != full[field]:
                raise ValueError(f"{contig}: old/full {field} mismatch")
        if full["contig"] != contig or Path(full["difference_bed_path"]).name != bed_path.name:
            raise ValueError(f"{contig}: BED/contig identity mismatch")
        if sum(full["difference_types"].values()) != full["n_different_bases"]:
            raise ValueError(f"{contig}: difference-type count mismatch")
        bed_hash = sha256(bed_path)
        if bed_hash != full["difference_bed_sha256"]:
            raise ValueError(f"{contig}: BED SHA-256 mismatch")

        bed_bases = bed_intervals = 0
        previous_end = -1
        first_positions = [record["position_1based"] - 1 for record in full["first_differences"]]
        next_first = 0
        for line in bed_path.read_text().splitlines():
            fields = line.split("\t")
            if len(fields) != 3 or fields[0] != contig:
                raise ValueError(f"{contig}: malformed BED3 row")
            start, end = (int(value) for value in fields[1:])
            if not (0 <= start < end <= full["length"]) or start <= previous_end:
                raise ValueError(f"{contig}: invalid, unsorted, or unmerged BED intervals")
            while next_first < len(first_positions) and first_positions[next_first] < end:
                if first_positions[next_first] < start:
                    raise ValueError(f"{contig}: recorded first difference outside BED")
                next_first += 1
            bed_bases += end - start
            bed_intervals += 1
            previous_end = end
        if next_first != len(first_positions):
            raise ValueError(f"{contig}: recorded first difference outside BED")
        if bed_bases != full["n_different_bases"] or bed_intervals != full["n_difference_intervals"]:
            raise ValueError(f"{contig}: BED length/count does not match JSON")
        total_bases += bed_bases
        total_length += full["length"]
        total_intervals += bed_intervals
        files.append({
            "contig": contig, "length": full["length"],
            "n_different_bases": bed_bases, "n_difference_intervals": bed_intervals,
            "old_json_sha256": sha256(old_path),
            "full_json_sha256": sha256(full_path), "bed_sha256": bed_hash,
        })
    return {
        "n_contigs": len(files), "n_compared_bases": total_length,
        "n_different_bases": total_bases, "n_difference_intervals": total_intervals,
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = verify(args.directory)
    formatted = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.write_text(formatted)
    print(f"Verified {result['n_contigs']} contigs, {result['n_different_bases']} "
          f"different bases in {result['n_difference_intervals']} BED intervals")


if __name__ == "__main__":
    main()
