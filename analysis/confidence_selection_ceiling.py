"""Finite-count oracle ceiling for a fixed 1% accepted-genotype error target."""


def confidence_selection_ceiling(k_correct, w_wrong, eligible):
    """Return the exact 1% selection ceiling for one fixed set of GTs.

    ``k_correct`` and ``w_wrong`` count usable fixed genotypes. ``eligible``
    is the shared denominator, including missing or unusable genotypes. The
    ceiling retains every correct genotype and the largest allowed number of
    wrong genotypes. It does not change or combine genotypes.
    """
    for name, value in (
        ("k_correct", k_correct),
        ("w_wrong", w_wrong),
        ("eligible", eligible),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer count")
        if value < 0:
            raise ValueError(f"{name} must be nonnegative")

    if k_correct + w_wrong > eligible:
        raise ValueError("usable counts cannot exceed the eligible denominator")

    accepted_wrong = min(w_wrong, k_correct // 99)
    accepted_total = k_correct + accepted_wrong

    coverage = accepted_total / eligible if eligible > 0 else None
    error_fraction = (
        accepted_wrong / accepted_total if accepted_total > 0 else None
    )

    return {
        "accepted_correct": k_correct,
        "accepted_wrong": accepted_wrong,
        "accepted_total": accepted_total,
        "eligible": eligible,
        "coverage": coverage,
        "error_fraction": error_fraction,
    }
