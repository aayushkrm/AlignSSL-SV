"""Focused synthetic checks for the preregistered run03 corrections."""

import collections
import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "analysis/audit_cloneseq_content_v3.py"
spec = importlib.util.spec_from_file_location("audit_cloneseq_content_v3", MODULE_PATH)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


class Sheet:
    def __init__(self, title, fields, rows):
        self.title = title
        self.fields = fields
        self.rows = rows

    def iter_rows(self, values_only=True):
        yield tuple(self.fields)
        for row in self.rows:
            yield tuple(row.get(field) for field in self.fields)


class Book:
    def __init__(self, sheets):
        self.sheets = {sheet.title: sheet for sheet in sheets}
        self.sheetnames = list(self.sheets)

    def __getitem__(self, title):
        return self.sheets[title]


def synthetic_audit():
    patient = "P_SYN"
    fields = {
        "S1 - Coverage": ["patient"],
        "S2 - Tumor Fractions": ["patient", "dna_yield"],
        "S3 - Clone frequencies (SVs)": ["patient"],
        "S4 - Clone frequencies (SNVs)": ["patient"],
        "S5 - Clone features": ["patient"],
        "S6 - Error rates & LOD": ["patient"],
        "S7 - SV read counts": ["patient", "sample_id", "timepoint", "days", "target_idx",
                                "bamtype", "total_counts", "alt_counts",
                                "total_counts.background", "alt_counts.background"],
        "S8 - SNV read counts": ["patient", "sample", "timepoint", "days", "target_idx",
                                 "bamtype", "clonality", "Hugo_Symbol", "clone_id",
                                 "total_counts", "alt_counts", "total_counts.background",
                                 "alt_counts.background"],
        "S9 - SV metadata": ["patient", "target_idx", "clone_id", "correction"],
        "S10 - SNV metadata": ["target_idx", "clonality", "Hugo_Symbol", "clone_id"],
    }
    sv_row = {
        "patient": patient, "sample_id": "SYN_SHARED", "timepoint": 1, "days": 0,
        "target_idx": "SYN_SV_TARGET", "bamtype": "raw", "total_counts": 10,
        "alt_counts": 0, "total_counts.background": 8, "alt_counts.background": 0,
    }
    sv_mixed = {
        **sv_row, "sample_id": "SYN_SV_EXTRA", "total_counts": None, "alt_counts": -1,
        "total_counts.background": None, "alt_counts.background": -1,
    }
    snv_row = {
        "patient": patient, "sample": "SYN_SHARED", "timepoint": 1, "days": 0,
        "target_idx": "SYN_SNV_TARGET", "bamtype": "duplex", "clonality": "subclonal",
        "Hugo_Symbol": "GENE", "clone_id": "A", "total_counts": 8, "alt_counts": 0,
        "total_counts.background": 6, "alt_counts.background": 0,
    }
    snv_incomplete = {
        **snv_row, "sample": "SYN_SNV_EXTRA", "target_idx": "SYN_SNV_INCOMPLETE",
        "Hugo_Symbol": None, "total_counts": 3, "alt_counts": 0,
    }
    sv_meta = [
        {"patient": patient, "target_idx": "SYN_SV_TARGET", "clone_id": "A", "correction": 1},
        {"patient": patient, "target_idx": "SYN_SV_TARGET", "clone_id": "A", "correction": 1},
        {"patient": patient, "target_idx": None, "clone_id": "A", "correction": 1},
        {"patient": None, "target_idx": "SYN_ORPHAN", "clone_id": "A", "correction": 1},
    ]
    snv_meta = [
        {"target_idx": "SYN_SNV_TARGET", "clonality": "subclonal", "Hugo_Symbol": "GENE", "clone_id": "A"},
        {"target_idx": "SYN_SNV_TARGET", "clonality": "subclonal", "Hugo_Symbol": "GENE", "clone_id": "A"},
        {"target_idx": "SYN_SNV_INCOMPLETE", "clonality": "subclonal", "Hugo_Symbol": None, "clone_id": "A"},
        {"target_idx": "SYN_SNV_OTHER", "clonality": None, "Hugo_Symbol": "GENE2", "clone_id": "A"},
    ]
    row_inputs = {
        "S7 - SV read counts": [sv_row, sv_mixed],
        "S8 - SNV read counts": [snv_row, snv_incomplete],
        "S9 - SV metadata": sv_meta,
        "S10 - SNV metadata": snv_meta,
    }
    sheets = [Sheet(name, columns, row_inputs.get(name, [])) for name, columns in fields.items()]
    schema = {"sheets": [{"sheet": name, "fields": columns} for name, columns in fields.items()]}
    return audit.build_audit(Book(sheets), schema, [patient], set(), collections.Counter())


def test_incomplete_metadata_is_counted_and_complete_duplicates_stay_separate():
    result = synthetic_audit()
    s9 = result["metadata_key_audit"]["S9"]
    s10 = result["metadata_key_audit"]["S10"]

    assert (s9["total_rows"], s9["incomplete_rows"], s9["complete_key_rows"]) == (4, 2, 2)
    assert s9["missing_components"] == {"patient": 1, "target_idx": 1}
    assert s9["complete_key_duplicate_groups"] == 1
    assert (s10["total_rows"], s10["incomplete_rows"], s10["complete_key_rows"]) == (4, 2, 2)
    assert s10["missing_components"] == {"target_idx": 0, "clonality": 1, "Hugo_Symbol": 1}
    assert s10["complete_key_duplicate_groups"] == 1

    patient = result["patients"][0]
    assert patient["evidence"]["sv_marker_join"]["ambiguous_metadata"] == 2
    assert patient["evidence"]["snv_marker_join"]["ambiguous_metadata"] == 1
    assert patient["evidence"]["snv_marker_join"]["missing_key"] == 1
    assert patient["statuses"]["marker_to_clone_metadata"] == "UNRESOLVED"

    serialized = json.dumps(result)
    for key in ("SYN_SHARED", "SYN_SV_TARGET", "SYN_SNV_TARGET", "SYN_SNV_INCOMPLETE"):
        assert key not in serialized


def test_mixed_same_time_group_counts_unmatched_sample_keys_on_both_sides():
    result = synthetic_audit()
    evidence = result["patients"][0]["evidence"]

    assert evidence["exact_shared_specimens"] == 1
    assert evidence["shared_timepoints_without_exact_sample"] == 0
    assert evidence["same_time_sample_key_diagnostics"] == {
        "time_day_groups_present_in_both_sheets": 1,
        "time_day_groups_with_unmatched_sample_keys": 1,
        "mixed_groups_with_exact_and_unmatched_sample_keys": 1,
        "time_day_groups_without_any_exact_sample_key": 0,
        "sv_sample_keys_without_exact_counterpart": 1,
        "snv_sample_keys_without_exact_counterpart": 1,
        "sv_unmatched_sample_keys_in_groups_present_in_both_sheets": 1,
        "snv_unmatched_sample_keys_in_groups_present_in_both_sheets": 1,
    }


def test_missing_and_invalid_count_flags_are_independent_and_primary_state_is_retained():
    assert audit.count_state(None, -1) == "missing"
    assert audit.count_flags(None, -1) == {
        "missing": True, "invalid": True, "zero_total": False,
    }
    assert audit.count_state(0, 0) == "zero_total"
    assert audit.count_flags(0, 0) == {
        "missing": False, "invalid": False, "zero_total": True,
    }
    assert audit.count_state(10, 0) == "valid_exposed"
    assert audit.count_state(math.nan, 0) == "invalid"

    evidence = synthetic_audit()["patients"][0]["evidence"]
    assert evidence["sv_counts"] == {"valid_exposed": 1, "missing": 1}
    assert evidence["sv_count_flags"] == {"missing": 1, "invalid": 1, "zero_total": 0}
    assert evidence["sv_background"]["missing"] == 1
    assert evidence["sv_background_flags"]["missing"] == 1
    assert evidence["sv_background_flags"]["invalid"] == 1


def test_failed_pre_read_hash_gate_does_not_open_workbook():
    fingerprints = {
        "workbook_sha256": audit.WORKBOOK_SHA,
        "author_config_sha256": audit.CONFIG_SHA,
        "schema_sha256": "0" * 64,
        "schema_receipt_schema_sha256": audit.SCHEMA_SHA,
        "schema_receipt_workbook_sha256": audit.WORKBOOK_SHA,
        "author_checkout_commit": audit.AUTHOR_COMMIT,
        "author_checkout_clean": True,
        "analysis_repo_head": audit.PREREGISTRATION_COMMIT,
        "preregistration_is_ancestor": True,
    }
    opened = []

    def loader(*args, **kwargs):
        opened.append((args, kwargs))
        raise AssertionError("workbook loader must not run after a failed hash gate")

    with pytest.raises(ValueError, match="Frozen pre-read verification failed: schema_sha256"):
        audit.open_verified_workbook(fingerprints, workbook_path="synthetic.xlsx", loader=loader)
    assert opened == []
