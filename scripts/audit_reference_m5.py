"""Compare FASTA sequence digests with VCF contig MD5 and SAM dictionary M5."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path


def read_vcf_contigs(path: Path) -> dict[str, dict[str, str | int]]:
    result = {}
    with gzip.open(path, "rt") as source:
        for line in source:
            if not line.startswith("##"):
                break
            if not line.startswith("##contig=<"):
                continue
            fields = dict(re.findall(r"(?:^|,)(ID|length|md5)=([^,>]+)", line[10:]))
            if {"ID", "length", "md5"} <= fields.keys():
                result[fields["ID"]] = {
                    "length": int(fields["length"]), "md5": fields["md5"].lower()
                }
    return result


def read_sam_dict(path: Path) -> dict[str, dict[str, str | int]]:
    result = {}
    for line in path.read_text().splitlines():
        if not line.startswith("@SQ\t"):
            continue
        fields = dict(field.split(":", 1) for field in line.split("\t")[1:])
        result[fields["SN"]] = {"length": int(fields["LN"]), "md5": fields["M5"].lower()}
    return result


def fasta_digests(path: Path, stop_after: str | None = None) -> dict[str, dict[str, str | int]]:
    result = {}
    name = None
    canonical = original_case = None
    length = 0

    def finish() -> None:
        if name is not None:
            result[name] = {
                "length": length,
                "canonical_m5": canonical.hexdigest(),
                "case_preserving_md5": original_case.hexdigest(),
            }

    with gzip.open(path, "rb") as source:
        for line in source:
            if line.startswith(b">"):
                finish()
                if stop_after is not None and name == stop_after:
                    return result
                name = line[1:].split()[0].decode("ascii")
                canonical = hashlib.md5()
                original_case = hashlib.md5()
                length = 0
            else:
                if name is None:
                    raise ValueError("FASTA sequence before header")
                sequence = b"".join(line.split())
                length += len(sequence)
                canonical.update(sequence.upper())
                original_case.update(sequence)
    finish()
    return result


def compare(fasta: Path, vcf: Path, sam_dict: Path,
            stop_after: str | None = None) -> dict:
    truth = read_vcf_contigs(vcf)
    reads = read_sam_dict(sam_dict)
    sequences = fasta_digests(fasta, stop_after=stop_after)
    shared = sorted(truth.keys() & reads.keys() & sequences.keys())
    rows = {}
    for name in shared:
        seq = sequences[name]
        v = truth[name]
        d = reads[name]
        rows[name] = {
            **seq,
            "vcf_length": v["length"], "vcf_md5": v["md5"],
            "dict_length": d["length"], "dict_m5": d["md5"],
            "vcf_matches_canonical": v["md5"] == seq["canonical_m5"],
            "vcf_matches_case_preserving": v["md5"] == seq["case_preserving_md5"],
            "dict_matches_canonical": d["md5"] == seq["canonical_m5"],
            "lengths_match": v["length"] == d["length"] == seq["length"],
        }
    return {
        "fasta": str(fasta), "vcf": str(vcf), "sam_dict": str(sam_dict),
        "stop_after_contig": stop_after,
        "n_shared": len(shared),
        "n_vcf_matches_canonical": sum(row["vcf_matches_canonical"] for row in rows.values()),
        "n_vcf_matches_case_preserving": sum(row["vcf_matches_case_preserving"] for row in rows.values()),
        "n_dict_matches_canonical": sum(row["dict_matches_canonical"] for row in rows.values()),
        "n_lengths_match": sum(row["lengths_match"] for row in rows.values()),
        "contigs": rows,
        "caveat": "FASTA is the official HGSVC no-ALT source; verify it is the exact HGSVC3 calling reference before inferring provenance.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fasta", type=Path, required=True)
    parser.add_argument("--vcf", type=Path, required=True)
    parser.add_argument("--dict", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stop-after-contig", help="Preliminary partial-stream check only")
    args = parser.parse_args()
    result = compare(args.fasta, args.vcf, args.dict,
                     stop_after=args.stop_after_contig)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"shared={result['n_shared']} "
        f"vcf_canonical={result['n_vcf_matches_canonical']} "
        f"vcf_case={result['n_vcf_matches_case_preserving']} "
        f"dict_canonical={result['n_dict_matches_canonical']} "
        f"lengths={result['n_lengths_match']}"
    )


if __name__ == "__main__":
    main()
