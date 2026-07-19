% AlignSSL-SV: A Self-Supervised, Calibrated Deep Model for Deletion Calling
% Extending DeepSV (Cai, Wu & Gao, 2019)
% Project status & results — comparison note: see slide "How we compared to DeepSV" for exactly what was and wasn't run

# What problem are we solving?

- **Structural variants (SVs)** are large changes in the genome — here we focus on **deletions** (a chunk of DNA is missing).
- Finding them from sequencing data is hard: the signal is noisy and buried in millions of aligned reads.
- **DeepSV (2019)** was an early deep-learning attempt: it turned each candidate site into a small **color (RGB) image** and ran a **CNN** on it — like teaching a computer to "look" at a picture of the reads.
- We built a newer system, **AlignSSL-SV**, that learns a smarter representation of the reads *before* it ever sees a single label.

# The one-sentence result

> **Our model finds deletions substantially better than a DeepSV-style baseline, and it "knows what it doesn't know" far better too.**

- Best deletion F1: **~0.80–0.82** (AlignSSL-SV) vs **~0.57 ceiling** (DeepSV-representation reimplementation — see methodology note, next slides).
- Calibration error (how honest its confidence is): **0.02** (ours) vs **0.09** (DeepSV-repr.) — about **4–5× better**.

# How our approach differs from DeepSV

| | DeepSV (2019) | AlignSSL-SV (ours) |
|---|---|---|
| Input | Hand-designed RGB image | **Learned** 18-channel alignment encoding |
| Window | Single fixed 50 bp view | **Multi-scale** windows |
| Training | Fully supervised only | **Self-supervised pretraining** first |
| Confidence | Uncalibrated | **Calibrated** (temperature + conformal) |
| Scope | Deletions, short reads | Deletions, short reads (same, for fair comparison) |

*Plain version:* DeepSV was told exactly what picture to draw. We let the model **learn its own picture** from lots of unlabeled data, so it needs far fewer labeled examples to do well.

# How we compared to DeepSV (important methodology note)

- We did **not** run DeepSV's original released code (`github.com/CSuperlei/DeepSV`) to get its numbers.
- We checked: their repo's main pipeline script has an incomplete/broken entry point (undefined `parser`, placeholder file paths), and its CNN training step requires **NVIDIA DIGITS** and **TensorFlow-1.x `contrib.slim`** — both discontinued years ago, with no pinned dependency file to reconstruct the original 2018 stack.
- Instead, we built a **faithful reimplementation**: their described RGB pileup encoding (base-colour + read-flag tinting) and a representative CNN of their era, then trained and tested it on **our own identical data/splits/loss** as our model.
- So the "DeepSV" numbers on these slides are really: *"DeepSV's core idea, reimplemented and controlled for a fair, apples-to-apples comparison"* — not a reproduction of their published paper numbers. We'll label this explicitly as **"DeepSV-representation reimplementation"** in the manuscript.

# Technical detail: self-supervised pretraining

- We first train the model on **80,000 unlabeled genomic windows** — no "deletion / not deletion" answers given.
- The objective combines two ideas:
  - **MAE (masked auto-encoding):** hide part of the read data and make the model fill it back in.
  - **VICReg:** keep the learned features informative and non-redundant.
- Result: an **encoder** that already understands what normal read alignments look like, so the deletion task becomes easier.

# Headline result: works with very little labeled data

- We measured deletion **F1** as we gave the model 1%, 5%, 10%, 25%, 50%, 100% of the labels.
- **At just 1% of labels:** the from-scratch model **completely fails (F1 = 0.00)**; our pretrained model still reaches **F1 ≈ 0.40**.
- At full labels both are strong (~0.80), but pretraining is what saves you when labels are scarce — which is the real-world situation.

*(Figure: `fig_label_efficiency.png` — the "money plot", three arms: pretrained vs scratch vs DeepSV-repr. baseline.)*

# Head-to-head vs DeepSV-representation baseline (3 random seeds)

- Deletion F1 across label fractions:
  - **AlignSSL-SV:** ~0.40 → 0.80–0.82 (peaks at full data)
  - **DeepSV-repr. baseline:** stuck around **0.57 and never clears ~0.6**
- Our model **wins 5 of 6** label settings (DeepSV-repr. only edges us at the 5% point).
- **Bottom line:** the DeepSV-style representation+CNN plateaus; our model keeps improving and ends much higher.
- *Reminder: this is our controlled reimplementation of DeepSV's representation and CNN, run on identical data/splits — not their original code (see methodology note above).*

# Technical detail: calibration (trustworthy confidence)

- A model can be accurate but **overconfident** — a problem when a clinician or researcher acts on its calls.
- We measure **ECE (Expected Calibration Error)** — lower is better.
  - **AlignSSL-SV: ECE ≈ 0.02**
  - **DeepSV-repr. baseline: ECE ≈ 0.09**
- We use **temperature scaling** (softens over-confident scores) and **conformal prediction** (gives statistically valid confidence).
- Meaning: when our model says "80% sure", it's right about 80% of the time.

# Result: robust across ancestries

- We trained on **African-ancestry samples** and tested on a **European sample (NA12878)** it had never seen.
- The performance **gap between seen and unseen ancestry**:
  - **Pretrained: +0.015** (essentially no drop)
  - **From scratch: +0.117** (clear drop)
- *Plain version:* pretraining makes the model **fairer and more portable** across human populations — it doesn't quietly get worse on groups underrepresented in training.

# Where the model is still weak

- **Long deletions (5,000+ bp)** remain the hardest for everyone.
- Recall by deletion size (our model, full labels):
  - 50–200 bp: **0.91**
  - 1,000–5,000 bp: **0.65**
  - 5,000+ bp: **0.63**
- This is a known frontier and a target for the next phase.

# Current project status

**Done and locked in:**

- Full literature survey (62 papers) + research proposal drafted.
- Core model built, self-supervised pretraining completed on the cluster.
- Three headline experiments finished (3 seeds each): label-efficiency, DeepSV head-to-head, cross-population.
- Calibration and length-stratified analyses complete.

# Current project status (in progress)

**Running / next up:**

- Downloading **7 more samples** to build a **5-super-population panel** (broader ancestry coverage).
- **Objective ablation** (MAE vs VICReg vs both) to confirm the design choice.
- Planned: coverage-robustness test, and adding the **GIAB HG002 gold-standard** benchmark for the final paper.

**Target venue:** *Bioinformatics* / *Briefings in Bioinformatics* (Q1).

# Summary — is it better than DeepSV?

**Yes, clearly** (vs our DeepSV-representation reimplementation — see methodology note):

1. **Higher accuracy** — F1 ~0.80–0.82 vs ~0.57 ceiling (DeepSV-repr.).
2. **Far better calibrated** — ECE 0.02 vs 0.09 (4–5× better).
3. **Data-efficient** — usable at 1% labels where the DeepSV-repr. baseline / from-scratch model fail.
4. **Ancestry-robust** — almost no performance drop on unseen populations.

*The novelty is not "swap CNN for a Transformer" — it's a learned, self-supervised, calibrated, multi-scale representation of read alignments.*
