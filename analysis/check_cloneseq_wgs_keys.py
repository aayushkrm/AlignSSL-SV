#!/usr/bin/env python3
"""Link author-listed cfDNA-WGS samples to public table keys only."""

import collections
import datetime
import json
import pathlib
import re
import sys

import openpyxl

from audit_cloneseq_content import (AUTHOR, AUTHOR_COMMIT, CONFIG, CONFIG_SHA,
                                    WORKBOOK, WORKBOOK_SHA, config_items, sha)

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results/cloneseq_wgs_key_audit_20261122_run01"
PROTOCOL_COMMIT = "1c72bb4"


def classify(wgs_names, purity_rows, sv_keys, snv_keys):
    by_sample = collections.defaultdict(list)
    for patient, sample, timepoint, days in purity_rows:
        if isinstance(sample, str):
            by_sample[sample].append((patient, sample, timepoint, days))
    totals = collections.Counter()
    patients = collections.defaultdict(collections.Counter)
    for sample in wgs_names:
        match = re.fullmatch(r"(SPECTRUM-OV-\d+)_.*", sample)
        if not match:
            raise ValueError("Unexpected author WGS identifier")
        patient = match.group(1)
        mappings = by_sample.get(sample, [])
        if not mappings:
            state = "no_exact_S2_sample"
        elif len(mappings) != 1:
            state = "duplicate_S2_sample"
        else:
            key = mappings[0]
            if key[0] != patient or any(x is None or x == "" for x in key):
                state = "conflicting_or_missing_S2_key"
            else:
                sv, snv = key in sv_keys, key in snv_keys
                state = "both_count_sheets" if sv and snv else "SV_only" if sv else "SNV_only" if snv else "neither_count_sheet"
        totals[state] += 1
        patients[patient][state] += 1
    return {"samples_listed": len(wgs_names), "sample_status_counts": dict(totals),
            "patients": [{"patient": p, "sample_status_counts": dict(c)} for p, c in sorted(patients.items())],
            "distinct_patients": len(patients),
            "patients_with_both_count_sheet_keys": sum(c["both_count_sheets"] > 0 for c in patients.values())}


def first_four(sheet, expected):
    rows = sheet.iter_rows(min_col=1, max_col=4, values_only=True)
    if tuple(next(rows, ())) != tuple(expected):
        raise ValueError("Unexpected first four field labels: " + sheet.title)
    yield from rows


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    if sha(WORKBOOK) != WORKBOOK_SHA or sha(CONFIG) != CONFIG_SHA:
        raise ValueError("Frozen input hash mismatch")
    wgs = config_items(CONFIG.read_text(), "patient_wgs")
    if len(wgs) != 12:
        raise ValueError("Author WGS list no longer has 12 sample identifiers")
    allowed = set(wgs)
    book = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=False)
    try:
        names = ["patient", "sample", "timepoint", "days"]
        purity = [row for row in first_four(book["S2 - Tumor Fractions"], names) if row[1] in allowed]
        sv = {row for row in first_four(book["S7 - SV read counts"], ["patient", "sample_id", "timepoint", "days"]) if row[1] in allowed}
        snv = {row for row in first_four(book["S8 - SNV read counts"], names) if row[1] in allowed}
    finally:
        book.close()
    result = classify(wgs, purity, sv, snv)
    result.update({"workbook_sha256": WORKBOOK_SHA, "author_config_sha256": CONFIG_SHA,
                   "author_commit": AUTHOR_COMMIT, "script_sha256": sha(pathlib.Path(__file__)),
                   "helper_sha256": sha(REPO / "analysis/audit_cloneseq_content.py"),
                   "protocol_commit": PROTOCOL_COMMIT,
                   "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "python": sys.version, "openpyxl": openpyxl.__version__,
                   "limits": "First four identifier/time columns only; no read counts, WGS signal files, clinical outcomes or clone accuracy inspected."})
    (OUT / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Author WGS samples", result["samples_listed"], "key statuses", result["sample_status_counts"],
          "patients with both keys", result["patients_with_both_count_sheet_keys"])


if __name__ == "__main__":
    main()
