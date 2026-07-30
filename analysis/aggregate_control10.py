#!/usr/bin/env python3
"""Aggregate the 10-seed hand-crafted-feature control on both benchmarks.

Why 10 seeds
------------
The hand-crafted control is this paper's central *negative* result: it is the
evidence that the uniform benchmark is separable without any learned
representation, and therefore that label-efficiency numbers measured on it
report benchmark structure as much as model quality. A negative result of that
weight should not rest on three seeds. The control is pure CPU (12 summary
features, logistic regression and gradient-boosted trees), so it costs a few
CPU-minutes per seed and the seed count is free -- 10 seeds on both
benchmarks, run as 20 parallel array tasks.

Primary metric is AUPRC, which is threshold-free and therefore immune to the
fixed-0.5-cut defect that `alignssl.metrics` was written to fix. Chance level
is the positive rate (0.25 by construction of the negative sampler), so an
AUPRC near 0.25 is a model that has learned nothing.

Usage
-----
    python analysis/aggregate_control10.py --json-dir <dir> --out-dir results
"""
from __future__ import annotations
import argparse
import csv
import glob
import json
import os

import numpy as np


def load(json_dir, pattern):
    out = {}
    for f in sorted(glob.glob(os.path.join(json_dir, pattern))):
        seed = int(f.split("seed")[-1].split(".")[0])
        out[seed] = json.load(open(f))
    if not out:
        raise SystemExit(f"no files matching {pattern} in {json_dir}")
    return out


def ms(v):
    v = np.asarray(v, dtype=float)
    return float(v.mean()), float(v.std(ddof=1)) if v.size > 1 else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", required=True)
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args()

    rows = []
    for pattern, bench in [("p10_classical_seed*.json", "uniform"),
                           ("p10_hn_classical_seed*.json", "candidate-filtered")]:
        ds = load(a.json_dir, pattern)
        seeds = sorted(ds)
        fracs = [r["frac"] for r in ds[seeds[0]]["label_efficiency"]]
        print("=" * 78)
        print(f"{bench}: n_seeds={len(seeds)} n_test={ds[seeds[0]]['n_test']} "
              f"pool={ds[seeds[0]]['n_train_pool']}")
        print(f"{'frac':>6} {'GBT AUPRC':>17} {'GBT F1@tau':>17} "
              f"{'logreg AUPRC':>17} {'chance':>7}")
        for i, fr in enumerate(fracs):
            g = [ds[s]["label_efficiency"][i]["hgb"] for s in seeds]
            l = [ds[s]["label_efficiency"][i]["logreg"] for s in seeds]
            gap_m, gap_s = ms([d["auprc"] for d in g])
            gf_m, gf_s = ms([d["f1_at_tau"] for d in g])
            lap_m, lap_s = ms([d["auprc"] for d in l])
            chance, _ = ms([d["pos_rate"] for d in g])
            print(f"{fr:>6} {gap_m:>8.4f}±{gap_s:<8.4f} {gf_m:>8.4f}±{gf_s:<8.4f} "
                  f"{lap_m:>8.4f}±{lap_s:<8.4f} {chance:>7.4f}")
            rows.append({
                "benchmark": bench, "label_frac": fr, "n_seeds": len(seeds),
                "n_labelled": ds[seeds[0]]["label_efficiency"][i]["n"],
                "gbt_auprc_mean": f"{gap_m:.4f}", "gbt_auprc_sd": f"{gap_s:.4f}",
                "gbt_f1_at_tau_mean": f"{gf_m:.4f}", "gbt_f1_at_tau_sd": f"{gf_s:.4f}",
                "logreg_auprc_mean": f"{lap_m:.4f}", "logreg_auprc_sd": f"{lap_s:.4f}",
                "chance_auprc": f"{chance:.4f}"})

    os.makedirs(a.out_dir, exist_ok=True)
    dst = os.path.join(a.out_dir, "table10_control10.csv")
    with open(dst, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("=" * 78)
    print(f"wrote {dst}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
