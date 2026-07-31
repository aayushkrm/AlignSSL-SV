#!/usr/bin/env python3
"""How much of the pretrained-vs-scratch gap is the decision threshold?

Every deep arm in this study was originally scored by thresholding the
positive-class probability at a fixed 0.5. That is the convention the DeepSV
lineage uses, and it is the convention under which we first reported a
"10x F1 improvement at 1% labels from self-supervised pretraining".

A fixed cut conflates two different things:

  * ranking quality  -- can the model order deletions above non-deletions?
  * calibration      -- are its scores centred such that 0.5 is a sensible cut?

A model can rank perfectly and still score F1 = 0 at a fixed 0.5 cut if all
its probabilities sit below 0.5. That is exactly what a randomly-initialised
network does when trained on 210 labels: it learns the ordering but stays
timid, so the fixed cut reads it as degenerate.

This script re-scores the identical runs under three rules and reports them
side by side:

  F1@0.5    the fixed cut  (what the original claim used)
  F1@tau    threshold chosen on a validation split, applied to test
  AUPRC     threshold-free; ranking only

The ratio between arms under each rule is the quantity of interest. If the
ratio collapses when the threshold stops being fixed, the gap was a
thresholding effect and not evidence about the representation.

Reads results/table12_label_efficiency_fixed.csv (produced by
analysis/aggregate_fixed.py) plus the per-seed JSONs for significance tests.

Usage:
    python analysis/threshold_sensitivity.py \
        --table results/table12_label_efficiency_fixed.csv \
        --json-dir handoff/deep \
        --out results/table13_threshold_sensitivity.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os

import numpy as np
from scipy import stats

RULES = [("f1_at_half", "F1@0.5"), ("f1_at_tau", "F1@tau"), ("auprc", "AUPRC")]
PAIR = [("AlignSSL-pretrained", "pre"), ("AlignSSL-scratch", "scr")]


def per_seed(json_dir, bench, arm_key, frac, metric):
    """Per-seed values so the test is over seeds, not over the summary row."""
    out = []
    pat = os.path.join(json_dir, f"f_{bench}_{arm_key}_seed*.json")
    for fn in sorted(glob.glob(pat)):
        for row in json.load(open(fn))["label_efficiency"]:
            if abs(float(row["frac"]) - frac) > 1e-9:
                continue
            m = row.get("pretrained") or row.get("scratch") or row.get("deepsv")
            if isinstance(m, dict) and m.get(metric) is not None:
                out.append(float(m[metric]))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default="results/table12_label_efficiency_fixed.csv")
    ap.add_argument("--json-dir", default="handoff/deep")
    ap.add_argument("--out", default="results/table13_threshold_sensitivity.csv")
    a = ap.parse_args()

    src = list(csv.DictReader(open(a.table)))
    benches = ["uniform", "candidate-filtered"]
    bkey = {"uniform": "uni", "candidate-filtered": "hn"}

    rows = []
    for bench in benches:
        fracs = sorted({float(r["label_frac"]) for r in src
                        if r["benchmark"] == bench})
        for frac in fracs:
            rec = {"benchmark": bench, "label_frac": frac}
            have = True
            for arm, _ in PAIR:
                sel = [r for r in src if r["benchmark"] == bench
                       and r["arm"] == arm
                       and abs(float(r["label_frac"]) - frac) < 1e-9]
                if not sel:
                    have = False
                    break
                rec["n_labelled"] = int(sel[0]["n_labelled"])
                for key, name in RULES:
                    rec[f"{arm}_{name}"] = float(sel[0][f"{key}_mean"])
            if not have:
                continue
            for key, name in RULES:
                p = rec[f"AlignSSL-pretrained_{name}"]
                s = rec[f"AlignSSL-scratch_{name}"]
                rec[f"ratio_{name}"] = round(p / s, 3) if s > 1e-9 else float("inf")
                pv = per_seed(a.json_dir, bkey[bench], "pre", frac, key)
                sv = per_seed(a.json_dir, bkey[bench], "scr", frac, key)
                if len(pv) > 1 and len(sv) > 1:
                    _, pval = stats.ttest_ind(pv, sv, equal_var=False)
                    rec[f"p_{name}"] = round(float(pval), 4)
                else:
                    rec[f"p_{name}"] = ""
            rows.append(rec)

    if not rows:
        raise SystemExit("no rows: check --table and --json-dir")

    cols = list(rows[0].keys())
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v)
                        for k, v in r.items()})

    for bench in benches:
        sel = [r for r in rows if r["benchmark"] == bench]
        if not sel:
            continue
        lo = sel[0]
        print(f"\n{bench}, smallest budget ({lo['n_labelled']} labels):")
        for _, name in RULES:
            print(f"  {name:8s} pretrained {lo[f'AlignSSL-pretrained_{name}']:.3f} "
                  f"vs scratch {lo[f'AlignSSL-scratch_{name}']:.3f}  "
                  f"ratio {lo[f'ratio_{name}']}x  p={lo[f'p_{name}']}")
        ahead = sum(1 for r in sel[1:]
                    if r["AlignSSL-scratch_F1@tau"] > r["AlignSSL-pretrained_F1@tau"])
        print(f"  at the other {len(sel) - 1} budgets, scratch leads on F1@tau "
              f"in {ahead} of them")
    print(f"\nwrote {a.out}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
