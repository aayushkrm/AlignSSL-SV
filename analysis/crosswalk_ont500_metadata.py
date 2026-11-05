#!/usr/bin/env python3
"""Compare exact RNA titles to public ONT-500 metadata and Vienna matches."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vienna-crosswalk", type=Path, required=True)
    p.add_argument("--ont500", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    vienna = json.loads(args.vienna_crosswalk.read_text())
    metadata = args.ont500 / "ont500_metadata.tsv"
    receipt = json.loads((args.ont500 / "receipt.json").read_text())
    item = next(x for x in receipt["sources"] if x["name"] == metadata.name)
    if item.get("error") or digest(metadata) != item["sha256"]:
        raise ValueError("ONT-500 metadata receipt mismatch")
    with metadata.open(newline="") as handle:
        table = list(csv.DictReader(handle, delimiter="\t"))
    ids = [row["NHGRI_ID"] for row in table]
    if not all(ids) or len(ids) != len(set(ids)):
        raise ValueError("ONT-500 metadata has missing or repeated sample labels")
    ont_ids = set(ids)
    rows = []
    for item in vienna["rows"]:
        title = item["sample_title"]
        rows.append({"rna_sample_title": title,
                     "vienna_listed_alignment": bool(item["listed_dna_files"]),
                     "ont500_exact_metadata_label": title in ont_ids})
    stats = {"ont500_metadata_rows": len(table), "ont500_distinct_ids": len(ont_ids),
             "ont500_id_prefixes": {prefix: sum(x.startswith(prefix) for x in ids) for prefix in ("HG", "GM", "NA")},
             "rna_titles": len(rows), "vienna_exact": sum(r["vienna_listed_alignment"] for r in rows),
             "ont500_exact": sum(r["ont500_exact_metadata_label"] for r in rows),
             "both_exact": sum(r["vienna_listed_alignment"] and r["ont500_exact_metadata_label"] for r in rows),
             "either_exact": sum(r["vienna_listed_alignment"] or r["ont500_exact_metadata_label"] for r in rows),
             "neither_exact": [r["rna_sample_title"] for r in rows
                               if not r["vienna_listed_alignment"] and not r["ont500_exact_metadata_label"]],
             "rows": rows, "ont500_source_sha256": digest(metadata),
             "vienna_crosswalk_sha256": digest(args.vienna_crosswalk),
             "limits": "Exact strings only; GM/NA aliases, individual file availability and biological identity unverified."}
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    path = out / "crosswalk.json"
    path.write_text(json.dumps(stats, indent=2) + "\n")
    (out / "receipt.json").write_text(json.dumps({"script_sha256": digest(Path(__file__).resolve()),
                                                   "crosswalk_sha256": digest(path)}, indent=2) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
