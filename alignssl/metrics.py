#!/usr/bin/env python3
"""Shared evaluation metrics for every arm of the benchmark.

Why this module exists
----------------------
An internal audit found that the deep arms (`finetune_eval.py`,
`deepsv_baseline_eval.py`) reported F1 at a *fixed* decision rule --
`logits.argmax(1)`, i.e. p >= 0.5 -- while the classical arms
(`classical_baseline_eval.py`) reported F1 at a fixed `p >= 0.5` cut on a
class-weight-balanced logistic regression. Neither selected a threshold.

At small label budgets a network can rank test windows well and still place
*every* window below 0.5, giving F1 = 0 for a model whose AUPRC is far above
chance. The label-efficiency gap measured in F1 was therefore partly an
artifact of where the decision boundary happened to fall, not of how well
the representation ranks. On the uniform benchmark at 1% labels the
from-scratch arm scored F1 = 0.05 against the pretrained arm's 0.514 (a
10.4x gap) while their AUPRCs were 0.411 vs 0.561 (a 1.36x gap), and 0.411
is well above the 0.25 positive rate.

Every arm now reports, from this module:

  * ``auprc``   -- average precision, threshold-free, primary metric
  * ``roc_auc`` -- threshold-free, reported for completeness
  * ``f1_at_half``  -- the legacy fixed-threshold number, kept so the
                      published tables remain reproducible and the size of
                      the artifact stays auditable
  * ``f1_at_tau``, ``tau`` -- F1 at a threshold selected to maximise F1 on a
                      held-out *validation* split, which is carved out of
                      the labelled budget rather than granted for free

The validation split costs labels. `select_threshold` is only ever handed
validation scores, never test scores, so `f1_at_tau` remains an honest
held-out number.
"""
from __future__ import annotations

import numpy as np


def _as_np(a):
    return a.detach().cpu().numpy() if hasattr(a, "detach") else np.asarray(a)


def prf1_at(scores, labels, tau):
    """Precision, recall, F1 for the rule ``score >= tau``."""
    s, y = _as_np(scores).ravel(), _as_np(labels).ravel().astype(int)
    pred = (s >= tau).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def select_threshold(val_scores, val_labels, grid=None):
    """Threshold maximising F1 on the validation split.

    Falls back to 0.5 when the validation split is degenerate (one class
    only, or empty), so the caller always receives a usable number and the
    fallback is visible in the recorded ``tau``.
    """
    s, y = _as_np(val_scores).ravel(), _as_np(val_labels).ravel().astype(int)
    if s.size == 0 or y.sum() == 0 or y.sum() == y.size:
        return 0.5
    if grid is None:
        # candidate cuts midway between consecutive distinct scores, capped
        # so the search stays cheap on large validation splits
        u = np.unique(s)
        if u.size > 512:
            u = np.quantile(s, np.linspace(0.0, 1.0, 512))
            u = np.unique(u)
        grid = np.concatenate([[0.0], (u[:-1] + u[1:]) / 2.0, [1.0]]) if u.size > 1 \
            else np.array([0.0, 0.5, 1.0])
    best_f, best_t = -1.0, 0.5
    for t in grid:
        _, _, f = prf1_at(s, y, t)
        if f > best_f:
            best_f, best_t = f, float(t)
    return best_t


def threshold_free(scores, labels):
    """AUPRC and ROC-AUC, plus the positive rate that defines chance AUPRC."""
    from sklearn.metrics import average_precision_score, roc_auc_score
    s, y = _as_np(scores).ravel(), _as_np(labels).ravel().astype(int)
    pos = int(y.sum())
    if pos == 0 or pos == y.size:
        return {"auprc": float("nan"), "roc_auc": float("nan"),
                "pos_rate": pos / y.size if y.size else float("nan")}
    return {"auprc": float(average_precision_score(y, s)),
            "roc_auc": float(roc_auc_score(y, s)),
            "pos_rate": pos / y.size}


def score_arm(test_scores, test_labels, val_scores=None, val_labels=None):
    """The full metric record for one arm at one label fraction.

    ``val_scores``/``val_labels`` may be omitted, in which case ``tau``
    falls back to 0.5 and ``f1_at_tau`` equals ``f1_at_half``; the record
    then carries ``tau_selected: False`` so downstream aggregation can tell
    a selected threshold from a defaulted one.
    """
    rec = threshold_free(test_scores, test_labels)
    p0, r0, f0 = prf1_at(test_scores, test_labels, 0.5)
    rec.update({"P_at_half": p0, "R_at_half": r0, "f1_at_half": f0})
    if val_scores is not None and val_labels is not None \
            and _as_np(val_scores).size > 0:
        tau = select_threshold(val_scores, val_labels)
        rec["tau_selected"] = True
    else:
        tau = 0.5
        rec["tau_selected"] = False
    pt, rt, ft = prf1_at(test_scores, test_labels, tau)
    rec.update({"tau": float(tau), "P_at_tau": pt, "R_at_tau": rt,
                "f1_at_tau": ft})
    # legacy aliases so existing aggregation keeps working unchanged
    rec["F1"] = f0
    rec["P"] = p0
    rec["R"] = r0
    rec["AUPRC"] = rec["auprc"]
    return rec
