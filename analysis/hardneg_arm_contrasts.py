#!/usr/bin/env python3
"""Arm-versus-arm contrasts on the candidate-filtered benchmark, corrected.

Section 6.3 of the manuscript originally drew three conclusions from the
candidate-filtered benchmark. All three were produced under the two
conventions that Sections 3.8 and 4.8 later showed to be defective (unequal
label budgets, F1 at a fixed 0.5 cut). This script re-tests each contrast on
the corrected `f_hn_*` runs, threshold-free.

Every contrast is reported on AUPRC and, for comparison, on F1 at the
validation-selected threshold -- because the point of Section 4.8 is that the
two can disagree, and a reader is entitled to see where they do.

Welch's t-test over seeds; the seeds are independent pretraining runs for the
pretrained arm, so the error bars span pretraining variance rather than
fine-tuning variance alone.

Usage:
    python analysis/hardneg_arm_contrasts.py --json-dir ../handoff/deep
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os

import numpy as np
from scipy import stats

ARMS = {"pre": "AlignSSL-pretrained", "scr": "AlignSSL-scratch",
        "dsv": "DeepSV-representation"}
# The three contrasts Section 6.3 makes claims about.
CONTRASTS = [("pre", "scr"), ("pre", "dsv"), ("scr", "dsv")]
METRICS = ["auprc", "f1_at_tau"]


def seed_values(json_dir, bench, stem, frac, metric):
    out = []
    for path in sorted(glob.glob(os.path.join(json_dir,
                                              f"f_{bench}_{stem}_seed*.json"))):
        with open(path) as fh:
            doc = json.load(fh)
        for row in doc.get("label_efficiency", []):
            if abs(float(row["frac"]) - frac) > 1e-9:
                continue
            m = (row.get("pretrained") or row.get("scratch")
                 or row.get("deepsv"))
            if isinstance(m, dict) and m.get(metric) is not None:
                out.append(float(m[metric]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", default="../handoff/deep")
    ap.add_argument("--bench", default="hn",
                    help="hn = candidate-filtered, uni = uniform")
    ap.add_argument("--out",
                    default="results/table15_hardneg_arm_contrasts.csv")
    a = ap.parse_args()

    fracs, budget = set(), {}
    for path in glob.glob(os.path.join(a.json_dir, f"f_{a.bench}_*_seed*.json")):
        with open(path) as fh:
            doc = json.load(fh)
        for row in doc.get("label_efficiency", []):
            fracs.add(float(row["frac"]))
            budget[float(row["frac"])] = int(row["n"])

    rows = []
    for frac in sorted(fracs):
        for lhs, rhs in CONTRASTS:
            for metric in METRICS:
                x = seed_values(a.json_dir, a.bench, lhs, frac, metric)
                y = seed_values(a.json_dir, a.bench, rhs, frac, metric)
                if len(x) < 2 or len(y) < 2:
                    continue
                _, p = stats.ttest_ind(x, y, equal_var=False)
                diff = float(np.mean(x) - np.mean(y))
                rows.append({
                    "label_frac": frac,
                    "n_labelled": budget[frac],
                    "metric": metric,
                    "arm_a": ARMS[lhs],
                    "arm_b": ARMS[rhs],
                    "mean_a": round(float(np.mean(x)), 4),
                    "sd_a": round(float(np.std(x, ddof=1)), 4),
                    "mean_b": round(float(np.mean(y)), 4),
                    "sd_b": round(float(np.std(y, ddof=1)), 4),
                    "a_minus_b": round(diff, 4),
                    "p": round(float(p), 4),
                    # Prose may only assert a difference where this says so.
                    "verdict": ("a" if diff > 0 and p < 0.05 else
                                "b" if diff < 0 and p < 0.05 else "tie"),
                })

    if not rows:
        raise SystemExit(f"no f_{a.bench}_* JSONs under {a.json_dir}")

    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    for metric in METRICS:
        print(f"\n{metric}:")
        for r in rows:
            if r["metric"] != metric:
                continue
            print(f"  {r['label_frac']:>5} n={r['n_labelled']:>5}  "
                  f"{r['arm_a']:<22s}{r['mean_a']:.3f}  vs  "
                  f"{r['arm_b']:<22s}{r['mean_b']:.3f}  "
                  f"p={r['p']:.4f}  -> {r['verdict']}")
    print(f"\nwrote {a.out}  ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
