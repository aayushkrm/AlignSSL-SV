#!/usr/bin/env python3
"""Single source of truth: derive EVERY manuscript table from the canonical
per-seed result JSONs, with the statistical tests the claims rest on.

This script supersedes analysis/aggregate_hardened.py, whose output filenames
and column schemas had drifted from the files committed under results/ and
which computed neither calibration nor length-stratified metrics.

Inputs (results/json/, all fine-tuned at batch 96, num_workers 2, 30 epochs):
  ft6_results_seed{0,1,2,3}.json      combined MAM+VICReg; encoder_ssl_seed{0..3}
  abft6h_maeonly_seed{0,1,2}.json     MAM-only;    encoder_abl_maeonly_120k[_seed{1,2}]
  abft6h_viconly_seed{0,1,2}.json     VICReg-only; encoder_abl_viconly_120k[_seed{1,2}]
  deepsv6h_results_seed{0,1,2}.json   DeepSV-representation baseline (no encoder)
  xpopll_results_seed{0,1,2}.json     cross-ancestry label sweep (CEU held out)
  classical_results_seed{0,1,2}.json  hand-crafted-feature control (optional)

Every pretrained arm's seeds use a DISTINCT pretraining encoder, so the
reported standard deviations span the full self-supervised pipeline rather
than fine-tuning noise alone. The script asserts this.

Outputs (results/):
  table1_label_efficiency.csv     F1/P/R/AUPRC per arm per label fraction
  table2_calibration.csv          ECE + temperature at full supervision
  table3_length_strata.csv        recall by deletion-length bin at full supervision
  table4_ablation.csv             SSL-objective ablation per label fraction
  table5_cross_ancestry.csv       in-distribution vs held-out-CEU F1 per fraction
  stats_tests.csv                 every significance test cited in the paper

Usage:  python analysis/aggregate_all.py --json-dir results/json --out-dir results
"""
from __future__ import annotations
import argparse, csv, glob, json, os
import numpy as np
from scipy import stats

FRACS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]


def load(json_dir: str, pat: str):
    return [json.load(open(p)) for p in sorted(glob.glob(os.path.join(json_dir, pat)))]


def pick(d, frac, arm, field=None):
    """Fetch one metric. Returns None when the arm or the field is absent --
    arms differ in schema (the DeepSV-representation baseline records no
    AUPRC), so callers must filter Nones rather than assume a uniform schema."""
    for r in d["label_efficiency"]:
        if abs(r["frac"] - frac) < 1e-9 and arm in r:
            return r[arm].get(field) if field else r[arm]
    return None


def series(ds, arm, field="F1"):
    """-> (mean, sd, n, per_seed_list) across seeds, per label fraction."""
    out = []
    for f in FRACS:
        v = [pick(d, f, arm, field) for d in ds]
        v = [x for x in v if x is not None]
        out.append((float(np.mean(v)), float(np.std(v)), len(v), v))
    return out


def ms(x):
    return f"{np.mean(x):.4f}", f"{np.std(x):.4f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-dir", default="results/json")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args()
    J, O = a.json_dir, a.out_dir
    os.makedirs(O, exist_ok=True)

    ft6 = load(J, "ft6_results_seed*.json")
    mam = load(J, "abft6h_maeonly_seed*.json")
    vic = load(J, "abft6h_viconly_seed*.json")
    dsv = load(J, "deepsv6h_results_seed*.json")
    xll = load(J, "xpopll_results_seed*.json")
    cls = load(J, "classical_results_seed*.json")
    assert ft6 and mam and vic and dsv and xll, "missing canonical result JSONs"

    # --- provenance assertion: distinct pretraining encoder per seed ----------
    for nm, ds in [("combined", ft6), ("MAM-only", mam), ("VICReg-only", vic)]:
        encs = [d["config"]["encoder"] for d in ds]
        assert len(set(encs)) == len(encs), f"{nm}: repeated encoder {encs}"
    bss = {d["config"]["batch_size"] for d in ft6 + mam + vic + dsv + xll}
    assert bss == {96}, f"fine-tune batch size not harmonised: {bss}"

    n_train = [r["n"] for r in ft6[0]["label_efficiency"]]
    arms = {"AlignSSL-combined": series(ft6, "pretrained"),
            "AlignSSL-scratch": series(ft6, "scratch"),
            "AlignSSL-MAM-only": series(mam, "pretrained"),
            "AlignSSL-VICReg-only": series(vic, "pretrained"),
            "DeepSV-representation": series(dsv, "deepsv")}
    if cls:
        arms["Classical-logreg"] = series(cls, "logreg")
        arms["Classical-GBT"] = series(cls, "hgb")

    # ---- Table 1: label efficiency ------------------------------------------
    with open(f"{O}/table1_label_efficiency.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["label_frac", "n_train", "arm", "n_seeds",
                    "F1_mean", "F1_sd", "P_mean", "R_mean", "AUPRC_mean", "F1_per_seed"])
        for name, se in arms.items():
            src = {"AlignSSL-combined": (ft6, "pretrained"),
                   "AlignSSL-scratch": (ft6, "scratch"),
                   "AlignSSL-MAM-only": (mam, "pretrained"),
                   "AlignSSL-VICReg-only": (vic, "pretrained"),
                   "DeepSV-representation": (dsv, "deepsv"),
                   "Classical-logreg": (cls, "logreg"),
                   "Classical-GBT": (cls, "hgb")}[name]
            ds, arm = src
            for i, f in enumerate(FRACS):
                m, sd, n, per = se[i]
                P = [pick(d, f, arm, "P") for d in ds]
                R = [pick(d, f, arm, "R") for d in ds]
                AU = [pick(d, f, arm, "AUPRC") for d in ds]
                P = [x for x in P if x is not None]; R = [x for x in R if x is not None]
                AU = [x for x in AU if x is not None]
                w.writerow([f, n_train[i], name, n, f"{m:.4f}", f"{sd:.4f}",
                            f"{np.mean(P):.4f}" if P else "",
                            f"{np.mean(R):.4f}" if R else "",
                            f"{np.mean(AU):.4f}" if AU else "",
                            ";".join(f"{x:.4f}" for x in per)])

    # ---- Table 2: calibration at full supervision ---------------------------
    with open(f"{O}/table2_calibration.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["arm", "n_seeds", "ECE_mean", "ECE_sd", "ECE_median",
                    "T_mean", "T_sd", "ECE_per_seed"])
        for name, (ds, arm) in [("AlignSSL-combined", (ft6, "pretrained")),
                                ("AlignSSL-scratch", (ft6, "scratch")),
                                ("DeepSV-representation", (dsv, "deepsv"))]:
            e = [pick(d, 1.0, arm, "ece") for d in ds]
            t = [pick(d, 1.0, arm, "temperature") for d in ds]
            w.writerow([name, len(e), f"{np.mean(e):.4f}", f"{np.std(e):.4f}",
                        f"{np.median(e):.4f}", f"{np.mean(t):.3f}", f"{np.std(t):.3f}",
                        ";".join(f"{x:.4f}" for x in e)])

    # ---- Table 3: length-stratified recall ----------------------------------
    with open(f"{O}/table3_length_strata.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["length_bin_bp", "n_test", "arm", "n_seeds",
                    "recall_mean", "recall_sd", "recall_per_seed"])
        bins = list(pick(ft6[0], 1.0, "pretrained", "length_strata").keys())
        for b in bins:
            for name, (ds, arm) in [("AlignSSL-combined", (ft6, "pretrained")),
                                    ("AlignSSL-scratch", (ft6, "scratch")),
                                    ("DeepSV-representation", (dsv, "deepsv"))]:
                v = [pick(d, 1.0, arm, "length_strata")[b]["recall"] for d in ds]
                nte = pick(ds[0], 1.0, arm, "length_strata")[b]["n"]
                w.writerow([b, nte, name, len(v), f"{np.mean(v):.4f}",
                            f"{np.std(v):.4f}", ";".join(f"{x:.4f}" for x in v)])

    # ---- Table 4: SSL-objective ablation ------------------------------------
    with open(f"{O}/table4_ablation.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["label_frac", "n_train", "objective", "n_pretrain_seeds",
                    "F1_mean", "F1_sd", "F1_per_seed"])
        for name in ["AlignSSL-MAM-only", "AlignSSL-VICReg-only", "AlignSSL-combined"]:
            for i, f in enumerate(FRACS):
                m, sd, n, per = arms[name][i]
                w.writerow([f, n_train[i], name.replace("AlignSSL-", ""), n,
                            f"{m:.4f}", f"{sd:.4f}", ";".join(f"{x:.4f}" for x in per)])

    # ---- Table 5: cross-ancestry -------------------------------------------
    with open(f"{O}/table5_cross_ancestry.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["label_frac", "arm", "n_seeds", "in_dist_F1_mean", "in_dist_F1_sd",
                    "heldout_CEU_F1_mean", "heldout_CEU_F1_sd", "gap_mean",
                    "welch_p_CEU_vs_scratch"])
        for f in FRACS:
            pc = [pick(d, f, "pretrained")["xpop"]["F1"] for d in xll]
            sc = [pick(d, f, "scratch")["xpop"]["F1"] for d in xll]
            p = stats.ttest_ind(pc, sc, equal_var=False).pvalue
            for arm, lbl in [("pretrained", "AlignSSL-combined"), ("scratch", "AlignSSL-scratch")]:
                ind = [pick(d, f, arm)["in_dist"]["F1"] for d in xll]
                xp = [pick(d, f, arm)["xpop"]["F1"] for d in xll]
                w.writerow([f, lbl, len(ind), f"{np.mean(ind):.4f}", f"{np.std(ind):.4f}",
                            f"{np.mean(xp):.4f}", f"{np.std(xp):.4f}",
                            f"{np.mean(ind) - np.mean(xp):+.4f}",
                            f"{p:.4f}" if arm == "pretrained" else ""])

    # ---- statistical tests behind every claim -------------------------------
    T = []
    a1 = [pick(d, 0.01, "pretrained", "F1") for d in ft6]
    s1 = [pick(d, 0.01, "scratch", "F1") for d in ft6]
    r = stats.ttest_rel(a1, s1)
    T.append(["headline low-label gain", "combined vs scratch @1% labels",
              "paired t-test (same 4 seeds)", f"{r.statistic:.3f}", f"{r.pvalue:.2e}",
              f"{np.mean(a1):.4f} vs {np.mean(s1):.4f}",
              f"{np.mean(a1)/max(np.mean(s1),1e-9):.1f}x"])
    for nm, ds in [("combined", ft6), ("MAM-only", mam), ("VICReg-only", vic)]:
        v = [pick(d, 0.01, "pretrained", "F1") for d in ds]
        r = stats.ttest_ind(v, s1, equal_var=False)
        T.append([f"low-label gain ({nm})", f"{nm} vs scratch @1%", "Welch t-test",
                  f"{r.statistic:.3f}", f"{r.pvalue:.2e}",
                  f"{np.mean(v):.4f} vs {np.mean(s1):.4f}",
                  f"{np.mean(v)/max(np.mean(s1),1e-9):.1f}x"])
    a100 = [pick(d, 1.0, "pretrained", "F1") for d in ft6]
    s100 = [pick(d, 1.0, "scratch", "F1") for d in ft6]
    r = stats.ttest_rel(a100, s100)
    T.append(["convergence at full supervision", "combined vs scratch @100%",
              "paired t-test (same 4 seeds)", f"{r.statistic:.3f}", f"{r.pvalue:.4f}",
              f"{np.mean(a100):.4f} vs {np.mean(s100):.4f}",
              f"scratch higher by {np.mean(s100)-np.mean(a100):.4f}"])
    m100 = [pick(d, 1.0, "pretrained", "F1") for d in mam]
    r = stats.ttest_ind(a100, m100, equal_var=False)
    T.append(["ablation @100%", "combined vs MAM-only @100%", "Welch t-test",
              f"{r.statistic:.3f}", f"{r.pvalue:.4f}",
              f"{np.mean(a100):.4f} vs {np.mean(m100):.4f}", "not significant"])
    m1 = [pick(d, 0.01, "pretrained", "F1") for d in mam]
    r = stats.ttest_ind(m1, a1, equal_var=False)
    T.append(["ablation @1%", "MAM-only vs combined @1%", "Welch t-test",
              f"{r.statistic:.3f}", f"{r.pvalue:.4f}",
              f"{np.mean(m1):.4f} vs {np.mean(a1):.4f}", "not significant"])
    for f in FRACS:
        pc = [pick(d, f, "pretrained")["xpop"]["F1"] for d in xll]
        sc = [pick(d, f, "scratch")["xpop"]["F1"] for d in xll]
        r = stats.ttest_ind(pc, sc, equal_var=False)
        T.append([f"cross-ancestry @{f:g}", "combined vs scratch, held-out CEU F1",
                  "Welch t-test", f"{r.statistic:.3f}", f"{r.pvalue:.4f}",
                  f"{np.mean(pc):.4f} vs {np.mean(sc):.4f}",
                  "significant" if r.pvalue < 0.05 else "not significant"])
    with open(f"{O}/stats_tests.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["claim", "comparison", "test", "statistic", "p_value",
                    "means", "note"])
        w.writerows(T)

    print(f"wrote 6 tables to {O}/  "
          f"(seeds: combined {len(ft6)}, MAM {len(mam)}, VICReg {len(vic)}, "
          f"DeepSV {len(dsv)}, cross-anc {len(xll)}, classical {len(cls)})")


if __name__ == "__main__":
    main()
