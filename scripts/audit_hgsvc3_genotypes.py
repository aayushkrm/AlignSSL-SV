"""Describe HGSVC3 deletion genotypes; do not treat 0/0 as callable negatives."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def summarize(vcf: Path) -> dict:
    samples: list[str] = []
    counts: dict[str, dict[str, int]] = {}
    records = 0
    del_records = 0
    with gzip.open(vcf, "rt") as source:
        for line in source:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM\t"):
                samples = line.rstrip("\n").split("\t")[9:]
                counts = {
                    sample: {"carrier": 0, "hom_ref": 0, "partial_missing": 0,
                             "fully_missing": 0}
                    for sample in samples
                }
                continue
            if not samples:
                raise ValueError("VCF has no #CHROM header before records")
            fields = line.rstrip("\n").split("\t")
            if len(fields) != len(samples) + 9:
                raise ValueError(f"VCF row has {len(fields)} fields, expected {len(samples) + 9}")
            records += 1
            info = dict(item.split("=", 1) for item in fields[7].split(";") if "=" in item)
            if info.get("SVTYPE") != "DEL" or abs(int(info["SVLEN"])) < 50:
                continue
            if fields[8] != "GT":
                raise ValueError(f"Expected GT-only FORMAT, got {fields[8]}")
            del_records += 1
            for sample, gt in zip(samples, fields[9:]):
                alleles = gt.replace("/", "|").split("|")
                if len(alleles) != 2:
                    raise ValueError(f"Expected diploid genotype, got {gt}")
                if alleles == [".", "."]:
                    counts[sample]["fully_missing"] += 1
                elif "." in alleles:
                    counts[sample]["partial_missing"] += 1
                elif any(int(allele) > 0 for allele in alleles):
                    counts[sample]["carrier"] += 1
                else:
                    counts[sample]["hom_ref"] += 1
    if not samples:
        raise ValueError("VCF has no #CHROM header")
    with vcf.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    return {
        "vcf": str(vcf),
        "vcf_sha256": digest,
        "total_sv_records": records,
        "del_records_ge_50bp": del_records,
        "samples": counts,
        "caveat": "0/0 at a variant record is not a genome-wide callable-negative mask.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vcf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.vcf)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"SV records={result['total_sv_records']} "
        f"DEL>=50bp={result['del_records_ge_50bp']} "
        f"samples={len(result['samples'])}"
    )


if __name__ == "__main__":
    main()
