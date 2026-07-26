"""Science-popular schematic for the AlignSSL-SV note.

Panel a: what a deletion does to sequencing reads.
Panel b: the two ways of showing that evidence to a neural network.
"""
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8,
    "axes.linewidth": 0.8, "savefig.dpi": 300,
})

BLUE, SAND, GREY, RED = "#1f4e79", "#a98261", "#8a8f98", "#b5482f"

fig = plt.figure(figsize=(7.2, 4.4))
gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1.0], hspace=0.42, wspace=0.28,
                      left=0.06, right=0.98, top=0.90, bottom=0.07)

# ---- panel a: reads over a deletion -------------------------------------
ax = fig.add_subplot(gs[0, :])
ax.set_xlim(0, 100); ax.set_ylim(0.55, 7.15); ax.axis("off")
ax.set_title("a  A deletion is a stretch of DNA the sample is missing — the reads say so in three ways",
             loc="left", fontsize=8.5, weight="normal")

# reference bar
ax.add_patch(Rectangle((2, 5.9), 96, 0.55, fc="#e8e4dd", ec=GREY, lw=0.7))
ax.text(2, 6.75, "reference genome", fontsize=7.5, color=GREY)
ax.add_patch(Rectangle((40, 5.9), 22, 0.55, fc=RED, ec="none", alpha=0.30))
ax.text(51, 6.72, "deleted in this person", fontsize=7.5, color=RED, ha="center")

rng = np.random.default_rng(3)
y0 = 5.2
# reads outside the deletion: normal coverage
for i, (x, y) in enumerate([(v, y0 - 0.42 * (i % 4))
                            for i, v in enumerate(rng.uniform(3, 36, 16))]):
    ax.add_patch(Rectangle((x, y), 5.5, 0.24, fc=BLUE, ec="none", alpha=0.75))
for i, (x, y) in enumerate([(v, y0 - 0.42 * (i % 4))
                            for i, v in enumerate(rng.uniform(63, 92, 16))]):
    ax.add_patch(Rectangle((x, y), 5.5, 0.24, fc=BLUE, ec="none", alpha=0.75))
# almost nothing inside
for i, x in enumerate(rng.uniform(42, 58, 2)):
    ax.add_patch(Rectangle((x, y0 - 0.42 * i), 5.5, 0.24, fc=BLUE, ec="none", alpha=0.35))

ax.annotate("", xy=(41, 3.05), xytext=(61, 3.05),
            arrowprops=dict(arrowstyle="<->", lw=0.9, color=RED))
ax.text(51, 2.72, "1. coverage drops", ha="center", fontsize=7.5, color=RED)

# spanning pair
ax.add_patch(Rectangle((33, 1.95), 5.5, 0.24, fc=SAND, ec="none"))
ax.add_patch(Rectangle((63, 1.95), 5.5, 0.24, fc=SAND, ec="none"))
ax.plot([38.5, 63], [2.07, 2.07], color=SAND, lw=0.8, ls=":")
ax.text(70.5, 1.98, "2. read pairs land further apart than expected", fontsize=7.5, color=SAND)

# clipped read
ax.add_patch(Rectangle((36.5, 1.05), 3.5, 0.24, fc=BLUE, ec="none"))
ax.add_patch(Rectangle((40.0, 1.05), 2.0, 0.24, fc="none", ec=RED, lw=0.8, ls="--"))
ax.text(44, 1.08, "3. reads are cut off at the edge of the deletion",
        fontsize=7.5, color=RED)

ax.plot([40, 40], [-0.2, 5.9], color=RED, lw=0.6, ls="--", alpha=0.6)
ax.plot([62, 62], [-0.2, 5.9], color=RED, lw=0.6, ls="--", alpha=0.6)
ax.text(51, -0.75, "the two breakpoints", ha="center", fontsize=7.5, color=RED)

# ---- panel b left: DeepSV RGB image -------------------------------------
axl = fig.add_subplot(gs[1, 0])
img = rng.uniform(0.35, 0.95, (26, 64, 3))
img[:, 22:42, :] *= 0.35
axl.imshow(img, aspect="auto", interpolation="nearest")
axl.set_xticks([]); axl.set_yticks([])
axl.set_title("b  DeepSV (2019): draw a picture, then look at it",
              loc="left", fontsize=8.5)
axl.set_xlabel("three colour channels — a lossy drawing of the reads", fontsize=7.5)

# ---- panel b right: alignment tensor ------------------------------------
axr = fig.add_subplot(gs[1, 1])
axr.set_xlim(0, 10); axr.set_ylim(0, 6.4); axr.axis("off")
axr.set_title("c  Ours: keep the numbers the aligner already computed",
              loc="left", fontsize=8.5)
for k in range(6):
    off = 0.30 * k
    axr.add_patch(Rectangle((0.9 + off, 1.7 + off), 3.4, 2.1,
                            fc=BLUE, ec="white", lw=0.8,
                            alpha=0.18 + 0.11 * k))
names = ["does the base match?", "mapping quality", "insert size",
         "soft-clipped?", "strand", "read depth"]
ytop, dy = 5.15, 0.52
for k, nm in enumerate(names):
    axr.text(6.9, ytop - dy * k, nm, fontsize=7, color=BLUE, va="center")
axr.plot([6.55, 6.55], [ytop - dy * (len(names) - 1) - 0.18, ytop + 0.18],
         color=BLUE, lw=0.9)
axr.annotate("", xy=(6.5, 3.6), xytext=(5.0, 3.4),
             arrowprops=dict(arrowstyle="->", lw=0.8, color=BLUE))
axr.text(9.95, 1.62, "18 channels in all", fontsize=7, color=BLUE, ha="right")
axr.annotate("", xy=(0.9, 1.35), xytext=(4.3, 1.35),
             arrowprops=dict(arrowstyle="<->", lw=0.8, color=GREY))
axr.text(2.6, 0.95, "256 positions along the genome", fontsize=7,
         color=GREY, ha="center")
axr.annotate("", xy=(0.62, 1.7), xytext=(0.62, 3.8),
             arrowprops=dict(arrowstyle="<->", lw=0.8, color=GREY))
axr.text(0.40, 2.75, "64 reads", fontsize=7, color=GREY, rotation=90,
         va="center", ha="center")

fig.savefig("note_fig1_schematic.png", bbox_inches="tight")
print("saved")
