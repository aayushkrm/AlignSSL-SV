#!/usr/bin/env python3
"""Aggregate the label-efficiency curves recomputed under the fixed protocol.

Consumes the `f_*` JSONs produced after two corrections landed:

  1. alignssl/metrics.py -- every arm is scored threshold-free (AUPRC, ROC-AUC)
     and at a threshold selected on a validation split, never on test.
  2. alignssl/protocol.py -- every arm receives the same label budget at each
     label fraction, and the validation split is no longer gated on batch size.

Emits, per benchmark and label fraction, each arm's F1 at the selected
threshold, F1 at the fixed 0.5 cut, and AUPRC -- side by side, because the
gap between the first two is exactly what the second correction exposed.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os

import numpy as np

ARMS = [("pre", "AlignSSL-pretrained"), ("scr", "AlignSSL-scratch"),
        ("dsv", "DeepSV-representation")]
BENCHES = [("uni", "uniform"), ("hn", "candidate-filtered")]


def _rows(path):
    """Yield (frac, n, metrics-dict) from one results JSON, arm-agnostic."""
    d = json.load(open(path))
    for row in d["label_efficiency"]:
        m = row.get("pretrained") or row.get("scratch") or row.get("deepsv") or row
        yield float(row["frac"]), int(row["n"]), m


def collect(ckpt_dir, bench, arm):
    """Return {frac: {metric: [per-seed values]}} plus the budget per frac."""
    acc, budget = {}, {}
    files = sorted(glob.glob(os.path.join(ckpt_dir, f"f_{bench}_{arm}_seed*.json")))
    for f in files:
        for frac, n, m in _rows(f):
            budget[frac] = n
            a = acc.setdefault(frac, {k: [] for k in
                                      ("f1_at_tau", "f1_at_half", "auprc",
                                       "roc_auc", "tau_selected")})
            for k in a:
                v = m.get(k)
                if v is not None and not (isinstance(v, float) and np.isnan(v)):
                    a[k].append(float(v))
    return acc, budget, len(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    out = []
    for bkey, bname in BENCHES:
        for arm, aname in ARMS:
            acc, budget, nseed = collect(a.ckpt_dir, bkey, arm)
            if not acc:
                continue
            for frac in sorted(acc):
                v = acc[frac]
                rec = {"benchmark": bname, "arm": aname, "label_frac": frac,
                       "n_labelled": budget[frac], "n_seeds": nseed}
                for k in ("f1_at_tau", "f1_at_half", "auprc", "roc_auc"):
                    xs = v[k]
                    rec[f"{k}_mean"] = round(float(np.mean(xs)), 4) if xs else ""
                    rec[f"{k}_sd"] = (round(float(np.std(xs, ddof=1)), 4)
                                      if len(xs) > 1 else 0.0)
                taus = v["tau_selected"]
                rec["tau_mean"] = round(float(np.mean(taus)), 3) if taus else ""
                out.append(rec)

    if not out:
        raise SystemExit(f"no f_*.json found under {a.ckpt_dir}")

    cols = list(out[0].keys())
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(out)

    # Console view of the cell the corrections bear on most directly.
    for bkey, bname in BENCHES:
        sel = [r for r in out if r["benchmark"] == bname]
        if not sel:
            continue
        fr = min(r["label_frac"] for r in sel)
        print(f"\n{bname}  @ label_frac={fr}  (n={sel[0]['n_labelled']})")
        print(f"  {'arm':24s} {'F1@tau':>16s} {'F1@0.5':>16s} {'AUPRC':>16s}")
        for r in sel:
            if r["label_frac"] != fr:
                continue
            print(f"  {r['arm']:24s} "
                  f"{r['f1_at_tau_mean']:>8} ±{r['f1_at_tau_sd']:<6} "
                  f"{r['f1_at_half_mean']:>8} ±{r['f1_at_half_sd']:<6} "
                  f"{r['auprc_mean']:>8} ±{r['auprc_sd']:<6}")
    print(f"\nwrote {a.out}  ({len(out)} rows)")


if __name__ == "__main__":
    main()
