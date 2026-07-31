#!/usr/bin/env python3
"""The hand-crafted-feature control, re-scored threshold-free on both benchmarks.

Twelve alignment summary features (read depth in the window centre and flanks,
their ratio, discordant-pair and soft-clip counts, mapping-quality summaries)
fed to a gradient-boosted tree. Ten seeds per benchmark per label fraction.

This control is the paper's most load-bearing experiment, so it is reported
threshold-free (AUPRC, with the positive rate carried alongside as the chance
level) as well as at a validation-selected threshold.

Its purpose is to bound what the deep results can mean. If a tree on twelve
hand-computed numbers saturates a benchmark from a handful of labels, then a
label-efficiency curve measured on that benchmark is not evidence about
representation learning -- it is evidence about how fast each initialisation
rediscovers a depth ratio.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os

import numpy as np

BENCHES = [("uni", "uniform"), ("hn", "candidate-filtered")]
METRICS = ("auprc", "roc_auc", "f1_at_tau", "f1_at_half")
# Each results row carries BOTH classical models under their own keys. They
# must be named explicitly: an earlier version of this script took whichever
# metric dict appeared first in the row and labelled it "gradient-boosted
# tree", which silently reported the logistic regression instead -- a model
# that is roughly 0.24 AUPRC weaker on the candidate-filtered benchmark.
MODELS = [("hgb", "Classical-GBT"), ("logreg", "Classical-logreg")]


def collect(json_dir, bench, model_key):
    acc = {}
    files = sorted(glob.glob(os.path.join(json_dir, f"f_{bench}_classical_seed*.json")))
    for f in files:
        for row in json.load(open(f))["label_efficiency"]:
            m = row.get(model_key)
            if not isinstance(m, dict):
                continue
            a = acc.setdefault(float(row["frac"]),
                               {k: [] for k in METRICS + ("pos_rate",)})
            a["n"] = int(row["n"])
            for k in METRICS + ("pos_rate",):
                v = m.get(k)
                if v is not None and not (isinstance(v, float) and np.isnan(v)):
                    a[k].append(float(v))
    return acc, len(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = []
    for bkey, bname in BENCHES:
      for mkey, mname in MODELS:
        acc, nseed = collect(a.json_dir, bkey, mkey)
        if not acc:
            continue
        for frac in sorted(acc):
            v = acc[frac]
            rec = {"benchmark": bname, "model": mname, "label_frac": frac,
                   "n_labelled": v["n"], "n_seeds": nseed}
            for k in METRICS:
                xs = v[k]
                rec[f"{k}_mean"] = round(float(np.mean(xs)), 4) if xs else ""
                rec[f"{k}_sd"] = (round(float(np.std(xs, ddof=1)), 4)
                                  if len(xs) > 1 else 0.0)
            rec["chance_auprc"] = (round(float(np.mean(v["pos_rate"])), 4)
                                   if v["pos_rate"] else "")
            rows.append(rec)

    if not rows:
        raise SystemExit(f"no f_*_classical_seed*.json under {a.json_dir}")

    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    for bkey, bname in BENCHES:
        sel = [r for r in rows
               if r["benchmark"] == bname and r["model"] == "Classical-GBT"]
        if not sel:
            continue
        lo, hi = sel[0], sel[-1]
        print(f"\n{bname} (GBT): AUPRC {lo['auprc_mean']:.3f} at {lo['n_labelled']} labels "
              f"-> {hi['auprc_mean']:.3f} at {hi['n_labelled']} "
              f"(chance {hi['chance_auprc']:.2f})")
        span = hi["auprc_mean"] - lo["auprc_mean"]
        frac_of_ceiling = lo["auprc_mean"] / hi["auprc_mean"]
        label_mult = hi["n_labelled"] // max(lo["n_labelled"], 1)
        print(f"  a {label_mult}x increase in labels buys {span:+.3f} AUPRC; "
              f"the smallest budget already reaches "
              f"{100 * frac_of_ceiling:.1f}% of the ceiling")
    print(f"\nwrote {a.out}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
