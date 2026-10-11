import pytest
from analysis.parent_sva_census import ANCHOR, aligned_bases, classify, sa_outside_buffer


def test_compatible_insertion_preserves_exact_sequence():
    seq = "A" * 1000 + "C" * 3407 + "G" * 1000
    category, left, right, events = classify([(0, 1000), (1, 3407), (0, 1000)], ANCHOR - 1000, seq)
    assert (category, left, right) == ("compatible_insertion", 1000, 1000)
    assert events[0]["sequence"] == "C" * 3407


def test_reference_compatible_does_not_mean_truth_negative():
    assert classify([(0, 2000)], ANCHOR - 1000, "A" * 2000)[0] == "reference_compatible_cigar"


@pytest.mark.parametrize("length", [2725, 4089])
def test_length_outside_frozen_bounds_is_not_alt(length):
    assert classify([(0, 1000), (1, length), (0, 1000)], ANCHOR - 1000, "A" * (2000 + length))[0] == "other_structural_cigar"


def test_deletion_is_not_reference_and_not_aligned_flank():
    assert aligned_bases([(0, 1000), (2, 500), (0, 1000)], ANCHOR - 1000, ANCHOR, ANCHOR + 1000) == 500
    assert classify([(0, 1000), (2, 500), (0, 1000)], ANCHOR - 1000, "A" * 2000)[0] == "other_structural_cigar"


def test_missing_flank_is_unresolved_not_reference():
    assert classify([(0, 300), (1, 3407), (0, 1000)], ANCHOR - 300, "A" * 4707)[0] == "insufficient_aligned_flanks"


def test_external_supplementary_is_recorded():
    assert sa_outside_buffer("chr3,71589910,+,100M,60,0;") == []
    assert len(sa_outside_buffer("chr4,500,+,100M,60,0;")) == 1
    with pytest.raises(ValueError):
        sa_outside_buffer("broken;")
