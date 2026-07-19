---
title: "AlignSSL-SV"
subtitle: "Teaching a computer to find missing pieces of DNA — with less labeled data and honest confidence"
author: "Project update"
date: "July 2026"
---

# 1. The problem, in plain words

**What we are looking for**

- Every person's DNA is a 3-billion-letter instruction book.
- Sometimes a chunk of letters is **missing** — a *deletion*. These missing chunks can cause disease.
- To read DNA, machines chop it into millions of short fragments ("reads") and lay them back over a reference book. Finding a deletion means spotting the *pattern* those reads make where letters are gone.

**Why it is hard**

- The patterns are subtle and noisy — like guessing a missing paragraph from smudged photocopies.
- Training a computer to spot them needs **huge amounts of hand-checked examples**, which are expensive and slow to produce.
- Deletions come in wildly different sizes (from ~50 letters to tens of thousands). One-size-fits-all methods miss the big ones.

# 2. What DeepSV did — and where it now falls short

**DeepSV (2019) — the paper we build on**

- Turned each stretch of DNA reads into a **picture** (an image), then used an image-recognition network to say "deletion" or "not".
- Clever for its time: it let vision AI tackle a genomics problem.

**What has aged badly**

| DeepSV choice | The limitation today |
|---|---|
| Hand-designed **fixed colour image** | Throws away information; the encoding is guessed, not learned |
| **One fixed small window** | Can only "see" short deletions; misses large ones |
| **Needs many labels** | Every training example must be hand-checked — costly |
| Gives a **yes/no with no honesty** | Never says "I'm unsure" — dangerous for medical use |

*DeepSV proved the idea. It did not solve the data-hunger, the scale problem, or the trust problem.*

# 3. Our idea: AlignSSL-SV — what is genuinely different

**Three real changes, not "swap one network for another":**

1. **Learn the representation instead of hand-drawing it.**
   We feed the raw alignment evidence to the model and let it *learn* what matters — no hand-picked colour picture.

2. **Learn first without labels (self-supervised).**
   The model studies millions of *unlabeled* DNA regions to learn "what normal looks like" — like a student reading widely before an exam. Then it needs only a *few* labeled examples to become a good deletion-caller. **This is the headline: good results with far less labeled data.**

3. **Say how confident it is (calibrated uncertainty).**
   Instead of a bare yes/no, it gives a *trustworthy* probability and can flag "I'm not sure — a human should look." Essential for clinical use.

**Plus:** a **multi-scale** view so the same model handles both tiny and very large deletions.

# 4. What we have done so far ✅

**Foundation is built and tested — this is real, running work, not a plan on paper.**

- **Literature review & proposal** delivered (62 papers surveyed); confirmed the idea is novel versus published work.
- **Real data secured** on the university cluster: reference genome + a truth list of ~41,000 known deletions, and two fully-sequenced individuals (~2,900 confirmed deletions between them).
- **Data pipeline built and validated** end-to-end on the *real* genomes: turned the raw alignments into **11,000 labeled** training windows and **80,000 unlabeled** windows for the self-supervised stage.
- **Self-supervised pretraining is training right now** on a cluster GPU. The learning curve is healthy — the model's error has already more than halved and keeps dropping.

*In short: the engine is assembled and the first major training run is underway.*

# 5. The full plan ahead 🗺️

**Phase A (now → next weeks)**

1. Finish self-supervised pretraining → save the learned "genome sense" model.
2. **The money plot:** show it reaches good accuracy with only 1–25% of the labels a normal method needs (pretrained vs. from-scratch).
3. Add and test the **honesty/confidence** layer (reliable probabilities, "flag when unsure").

**Phase B (evaluation & fairness)**

4. **Head-to-head vs. DeepSV** and other baselines, on the same data.
5. **Size test:** does it now catch large deletions DeepSV missed?
6. **Cross-population test:** train on some ancestries, test on another (a downloading step is ~90% done).
7. **Robustness test:** does it still work when the DNA is sequenced more cheaply/shallowly?

**Phase C (finish line)**

8. Add the gold-standard GIAB benchmark, write the paper, release the code, submit to a top journal.

# 6. Honest hurdles & current shortcomings ⚠️

**Technical hurdles we are managing**

- **Limited GPUs:** the fastest cluster GPUs are booked by others for days, so we run on a smaller free GPU — slower, but working. (We already re-engineered the data loading to keep it fully busy.)
- **Big data plumbing:** each training batch is heavy; we solved stalls by loading data straight from memory.

**Current shortcomings (to be transparent)**

- Results so far are from only **two individuals** — we have started the machinery, not the final numbers.
- Our current truth list is a good genotype set but **not yet the gold-standard benchmark** — that is deliberately scheduled for later, so reviewers see a clean top-tier comparison.
- Scope is **deletions only** for now (the most common, best-labeled variant) — a focused, defensible first paper.

# 7. The goal — and the result we want

**Goal in one sentence**

> Find missing pieces of DNA **more accurately, at every size, using far fewer hand-labeled examples, and with an honest confidence score** — a clear step beyond DeepSV.

**What success looks like**

- **Same or better accuracy than DeepSV** on short deletions, and **clearly better on large ones**.
- A **"money plot"** showing our model matches a fully-supervised method using only a **small fraction of the labels** — the practical win for labs that cannot label everything.
- Confidence scores you can **trust** (well-calibrated), so risky calls get a human's eyes.
- A **publishable, reproducible** result: open code + trained model, aimed at a Q1 bioinformatics journal.

*Why it matters: cheaper, more reliable deletion detection helps find disease-causing variants in people whose genomes have historically been under-studied.*
