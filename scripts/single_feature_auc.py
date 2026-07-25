#!/usr/bin/env python3
"""Untrained single-feature discrimination on a labelled benchmark.

This is the sharpest form of the benchmark-separability control in the paper: it
asks how well each of the twelve hand-crafted alignment features separates
deletions from non-deletions on the held-out test split *with no training and no
fitted parameters at all*. A feature that reaches high ROC-AUC by itself means
the benchmark can be solved by thresholding one scalar, which bounds what any
learned model on that benchmark can be said to demonstrate.

ROC-AUC is computed from the rank statistic (Mann-Whitney U / (n_pos * n_neg)),
which is exact and needs no threshold sweep. Because a feature can be
informative with either polarity -- for depth-like features the *low* tail is
deletion-like -- we report the raw AUC and also `auc_oriented`, defined as
max(auc, 1 - auc). The raw value tells you the direction; the oriented value
tells you the magnitude of the information leak, which is what the control is
measuring. A perfectly uninformative feature has auc_oriented = 0.5.

The feature definitions are imported from classical_baseline_eval so the numbers
here and the trained-classical numbers in Table 1 cannot drift apart.

Usage:
    python scripts/single_feature_auc.py --shard-dir $BASE/tensors_all6 \
        --split test --out results/table6_single_feature_auc.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classical_baseline_eval import FEAT_NAMES, build  # noqa: E402


def roc_auc_rank(y: np.ndarray, s: np.ndarray) -> float:
    """Exact ROC-AUC via the rank statistic, ties averaged.

    AUC = (sum of ranks of positives - n_pos*(n_pos+1)/2) / (n_pos*n_neg),
    the normalised Mann-Whitney U. Equivalent to the threshold-sweep integral
    but with no discretisation error, and correct under ties because
    scipy-style average ranks are used.
    """
    y = np.asarray(y).astype(bool)
    s = np.asarray(s, dtype=np.float64)
    n_pos, n_neg = int(y.sum()), int((~y).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=np.float64)
    ranks[order] = np.arange(1, len(s) + 1, dtype=np.float64)
    # average ranks within tie groups
    s_sorted = s[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return float((ranks[y].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-dir", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", default="results/table6_single_feature_auc.csv")
    a = ap.parse_args()

    X, y, _ = build(a.shard_dir, a.split)
    rows = []
    for k, name in enumerate(FEAT_NAMES):
        col = X[:, k]
        finite = np.isfinite(col)
        auc = roc_auc_rank(y[finite], col[finite])
        rows.append({
            "feature": name,
            "n_test": int(finite.sum()),
            "n_pos": int(y[finite].sum()),
            "auc": round(auc, 4),
            "auc_oriented": round(max(auc, 1.0 - auc), 4),
            "deletion_side": "low" if auc < 0.5 else "high",
        })
    rows.sort(key=lambda r: -r["auc_oriented"])

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nwrote {a.out}  (split={a.split}, n={rows[0]['n_test']}, "
          f"pos={rows[0]['n_pos']})")
    print(f"{'feature':<26}{'auc':>8}{'oriented':>10}{'del side':>10}")
    for r in rows:
        print(f"{r['feature']:<26}{r['auc']:>8.3f}{r['auc_oriented']:>10.3f}"
              f"{r['deletion_side']:>10}")
    top = rows[0]
    print(f"\nMost separable single feature: {top['feature']} at oriented "
          f"ROC-AUC {top['auc_oriented']:.3f} with no training.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
