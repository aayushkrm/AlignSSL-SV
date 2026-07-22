#!/usr/bin/env python3
"""Aggregate the hardened DAG result JSONs into harmonized figures + tables.

Consumes (all batch-96, num-workers-2 harmonized):
  Combined arm : ft6_results_seed{0,1,2,3}.json          (existing, 4 seeds)
  MAM-only     : abft6h_maeonly_seed{0,1,2}.json          (NEW, distinct pretrain enc/seed)
  VICReg-only  : abft6h_viconly_seed{0,1,2}.json          (NEW, distinct pretrain enc/seed)
  DeepSV       : deepsv6h_results_seed{0,1,2}.json         (NEW, batch-96)
  Cross-pop LL : xpopll_results_seed{0,1,2}.json           (NEW, in-dist vs NA12878 xpop)

Emits:
  results_ablation_4arm_hardened.csv
  results_crosspop_lowlabel.csv
  fig_ablation_4arm_hardened.png
  fig_crosspop_lowlabel.png
Run this AFTER downloading the JSONs from the cluster into ./hardened_json/.
"""
from __future__ import annotations
import json, glob, os
import numpy as np

FRACS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
JDIR = os.environ.get("JDIR", "hardened_json")


def load_le(path):
    """Return dict frac -> F1 for the 'pretrained' arm of a finetune-style json."""
    d = json.load(open(path))
    out = {}
    for row in d["label_efficiency"]:
        f = row["frac"]
        # SSL fine-tune jsons -> 'pretrained'; DeepSV baseline -> 'deepsv'
        if "pretrained" in row:
            out[f] = row["pretrained"]["F1"]
        elif "deepsv" in row:
            out[f] = row["deepsv"]["F1"]
        elif "scratch" in row:
            out[f] = row["scratch"]["F1"]
    return out


def load_scratch(path):
    d = json.load(open(path))
    out = {}
    for row in d["label_efficiency"]:
        if "scratch" in row:
            out[row["frac"]] = row["scratch"]["F1"]
    return out


def agg(paths):
    """Mean/std across seeds -> arrays aligned to FRACS."""
    perseed = [load_le(p) for p in paths]
    M = np.array([[s.get(f, np.nan) for f in FRACS] for s in perseed])
    return np.nanmean(M, 0), np.nanstd(M, 0), M.shape[0]


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    arms = {
        "Combined (MAM+VICReg)": sorted(glob.glob(f"{JDIR}/ft6_results_seed*.json")),
        "MAM-only":              sorted(glob.glob(f"{JDIR}/abft6h_maeonly_seed*.json")),
        "VICReg-only":           sorted(glob.glob(f"{JDIR}/abft6h_viconly_seed*.json")),
        "DeepSV (repr. baseline)": sorted(glob.glob(f"{JDIR}/deepsv6h_results_seed*.json")),
    }
    # scratch from combined arm (from-scratch reference)
    scratch_paths = arms["Combined (MAM+VICReg)"]

    rows = []
    stats = {}
    for name, paths in arms.items():
        if not paths:
            print(f"WARN: no files for {name}")
            continue
        mean, std, nseed = agg(paths)
        stats[name] = (mean, std, nseed)
        for i, f in enumerate(FRACS):
            rows.append({"arm": name, "frac": f, "F1_mean": mean[i],
                         "F1_std": std[i], "n_seed": nseed})

    # from-scratch
    if scratch_paths:
        perseed = [load_scratch(p) for p in scratch_paths]
        M = np.array([[s.get(f, np.nan) for f in FRACS] for s in perseed])
        smean, sstd = np.nanmean(M, 0), np.nanstd(M, 0)
        stats["From scratch"] = (smean, sstd, M.shape[0])
        for i, f in enumerate(FRACS):
            rows.append({"arm": "From scratch", "frac": f, "F1_mean": smean[i],
                         "F1_std": sstd[i], "n_seed": M.shape[0]})

    import csv
    with open("results_ablation_4arm_hardened.csv", "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=["arm", "frac", "F1_mean", "F1_std", "n_seed"])
        w.writeheader(); w.writerows(rows)
    print("wrote results_ablation_4arm_hardened.csv", len(rows), "rows")

    # ---- ablation figure ----
    fig, ax = plt.subplots(figsize=(7, 5))
    order = ["Combined (MAM+VICReg)", "MAM-only", "VICReg-only",
             "From scratch", "DeepSV (repr. baseline)"]
    for name in order:
        if name not in stats:
            continue
        mean, std, nseed = stats[name]
        x = [f * 100 for f in FRACS]
        ax.errorbar(x, mean, yerr=std, marker="o", capsize=3, label=f"{name} (n={nseed})")
    ax.set_xscale("log")
    ax.set_xlabel("Labeled training data (%)")
    ax.set_ylabel("Deletion F1 (test: chr12–22)")
    ax.set_title("Ablation — harmonized (batch 96, per-pretraining-seed error bars)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig("fig_ablation_4arm_hardened.png", dpi=150)
    print("wrote fig_ablation_4arm_hardened.png")

    # ---- cross-pop low-label ----
    xpaths = sorted(glob.glob(f"{JDIR}/xpopll_results_seed*.json"))
    if xpaths:
        indist = {m: [] for m in ["pretrained", "scratch"]}
        xpop = {m: [] for m in ["pretrained", "scratch"]}
        for p in xpaths:
            d = json.load(open(p))
            for m in ["pretrained", "scratch"]:
                ir = {}; xr = {}
                for row in d["label_efficiency"]:
                    if m in row:
                        ir[row["frac"]] = row[m]["in_dist"]["F1"]
                        xr[row["frac"]] = row[m]["xpop"]["F1"]
                indist[m].append([ir.get(f, np.nan) for f in FRACS])
                xpop[m].append([xr.get(f, np.nan) for f in FRACS])
        xrows = []
        for m in ["pretrained", "scratch"]:
            im = np.nanmean(np.array(indist[m]), 0); ist = np.nanstd(np.array(indist[m]), 0)
            xm = np.nanmean(np.array(xpop[m]), 0); xst = np.nanstd(np.array(xpop[m]), 0)
            for i, f in enumerate(FRACS):
                xrows.append({"mode": m, "frac": f, "in_dist_F1": im[i],
                              "in_dist_std": ist[i], "xpop_F1": xm[i],
                              "xpop_std": xst[i], "gap": im[i] - xm[i]})
        with open("results_crosspop_lowlabel.csv", "w", newline="") as fo:
            w = csv.DictWriter(fo, fieldnames=["mode", "frac", "in_dist_F1",
                "in_dist_std", "xpop_F1", "xpop_std", "gap"])
            w.writeheader(); w.writerows(xrows)
        print("wrote results_crosspop_lowlabel.csv", len(xrows), "rows")

        fig2, ax2 = plt.subplots(figsize=(7, 5))
        x = [f * 100 for f in FRACS]
        for m, ls in [("pretrained", "-"), ("scratch", "--")]:
            im = np.nanmean(np.array(indist[m]), 0)
            xm = np.nanmean(np.array(xpop[m]), 0)
            ax2.plot(x, im, ls, marker="o", label=f"{m} in-dist (African)")
            ax2.plot(x, xm, ls, marker="s", label=f"{m} xpop (NA12878 CEU)")
        ax2.set_xscale("log")
        ax2.set_xlabel("Labeled training data (%)")
        ax2.set_ylabel("Deletion F1")
        ax2.set_title("Cross-population generalization vs label budget")
        ax2.legend(fontsize=8); ax2.grid(alpha=0.3)
        fig2.tight_layout(); fig2.savefig("fig_crosspop_lowlabel.png", dpi=150)
        print("wrote fig_crosspop_lowlabel.png")


if __name__ == "__main__":
    main()
