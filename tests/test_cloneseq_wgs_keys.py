"""Ensure the WGS-reference key check does not guess sample matches."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from check_cloneseq_wgs_keys import classify


def test_unique_exact_wgs_key_can_link_both_count_tables():
    sample = "SPECTRUM-OV-001_example"
    key = ("SPECTRUM-OV-001", sample, 2, 100)
    result = classify([sample], [key], {key}, {key})
    assert result["sample_status_counts"] == {"both_count_sheets": 1}
    assert result["patients_with_both_count_sheet_keys"] == 1


def test_duplicate_mapping_and_different_day_do_not_become_matches():
    sample = "SPECTRUM-OV-001_example"
    key = ("SPECTRUM-OV-001", sample, 2, 100)
    duplicated = classify([sample], [key, key], {key}, {key})
    assert duplicated["sample_status_counts"] == {"duplicate_S2_sample": 1}
    other_day = ("SPECTRUM-OV-001", sample, 2, 101)
    partial = classify([sample], [key], {key}, {other_day})
    assert partial["sample_status_counts"] == {"SV_only": 1}
