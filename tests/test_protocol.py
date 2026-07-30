#!/usr/bin/env python3
"""Guards on alignssl.protocol -- the shared label-efficiency protocol.

The regression this file exists to prevent, stated concretely: on the
candidate-filtered benchmark (n_pool = 3452) at the 1% label fraction, the
deep arms used `max(batch_size=96, int(0.01*3452)=34) = 96` labels while the
classical control used `max(2, round(0.01*3452)) = 35`. The deep arms
therefore had a 2.8x label advantage in the single cell carrying the paper's
headline low-label claim, and the two curves did not share an x-axis.

test_budget_is_arm_independent is the direct guard: one function, called by
every arm, must return one number.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pytest
except ModuleNotFoundError:  # cluster env has no pytest
    class _P:
        @staticmethod
        def mark_parametrize(*a, **k):
            def deco(f):
                return f
            return deco

        class mark:
            @staticmethod
            def parametrize(*a, **k):
                def deco(f):
                    return f
                return deco

        @staticmethod
        def raises(exc):
            class _C:
                def __enter__(self):
                    return self

                def __exit__(self, t, v, tb):
                    assert t is not None and issubclass(t, exc), \
                        f"expected {exc.__name__}"
                    return True
            return _C()
    pytest = _P()

from alignssl.protocol import (MIN_SPLIT_SIDE, label_budget, loader_params,
                               split_budget)

# The two benchmarks actually used in the paper.
N_UNIFORM = 21016
N_FILTERED = 3452
FRACS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]


def test_budget_is_arm_independent():
    """THE regression guard: the old deep and classical rules disagreed."""
    old_deep = lambda f, N: max(96, int(f * N))          # noqa: E731
    old_classical = lambda f, N: max(2, int(round(f * N)))  # noqa: E731

    # Demonstrate the historical defect exists in the OLD rules ...
    assert old_deep(0.01, N_FILTERED) == 96
    assert old_classical(0.01, N_FILTERED) == 35
    assert old_deep(0.01, N_FILTERED) != old_classical(0.01, N_FILTERED)

    # ... and that the shared rule removes it everywhere.
    for N in (N_UNIFORM, N_FILTERED):
        for f in FRACS:
            assert label_budget(f, N) == old_classical(f, N), (f, N)


def test_budget_no_batch_floor():
    """A 1% budget on the filtered pool is 35 labels, not 96."""
    assert label_budget(0.01, N_FILTERED) == 35
    assert label_budget(1.0, N_FILTERED) == N_FILTERED
    assert label_budget(1.0, N_UNIFORM) == N_UNIFORM


def test_budget_monotone_and_bounded():
    for N in (N_UNIFORM, N_FILTERED, 100, 7):
        vals = [label_budget(f, N) for f in FRACS]
        assert vals == sorted(vals), (N, vals)
        assert all(2 <= v <= N for v in vals), (N, vals)


def test_budget_rejects_bad_input():
    with pytest.raises(ValueError):
        label_budget(0.0, 100)
    with pytest.raises(ValueError):
        label_budget(1.5, 100)
    with pytest.raises(ValueError):
        label_budget(0.5, 1)


def test_val_split_is_carved_from_budget():
    """Validation is never free: n_val + n_train == n exactly."""
    for n in (2, 12, 35, 96, 345, 3452, 21016):
        n_val, n_train, did = split_budget(n, 0.2)
        assert n_val + n_train == n, (n, n_val, n_train)
        assert n_val >= 0 and n_train >= 1


def test_val_split_no_longer_gated_on_batch_size():
    """Old gate `n_val >= 96` blocked every filtered cell below 25%.

    35 labels at val_frac 0.2 gives n_val = 7, which the old rule rejected
    (7 < 96) and the new rule also rejects (7 < 12) -- but 96 labels gives
    n_val = 19, which the old rule rejected and the new rule accepts.
    """
    assert split_budget(35, 0.2)[2] is False       # genuinely too small
    n_val, n_train, did = split_budget(96, 0.2)
    assert did is True and n_val == 19 and n_train == 77
    assert split_budget(173, 0.2)[2] is True
    assert split_budget(345, 0.2)[2] is True


def test_val_split_threshold_is_min_side():
    n_val, _, did = split_budget(int(round(MIN_SPLIT_SIDE / 0.2)), 0.2)
    assert did is True and n_val == MIN_SPLIT_SIDE


def test_loader_never_yields_zero_batches():
    """The reason the batch floor existed -- fixed by shrinking the batch."""
    for n_train in range(1, 400):
        bs, drop = loader_params(n_train, 96)
        n_batches = n_train // bs if drop else -(-n_train // bs)
        assert n_batches >= 1, (n_train, bs, drop)
        assert bs <= n_train and bs <= 96


def test_loader_drops_only_when_tail_is_small_share():
    assert loader_params(28, 96) == (28, False)     # single short batch
    assert loader_params(96, 96) == (96, False)     # exactly one batch
    assert loader_params(192, 96) == (96, True)     # two full batches
    assert loader_params(21016, 96)[1] is True


def test_loader_rejects_empty():
    with pytest.raises(ValueError):
        loader_params(0, 96)


def test_filtered_1pct_cell_end_to_end():
    """The exact cell that was broken, traced through the whole protocol."""
    n = label_budget(0.01, N_FILTERED)
    assert n == 35
    n_val, n_train, did = split_budget(n, 0.2)
    assert (n_val, n_train, did) == (0, 35, False)   # falls back to fixed cut
    bs, drop = loader_params(n_train, 96)
    assert (bs, drop) == (35, False)                 # one batch of 35, no loss


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"PASS: {len(fns)} protocol guards")
