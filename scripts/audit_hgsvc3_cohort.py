"""Join the HGSVC3 assembly SV roster to IGSR 30x CRAM and pedigree indexes."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from urllib.request import urlopen

BASE = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage"
SOURCES = {
    "unrelated_index": f"{BASE}/1000G_2504_high_coverage.sequence.index",
    "related_index": f"{BASE}/1000G_698_related_high_coverage.sequence.index",
    "pedigree": f"{BASE}/working/1kGP.3202_samples.pedigree_info.txt",
}


def download_text(url: str) -> tuple[str, str]:
    with urlopen(url, timeout=120) as response:
        payload = response.read()
    return payload.decode("utf-8"), hashlib.sha256(payload).hexdigest()


def parse_index(text: str, cohort: str) -> dict[str, list[dict[str, str]]]:
    rows = csv.reader(
        (line for line in text.splitlines() if line and not line.startswith("##")),
        delimiter="\t",
    )
    columns = next(rows)
    experiment_index = columns.index("EXPERIMENT_ID")
    matches: dict[str, list[dict[str, str]]] = defaultdict(list)
    for values in rows:
        # The official 698-related index has an unnamed empty field between
        # POPULATION and EXPERIMENT_ID; its header omits that field.
        if len(values) == len(columns) + 1 and values[experiment_index] == "":
            del values[experiment_index]
        if len(values) != len(columns):
            raise ValueError(f"Unexpected {cohort} index row width: {len(values)}")
        row = dict(zip(columns, values))
        sample = row["SAMPLE_NAME"]
        path = row["#ENA_FILE_PATH"]
        if not path.endswith(".cram") or row["INSTRUMENT_PLATFORM"] != "ILLUMINA":
            continue
        matches[sample].append(
            {
                "cohort": cohort,
                "url": path.replace("ftp://", "https://", 1),
                "md5": row["MD5SUM"],
                "run_id": row["RUN_ID"],
                "population": row["POPULATION"],
                "analysis_group": row["ANALYSIS_GROUP"],
            }
        )
    return matches


def parse_pedigree(text: str) -> dict[str, dict[str, str]]:
    lines = [line.split() for line in text.splitlines() if line.strip()]
    columns = lines[0]
    return {row[0]: dict(zip(columns, row)) for row in lines[1:]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vcf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    with gzip.open(args.vcf, "rt") as variants:
        for line in variants:
            if line.startswith("#CHROM\t"):
                samples = line.rstrip("\n").split("\t")[9:]
                break
        else:
            raise ValueError("VCF has no #CHROM header")

    source_hashes = {}
    source_texts = {}
    for name, url in SOURCES.items():
        source_texts[name], digest = download_text(url)
        source_hashes[name] = {"url": url, "sha256": digest}

    alignments: dict[str, list[dict[str, str]]] = defaultdict(list)
    for name, cohort in [("unrelated_index", "2504"), ("related_index", "698")]:
        for sample, rows in parse_index(source_texts[name], cohort).items():
            alignments[sample].extend(rows)
    pedigree = parse_pedigree(source_texts["pedigree"])
    roster = set(samples)

    sample_records = []
    for sample in samples:
        family = pedigree.get(sample, {})
        sample_records.append(
            {
                "sample": sample,
                "alignments": alignments.get(sample, []),
                "father": family.get("fatherID", "unknown"),
                "mother": family.get("motherID", "unknown"),
                "sex": family.get("sex", "unknown"),
                "parents_in_hgsvc3": [
                    parent
                    for parent in (family.get("fatherID"), family.get("motherID"))
                    if parent and parent != "0" and parent in roster
                ],
            }
        )

    result = {
        "purpose": "cohort_feasibility_only",
        "truth_vcf": str(args.vcf),
        "truth_vcf_sha256": hashlib.sha256(args.vcf.read_bytes()).hexdigest(),
        "source_indexes": source_hashes,
        "n_truth_samples": len(samples),
        "n_with_30x_illumina_cram": sum(bool(row["alignments"]) for row in sample_records),
        "n_without_30x_illumina_cram": sum(not row["alignments"] for row in sample_records),
        "unmatched_samples": [row["sample"] for row in sample_records if not row["alignments"]],
        "family_links_within_truth_roster": [
            {"child": row["sample"], "parents": row["parents_in_hgsvc3"]}
            for row in sample_records
            if row["parents_in_hgsvc3"]
        ],
        "samples": sample_records,
        "limitations": [
            "A matching CRAM index entry does not prove its file is available or intact.",
            "Reference dictionary and CRAM sequence MD5 compatibility are not yet verified.",
            "A variant VCF genotype is not a genome-wide confident-negative mask.",
            "Pedigree links in this file may not capture all genetic relatedness.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"HGSVC3 samples={result['n_truth_samples']} "
        f"matched_cram={result['n_with_30x_illumina_cram']} "
        f"unmatched={result['unmatched_samples']} "
        f"family_links={len(result['family_links_within_truth_roster'])}"
    )


if __name__ == "__main__":
    main()
