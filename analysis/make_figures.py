#!/usr/bin/env python3
"""Regenerate every manuscript figure from the canonical tables in results/.

The figures in results/ were originally produced ad hoc, which made them the
one class of manuscript object with no committed provenance. This script closes
that gap: it reads only the canonical numbered CSVs that
analysis/aggregate_all.py emits, so a figure can never disagree with the table
it is drawn from.

    python analysis/make_figures.py --results-dir results

Emits, overwriting in place:
    figure1_label_efficiency.png   Label-efficiency sweep, deep arms
    figure2_classical_control.png  Classical controls vs deep arms + untrained AUC
    figure3_length_strata.png      Recall by deletion length
    figure4_ssl_ablation.png       MAM vs VICReg vs combined
    figure5_cross_ancestry.png     In-distribution vs held-out CEU
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------- house style
# Colour is threaded consistently across all five panels: one hue per arm,
# reused wherever that arm appears, so a reader never has to re-learn the key.
COLOUR = {
    "AlignSSL-combined": "#1f4e79",
    "AlignSSL-scratch": "#a98261",
    "DeepSV-representation": "#8c8c8c",
    "Classical-GBT": "#c0392b",
    "Classical-logreg": "#e08e79",
    "AlignSSL-MAM-only": "#2e7d5b",
    "AlignSSL-VICReg-only": "#7b5aa6",
}
LABEL = {
    "AlignSSL-combined": "AlignSSL (pretrained)",
    "AlignSSL-scratch": "AlignSSL (from scratch)",
    "DeepSV-representation": "DeepSV representation",
    "Classical-GBT": "Classical GBT (12 features)",
    "Classical-logreg": "Classical logistic regression",
    "AlignSSL-MAM-only": "MAM only",
    "AlignSSL-VICReg-only": "VICReg only",
}
OBJ_COLOUR = {
    "MAM-only": COLOUR["AlignSSL-MAM-only"],
    "VICReg-only": COLOUR["AlignSSL-VICReg-only"],
    "combined": COLOUR["AlignSSL-combined"],
}

RC = {
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "lines.linewidth": 1.6,
    "lines.markersize": 4.5,
}


def read(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"missing canonical table: {path}")
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def by_arm(rows, key: str, xkey: str, ykey: str, sdkey: str | None):
    """Group rows into {arm: (x, y, sd)} with x sorted ascending."""
    acc = defaultdict(list)
    for r in rows:
        sd = float(r[sdkey]) if sdkey and r.get(sdkey) else 0.0
        acc[r[key]].append((float(r[xkey]), float(r[ykey]), sd))
    out = {}
    for arm, pts in acc.items():
        pts.sort()
        x, y, s = zip(*pts)
        out[arm] = (np.array(x), np.array(y), np.array(s))
    return out


def pct_axis(ax, x):
    ax.set_xscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{v*100:g}" for v in x])
    ax.set_xlabel("Labelled training windows (% of 21,016)")


# ------------------------------------------------------------------ figure 1
def figure1(res: Path, out: Path) -> None:
    rows = read(res / "table1_label_efficiency.csv")
    arms = ["AlignSSL-combined", "AlignSSL-scratch", "DeepSV-representation"]
    g = by_arm([r for r in rows if r["arm"] in arms], "arm",
               "label_frac", "F1_mean", "F1_sd")
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    for arm in arms:
        x, y, sd = g[arm]
        ax.plot(x, y, "-o", color=COLOUR[arm], label=LABEL[arm],
                zorder=3 if arm == "AlignSSL-combined" else 2)
        ax.fill_between(x, y - sd, y + sd, color=COLOUR[arm], alpha=0.15,
                        linewidth=0)
    x = g[arms[0]][0]
    pct_axis(ax, x)
    ax.set_ylabel("Deletion F1 (held-out chr12–22)")
    ax.set_ylim(0, 1.0)
    # annotate the headline gap at the smallest budget
    lo_p = g["AlignSSL-combined"][1][0]
    lo_s = g["AlignSSL-scratch"][1][0]
    ax.annotate("", xy=(x[0], lo_p), xytext=(x[0], lo_s),
                arrowprops=dict(arrowstyle="<->", lw=0.9, color="0.25",
                                shrinkA=2, shrinkB=2))
    ax.annotate(f"{lo_p / max(lo_s, 1e-9):.0f}\u00d7 F1\nat 1% labels",
                xy=(x[0], (lo_p + lo_s) / 2), xytext=(x[0] * 1.35, 0.20),
                fontsize=8, color="0.25", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.6, color="0.55"))
    ax.set_title("Self-supervised pretraining buys label efficiency")
    ax.legend(loc="lower right", frameon=False)
    fig.savefig(out / "figure1_label_efficiency.png")
    plt.close(fig)


# ------------------------------------------------------------------ figure 2
def figure2(res: Path, out: Path) -> None:
    rows = read(res / "table1_label_efficiency.csv")
    feats = read(res / "table6_single_feature_auc.csv")
    arms = ["Classical-GBT", "Classical-logreg", "AlignSSL-combined",
            "AlignSSL-scratch", "DeepSV-representation"]
    g = by_arm([r for r in rows if r["arm"] in arms], "arm",
               "label_frac", "F1_mean", "F1_sd")
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.4),
                             gridspec_kw=dict(width_ratios=[1.15, 1.0], wspace=0.42))
    ax = axes[0]
    for arm in arms:
        x, y, sd = g[arm]
        classical = arm.startswith("Classical")
        ax.plot(x, y, "-s" if classical else "-o", color=COLOUR[arm],
                label=LABEL[arm], linestyle="-" if classical else "--",
                zorder=3 if classical else 2)
        ax.fill_between(x, y - sd, y + sd, color=COLOUR[arm], alpha=0.12,
                        linewidth=0)
    pct_axis(ax, g[arms[0]][0])
    ax.set_ylabel("Deletion F1 (held-out chr12–22)")
    ax.set_ylim(0, 1.0)
    ax.set_title("Hand-engineered features beat every deep arm")
    ax.legend(loc="lower right", frameon=False)

    # right panel: untrained single-feature separability
    ax = axes[1]
    feats = sorted(feats, key=lambda r: float(r["auc_oriented"]))
    names = [r["feature"].replace("_", " ") for r in feats]
    vals = [float(r["auc_oriented"]) for r in feats]
    bars = ax.barh(names, vals, color="#c0392b", alpha=0.85, height=0.72)
    bars[-1].set_color("#7b1a10")
    ax.axvline(0.5, color="0.3", lw=0.9, ls=":")
    ax.text(0.503, len(names) - 0.4, "chance", fontsize=7, color="0.3",
            ha="left", va="center")
    ax.set_xlim(0.45, 1.06)
    ax.set_xlabel("Orientation-corrected ROC-AUC (untrained)")
    ax.set_title("A single raw feature nearly solves the task")
    for b, v in zip(bars, vals):
        ax.text(v + 0.008, b.get_y() + b.get_height() / 2, f"{v:.3f}",
                va="center", fontsize=7)
    fig.savefig(out / "figure2_classical_control.png")
    plt.close(fig)


# ------------------------------------------------------------------ figure 3
def figure3(res: Path, out: Path) -> None:
    rows = read(res / "table3_length_strata.csv")
    arms = ["AlignSSL-combined", "AlignSSL-scratch", "DeepSV-representation"]
    bins, seen = [], set()
    for r in rows:
        if r["length_bin_bp"] not in seen:
            seen.add(r["length_bin_bp"])
            bins.append(r["length_bin_bp"])
    idx = {b: i for i, b in enumerate(bins)}
    fig, ax = plt.subplots(figsize=(6.0, 3.9))
    w = 0.26
    for k, arm in enumerate(arms):
        sub = [r for r in rows if r["arm"] == arm]
        sub.sort(key=lambda r: idx[r["length_bin_bp"]])
        xs = np.arange(len(bins)) + (k - 1) * w
        ys = [float(r["recall_mean"]) for r in sub]
        es = [float(r["recall_sd"]) for r in sub]
        ax.bar(xs, ys, width=w, color=COLOUR[arm], label=LABEL[arm],
               yerr=es, capsize=2, error_kw=dict(lw=0.8))
    ns = {r["length_bin_bp"]: r["n_test"] for r in rows}

    def pretty(b: str) -> str:
        lo, hi = b.split("-")
        # the top bin's upper edge is an open sentinel, not a real length
        return f"\u2265{int(lo):,}" if int(hi) > 100_000 else f"{int(lo):,}\u2013{int(hi):,}"

    ax.set_xticks(np.arange(len(bins)))
    ax.set_xticklabels([f"{pretty(b)}\n(n={ns[b]})" for b in bins])
    ax.set_xlabel("Deletion length (bp)")
    ax.set_ylabel("Recall at full supervision")
    ax.set_ylim(0, 1.10)
    ax.set_title("Recall is length-consistent for the tensor models")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.26), ncol=3,
              frameon=False, fontsize=8, handlelength=1.5,
              columnspacing=1.6)
    fig.savefig(out / "figure3_length_strata.png")
    plt.close(fig)


# ------------------------------------------------------------------ figure 4
def figure4(res: Path, out: Path) -> None:
    rows = read(res / "table4_ablation.csv")
    g = by_arm(rows, "objective", "label_frac", "F1_mean", "F1_sd")
    order = ["MAM-only", "VICReg-only", "combined"]
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    for obj in order:
        x, y, sd = g[obj]
        ax.plot(x, y, "-o", color=OBJ_COLOUR[obj], label=obj)
        ax.fill_between(x, y - sd, y + sd, color=OBJ_COLOUR[obj], alpha=0.15,
                        linewidth=0)
    pct_axis(ax, g[order[0]][0])
    ax.set_ylabel("Deletion F1 (held-out chr12–22)")
    ax.set_ylim(0, 1.0)
    ax.set_title("Objectives are not separated by the available seeds")
    ax.legend(title="SSL objective", loc="lower right", frameon=False)
    fig.savefig(out / "figure4_ssl_ablation.png")
    plt.close(fig)


# ------------------------------------------------------------------ figure 5
def figure5(res: Path, out: Path) -> None:
    rows = read(res / "table5_cross_ancestry.csv")
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    for arm in ["AlignSSL-combined", "AlignSSL-scratch"]:
        sub = sorted([r for r in rows if r["arm"] == arm],
                     key=lambda r: float(r["label_frac"]))
        x = np.array([float(r["label_frac"]) for r in sub])
        ind = np.array([float(r["in_dist_F1_mean"]) for r in sub])
        ceu = np.array([float(r["heldout_CEU_F1_mean"]) for r in sub])
        ceu_sd = np.array([float(r["heldout_CEU_F1_sd"]) for r in sub])
        ax.plot(x, ind, "--o", color=COLOUR[arm], alpha=0.55,
                label=f"{LABEL[arm]} — in-distribution")
        ax.plot(x, ceu, "-s", color=COLOUR[arm],
                label=f"{LABEL[arm]} — held-out CEU")
        ax.fill_between(x, ceu - ceu_sd, ceu + ceu_sd, color=COLOUR[arm],
                        alpha=0.14, linewidth=0)
    pct_axis(ax, x)
    ax.set_ylabel("Deletion F1")
    ax.set_ylim(0, 1.0)
    ax.set_title("Transfer to held-out ancestry tracks in-distribution F1")
    ax.legend(loc="lower right", frameon=False, fontsize=7)
    fig.savefig(out / "figure5_cross_ancestry.png")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results")
    a = ap.parse_args()
    res = Path(a.results_dir)
    with plt.rc_context(RC):
        for fn in (figure1, figure2, figure3, figure4, figure5):
            fn(res, res)
            print(f"{fn.__name__} ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
