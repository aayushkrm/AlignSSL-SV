#!/usr/bin/env python3
"""Audit public CloneSeq-SV table joinability without scoring outcomes."""

import collections
import datetime
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys

import openpyxl

REPO = pathlib.Path(__file__).resolve().parent.parent
WORKBOOK = REPO.parent / "runs/cloneseq_workbook_metadata_20261106_run01/SupplementaryTables.xlsx"
AUTHOR = REPO.parent / "runs/cloneseq-figure-code-20261122"
CONFIG = AUTHOR / "config.yaml"
SCHEMA = REPO / "results/cloneseq_schema_20261122_run01/schema.json"
OUT = REPO / "results/cloneseq_content_audit_20261122_run02"
WORKBOOK_SHA = "7fd3bf312acb0ba617d28878bd9b4a54122164fb842e933d6a13c5efdc53ee33"
CONFIG_SHA = "f5a25b5b0109a102b670e0a549679da08e49c33bd6fdb1d65292005e366ac954"
AUTHOR_COMMIT = "076281373393e6922652371262f5975af9a41a30"
PROTOCOL_COMMIT = "364d75a"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def config_items(text, name):
    match = re.search(r"(?m)^" + re.escape(name) + r':\s*\n((?:[ \t]+-\s+"[^"]+"\s*\n)+)', text)
    if not match:
        raise ValueError("Missing expected author configuration list: " + name)
    values = re.findall(r'(?m)^\s*-\s+"([^"]+)"\s*$', match.group(1))
    if len(values) != len(set(values)):
        raise ValueError("Duplicate author configuration entries: " + name)
    return values


def missing(value):
    return value is None or value == ""


def count_state(total, alt):
    if missing(total) or missing(alt):
        return "missing"
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or
           not math.isfinite(x) or x < 0 or int(x) != x for x in (total, alt)):
        return "invalid"
    if alt > total:
        return "invalid"
    return "zero_total" if total == 0 else "valid_exposed"


def specimen_key(row, sample_field):
    values = tuple(row.get(x) for x in (sample_field, "timepoint", "days"))
    if any(missing(x) for x in values) or not isinstance(values[0], str):
        return None
    try:
        hash(values)
    except TypeError:
        return None
    return values


def status_pair(sv, snv, sv_rows, snv_rows):
    if not sv_rows or not snv_rows:
        return "ABSENT"
    return "PRESENT" if sv & snv else "UNRESOLVED"


def read_rows(sheet, expected):
    iterator = sheet.iter_rows(values_only=True)
    header = next(iterator, ())
    if list(header) != expected:
        raise ValueError("Header differs from frozen schema: " + sheet.title)
    names = [value for value in header if value is not None]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate column labels: " + sheet.title)
    for row in iterator:
        if all(missing(v) for v in row):
            continue
        yield dict(zip(header, row))


def build_audit(book, schema, roster, timeline, wgs_counts):
    by_name = {s["sheet"]: s["fields"] for s in schema["sheets"]}
    targets = [name for name in book.sheetnames if re.match(r"^S(?:[1-9]|10) - ", name)]
    if len(targets) != 10:
        raise ValueError("Expected exactly the ten S1-S10 input sheets")
    per = {p: {"sheet_rows": collections.Counter(), "sv_samples": set(), "snv_samples": set(),
               "sv_exposed": set(), "snv_exposed": set(), "sv_types": set(), "snv_types": set(),
               "sv_counts": collections.Counter(), "snv_counts": collections.Counter(),
               "sv_background": collections.Counter(), "snv_background": collections.Counter(),
               "sv_join": collections.Counter(), "snv_join": collections.Counter(),
               "correction_fields": 0, "yield_rows": 0, "coverage_rows": 0}
           for p in roster}
    rows_seen = collections.Counter()
    missing_patient = collections.Counter()
    outside = collections.defaultdict(set)
    sv_meta = collections.defaultdict(list)
    snv_meta = collections.defaultdict(list)
    pending = {"SV": [], "SNV": []}
    for sheet_name in targets:
        for row in read_rows(book[sheet_name], by_name[sheet_name]):
            rows_seen[sheet_name] += 1
            if sheet_name.startswith("S10 "):
                key = tuple(row.get(k) for k in ("target_idx", "clonality", "Hugo_Symbol"))
                if not any(missing(v) for v in key):
                    snv_meta[key].append(row.get("clone_id"))
                continue
            patient = row.get("patient")
            if missing(patient):
                missing_patient[sheet_name] += 1
                continue
            if patient not in per:
                outside[sheet_name].add(str(patient))
                continue
            item = per[patient]
            item["sheet_rows"][sheet_name] += 1
            if sheet_name.startswith("S1 "):
                item["coverage_rows"] += 1
            elif sheet_name.startswith("S2 "):
                item["yield_rows"] += not missing(row.get("dna_yield"))
            elif sheet_name.startswith("S9 "):
                key = (patient, row.get("target_idx"))
                if not missing(key[1]):
                    sv_meta[key].append(row.get("clone_id"))
                    item["correction_fields"] += not missing(row.get("correction"))
            elif sheet_name.startswith(("S7 ", "S8 ")):
                sv = sheet_name.startswith("S7 ")
                kind = "sv" if sv else "snv"
                spec = specimen_key(row, "sample_id" if sv else "sample")
                if spec is not None:
                    item[kind + "_samples"].add(spec)
                state = count_state(row.get("total_counts"), row.get("alt_counts"))
                item[kind + "_counts"][state] += 1
                item[kind + "_background"][count_state(row.get("total_counts.background"),
                                                        row.get("alt_counts.background"))] += 1
                if state == "valid_exposed" and spec is not None:
                    item[kind + "_exposed"].add(spec)
                if not missing(row.get("bamtype")):
                    item[kind + "_types"].add(str(row["bamtype"]))
                key = ((patient, row.get("target_idx")) if sv else
                       tuple(row.get(k) for k in ("target_idx", "clonality", "Hugo_Symbol")))
                pending["SV" if sv else "SNV"].append((patient, key, row.get("clone_id")))

    for kind, metadata in (("SV", sv_meta), ("SNV", snv_meta)):
        for patient, key, observed_clone in pending[kind]:
            counts = per[patient][kind.lower() + "_join"]
            if any(missing(v) for v in key):
                counts["missing_key"] += 1
            elif key not in metadata:
                counts["unmatched"] += 1
            elif len(metadata[key]) != 1:
                counts["ambiguous_metadata"] += 1
            else:
                counts["unique"] += 1
                assigned = metadata[key][0]
                if missing(assigned):
                    counts["missing_clone_label"] += 1
                else:
                    counts["unique_with_clone_label"] += 1
                if kind == "SNV" and not missing(observed_clone) and not missing(assigned) and observed_clone != assigned:
                    counts["clone_label_conflict"] += 1

    cases = []
    for patient in roster:
        x = per[patient]
        shared = x["sv_samples"] & x["snv_samples"]
        exposed = x["sv_exposed"] & x["snv_exposed"]
        time_sv = {(x[1], x[2]) for x in x["sv_samples"]}
        time_snv = {(x[1], x[2]) for x in x["snv_samples"]}
        joined = x["sv_join"]["unique_with_clone_label"] > 0 and x["snv_join"]["unique_with_clone_label"] > 0
        conflict = sum(x[k][j] for k in ("sv_join", "snv_join")
                       for j in ("missing_key", "unmatched", "ambiguous_metadata", "clone_label_conflict", "missing_clone_label"))
        marker_status = "PRESENT" if joined and conflict == 0 else ("ABSENT" if not x["sv_join"] or not x["snv_join"] else "UNRESOLVED")
        sheet_rows = dict(x["sheet_rows"])
        statuses = {
            "sample_time_keys": status_pair(x["sv_samples"], x["snv_samples"],
                                            bool(x["sv_counts"]), bool(x["snv_counts"])),
            "marker_to_clone_metadata": marker_status,
            "count_fields_and_units": "UNRESOLVED" if exposed else "ABSENT" if not x["sv_counts"] or not x["snv_counts"] else "UNRESOLVED",
            "material_and_sequencing_budget": "UNRESOLVED",
            "independent_error_controls": "UNRESOLVED",
            "timing_and_calibration": "UNRESOLVED",
            "separate_molecular_reference": "UNRESOLVED",
            "full_reuse_and_reproducibility": "UNRESOLVED",
        }
        cases.append({"patient": patient, "in_author_timeline": patient in timeline,
                      "author_wgs_specimens_listed": wgs_counts[patient], "statuses": statuses,
                      "evidence": {"sheet_rows": sheet_rows, "exact_shared_specimens": len(shared),
                                   "shared_specimens_with_exposed_numeric_counts": len(exposed),
                                   "shared_timepoints_without_exact_sample": len((time_sv & time_snv) - {(z[1], z[2]) for z in shared}),
                                   "sv_counts": dict(x["sv_counts"]), "snv_counts": dict(x["snv_counts"]),
                                   "sv_background": dict(x["sv_background"]), "snv_background": dict(x["snv_background"]),
                                   "sv_marker_join": dict(x["sv_join"]), "snv_marker_join": dict(x["snv_join"]),
                                   "sv_bamtypes": sorted(x["sv_types"]), "snv_bamtypes": sorted(x["snv_types"]),
                                   "coverage_rows": x["coverage_rows"], "dna_yield_rows": x["yield_rows"],
                                   "sv_correction_rows": x["correction_fields"]}})
    return {"patients": cases, "sheet_row_counts": dict(rows_seen),
            "missing_patient_rows": dict(missing_patient),
            "outside_roster_patient_labels": {k: sorted(v) for k, v in outside.items()},
            "sv_metadata_keys": len(sv_meta), "snv_metadata_keys": len(snv_meta),
            "sv_duplicate_metadata_keys": sum(len(v) > 1 for v in sv_meta.values()),
            "snv_duplicate_metadata_keys": sum(len(v) > 1 for v in snv_meta.values())}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    if sha(WORKBOOK) != WORKBOOK_SHA or sha(CONFIG) != CONFIG_SHA:
        raise ValueError("Frozen input hash mismatch")
    author_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=AUTHOR, text=True).strip()
    if author_commit != AUTHOR_COMMIT:
        raise ValueError("Author source commit mismatch")
    text = CONFIG.read_text()
    roster, timeline, wgs = (config_items(text, name) for name in ("patients", "patients_timeline", "patient_wgs"))
    if len(roster) != 24 or len(timeline) != 18 or len(wgs) != 12 or not set(timeline) <= set(roster):
        raise ValueError("Author roster or nested list does not match the frozen frame")
    wgs_patients = []
    for name in wgs:
        match = re.fullmatch(r"(SPECTRUM-OV-\d+)_.*", name)
        if not match or match.group(1) not in roster:
            raise ValueError("Unresolved author WGS sample identifier")
        wgs_patients.append(match.group(1))
    if len(set(wgs_patients)) != 6:
        raise ValueError("Author WGS patient count does not match the frozen frame")
    schema = json.loads(SCHEMA.read_text())
    book = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=False)
    try:
        audit = build_audit(book, schema, roster, set(timeline), collections.Counter(wgs_patients))
    finally:
        book.close()
    audit.update({"workbook_sha256": WORKBOOK_SHA, "author_config_sha256": CONFIG_SHA,
                  "author_commit": AUTHOR_COMMIT, "schema_sha256": sha(SCHEMA),
                  "protocol_commit": PROTOCOL_COMMIT, "script_sha256": sha(pathlib.Path(__file__)),
                  "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "python": sys.version, "openpyxl": openpyxl.__version__,
                  "limits": "S1-S10 keys, count validity and field presence only; no recurrence rows, allele fractions, performance comparisons or outcome analysis."})
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print("Roster", len(audit["patients"]), "S1-S10 rows", sum(audit["sheet_row_counts"].values()),
          "patients with exact specimen match", sum(p["statuses"]["sample_time_keys"] == "PRESENT" for p in audit["patients"]))


if __name__ == "__main__":
    main()
