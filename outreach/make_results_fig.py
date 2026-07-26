"""Science-popular results figure for the AlignSSL-SV note.

Panel a: how much labelled data each approach needs (uniform benchmark).
Panel b: the honesty check - how easy the task was, before and after repair.
"""
import csv
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                     "axes.linewidth": 0.8, "savefig.dpi": 300})
BLUE, SAND, GREY, RED = "#1f4e79", "#a98261", "#8a8f98", "#b5482f"

R = "../_repo_stage/results/"

def load(fn):
    with open(R + fn) as fh:
        return list(csv.DictReader(fh))

t1 = load("table1_label_efficiency.csv")
t6 = {r["feature"]: float(r["auc_oriented"]) for r in load("table6_single_feature_auc.csv")}
t9 = {r["feature"]: float(r["auc_oriented"]) for r in load("table9_hardneg_single_feature_auc.csv")}

fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.2, 3.1))

# --- panel a --------------------------------------------------------------
arms = [("AlignSSL-combined", BLUE, "with self-supervised pre-training"),
        ("AlignSSL-scratch", SAND, "same network, trained from scratch")]
for arm, col, lab in arms:
    rows = sorted((r for r in t1 if r["arm"] == arm),
                  key=lambda r: float(r["label_frac"]))
    x = [float(r["label_frac"]) * 100 for r in rows]
    y = [float(r["F1_mean"]) for r in rows]
    e = [float(r["F1_sd"]) for r in rows]
    axa.errorbar(x, y, yerr=e, marker="o", ms=4, lw=1.6, color=col,
                 capsize=2, elinewidth=0.8, label=lab)
axa.set_xscale("log")
axa.set_xticks([1, 5, 10, 25, 50, 100])
axa.set_xticklabels(["1", "5", "10", "25", "50", "100"])
axa.set_xlabel("Labelled examples used (% of 21,016)")
axa.set_ylabel("Accuracy of deletion calls (F1)")
axa.set_ylim(-0.03, 1.0)
axa.set_title("a  Pre-training pays off when labels are scarce",
              loc="left", fontsize=8.5)
axa.legend(frameon=False, fontsize=7, loc="lower right")
axa.annotate("", xy=(1, 0.514), xytext=(1, 0.050),
             arrowprops=dict(arrowstyle="<->", lw=0.9, color=RED))
axa.text(1.9, 0.27, "0.51 vs 0.05 with only\n210 labelled examples",
         fontsize=7, color=RED, va="center", ha="left")
for s in ("top", "right"):
    axa.spines[s].set_visible(False)

# --- panel b --------------------------------------------------------------
feats = ["depth_centre_flank_ratio", "clip_rate", "discordant_rate",
         "isize_absz_max", "depth_sd"]
pretty = ["drop in read depth", "reads cut off", "read pairs too far apart",
          "worst insert size", "variability of depth"]
y = np.arange(len(feats))[::-1]
axb.barh(y + 0.19, [t6[f] for f in feats], height=0.36, color=RED,
         alpha=0.85, label="original benchmark")
axb.barh(y - 0.19, [t9[f] for f in feats], height=0.36, color=BLUE,
         alpha=0.85, label="repaired benchmark")
axb.axvline(0.5, color=GREY, lw=0.9, ls="--")
axb.text(0.505, len(feats) - 0.35, "coin flip", fontsize=7, color=GREY)
axb.set_yticks(y)
axb.set_yticklabels(pretty, fontsize=7.5)
axb.set_xlim(0.45, 1.02)
axb.set_xlabel("How well one simple measurement alone\nseparates real deletions from decoys (AUC)")
axb.set_title("b  We then made the test harder — on purpose",
              loc="left", fontsize=8.5)
axb.legend(frameon=False, fontsize=7, loc="lower right")
for s in ("top", "right", "left"):
    axb.spines[s].set_visible(False)
axb.tick_params(axis="y", length=0)

fig.tight_layout(w_pad=2.0)
fig.savefig("note_fig2_results.png", bbox_inches="tight")
print("saved")
