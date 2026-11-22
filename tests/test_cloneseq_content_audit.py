"""Checks for missing data, ambiguous joins and assay-unit boundaries."""

import collections
import importlib.util
import math
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "analysis/audit_cloneseq_content.py"
spec = importlib.util.spec_from_file_location("audit_cloneseq_content", MODULE_PATH)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


def test_count_validation_does_not_treat_missing_as_zero():
    assert audit.count_state(None, 0) == "missing"
    assert audit.count_state(0, 0) == "zero_total"
    assert audit.count_state(10, 0) == "valid_exposed"
    for total, alt in [(10, 11), (-1, 0), (1.5, 1), (math.nan, 0), (True, 0)]:
        assert audit.count_state(total, alt) == "invalid"


def test_specimen_matching_requires_exact_sample_and_time():
    a = audit.specimen_key({"sample_id": "S1", "timepoint": 1, "days": 0}, "sample_id")
    b = audit.specimen_key({"sample": "S1 ", "timepoint": 1, "days": 0}, "sample")
    assert audit.status_pair({a}, {b}, True, True) == "UNRESOLVED"
    assert audit.status_pair({a}, {a}, True, True) == "PRESENT"
    assert audit.status_pair(set(), {a}, True, True) == "UNRESOLVED"
    assert audit.status_pair(set(), {a}, False, True) == "ABSENT"


class Sheet:
    def __init__(self, title, fields, rows):
        self.title, self.fields, self.rows = title, fields, rows

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


def example(duplicate_snv=False, conflicting_snv=False, missing_snv_clone=False):
    patient = "P1"
    fields = {
        "S1 - Coverage": ["patient"],
        "S2 - Tumor Fractions": ["patient", "dna_yield"],
        "S3 - Clone frequencies (SVs)": ["patient"],
        "S4 - Clone frequencies (SNVs)": ["patient"],
        "S5 - Clone features": ["patient"],
        "S6 - Error rates & LOD": ["patient"],
        "S7 - SV read counts": ["patient", "sample_id", "timepoint", "days", "target_idx", "bamtype", "total_counts", "alt_counts", "total_counts.background", "alt_counts.background"],
        "S8 - SNV read counts": ["patient", "sample", "timepoint", "days", "target_idx", "bamtype", "clonality", "Hugo_Symbol", "clone_id", "total_counts", "alt_counts", "total_counts.background", "alt_counts.background"],
        "S9 - SV metadata": ["patient", "target_idx", "clone_id", "correction"],
        "S10 - SNV metadata": ["target_idx", "clonality", "Hugo_Symbol", "clone_id"],
    }
    sv = {"patient": patient, "sample_id": "S1", "timepoint": 1, "days": 0, "target_idx": "sv1", "bamtype": "raw", "total_counts": 10, "alt_counts": 0}
    snv = {"patient": patient, "sample": "S1", "timepoint": 1, "days": 0, "target_idx": "snv1", "bamtype": "duplex", "clonality": "subclonal", "Hugo_Symbol": "GENE", "clone_id": "B" if conflicting_snv else "A", "total_counts": 8, "alt_counts": 0}
    svmeta = {"patient": patient, "target_idx": "sv1", "clone_id": "A", "correction": 1}
    snvmeta = {"target_idx": "snv1", "clonality": "subclonal", "Hugo_Symbol": "GENE", "clone_id": None if missing_snv_clone else "A"}
    inputs = {"S7 - SV read counts": [sv], "S8 - SNV read counts": [snv], "S9 - SV metadata": [svmeta], "S10 - SNV metadata": [snvmeta] * (2 if duplicate_snv else 1)}
    sheets = [Sheet(name, columns, inputs.get(name, [])) for name, columns in fields.items()]
    schema = {"sheets": [{"sheet": name, "fields": cols} for name, cols in fields.items()]}
    return audit.build_audit(Book(sheets), schema, [patient], set(), collections.Counter())


def test_joined_columns_do_not_become_truth_or_equal_budgets():
    patient = example()["patients"][0]
    assert patient["statuses"]["sample_time_keys"] == "PRESENT"
    assert patient["statuses"]["marker_to_clone_metadata"] == "PRESENT"
    assert patient["statuses"]["separate_molecular_reference"] == "UNRESOLVED"
    assert patient["statuses"]["material_and_sequencing_budget"] == "UNRESOLVED"


def test_duplicate_metadata_is_ambiguous_even_if_rows_are_identical():
    patient = example(duplicate_snv=True)["patients"][0]
    assert patient["statuses"]["marker_to_clone_metadata"] == "UNRESOLVED"
    assert patient["evidence"]["snv_marker_join"]["ambiguous_metadata"] == 1


def test_conflicting_clone_assignments_remain_unresolved():
    patient = example(conflicting_snv=True)["patients"][0]
    assert patient["statuses"]["marker_to_clone_metadata"] == "UNRESOLVED"
    assert patient["evidence"]["snv_marker_join"]["clone_label_conflict"] == 1


def test_missing_clone_label_does_not_count_as_linked_clone():
    patient = example(missing_snv_clone=True)["patients"][0]
    assert patient["statuses"]["marker_to_clone_metadata"] == "UNRESOLVED"
    assert patient["evidence"]["snv_marker_join"]["missing_clone_label"] == 1
