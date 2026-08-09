#!/usr/bin/env python3
"""Third benchmark: can any method filter a real caller's candidate list?

The uniform benchmark (Section 4) draws negatives at random from the genome,
which lets a single depth statistic reach ROC-AUC 0.955. The candidate-filtered
benchmark (Section 6) suppresses that shortcut by quantile-matching negative
windows to positives on depth, but its negatives are still *constructed* by us.

This benchmark removes our hand from the negative set entirely. Positives and
negatives are both taken from the candidate list a production short-read SV
caller actually emitted on HG002, and the label is whether the candidate
overlaps the GIAB Tier1 v0.6 truth set inside the Tier1 confident regions.
It therefore measures the task a filter is deployed to do: rank a caller's
own candidates.

Two consequences for scoring, both of which change which metric is admissible:

  * The positive rate is 0.805, not 0.25 or 0.05. AUPRC has a floor at the
    positive rate, so an arm that outputs a constant scores AUPRC 0.805 here
    and looks strong. AUPRC is near-uninformative on this benchmark and we
    do not rank on it.
  * ROC-AUC is invariant to the positive rate and is the metric we report.
    A constant predictor scores 0.5 regardless of class balance.

Emits results/table24_caller_candidate.csv: per label budget, the best
control arm and the best deep arm on ROC-AUC, the signed difference, and a
Welch test over seeds.

Usage:
    python analysis/caller_candidate.py --json-dir ../handoff/cand
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os

import numpy as np
from scipy import stats

# Deep arms are keyed by their sibling name inside each label_efficiency row.
DEEP = [("pretrained", "AlignSSL-pretrained"), ("scratch", "AlignSSL-scratch")]
# The classical control JSONs carry both models as siblings; `hgb` is the
# gradient-boosted tree and `logreg` the logistic regression. Both families
# are reduced by best-of-family so neither side gets a best-of-K advantage
# the other does not (the same symmetry analysis/control_vs_deep.py enforces).
CONTROL = [("hgb", "Classical-GBT"), ("logreg", "Classical-logreg")]
METRIC = "roc_auc"


def _rows(path):
    with open(path) as fh:
        return json.load(fh)["label_efficiency"]


def _seed_values(files, frac, model_key):
    """ROC-AUC for one arm at one budget, one value per seed."""
    out = []
    for path in files:
        for row in _rows(path):
            if abs(float(row["frac"]) - frac) < 1e-9 and model_key in row:
                out.append(float(row[model_key][METRIC]))
    return np.asarray(out, dtype=float)


def _best_of_family(files, frac, family):
    """Return (display_name, values) for the family member with the best mean.

    Returns (None, empty) when no member has data at this budget, which is the
    normal state for a budget whose jobs have not finished.
    """
    best = (None, np.asarray([], dtype=float), -np.inf)
    for key, name in family:
        vals = _seed_values(files, frac, key)
        if vals.size == 0:
            continue
        mean = float(vals.mean())
        if mean > best[2]:
            best = (name, vals, mean)
    return best[0], best[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deep-glob", default="handoff/cand/cand_pre_*.json")
    ap.add_argument("--control-glob", default="handoff/cand/cls_cand_seed*.json")
    ap.add_argument("--out", default="results/table24_caller_candidate.csv")
    args = ap.parse_args()

    deep_files = sorted(glob.glob(args.deep_glob))
    ctrl_files = sorted(glob.glob(args.control_glob))
    if not deep_files or not ctrl_files:
        raise SystemExit(
            f"no inputs: {len(deep_files)} deep, {len(ctrl_files)} control"
        )

    fracs = sorted({float(r["frac"]) for f in deep_files + ctrl_files
                    for r in _rows(f)})

    out_rows = []
    for frac in fracs:
        c_name, c_vals = _best_of_family(ctrl_files, frac, CONTROL)
        d_name, d_vals = _best_of_family(deep_files, frac, DEEP)
        # A budget with no deep seeds yet is skipped rather than reported as a
        # control win: an absent arm is not a beaten arm.
        if c_vals.size == 0 or d_vals.size == 0:
            continue
        n = next((int(r["n"]) for f in ctrl_files for r in _rows(f)
                  if abs(float(r["frac"]) - frac) < 1e-9), 0)
        diff = float(d_vals.mean() - c_vals.mean())
        if c_vals.size > 1 and d_vals.size > 1:
            p = float(stats.ttest_ind(d_vals, c_vals, equal_var=False).pvalue)
        else:
            p = float("nan")
        # `tie` when the test does not separate; the sign of `diff` alone is
        # not evidence at these seed counts.
        if not np.isfinite(p) or p >= 0.05:
            verdict = "tie"
        else:
            verdict = "deep" if diff > 0 else "control"
        out_rows.append({
            "label_frac": frac,
            "n_labelled": n,
            "control_arm": c_name,
            "control_roc_auc": round(float(c_vals.mean()), 4),
            "control_sd": round(float(c_vals.std(ddof=1)) if c_vals.size > 1 else 0.0, 4),
            "control_n_seeds": int(c_vals.size),
            "deep_arm": d_name,
            "deep_roc_auc": round(float(d_vals.mean()), 4),
            "deep_sd": round(float(d_vals.std(ddof=1)) if d_vals.size > 1 else 0.0, 4),
            "deep_n_seeds": int(d_vals.size),
            "deep_minus_control": round(diff, 4),
            "p": round(p, 4) if np.isfinite(p) else "",
            "verdict": verdict,
        })

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {args.out} ({len(out_rows)} budgets)")
    for r in out_rows:
        print(f"  frac={r['label_frac']:<5} n={r['n_labelled']:<5} "
              f"control={r['control_roc_auc']:.3f} deep={r['deep_roc_auc']:.3f} "
              f"p={r['p']} {r['verdict']}")


if __name__ == "__main__":
    main()
