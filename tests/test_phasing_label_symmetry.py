import math

import pytest

from analysis.probe_phasing_label_symmetry import posterior, producer_endpoint, run_probes, swap


def test_endpoint_counterexample_changes_gt_and_gq():
    result = run_probes()["fixtures"]["endpoints_six_ref_one_alt"]
    assert result["zero_as_missing"]["original"]["gt"] == "0/1"
    assert result["zero_as_missing"]["swapped"]["gt"] == "0/0"
    assert result["zero_as_missing"]["original"]["gq"] == 14
    assert result["zero_as_missing"]["swapped"]["gq"] == 3
    corrected = result["zero_is_probability"]
    assert corrected["original"] == corrected["swapped"]
    assert corrected["original"]["gq"] == 17


@pytest.mark.parametrize("name", ["interior_six_ref_one_alt", "missing_six_ref_one_alt",
                                 "unphased_half_six_ref_one_alt"])
def test_negative_controls(name):
    modes = run_probes()["fixtures"][name]
    for pair in modes.values():
        assert pair["original"]["gt"] == pair["swapped"]["gt"]
        assert pair["original"]["gq"] == pair["swapped"]["gq"]
        assert pair["original"]["posterior_before_output_floor"] == pytest.approx(
            pair["swapped"]["posterior_before_output_floor"], rel=0, abs=1e-14)
    assert modes["zero_as_missing"]["original"] == modes["zero_is_probability"]["original"]


def test_explicit_missing_differs_from_zero():
    assert posterior([(0, None), (1, 1)], False) != posterior([(0, 0), (1, 1)], False)
    assert posterior([(0, None), (1, 1)], True) == posterior([(0, 0), (1, 1)], True)


def test_corrected_symmetry_grid():
    for p in (0, 0.01, 0.5, 0.99, 1, None):
        for q in (0, 0.01, 0.5, 0.99, 1, None):
            reads = [(0, p)] * 6 + [(1, q)]
            a, b = posterior(reads, False), posterior(swap(reads), False)
            assert a["gt"] == b["gt"]
            assert a["posterior_before_output_floor"] == pytest.approx(
                b["posterior_before_output_floor"], rel=0, abs=1e-14)
            assert math.isclose(sum(a["posterior_before_output_floor"]), 1)


def test_independent_endpoint_posterior_anchor():
    # Analytic likelihoods with six REF on hap1 and one ALT on hap2.
    hom_ref = 0.99 ** 6 * 0.01
    het = (0.99 ** 7 + 0.01 ** 7) / 2
    hom_alt = 0.01 ** 6 * 0.99
    total = hom_ref + het + hom_alt
    observed = posterior([(0, 1)] * 6 + [(1, 0)], False)
    assert observed["posterior_before_output_floor"] == pytest.approx(
        [hom_ref / total, het / total, hom_alt / total], rel=0, abs=1e-14)


def test_missing_equals_half_probability():
    for mode in (False, True):
        assert posterior([(0, None)] * 6 + [(1, None)], mode) == posterior(
            [(0, 0.5)] * 6 + [(1, 0.5)], mode)


def test_source_formula_can_round_to_endpoint_without_underflow():
    result = producer_endpoint()
    assert result["favored_haplotype_likelihood"] > 0
    assert result["other_haplotype_likelihood"] > 0
    assert result["binary64_confidence"] == 1
    assert result["opposite_raw_ratio"] > 0
    assert result["opposite_folded_confidence"] == 1
    assert result["parsed_haplotype2_probability"] == 0


@pytest.mark.parametrize("reads", [[], [(2, 0.5)], [(0, -0.1)], [(1, 1.1)], [(0, math.nan)]])
def test_invalid_inputs(reads):
    with pytest.raises(ValueError):
        posterior(reads, False)
