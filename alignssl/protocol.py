#!/usr/bin/env python3
"""The label-efficiency protocol, shared verbatim by every evaluated arm.

Why this module exists
----------------------
A label-efficiency curve is only interpretable if every arm is handed the
*same number of labels* at each point on the x-axis. Before this module, the
three evaluators computed that number in two different ways:

    deep arms       n = max(batch_size, int(frac * n_pool))      # 96 floor
    classical arms  n = max(2,          round(frac * n_pool))

On the uniform benchmark (n_pool = 21,016) the floor never binds and the two
agree. On the candidate-filtered benchmark (n_pool = 3,452) the 1% cell is
`int(0.01 * 3452) = 34`, which is below the batch-size floor of 96 -- so the
deep arms silently received 96 labels while the classical control received
35. That is a 2.8x label advantage to the deep arms in exactly the cell that
carries the paper's headline low-label claim.

The floor was not arbitrary: `DataLoader(..., drop_last=True)` yields zero
batches when the subset is smaller than one batch, so a naive removal of the
floor trains the low-label cells on nothing. The fix is therefore to honour
the true budget and adapt the *loader* to it, not to inflate the budget to
suit the loader.

A second defect had the same root cause. The validation split that selects
the decision threshold was gated on `n_val >= batch_size`, so on the
filtered benchmark no split was carved below 25% of labels and those cells
fell back to a fixed 0.5 cut -- again, precisely the low-label cells of
interest. The gate is now a small absolute minimum independent of batch size.

Every function here is deliberately free of torch and sklearn so it can be
unit-tested without either.
"""
from __future__ import annotations

# Minimum examples required on each side of the budget/validation split for
# the split to be worth making. Below this a threshold estimated on the
# validation side would be noisier than the fixed 0.5 cut it replaces.
MIN_SPLIT_SIDE = 12


def label_budget(frac: float, n_pool: int) -> int:
    """Number of labelled examples granted at label fraction `frac`.

    `round` (not truncation) and a floor of 2 -- matching the classical
    evaluator exactly, so the curves share an x-axis by construction.
    """
    if not 0.0 < frac <= 1.0:
        raise ValueError(f"frac must be in (0, 1], got {frac}")
    if n_pool < 2:
        raise ValueError(f"n_pool must be >= 2, got {n_pool}")
    return max(2, min(n_pool, int(round(frac * n_pool))))


# ---------------------------------------------------------------------------
# Label accounting: the validation split is drawn FROM the label budget, not
# in addition to it.
#
# A label-efficiency x-axis must count every label the method consumed. Once a
# decision threshold is selected on held-out data, those held-out labels were
# used, so they belong inside the budget. At the 1% point on the uniform
# benchmark the arm therefore sees 210 labels total -- 168 for gradient steps
# and 42 for threshold selection -- not 210 for training plus a free 42.
#
# The consequence is visible and intended: full supervision now fits on 16,813
# of 21,016 windows, so absolute scores sit below the previously published
# fixed-threshold numbers, which trained on all 21,016 and then evaluated at an
# arbitrary 0.5 cut. Comparisons across arms remain exact because every arm
# pays the identical cost.
# ---------------------------------------------------------------------------
def split_budget(n: int, val_frac: float, min_side: int = MIN_SPLIT_SIDE):
    """Split a labelled budget of `n` into (n_val, n_train).

    The validation split is carved OUT OF the budget -- it is not granted for
    free -- because a curve in which every arm also gets an unbudgeted
    validation set is not a label-efficiency curve.

    Returns (n_val, n_train, did_split). When the budget is too small to
    split, n_val is 0 and the caller must fall back to a fixed threshold.
    """
    if n < 2:
        raise ValueError(f"n must be >= 2, got {n}")
    n_val = int(round(val_frac * n))
    if n_val >= min_side and (n - n_val) >= min_side:
        return n_val, n - n_val, True
    return 0, n, False


def loader_params(n_train: int, requested_batch: int):
    """Batch size and drop_last that train on `n_train` examples without loss.

    Guarantees at least one batch for any n_train >= 1: the batch shrinks to
    the subset rather than the subset being padded up to the batch. `drop_last`
    is kept only when a dropped tail is a small fraction of the data, so that
    batch-norm statistics stay stable on large subsets without discarding a
    meaningful share of a small one.
    """
    if n_train < 1:
        raise ValueError(f"n_train must be >= 1, got {n_train}")
    bs = max(1, min(requested_batch, n_train))
    drop_last = n_train >= 2 * bs
    return bs, drop_last
