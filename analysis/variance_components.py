#!/usr/bin/env python
"""Decompose fine-tuning variance into data-split and training-run components.

Why this exists
---------------
Every benchmark in this paper reports mean +/- sd over three "seeds", where a
seed simultaneously fixes (a) the labelled subset drawn at each budget and (b)
the torch RNG stream that drives weight initialisation, batch shuffling and
dropout. A single number over three seeds therefore estimates the TOTAL
variance but says nothing about which of the two sources dominates -- and the
answer matters, because it sets the smallest effect the design can resolve.

The cross-population low-label sweep affords the decomposition for free, by
accident of how it was run. ``cross_pop_lowlabel.py`` seeds once and then loops
``["pretrained", "scratch"]``, so the from-scratch arm inherits a torch stream
already advanced by the pretrained arm. Running the script twice per seed --
once with ``--encoder`` (both arms) and once without (scratch only) -- yields
TWO from-scratch runs per seed that share the labelled subset exactly (it comes
from ``np.random.default_rng(seed)``, re-created per invocation, and the
recorded ``n_train`` confirms it) and differ ONLY in the torch stream.

That is a controlled contrast:

  within-split sd  = training-run noise at fixed data (torch stream only)
  between-split sd = variation of the split means (data split + run)

Reported per (rule, site, budget) cell, plus the minimum detectable effect a
paired n=3 design achieves given the observed total sd.

Usage:
    python analysis/variance_components.py --json-dir results/json_xpop_lowlabel \
        --out results/table27_variance_components.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import os

import numpy as np
from scipy import stats

SEEDS = (0, 1, 2)
FRACS = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0)
RULES = ("f1_at_half", "f1_at_tau", "auprc")
SITES = ("in_dist", "xpop")


def _row(doc: dict, frac: float, mode: str):
    for r in doc["label_efficiency"]:
        if abs(r["frac"] - frac) < 1e-9 and isinstance(r.get(mode), dict):
            return r[mode]
    return None


def load_pairs(json_dir: str) -> tuple[dict, dict]:
    """Return {seed: doc} for the two-arm and the scratch-only invocations."""
    P, Q = {}, {}
    for s in SEEDS:
        p = os.path.join(json_dir, f"xpopll_pre_seed{s}.json")
        q = os.path.join(json_dir, f"xpopll_scratch_seed{s}.json")
        if os.path.exists(p) and os.path.exists(q):
            P[s], Q[s] = json.load(open(p)), json.load(open(q))
    if not P:
        raise SystemExit(f"no paired xpopll JSONs in {json_dir}")
    return P, Q


def assert_same_split(P: dict, Q: dict) -> None:
    """The decomposition is only valid if the two runs share the labelled subset.

    ``n_train`` is the recorded size of the drawn subset at each budget. Equal
    sizes at every budget is a necessary condition; the subsets are drawn from a
    generator re-created from the same seed, so equality of the recorded sizes
    together with identical seeds is the strongest check the artefacts support.
    """
    for s in P:
        a = [r["n_train"] for r in P[s]["label_efficiency"]]
        b = [r["n_train"] for r in Q[s]["label_efficiency"]]
        assert a == b, f"seed {s}: label budgets differ ({a} vs {b}) -- not a controlled pair"
        assert P[s]["config"]["seed"] == Q[s]["config"]["seed"], f"seed {s}: seed mismatch"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", default="results/json_xpop_lowlabel")
    ap.add_argument("--out", default="results/table27_variance_components.csv")
    a = ap.parse_args()

    P, Q = load_pairs(a.json_dir)
    assert_same_split(P, Q)
    seeds = sorted(P)

    rows = []
    for rule in RULES:
        for site in SITES:
            for frac in FRACS:
                within, means = [], []
                for s in seeds:
                    rp, rq = _row(P[s], frac, "scratch"), _row(Q[s], frac, "scratch")
                    if rp is None or rq is None:
                        continue
                    pair = np.array([float(rp[site][rule]), float(rq[site][rule])])
                    within.append(pair.std(ddof=1))
                    means.append(pair.mean())
                if len(means) < 2:
                    continue
                sw = float(np.mean(within))              # run noise at fixed data
                sb = float(np.std(means, ddof=1))        # split-mean spread
                # Total sd a single-run-per-seed design would report.
                st = float(np.sqrt(sb ** 2 + sw ** 2))
                # Two-sided paired MDE at n=3, alpha=.05, power=.80.
                tcrit = stats.t.ppf(0.975, len(means) - 1)
                tpow = stats.t.ppf(0.80, len(means) - 1)
                mde = float((tcrit + tpow) * st / np.sqrt(len(means)))
                rows.append({
                    "rule": rule, "site": site, "label_frac": frac,
                    "n_splits": len(means), "runs_per_split": 2,
                    "sd_within_split": round(sw, 4),
                    "sd_between_split": round(sb, 4),
                    "sd_total": round(st, 4),
                    "within_over_between": round(sw / sb, 3) if sb > 1e-9 else "",
                    "run_noise_share": round(sw ** 2 / st ** 2, 3) if st > 1e-9 else "",
                    "mde_paired_n3": round(mde, 4),
                })

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    ratios = np.array([r["within_over_between"] for r in rows
                       if isinstance(r["within_over_between"], float)])
    share = np.array([r["run_noise_share"] for r in rows
                      if isinstance(r["run_noise_share"], float)])
    print(f"cells={len(rows)} median_within_over_between={np.median(ratios):.2f} "
          f"cells_run_noise_dominates={int((ratios >= 1).sum())}/{ratios.size} "
          f"median_run_noise_share={np.median(share):.2f} "
          f"median_mde={np.median([r['mde_paired_n3'] for r in rows]):.4f}")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
