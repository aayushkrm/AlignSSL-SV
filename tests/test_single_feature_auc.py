"""Verify the rank-statistic ROC-AUC used for the single-feature control.

The benchmark-separability control is the paper's most consequential number, so
the estimator behind it is checked against a brute-force pairwise definition
rather than trusted. `roc_auc_rank` is imported by source-exec so this test does
not require the torch/pysam stack that the rest of the evaluation script pulls
in.
"""
import numpy as np
import pytest


def _load():
    """Exec just the estimator out of the script, without its heavy imports."""
    import os
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "scripts", "single_feature_auc.py")).read()
    body = "def roc_auc_rank" + src.split("def roc_auc_rank")[1].split("def main")[0]
    ns = {}
    exec(body, {"np": np}, ns)
    return ns["roc_auc_rank"]


def _brute(y, s):
    """AUC as P(score_pos > score_neg) + 0.5 P(tie), over all pairs."""
    y = np.asarray(y).astype(bool)
    s = np.asarray(s, dtype=float)
    pos, neg = s[y], s[~y]
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def test_matches_pairwise_definition():
    f = _load()
    rng = np.random.default_rng(0)
    for _ in range(8):
        n = 200
        y = rng.integers(0, 2, n)
        s = rng.normal(size=n) + y * 0.8
        assert f(y, s) == pytest.approx(_brute(y, s), abs=1e-12)


def test_exact_under_heavy_ties():
    """A constant feature carries no information: AUC must be exactly 0.5."""
    f = _load()
    y = np.array([1, 1, 0, 0, 1, 0])
    assert f(y, np.ones(6)) == pytest.approx(0.5, abs=1e-12)


def test_both_polarities():
    """A feature can be perfectly informative with either sign."""
    f = _load()
    y = np.array([1, 1, 0, 0])
    assert f(y, np.array([9.0, 8.0, 1.0, 0.0])) == 1.0
    assert f(y, np.array([0.0, 1.0, 8.0, 9.0])) == 0.0


def test_degenerate_single_class():
    f = _load()
    assert np.isnan(f(np.zeros(5), np.arange(5.0)))
