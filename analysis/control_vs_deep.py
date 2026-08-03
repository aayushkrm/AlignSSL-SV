#!/usr/bin/env python3
"""Does the hand-crafted-feature control still lead once scoring is fixed?

The paper's central negative result is that twelve scalar alignment features
fed to a gradient-boosted tree match or beat every deep arm at every label
budget. That claim was established under two conventions that later proved
defective:

  * F1 at a fixed 0.5 probability cut, which penalises a well-ranking but
    uncalibrated model (see analysis/threshold_sensitivity.py), and
  * a label budget that granted the deep arms a batch-size floor the
    classical arms did not receive (see alignssl/protocol.py).

Both are corrected in the `f_*` runs. This script re-asks the question on
those runs using AUPRC, which is threshold-free, and tests each contrast over
seeds rather than over summary rows.

The answer is not uniform across the curve, which is why it needs a table
rather than a sentence: the control's lead is real and large where labels are
scarce, and it does not survive at full supervision on the uniform benchmark.

Emits results/table14_control_vs_deep.csv with, per benchmark and label
fraction: the control's AUPRC, the best deep arm's AUPRC, which arm that was,
the signed difference, and a Welch test over seeds.

Usage:
    python analysis/control_vs_deep.py --json-dir ../handoff/deep
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os

import numpy as np
from scipy import stats

# (file-stem, display name) for the deep arms. The control is read from the
# `classical` JSONs, whose rows carry both models as sibling keys -- `hgb` is
# the gradient-boosted tree, `logreg` the logistic regression. Selecting by
# name matters: an earlier aggregator took whichever key came first and
# reported the logistic regression under the tree's name.
DEEP = [("pre", "AlignSSL-pretrained"), ("scr", "AlignSSL-scratch"),
        ("dsv", "DeepSV-representation")]
# Both families are reduced by best-of-family at each budget, and the winning
# member is named in the table. Symmetry matters here: an earlier version
# fixed the control to the tree while letting the deep side take the best of
# three, which inverted the verdict in the one cell where the tree happens to
# be degenerate (35 candidate-filtered labels, where it never fires and scores
# AUPRC = the positive rate, while the logistic regression on the same twelve
# features reaches 0.477). Best-of-K inflates whichever side it is applied to,
# so it must be applied to both or neither.
CONTROL = [("hgb", "Classical-GBT"), ("logreg", "Classical-logreg")]
BENCHES = [("uni", "uniform"), ("hn", "candidate-filtered")]
METRIC = "auprc"


def _seed_values(json_dir, bench, stem, frac, metric, model_key=None):
    """Per-seed values of `metric` at label fraction `frac`.

    `model_key` selects a named sub-dict (the classical JSONs hold two models
    per row); when None the row's single arm dict is used.
    """
    out = []
    for path in sorted(glob.glob(os.path.join(json_dir,
                                              f"f_{bench}_{stem}_seed*.json"))):
        with open(path) as fh:
            doc = json.load(fh)
        for row in doc.get("label_efficiency", []):
            if abs(float(row["frac"]) - frac) > 1e-9:
                continue
            if model_key is not None:
                m = row.get(model_key)
            else:
                m = (row.get("pretrained") or row.get("scratch")
                     or row.get("deepsv"))
            if isinstance(m, dict) and m.get(metric) is not None:
                out.append(float(m[metric]))
    return out


def _fracs(json_dir, bench):
    fracs, budget = set(), {}
    for path in glob.glob(os.path.join(json_dir, f"f_{bench}_*_seed*.json")):
        with open(path) as fh:
            doc = json.load(fh)
        for row in doc.get("label_efficiency", []):
            f = float(row["frac"])
            fracs.add(f)
            budget[f] = int(row["n"])
    return sorted(fracs), budget


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", default="../handoff/deep")
    ap.add_argument("--out", default="results/table14_control_vs_deep.csv")
    a = ap.parse_args()

    rows = []
    for bench, bench_name in BENCHES:
        fracs, budget = _fracs(a.json_dir, bench)
        for frac in fracs:
            ctrl_name, ctrl = None, []
            for key, name in CONTROL:
                vals = _seed_values(a.json_dir, bench, "classical", frac,
                                    METRIC, model_key=key)
                if len(vals) > 1 and np.mean(vals) > (np.mean(ctrl)
                                                      if ctrl else -1):
                    ctrl_name, ctrl = name, vals
            if ctrl_name is None:
                continue
            best_name, best_vals = None, []
            for stem, name in DEEP:
                vals = _seed_values(a.json_dir, bench, stem, frac, METRIC)
                if len(vals) > 1 and np.mean(vals) > (np.mean(best_vals)
                                                     if best_vals else -1):
                    best_name, best_vals = name, vals
            if best_name is None:
                continue
            _, pval = stats.ttest_ind(best_vals, ctrl, equal_var=False)
            diff = float(np.mean(best_vals) - np.mean(ctrl))
            rows.append({
                "benchmark": bench_name,
                "label_frac": frac,
                "n_labelled": budget[frac],
                "control_arm": ctrl_name,
                "control_auprc_mean": round(float(np.mean(ctrl)), 4),
                "control_auprc_sd": round(float(np.std(ctrl, ddof=1)), 4),
                "control_n_seeds": len(ctrl),
                "best_deep_arm": best_name,
                "best_deep_auprc_mean": round(float(np.mean(best_vals)), 4),
                "best_deep_auprc_sd": round(float(np.std(best_vals, ddof=1)), 4),
                "best_deep_n_seeds": len(best_vals),
                "deep_minus_control": round(diff, 4),
                "p_value": round(float(pval), 4),
                # A lead is only claimed where the contrast clears 0.05; the
                # column exists so prose can never assert a lead the test
                # does not support.
                "leader": ("deep" if diff > 0 and pval < 0.05 else
                           "control" if diff < 0 and pval < 0.05 else "tie"),
            })

    if not rows:
        raise SystemExit("no rows: check --json-dir")

    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    for _, bench_name in BENCHES:
        sel = [r for r in rows if r["benchmark"] == bench_name]
        if not sel:
            continue
        print(f"\n{bench_name}:")
        for r in sel:
            print(f"  {r['label_frac']:>5}  n={r['n_labelled']:>6}  "
                  f"{r['control_arm']:<17s} {r['control_auprc_mean']:.3f}  "
                  f"{r['best_deep_arm']:<22s} {r['best_deep_auprc_mean']:.3f}  "
                  f"p={r['p_value']:.4f}  -> {r['leader']}")
        n_ctrl = sum(1 for r in sel if r["leader"] == "control")
        print(f"  control leads significantly at {n_ctrl} of {len(sel)} budgets")
    print(f"\nwrote {a.out}  ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
