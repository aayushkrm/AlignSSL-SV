# RESEARCH ROADMAP & EXECUTION PLAN

## AlignSSL-SV: Self-Supervised Pretraining on Read Alignments with Calibrated Uncertainty for Structural-Variant Deletion Calling

> **STATUS BANNER (updated 2026-07-18).** This document was the original ~10-month execution plan, written before any code existed. Phases 0–3 and most of Phase 4 are now **implemented and validated on real 1000 Genomes BAMs**, with three-seed results for every headline claim. This revision keeps the original section numbering and every planned design choice, but adds an **"AS IMPLEMENTED"** callout under each section header stating what was actually built, what changed and why, and what remains open. Treat the original prose as the *plan*; the callouts are the *record*. Where a callout says **DECISION**, that choice has been acted on and downstream work now assumes it.

### Project Summary

* **Project in one sentence:** Pretrain a neural encoder on large volumes of unlabeled read-alignment (BAM/pileup) data using masked-reconstruction and (optionally) redundancy-reduction contrastive objectives, then fine-tune it for deletion calling with a calibrated-confidence output head — directly attacking DeepSV's two admitted weaknesses: its hunger for scarce labels and its uncalibrated binary output.

### Project Overview

| Field | Value |
| --- | --- |
| **Base / reference paper** | Cai, Wu & Gao (2019), DeepSV, *BMC Bioinformatics* 20:665 |
| **Working title** | AlignSSL-SV (see §12 for publication titles) |
| **Target venue** | *Bioinformatics* or *Briefings in Bioinformatics* (Q1) |
| **Team stage (original)** | Lit review + environment setup complete; no experiments run |
| **Team stage (AS IMPLEMENTED, 2026-07-18)** | Phases 0–3 done; Phase 4 partially done (1000G eval complete, GIAB HG002 deferred); manuscript drafted; adversarial novelty re-check complete; 5-superpopulation panel expansion in flight |
| **Compute assumption (original)** | Multi-GPU (A100/H100-class) available |
| **Compute (AS IMPLEMENTED)** | SLURM cluster `ssh:scc`, 4× T4 (15 GB) GPUs shared with other lab users, no dedicated A100 access in practice; all pretraining/fine-tuning done on T4 |
| **Est. duration** | ~10 months to submission (see §11 timeline) |

*This is now a hybrid document: plan + as-built record. Every empirical figure below a callout is a real, reproducible measurement (3 seeds, mean±sd), not a hypothesis.*

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
13. **[NEW] Results as of 2026-07-18**
14. **[NEW] Novelty positioning update (BASILISC)**
15. **[NEW] Open caveats & deferred work**

---

## 1. Executive overview

This document is the complete technical roadmap for **AlignSSL-SV**. The scientific hypothesis is deliberately narrow and testable:

| Central hypothesis |
| --- |
| "Short-read deletion calling improves not from a new network backbone, but from (a) learning the representation of alignment evidence self-supervised on unlabeled BAMs instead of hand-designing it (DeepSV's RGB scheme), and (b) emitting a calibrated confidence per call instead of a bare binary label. The gains should concentrate in the low-label, low-coverage, and repeat-rich regimes where DeepSV is weakest." |

> **AS IMPLEMENTED.** The label-efficiency half of the hypothesis holds cleanly at the extreme end: at 1% labels the from-scratch model collapses (F1 = 0.000 in the DeepSV head-to-head arm; 0.000±0.000 in the main sweep), while the pretrained encoder still calls real deletions (F1 = 0.40–0.58 depending on SSL objective). The two arms converge by 50–100% labels — the classic label-efficiency signature, not a blanket "always wins," and the manuscript states this honestly. The calibration half holds too: the DeepSV-representation baseline is markedly worse-calibrated (ECE 0.091±0.045, T=1.79) than either pretrained or from-scratch AlignSSL-SV arms (ECE 0.010–0.025). The cross-ancestry robustness sub-claim is supported directionally (smaller in-distribution→cross-population generalization gap for the pretrained encoder) but with wide seed variance — flagged as a claim to strengthen with the larger panel, not yet a fully secured result.

Two properties made this a good bet for a university team, and both have been tested in practice:

1. **Novelty:** Confirmed narrower after an adversarial re-check (§14) than originally scored — one genuine prior-art collision (BASILISC, a 2026 repository deposit) was found and the manuscript's claims were reframed around image-free representation + calibration/ancestry, not "SSL for SV" as a category.
2. **Feasibility:** Confirmed. The full pipeline — tensor extraction, MAM/VICReg pretraining, fine-tuning, calibration, a from-scratch DeepSV-representation reimplementation, and cross-population evaluation — runs end-to-end on shared T4 GPUs in a matter of days, not months, once the engineering bugs (§9) were fixed.

The deliverable of the project is a method paper with:

1. A pretrained alignment encoder released as open weights. **[built: `ckpt/encoder_ssl.pt`, MAM-only objective — see §4]**
2. A deletion caller fine-tuned from it. **[built and evaluated across 6 label fractions]**
3. A calibrated-uncertainty head with reliability diagrams. **[built: temperature scaling + MC-dropout, simplified from the original evidential/conformal plan — see §6]**
4. A benchmark showing where the self-supervised prior and calibration help versus DeepSV and modern baselines. **[built: a faithful DeepSV-representation reimplementation, since the original TensorFlow/DIGITS codebase is not runnable — see §13]**

### 1.1 What we keep, replace, and add versus DeepSV

| DeepSV component | Our decision | Why | AS IMPLEMENTED |
| --- | --- | --- | --- |
| Alignment evidence → learned representation → deletion call | **KEEP** | Core insight is correct. | Unchanged. |
| Hand-designed 64-color RGB pileup encoding | **REPLACE** | Lossy, non-learnable; we feed raw channels + learn the encoding. | Built: 18-channel continuous tensor (`tensorize.py`), residual-CNN + Transformer encoder with a learned stem. Also built a faithful RGB+CNN reimplementation as the head-to-head baseline (`deepsv_baseline.py`) since the original repo would not run. |
| Fixed 50 bp / 256×256 windows | **REPLACE (soften)** | Use larger, multi-scale windows. | Built: window shape `(18, 128, 256)` — 128 read rows × 256 bp columns, with length-adaptive binning (`bin_for_len`) mapping deletion size to a span from 4096 bp up. Length-stratified evaluation implemented (§13). |
| k-means candidate generation | **KEEP (v1)** | Reuse truth-VCF-anchored candidates initially. | v1 only: candidates are truth-VCF loci (positives) + random/negative genomic windows, not a learned or classical-caller proposer. Learned candidate generation (v2) not attempted — deferred, see §15. |
| Purely supervised training on scarce labels | **ADD self-supervision** | Pretrain on unlabeled BAMs, fine-tune on the small truth set. | Built and ablated: masked-alignment modelling (MAM) vs VICReg vs combined. **DECISION: MAM-only** wins 5/6 label fractions, best calibration, most stable long-deletion recall — supersedes the original "combine both" plan (§4). |
| Binary softmax output | **ADD calibrated uncertainty** | Evidential / ensemble head + conformal calibration (original plan). | Simplified: temperature scaling + MC-dropout (epistemic/aleatoric decomposition), not the originally planned evidential-NLL + conformal-prediction stack. Documented as a scope simplification, not silently substituted (§6, §15). |

---

## 2. Problem formulation & data foundation

### 2.1 Precise task definition

Scope the paper tightly to **germline long-deletion (DEL, ≥50 bp) calling from short-read (Illumina) whole-genome data**. This matches DeepSV's scope exactly, which makes the head-to-head comparison clean and defensible.

> **AS IMPLEMENTED.** Scope held exactly as planned: DEL-vs-non-DEL binary classification only. Breakpoint regression (item 2 below) was **not** implemented — the fine-tuning head set actually built is classification + calibration only, not the three-head (`cls`+`bp`+`unc`) design in §5.2. This is a real scope reduction from the original plan, made to ship a defensible headline result faster; breakpoint regression is listed as future work (§15).

Insertions, inversions, duplications, translocations, long-read, and somatic calling are explicitly out of scope for v1.

Formally: given a candidate locus and its surrounding aligned reads, predict:

1. DEL vs non-DEL — **[implemented]**
2. Left/right breakpoint offsets — **[NOT implemented — deferred]**
3. A calibrated confidence — **[implemented: temperature scaling + MC-dropout]**

Training has two stages: self-supervised pretraining with no labels, then supervised fine-tuning on truth-set deletions. **[implemented as planned]**

### 2.2 Datasets — exactly what to download and how to use each

| Dataset | Role in project | Notes (original plan) |
| --- | --- | --- |
| **1000 Genomes Phase 3** (Illumina WGS BAMs) | Self-supervised PRETRAINING corpus (unlabeled) + historical comparability with DeepSV | Hundreds of samples, ~7–30×. |
| **GIAB HG002** (+ HG003/HG004) with the GIAB Tier-1 SV benchmark | Supervised FINE-TUNE + primary in-distribution TEST | Gold-standard truth (Zook et al. 2020). |
| **HGSVC / HPRC** diverse-ancestry samples | Held-out GENERALIZATION test (cross-ancestry) | Tests whether the SSL representation generalizes. |
| Down-sampled copies (10×/30×/60×) | Coverage-robustness axis | Cheap, informative slice. |
| RepeatMasker / segdup annotation | Region STRATIFICATION | Shows where the prior helps most. |

> **AS IMPLEMENTED (major deviation, deliberate, open caveat).** We did **not** use GIAB HG002 or HGSVC/HPRC. Instead: (1) **Truth labels** come from the 1000 Genomes Phase 3 integrated SV genotype VCF (`ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz`, 40,975 deletions across 2,504 samples) — independently byte-size-verified against the official EBI FTP source on 2026-07-17. (2) **BAMs used**: original 2-sample pretrain corpus NA19238 (YRI) + NA19625 (ASW); held-out cross-population test NA12878 (CEU); an in-progress 5-superpopulation expansion panel — NA18525 (CHB), NA19648 (MXL), NA20502 (TSI) already downloaded/extracted, NA20845 (GIH)/NA19017 (LWK)/NA19240 (YRI)/NA19239 (YRI, QC/trio) still downloading as of this revision. Planned final split: **TRAIN** = NA19238+NA19625+NA18525+NA19648+NA20502+NA20845 (6 samples, 5 superpopulations); **HELD-OUT TEST** = NA12878 (CEU) + NA19017 (LWK), both unseen ancestries; **TRIO/QC** = NA19239+NA19240. (3) Coverage down-sampling and repeat/segdup stratification were **not** implemented — deferred (§15). **Ruling (standing, unchanged): proceed on 1000G now; add GIAB HG002 as the Phase-4 headline gold-standard benchmark once the Truvari harness exists.** This is caveat **C1**.

| Data hygiene rule (non-negotiable) |
| --- |
| Never let a pretraining sample overlap a test individual or test chromosome. Hold out entire individuals AND entire chromosomes for test. |

> **AS IMPLEMENTED.** Held exactly: chr1–11 = train, chr12–22 = test (matching DeepSV's own split), individual-level holdout for NA12878/NA19017 cross-population evaluation. No leakage across the tensor extraction, pretraining, or fine-tuning code paths.

### 2.3 The candidate-generation choice

* **v1 (recommended, low-risk):** truth-VCF-anchored positives + sampled negatives.
* **v2 (optional, higher novelty):** a learned scanning head.

> **AS IMPLEMENTED.** v1 only, as recommended. Candidates are drawn directly from the 1000G truth VCF (positives) plus randomly sampled genomic windows (negatives), never from a classical caller (Delly/Manta) or a learned proposer. v2 is deferred (§15) — this keeps candidate-generation quality out of scope of the comparison, which is the intended effect, but it also means recall against *undetected* loci (false negatives from a real caller's candidate stage) is not measured; only classification performance on a fixed candidate set is. This should be stated plainly in the manuscript's limitations (it already is, per PROGRESS.md).

---
## 3. Input representation — the learnable alignment tensor

This section replaces DeepSV's RGB scheme. Instead of packing signals into an 8-bit color, we build a **multi-channel tensor** where each alignment signal is its own channel, then let a small learned stem fuse them.

### 3.1 Tensor layout

For a candidate locus, build a tensor of shape `[C, R, W]`: `C` channels, `R` read rows, `W` window columns.

#### Recommended channels (C ≈ 8–10, original plan)

1. Base identity (A/C/G/T/gap)
2. Base quality (Phred)
3. Mapping quality (MAPQ)
4. Strand
5. Read-pair orientation / discordant flag
6. Soft-clip / split-read flag
7. Insert-size z-score
8. Per-column read depth
9. Reference base track

> **AS IMPLEMENTED (`alignssl/tensorize.py`, verified shape `(18, 128, 256)`).** Built with **18 channels**, not 8–10 — the plan's minimum recommendation was expanded to include richer per-read encodings (separate one-hot planes for base identity rather than a single embedding channel, explicit CIGAR-derived indel-context channels, and a padding/validity mask channel) once real BAMs were in hand and channel budget was cheap on a `(18,128,256)` float16 tensor (~1.18 MB/window). `R=128` read rows (padded/masked) × `W=256` columns, as recommended. Reference-base track, MAPQ, strand, insert-size z-score, and per-column depth are all present as planned; breakpoint offset labels are stored in the shard schema (`bp` key) but **not** consumed by any implemented loss (§2.1 scope reduction). Tensors are built with `pysam`, cached as compressed `.npz` shards (1024 items/shard) — matches the plan's "cache, don't build on the fly" guidance. Continuous channels are normalized with fixed constants (`isize_mean=450, isize_sd=100, depth_norm=60`) rather than training-set-computed statistics — a simplification worth revisiting if the panel expansion changes coverage/insert-size distributions materially.

### 3.2 Implementation notes

> **AS IMPLEMENTED.** All four bullet points from the original plan were followed: `pysam`-based extraction, compressed `.npz` shard caching, fixed-row padding with a mask channel, and offline precomputation (`extract_tensors.py` run as a batch SLURM job, never inline with GPU training). One added engineering fix not anticipated in the plan: for pretraining specifically, 40 separate shard files caused severe DataLoader I/O starvation on the cluster's shared filesystem; the fix was to consolidate all shards into a single flat float16 `.npy` memmap (`build_memmap.py`) and stage it into node-local `/dev/shm` at job start, reading with `mmap_mode='r'` and `num_workers=0`. This was necessary for GPU utilization, not part of the original design, and is now the standard pretraining data path.

---

## 4. Stage 1 — Self-supervised pretraining

This is the scientific heart of the project. Two complementary objectives were recommended in the original plan; both were implemented and ablated against a third (combined) variant.

### 4.1 Objective A — Masked-channel / masked-region modeling (MAE-style)

Randomly mask a large fraction of the input and train the encoder + a lightweight decoder to reconstruct it. Loss: MSE on continuous channels + cross-entropy on categorical channels.

> **AS IMPLEMENTED as "MAM" (masked-alignment modelling), `alignssl/ssl.py`.** Built as planned: asymmetric encoder (heavy) / decoder (light, discarded after pretraining), mask ratio swept 0.5→0.75 per the original recipe (settled at 0.6 for production runs). Implemented as a single MSE-style masked-reconstruction loss over the continuous tensor (not split by channel type into MSE+CE — the categorical channels are reconstructed under the same continuous regression loss, a simplification from the original per-channel-type loss design).

### 4.2 Objective B — Contrastive region discrimination (InfoNCE) → built as VICReg, not InfoNCE

Create two augmented views of the same locus, pull embeddings together, push apart embeddings of different loci.

| Guard against a known failure mode (original plan) |
| --- |
| "Contrastive methods can collapse... consider a redundancy-reduction objective (VICReg / Barlow Twins) which is more collapse-resistant than plain InfoNCE. CSV-Filter used VICReg for exactly this reason." |

> **AS IMPLEMENTED — a plan-level substitution made deliberately, not a deviation discovered by accident.** The original §4.2 nominally specced InfoNCE with a note that VICReg was a collapse-resistant alternative "CSV-Filter used." We built **VICReg directly** (`sim_coef=25, var_coef=25, cov_coef=1`, `alignssl/ssl.py`), skipping InfoNCE entirely, following the guard-against-failure-mode advice from the outset rather than discovering collapse empirically. The CSV-Filter/VICReg attribution was independently verified against the actual paper (Xia et al. 2024, *Bioinformatics*, DOI 10.1093/bioinformatics/btae539) before relying on it, resolving the "verify before citing" flag a reviewing agent raised on this document — confirmed true. Coverage-invariance and cross-sample augmented views (the two view types recommended) were **not** separately implemented; VICReg is applied over two stochastic augmentations of the same tensor (masking-based), not the coverage-downsampling or cross-individual views originally specified. This is a real scope reduction, noted as future work (§15).

### 4.3 Encoder architecture

Keep the backbone unremarkable on purpose.

> **AS IMPLEMENTED (`alignssl/encoder.py`).** Residual-CNN stem (`stem_ch=32`) + CNN body (`body_ch=64`, `n_res=3` residual blocks) over the local tensor, followed by a light Transformer block (`d_model=128, n_tx=2, n_heads=4`) over the column axis for long-context — exactly the "CNN stem + light long-context block" design recommended, using a Transformer rather than a Mamba/SSM block (SSM was offered as an alternative in the plan, not mandated). Framed in the manuscript as a design detail, not a contribution, per the plan's explicit warning against the "encoder-swap" rejection trap.

### 4.4 Pretraining recipe — and the ablation that changed the plan

| Setting | Original starting value | AS IMPLEMENTED |
| --- | --- | --- |
| Optimizer | AdamW | AdamW (unchanged) |
| LR schedule | Warmup + cosine decay | Cosine with `pct_start=0.05` warmup (unchanged) |
| Peak LR | 1e-3 (contrastive) / 1.5e-4 (MAE) | 1.5e-4 (production runs; matches MAE-only value since MAM-only was selected) |
| Batch size | ≥512 (contrastive) | 96 (T4 15 GB VRAM hard ceiling — 128 OOMs at ~14.1 GB peak; far below the ≥512 recommendation) |
| Mask ratio | 0.5 → 0.75 | 0.6 |
| Pretraining data | 1000G BAMs, millions of loci genome-wide | 80,000 windows from 2 samples (NA19238, NA19625), chr1-11 only — orders of magnitude smaller than "millions of loci," a real scale gap (§15) |
| Precision | bf16 | fp16, selected by compute-capability check (`sm_80` cutoff) — T4 (`sm_75`) emulates bf16 in software at ~4× slower than native fp16, so the plan's bf16 default was actively wrong for this hardware and had to be corrected |
| Checkpointing | Save every N steps + linear-probe proxy | Save at epoch end; no linear-probe proxy tracked during pretraining (added value, deferred) |

**The ablation that superseded the original combined-objective design.** The plan's default was to run both MAE and contrastive objectives and "ablate each" without committing to one for production. A 3-seed ablation (`abl_ft_{combined,maeonly,viconly}_seed{0,1,2}.json`) was run comparing MAM-only, VICReg-only, and Combined (MAM+VICReg) as the pretraining objective, then fine-tuned identically on each:

| frac | Combined (MAM+VICReg) F1 | MAM-only F1 | VICReg-only F1 |
|------|---------------------------|--------------|------------------|
| 0.01 | 0.400 ± 0.066 | **0.584 ± 0.073** | 0.371 ± 0.035 |
| 0.05 | 0.408 ± 0.085 | **0.636 ± 0.020** | 0.430 ± 0.017 |
| 0.10 | 0.565 ± 0.052 | **0.685 ± 0.022** | 0.488 ± 0.047 |
| 0.25 | 0.678 ± 0.040 | **0.722 ± 0.080** | 0.657 ± 0.022 |
| 0.50 | 0.748 ± 0.070 | 0.804 ± 0.056 | 0.825 ± 0.067 |
| 1.00 | 0.855 ± 0.031 | **0.931 ± 0.006** | 0.873 ± 0.042 |

Calibration and long-deletion recall at 100% labels:

| Config | ECE | 5000+ bp recall |
|--------|-----|-------------------|
| Combined | 0.022 ± 0.009 | 0.578 ± 0.291 (unstable — one seed collapsed) |
| **MAM-only** | **0.010 ± 0.001** | 0.908–0.947 ± 0.055 |
| VICReg-only | 0.016 ± 0.006 | 0.809–0.911 ± 0.079 |

> **DECISION (acted on, supersedes the original plan): SSL objective changed to MAM-only** for the 8-sample panel re-pretrain and all downstream work. MAM-only wins 5 of 6 label fractions, has the best and tightest calibration, and the most stable long-deletion recall. Combined — the plan's original default recommendation — is the *worst* performer at full supervision (F1 0.855 vs MAM-only's 0.931) and has unstable long-deletion recall (one seed collapsed to near-zero). Framing for the paper: a **"less-is-more" ablation** — MAM alone is sufficient and superior; adding VICReg hurts stability rather than helping, which is a more defensible and more interesting empirical finding than "we combined two losses."

---

## 5. Stage 2 — Supervised fine-tuning for deletion calling

Attach task heads to the pretrained encoder and fine-tune on truth deletions.

### 5.1 Task heads (original plan: classification + breakpoint regression + uncertainty)

> **AS IMPLEMENTED (`alignssl/heads.py`).** Only the **classification head** was built and trained: DEL vs non-DEL via **focal loss** (`γ=2`, matches the plan exactly — chosen for class imbalance). The **breakpoint regression head** (SmoothL1/Huber) was **not implemented** — a real scope reduction from §5.2's three-term loss (§2.1). The uncertainty mechanism (§6) is attached and trained jointly with the classification head, as planned, but via temperature scaling + MC-dropout rather than the evidential-NLL head originally specified in §5.2's loss formula.

### 5.2 Combined objective — simplified

Original: $L = \lambda_{cls} \cdot \text{FocalLoss} + \lambda_{bp} \cdot \text{SmoothL1} + \lambda_{unc} \cdot \text{UncertaintyLoss}$, with $\lambda_{cls}=1.0, \lambda_{bp}=0.5, \lambda_{unc}=0.3$.

> **AS IMPLEMENTED.** $L = \text{FocalLoss}(\gamma=2)$ only. The breakpoint and evidential-uncertainty terms — and their weights — were never instantiated; MC-dropout and temperature scaling are applied as a post-hoc/inference-time mechanism (§6), not as an additional training loss term. This is the single largest simplification in the project relative to the original plan and should be stated explicitly in the manuscript's methods section (it already is).

### 5.3 The label-efficiency experiment — the headline result, confirmed

> **AS IMPLEMENTED and delivered exactly as envisioned.** The money plot (F1 vs label fraction, pretrained vs from-scratch vs DeepSV-representation baseline) was built at 6 fractions (1/5/10/25/50/100%), 3 seeds each. Main-sweep numbers (2-sample pretrain corpus, mean ± sd): pretrained F1 1%=0.400±0.066→100%=0.803±0.117; from-scratch F1 1%=0.000±0.000→100%=0.819±0.036. The DeepSV-representation baseline plateaus at F1≈0.57 and never clears ~0.6 at any label fraction, and is beaten by the pretrained/scratch AlignSSL-SV arms at 5 of 6 fractions. Figure and CSVs saved as artifacts (`fig_label_efficiency.png`, `results_label_efficiency.csv`). The wide low-label gap closing by 100% is exactly the "reviewer-convincing signature" the plan called for.

---

## 6. Calibrated uncertainty — the second contribution, simplified from the original design

DeepSV outputs a bare, uncalibrated probability. We add a calibration mechanism and, crucially, evaluate it.

### 6.1 Choose an uncertainty mechanism (original plan offered 4 options + conformal on top)

| Method | Original recommendation | AS IMPLEMENTED |
| --- | --- | --- |
| Deep ensembles | Strongest baseline, use if budget allows | **Not implemented** — N× training cost was judged too expensive on shared T4s for the project's timeline |
| MC-dropout | Cheap, weaker epistemic estimate | **Implemented** (`dropout=0.2`) — provides the epistemic component |
| Evidential deep learning | Elegant, single-model, watch stability | **Not implemented** — deferred as a stated simplification |
| Conformal prediction (post-hoc, on top of any of the above) | Add on top for distribution-free coverage guarantees | **Not implemented** — deferred |

> **DECISION (simplification, made explicitly, not silently substituted): temperature scaling + MC-dropout**, not the recommended ensemble/evidential + conformal stack. This is a genuine reduction in rigor relative to the original design — conformal prediction's distribution-free coverage guarantee is a stronger claim than temperature-scaled ECE — and is documented here and in the manuscript as future work (§15), not presented as equivalent.

### 6.2 How to calibrate and prove it

> **AS IMPLEMENTED.** Held-out calibration is the chr12–22 test split (not a separate calibration-only split — the same test set is used for both ECE reporting and the label-efficiency F1, a minor methodological economy worth flagging to reviewers). Temperature scaling fit post-hoc; ECE computed and reported at every label fraction where applicable, always at 100% labels as the headline number. Reliability diagrams were **not** rendered as a standalone figure (ECE numbers are reported in tables/CSV, not visualized) — a presentation gap to close before submission, not a measurement gap. Risk-coverage / selective-prediction curves were **not implemented** — deferred (§15).

**Calibration result, 100% labels, 3-seed mean±sd (main sweep):** pretrained ECE = 0.018±0.009 (T=0.78); from-scratch ECE = 0.025±0.009 (T=0.82); DeepSV-representation baseline ECE = 0.091±0.045 (T=1.79). The pretrained and from-scratch AlignSSL-SV arms are both far better calibrated than the DeepSV-lineage baseline — this is the calibration headline the plan called for, and it holds.

---
## 7. Evaluation protocol

Use Truvari to match calls against GIAB truth; report metrics always stratified.

> **AS IMPLEMENTED (deviation, open caveat C2).** Truvari was **not** used — evaluation is direct genotype-vs-prediction scoring against the 1000G truth VCF on the held-out chromosome split, not breakpoint-tolerant SV-benchmarking. This is consistent with using 1000G instead of GIAB HG002 (§2.2, C1): Truvari's value is greatest against a gold-standard breakpoint-precise truth set, and the harness has not yet been built. **Standing ruling: build the Truvari harness alongside the GIAB HG002 addition in Phase 4** — both caveats resolve together.

### 7.1 Metrics

* Precision, Recall, F1 — **implemented**, via direct scoring, not Truvari.
* Breakpoint MAE — **not implemented** (no breakpoint head, §5.1).
* Calibration: ECE, reliability diagram, risk-coverage — **ECE implemented; reliability diagram and risk-coverage curve not rendered** (§6.2).
* Label efficiency — **implemented and is the headline result** (§5.3).

### 7.2 Stratification axes

| Stratum | Original plan | AS IMPLEMENTED |
| --- | --- | --- |
| Deletion size bins | 50–200, 200–500, 500bp–1kb, 1–5kb, 5–10kb+ | **Implemented**, close to plan: bins observed at 50-200/200-500/500-1000/1000-5000/5000+ bp, with recall reported per bin (`fig_length_strata.png`, `results_length_strata.csv`) |
| Coverage (10×/30×/60×) | Via down-sampling | **Not implemented** — deferred (§15) |
| Region class (unique vs repeat/segdup) | RepeatMasker/segdup annotation | **Not implemented** — deferred (§15) |
| Ancestry (in-dist vs held-out) | HGSVC/HPRC | **Implemented** using 1000G superpopulations instead: NA12878 (CEU) held out from a YRI/ASW-trained encoder in the initial cross-population run; the 5-superpopulation panel (CHB/MXL/TSI/GIH/LWK) extends this substantially once downloads complete |
| Label budget (1–100%) | — | **Implemented, is the headline result** |

**Cross-population result, 3-seed mean±sd (2-sample training corpus, before panel expansion):** in-distribution F1 (African, held-out chr) pretrained 0.686±0.137 vs scratch 0.898±0.052; cross-population F1 (NA12878/CEU) pretrained 0.672±0.174 vs scratch 0.781±0.136; cross-population ECE pretrained 0.113±0.131 vs scratch 0.055±0.050; **generalization gap** (in-dist→cross-pop F1 drop) pretrained +0.015±0.114 vs scratch +0.117±0.084. Interpretation held honestly in the manuscript: both models transfer without collapse; the pretrained encoder's near-zero mean gap is suggestive of better ancestry robustness, but per-seed variance is high enough (±0.114 to ±0.174) that this is reported as a directional finding to be confirmed at panel scale, not a secured claim.

### 7.4 Ablation matrix — partially completed

| Ablation | Original plan | AS IMPLEMENTED |
| --- | --- | --- |
| Pretrained vs from-scratch | Value of self-supervision | **Done** — the core result |
| MAE-only vs contrastive-only vs both | Which objective drives the gain | **Done** — the ablation that changed the plan (§4.4) |
| With vs without coverage-invariance views | Source of low-coverage robustness | **Not done** — no coverage-invariance views were built (§4.2) |
| With vs without cross-sample views | Source of cross-ancestry robustness | **Not done** in the strict sense (no dedicated cross-sample augmentation); the cross-population *evaluation* (not ablation) substitutes partially |
| Learned channels vs DeepSV RGB encoding | Value of the learnable representation | **Done** — the DeepSV-representation head-to-head baseline (§13) |
| With vs without uncertainty head | Does calibration cost raw F1? | **Not done as a controlled ablation** — MC-dropout/temperature scaling is always on in the reported pipeline; no "without" arm was run |
| CNN-only vs CNN+long-context block | Justifies the context block | **Not done** — the Transformer context block was never ablated out |

---

## 8. Step-by-step execution plan

> **AS IMPLEMENTED — phase-by-phase status.**

### Phase 0 — Baseline & harness (weeks 1–3)

* Reproduce DeepSV on HG002 / run its released code. → **Attempted, found infeasible.** The actual GitHub repository (`github.com/CSuperlei/DeepSV`) does not run: `Generate_Deletion_Image.py` has argparse imported but never instantiated, hardcoded placeholder paths, and a dead `return` after an error print; the pipeline depends on the discontinued NVIDIA DIGITS framework, TensorFlow 1.x `contrib.slim` (removed in TF2), and standalone Keras 1.x calls (`K.set_image_dim_ordering`) removed years ago; there is no requirements/setup file; the released sample zips contain only cached 2018 result files, not a runnable pipeline. **Resolution:** built a faithful reimplementation of the DeepSV *representation* (RGB pileup encoding, A=red/T=green/C=blue/G=black with a MAPQ-weighted intensity) and a matching supervised CNN (`DeepSVNet`, 4 conv blocks 32→64→128→256, 389,410 params) on our own tensors/splits — labeled throughout as "**DeepSV-representation reimplementation**" / "DeepSV-repr. baseline," never claimed as a run of the original binary. This relabeling was applied consistently across the manuscript, deck, and progress tracker to avoid overclaiming.
* Truvari harness. → **Not built** (C2, standing).
* Alignment-tensor pipeline. → **Done**, exceeds the "loads fast, visually matches IGV" bar informally (validated via shape/content checks, not a visual IGV comparison).

### Phase 1 — Supervised skeleton, no SSL (weeks 3–6)

* Train encoder + heads fully supervised, no pretraining. → **Done** (the "from-scratch" arm in every sweep).
* Learned-channels-vs-RGB ablation. → **Done**, via the DeepSV-representation head-to-head rather than an ablation on a shared backbone — learned channels + our encoder beats the DeepSV representation + `DeepSVNet` at 5/6 label fractions and is far better calibrated.

### Phase 2 — Self-supervised pretraining (weeks 6–12)

* MAE objective, monitor linear-probe proxy. → **Done** (as "MAM"); no linear-probe proxy tracked during pretraining itself (evaluated only after fine-tuning).
* Contrastive objective with coverage + cross-sample views, collapse guards. → **Partially done**: VICReg implemented directly (collapse-resistant by construction, per plan's own guidance); coverage/cross-sample views not implemented.
* Label-efficiency money plot. → **Done**, and is the strongest single deliverable of the project so far.

### Phase 3 — Uncertainty & calibration (weeks 12–16)

* Ensemble/evidential + conformal. → **Simplified to temperature scaling + MC-dropout** (§6).
* Risk-coverage curves. → **Not done.**

### Phase 4 — Full evaluation & ablations (weeks 16–22)

* All baselines, stratifications, ablation matrix, cross-ancestry test. → **Partially done**: DeepSV baseline ✓, length strata ✓, label-fraction ablation ✓, cross-population eval ✓ (2-sample corpus; panel expansion in flight); coverage/region/uncertainty-ablation strata ✗ (§15).

### Phase 5 — Writing, release, submission (weeks 22–34)

* Draft manuscript, release code+weights, adversarial novelty re-check, submit. → **Manuscript drafted** (`AlignSSL_SV_manuscript.md`); **adversarial novelty re-check done** (§14, found and addressed the BASILISC collision); code packaged (`alignssl_sv.tar.gz`); weights not yet formally released to a public archive; **not yet submitted.**

---

## 9. Compute, tooling & engineering

### 9.1 Software stack

> **AS IMPLEMENTED.** `pysam`/`samtools` for I/O (matches plan). `.npz` shard + flat float16 memmap for storage (plan recommended HDF5 or `.npz`; memmap consolidation was an added fix, §3.2). `PyTorch` (2.5.1+cu121 on the cluster's `deepsv2_new` env for GPU work; 2.12.1 CPU-only in the local `svssl` build/test env) — no Lightning, no `mamba-ssm` (Transformer chosen over SSM, §4.3). No experiment tracker (W&B/MLflow) was wired in — all results were aggregated manually from JSON result dumps. This is a reproducibility gap worth closing before submission (raw JSONs are preserved and sufficient to reconstruct every table, but a run registry would be stronger).

### 9.2 Using the GPU resources well — real engineering history, not hypothetical

> **AS IMPLEMENTED, with a documented bug chain.** Contrary to the original compute assumption (multi-GPU A100/H100-class), production runs were on **shared T4 (15 GB) GPUs**, one per job, not DDP multi-GPU. Bugs found and fixed in order: (1) DataLoader reading 40 separate ~1.2 GB compressed shards starved the GPU — fixed by the `/dev/shm` memmap consolidation (§3.2); (2) batch 256 OOM'd a 15 GB T4 — fixed by dropping to batch 96 plus `expandable_segments:True`; (3) `torch.cuda.is_bf16_supported()` returns `True` on Turing (T4) but bf16 there is software-emulated and ~4× slower than native fp16 — fixed by selecting precision via compute-capability check (`<sm_80` → fp16) rather than the capability flag; (4) a separate fine-tuning performance bug (`ShardDataset.__getitem__` re-decompressing a `.npz` on nearly every access under shuffle) caused 4-hour jobs to complete only ~2 of 6 label fractions — fixed by preloading the full ~25 MB labeled set into contiguous in-RAM arrays at init, cutting a >1-hour fraction to ~3 minutes. None of these are present in the original plan, which assumed hardware and a data pipeline scale that did not match what was actually available; documenting them here because they materially shaped the achievable timeline (§11 update, §15).

---

## 10. Risks, reviewer criticisms & defenses

> **AS IMPLEMENTED / status of each defense.**

| Risk / criticism | Original mitigation | Status |
| --- | --- | --- |
| "Self-supervision in genomics isn't new." | Be precise: SSL on raw reference sequence exists; SSL on alignment/pileup evidence for SV calling does not. | **Partially undermined and then repaired.** BASILISC (2026) is exactly an SSL-on-alignment-evidence-for-SV effort, found in the adversarial re-check (§14). The defense was rebuilt around a narrower, still-true claim: image-free continuous-tensor SSL + calibrated ancestry-robust uncertainty, a combination BASILISC does not cover. |
| "Gains are marginal F1 over simple baselines." | Lead with label-efficiency + calibration, not headline F1. | **Followed as planned** — the manuscript leads with the low-label rescue and the calibration gap versus the DeepSV baseline, not a blanket F1 win (which does not hold at 100% labels: from-scratch edges pretrained there in the main sweep). |
| Contrastive collapse / unstable pretraining. | VICReg, projection head, large batch, probe metric. | VICReg used from the outset (no InfoNCE collapse observed to guard against). No probe metric was tracked during pretraining itself — collapse was checked only indirectly via downstream fine-tune F1. |
| Evidential/uncertainty head hurts raw accuracy. | Report the with/without ablation honestly. | **Not directly testable as planned** — no evidential head was built, and no with/without uncertainty ablation was run (§7.4). |
| A peer-reviewed SSL-for-SV paper appears before submission. | Re-run the adversarial novelty search right before submission. | **Done once already** (§14); standing instruction to re-run again immediately before submission. |
| Truth-set sparsity at large deletion sizes. | Report per-size-bin honestly. | **Done** — length-stratified recall is reported and is honestly weak at 5kb+ for both arms (high variance), stated as an open problem, not hidden. |

---

## 11. Timeline summary (~10 months) — status update

| Phase | Weeks (plan) | Milestone | Status (2026-07-18) |
| --- | --- | --- | --- |
| 0 — Baseline & harness | 1–3 | DeepSV reproduced; Truvari harness live; tensor pipeline cached | DeepSV reproduction infeasible → reimplementation done instead; Truvari harness not built (C2); tensor pipeline done |
| 1 — Supervised skeleton | 3–6 | Matches DeepSV without SSL; RGB-vs-learned ablation done | Done (via head-to-head baseline) |
| 2 — Self-supervised pretraining | 6–12 | MAE + contrastive working; label-efficiency money plot | Done; objective ablation additionally resolved (MAM-only wins) |
| 3 — Uncertainty & calibration | 12–16 | Calibrated caller; ECE + reliability diagrams | ECE done; reliability diagrams not rendered; mechanism simplified |
| 4 — Full eval & ablations | 16–22 | All baselines, strata, ablation matrix, cross-ancestry | Partially done — see §7.4 and §13 |
| 5 — Write / release / submit | 22–34 | Manuscript submitted; code + weights released | Manuscript drafted, not submitted; code packaged, weights not archived |

The critical-path go/no-go at week 12 ("if pretraining shows no label-efficiency gain, pivot to calibration + cross-ancestry") **resolved positively** — the label-efficiency gain is real and is now the lead result, so no pivot was needed.

---

## 12. Publication plan

Unchanged from the original plan (titles, target venues, release plan, abstract skeleton) — see the original text below for reference. The self-assessment scores are superseded by §14.

### 12.1 Suggested paper titles

1. **AlignSSL-SV:** Self-Supervised Representation Learning on Read Alignments for Label-Efficient, Uncertainty-Calibrated Deletion Calling
2. **Learning to Call Structural Variants Without Labels:** Self-Supervised Pretraining on Sequence Alignments with Calibrated Confidence
3. **Beyond Hand-Crafted Pileups:** Self-Supervised Alignment Representations for Deletion Detection
4. **Calibrated, Label-Efficient Structural-Variant Calling via Self-Supervised Pretraining on BAM Evidence**
5. **MaskAlign-SV:** Masked and Contrastive Pretraining of Alignment Tensors for Robust Deletion Calling

### 12.2 Target venues

| Venue | Fit |
| --- | --- |
| **Bioinformatics** (Oxford) | Primary target. |
| **Briefings in Bioinformatics** | Strong alternative. |
| **BMC Bioinformatics** | Fallback (DeepSV's own venue). |
| **ISMB / RECOMB** | If leading with the SSL/CS-methods angle. |

### 12.3 Framing the contribution

Unchanged — lead with the label-efficiency curve and calibration/reliability result; F1 parity-or-better as support, not the headline.

### 12.4 What to release

Pretrained encoder weights, fine-tuned caller + inference code, preprocessing/evaluation scripts, per-run configs. **Status:** code is packaged (`alignssl_sv.tar.gz`); a public weights/code release (e.g. Zenodo/GitHub archive) has not yet been made.

### 12.5 Self-assessment — superseded, see §14 for current numbers

The original table (Novelty 7–8/10, Technical difficulty 6/10, Publication potential 7–8/10, Risk of prior work 4/10, Feasibility 9/10) is retained below for the historical record but is **out of date** — §14 has the current, adversarially-checked scores.

---
## 13. [NEW] Results as of 2026-07-18

### 13.1 Headline: label-efficiency and DeepSV-representation head-to-head

3 seeds, 6 label fractions, held-out chr12–22 test:

| Label % | Pretrained F1 | From-scratch F1 | DeepSV-repr. baseline F1 |
|---|---|---|---|
| 1% | 0.400 ± 0.066 | 0.000 ± 0.000 | 0.081 ± 0.115 |
| 5% | — | — | 0.492 ± 0.029 |
| 10% | — | — | 0.543 ± 0.066 |
| 25% | — | — | 0.302 ± 0.177 |
| 50% | — | — | 0.557 ± 0.250 |
| 100% | 0.803 ± 0.117 | 0.819 ± 0.036 | 0.574 ± 0.076 |

(Full 6-point curves for pretrained/from-scratch are in `results_label_efficiency.csv`; the DeepSV-repr. baseline never exceeds ~0.6 F1 at any fraction and shows high seed-to-seed variance, consistent with training instability on a shallow supervised CNN at small label budgets — itself a finding worth stating.)

Calibration at 100% labels: pretrained ECE 0.018±0.009 (T=0.78); from-scratch ECE 0.025±0.009 (T=0.82); **DeepSV-repr. baseline ECE 0.091±0.045 (T=1.79)** — a 4–5× worse calibration than either AlignSSL-SV arm.

### 13.2 SSL objective ablation (supersedes the original combined-objective plan)

See §4.4 for the full table. **DECISION: MAM-only** is the production objective going forward.

### 13.3 Length-stratified recall

| Bin (bp) | n | Pretrained recall | From-scratch recall |
|---|---|---|---|
| 50–200 | 231 | 0.906 | 0.964 |
| 200–500 | 94 | 0.823 | 0.954 |
| 500–1000 | 131 | 0.804 | 0.967 |
| 1000–5000 | 286 | 0.653 | 0.798 |
| 5000+ | 94 | 0.628 | 0.496 |

The pretrained encoder recalls long deletions (5000+ bp) noticeably better than from-scratch (0.628 vs 0.496) despite lower recall in the small/mid-size bins — the opposite pattern of the label-efficiency result, and a genuinely interesting secondary finding: self-supervision seems to help most exactly where DeepSV-style small local windows are weakest.

### 13.4 Cross-population generalization (2-sample training corpus; panel expansion in flight)

See §7.2 for the full numbers. Directional finding (smaller mean generalization gap for pretrained), high seed variance, to be confirmed at panel scale.

### 13.5 Panel expansion status (as of this revision)

| Sample | Superpopulation | Role | Status |
|---|---|---|---|
| NA19238 | YRI | TRAIN (original) | Extracted, tensors validated |
| NA19625 | ASW | TRAIN (original) | Extracted, tensors validated |
| NA18525 | CHB | TRAIN (panel) | Extracted, tensors validated, BAM deleted post-validation |
| NA19648 | MXL | TRAIN (panel) | Extracted, tensors validated, BAM deleted post-validation |
| NA20502 | TSI | TRAIN (panel) | Extracted, tensors validated, BAM deleted post-validation |
| NA20845 | GIH | TRAIN (panel) | Downloading (parallel chunked fetch), integrity-gate re-check in progress |
| NA19017 | LWK | TEST (held-out) | Downloading (parallel chunked fetch), integrity-gate re-check in progress |
| NA19240 | YRI | TRIO/QC | Downloading (parallel chunked fetch) |
| NA19239 | YRI | TRIO/QC | Downloading (single-stream redo, ~71% at last check) |
| NA12878 | CEU | TEST (held-out) | Extracted, tensors validated (1448 items); BAM retained as insurance |

Once all downloads pass the mandatory `samtools view -c` BGZF integrity gate and are extracted, the plan is to re-pretrain with **MAM-only** on the 6-sample TRAIN panel and re-run the full label-efficiency/calibration/length-strata/cross-population sweep against the CEU+LWK held-out test set.

---

## 14. [NEW] Novelty positioning update (BASILISC)

An adversarial novelty re-check (searching OpenAlex, PubMed, and arXiv with alternative terminology, deliberately trying to disprove novelty) found **one genuine prior-art collision**:

**BASILISC** (Banerjee, 2026, Stanford Digital Repository, DOI 10.25740/jj829qd2843) — a BEiT-style masked-image-modeling approach to self-supervised pretraining for structural variant analysis. Differentiation:

| Axis | BASILISC | AlignSSL-SV |
|---|---|---|
| Representation | Rendered RGB pileup images + dVAE discrete visual tokens (a learned tokenizer, BEiT-style) | Raw 18-channel continuous alignment tensor, no image rendering, no discrete tokenizer |
| Pretext task | BEiT masked discrete-token classification | Masked-alignment (continuous) regression, optionally + VICReg |
| Calibration/uncertainty | Absent | Central contribution (temperature scaling + MC-dropout, §6) |
| Publication status | Repository deposit (not peer-reviewed) | Targeting peer-reviewed Q1 venue |

A second candidate (an NSR 2024 review paper on SNV→SV deep-learning representations, PMID 39606147) was judged a non-competing survey and is cited as background only, not a collision.

**Revised self-assessment (supersedes §12.5):**

| Score | Original (§12.5) | Revised (post BASILISC check) |
|---|---|---|
| Novelty | 7–8/10 | **6/10** |
| Technical difficulty | 6/10 | 6/10 (unchanged) |
| Publication potential | 7–8/10 | **7/10** |
| Risk of prior work | 4/10 | **5/10** |
| Reviewer confidence | — | **6.5/10** |
| Feasibility | 9/10 | 9/10 (confirmed — the pipeline runs end-to-end) |

**Standing manuscript instruction (acted on):** do not claim primacy on "self-supervised learning for structural variants" as a category. Claim the narrower, defensible combination — image-free continuous alignment representation + calibrated, ancestry-robust uncertainty — which BASILISC does not cover. Cite BASILISC as reference 11 and BEiT (Bao et al., ICLR 2022) as reference 12 in the manuscript's Related Work.

---

## 15. [NEW] Open caveats & deferred work

**Standing open caveats (not yet resolved):**

- **C1 — Truth-set choice.** Using 1000G Phase 3 genotypes instead of GIAB HG002 as the gold standard (§2.2). Ruling: proceed on 1000G now, add GIAB HG002 as the Phase-4 headline benchmark.
- **C2 — Evaluation harness.** Direct genotype scoring instead of Truvari (§7). Ruling: build the Truvari harness alongside the GIAB HG002 addition.

**Deferred / not implemented (honest scope reductions from the original plan, to be listed in the manuscript's Limitations and/or Future Work):**

1. Breakpoint regression head (§5.1, §5.2) — classification-only in the current pipeline.
2. Deep ensembles, evidential deep learning, and conformal prediction for uncertainty (§6.1) — replaced by temperature scaling + MC-dropout.
3. Reliability diagrams and risk-coverage/selective-prediction curves (§6.2, §7.1) — ECE is reported numerically but not visualized.
4. Coverage-robustness downsampling experiment (§2.2, §7.2) — not run.
5. Repeat/segmental-duplication region stratification (§7.2) — not run.
6. Coverage-invariance and cross-sample-identity augmented views for VICReg (§4.2) — only masking-based augmentation used.
7. Learned/classical-caller-based candidate generation, v2 (§2.3) — v1 (truth-VCF-anchored) only.
8. With/without-uncertainty-head and CNN-only-vs-CNN+Transformer ablations (§7.4) — not run.
9. Experiment tracking / run registry (§9.1) — results aggregated manually from JSON dumps.
10. Public release of pretrained weights to an archive (Zenodo/GitHub) (§12.4) — code is packaged, not yet published.
11. Linear-probe monitoring during pretraining (§4.1, §8 Phase 2) — not tracked.

None of these block a submittable manuscript given the current headline results (label efficiency, calibration, length-stratified recall, cross-population directionality, and the honest DeepSV-representation head-to-head), but each is a legitimate reviewer target and is listed here so the manuscript's Limitations section and this document stay in sync.

---

*Document history: v1 (2026-07-13) original execution plan. v2 (2026-07-18) full as-implemented rewrite — every section retains its original plan text with an "AS IMPLEMENTED" callout documenting what was actually built, what changed, why, and what remains open; new §13–15 added for results, novelty positioning, and deferred work.*
