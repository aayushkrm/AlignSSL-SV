#!/usr/bin/env python3
"""Recheck an independently fetched header-only BGZF block without variants."""

import csv
import gzip
import hashlib
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
PACKET = REPO / "results/vienna_vcf_header_20261106_run01"


def main():
    preservation = json.loads((PACKET / "preservation.json").read_text())
    for name, record in preservation["files"].items():
        data = (PACKET / name).read_bytes()
        if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError(f"Preserved source mismatch: {name}")
    decoded = gzip.decompress((PACKET / "vcf_header_bgzf_blocks.bin").read_bytes())
    if decoded != (PACKET / "vcf_header.txt").read_bytes():
        raise ValueError("BGZF and preserved header differ")
    lines = decoded.decode("utf-8").splitlines()
    if not lines or any(not line.startswith("#") for line in lines) or not lines[-1].startswith("#CHROM\t"):
        raise ValueError("Block must end with a header and contain no VCF records")
    samples = lines[-1].split("\t")[9:]
    if len(samples) != len(set(samples)):
        raise ValueError("Duplicate VCF sample columns")
    rna_path = REPO / "results/paired_dna_rna_ena_titles_20261104_run01/ena_titles.tsv"
    with rna_path.open(newline="") as stream:
        rna = {row["sample_title"] for row in csv.DictReader(stream, delimiter="\t")}
    hgs_path = REPO / "results/hgsvc2_vcf_header_20261106_run01/header_summary.json"
    hgs = json.loads(hgs_path.read_text())
    hgs_rna = {row["rna_title"] for row in hgs["rows"] if row["unambiguous"]}
    vienna_rna = set(samples) & rna
    print(f"Verified {len(preservation['files'])} preserved files and {len(samples)} unique Vienna columns")
    print(f"Exact RNA matches: {len(vienna_rna)}; also in HGSVC2 header: {len(vienna_rna & hgs_rna)}")
    print("RNA titles present in Vienna header:", ", ".join(sorted(vienna_rna)))


if __name__ == "__main__":
    main()
