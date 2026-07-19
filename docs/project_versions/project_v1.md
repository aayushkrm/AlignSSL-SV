# RESEARCH ROADMAP & EXECUTION PLAN

## AlignSSL-SV: Self-Supervised Pretraining on Read Alignments with Calibrated Uncertainty for Structural-Variant Deletion Calling

### Project Summary

* **Project in one sentence:** Pretrain a neural encoder on large volumes of unlabeled read-alignment (BAM/pileup) data using masked-reconstruction and contrastive objectives, then fine-tune it for deletion calling with a calibrated-uncertainty output head — directly attacking DeepSV's two admitted weaknesses: its hunger for scarce labels and its uncalibrated binary output.

### Project Overview

| Field | Value |
| --- | --- |
| **Base / reference paper** | Cai, Wu & Gao (2019), DeepSV, *BMC Bioinformatics* 20:665 |
| **Working title** | AlignSSL-SV (see §12 for publication titles) |
| **Target venue** | *Bioinformatics* or *Briefings in Bioinformatics* (Q1) |
| **Team stage** | Lit review + environment setup complete; no experiments run |
| **Compute assumption** | Multi-GPU (A100/H100-class) available |
| **Est. duration** | ~10 months to submission (see §11 timeline) |

*Prepared as a working execution plan — treat every empirical figure as a hypothesis to verify, not a result.*

---

## Contents

1. Executive overview
2. Problem formulation & data foundation
3. Input representation — the learnable alignment tensor
4. Stage 1 — Self-supervised pretraining
5. Stage 2 — Supervised fine-tuning for deletion calling
6. Calibrated uncertainty — the second contribution
7. Evaluation protocol
8. Step-by-step execution plan
9. Compute, tooling & engineering
10. Risks, reviewer criticisms & defenses
11. Timeline summary (~10 months)
12. Publication plan

---

## 1. Executive overview

This document is the complete technical roadmap for **AlignSSL-SV**, the self-supervised + calibrated-uncertainty project selected from the ten research reports. It is written to be executed section by section. Where a design decision has a real alternative, both options are stated so the team can choose deliberately rather than inherit a default.

The scientific hypothesis is deliberately narrow and testable:

| Central hypothesis |
| --- |
| "Short-read deletion calling improves not from a new network backbone, but from (a) learning the representation of alignment evidence self-supervised on unlabeled BAMs instead of hand-designing it (DeepSV's RGB scheme), and (b) emitting a calibrated confidence per call instead of a bare binary label. The gains should concentrate in the low-label, low-coverage, and repeat-rich regimes where DeepSV is weakest." |

Two properties make this a good bet for a university team:

1. **Novelty survives review:** Self-supervised learning exists broadly in genomics, but on raw reference sequence — not on alignment/pileup evidence for SV calling. That precise combination is unoccupied across all ten reports.
2. **It is feasible:** Pretraining on public 1000 Genomes / HGSVC BAMs is far cheaper than an LLM-scale foundation model and fits comfortably on the GPU resources you have.

The deliverable of the project is a method paper with:

1. A pretrained alignment encoder released as open weights.
2. A deletion caller fine-tuned from it.
3. A calibrated-uncertainty head with reliability diagrams.
4. A benchmark showing where the self-supervised prior and calibration help versus DeepSV and modern baselines.

### 1.1 What we keep, replace, and add versus DeepSV

| DeepSV component | Our decision | Why |
| --- | --- | --- |
| Alignment evidence → learned representation → deletion call | **KEEP** | This core insight is correct and still the foundation. |
| Hand-designed 64-color RGB pileup encoding | **REPLACE** | Lossy, non-learnable; we feed raw channels + learn the encoding. |
| Fixed 50 bp / 256×256 windows | **REPLACE (soften)** | Use larger, multi-scale windows; keep tractable for short reads. |
| k-means candidate generation | **KEEP (v1) / REPLACE (v2)** | Reuse as candidate proposer initially; optionally learn later. |
| Purely supervised training on scarce labels | **ADD self-supervision** | Pretrain on unlabeled BAMs, fine-tune on the small truth set. |
| Binary softmax output | **ADD calibrated uncertainty** | Evidential / ensemble head + conformal calibration. |

---

## 2. Problem formulation & data foundation

### 2.1 Precise task definition

Scope the paper tightly to **germline long-deletion (DEL, ≥50 bp) calling from short-read (Illumina) whole-genome data**. This matches DeepSV's scope exactly, which makes the head-to-head comparison clean and defensible.

Insertions, inversions, duplications, translocations, long-read, and somatic calling are explicitly out of scope for v1 (list them as future work — reviewers respect a focused paper).

Formally: given a candidate locus and its surrounding aligned reads, predict:

1. DEL vs non-DEL
2. Left/right breakpoint offsets
3. A calibrated confidence

Training has two stages: self-supervised pretraining with no labels, then supervised fine-tuning on truth-set deletions.

### 2.2 Datasets — exactly what to download and how to use each

| Dataset | Role in project | Notes |
| --- | --- | --- |
| **1000 Genomes Phase 3** (Illumina WGS BAMs) | Self-supervised PRETRAINING corpus (unlabeled) + historical comparability with DeepSV | Hundreds of samples, ~7–30×. Use reads only, ignore any labels here. |
| **GIAB HG002** (+ HG003/HG004) with the GIAB Tier-1 SV benchmark | Supervised FINE-TUNE + primary in-distribution TEST | Gold-standard truth (Zook et al. 2020). HG002 is the community standard. |
| **HGSVC / HPRC** diverse-ancestry samples | Held-out GENERALIZATION test (cross-ancestry) | Tests whether the SSL representation generalizes beyond training ancestries. |
| Down-sampled copies (e.g. 10×, 30×, 60×) via `samtools view -s` | Coverage-robustness axis | DeepSV itself studied coverage; this is a strong, cheap evaluation slice. |
| A repeat / segmental-duplication region annotation (e.g. RepeatMasker, segdup track) | Region STRATIFICATION for evaluation | Lets you show where the prior helps most. |

| Data hygiene rule (non-negotiable) |
| --- |
| Never let a pretraining sample overlap a test individual or test chromosome. Hold out entire individuals AND entire chromosomes for test. DeepSV trained on chr1–11 and tested on chr12–22; adopt the same chromosome split plus individual-level holdout so a reviewer cannot claim leakage. |

### 2.3 The candidate-generation choice

Detection needs candidate loci to score. Two options:

* **v1 (recommended, low-risk):** Reuse DeepSV's k-means / clustering-style proposer, or run a fast classical caller (e.g. Delly or Manta) at permissive settings to over-generate candidates, then let your model classify+refine. This decouples the novelty (representation + uncertainty) from candidate generation and de-risks the first result.
* **v2 (optional, higher novelty):** Replace the proposer with a learned scanning head. Only attempt after v1 works — it raises the recall ceiling but adds engineering and a second failure mode.

---

## 3. Input representation — the learnable alignment tensor

This section replaces DeepSV's RGB scheme. Instead of packing signals into an 8-bit color, we build a **multi-channel tensor** where each alignment signal is its own channel, then let a small learned stem (not a hand-picked color map) fuse them. This is the concrete meaning of 'learnable encoding'.

### 3.1 Tensor layout

For a candidate locus, build a tensor of shape `[C, R, W]`:

* `C` channels
* `R` read rows (padded/truncated to a fixed depth, e.g. 128)
* `W` window columns (reference positions, e.g. 1024–4096 bp — larger than DeepSV's 50 bp so more of the deletion context fits)

#### Recommended channels (C ≈ 8–10)

1. **Base identity** (A/C/G/T/gap) — one-hot or learned embedding, 4–5 planes or an embedding channel.
2. **Base quality** (Phred) — continuous, normalized to [0,1].
3. **Mapping quality (MAPQ)** — continuous, normalized.
4. **Strand** — binary (+/−).
5. **Read-pair orientation / is-discordant flag** — the discordant-pair signature DeepSV used.
6. **Soft-clip / split-read flag** — the split-read signature (marks breakpoint-spanning reads).
7. **Insert-size z-score** — normalized deviation of the pair's insert size from the library mean.
8. **Per-column read depth** — the depth-drop signature of a deletion.
9. **Reference base track** — the reference sequence in the window (gives the model the 'expected' sequence).

| Why this beats RGB in plain words |
| --- |
| "DeepSV forced continuous values like mapping quality into an 8-bit color offset, then asked the CNN to decode an arbitrary color scheme. Here every signal stays in its own channel at full fidelity, and a learned 1×1 convolutional stem discovers the optimal fusion during training. Nothing is quantized away before learning begins. This is a clean, defensible ablation: 'learned channels vs DeepSV RGB'." |

### 3.2 Implementation notes

* Build tensors with `pysam` (iterate reads over a region, pull cigar/flags/quals).
* Cache to disk as compressed `.npz` or memory-mapped `HDF5` so the data loader is not I/O-bound — this matters a lot at scale.
* Fix read-depth padding (`R`): sample or pad to a constant number of rows; store a mask channel so the model ignores padding.
* Normalize continuous channels with training-set statistics computed once and frozen.
* Precompute tensors for pretraining loci offline in a preprocessing job; do not build them on the fly during GPU training.

---

## 4. Stage 1 — Self-supervised pretraining

This is the scientific heart of the project. The encoder learns the 'grammar' of alignment evidence from unlabeled BAMs before it ever sees a deletion label. Two complementary objectives are recommended; run both and ablate each.

### 4.1 Objective A — Masked-channel / masked-region modeling (MAE-style)

Randomly mask a large fraction (start at 50–75%) of the input — mask whole read rows, column spans, or channel patches — and train the encoder + a lightweight decoder to reconstruct the masked values.

* This forces the model to learn how alignment signals co-vary (e.g. that a depth drop co-occurs with soft-clipped reads at its edges).
* **Loss:** MSE on continuous channels (quality, depth, insert-size) + cross-entropy on categorical channels (base identity, strand, flags).
* Use an asymmetric encoder–decoder (heavy encoder, light decoder) as in vision MAE — the decoder is discarded after pretraining.

### 4.2 Objective B — Contrastive region discrimination (InfoNCE)

Create two augmented 'views' of the same genomic locus and pull their embeddings together, while pushing apart embeddings of different loci. This is where you can bake in the invariances you care about:

* **Coverage-invariance view:** Down-sample the same locus to two different depths → forces embeddings that don't collapse at low coverage. This is the axis that pays off in the low-coverage evaluation slice.
* **Cross-sample view:** The same orthologous locus from two individuals → forces population-robust embeddings (pays off in the cross-ancestry test).
* **Loss:** InfoNCE / NT-Xent with a temperature parameter; a projection head on top of the encoder (discarded after pretraining, SimCLR-style).

| Guard against a known failure mode |
| --- |
| "Contrastive methods can 'collapse' (all embeddings become identical). Mitigations: use a large batch or a memory queue (MoCo-style), a projection head, and consider a redundancy-reduction objective (VICReg / Barlow Twins) which is more collapse-resistant than plain InfoNCE. CSV-Filter used VICReg for exactly this reason — cite it and note you extend SSL from filtering to representation-for-calling." |

### 4.3 Encoder architecture

Keep the backbone unremarkable on purpose — novelty must live in the objective, not the backbone, or you fall into the 'encoder-swap' rejection every report warns about.

* **CNN stem** over the local `[C,R,W]` tensor to capture read-level / breakpoint texture (this is the DeepSV-lineage part).
* **A light long-context block** over the column axis (a few Transformer layers, or a Mamba/SSM block) so window-to-window / breakpoint-spanning context is captured without DeepSV's fixed-window ceiling.
* Frame this as a design detail, never as the contribution.
* **Output:** A per-locus embedding (pooled) plus optionally per-column features for breakpoint regression.

### 4.4 Pretraining recipe (starting hyperparameters)

| Setting | Starting value | Comment |
| --- | --- | --- |
| **Optimizer** | AdamW | Standard; robust. |
| **LR schedule** | Warmup + cosine decay | Warmup ~5% of steps. |
| **Peak LR** | 1e-3 (contrastive) / 1.5e-4 (MAE) | Tune per objective. |
| **Batch size** | As large as GPUs allow (≥512 for contrastive) | Large batches matter for InfoNCE. |
| **Mask ratio (MAE)** | 0.5 → 0.75 | Sweep; higher = harder task. |
| **Pretraining data** | 1000 Genomes BAMs, millions of loci | Sample loci genome-wide, not just SV sites. |
| **Precision** | bf16 mixed precision | Fits your GPUs, speeds training. |
| **Checkpointing** | Save every N steps + track a linear-probe metric | Monitor a downstream proxy to know pretraining is working. |

---

## 5. Stage 2 — Supervised fine-tuning for deletion calling

Attach task heads to the pretrained encoder and fine-tune on GIAB truth deletions. Compare two regimes and report both: **frozen encoder + trained heads** (shows pure representation quality) and **full fine-tune** (best accuracy).

### 5.1 Task heads

* **Deletion classification head:** DEL vs non-DEL. Loss: focal loss (handles the heavy class imbalance — wild-type sites vastly outnumber deletions).
* **Breakpoint regression head:** Left/right offset from the candidate anchor. Loss: smooth-L1 (Huber), computed on positives only.
* **Uncertainty head:** See §6 — this is added here and trained jointly.

### 5.2 Combined objective

$$L_{\text{finetune}} = \lambda_{\text{cls}} \cdot \text{FocalLoss}(\text{DEL vs non-DEL}) + \lambda_{\text{bp}} \cdot \text{SmoothL1}(\text{breakpoint offsets}) + \lambda_{\text{unc}} \cdot \text{UncertaintyLoss}$$

*(Note: Breakpoint SmoothL1 is computed on positives only. UncertaintyLoss is the evidential NLL, see §6).*

**Starting weights:** $\lambda_{\text{cls}} = 1.0, \lambda_{\text{bp}} = 0.5, \lambda_{\text{unc}} = 0.3$ (then sweep)

### 5.3 The label-efficiency experiment (a headline result)

Because the selling point is self-supervision, your most persuasive figure is a **label-efficiency curve**: fine-tune on 1%, 5%, 10%, 25%, 50%, 100% of the truth labels, with vs without pretraining.

If the pretrained model reaches the same F1 with far fewer labels, that is the paper's money plot — and it directly demonstrates the value of SSL that DeepSV cannot offer.

| Design the money plot early |
| --- |
| "Two curves (pretrained vs from-scratch) across label fractions on the x-axis, F1 on the y-axis. A wide gap at low label fractions closing at 100% is the classic, reviewer-convincing signature of useful self-supervision. Plan the experiment now so all runs are logged consistently." |

---

## 6. Calibrated uncertainty — the second contribution

DeepSV outputs a bare probability that is not calibrated (a '0.9' does not mean 90% of such calls are correct). We add a principled uncertainty mechanism plus post-hoc calibration, and — crucially — we *evaluate* calibration, which almost no SV caller does.

### 6.1 Choose an uncertainty mechanism

| Method | Cost | Recommendation |
| --- | --- | --- |
| **Deep ensembles** (train N models, average) | N× training cost | Strongest baseline; use if GPU budget allows (you have it). |
| **MC-dropout** (dropout at inference) | Cheap | Easy add-on; weaker epistemic estimates. |
| **Evidential deep learning** (Dirichlet head) | Cheap, single model | Elegant: separates aleatoric vs epistemic in one pass. Watch training stability (KL-annealing). |
| **Conformal prediction** (post-hoc) | Very cheap | **ADD ON TOP** of any of the above — gives distribution-free coverage guarantees. |

* **Recommended combination:** A deep ensemble (or evidential head if compute-limited) for the raw uncertainty, then **conformal prediction** on a held-out calibration split for a formal guarantee. Conformal is cheap and rigorous, and it stratifies naturally by SV size and coverage.

### 6.2 How to calibrate and prove it

* Hold out a calibration set (a chromosome or fraction never used in training).
* Apply temperature scaling and/or conformal prediction on that set.
* Report calibration with reliability diagrams, Expected Calibration Error (ECE), and Brier score.
* Report selective-prediction curves (risk vs coverage): accuracy when the model is allowed to abstain on its least-confident calls.

| Why calibration is a real contribution, in plain words |
| --- |
| "A clinician or population-genetics pipeline needs to know which calls to trust. A caller that says 'DEL, 92% confident' and is right 92% of the time is far more useful than one that just says 'DEL'. Showing low ECE and a good risk–coverage curve is a contribution on an axis most SV papers ignore — so you compete where the field is thin." |

---

## 7. Evaluation protocol

Use the standard SV-benchmarking tool **Truvari** to match calls against GIAB truth (it handles breakpoint tolerance correctly). Report the following, always stratified — headline single numbers are weak in this field.

### 7.1 Metrics

* **Calling:** Precision, Recall, F1 (via Truvari) — overall and per stratum.
* **Breakpoint:** Mean absolute error (bp) between predicted and true breakpoints.
* **Calibration:** ECE, Brier score, reliability diagram, risk–coverage curve.
* **Label efficiency:** F1 vs label-fraction, pretrained vs scratch (the money plot).

### 7.2 Stratification axes (where you expect to win)

| Stratum | Why it matters |
| --- | --- |
| **Deletion size bins** (50–200, 200–500, 500 bp–1 kb, 1–5 kb, 5–10 kb+) | DeepSV's own size bins; larger events are harder. |
| **Coverage** (10× / 30× / 60×, via down-sampling) | Coverage-invariant SSL should shine at 10×. |
| **Region class** (unique vs repeat / segmental duplication) | Where all short-read callers fail; SSL prior may help. |
| **Ancestry** (in-distribution vs held-out HGSVC/HPRC) | Tests cross-population generalization from contrastive views. |
| **Label budget** (1% … 100%) | The core SSL claim. |

### 7.4 Ablation matrix (the credibility core)

| Ablation | Isolates |
| --- | --- |
| Pretrained vs from-scratch | Value of self-supervision (the main claim) |
| MAE-only vs contrastive-only vs both | Which objective drives the gain |
| With vs without coverage-invariance views | Source of low-coverage robustness |
| With vs without cross-sample views | Source of cross-ancestry robustness |
| Learned channels vs DeepSV RGB encoding | Value of the learnable representation |
| With vs without uncertainty head | Does calibration cost raw F1? |
| CNN-only vs CNN + long-context block | Justifies (or drops) the context block |

---

## 8. Step-by-step execution plan

Execute in this order. Each phase has a concrete exit criterion; do not advance until it is met.

### Phase 0 — Baseline & harness (weeks 1–3)

* Reproduce DeepSV on HG002 (or run its released code) to get an honest baseline number.
* *Exit:* You can reproduce a DeepSV-like F1 on your split.


* Stand up the Truvari evaluation harness + stratification scripts.
* *Exit:* One command produces stratified P/R/F1 for any VCF.


* Build and cache the alignment-tensor pipeline (`pysam` → HDF5).
* *Exit:* Tensors for a test region load in  < X ms and visually match IGV.



### Phase 1 — Supervised skeleton, no SSL (weeks 3–6)

* Train the encoder + classification + breakpoint heads fully supervised (no pretraining) on learned channels.
* *Exit:* Matches or beats DeepSV — this validates the representation before SSL is even added.


* Run the 'learned channels vs RGB' ablation here.
* *Exit:* A clear ablation number.



### Phase 2 — Self-supervised pretraining (weeks 6–12)

* Implement MAE objective; pretrain on 1000 Genomes; monitor a linear-probe proxy.
* *Exit:* Probe metric improves over training.


* Implement contrastive objective with coverage + cross-sample views; add collapse guards.
* *Exit:* No collapse; probe improves.


* Fine-tune from each pretrained checkpoint; produce the label-efficiency money plot.
* *Exit:* Pretrained beats scratch at low label fractions.



### Phase 3 — Uncertainty & calibration (weeks 12–16)

* Add the uncertainty mechanism (ensemble or evidential) and conformal calibration.
* *Exit:* Reliability diagram + ECE computed.


* Produce risk–coverage curves and selective-prediction results.
* *Exit:* Calibrated, low-ECE caller.



### Phase 4 — Full evaluation & ablations (weeks 16–22)

* Run all baselines, all stratifications, the full ablation matrix, cross-ancestry test.
* *Exit:* Every table in §7 is populated.



### Phase 5 — Writing, release, submission (weeks 22–34)

* Draft manuscript; release code + pretrained weights; internal review; adversarial novelty re-check (see §10); submit.
* *Exit:* Submitted to target venue.



---

## 9. Compute, tooling & engineering

### 9.1 Software stack

| Layer | Tools |
| --- | --- |
| **Alignment I/O** | `pysam`, `samtools`, `htslib` |
| **Tensor storage** | HDF5 (`h5py`) or memory-mapped `.npz`; `WebDataset` for sharded streaming |
| **DL framework** | `PyTorch` (+ optional `Lightning`), `bf16` AMP |
| **SSL components** | MAE / SimCLR / VICReg / MoCo implementations; `mamba-ssm` if using SSM block |
| **Uncertainty** | `torch` ensembles / evidential-DL; `MAPIE` or a conformal library |
| **Evaluation** | `Truvari` (SV benchmarking), `bcftools`, custom stratification scripts |
| **Experiment tracking** | Weights & Biases or MLflow — log every run for the ablation tables |

### 9.2 Using your GPU resources well

* **Pretraining is the compute sink.** Use large batches (multi-GPU DDP), `bf16`, and gradient checkpointing if memory-bound. Contrastive learning especially benefits from a large effective batch — use all GPUs.
* **Ensembles are embarrassingly parallel** — train the N ensemble members concurrently across GPUs rather than sequentially.
* **Data pipeline is the usual bottleneck.** Precompute and shard tensors; keep GPUs >90% utilized. Profile early — a starved GPU wastes your best resource.
* **Checkpoint aggressively** and keep a small held-out linear-probe eval running so you catch a bad pretraining run within hours, not days.

---

## 10. Risks, reviewer criticisms & defenses

| Risk / criticism | Mitigation / defense |
| --- | --- |
| **'Self-supervision in genomics isn't new.'** | Be precise: SSL on **RAW REFERENCE SEQUENCE** exists; SSL on **ALIGNMENT/PILEUP EVIDENCE** for SV **CALLING** does not. State the exact combination. |
| **'Gains are marginal F1 over simple baselines'** (the Kalra–Sedlazeck 2026 warning). | Don't compete on headline F1. Lead with the label-efficiency curve and calibration — axes where simple baselines have nothing to say. |
| **Contrastive collapse / unstable pretraining.** | VICReg/Barlow-Twins objective, projection head, large batch/memory queue; monitor a probe metric from step one. |
| **Evidential/uncertainty head hurts raw accuracy.** | Report the with/without ablation honestly; frame calibration as the value even at small F1 cost. |
| **A peer-reviewed SSL-for-SV-calling paper appears before submission.** | Re-run the adversarial novelty search right before submission; escalate by adding the cross-ancestry or calibration angle as the primary claim. |
| **Truth-set sparsity at large deletion sizes.** | Report per-size-bin honestly; note the ceiling rather than hiding it. Consider simulation to stress large events. |

| The one thing to verify before committing hard |
| --- |
| "Several competing methods cited across the reports are 2026 preprints surfaced by other tools and were not independently verified here. Before Phase 2, run one focused literature search on the exact string 'self-supervised pretraining alignment structural variant calling' (and 'masked autoencoder pileup SV'). If a direct peer-reviewed hit exists, pivot the primary claim toward calibration + cross-ancestry, which remain thinner." |

---

## 11. Timeline summary (~10 months)

| Phase | Weeks | Milestone / exit criterion |
| --- | --- | --- |
| **0 — Baseline & harness** | 1–3 | DeepSV reproduced; Truvari harness live; tensor pipeline cached |
| **1 — Supervised skeleton** | 3–6 | Matches DeepSV without SSL; RGB-vs-learned ablation done |
| **2 — Self-supervised pretraining** | 6–12 | MAE + contrastive working; label-efficiency money plot |
| **3 — Uncertainty & calibration** | 12–16 | Calibrated caller; ECE + reliability diagrams |
| **4 — Full eval & ablations** | 16–22 | All baselines, strata, ablation matrix, cross-ancestry |
| **5 — Write / release / submit** | 22–34 | Manuscript submitted; code + weights released |

This is realistic for a small university team with good GPUs. The critical path runs through Phase 2 — if pretraining shows no label-efficiency gain by week 12, that is your go/no-go signal to pivot the primary claim to calibration + cross-ancestry (both still viable) rather than push a weak SSL result.

---

## 12. Publication plan

### 12.1 Suggested paper titles

*Ordered from most descriptive to most concise; pick based on which contribution you lead with.*

1. **AlignSSL-SV:** Self-Supervised Representation Learning on Read Alignments for Label-Efficient, Uncertainty-Calibrated Deletion Calling
2. **Learning to Call Structural Variants Without Labels:** Self-Supervised Pretraining on Sequence Alignments with Calibrated Confidence
3. **Beyond Hand-Crafted Pileups:** Self-Supervised Alignment Representations for Deletion Detection
4. **Calibrated, Label-Efficient Structural-Variant Calling via Self-Supervised Pretraining on BAM Evidence**
5. **MaskAlign-SV:** Masked and Contrastive Pretraining of Alignment Tensors for Robust Deletion Calling

### 12.2 Target venues

| Venue | Fit |
| --- | --- |
| **Bioinformatics** (Oxford) | Primary target. Method papers with strong benchmarking; DeepSV-adjacent audience. |
| **Briefings in Bioinformatics** | Strong alternative; welcomes representation-learning + evaluation-heavy work. |
| **BMC Bioinformatics** | Solid fallback (DeepSV itself was published here). |
| **ISMB / RECOMB** (conference) | If you want a CS-methods venue for the SSL contribution. |

### 12.3 Framing the contribution (abstract skeleton)

Lead with the problem (scarce labels + uncalibrated output in DeepSV-style callers), state the method (self-supervised alignment pretraining + calibrated uncertainty), and headline the two results reviewers will remember: the label-efficiency curve and the calibration/reliability result — with F1 parity-or-better as support, not the headline.

### 12.4 What to release

* Pretrained alignment encoder (open weights) — reusable by others = citations.
* Fine-tuned deletion caller + inference code.
* Preprocessing (BAM→tensor) and evaluation (Truvari + stratification) scripts.
* Config files for every ablation run, for reproducibility.

### 12.5 Self-assessment (honest)

| Axis | Rating | Note |
| --- | --- | --- |
| **Novelty** | 7–8 / 10 | SSL-on-alignments + calibration for SV calling is unoccupied; components exist separately. |
| **Technical difficulty** | 6 / 10 | Feasible for a strong team; SSL stability is the main challenge. |
| **Publication potential** | 7–8 / 10 | Bioinformatics / Briefings realistic if led by label-efficiency + calibration. |
| **Risk of prior work** | 4 / 10 | Moderate; fast-moving field — re-check at submission. |
| **Feasibility on your compute** | 9 / 10 | Fits multi-GPU resources; pretraining is the only heavy cost. |

---

*End of roadmap — proceed from Phase 0. Verify every empirical claim against your own runs.*


-------------------------------------------------------------------------------------------------------------------------------------

Your comparison of PULSE-SV and AlignSSL-SV and final verdict on AlignSSL-SV 

`Let me read the project.md file to evaluate it against PULSE-SV.

This is a substantive comparison — and the first thing worth naming is that **AlignSSL-SV is essentially PULSE-SV, refined and tightened.** The project.md itself says it was "selected from the ten research reports," and its core is identical to my P1+P3 synthesis: self-supervised pretraining on alignment/pileup evidence, a learned encoding replacing DeepSV's RGB scheme, and calibrated uncertainty. So the question isn't really "which of two rival ideas is better" — it's "is this refinement of the shared idea better than my original PULSE-SV framing?"

Let me verify two load-bearing claims before I give a verdict — the CSV-Filter/VICReg claim project.md leans on, and whether a direct SSL-on-alignment-for-SV paper already exists (the risk that would sink *both* proposals).

The prior-art check is reassuring for both proposals: no peer-reviewed self-supervised-on-alignment SV caller surfaced, and the "contrastive/label-efficient SV" queries returned only generic noise — which confirms the intersection is genuinely open. One caveat: I **could not verify** project.md's specific claim that "CSV-Filter used VICReg." In my corpus CSV-Filter ([Xia et al. 2024](https://doi.org/10.1093/bioinformatics/btae539)) is described as a CNN-based filter; the VICReg attribution should be checked against the actual paper before you cite it that way.

## My verdict

**Yes, I agree with the idea — because it *is* the PULSE-SV thesis, and in most respects the project.md version is executed better than my original framing.** This is not a rival concept; it's a tightened, de-risked refinement of the same core (SSL on alignment evidence + learned encoding replacing RGB + calibrated uncertainty).

### Where AlignSSL-SV is genuinely better than my PULSE-SV writeup

| Dimension | Why project.md wins |
|---|---|
| **Scope discipline** | Deletion-only, matching DeepSV *exactly* → a clean head-to-head comparison. My multi-type ambition (DEL/INS/DUP/INV) diluted the comparison and added failure modes for marginal novelty gain. Reviewers reward focus. |
| **Headline result** | The **label-efficiency "money plot"** (F1 vs label fraction, pretrained vs scratch) is the single most persuasive way to demonstrate SSL value. My proposal gestured at "low-label gains" but never crystallized it into *the* figure. This is the strongest single improvement. |
| **Avoiding the architecture-swap trap** | It explicitly demotes the long-context block to "a design detail, never the contribution." I made multi-scale a co-headline (P2), which is weaker, more contestable novelty. |
| **Execution-readiness** | Phase gates with concrete exit criteria, an explicit week-12 go/no-go, and a v1/v2 candidate-generation plan. Mine was a timeline; this is a runbook. |
| **The learnable-encoding ablation** | "Multi-channel tensor + learned 1×1 stem vs DeepSV RGB" is a crisper, more directly defensible ablation than my per-read token embedding framing. |
| **Rigor of calibration** | Adds **conformal prediction** (distribution-free coverage) on top of ensembles/evidential — more rigorous than my temperature-scaling-only plan. |

### The one thing worth carrying back from PULSE-SV

**Multi-scale context for long-deletion recall is a real scientific lever, not just framing.** Short-read callers (DeepSV included) degrade on >1 kb deletions, and jointly modelling base-resolution + kilobase-span context can genuinely recover recall there. project.md already handles this correctly — it *softens* the window and keeps a long-context block as an **ablated design choice** rather than a novelty claim. That's exactly right. I'd only make sure the ablation matrix explicitly reports a **length-stratified** result for it (single-scale vs multi-scale on the 1–5 kb and 5–10 kb bins), so the design choice earns its place empirically.

### Shared weaknesses (true of both, and project.md manages them better)

1. **The dominant risk is identical** — an SSL-on-pileup preprint appearing first. project.md handles this more maturely with an explicit pivot to calibration + cross-ancestry, and the correct instinct to re-run the adversarial search right before submission. My check above suggests the risk is currently low, but it's a fast-moving area.
2. **Novelty ceiling is honestly ~7–8, not 9.** Both proposals are "novel combination, not novel components." project.md's self-assessment (Novelty 7–8) is more calibrated than my 8.5 — the tighter scope trades a little novelty for a lot of defensibility, which is the right trade for a university group targeting *Bioinformatics*/*Briefings*.
3. **Compute honesty** — project.md correctly assumes multi-GPU A100/H100-class hardware and names pretraining as the compute sink. My "1–2 GPUs suffice" claim was optimistic for the contrastive stage (InfoNCE wants large batches). project.md is the more realistic of the two.

### Bottom line

If I had to pick one plan to actually execute, I'd run **AlignSSL-SV as written**, with two amendments: (1) keep the length-stratified multi-scale ablation from PULSE-SV so the long-deletion angle is tested, and (2) verify the CSV-Filter/VICReg claim before relying on it. It is the stronger *plan* — same core bet, sharper scope, better headline result, and a genuinely executable phase structure — whereas PULSE-SV was the stronger *survey-level idea generator*. They're the same organism at two stages of maturity, and the project.md is the more mature one.

One honest caveat on both: the empirical figures in project.md (and my scores) are hypotheses, not results — the week-12 go/no-go on the label-efficiency gain is the real test of whether the shared thesis holds.	`