#!/usr/bin/env python3
"""Run the preregistered CloneSeq-SV content audit corrections."""

import collections
import datetime
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys
import time
import traceback

import openpyxl


REPO = pathlib.Path(__file__).resolve().parents[1]
WORKBOOK = REPO.parent / "runs/cloneseq_workbook_metadata_20261106_run01/SupplementaryTables.xlsx"
AUTHOR = REPO.parent / "runs/cloneseq-figure-code-20261122"
CONFIG = AUTHOR / "config.yaml"
SCHEMA = REPO / "results/cloneseq_schema_20261122_run01/schema.json"
SCHEMA_RECEIPT = SCHEMA.parent / "receipt.json"
PROTOCOL = REPO / "docs/research/2026-11-22-cloneseq-content-protocol.md"
REVIEW = REPO / "docs/research/2026-11-22-cloneseq-content-independent-review.md"
ORIGINAL_AUDIT = REPO / "analysis/audit_cloneseq_content.py"
RUN02_AUDIT = REPO / "results/cloneseq_content_audit_20261122_run02/audit.json"
OUT = REPO / "results/cloneseq_content_audit_20261122_run03"

WORKBOOK_SHA = "7fd3bf312acb0ba617d28878bd9b4a54122164fb842e933d6a13c5efdc53ee33"
CONFIG_SHA = "f5a25b5b0109a102b670e0a549679da08e49c33bd6fdb1d65292005e366ac954"
SCHEMA_SHA = "02917a6c1bef6dfc59e63f2cd1284322dab19a4c3fe23d3b833e803ceeb78d93"
AUTHOR_COMMIT = "076281373393e6922652371262f5975af9a41a30"
PREREGISTRATION_COMMIT = "3d04c136d8e96a3130c3cbaaf6e3b10cfb6353b4"


def sha256_file(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(args, cwd):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def collect_pre_read_fingerprints():
    """Read hashes and checkout metadata only. This function never opens Excel."""
    schema_receipt = json.loads(SCHEMA_RECEIPT.read_text())
    author_commit = git_output(["rev-parse", "HEAD"], AUTHOR)
    author_dirty = git_output(["status", "--porcelain=v1", "--untracked-files=all"], AUTHOR)
    repo_head = git_output(["rev-parse", "HEAD"], REPO)
    preregistration_is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREREGISTRATION_COMMIT, "HEAD"],
        cwd=REPO, check=False,
    ).returncode == 0
    return {
        "workbook_sha256": sha256_file(WORKBOOK),
        "author_config_sha256": sha256_file(CONFIG),
        "schema_sha256": sha256_file(SCHEMA),
        "schema_receipt_sha256": sha256_file(SCHEMA_RECEIPT),
        "schema_receipt_schema_sha256": schema_receipt.get("schema_sha256"),
        "schema_receipt_workbook_sha256": schema_receipt.get("workbook_sha256"),
        "author_checkout_commit": author_commit,
        "author_checkout_clean": not bool(author_dirty),
        "analysis_repo_head": repo_head,
        "preregistration_is_ancestor": preregistration_is_ancestor,
    }


def verify_pre_read_gate(fingerprints):
    """Reject an input or checkout mismatch before opening the workbook."""
    expected = {
        "workbook_sha256": WORKBOOK_SHA,
        "author_config_sha256": CONFIG_SHA,
        "schema_sha256": SCHEMA_SHA,
        "schema_receipt_schema_sha256": SCHEMA_SHA,
        "schema_receipt_workbook_sha256": WORKBOOK_SHA,
        "author_checkout_commit": AUTHOR_COMMIT,
    }
    failed = [name for name, value in expected.items() if fingerprints.get(name) != value]
    if fingerprints.get("author_checkout_clean") is not True:
        failed.append("author_checkout_clean")
    if fingerprints.get("preregistration_is_ancestor") is not True:
        failed.append("preregistration_is_ancestor")
    if failed:
        raise ValueError("Frozen pre-read verification failed: " + ", ".join(failed))


def open_verified_workbook(fingerprints, workbook_path=WORKBOOK, loader=None):
    """Open the workbook only after all frozen hashes and checkouts pass."""
    verify_pre_read_gate(fingerprints)
    open_workbook = loader or openpyxl.load_workbook
    return open_workbook(workbook_path, read_only=True, data_only=False)


def config_items(text, name):
    match = re.search(
        r"(?m)^" + re.escape(name) + r':\s*\n((?:[ \t]+-\s+"[^\"]+"\s*\n)+)', text
    )
    if not match:
        raise ValueError("Missing expected author configuration list: " + name)
    values = re.findall(r'(?m)^\s*-\s+"([^\"]+)"\s*$', match.group(1))
    if len(values) != len(set(values)):
        raise ValueError("Duplicate author configuration entries: " + name)
    return values


def missing(value):
    return value is None or value == ""


def valid_count(value):
    return (not missing(value) and not isinstance(value, bool) and
            isinstance(value, (int, float)) and math.isfinite(value) and
            value >= 0 and int(value) == value)


def count_state(total, alt):
    """Keep the original primary classification and its missing precedence."""
    if missing(total) or missing(alt):
        return "missing"
    if not valid_count(total) or not valid_count(alt) or alt > total:
        return "invalid"
    return "zero_total" if total == 0 else "valid_exposed"


def count_flags(total, alt):
    """Return independent flags, including missing and invalid at once."""
    has_missing = missing(total) or missing(alt)
    has_invalid = (
        (not missing(total) and not valid_count(total)) or
        (not missing(alt) and not valid_count(alt)) or
        (valid_count(total) and valid_count(alt) and alt > total)
    )
    return {
        "missing": has_missing,
        "invalid": has_invalid,
        "zero_total": count_state(total, alt) == "zero_total",
    }


def specimen_key(row, sample_field):
    values = tuple(row.get(name) for name in (sample_field, "timepoint", "days"))
    if any(missing(value) for value in values) or not isinstance(values[0], str):
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
    for values in iterator:
        if all(missing(value) for value in values):
            continue
        yield dict(zip(header, values))


def _new_count_flags():
    return collections.Counter({"missing": 0, "invalid": 0, "zero_total": 0})


def _record_metadata_row(stats, complete_keys, key_fields, row):
    stats["total_rows"] += 1
    key = tuple(row.get(field) for field in key_fields)
    missing_fields = [field for field, value in zip(key_fields, key) if missing(value)]
    for field in key_fields:
        stats["missing_components"][field] += int(field in missing_fields)
    if missing_fields:
        stats["incomplete_rows"] += 1
        return key, False
    stats["complete_key_rows"] += 1
    complete_keys[key] += 1
    return key, True


def same_time_sample_diagnostics(sv_samples, snv_samples):
    """Count unmatched exact sample keys by patient, without returning keys."""
    sv_by_group = collections.defaultdict(set)
    snv_by_group = collections.defaultdict(set)
    for sample, timepoint, days in sv_samples:
        sv_by_group[(timepoint, days)].add(sample)
    for sample, timepoint, days in snv_samples:
        snv_by_group[(timepoint, days)].add(sample)

    groups = set(sv_by_group) | set(snv_by_group)
    both = set(sv_by_group) & set(snv_by_group)
    groups_with_unmatched = 0
    groups_with_exact_and_unmatched = 0
    groups_without_exact = 0
    sv_unmatched_in_both = 0
    snv_unmatched_in_both = 0
    for group in groups:
        sv_names = sv_by_group.get(group, set())
        snv_names = snv_by_group.get(group, set())
        matched = sv_names & snv_names
        sv_only = sv_names - snv_names
        snv_only = snv_names - sv_names
        if sv_only or snv_only:
            groups_with_unmatched += 1
            if matched:
                groups_with_exact_and_unmatched += 1
        if group in both:
            sv_unmatched_in_both += len(sv_only)
            snv_unmatched_in_both += len(snv_only)
            if not matched:
                groups_without_exact += 1

    return {
        "time_day_groups_present_in_both_sheets": len(both),
        "time_day_groups_with_unmatched_sample_keys": groups_with_unmatched,
        "mixed_groups_with_exact_and_unmatched_sample_keys": groups_with_exact_and_unmatched,
        "time_day_groups_without_any_exact_sample_key": groups_without_exact,
        "sv_sample_keys_without_exact_counterpart": len(sv_samples - snv_samples),
        "snv_sample_keys_without_exact_counterpart": len(snv_samples - sv_samples),
        "sv_unmatched_sample_keys_in_groups_present_in_both_sheets": sv_unmatched_in_both,
        "snv_unmatched_sample_keys_in_groups_present_in_both_sheets": snv_unmatched_in_both,
    }


def build_audit(book, schema, roster, timeline, wgs_counts):
    by_name = {sheet["sheet"]: sheet["fields"] for sheet in schema["sheets"]}
    targets = [name for name in book.sheetnames if re.match(r"^S(?:[1-9]|10) - ", name)]
    if len(targets) != 10:
        raise ValueError("Expected exactly the ten S1-S10 input sheets")

    per = {
        patient: {
            "sheet_rows": collections.Counter(),
            "sv_samples": set(), "snv_samples": set(),
            "sv_exposed": set(), "snv_exposed": set(),
            "sv_types": set(), "snv_types": set(),
            "sv_counts": collections.Counter(), "snv_counts": collections.Counter(),
            "sv_count_flags": _new_count_flags(), "snv_count_flags": _new_count_flags(),
            "sv_background": collections.Counter(), "snv_background": collections.Counter(),
            "sv_background_flags": _new_count_flags(), "snv_background_flags": _new_count_flags(),
            "sv_join": collections.Counter(), "snv_join": collections.Counter(),
            "correction_fields": 0, "yield_rows": 0, "coverage_rows": 0,
        }
        for patient in roster
    }
    rows_seen = collections.Counter()
    missing_patient = collections.Counter()
    outside = collections.defaultdict(set)
    sv_meta = collections.defaultdict(list)
    snv_meta = collections.defaultdict(list)
    sv_complete_keys = collections.Counter()
    snv_complete_keys = collections.Counter()
    metadata_stats = {
        "S9": {"total_rows": 0, "incomplete_rows": 0, "complete_key_rows": 0,
               "missing_components": collections.Counter({"patient": 0, "target_idx": 0})},
        "S10": {"total_rows": 0, "incomplete_rows": 0, "complete_key_rows": 0,
                "missing_components": collections.Counter({"target_idx": 0, "clonality": 0,
                                                             "Hugo_Symbol": 0})},
    }
    pending = {"SV": [], "SNV": []}

    for sheet_name in targets:
        for row in read_rows(book[sheet_name], by_name[sheet_name]):
            rows_seen[sheet_name] += 1
            if sheet_name.startswith("S10 "):
                key, complete = _record_metadata_row(
                    metadata_stats["S10"], snv_complete_keys,
                    ("target_idx", "clonality", "Hugo_Symbol"), row)
                if complete:
                    snv_meta[key].append(row.get("clone_id"))
                continue

            if sheet_name.startswith("S9 "):
                key, complete = _record_metadata_row(
                    metadata_stats["S9"], sv_complete_keys, ("patient", "target_idx"), row)
                if complete:
                    sv_meta[key].append(row.get("clone_id"))

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
                item["correction_fields"] += not missing(row.get("correction"))
            elif sheet_name.startswith(("S7 ", "S8 ")):
                is_sv = sheet_name.startswith("S7 ")
                kind = "sv" if is_sv else "snv"
                spec = specimen_key(row, "sample_id" if is_sv else "sample")
                if spec is not None:
                    item[kind + "_samples"].add(spec)

                state = count_state(row.get("total_counts"), row.get("alt_counts"))
                item[kind + "_counts"][state] += 1
                item[kind + "_count_flags"].update(count_flags(
                    row.get("total_counts"), row.get("alt_counts")))

                background_state = count_state(row.get("total_counts.background"),
                                               row.get("alt_counts.background"))
                item[kind + "_background"][background_state] += 1
                item[kind + "_background_flags"].update(count_flags(
                    row.get("total_counts.background"), row.get("alt_counts.background")))

                if state == "valid_exposed" and spec is not None:
                    item[kind + "_exposed"].add(spec)
                if not missing(row.get("bamtype")):
                    item[kind + "_types"].add(str(row["bamtype"]))
                key = ((patient, row.get("target_idx")) if is_sv else
                       tuple(row.get(field) for field in ("target_idx", "clonality", "Hugo_Symbol")))
                pending["SV" if is_sv else "SNV"].append((patient, key, row.get("clone_id")))

    for kind, metadata in (("SV", sv_meta), ("SNV", snv_meta)):
        for patient, key, observed_clone in pending[kind]:
            counts = per[patient][kind.lower() + "_join"]
            if any(missing(value) for value in key):
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
                if (kind == "SNV" and not missing(observed_clone) and not missing(assigned)
                        and observed_clone != assigned):
                    counts["clone_label_conflict"] += 1

    cases = []
    for patient in roster:
        item = per[patient]
        shared = item["sv_samples"] & item["snv_samples"]
        exposed = item["sv_exposed"] & item["snv_exposed"]
        diagnostics = same_time_sample_diagnostics(item["sv_samples"], item["snv_samples"])
        joined = (item["sv_join"]["unique_with_clone_label"] > 0 and
                  item["snv_join"]["unique_with_clone_label"] > 0)
        conflict = sum(item[kind][name] for kind in ("sv_join", "snv_join")
                       for name in ("missing_key", "unmatched", "ambiguous_metadata",
                                    "clone_label_conflict", "missing_clone_label"))
        marker_status = ("PRESENT" if joined and conflict == 0 else
                         "ABSENT" if not item["sv_join"] or not item["snv_join"] else "UNRESOLVED")
        sheet_rows = dict(item["sheet_rows"])
        statuses = {
            "sample_time_keys": status_pair(item["sv_samples"], item["snv_samples"],
                                             bool(item["sv_counts"]), bool(item["snv_counts"])),
            "marker_to_clone_metadata": marker_status,
            "count_fields_and_units": ("UNRESOLVED" if exposed else
                                       "ABSENT" if not item["sv_counts"] or not item["snv_counts"]
                                       else "UNRESOLVED"),
            "material_and_sequencing_budget": "UNRESOLVED",
            "independent_error_controls": "UNRESOLVED",
            "timing_and_calibration": "UNRESOLVED",
            "separate_molecular_reference": "UNRESOLVED",
            "full_reuse_and_reproducibility": "UNRESOLVED",
        }
        cases.append({
            "patient": patient,
            "in_author_timeline": patient in timeline,
            "author_wgs_specimens_listed": wgs_counts[patient],
            "statuses": statuses,
            "evidence": {
                "sheet_rows": sheet_rows,
                "exact_shared_specimens": len(shared),
                "shared_specimens_with_exposed_numeric_counts": len(exposed),
                "shared_timepoints_without_exact_sample": diagnostics["time_day_groups_without_any_exact_sample_key"],
                "same_time_sample_key_diagnostics": diagnostics,
                "sv_counts": dict(item["sv_counts"]),
                "snv_counts": dict(item["snv_counts"]),
                "sv_count_flags": dict(item["sv_count_flags"]),
                "snv_count_flags": dict(item["snv_count_flags"]),
                "sv_background": dict(item["sv_background"]),
                "snv_background": dict(item["snv_background"]),
                "sv_background_flags": dict(item["sv_background_flags"]),
                "snv_background_flags": dict(item["snv_background_flags"]),
                "sv_marker_join": dict(item["sv_join"]),
                "snv_marker_join": dict(item["snv_join"]),
                "sv_bamtypes": sorted(item["sv_types"]),
                "snv_bamtypes": sorted(item["snv_types"]),
                "coverage_rows": item["coverage_rows"],
                "dna_yield_rows": item["yield_rows"],
                "sv_correction_rows": item["correction_fields"],
            },
        })

    metadata_key_audit = {}
    for sheet_name, stats in metadata_stats.items():
        complete_keys = sv_complete_keys if sheet_name == "S9" else snv_complete_keys
        metadata_key_audit[sheet_name] = {
            "total_rows": stats["total_rows"],
            "incomplete_rows": stats["incomplete_rows"],
            "complete_key_rows": stats["complete_key_rows"],
            "missing_components": dict(stats["missing_components"]),
            "complete_key_duplicate_groups": sum(count > 1 for count in complete_keys.values()),
        }

    return {
        "patients": cases,
        "sheet_row_counts": dict(rows_seen),
        "missing_patient_rows": dict(missing_patient),
        "outside_roster_patient_labels": {name: sorted(values) for name, values in outside.items()},
        "metadata_key_audit": metadata_key_audit,
        "sv_metadata_keys": len(sv_meta),
        "snv_metadata_keys": len(snv_meta),
        "sv_duplicate_metadata_keys": sum(len(values) > 1 for values in sv_meta.values()),
        "snv_duplicate_metadata_keys": sum(len(values) > 1 for values in snv_meta.values()),
    }


def _status_totals(audit):
    if not audit["patients"]:
        return {}
    return {
        name: {value: sum(case["statuses"].get(name) == value for case in audit["patients"])
               for value in ("PRESENT", "ABSENT", "UNRESOLVED")}
        for name in audit["patients"][0]["statuses"]
    }


def _common_aggregates(audit):
    evidence = [case["evidence"] for case in audit["patients"]]
    result = {
        "patient_count": len(audit["patients"]),
        "sample_time_present_patients": sum(case["statuses"]["sample_time_keys"] == "PRESENT"
                                             for case in audit["patients"]),
        "exact_shared_sample_time_keys": sum(row["exact_shared_specimens"] for row in evidence),
        "shared_keys_with_exposed_counts": sum(row["shared_specimens_with_exposed_numeric_counts"]
                                                for row in evidence),
        "patient_status_totals": _status_totals(audit),
        "sv_metadata_keys": audit["sv_metadata_keys"],
        "snv_metadata_keys": audit["snv_metadata_keys"],
        "sv_complete_key_duplicate_groups": audit["sv_duplicate_metadata_keys"],
        "snv_complete_key_duplicate_groups": audit["snv_duplicate_metadata_keys"],
    }
    if evidence and "same_time_sample_key_diagnostics" in evidence[0]:
        result["sv_only_sample_time_keys"] = sum(
            row["same_time_sample_key_diagnostics"]["sv_sample_keys_without_exact_counterpart"]
            for row in evidence)
        result["snv_only_sample_time_keys"] = sum(
            row["same_time_sample_key_diagnostics"]["snv_sample_keys_without_exact_counterpart"]
            for row in evidence)
        result["mixed_same_time_groups"] = sum(
            row["same_time_sample_key_diagnostics"]["mixed_groups_with_exact_and_unmatched_sample_keys"]
            for row in evidence)
    return result


def compare_run02(audit, run02):
    current = _common_aggregates(audit)
    historical = _common_aggregates(run02)
    common_fields = (
        "patient_count", "sample_time_present_patients", "exact_shared_sample_time_keys",
        "shared_keys_with_exposed_counts", "patient_status_totals", "sv_metadata_keys",
        "snv_metadata_keys", "sv_complete_key_duplicate_groups", "snv_complete_key_duplicate_groups",
    )
    return {
        "run02_audit_sha256": sha256_file(RUN02_AUDIT),
        "patient_frame_order_unchanged": [case["patient"] for case in audit["patients"]] ==
                                          [case["patient"] for case in run02["patients"]],
        "patient_statuses_unchanged": [case["statuses"] for case in audit["patients"]] ==
                                       [case["statuses"] for case in run02["patients"]],
        "common_metrics": {
            field: {"run02": historical[field], "run03": current[field],
                    "unchanged": historical[field] == current[field]}
            for field in common_fields
        },
        "run03_unmatched_sample_metrics": {
            "sv_only_sample_time_keys": current["sv_only_sample_time_keys"],
            "snv_only_sample_time_keys": current["snv_only_sample_time_keys"],
            "mixed_same_time_groups": current["mixed_same_time_groups"],
        },
    }


def run_audit():
    fingerprints = collect_pre_read_fingerprints()
    verify_pre_read_gate(fingerprints)

    # Read and validate metadata only after the frozen pre-read gate passes.
    config_text = CONFIG.read_text()
    roster, timeline, wgs = (
        config_items(config_text, name) for name in ("patients", "patients_timeline", "patient_wgs")
    )
    if (len(roster) != 24 or len(timeline) != 18 or len(wgs) != 12 or
            len(set(roster)) != 24 or not set(timeline) <= set(roster)):
        raise ValueError("Author roster or nested list does not match the frozen frame")
    wgs_patients = []
    for sample in wgs:
        match = re.fullmatch(r"(SPECTRUM-OV-\d+)_.*", sample)
        if not match or match.group(1) not in roster:
            raise ValueError("Unresolved author WGS sample identifier")
        wgs_patients.append(match.group(1))
    if len(set(wgs_patients)) != 6:
        raise ValueError("Author WGS patient count does not match the frozen frame")
    schema = json.loads(SCHEMA.read_text())

    # This is the first workbook open. Only S1-S10 rows are iterated below.
    book = open_verified_workbook(fingerprints)
    try:
        audit = build_audit(book, schema, roster, set(timeline), collections.Counter(wgs_patients))
    finally:
        book.close()

    run02 = json.loads(RUN02_AUDIT.read_text())
    audit["run02_comparison"] = compare_run02(audit, run02)
    audit.update({
        "workbook_sha256": fingerprints["workbook_sha256"],
        "author_config_sha256": fingerprints["author_config_sha256"],
        "author_commit": fingerprints["author_checkout_commit"],
        "author_checkout_clean": fingerprints["author_checkout_clean"],
        "analysis_repo_head": fingerprints["analysis_repo_head"],
        "preregistration_is_ancestor": fingerprints["preregistration_is_ancestor"],
        "schema_sha256": fingerprints["schema_sha256"],
        "schema_receipt_sha256": fingerprints["schema_receipt_sha256"],
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
        "protocol_sha256": sha256_file(PROTOCOL),
        "independent_review_sha256": sha256_file(REVIEW),
        "original_audit_sha256": sha256_file(ORIGINAL_AUDIT),
        "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "python": sys.version,
        "openpyxl": openpyxl.__version__,
        "limits": ("S1-S10 identifiers, metadata completeness, count validity and field presence only; "
                   "no S11-S14 rows, allele fractions, arm/outcome comparisons, WGS signals, "
                   "imputation or biological-truth inference."),
    })
    return audit, fingerprints


def render_readme(audit):
    metadata = audit["metadata_key_audit"]
    s9, s10 = metadata["S9"], metadata["S10"]
    comparison = audit["run02_comparison"]
    unchanged = all(value["unchanged"] for value in comparison["common_metrics"].values())
    diagnostics = comparison["run03_unmatched_sample_metrics"]
    return (
        "# CloneSeq content audit — run 03\n\n"
        "This run applies the reporting corrections preregistered in commit `3d04c13`. "
        "It uses the frozen workbook, author configuration, 24-patient frame and schema.\n\n"
        f"- S9 metadata rows: {s9['total_rows']}; incomplete rows: {s9['incomplete_rows']}; "
        f"missing components: `{json.dumps(s9['missing_components'], sort_keys=True)}`.\n"
        f"- S10 metadata rows: {s10['total_rows']}; incomplete rows: {s10['incomplete_rows']}; "
        f"missing components: `{json.dumps(s10['missing_components'], sort_keys=True)}`.\n"
        f"- Duplicate complete metadata key groups: S9 {s9['complete_key_duplicate_groups']}; "
        f"S10 {s10['complete_key_duplicate_groups']}. Incomplete keys are not matches.\n"
        f"- Exact patient/sample/time/day matches: "
        f"{comparison['common_metrics']['sample_time_present_patients']['run03']} patients and "
        f"{comparison['common_metrics']['exact_shared_sample_time_keys']['run03']} keys. "
        f"Unmatched keys: SV {diagnostics['sv_only_sample_time_keys']}; "
        f"SNV {diagnostics['snv_only_sample_time_keys']}; mixed same-time groups "
        f"{diagnostics['mixed_same_time_groups']}.\n"
        f"- Common run02 aggregate metrics and patient statuses unchanged: {str(unchanged).lower()}.\n"
        "- Missing and invalid count flags are independent. Primary count categories are retained. "
        "No zero is imputed.\n\n"
        "The audit reports metadata and key availability. It does not establish biological truth. "
        "It reads S1-S10 only. It does not inspect S11-S14 clinical rows, calculate allele fractions, "
        "compare arms or outcomes, or access WGS signals. `audit.json` contains aggregate diagnostics "
        "and the fixed patient frame; it contains no specimen or target keys. `receipt.json` records "
        "the invocation, runtime, source/input/output hashes and any exception.\n"
    )


def main():
    started = time.monotonic()
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    prior_preflight_failure = None
    if OUT.exists():
        prior_receipt = OUT / "receipt.json"
        present_files = {path.name for path in OUT.iterdir() if path.is_file()}
        if present_files != {"receipt.json"} or not prior_receipt.is_file():
            raise FileExistsError("Run03 output directory already contains results")
        previous = json.loads(prior_receipt.read_text())
        message = (previous.get("exception") or {}).get("message", "")
        if not message.startswith("Frozen pre-read verification failed:"):
            raise FileExistsError("Run03 output directory is not a pre-read failure packet")
        prior_preflight_failure = {
            "invocation_argv": previous.get("invocation_argv"),
            "runtime_seconds": previous.get("runtime_seconds"),
            "finished_utc": previous.get("finished_utc"),
            "exception": previous.get("exception"),
            "workbook_opened": False,
        }
    else:
        OUT.mkdir(parents=True, exist_ok=False)
    source_paths = {
        "audit_script": pathlib.Path(__file__),
        "protocol": PROTOCOL,
        "independent_review": REVIEW,
        "original_audit": ORIGINAL_AUDIT,
    }
    receipt = {
        "invocation_argv": sys.argv,
        "started_utc": started_utc,
        "runtime_seconds": None,
        "runtime": {"python": sys.version, "openpyxl": openpyxl.__version__},
        "source_sha256": {name: sha256_file(path) for name, path in source_paths.items()},
        "input_sha256": {},
        "checkout": {"preregistration_commit": PREREGISTRATION_COMMIT,
                     "author_commit_expected": AUTHOR_COMMIT},
        "output_sha256": {},
        "exception": None,
        "prior_preflight_failures": ([prior_preflight_failure]
                                      if prior_preflight_failure is not None else []),
    }
    try:
        audit, fingerprints = run_audit()
        receipt["input_sha256"] = {
            "workbook": fingerprints["workbook_sha256"],
            "author_config": fingerprints["author_config_sha256"],
            "schema": fingerprints["schema_sha256"],
            "schema_receipt": fingerprints["schema_receipt_sha256"],
            "run02_audit": sha256_file(RUN02_AUDIT),
        }
        receipt["checkout"].update({
            "analysis_repo_head": fingerprints["analysis_repo_head"],
            "author_checkout_commit": fingerprints["author_checkout_commit"],
            "author_checkout_clean": fingerprints["author_checkout_clean"],
            "preregistration_is_ancestor": fingerprints["preregistration_is_ancestor"],
        })
        audit_path = OUT / "audit.json"
        readme_path = OUT / "README.md"
        audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
        readme_path.write_text(render_readme(audit))
        receipt["output_sha256"] = {
            "audit.json": sha256_file(audit_path),
            "README.md": sha256_file(readme_path),
        }
        evidence = [case["evidence"] for case in audit["patients"]]
        print("Patient frame", len(audit["patients"]),
              "exact shared keys", sum(row["exact_shared_specimens"] for row in evidence),
              "S10 incomplete metadata rows", audit["metadata_key_audit"]["S10"]["incomplete_rows"])
    except Exception as exc:
        receipt["exception"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        raise
    finally:
        receipt["runtime_seconds"] = round(time.monotonic() - started, 6)
        receipt["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
