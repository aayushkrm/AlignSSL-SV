#!/usr/bin/env python3
"""Aggregate the cross-population label sweep re-run under the corrected protocol.

WHY THIS RE-RUN EXISTS
----------------------
Section 4.6 of the manuscript reports a *null*: no significant cross-ancestry
effect at any label budget. That null was measured under the pre-correction
label protocol, and under a fixed 0.5 probability cut -- the two defects the
paper itself diagnoses (Sections 3.8 and 4.8).

An earlier plan record dismissed re-running it on the grounds that "a re-run
cannot change a withdrawn claim". That reasoning is wrong and the correction is
the reason this script exists. It holds for a withdrawn *positive* claim. It
does not hold for a null, which is precisely the kind of statement a corrected
re-run can falsify -- and the equal-budget correction is known to have reversed
the direction of the headline label-efficiency contrast elsewhere, so it can
create an effect here as easily as leave the null standing.

WHAT THIS MEASURES
------------------
Train on the in-distribution panel (tensors_all6), evaluate on both the
in-distribution test split and the entirely held-out CEU sample (NA12878),
across six label budgets, three seeds per arm, each pretrained seed using its
OWN pretraining encoder so the error bars span pretraining variance.

Every cell is reported under all three scoring rules, because the paper's
governing finding is that the rule decides the verdict:

  f1_at_half   fixed 0.5 cut          -- the convention this literature inherits
  f1_at_tau    validation-selected    -- tau chosen on a split of the TRAINING
                                        labels, never test, and applied
                                        unchanged to both test sets
  auprc        threshold-free         -- ranking quality, no cut at all

Reporting only the fixed cut is how the original claim survived as long as it
did; a re-run that repeated that mistake would be worthless.

DIRECTION CONVENTION
--------------------
`gap` is in-distribution minus cross-population, so a POSITIVE gap means the
model transfers WORSE than it performs at home. A pretraining benefit for
robustness would show as a SMALLER gap for the pretrained arm, which is a
different question from whether its absolute cross-population score is higher.
Both are reported; conflating them is the error the original section made.

Inputs (results/json_xpop_lowlabel/):
  xpopll_pre_seed{0,1,2}.json       AlignSSL combined, per-seed encoder
  xpopll_scratch_seed{0,1,2}.json   identical architecture, random init

Outputs (results/):
  table26_xpop_lowlabel.csv         per-budget, per-rule, both arms
  stats_xpop_lowlabel.csv           every test this sweep licenses, with the
                                    within-sweep Holm correction applied

Usage:
  python analysis/aggregate_xpop_lowlabel.py \
      --json-dir results/json_xpop_lowlabel --out-dir results
"""
from __future__ import annotations
import argparse, csv, glob, json, os
import numpy as np
from scipy import stats

FRACS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
RULES = ["f1_at_half", "f1_at_tau", "auprc"]
ARMS = {"pre": "AlignSSL-pretrained", "scratch": "AlignSSL-scratch"}


def load(json_dir: str, arm: str) -> list[dict]:
    paths = sorted(glob.glob(os.path.join(json_dir, f"xpopll_{arm}_seed*.json")))
    if not paths:
        raise SystemExit(f"no JSONs for arm '{arm}' in {json_dir}")
    return [json.load(open(p)) for p in paths]


def cell(runs: list[dict], frac: float, site: str, rule: str) -> np.ndarray:
    """Per-seed values for one (budget, test site, scoring rule) cell."""
    vals = []
    for r in runs:
        rows = [x for x in r["label_efficiency"]
                if abs(x["frac"] - frac) < 1e-9]
        if not rows:
            continue
        # the sweep script nests arm results under a mode key; a single-arm
        # run has exactly one such key besides the bookkeeping fields
        modes = [k for k, v in rows[0].items()
                 if isinstance(v, dict) and site in v]
        if not modes:
            continue
        vals.append(float(rows[0][modes[0]][site][rule]))
    return np.asarray(vals, dtype=float)


def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni step-down, returned in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", default="results/json_xpop_lowlabel")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args()

    pre, scr = load(a.json_dir, "pre"), load(a.json_dir, "scratch")

    rows, tests = [], []
    for frac in FRACS:
        for rule in RULES:
            for site in ("in_dist", "xpop"):
                p_v, s_v = cell(pre, frac, site, rule), cell(scr, frac, site, rule)
                if p_v.size == 0 or s_v.size == 0:
                    continue
                t, pval = stats.ttest_ind(p_v, s_v, equal_var=False)
                rows.append({
                    "label_frac": frac, "rule": rule, "site": site,
                    "pretrained_mean": round(float(p_v.mean()), 4),
                    "pretrained_sd": round(float(p_v.std(ddof=1)), 4),
                    "scratch_mean": round(float(s_v.mean()), 4),
                    "scratch_sd": round(float(s_v.std(ddof=1)), 4),
                    "n_seeds_pre": int(p_v.size), "n_seeds_scratch": int(s_v.size),
                    "leader": ("pretrained" if p_v.mean() > s_v.mean()
                               else "scratch" if s_v.mean() > p_v.mean() else "tie"),
                    "t": round(float(t), 4), "p_raw": round(float(pval), 6),
                })
                tests.append(float(pval))

    # generalisation gap: in-dist minus xpop, per arm. A positive gap means the
    # arm transfers worse than it performs at home.
    for frac in FRACS:
        for rule in RULES:
            for key, arm in ARMS.items():
                runs = pre if key == "pre" else scr
                ind, xp = cell(runs, frac, "in_dist", rule), cell(runs, frac, "xpop", rule)
                if ind.size == 0 or xp.size == 0 or ind.size != xp.size:
                    continue
                gap = ind - xp
                rows.append({
                    "label_frac": frac, "rule": rule, "site": f"gap[{arm}]",
                    "pretrained_mean": "", "pretrained_sd": "",
                    "scratch_mean": "", "scratch_sd": "",
                    "n_seeds_pre": int(gap.size), "n_seeds_scratch": "",
                    "leader": "", "t": "",
                    "p_raw": "", "gap_mean": round(float(gap.mean()), 4),
                    "gap_sd": round(float(gap.std(ddof=1)), 4),
                })

    # Holm within this sweep only. The sweep is a multiple-comparison procedure:
    # 6 budgets x 3 rules x 2 sites = up to 36 simultaneous arm contrasts, and
    # reporting the smallest of them as though it were a single test is exactly
    # the defect Section 4.9 audits.
    adj = holm(tests)
    it = iter(adj)
    for r in rows:
        if r.get("p_raw") not in ("", None):
            q = next(it)
            r["p_holm"] = round(q, 6)
            r["survives_holm_0.05"] = bool(q < 0.05)
        else:
            r["p_holm"] = ""
            r["survives_holm_0.05"] = ""

    os.makedirs(a.out_dir, exist_ok=True)
    cols = ["label_frac", "rule", "site", "pretrained_mean", "pretrained_sd",
            "scratch_mean", "scratch_sd", "gap_mean", "gap_sd",
            "n_seeds_pre", "n_seeds_scratch", "leader", "t", "p_raw",
            "p_holm", "survives_holm_0.05"]
    out = os.path.join(a.out_dir, "table26_xpop_lowlabel.csv")
    with open(out, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    stats_rows = [r for r in rows if r.get("p_raw") not in ("", None)]
    with open(os.path.join(a.out_dir, "stats_xpop_lowlabel.csv"), "w",
              newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=["label_frac", "rule", "site", "t",
                                           "p_raw", "p_holm",
                                           "survives_holm_0.05", "leader"])
        w.writeheader()
        for r in stats_rows:
            w.writerow({k: r[k] for k in w.fieldnames})

    n_sig = sum(1 for r in stats_rows if float(r["p_raw"]) < 0.05)
    n_holm = sum(1 for r in stats_rows if r["survives_holm_0.05"] is True)
    print(f"tests={len(stats_rows)} nominal_0.05={n_sig} survives_holm={n_holm}")
    for r in stats_rows:
        if r["survives_holm_0.05"] is True:
            print(f"  SURVIVES: frac={r['label_frac']} {r['rule']} "
                  f"{r['site']} leader={r['leader']} p_holm={r['p_holm']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
