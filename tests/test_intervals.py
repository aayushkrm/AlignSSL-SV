"""Correctness of the interval helpers used for GIAB truth labelling.

These two predicates decide whether a window is a legitimate negative:
``interval_contains`` asks "is this inside a confident region", and
``interval_overlaps`` asks "does this touch a called variant". A wrong answer
is not a performance bug -- it silently mislabels a locus the truth set makes
no claim about as a confident negative, which then trains and scores the model
against a label that does not exist.

Both use binary search on the interval start column, which is only exact when
the intervals are disjoint. GIAB exclusion zones are NOT disjoint as loaded: a
long Tier1 deletion record encloses smaller INS and non-PASS records. The tests
below encode both the specific failure that was found (a query deep inside a
long early interval reading as not-overlapping) and a brute-force property
check over random nested intervals.
"""
from __future__ import annotations
import numpy as np
import pytest

from alignssl.data import merge_intervals, interval_contains, interval_overlaps


def brute_overlaps(arr, s, e):
    return bool(np.any((np.asarray(arr)[:, 0] < e) & (np.asarray(arr)[:, 1] > s)))


def brute_contains(arr, s, e):
    """Wholly inside the UNION -- which is what an exclusion/confident region
    means. A query spanning two abutting intervals is contained by the union
    even though no single row contains it, which is why the helper requires a
    merged array."""
    m = merge_intervals(arr)
    return bool(np.any((m[:, 0] <= s) & (m[:, 1] >= e)))


NESTED = [[1000, 500000], [2000, 2100], [3000, 3100], [4000, 4100],
          [5000, 5100]]


def test_regression_deep_inside_long_early_interval():
    # The concrete bug: 400000 is inside [1000, 500000) but the binary search
    # on unmerged starts landed four rows past it and returned False.
    raw = np.asarray(NESTED, dtype=np.int64)
    assert brute_overlaps(raw, 400_000, 400_100) is True
    m = merge_intervals(raw)
    assert interval_overlaps(m, 400_000, 400_100) is True
    assert interval_contains(m, 400_000, 400_100) is True


def test_merge_produces_disjoint_sorted_union():
    m = merge_intervals(NESTED)
    assert m.tolist() == [[1000, 500000]]
    # Disjoint and sorted, for any input
    rng = np.random.default_rng(0)
    for _ in range(50):
        starts = rng.integers(0, 10_000, size=40)
        lens = rng.integers(1, 3_000, size=40)
        m = merge_intervals(np.stack([starts, starts + lens], axis=1))
        assert np.all(m[:, 0] < m[:, 1])
        assert np.all(m[1:, 0] > m[:-1, 1]), "merged intervals must be disjoint"
        assert np.all(np.diff(m[:, 0]) > 0)


def test_merge_is_idempotent_and_preserves_coverage():
    rng = np.random.default_rng(1)
    starts = rng.integers(0, 20_000, size=60)
    raw = np.stack([starts, starts + rng.integers(1, 5_000, size=60)], axis=1)
    m = merge_intervals(raw)
    assert merge_intervals(m).tolist() == m.tolist()
    # Every base covered by raw is covered by m and vice versa.
    hi = int(raw[:, 1].max()) + 10
    cov_raw = np.zeros(hi, bool)
    for s, e in raw:
        cov_raw[s:e] = True
    cov_m = np.zeros(hi, bool)
    for s, e in m:
        cov_m[s:e] = True
    assert np.array_equal(cov_raw, cov_m)


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_predicates_match_brute_force_on_nested_input(seed):
    rng = np.random.default_rng(seed)
    # Deliberately include a few very long intervals so nesting is guaranteed.
    starts = rng.integers(0, 50_000, size=30)
    lens = rng.integers(1, 500, size=30)
    lens[:3] = rng.integers(20_000, 60_000, size=3)
    raw = np.stack([starts, starts + lens], axis=1).astype(np.int64)
    m = merge_intervals(raw)
    qs = rng.integers(0, 110_000, size=400)
    qlen = rng.integers(1, 2_000, size=400)
    for s, ln in zip(qs, qlen):
        e = int(s) + int(ln)
        assert interval_overlaps(m, int(s), e) == brute_overlaps(raw, int(s), e), \
            (int(s), e)
        assert interval_contains(m, int(s), e) == brute_contains(raw, int(s), e), \
            (int(s), e)


def test_empty_and_degenerate_inputs():
    for empty in (None, [], np.zeros((0, 2), dtype=np.int64)):
        assert merge_intervals(empty).shape == (0, 2)
        assert interval_overlaps(merge_intervals(empty), 5, 10) is False
        assert interval_contains(merge_intervals(empty), 5, 10) is False
    # Abutting intervals are one union; a query spanning the join is contained.
    m = merge_intervals([[0, 100], [100, 200]])
    assert m.tolist() == [[0, 200]]
    assert interval_contains(m, 50, 150) is True
    # Half-open semantics: touching at the boundary is not an overlap.
    m2 = merge_intervals([[100, 200]])
    assert interval_overlaps(m2, 0, 100) is False
    assert interval_overlaps(m2, 200, 300) is False
    assert interval_overlaps(m2, 199, 300) is True


def test_load_bed_returns_merged(tmp_path):
    p = tmp_path / "conf.bed"
    p.write_text("chr1\t1000\t500000\nchr1\t2000\t2100\nchr1\t600000\t600500\n")
    from alignssl.data import load_bed
    out = load_bed(str(p), chroms=["1"])
    assert out["1"].tolist() == [[1000, 500000], [600000, 600500]]
    assert interval_contains(out["1"], 400_000, 400_100) is True
