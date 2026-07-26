"""Final standings on the repaired (candidate-filtered) benchmark."""
import csv
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                     "axes.linewidth": 0.8, "savefig.dpi": 300})
BLUE, SAND, GREY, RED = "#1f4e79", "#a98261", "#8a8f98", "#b5482f"

with open("../_repo_stage/results/table7_hardneg_label_efficiency.csv") as fh:
    rows = [r for r in csv.DictReader(fh) if float(r["label_frac"]) == 1.0]
src = {r["arm"]: (float(r["F1_mean"]), float(r["F1_sd"])) for r in rows}

order = [("Classical-GBT", "Hand-crafted summary numbers\n+ gradient boosting", GREY),
         ("AlignSSL-combined", "Ours: alignment tensor\n+ self-supervised pre-training", BLUE),
         ("AlignSSL-scratch", "Ours: alignment tensor,\nno pre-training", SAND),
         ("Classical-logreg", "Hand-crafted summary numbers\n+ logistic regression", GREY),
         ("DeepSV-representation", "DeepSV-style colour image\n(2019 representation)", RED)]

fig, ax = plt.subplots(figsize=(6.6, 3.0))
y = list(range(len(order)))[::-1]
for yi, (arm, lab, col) in zip(y, order):
    m, sd = src[arm]
    ax.barh(yi, m, xerr=sd, height=0.62, color=col, alpha=0.9,
            error_kw=dict(lw=0.9, capsize=2.5, ecolor="#444444"))
    ax.text(m + sd + 0.015, yi, f"{m:.2f}", va="center", fontsize=7.5,
            color="#222222")
ax.set_yticks(y)
ax.set_yticklabels([lab for _, lab, _ in order], fontsize=7.5)
ax.set_xlim(0, 1.0)
ax.set_xlabel("Accuracy of deletion calls on the harder benchmark (F1)")
ax.set_title("Once the easy shortcut is taken away, no method is comfortable",
             loc="left", fontsize=8.5)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)
fig.tight_layout()
fig.savefig("note_fig3_standings.png", bbox_inches="tight")
print("saved")
