#!/usr/bin/env python3
"""Family-wise multiple-comparison correction over every test the paper quotes.

Why
---
The paper quotes 31 significance tests across `results/stats_tests.csv` and
`results/stats_hardneg.csv`, and an internal audit found that none of them
carried a multiplicity adjustment. Several claims stated as "significant at
0.05" rest on raw p-values between 0.016 and 0.028 drawn from families of six
simultaneous tests, where a single nominal hit is close to what one expects
by chance.

What it does
------------
Tests are partitioned into pre-declared families -- one family per sweep of
label fractions, because within a sweep the same contrast is repeated six
times and that is exactly the situation multiplicity correction exists for.
Two adjustments are reported:

  * **Holm-Bonferroni** -- controls the family-wise error rate. The strict
    reading: a claim that survives Holm is one where the probability of ANY
    false positive in its family is below 0.05.
  * **Benjamini-Hochberg** -- controls the false discovery rate. The lenient
    reading, appropriate for the exploratory sweeps (ablation, cross-ancestry)
    where the question is which effects merit follow-up rather than which are
    individually established.

The headline low-label contrast is deliberately left in a family with the
ablation contrasts rather than given a family of its own, so it is corrected
against its own neighbourhood rather than privileged.

Usage
-----
    python analysis/apply_multiplicity.py --results-dir results

Writes `results/stats_multiplicity.csv` and prints a per-family table.
"""
from __future__ import annotations
import argparse
import csv
import os

import numpy as np


def holm(ps):
    """Holm-Bonferroni step-down adjusted p-values."""
    ps = np.asarray(ps, dtype=float)
    m = ps.size
    order = np.argsort(ps)
    adj = np.empty(m)
    running = 0.0
    for i, j in enumerate(order):
        running = max(running, (m - i) * ps[j])
        adj[j] = min(running, 1.0)
    return adj


def benjamini_hochberg(ps):
    """BH step-up adjusted p-values (q-values)."""
    ps = np.asarray(ps, dtype=float)
    m = ps.size
    order = np.argsort(ps)
    adj = np.empty(m)
    running = 1.0
    for i in range(m - 1, -1, -1):
        j = order[i]
        running = min(running, m * ps[j] / (i + 1))
        adj[j] = min(running, 1.0)
    return adj


def build_families(results_dir):
    """Partition every quoted test into pre-declared families."""
    fams: dict[str, list[tuple[str, float]]] = {}

    p_uni = os.path.join(results_dir, "stats_tests.csv")
    if os.path.exists(p_uni):
        rows = list(csv.DictReader(open(p_uni)))
        core, xanc = [], []
        for r in rows:
            item = (f"{r['claim']} | {r['comparison']}", float(r["p_value"]))
            (xanc if r["claim"].startswith("cross-ancestry") else core).append(item)
        if core:
            fams["uniform: label-efficiency and ablation"] = core
        if xanc:
            fams["uniform: cross-ancestry sweep"] = xanc

    p_hn = os.path.join(results_dir, "stats_hardneg.csv")
    if os.path.exists(p_hn):
        rows = list(csv.DictReader(open(p_hn)))
        for comp in sorted({r["comparison"] for r in rows}):
            fams[f"candidate-filtered: {comp}"] = [
                (f"{comp} @{r['label_frac']}", float(r["p"]))
                for r in rows if r["comparison"] == comp]
    return fams


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results")
    ap.add_argument("--alpha", type=float, default=0.05)
    a = ap.parse_args()

    fams = build_families(a.results_dir)
    if not fams:
        raise SystemExit(f"no stats_*.csv found under {a.results_dir}")

    out_rows = []
    n_nominal = n_holm = n_bh = 0
    for fam, items in fams.items():
        names = [n for n, _ in items]
        ps = np.array([p for _, p in items], dtype=float)
        h, q = holm(ps), benjamini_hochberg(ps)
        print("=" * 78)
        print(f"{fam}   (m = {ps.size} simultaneous tests)")
        print(f"  {'test':<46}{'raw p':>9}{'Holm':>9}{'BH q':>9}  verdict")
        for n, p, hh, qq in zip(names, ps, h, q):
            nominal = p < a.alpha
            n_nominal += nominal
            n_holm += hh < a.alpha
            n_bh += qq < a.alpha
            if hh < a.alpha:
                v = "survives Holm"
            elif qq < a.alpha:
                v = "survives BH only"
            elif nominal:
                v = "LOST to multiplicity"
            else:
                v = "not significant"
            print(f"  {n[:46]:<46}{p:>9.4f}{hh:>9.4f}{qq:>9.4f}  {v}")
            out_rows.append({
                "family": fam, "test": n, "m_family": int(ps.size),
                "p_raw": f"{p:.6g}", "p_holm": f"{hh:.6g}", "q_bh": f"{qq:.6g}",
                "nominal_0.05": nominal, "survives_holm_0.05": bool(hh < a.alpha),
                "survives_bh_0.05": bool(qq < a.alpha), "verdict": v})

    dst = os.path.join(a.results_dir, "stats_multiplicity.csv")
    with open(dst, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    print("=" * 78)
    print(f"{len(out_rows)} tests in {len(fams)} families: "
          f"{n_nominal} nominally significant, {n_bh} survive BH, "
          f"{n_holm} survive Holm")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
