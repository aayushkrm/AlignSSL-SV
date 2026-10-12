"""Read-only inventory of Weller2025 Table S4; guide outcomes are not allele truth."""

import argparse
import collections
import csv
import hashlib
import io
import json
import math
from pathlib import Path


MISSING = {"", "NA"}
MAX_BYTES = 16 * 1024 * 1024


def number(value):
    if value in MISSING:
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Nonfinite source value: {value!r}")
    return result


def summarize(text):
    rows = list(csv.reader(io.StringIO(text), delimiter="\t", strict=True))
    if len(rows) < 2:
        raise ValueError("No source records")
    headers, rows = rows[0], rows[1:]
    if any(len(row) != len(headers) for row in rows):
        raise ValueError("Ragged source record")
    duplicates = {name: [i for i, h in enumerate(headers) if h == name]
                  for name, count in collections.Counter(headers).items() if count > 1}
    for name, positions in duplicates.items():
        if any(len({row[i] for i in positions}) != 1 for row in rows):
            raise ValueError(f"Conflicting duplicate header: {name}")
    index = {name: headers.index(name) for name in headers}
    required = {"oligo_id_short", "gene_name", "gene_group_label", "L2FC", "dropout",
                "enriched", "positive_control_gene", "HAP1_exonic", "freq_BFP"}
    if not required <= index.keys():
        raise ValueError(f"Missing required fields: {sorted(required - index.keys())}")
    field = lambda row, name: row[index[name]]
    identities = [field(row, "oligo_id_short") for row in rows]
    if len(set(identities)) != len(rows) or any(x in MISSING for x in identities):
        raise ValueError("Duplicate or missing construct identity")
    labels = [number(field(row, "L2FC")) for row in rows]
    for row in rows:
        for name in ("dropout", "enriched", "positive_control_gene", "HAP1_exonic"):
            if field(row, name) not in {"TRUE", "FALSE", "NA", ""}:
                raise ValueError(f"Unexpected flag: {name}")
    known = [(row, value) for row, value in zip(rows, labels) if value is not None]
    controls = [row for row in rows if field(row, "positive_control_gene") == "TRUE"
                and field(row, "HAP1_exonic") == "TRUE"]
    control_values = [number(field(row, "L2FC")) for row in controls]
    return {
        "schema": 1,
        "scope": "PUBLISHED_CONSTRUCT_TABLE_INVENTORY_NOT_ALLELE_FITNESS",
        "source_doi": "10.1101/2025.11.03.686307",
        "records": len(rows), "columns": len(headers), "headers": headers,
        "duplicate_header_positions_zero_based": duplicates,
        "duplicate_header_cells_all_equal": True,
        "unique_construct_identities": len(identities),
        "gene_name_distinct_literal_values": len({field(row, "gene_name") for row in rows}),
        "gene_groups": dict(collections.Counter(field(row, "gene_group_label") for row in rows)),
        "numeric_L2FC_records": len(known),
        "missing_L2FC_records": len(rows) - len(known),
        "L2FC_lt_minus_one": sum(value < -1 for _, value in known),
        "L2FC_gt_plus_one": sum(value > 1 for _, value in known),
        "unknown_rows_with_TRUE_dropout_flag": sum(
            value is None and field(row, "dropout") == "TRUE" for row, value in zip(rows, labels)),
        "missing_flag_values": {name: sum(field(row, name) in MISSING for row in rows)
                                for name in ("dropout", "enriched", "positive_control_gene", "HAP1_exonic")},
        "dropout_flag_disagreements_known_rows": sum(
            (value < -1) != (field(row, "dropout") == "TRUE") for row, value in known
            if field(row, "dropout") not in MISSING),
        "enrichment_flag_disagreements_known_rows": sum(
            (value > 1) != (field(row, "enriched") == "TRUE") for row, value in known
            if field(row, "enriched") not in MISSING),
        "positive_control_exonic_records": len(controls),
        "positive_control_exonic_missing_L2FC": sum(value is None for value in control_values),
        "positive_control_exonic_lt_minus_one": sum(
            value is not None and value < -1 for value in control_values),
        "missing_BFP_literal_values": sum(field(row, "freq_BFP") in MISSING for row in rows),
        "per_construct_confirmed_edit_fraction": "NOT_ESTABLISHED_BY_HEADER_OR_INVENTORY",
        "publication_or_causal_claim": "NONE",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.source.stat().st_size > MAX_BYTES:
        raise ValueError("Source exceeds read cap")
    payload = args.source.read_bytes()
    result = summarize(payload.decode("utf-8-sig"))
    result.update({"source_bytes": len(payload), "source_sha256": hashlib.sha256(payload).hexdigest()})
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
