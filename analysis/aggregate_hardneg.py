#!/usr/bin/env python3
"""Aggregate the hard-negative (candidate-filtering) benchmark.

This is a SEPARATE benchmark from the uniform-negative one, not a corrected
version of it, and the two must not be merged into a single before/after table:

  * Sample scope differs. The uniform-negative results use the six-sample
    fine-tune panel; the beegfs source directory was lost before the
    re-benchmark, so only NA20845 (GIH) and NA12878 (CEU) survived and the
    hard-negative benchmark trains and tests within NA20845.
  * The negative class differs by construction. Uniform negatives are drawn at
    random from the genome; hard negatives are quantile-matched to the
    positives' own centre-versus-flank depth-ratio distribution within each
    multi-scale bin, so a depth-ratio classifier is uninformative by design
    (measured ROC-AUC 0.504 vs 0.955 for uniform negatives).

Because the negative class is redefined, absolute F1 is not comparable across
the two benchmarks. What IS comparable, and what this script is for, is the
*ordering of the arms* -- specifically whether the hand-crafted-feature control
still dominates the deep arms. That is the diagnostic the remediation was for.

Inputs (results/json_hardneg/):
  hn_classical_seed{0,1,2}.json   12-feature logreg + GBT control
  hn_pre_seed{0,1,2}.json         AlignSSL combined objective, distinct
                                  pretraining encoder per seed
  hn_scratch_seed{0,1,2}.json     identical architecture, random init
  hn_deepsv_seed{0,1,2}.json      DeepSV representation baseline

Outputs (results/):
  table6_hardneg_label_efficiency.csv
  table7_hardneg_vs_uniform.csv        arm ordering under both benchmarks
  stats_hardneg.csv                    every test quoted for this benchmark

Usage:
  python analysis/aggregate_hardneg.py --json-dir results/json_hardneg \
      --uniform-table results/table1_label_efficiency.csv --out-dir results
"""
from __future__ import annotations
import argparse, csv, glob, json, os
import numpy as np
from scipy import stats

FRACS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]


def load(json_dir: str, pat: str):
    return [json.load(open(p)) for p in sorted(glob.glob(os.path.join(json_dir, pat)))]


def pick(d, frac, arm, field=None):
    """Fetch one metric, or None when the arm/field is absent. Arms differ in
    schema (the DeepSV-representation baseline records no AUPRC), so callers
    filter Nones rather than assuming uniformity."""
    for r in d["label_efficiency"]:
        if abs(r["frac"] - frac) < 1e-9 and arm in r:
            return r[arm].get(field) if field else r[arm]
    return None


def series(ds, arm, field="F1"):
    """-> [(mean, sd, n, per_seed), ...] over FRACS."""
    out = []
    for f in FRACS:
        v = [pick(d, f, arm, field) for d in ds]
        v = [x for x in v if x is not None]
        out.append((float(np.mean(v)) if v else float("nan"),
                    float(np.std(v)) if v else float("nan"), len(v), v))
    return out


def read_uniform(path):
    """arm -> {frac: F1_mean} from the uniform-negative Table 1."""
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path) as fh:
        for row in csv.DictReader(fh):
            out.setdefault(row["arm"], {})[float(row["label_frac"])] = \
                float(row["F1_mean"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", default="results/json_hardneg")
    ap.add_argument("--uniform-table", default="results/table1_label_efficiency.csv")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args()
    J, O = a.json_dir, a.out_dir
    os.makedirs(O, exist_ok=True)

    cls = load(J, "hn_classical_seed*.json")
    pre = load(J, "hn_pre_seed*.json")
    scr = load(J, "hn_scratch_seed*.json")
    dsv = load(J, "hn_deepsv_seed*.json")
    assert pre and scr and dsv and cls, (
        f"missing hard-negative result JSONs in {J}: "
        f"classical={len(cls)} pre={len(pre)} scratch={len(scr)} deepsv={len(dsv)}")

    # Provenance: each pretrained seed must use its own pretraining encoder, so
    # the reported sd spans the whole self-supervised pipeline, not fine-tuning
    # noise alone. This was an audit finding on the earlier benchmark.
    encs = [d["config"]["encoder"] for d in pre]
    assert len(set(encs)) == len(encs), f"repeated pretraining encoder: {encs}"
    bss = {d["config"]["batch_size"] for d in pre + scr + dsv}
    assert bss == {96}, f"fine-tune batch size not harmonised: {bss}"

    arms = {"AlignSSL-combined": (pre, "pretrained"),
            "AlignSSL-scratch": (scr, "scratch"),
            "DeepSV-representation": (dsv, "deepsv"),
            "Classical-logreg": (cls, "logreg"),
            "Classical-GBT": (cls, "hgb")}
    ser = {k: series(*v) for k, v in arms.items()}
    n_train = [r["n"] for r in pre[0]["label_efficiency"]]

    # ---- Table 6: label efficiency on the hard-negative benchmark -----------
    with open(f"{O}/table6_hardneg_label_efficiency.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["label_frac", "n_train", "arm", "n_seeds",
                    "F1_mean", "F1_sd", "P_mean", "R_mean", "AUPRC_mean",
                    "F1_per_seed"])
        for name, (ds, arm) in arms.items():
            for i, f in enumerate(FRACS):
                m, sd, n, per = ser[name][i]
                P = [x for x in (pick(d, f, arm, "P") for d in ds) if x is not None]
                R = [x for x in (pick(d, f, arm, "R") for d in ds) if x is not None]
                AU = [x for x in (pick(d, f, arm, "AUPRC") for d in ds) if x is not None]
                w.writerow([f, n_train[i], name, n, f"{m:.4f}", f"{sd:.4f}",
                            f"{np.mean(P):.4f}" if P else "",
                            f"{np.mean(R):.4f}" if R else "",
                            f"{np.mean(AU):.4f}" if AU else "",
                            ";".join(f"{x:.4f}" for x in per)])

    # ---- Table 7: does the arm ordering change between benchmarks? ----------
    # The scientific question. Absolute F1 is NOT comparable across benchmarks
    # (different negative class, different sample scope) so the table reports
    # each benchmark's own within-benchmark rank alongside the raw means, and
    # the rank column is what the manuscript may cite.
    uni = read_uniform(a.uniform_table)
    with open(f"{O}/table7_hardneg_vs_uniform.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["label_frac", "arm",
                    "uniform_F1_mean", "uniform_rank",
                    "hardneg_F1_mean", "hardneg_rank",
                    "rank_change"])
        # Rank only over the arms present in BOTH benchmarks. The uniform Table 1
        # additionally carries the two SSL-objective ablation arms, which were not
        # re-run here; ranking 7 arms against 5 would make rank_change an artefact
        # of the differing arm counts rather than a change in ordering.
        shared = [k for k in arms if k in uni]
        if len(shared) < len(arms):
            print(f"note: ranking restricted to {len(shared)} arms present in both "
                  f"benchmarks; absent from uniform table: "
                  f"{sorted(set(arms) - set(shared))}")
        for f in FRACS:
            u_vals = {k: uni[k].get(f) for k in shared}
            h_vals = {k: ser[k][FRACS.index(f)][0] for k in arms}
            u_rank = {k: r + 1 for r, (k, _) in enumerate(
                sorted(((k, v) for k, v in u_vals.items() if v is not None),
                       key=lambda kv: -kv[1]))}
            # hard-negative rank restricted to the same arm set for comparability
            h_rank = {k: r + 1 for r, (k, _) in enumerate(
                sorted(((k, h_vals[k]) for k in u_rank), key=lambda kv: -kv[1]))}
            for k in arms:
                uv, hv = u_vals[k], h_vals[k]
                ur, hr = u_rank.get(k), h_rank.get(k)
                w.writerow([f, k,
                            f"{uv:.4f}" if uv is not None else "",
                            ur if ur else "",
                            f"{hv:.4f}",
                            hr,
                            (ur - hr) if (ur and hr) else ""])

    # ---- Statistical tests -------------------------------------------------
    # Three seeds per arm. Welch's t-test on n=3 has very low power, so every
    # row carries n and the paper must not read a null as evidence of
    # equivalence. Reported so the claim and its power are visible together.
    rows = []

    def test(label, x, y, frac):
        x = [v for v in x if v is not None]
        y = [v for v in y if v is not None]
        if len(x) < 2 or len(y) < 2:
            rows.append([label, frac, len(x), len(y), "", "", "", "insufficient seeds"])
            return
        t, p = stats.ttest_ind(x, y, equal_var=False)
        rows.append([label, frac, len(x), len(y),
                     f"{np.mean(x) - np.mean(y):+.4f}", f"{t:.3f}", f"{p:.4f}",
                     "significant at 0.05" if p < 0.05 else "not significant"])

    for i, f in enumerate(FRACS):
        test("pretrained vs scratch", ser["AlignSSL-combined"][i][3],
             ser["AlignSSL-scratch"][i][3], f)
        test("pretrained vs DeepSV-representation", ser["AlignSSL-combined"][i][3],
             ser["DeepSV-representation"][i][3], f)
        # The decisive one: does the 12-feature control still beat the deep arm?
        test("pretrained vs Classical-GBT", ser["AlignSSL-combined"][i][3],
             ser["Classical-GBT"][i][3], f)

    with open(f"{O}/stats_hardneg.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["comparison", "label_frac", "n_a", "n_b",
                    "mean_diff", "t", "p", "verdict"])
        w.writerows(rows)

    # ---- Console verdict ---------------------------------------------------
    print(f"wrote {O}/table6_hardneg_label_efficiency.csv, "
          f"{O}/table7_hardneg_vs_uniform.csv, {O}/stats_hardneg.csv")
    print("\nF1 by label fraction (hard-negative benchmark):")
    print("  frac  " + "".join(f"{k[:14]:>16}" for k in arms))
    for i, f in enumerate(FRACS):
        print(f"  {f:<5} " + "".join(
            f"{ser[k][i][0]:>10.3f}±{ser[k][i][1]:<5.3f}" for k in arms))

    gbt_wins = sum(1 for i in range(len(FRACS))
                   if ser["Classical-GBT"][i][0] > ser["AlignSSL-combined"][i][0])
    print(f"\nClassical-GBT beats AlignSSL-combined at {gbt_wins}/{len(FRACS)} "
          f"label fractions.")
    print("Remediation succeeded only if this is a minority; report it either way."
          if gbt_wins else
          "Remediation succeeded: the deep arm now leads at every label budget.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
