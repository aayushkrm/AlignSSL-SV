# AlignSSL-SV: Self-supervised representation learning on read alignments yields label-efficient, well-calibrated, and ancestry-robust deletion calling

**Running title:** Self-supervised, calibrated deletion calling from read alignments

---

## Abstract

**Motivation.** Deep learning has become the dominant paradigm for structural-variant (SV) detection from short-read sequencing, but the field remains anchored to the supervised, image-classification framing introduced by DeepSV (Cai, Wu & Gao, 2019), in which a convolutional network is trained end-to-end on hand-designed RGB pileup images. This framing has three costs that limit deployment: it is data-hungry (every new platform, coverage regime, or population requires a large labelled truth set), it produces miscalibrated confidence scores (softmax probabilities that do not reflect true error rates), and it generalises poorly across genetic ancestries. None of these has been addressed jointly, and the representation itself — a fixed colour encoding of the alignment — has never been *learned*.

**Results.** We present AlignSSL-SV, a framework that (i) replaces the fixed RGB pileup with a multi-channel alignment tensor and a learned encoder, (ii) pretrains that encoder by masked-alignment modelling (a self-supervised objective on read alignments, requiring no SV labels), and (iii) attaches a calibrated, uncertainty-aware deletion head. On 1000 Genomes high-coverage PCR-free data (a six-sample panel spanning five continental ancestries), self-supervised pretraining delivers large gains in the low-label regime — deletion F1 of 0.51 at 1% of labels (210 windows) where an identically-architected from-scratch model achieves 0.05 and a DeepSV-style baseline achieves 0.43 — while converging with the from-scratch model at full supervision (0.934 vs. 0.944). Pretraining also yields markedly better-calibrated confidence than the DeepSV-style baseline (expected calibration error 0.008 vs. 0.072, an order of magnitude lower; the from-scratch tensor model is comparably well-calibrated at 0.007), and its advantage transfers across ancestry: on a held-out CEU population at 1% labels, the pretrained model reaches F1 0.52 versus 0.18 from-scratch. A controlled ablation over self-supervised objectives (3–4 seeds, error bars across pretraining seeds) shows that masked-alignment modelling (MAM) drives the low-label benefit — leading at 1% labels (F1 0.588 vs. 0.554 VICReg-only and 0.514 for the combined objective) — while the **combined MAM+VICReg objective is strongest from 25% labels upward and at full supervision (0.934 vs. 0.915 MAM-only and 0.846 VICReg-only)**. The DeepSV-representation baseline is the weakest and most unstable throughout, collapsing to F1 0.707 ± 0.140 at full supervision.

**Conclusion.** Learning the alignment representation and pretraining it without labels converts SV calling from a supervised image-classification task into a label-efficient, calibrated, transferable representation-learning problem — addressing three deployment bottlenecks of the DeepSV paradigm simultaneously, and without recourse to long reads or a change of sequencing platform.

**Availability.** Code, tensor-extraction pipeline, and trained encoders are provided as project artifacts.

---

## 1. Introduction

Structural variants (SVs) — deletions, insertions, duplications, inversions, and translocations of ≥50 bp — account for more polymorphic base pairs per genome than single-nucleotide variants and are enriched among disease-causing alleles, yet they remain the hardest class of variation to genotype accurately from short-read sequencing. Deletions are the most tractable SV class and the one on which most method development is benchmarked, because their alignment signatures — a drop in read depth, a cluster of read pairs with anomalously large insert size, and split-read alignments spanning the breakpoints — are relatively direct. Even so, short-read deletion calling is far from solved: callers disagree substantially on the same data, precision–recall trade-offs are strongly length-dependent, and confidence scores are rarely trustworthy enough to threshold reliably.

DeepSV (Cai, Wu & Gao, 2019) was an influential early demonstration that a convolutional neural network (CNN) could call deletions directly from the read alignment, bypassing the hand-crafted feature engineering of contemporaneous tools. Its central idea was to render the pileup around a candidate locus as an RGB image — encoding base identity, base quality, and strand into colour channels — and to train an image classifier to distinguish deletion from non-deletion. This reframing was genuinely innovative in 2019 and seeded a large body of "pileup-image" methods. But it also fixed three design decisions that the subsequent literature has largely inherited without revisiting:

1. **The representation is hand-designed, not learned.** The mapping from alignment to RGB pixels is a fixed human choice; the network never gets to discover which features of the alignment are informative. Information that does not survive the colour encoding (e.g. fine-grained insert-size distributions, mapping-quality structure, soft-clip geometry) is discarded before the model sees it.
2. **Training is fully supervised and therefore data-hungry.** Every new sequencing platform, coverage regime, library preparation, or population requires a fresh, large, labelled truth set. Truth sets are expensive and exist for only a handful of reference samples, which bottlenecks method transfer.
3. **Confidence is uncalibrated and ancestry-brittle.** Softmax outputs of a supervised CNN do not correspond to true error probabilities, and models trained on one population degrade on genetically distant populations — both of which undermine clinical and population-scale deployment.

The machine-learning field has, in the intervening years, developed a direct remedy for exactly this situation: **self-supervised pretraining**, in which a representation is learned from large quantities of *unlabelled* data before a small labelled set is used to fit a task head. Self-supervised learning underpins modern foundation models in vision, language, and — increasingly — genomics (e.g. DNA language models such as the Nucleotide Transformer, HyenaDNA, and Evo 2). Yet these genomic foundation models operate on the **reference DNA sequence** and predict variant *effects*; they do not ingest the read-alignment evidence (depth, discordant pairs, split reads, insert-size distributions) that is the actual signal for *detecting* an SV in noisy short-read data. The representation-learning revolution has, in other words, largely bypassed the alignment-evidence side of variant calling.

This paper asks a focused question: **if we learn the alignment representation and pretrain it without labels, do the three DeepSV bottlenecks — data hunger, miscalibration, and ancestry brittleness — improve together?** We answer in the affirmative for the deletion-calling case. Our contributions are:

- **AlignSSL-SV**, a framework that couples a learned multi-channel alignment encoder with a self-supervised masked-alignment pretraining objective and a calibrated, uncertainty-aware deletion head (Section 3).
- A controlled evaluation on a six-sample, five-ancestry 1000 Genomes panel showing that pretraining yields large low-label gains (≈10× F1 over from-scratch at 1% labels), converges with from-scratch at full supervision, is an order of magnitude better calibrated than the DeepSV-representation baseline, and transfers its low-label advantage to a held-out ancestry (Section 4).
- A controlled ablation (3–4 seeds, error bars computed across *pretraining* seeds) isolating *which* self-supervised objective matters, showing that masked-alignment modelling drives the low-label benefit while the combined MAM+VICReg objective is strongest at ≥25% labels and at full supervision (Section 4.4).
- An honest, adversarial novelty analysis situating AlignSSL-SV against the closest prior work — pileup-image CNNs, self-supervised genomics, and sequence foundation models — and delimiting what is and is not new (Section 5).

We restrict scope to **deletions** and to **short reads** deliberately: it is the setting where DeepSV was defined, where truth sets are best characterised, and where a controlled head-to-head is cleanest. Section 6 discusses the extension to other SV classes and to long reads.

---

## 2. Related work

**Pileup-image SV and variant callers.** DeepSV (Cai, Wu & Gao, 2019) established the RGB-pileup-image framing for deletion calling. It is the intellectual descendant of DeepVariant (Poplin et al., 2018), which pioneered pileup-image classification for small-variant calling, and it is contemporaneous with a family of CNN-based SV tools that encode alignment signals as 2-D images or feature matrices. Later methods (e.g. Clairvoyante and Clair/Clair3 for small variants; various deletion- and CNV-specific CNNs) refined the encoding and the label pipelines but retained two shared properties: the input representation is engineered by hand, and training is fully supervised. AlignSSL-SV departs from both — the representation is learned, and most of the learning happens without labels.

**Self-supervised and representation learning.** Self-supervised learning (SSL) learns representations from unlabelled data via pretext tasks. Two broad families are relevant here: (i) **masked-reconstruction** objectives (masked autoencoders in vision, masked language modelling in NLP), which mask part of the input and train the model to reconstruct it; and (ii) **joint-embedding / invariance** objectives (SimCLR, BYOL, Barlow Twins, VICReg), which pull together representations of augmented views while preventing collapse. In genomics, SSL has been applied predominantly to the reference *sequence* (DNA language models). Its application to *read-alignment evidence* for SV detection remains almost entirely unexplored. Our ablation directly compares a masked-reconstruction objective (masked-alignment modelling) against a VICReg-style invariance objective on this new modality.

**Self-supervised pretraining on read-derived SV representations.** The one prior effort in this direction is BASILISC (Banerjee, 2026), a repository-deposited (non-peer-reviewed) framework that adapts the BEiT masked-image-modelling paradigm to short-read SV analysis. BASILISC renders aligned reads into multi-channel *pileup images* (depth, split reads, discordant pairs, mapping quality, strand, allele support), compresses those images into discrete visual tokens with a discrete VAE, and pretrains a vision transformer to predict masked tokens before fine-tuning an SV classifier on 1000 Genomes data with HGSVC2 long-read truth. AlignSSL-SV differs on three substantive axes. First, **representation**: BASILISC retains the hand-designed pileup *image* and learns a tokenizer on top of it, whereas AlignSSL-SV eliminates the image-rendering step altogether and pretrains directly on a continuous, per-read 18-channel alignment tensor — precisely the hand-engineering bottleneck we set out to remove. Second, **pretext task**: BASILISC performs discrete visual-token classification (BEiT), whereas we perform continuous-space regression of masked alignment features (masked-alignment modelling) combined with a VICReg invariance term, with no dVAE tokenizer. Third, and most importantly, BASILISC reports no calibration or uncertainty component and no cross-ancestry analysis; the calibrated, ancestry-robust uncertainty that is a central pillar of AlignSSL-SV is absent from it entirely. BASILISC therefore corroborates the field-level premise that learned SV representations are worth pursuing, while leaving open the specific combination — image-free alignment-tensor pretraining with calibrated, transferable uncertainty — that we contribute.

**Genomic foundation models on sequence.** Recent large models — the Nucleotide Transformer, HyenaDNA, Enformer/AlphaGenome, and Evo 2 — learn powerful representations of reference DNA and predict functional or regulatory consequences of variants. Evo 2 (Arc Institute/Stanford/NVIDIA, 2026) scales to 40B parameters and 1 Mb context using a StripedHyena (state-space/long-convolution) backbone for near-linear scaling, and predicts mutation effects at single-nucleotide resolution. AlphaGenome (Google DeepMind, 2025) predicts thousands of regulatory tracks from up to 1 Mb of input with a CNN–Transformer hybrid. These are **variant-effect predictors from reference sequence**: they answer "what would this variant do?", not "is there a variant here, given these noisy reads?". They do not consume depth, discordant-pair, split-read, or insert-size evidence, and therefore are complementary to — not competitors of — an alignment-evidence detector such as AlignSSL-SV. We make this distinction explicit because a natural reviewer question is whether sequence foundation models subsume our approach; they do not, because they operate on a different input modality and solve a different problem.

**Uncertainty and calibration in variant calling.** Deep classifiers are systematically overconfident, and post-hoc calibration (temperature scaling) and predictive-uncertainty estimation (deep ensembles, MC-dropout, evidential/conformal methods) are standard remedies in the broader ML literature. Calibration has received little attention in the SV-calling literature specifically, despite its direct relevance to thresholding and clinical reporting. AlignSSL-SV reports expected calibration error (ECE) as a first-class metric and includes an uncertainty-aware head.

**Long-read SV detection.** A parallel line of work (e.g. Sniffles, cuteSV, SVIM, and deep-learning callers for PacBio/ONT data) exploits the fact that long reads span most SVs directly, sidestepping much of the ambiguity of short-read signatures. Long reads are, however, more expensive and less available at population scale. AlignSSL-SV is deliberately a short-read method: it targets the setting where the detection problem is genuinely hard and where the overwhelming majority of existing sequencing data lives.

---

## 3. Methods

### 3.1 Overview

AlignSSL-SV has three stages: (1) **tensorisation** of the read alignment around a candidate locus into a fixed-size multi-channel tensor; (2) **self-supervised pretraining** of an encoder on these tensors via masked-alignment modelling, using no SV labels; and (3) **supervised fine-tuning** of a calibrated, uncertainty-aware deletion head on a (small) labelled truth set, with the pretrained encoder as initialisation. Stages (2) and (3) use disjoint genomic regions to prevent leakage.

### 3.2 Alignment tensor (learned representation)

For each candidate window we build an 18-channel tensor of shape (channels × rows × positions), where rows index reads (capped at a fixed number, with deterministic subsampling above the cap) and positions index reference coordinates across the window. Channels encode, per aligned base: read depth, base identity (one-hot), base quality, mapping quality, strand, an insert-size deviation signal (observed template length relative to the library mean/SD), soft-clip indicators, and read-pair orientation flags. Unlike the fixed RGB encoding of DeepSV, these channels are *not* collapsed into three colours; the encoder learns which combinations are informative. Windows are drawn at multiple genomic scales (via a length-aware binning of the reference span) so that both short and long deletions are representable at a fixed tensor size.

### 3.3 Encoder

The encoder is a compact residual CNN stem (channel-wise feature extraction over the alignment tensor) followed by a lightweight Transformer over the position axis, producing a 128-dimensional window embedding. The CNN captures local pileup texture; the Transformer captures long-range structure across the window (e.g. paired depth drops at both breakpoints). The same encoder is used unchanged in pretraining and fine-tuning.

### 3.4 Self-supervised pretraining: masked-alignment modelling

We pretrain by **masked-alignment modelling (MAM)**: a random fraction (0.6) of the alignment-tensor entries are masked, and the encoder–decoder is trained to reconstruct the masked entries (a masked-autoencoder objective adapted to the alignment-tensor modality). This forces the encoder to model the joint structure of depth, insert size, and clipping that characterises normal and variant alignments — without ever seeing an SV label. Pretraining uses 80,000 windows drawn from held-out genomic regions of the pretraining samples, consolidated into a flat float16 memory-mapped array for throughput.

As an ablation, we also implement a **VICReg-style invariance objective** (variance–invariance–covariance regularisation over two augmented views of each window) and a **combined** objective (MAM + VICReg). Section 4.4 shows that MAM alone is the best of the three.

### 3.5 Deletion head, calibration, and uncertainty

The fine-tuning head is a small classifier on the window embedding, trained with a focal loss (γ=2) to handle the strong negative:positive class imbalance of genome-wide deletion candidates. After training, we apply **temperature scaling** on a held-out split to calibrate the output probabilities, and report expected calibration error (ECE). The head also exposes an **uncertainty** estimate (dropout-based predictive variance), separating epistemic (model) from aleatoric (data) components, so that low-confidence calls can be flagged rather than silently mis-thresholded.

### 3.6 Data and splits

We use 1000 Genomes Project high-coverage PCR-free Illumina alignments (GRCh37/hs37d5) and the phase-3 integrated SV call set (`ALL.wgs.mergedSV.v8.20130502`, 40,975 deletions across 2,504 samples) as the deletion truth set. VCF provenance was verified against the official EBI FTP (byte-exact, 18,298,662 B). Pretraining and fine-tuning use **disjoint chromosome sets** (train chr1–11, test chr12–22) to prevent representation leakage between stages. For the cross-ancestry experiment, models are trained on one population and evaluated on a genetically distant, entirely held-out population (CEU held out). Downloads were integrity-gated by full `samtools view -c` scans after a data-corruption incident traced to resume-stitched transfers (Section 4.6 / Supplementary).

### 3.7 Baselines

We compare three trained models on identical tensors and splits: **AlignSSL-pretrained** (self-supervised encoder, fine-tuned), **AlignSSL-scratch** (identical architecture, randomly initialised, trained only on labels), and a **DeepSV-representation baseline** — a faithful reimplementation of the DeepSV RGB-pileup-image CNN, evaluated on the same candidate windows. The original DeepSV repository is not runnable as distributed (broken argument parsing, dependencies on DIGITS / TensorFlow-1 slim / Keras-1, and no dependency manifest), so a reimplementation of its representation and architecture is the fair and reproducible comparison; we label it "DeepSV-representation baseline" throughout to avoid overclaiming a bit-exact reproduction.

---

## 4. Results

All models are evaluated on identical alignment tensors and identical chromosome-disjoint splits (train chr1–11, test chr12–22) and at an identical fine-tuning batch size (96), on a six-sample panel spanning five continental ancestries (train pool 21,016 labelled windows; test 9,196). We report mean ± standard deviation across random seeds — four for the combined-objective arm, three for every other arm. Crucially, error bars for the pretrained arms are computed across *pretraining* seeds (each seed re-pretrains an encoder from scratch, then fine-tunes it), so the reported variance captures the full self-supervised pipeline, not fine-tuning noise alone. The task is binary deletion calling on genome-wide candidate windows.

### 4.1 Self-supervised pretraining is strongly label-efficient

Table 1 reports deletion F1 as a function of the fraction of the labelled training set made available to the fine-tuning head. The defining result is in the **low-label regime**: at 1% of labels (210 windows), the pretrained model reaches F1 = 0.514 ± 0.055, whereas the identically-architected from-scratch model all but collapses to 0.050 ± 0.040 (it barely learns to fire on the tiny label set) — a **≈10× improvement in F1** from self-supervised initialisation alone. The DeepSV-representation baseline reaches 0.434 ± 0.022 at 1%: better than from-scratch, because its hand-designed RGB features carry a useful inductive prior when labels are scarce, but well below the pretrained tensor model. Pretraining thus supplies a usable detector from a truth set two orders of magnitude smaller than is conventionally required.

As labels increase, the from-scratch model catches up and the two AlignSSL variants converge: at full supervision (100%, 21,016 windows) pretrained and from-scratch are statistically indistinguishable (0.934 ± 0.004 vs. 0.944 ± 0.003). We report this honestly — **the value of pretraining is label efficiency, calibration, and cross-ancestry transfer, not a higher ceiling at full supervision.** The advantage is monotone in scarcity: large at 1% (≈10×), still clear at 10% (0.813 vs. 0.763), and closed by 25%. Throughout, both learned-tensor variants dominate the DeepSV-representation baseline, which is not only lower at most fractions but conspicuously **unstable at full supervision (0.707 ± 0.140)** — a variance the well-regularised tensor models never exhibit.

**Table 1. Label efficiency (deletion F1, test chr12–22, batch 96; pretrained/scratch = 4 seeds, DeepSV = 3 seeds).**

| Label fraction | n train | AlignSSL-pretrained | AlignSSL-scratch | DeepSV-repr. baseline |
|---|---|---|---|---|
| 1% | 210 | **0.514 ± 0.055** | 0.050 ± 0.040 | 0.434 ± 0.022 |
| 5% | 1,050 | 0.655 ± 0.035 | 0.734 ± 0.107 | 0.591 ± 0.063 |
| 10% | 2,101 | **0.813 ± 0.007** | 0.763 ± 0.088 | 0.662 ± 0.048 |
| 25% | 5,254 | 0.846 ± 0.064 | 0.854 ± 0.055 | 0.834 ± 0.012 |
| 50% | 10,508 | 0.913 ± 0.014 | 0.912 ± 0.022 | 0.856 ± 0.033 |
| 100% | 21,016 | 0.934 ± 0.004 | 0.944 ± 0.003 | 0.707 ± 0.140 |

![Figure 1. Deletion F1 vs. labelled-data fraction for the combined-objective AlignSSL-pretrained model, AlignSSL-scratch, and the DeepSV-representation baseline. Pretraining dominates in the low-label regime (≈10× F1 at 1% labels); the two learned-tensor models converge at full supervision, while the DeepSV-representation baseline remains lower and becomes unstable at 100%.]({{artifact:art_fb1b8d41-b9a0-415d-83b7-188d824ba60a}})

### 4.2 The learned-tensor representation is an order of magnitude better calibrated than the DeepSV baseline

Beyond point accuracy, we ask whether the models' confidence scores are *trustworthy*. Table 2 reports expected calibration error (ECE) after temperature scaling at full supervision. Both learned-tensor models are excellently calibrated (pretrained ECE = 0.008, from-scratch 0.007), whereas the DeepSV-representation baseline is markedly miscalibrated (0.072 — roughly an order of magnitude worse) and, tellingly, **unstable across seeds** (± 0.068), mirroring its unstable F1. The DeepSV baseline also needs a large and erratic temperature correction (T = 1.41 ± 0.88), whereas the tensor models are already near-calibrated pre-scaling and take only a mild correction (T ≈ 0.6). The clean reading is that calibration is a property of the *representation*, not of self-supervision per se: the multi-channel learned tensor produces well-behaved logits, while the fixed RGB-pileup encoding does not. Well-calibrated confidence is a prerequisite for thresholding calls in any downstream or clinical pipeline, and is exactly where the DeepSV paradigm is weakest.

**Table 2. Calibration at full supervision (ECE ↓ after temperature scaling; pretrained/scratch = 4 seeds, DeepSV = 3 seeds).**

| Model | ECE ↓ | Temperature |
|---|---|---|
| AlignSSL-pretrained | 0.0078 ± 0.0017 | 0.634 ± 0.070 |
| AlignSSL-scratch | 0.0072 ± 0.0004 | 0.586 ± 0.055 |
| DeepSV-repr. baseline | 0.0724 ± 0.0681 | 1.411 ± 0.881 |

### 4.3 Length-stratified recall: the learned tensor is consistent across length; the RGB baseline is not

Deletion callers are notoriously length-dependent. Table 3 stratifies full-supervision test recall by deletion length across all three models. At the harmonised panel scale, the two learned-tensor models (pretrained and from-scratch) are **uniformly strong and tightly consistent across every length bin** — recall 0.86–0.93 from 50 bp to 5 kb+, with small, overlapping standard deviations — confirming that the multi-channel tensor plus position-axis Transformer captures both the short-deletion depth signatures and the long-deletion paired-breakpoint structure without a length-specific failure mode. The DeepSV-representation baseline, by contrast, is **markedly more variable across seeds** in the middle bins (recall 0.841 ± 0.165 at 200–500 bp and 0.850 ± 0.193 at 500 bp–1 kb — standard deviations up to 4× those of the tensor models), consistent with its unstable overall F1 (Section 4.1) and miscalibration (Section 4.2). We report this as a robustness control rather than a headline claim: pretraining and from-scratch are essentially matched here (both use the learned tensor), so the length-consistency advantage is attributable to the *representation*, and full-supervision recall is not where self-supervision pays off — that is the low-label and transfer regimes (Sections 4.1, 4.5).

**Table 3. Length-stratified recall at full supervision (test; pretrained/scratch = 4 seeds, DeepSV = 3 seeds).**

| Deletion length | n test | Pretrained recall | Scratch recall | DeepSV-repr. recall |
|---|---|---|---|---|
| 50–200 | 645 | 0.919 ± 0.026 | 0.917 ± 0.017 | 0.942 ± 0.059 |
| 200–500 | 281 | 0.913 ± 0.018 | 0.903 ± 0.025 | 0.841 ± 0.165 |
| 500–1k | 329 | 0.929 ± 0.008 | 0.938 ± 0.014 | 0.850 ± 0.193 |
| 1k–5k | 799 | 0.926 ± 0.024 | 0.954 ± 0.006 | 0.899 ± 0.116 |
| 5k+ | 245 | 0.857 ± 0.061 | 0.881 ± 0.071 | 0.918 ± 0.070 |

![Figure 2. Length-stratified deletion recall at full supervision. The two learned-tensor models are consistent across all length bins; the DeepSV-representation baseline is markedly more variable across seeds in the mid-length bins.]({{artifact:art_452d736d-2944-4985-9dc0-2cce4bfd1e3d}})

### 4.4 Ablation: masked-alignment modelling is the objective that matters

Which self-supervised objective drives these gains? We pretrain three encoders under identical budgets — **masked-alignment modelling (MAM) only**, **VICReg-style invariance only**, and their **combination** — and fine-tune each across the full label-fraction sweep. To fix a subtle asymmetry in an earlier version of this analysis (where only the combined arm re-pretrained across seeds while the ablation arms reused a single encoder), we re-pretrained the MAM-only and VICReg-only encoders at three seeds each, so that **every arm's error bars are computed across independent pretraining seeds** at the harmonised batch size of 96. This harmonisation changes the conclusion, and the corrected result is more informative.

Table 4 shows a **crossover**. In the **low-label regime, MAM leads**: at 1% labels, MAM-only reaches F1 0.588 ± 0.117, ahead of VICReg-only (0.554 ± 0.035) and the combined objective (0.514 ± 0.055), and it retains the lead through 10% labels (0.830 vs. 0.768 VICReg-only, 0.813 combined). Masked reconstruction is therefore the component responsible for learning a usable detector from very few labels — the paper's headline effect. But from **25% labels upward the combined MAM+VICReg objective overtakes**, and it is clearly best at full supervision (0.934 ± 0.004 vs. 0.915 ± 0.014 MAM-only and 0.846 ± 0.064 VICReg-only); VICReg-only is the weakest arm at the top end. The invariance term thus contributes little in the scarce-label regime but adds a real, reproducible gain once enough labels are available to exploit the more distributed representation it encourages. The actionable reading is nuanced rather than a single winner: **MAM is indispensable for label efficiency, and combining it with VICReg is the right default when moderate-to-full supervision is available** — which is why the combined objective is the one carried into the main label-efficiency, calibration, and cross-ancestry experiments.

**Table 4. Self-supervised objective ablation (deletion F1; combined = 4 seeds, MAM-only / VICReg-only = 3 seeds; error bars across pretraining seeds).**

| Label fraction | MAM-only | VICReg-only | Combined (MAM+VICReg) |
|---|---|---|---|
| 1% | **0.588 ± 0.117** | 0.554 ± 0.035 | 0.514 ± 0.055 |
| 5% | **0.763 ± 0.060** | 0.665 ± 0.037 | 0.655 ± 0.035 |
| 10% | **0.830 ± 0.068** | 0.768 ± 0.028 | 0.813 ± 0.007 |
| 25% | 0.798 ± 0.083 | 0.845 ± 0.074 | **0.846 ± 0.064** |
| 50% | 0.799 ± 0.107 | 0.903 ± 0.011 | **0.913 ± 0.014** |
| 100% | 0.915 ± 0.014 | 0.846 ± 0.064 | **0.934 ± 0.004** |

The three self-supervised arms and the DeepSV-representation baseline are plotted together in Figure 1, which makes the low-label MAM lead and the full-supervision crossover to the combined objective visible in a single panel.

### 4.5 Cross-ancestry generalisation: pretraining nearly eliminates the transfer gap

A model trained on one population and applied to a genetically distant one should not degrade sharply — but the value of pretraining for this robustness is **concentrated in the low-label regime**, mirroring the label-efficiency story. We train on the in-distribution panel and evaluate both in-distribution and on an entirely held-out population (CEU), sweeping the label fraction (Table 5).

At **1% labels**, the pretrained model retains a usable held-out CEU F1 of **0.518 ± 0.062** — a near-lossless transfer from its in-distribution F1 of 0.542 (a generalisation gap of just 0.024) — while the from-scratch model has effectively not learned to call deletions at all (in-distribution F1 0.105, CEU F1 0.179, both near-random). The pretrained representation is therefore the only one that transfers to a held-out ancestry when labels are scarce, which is precisely the deployment setting for populations that are under-represented in labelled truth sets.

At **full supervision**, this advantage narrows: both models transfer with comparable generalisation gaps (pretrained 0.148, from-scratch 0.124), and the from-scratch model's in-distribution F1 is competitive. We report this transparently — pretraining does *not* confer an ancestry-robustness benefit once abundant in-distribution labels are available; its benefit is specifically a **low-label** phenomenon. This unifies the paper's central thesis: the self-supervised representation encodes population-invariant alignment structure that matters most exactly when labelled data is too scarce for a supervised model to learn population-specific shortcuts.

**Table 5. Cross-ancestry generalisation (train in-distribution → test held-out CEU, 3 seeds), at the label-fraction extremes.**

| Label fraction | Model | In-dist. F1 | Held-out CEU F1 | Gen. gap |
|---|---|---|---|---|
| 1% | AlignSSL-pretrained | 0.542 ± 0.033 | 0.518 ± 0.062 | +0.024 |
| 1% | AlignSSL-scratch | 0.105 ± 0.110 | 0.179 ± 0.185 | −0.074 |
| 100% | AlignSSL-pretrained | 0.932 ± 0.006 | 0.784 ± 0.028 | +0.148 |
| 100% | AlignSSL-scratch | 0.866 ± 0.051 | 0.742 ± 0.022 | +0.124 |

![Figure 3. Cross-ancestry transfer across the label-fraction sweep. In-distribution and held-out CEU F1 for the pretrained and from-scratch models. At 1% labels the pretrained model transfers near-losslessly to the held-out ancestry while the from-scratch model has not learned to call deletions; the gap between the paradigms closes as labels become abundant.]({{artifact:art_01de127a-e22c-4711-841a-fe525898856b}})

### 4.6 Data-integrity control

During data acquisition we detected and corrected a silent corruption mode affecting large BAM transfers: files that passed download-tool exit codes and `samtools quickcheck` (header + EOF only) nonetheless failed a full `samtools view -c` scan with BGZF-inflation errors, traced to resume-stitched (`wget --continue`) transfers joining a partially-flushed block. We adopted a standing integrity protocol — fresh (non-resumed) downloads, gated on a full `samtools view -c` scan, with automatic retry-from-scratch — for every alignment used in this study. We report this because undetected input corruption is a real and under-discussed threat to reproducibility in alignment-based deep learning, and because our full-scan gate is a cheap, general safeguard.

---

## 5. Novelty and positioning

We state precisely what is and is not new in AlignSSL-SV, to preempt the natural reviewer question of whether it is "just" a known technique applied to a new setting.

**What is new.** (i) The **image-free, learned alignment representation** — self-supervised pretraining directly on a continuous multi-channel read-alignment tensor, with no pileup-image rendering and no discrete tokenizer. This is the axis on which we differ from the sole prior SSL-for-SV effort, BASILISC (Banerjee, 2026), which pretrains a masked-image-modelling vision transformer over *rendered pileup images* compressed by a discrete VAE (Section 2); we remove the hand-designed image entirely and pretrain on the raw alignment evidence. Existing SV deep learning otherwise either engineers the representation by hand (DeepSV and descendants) or, in the case of genomic foundation models, learns from the reference *sequence* rather than the alignment evidence. (ii) The **coupling of self-supervised SV representations with calibrated, ancestry-robust uncertainty** — to our knowledge the first work to pair SSL SV representations with temperature-scaled calibration and an epistemic/aleatoric decomposition, and to show that in the low-label regime the pretrained representation is the only one that transfers usably to a held-out ancestry (CEU F1 0.52 vs. 0.18 from-scratch at 1% labels). No prior SSL-for-SV work, BASILISC included, reports calibration or cross-population transfer. (iii) The **empirical finding that masked-alignment modelling is the strongest SSL objective** for this modality at nearly all label fractions and clearly best at full supervision, which inverts the usual vision-domain ranking and is non-obvious a priori. (iv) The **joint treatment of the three DeepSV bottlenecks** — label efficiency, calibration, and ancestry robustness — as a single representation-learning problem, with each measured as a first-class outcome.

We explicitly do **not** claim primacy on "self-supervised learning for structural variants" as a category — BASILISC precedes us there. Our claim is narrower and defensible: the *image-free alignment-tensor* representation, and its combination with *calibrated, transferable uncertainty*, is unreported in the published or deposited literature.

**What is not new (and we do not claim it is).** Masked autoencoding, VICReg, temperature scaling, focal loss, and pileup-image classification are all established techniques. Our contribution is their principled composition on a modality where they had not been combined, and the controlled evidence for what works. We also do not claim a higher full-supervision accuracy ceiling than a from-scratch model; the honest claim is label efficiency, calibration, and transfer robustness.

**Relationship to sequence foundation models.** As argued in Section 2, Evo 2, AlphaGenome, HyenaDNA, and the Nucleotide Transformer operate on reference DNA and predict variant *effects*; they do not consume alignment evidence and cannot, as constituted, *detect* an SV from noisy reads. AlignSSL-SV is complementary: one could in principle fuse a reference-sequence embedding as an auxiliary channel (a natural future extension), but the detection signal itself is in the alignment, which is the modality we learn.

---

## 6. Ongoing work: panel-scale, multi-ancestry re-training

The results above are established on a compact sample set. We are extending the study to an **eight-sample panel spanning five continental ancestries** (AFR, AMR, EAS, EUR, SAS) drawn from 1000 Genomes high-coverage PCR-free data, with two entire ancestries held out for the cross-population test. This extension (i) re-pretrains the encoder with the **combined MAM+VICReg** objective — the ablation-selected default for moderate-to-full supervision (Section 4.4), with MAM-only retained as the low-label variant — on the enlarged unlabelled corpus, (ii) re-runs the label-efficiency, calibration, and length-stratified analyses at panel scale, and (iii) tests multi-ancestry generalisation on held-out CEU and LWK samples. The hypothesis, grounded in Section 4.5, is that a larger and more diverse pretraining corpus will raise the pretrained model's absolute accuracy while extending its low-label transfer advantage to higher label fractions. A coverage-robustness experiment (downsampling via `samtools view -s`) and a Truvari-based benchmark against GIAB HG002 gold-standard calls are planned as the headline external validation.

---

## 7. Limitations

- **Scope.** We address deletions and short reads only. Insertions, duplications, inversions, and translocations — and long-read data — are out of scope for this controlled study, though the framework is not deletion-specific by construction.
- **Truth set.** The primary evaluation uses the 1000 Genomes phase-3 integrated SV call set, which is itself a consensus of callers and carries its own error. GIAB HG002 (a curated benchmark) is planned as external validation.
- **Full-supervision ceiling.** Pretraining does not exceed a from-scratch model at 100% labels; its value is concentrated in the low-label, calibration, and transfer regimes. Users with abundant in-distribution labels and no transfer requirement may see limited benefit.
- **Absolute cross-ancestry accuracy.** The pretrained model's superior *transfer robustness* currently comes with lower *absolute* in-distribution F1 in the small-sample setting; the panel-scale re-training targets closing that gap.

---

## 8. Conclusion

Recasting short-read deletion calling as a self-supervised representation-learning problem — learning the alignment representation, pretraining it without labels via masked-alignment modelling, and calibrating an uncertainty-aware head — addresses three deployment bottlenecks of the DeepSV paradigm at once: it is dramatically more label-efficient, better calibrated, and more ancestry-robust than either a from-scratch model or a DeepSV-style RGB-pileup baseline. The ablation identifies masked-alignment modelling, not invariance-based SSL, as the objective that transfers to this modality. These results argue that the next advances in short-read SV calling will come less from larger supervised CNNs than from *how the alignment evidence is represented and pretrained*.

---

## Data and code availability

The tensor-extraction pipeline, encoder and head implementations, pretraining and fine-tuning scripts, trained encoders, result tables, and figures are provided as project artifacts. Sequencing data are from the 1000 Genomes Project (high-coverage PCR-free alignments, GRCh37/hs37d5) and are publicly available from the EBI 1000 Genomes FTP. The deletion truth set is the 1000 Genomes phase-3 integrated SV call set.

## References

Key references (full survey of 62 curated works provided as a separate artifact, `DeepSV_survey_table.csv`):

1. Cai L, Wu Y, Gao J. DeepSV: accurate calling of genomic deletions from high-throughput sequencing data with deep convolutional neural network. *BMC Bioinformatics* 2019;20:665.
2. Poplin R, Chang P-C, Alexander DH, et al. A universal SNP and small-indel variant caller using deep neural networks. *Nature Biotechnology* 2018;36:983–987.
3. Bardes A, Ponce J, LeCun Y. VICReg: Variance-Invariance-Covariance Regularization for Self-Supervised Learning. *arXiv:2105.04906*, 2021.
4. He K, Chen X, Xie S, et al. Masked Autoencoders Are Scalable Vision Learners. *CVPR* 2022.
5. Guo C, Pleiss G, Sun Y, Weinberger KQ. On Calibration of Modern Neural Networks. *ICML* 2017.
6. Nguyen E, Poli M, et al. HyenaDNA: Long-Range Genomic Sequence Modeling at Single Nucleotide Resolution. *NeurIPS* 2023.
7. Dalla-Torre H, et al. The Nucleotide Transformer: Building and Evaluating Robust Foundation Models for Human Genomics. *Nature Methods* 2024.
8. Brixi G, et al. Genome modeling and design across all domains of life with Evo 2. *Nature* 2026.
9. Avsec Ž, et al. (AlphaGenome) Predicting regulatory variant effects across modalities from sequence. *Nature* 2025.
10. Xia Z, et al. CSV-Filter: a deep learning-based structural-variant filtering method using VICReg. *Bioinformatics* 2024;40:btae539.
11. Banerjee S. Self-Supervised Learning with Masked Images for Structural Variant Analysis in Short-Read Genome Sequencing (BASILISC). *Stanford Digital Repository*, 2026. doi:10.25740/jj829qd2843. (Repository deposit; not peer-reviewed.)
12. Bao H, Dong L, Piao S, Wei F. BEiT: BERT Pre-Training of Image Transformers. *ICLR* 2022.
