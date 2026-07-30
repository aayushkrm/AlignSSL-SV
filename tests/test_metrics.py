#!/usr/bin/env python3
"""Guards on alignssl.metrics -- the shared scoring path for every arm.

The regression this file exists to prevent: a model that RANKS the test set
perfectly but places every score below 0.5 scored F1 = 0 under the old fixed
`logits.argmax(1)` rule, while its AUPRC was 1.0. Reporting only the former
made the low-label label-efficiency gap look an order of magnitude larger
than the ranking quality justified.

Runs under pytest, or as a plain script on hosts without pytest (the cluster
env `deepsv2_new` has none):  python tests/test_metrics.py
"""
from __future__ import annotations
import numpy as np

try:
    import pytest
except ModuleNotFoundError:  # cluster env has no pytest
    class _Shim:
        @staticmethod
        def approx(x, abs=1e-9, rel=None):
            class _A:
                def __eq__(self, o):
                    return abs_ok(o, x, abs)
            return _A()
    def abs_ok(o, x, tol):
        return np.allclose(np.asarray(o, float), np.asarray(x, float), atol=tol)
    pytest = _Shim()  # type: ignore

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from alignssl.metrics import prf1_at, select_threshold, threshold_free, score_arm


def test_perfect_ranking_below_half_is_not_zero():
    """The exact bug. Perfect ranking, all scores < 0.5."""
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    s = np.array([0.01, 0.02, 0.03, 0.04, 0.10, 0.12, 0.14, 0.16])
    tf = threshold_free(s, y)
    assert abs(tf["auprc"] - 1.0) < 1e-9, tf
    assert abs(tf["roc_auc"] - 1.0) < 1e-9, tf
    _, _, f_half = prf1_at(s, y, 0.5)
    assert f_half == 0.0, f_half           # what the old code reported
    tau = select_threshold(s, y)
    _, _, f_tau = prf1_at(s, y, tau)
    assert abs(f_tau - 1.0) < 1e-9, (tau, f_tau)


def test_f1_at_half_preserved_as_legacy_alias():
    y = np.array([0, 1, 0, 1])
    s = np.array([0.2, 0.9, 0.6, 0.8])
    rec = score_arm(s, y)
    _, _, f = prf1_at(s, y, 0.5)
    assert rec["f1_at_half"] == f
    assert rec["F1"] == f            # legacy key must still be F1@0.5
    assert rec["AUPRC"] == rec["auprc"]
    assert rec["tau_selected"] is False
    assert rec["tau"] == 0.5
    assert rec["f1_at_tau"] == f     # no val split -> tau defaults to 0.5


def test_threshold_never_selected_on_test_scores():
    """tau must come from the validation split, not the test split."""
    rng = np.random.default_rng(0)
    y_te = rng.integers(0, 2, 400)
    s_te = rng.random(400)                       # test scores: pure noise
    y_va = np.array([0] * 50 + [1] * 50)
    s_va = np.concatenate([rng.random(50) * 0.1,        # clean val signal
                           0.8 + rng.random(50) * 0.1])
    rec = score_arm(s_te, y_te, s_va, y_va)
    assert rec["tau_selected"] is True
    # a tau tuned on the clean val split lands in the val gap (0.1, 0.8)
    assert 0.1 < rec["tau"] < 0.8, rec["tau"]
    # and it must NOT have found the test-optimal cut
    best = max(prf1_at(s_te, y_te, t)[2] for t in np.linspace(0, 1, 201))
    assert rec["f1_at_tau"] <= best + 1e-12


def test_degenerate_val_split_falls_back_visibly():
    y = np.array([0, 1, 0, 1])
    s = np.array([0.2, 0.9, 0.6, 0.8])
    rec = score_arm(s, y, np.array([0.3, 0.4]), np.array([0, 0]))  # one class
    assert rec["tau"] == 0.5
    rec2 = score_arm(s, y, np.array([]), np.array([]))
    assert rec2["tau_selected"] is False


def test_pos_rate_is_chance_auprc():
    y = np.array([0] * 75 + [1] * 25)
    s = np.linspace(0, 1, 100)
    assert abs(threshold_free(s, y)["pos_rate"] - 0.25) < 1e-12


def test_all_one_class_returns_nan_not_crash():
    y = np.zeros(10, dtype=int)
    tf = threshold_free(np.linspace(0, 1, 10), y)
    assert np.isnan(tf["auprc"]) and np.isnan(tf["roc_auc"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"PASS: {len(fns)} metric guards")
