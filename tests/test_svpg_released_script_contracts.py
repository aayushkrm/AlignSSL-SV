"""Synthetic tests for the pinned SVPG replicate-evaluator contract."""

import pytest

from analysis.probe_svpg_released_script_contracts import (
    SOURCE_ARCHIVE,
    SyntheticCall,
    compare_callsets,
    inspect_pinned_source,
    phase_gt,
    retained_by_released_contract,
    run_probe,
)


@pytest.mark.parametrize(
    ("genotype", "expected"),
    [("0/1", "het"), ("1/0", "het"), ("1/1", "hom"), ("0|1", "unknown")],
)
def test_unphased_genotype_mapping_and_phased_exclusion(genotype, expected):
    call = SyntheticCall("chr1", 100, 199, "DEL", 100, genotype)
    assert phase_gt(genotype) == expected
    assert retained_by_released_contract(call) is (expected != "unknown")


def test_gt_disagreement_is_counted_as_an_event_match_with_zero_inconsistency():
    result = run_probe()["genotype_mismatch_counterexample"]
    assert result["call_a_genotype_class"] == "het"
    assert result["call_b_genotype_class"] == "hom"
    assert result["genotypes_agree"] is False
    assert result["candidate_records"] == 1
    assert result["event_matches"] == 1
    assert result["event_inconsistency"] == 0


def test_phased_candidate_is_excluded_before_event_counting():
    result = run_probe()["phased_call"]
    assert result["genotype_class"] == "unknown"
    assert result["retained"] is False
    assert result["candidate_records"] == 0
    assert result["event_matches"] == 0


@pytest.mark.parametrize(
    "control",
    [
        "genuine_no_overlap",
        "type_mismatch",
        "chromosome_mismatch",
        "length_ratio_below_bias",
    ],
)
def test_geometry_and_identity_negative_controls_remain_unmatched(control):
    result = run_probe()["negative_controls"][control]
    assert result["candidate_records"] == 1
    assert result["event_matches"] == 0
    assert result["event_inconsistency"] == 1


def test_independent_comparator_keeps_the_directional_candidate_count():
    candidate = SyntheticCall("chr1", 500, 599, "DEL", 100, "1/1")
    unrelated = SyntheticCall("chr1", 5_000, 5_099, "DEL", 100, "0/1")
    assert compare_callsets([unrelated], [candidate]) == {
        "candidate_records": 1,
        "event_matches": 0,
        "event_inconsistency": 1,
        "candidate_genotype_classes": ["hom"],
    }


@pytest.mark.skipif(
    not SOURCE_ARCHIVE.is_file(),
    reason="optional pinned external source archive is absent",
)
def test_pinned_source_hashes_and_static_ast_contract():
    report = inspect_pinned_source()
    assert report["archive"]["bytes"] == 18_200
    assert report["archive"]["sha256"] == (
        "cc7f077cee6a1e0c503aa21d04e935feae44f79ee32857343017bdb16215091e"
    )
    assert report["source_parsed_as_data_only"] is True
    assert report["source_compiled_or_executed"] is False
    assert all(report["ast_contracts"].values())


def test_reproducer_declares_synthetic_scope_and_no_source_execution():
    report = run_probe()
    assert "Synthetic" in report["scope"]
    assert report["source_execution"] is False


def test_wrong_size_archive_is_rejected_before_payload_read(tmp_path, monkeypatch):
    path = tmp_path / "wrong-size.zip"
    path.write_bytes(b"not a source archive")

    def forbidden_open(*args, **kwargs):
        raise AssertionError("wrong-size payload must not be read")

    monkeypatch.setattr(type(path), "open", forbidden_open)
    with pytest.raises(ValueError, match="size mismatch before read"):
        inspect_pinned_source(path)


def test_same_size_wrong_hash_archive_is_rejected(tmp_path):
    path = tmp_path / "wrong-hash.zip"
    path.write_bytes(b"x" * 18_200)
    with pytest.raises(ValueError, match="identity mismatch"):
        inspect_pinned_source(path)
