import hashlib

import pytest

from analysis.released_truth_units import (
    ScreenObservation,
    classify_truth_record,
    contains_interval,
    intersect_bed,
    joint_block_bootstrap,
    is_autosome,
    merge_bed,
    subtract_bed,
    territory_sets,
    territory_status,
    TerritoryIndex,
    truth_identity,
)


SOURCE = "a" * 64


def classify(ref, alt, gt="0/1", *, ordinal=1, pos=2501, chrom="chr1"):
    return classify_truth_record(SOURCE, ordinal, chrom, pos, ref, alt, gt)


def test_identity_is_stable_and_keeps_duplicate_rows_distinct():
    expected = hashlib.sha256(f"{SOURCE}|1".encode()).hexdigest()
    assert truth_identity(SOURCE, 1) == expected
    assert truth_identity(SOURCE.upper(), 1) == expected
    assert truth_identity(SOURCE, 1) != truth_identity(SOURCE, 2)
    first = classify("A", "A" + "C" * 50, ordinal=1)
    duplicate = classify("A", "A" + "C" * 50, ordinal=2)
    assert first.unit and duplicate.unit
    assert first.unit.alt == duplicate.unit.alt
    assert first.identity != duplicate.identity


def test_maximal_suffix_then_prefix_and_50bp_indel_boundary():
    insertion = classify("ACA", "AC" + "G" * 50 + "A", "0|1")
    deletion = classify("AC" + "G" * 50 + "A", "ACA", "1|0")
    too_short = classify("A", "A" + "C" * 49)
    assert insertion.unit and (insertion.unit.kind, insertion.unit.length) == ("INS", 50)
    assert deletion.unit and (deletion.unit.kind, deletion.unit.length) == ("DEL", 50)
    assert insertion.unit.gt == "0|1" and insertion.unit.phased
    assert deletion.unit.gt == "1|0" and deletion.unit.phased
    assert too_short.exclusion_reason == "below_min_length"


def test_large_common_prefix_and_suffix_trim_without_repeated_slicing():
    prefix, suffix, inserted = "A" * 100_000, "C" * 100_000, "G" * 50
    insertion = classify(prefix + suffix, prefix + inserted + suffix)
    deletion = classify(prefix + inserted + suffix, prefix + suffix)
    assert insertion.unit and (insertion.unit.kind, insertion.unit.length) == ("INS", 50)
    assert deletion.unit and (deletion.unit.kind, deletion.unit.length) == ("DEL", 50)


@pytest.mark.parametrize(
    ("chrom", "expected"),
    [("1", True), ("22", True), ("chr1", True), ("chr22", True),
     ("chr01", False), ("01", False), ("chr23", False), ("chrX", False),
     ("１", False), ("chr１", False)],
)
def test_autosome_names_are_explicit_and_ascii(chrom, expected):
    assert is_autosome(chrom) is expected


@pytest.mark.parametrize(
    ("ref", "alt", "gt", "reason"),
    [
        ("A", "A," + "C" * 50, "0/1", "multiallelic"),
        ("A", "<DEL>", "0/1", "symbolic_or_star"),
        ("A", "*", "0/1", "symbolic_or_star"),
        ("A", "N" * 50, "0/1", "ambiguous_base"),
        ("A", "A" + "C" * 50, "0|.", "missing_or_partial_gt"),
        ("A", "A" + "C" * 50, "1", "non_diploid_gt"),
        ("A", "A" + "C" * 50, "0/0", "reference_only"),
        ("AC" + "G" * 50, "AT" + "G" * 50, "0/1", "complex_replacement"),
    ],
)
def test_exclusions_are_named_and_never_imputed(ref, alt, gt, reason):
    result = classify(ref, alt, gt)
    assert result.unit is None
    assert result.exclusion_reason == reason


def test_full_anchored_span_and_mixed_territory_boundary():
    unit = classify("A", "A" + "C" * 50).unit
    assert unit
    assert unit.full_span() == ("chr1", 500, 4501)
    adjacent = [("chr1", 0, 2_000), ("chr1", 2_000, 5_000)]
    assert territory_status(unit, adjacent) == "eligible"
    index = TerritoryIndex(adjacent)
    assert index.intervals == (("chr1", 0, 5_000),)
    assert territory_status(unit, index) == "eligible"
    for start, end, expected in [(0, 5_000, True), (2_000, 5_000, True), (0, 5_001, False)]:
        assert contains_interval("chr1", start, end, adjacent) is expected
        assert contains_interval("chr1", start, end, index) is expected
    with pytest.raises((AttributeError, TypeError)):
        index.intervals = ()
    with pytest.raises(TypeError):
        index._by_chrom["chr1"] = ((), ())
    assert territory_status(unit, [("chr1", 501, 5_000)]) == "boundary_or_mixed"
    assert territory_status(unit, [("chr1", 0, 2_500), ("chr1", 2_501, 5_000)]) == "boundary_or_mixed"
    assert not contains_interval("chr1", -1, 1, [("chr1", 0, 10)])


def test_bed_merge_subtract_intersect_and_autosomal_territories():
    left = [("chr1", 0, 10), ("chr1", 10, 20), ("chr1", 30, 40), ("chrX", 0, 9)]
    right = [("chr1", 5, 12), ("chr1", 18, 33), ("chrX", 2, 4)]
    assert merge_bed(left) == [("chr1", 0, 20), ("chr1", 30, 40), ("chrX", 0, 9)]
    assert subtract_bed(left, right) == [("chr1", 0, 5), ("chr1", 12, 18), ("chr1", 33, 40), ("chrX", 0, 2), ("chrX", 4, 9)]
    assert intersect_bed(left, right) == [("chr1", 5, 12), ("chr1", 18, 20), ("chr1", 30, 33), ("chrX", 2, 4)]
    hard, ordinary = territory_sets(left, right)
    assert hard == [("chr1", 0, 5), ("chr1", 12, 18), ("chr1", 33, 40)]
    assert ordinary == [("chr1", 5, 12), ("chr1", 18, 20), ("chr1", 30, 33)]


def test_joint_bootstrap_resamples_paired_blocks_and_is_fixed():
    hard = [ScreenObservation("chr1", 10, True), ScreenObservation("chr1", 20, False)]
    ordinary = [ScreenObservation("chr1", 30, False), ScreenObservation("chr1", 40, False)]
    result = joint_block_bootstrap(hard, ordinary)
    assert result.difference == 0.5
    assert result.interval == (0.5, 0.5)
    assert (result.union_blocks, result.valid_draws, result.zero_denominator_draws) == (1, 2_000, 0)
    assert joint_block_bootstrap(reversed(hard), reversed(ordinary)) == result


def test_zero_denominator_draws_are_counted_without_retry():
    hard = [ScreenObservation("chr1", 1, True)]
    ordinary = [ScreenObservation("chr1", 1_000_001, False)]
    result = joint_block_bootstrap(hard, ordinary)
    assert result.difference == 1.0
    assert result.valid_draws + result.zero_denominator_draws == 2_000
    assert result.valid_draws < 1_900
    assert result.interval is None and result.status == "inconclusive"


def test_zero_observed_territory_denominator_makes_difference_undefined():
    result = joint_block_bootstrap([], [ScreenObservation("chr1", 1, False)])
    assert result.difference is None and result.interval is None
    assert result.status == "undefined_observed_denominator"
    assert result.zero_denominator_draws == 2_000


def test_secondary_arm_requires_explicit_residual_flags():
    hard = [ScreenObservation("chr1", 1, True, False)]
    ordinary = [ScreenObservation("chr1", 2, False, True)]
    result = joint_block_bootstrap(hard, ordinary, secondary_provided=True)
    assert result.secondary_provided and result.difference == -1.0
    with pytest.raises(ValueError, match="explicit residual bool"):
        joint_block_bootstrap([ScreenObservation("chr1", 1, True)], ordinary, secondary_provided=True)
