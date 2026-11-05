#!/usr/bin/env python3
"""Join HGSVC2 sample-list name tokens to fixed ENA RNA sample titles."""

import collections
import hashlib
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
SOURCE = REPO / "results/hgsvc2_sample_lists_20261106_run01"
CROSSWALK = REPO / "results/paired_dna_rna_ont500_crosswalk_20261104_run01/crosswalk.json"
OUTPUT = SOURCE / "crosswalk.json"
NAMES = ["pangenie-genotyping.PRJEB31736.2504.sample-list.txt",
         "pangenie-genotyping.PRJEB36890.698.sample-list.txt"]
PATTERN = re.compile(r"((?:HG|NA)\d{5})_(ERR\d+)")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    receipt = json.loads((SOURCE / "receipt.json").read_text())
    sources = {x["name"]: x for x in receipt["sources"]}
    by_sample = collections.defaultdict(list)
    source_hashes = {}
    for name in NAMES:
        source = sources[name]
        attempt = source["successful_attempt"]
        path = SOURCE / f"{name}.attempt{attempt:02d}.stdout"
        expected = source["attempts"][attempt - 1]["stdout_sha256"]
        if sha(path) != expected:
            raise ValueError(f"Source hash mismatch: {name}")
        source_hashes[name] = expected
        for raw in path.read_text().splitlines():
            match = PATTERN.fullmatch(raw)
            if not match:
                raise ValueError(f"Unexpected sample-list row: {raw!r}")
            by_sample[match.group(1)].append({"source": name, "full_row": raw})
    prior = json.loads(CROSSWALK.read_text())
    rows = []
    for row in prior["rows"]:
        sample = row["rna_sample_title"]
        has_long_read_metadata = row["vienna_listed_alignment"] or row["ont500_exact_metadata_label"]
        rows.append({"rna_title": sample, "pangenie_list_rows": by_sample.get(sample, []),
                     "prior_long_read_metadata_match": has_long_read_metadata})
    result = {"source_rows": sum(map(len, by_sample.values())),
              "distinct_source_sample_tokens": len(by_sample),
              "duplicate_source_tokens": {k: v for k, v in sorted(by_sample.items()) if len(v) > 1},
              "rna_titles": len(rows),
              "rna_titles_matching_pangenie_list": sum(bool(r["pangenie_list_rows"]) for r in rows),
              "additional_matches_beyond_prior_24": sum(bool(r["pangenie_list_rows"]) and not r["prior_long_read_metadata_match"] for r in rows),
              "rows": rows, "source_sha256": source_hashes,
              "prior_crosswalk_sha256": sha(CROSSWALK),
              "script_sha256": sha(pathlib.Path(__file__)),
              "limits": "Sample-list tokens only: no VCF header, genotypes or biological identity verified."}
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print("source rows", result["source_rows"], "unique tokens", result["distinct_source_sample_tokens"],
          "RNA matches", result["rna_titles_matching_pangenie_list"],
          "additional beyond prior 24", result["additional_matches_beyond_prior_24"])


if __name__ == "__main__":
    main()
