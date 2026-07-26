"""High-quality rendered formula images for the note (mathtext, 400 dpi)."""
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({"mathtext.fontset": "cm", "savefig.dpi": 400})
GREY = "#5a5f66"

# --- eq 1: the alignment tensor ------------------------------------------
fig = plt.figure(figsize=(3.2, 0.6))
fig.text(0.5, 0.5, r"$X \in \mathbb{R}^{18 \times 64 \times 256}$",
         ha="center", va="center", fontsize=17)
fig.savefig("eq1_tensor.png", bbox_inches="tight", pad_inches=0.06,
            facecolor="white")
plt.close(fig)

# --- eq 2: the pre-training objective ------------------------------------
fig = plt.figure(figsize=(6.4, 0.98))
fig.text(0.5, 0.75,
         r"$\mathcal{L} \;=\; \dfrac{1}{|M|}\sum_{(r,p)\,\in\,M}"
         r"\left| \hat{x}_{rp} - x_{rp} \right|"
         r"\;\;+\;\; \lambda\, \mathcal{L}_{\mathrm{VICReg}}(z_1, z_2)$",
         ha="center", va="center", fontsize=16)
fig.text(0.315, 0.14, "fill in what was hidden", ha="center", va="center",
         fontsize=9.5, color=GREY, style="italic")
fig.text(0.795, 0.14, "two views of one place must agree,\n"
                     "while the features stay varied",
         ha="center", va="center", fontsize=9.5, color=GREY, style="italic")
fig.savefig("eq2_loss.png", bbox_inches="tight", pad_inches=0.06,
            facecolor="white")
plt.close(fig)
print("saved")
