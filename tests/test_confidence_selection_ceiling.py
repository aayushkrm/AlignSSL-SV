import pytest

from analysis.confidence_selection_ceiling import confidence_selection_ceiling


def test_small_counts_match_brute_force_maximum():
    # Include floors that admit one and two wrong calls, not only cases
    # below99 where every feasible selection must exclude all wrong calls.
    for k_correct in list(range(10)) + [98, 99, 100, 197, 198, 199]:
        for w_wrong in range(5):
            outcome = confidence_selection_ceiling(
                k_correct, w_wrong, k_correct + w_wrong
            )
            feasible_totals = [
                correct + wrong
                for correct in range(k_correct + 1)
                for wrong in range(w_wrong + 1)
                if 100 * wrong <= correct + wrong
            ]

            assert outcome["accepted_total"] == max(feasible_totals)
            assert 100 * outcome["accepted_wrong"] <= outcome["accepted_total"]


def test_exact_one_percent_boundary_at_99_correct():
    outcome = confidence_selection_ceiling(99, 1, 100)

    assert outcome == {
        "accepted_correct": 99,
        "accepted_wrong": 1,
        "accepted_total": 100,
        "eligible": 100,
        "coverage": 1.0,
        "error_fraction": 0.01,
    }


def test_98_correct_does_not_allow_a_wrong_genotype():
    outcome = confidence_selection_ceiling(98, 1, 99)

    assert outcome["accepted_correct"] == 98
    assert outcome["accepted_wrong"] == 0
    assert outcome["accepted_total"] == 98
    assert outcome["error_fraction"] == 0.0


def test_zero_correct_accepts_nothing_and_has_undefined_error_fraction():
    outcome = confidence_selection_ceiling(0, 7, 10)

    assert outcome["accepted_correct"] == 0
    assert outcome["accepted_wrong"] == 0
    assert outcome["accepted_total"] == 0
    assert outcome["coverage"] == 0.0
    assert outcome["error_fraction"] is None


def test_empty_eligible_set_has_undefined_coverage_and_no_claim():
    outcome = confidence_selection_ceiling(0, 0, 0)

    assert outcome == {
        "accepted_correct": 0,
        "accepted_wrong": 0,
        "accepted_total": 0,
        "eligible": 0,
        "coverage": None,
        "error_fraction": None,
    }


def test_missing_or_unusable_genotypes_stay_in_fixed_denominator():
    outcome = confidence_selection_ceiling(99, 1, 1000)

    assert outcome["accepted_total"] == 100
    assert outcome["eligible"] == 1000
    assert outcome["coverage"] == 0.1


def test_large_integer_cutoff_is_exact():
    allowed_wrong = 10**100
    k_correct = 99 * allowed_wrong
    w_wrong = allowed_wrong
    eligible = k_correct + w_wrong

    outcome = confidence_selection_ceiling(k_correct, w_wrong, eligible)

    assert outcome["accepted_wrong"] == allowed_wrong
    assert outcome["accepted_correct"] == k_correct
    assert outcome["accepted_total"] == eligible
    assert outcome["coverage"] == 1.0


@pytest.mark.parametrize("bad_count", [True, False, 1.0, 1.5])
@pytest.mark.parametrize("position", [0, 1, 2])
def test_rejects_boolean_and_float_counts(bad_count, position):
    counts = [0, 0, 1]
    counts[position] = bad_count

    with pytest.raises(TypeError):
        confidence_selection_ceiling(*counts)


@pytest.mark.parametrize(
    "counts",
    [(-1, 0, 1), (0, -1, 1), (0, 0, -1), (2, 1, 2)],
)
def test_rejects_negative_counts_and_usable_counts_above_denominator(counts):
    with pytest.raises(ValueError):
        confidence_selection_ceiling(*counts)
