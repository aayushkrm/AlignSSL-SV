"""Contract tests for bounded synthetic probes, not biological validation."""

import pytest

from analysis.probe_ensemble_semantics import (
    Variant,
    fp_position_clusters,
    retrospective_calls,
    run_probes,
    vote_counts,
)


def test_symbolic_key_does_not_retain_end():
    a = Variant("chr1", 100, "N", "<DEL>", 200, "DEL")
    b = Variant("chr1", 100, "N", "<DEL>", 1000, "DEL")
    assert a != b
    assert a.upstream_key() == b.upstream_key()


def test_fp_single_linkage_can_span_more_than_window_and_ignore_type():
    keys = {("chr1", 100, "N", "<DEL>"), ("chr1", 145, "N", "<INS>"),
            ("chr1", 190, "N", "<DUP>")}
    assert fp_position_clusters(keys) == {("chr1", 100, "N", "<DEL>")}


def test_fp_clusters_do_not_cross_chromosomes_or_large_gap():
    keys = {("chr1", 100, "N", "<DEL>"), ("chr1", 151, "N", "<INS>"),
            ("chr2", 100, "N", "<DUP>")}
    assert fp_position_clusters(keys) == keys
    assert fp_position_clusters(set()) == set()
    with pytest.raises(ValueError):
        fp_position_clusters(keys, -1)


def test_truth_partition_changes_retrospective_output_not_predictions():
    raw = {("chr1", 100, "N", "<DEL>"), ("chr1", 120, "N", "<DEL>")}
    before = raw.copy()
    all_fp = retrospective_calls(set(), raw)
    one_tp = retrospective_calls({("chr1", 101, "N", "<DEL>")},
                                  {("chr1", 120, "N", "<DEL>")})
    assert raw == before
    assert len(all_fp) == 1 and len(one_tp) == 2
    assert all_fp != one_tp


def test_asymmetric_consensus_counts_a_rejected_fp():
    result = vote_counts({"true": 2, "false": 1}, {"true"})
    assert result["fp_at_any_support"] == 1
    assert result["fp_at_required_support"] == 0
    assert result["retrospective_precision"] == 0.5
    assert result["consistent_support_precision"] == 1.0
    assert vote_counts({}, set())["retrospective_precision"] is None
    with pytest.raises(ValueError):
        vote_counts({}, set(), support=0)


def test_probe_report_preserves_its_scientific_limits():
    report = run_probes()
    assert report["symbolic_key_collision"]["four_field_key_count"] == 1
    assert report["truth_conditioned_output"]["output_changes_with_truth_partition"]
    assert not report["position_only_fp_chain"]["allele_equivalence_tested"]
    assert any("No real VCF" in limit for limit in report["limits"])
    assert any("novelty" in limit for limit in report["limits"])
