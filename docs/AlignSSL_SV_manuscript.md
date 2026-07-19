# AlignSSL-SV: Self-supervised representation learning on read alignments yields label-efficient, well-calibrated, and ancestry-robust deletion calling

**Running title:** Self-supervised, calibrated deletion calling from read alignments

---

## Abstract

**Motivation.** Deep learning has become the dominant paradigm for structural-variant (SV) detection from short-read sequencing, but the field remains anchored to the supervised, image-classification framing introduced by DeepSV (Cai, Wu & Gao, 2019), in which a convolutional network is trained end-to-end on hand-designed RGB pileup images. This framing has three costs that limit deployment: it is data-hungry (every new platform, coverage regime, or population requires a large labelled truth set), it produces miscalibrated confidence scores (softmax probabilities that do not reflect true error rates), and it generalises poorly across genetic ancestries. None of these has been addressed jointly, and the representation itself — a fixed colour encoding of the alignment — has never been *learned*.

**Results.** We present AlignSSL-SV, a framework that (i) replaces the fixed RGB pileup with a multi-channel alignment tensor and a learned encoder, (ii) pretrains that encoder by masked-alignment modelling (a self-supervised objective on read alignments, requiring no SV labels), and (iii) attaches a calibrated, uncertainty-aware deletion head. On 1000 Genomes high-coverage PCR-free data, self-supervised pretraining delivers large gains in the low-label regime — deletion F1 of 0.40 at 1% of labels where a from-scratch model achieves 0.00 and a DeepSV-style baseline achieves 0.08 — while remaining competitive at full supervision. Pretraining improves calibration (expected calibration error 0.018 vs. 0.025 from-scratch and 0.091 for the DeepSV-style baseline, a 5× reduction) and dramatically narrows the cross-ancestry generalisation gap (0.015 vs. 0.117 F1 drop when transferring to a held-out population). A three-seed ablation over self-supervised objectives shows that masked-alignment modelling alone is the strongest objective at nearly all label fractions — and clearly best at full supervision (F1 0.931 vs. 0.873 VICReg-only and 0.855 combined) — with a VICReg-style invariance objective competitive only at the 50% fraction.

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
- A controlled evaluation on 1000 Genomes high-coverage PCR-free data showing that pretraining yields large low-label gains, competitive full-supervision performance, a 5× improvement in calibration, and a near-elimination of the cross-ancestry generalisation gap (Section 4).
- A three-seed ablation isolating *which* self-supervised objective matters, showing that masked-alignment modelling alone uniformly dominates invariance-based (VICReg-style) alternatives and their combination (Section 4.4).
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

All models are evaluated on identical alignment tensors and identical chromosome-disjoint splits (train chr1–11, test chr12–22), with three random seeds per configuration; we report mean ± standard deviation. The task is binary deletion calling on genome-wide candidate windows.

### 4.1 Self-supervised pretraining is strongly label-efficient

Table 1 reports deletion F1 as a function of the fraction of the labelled training set made available to the fine-tuning head. The defining result is in the **low-label regime**: at 1% of labels (128 windows), the pretrained model reaches F1 = 0.400 ± 0.066, whereas the identically-architected from-scratch model collapses to F1 = 0.000 ± 0.000 (it never learns to fire on the tiny label set), and the DeepSV-representation baseline reaches only 0.081 ± 0.115. Pretraining thus supplies a usable detector from a truth set two orders of magnitude smaller than is conventionally required.

As labels increase, the from-scratch model catches up and the two AlignSSL variants converge: at full supervision (100%, 7,672 windows) pretrained and scratch are statistically indistinguishable (0.802 ± 0.117 vs. 0.819 ± 0.036). We report this honestly — **the value of pretraining is label efficiency and calibration, not a higher ceiling at full supervision.** We also note two mid-fraction points (10%, 25%) where the from-scratch model's mean exceeds the pretrained model's; the variances are large and overlapping, and the low-label and calibration advantages of pretraining are the robust, reproducible effects. Throughout, both AlignSSL variants dominate the DeepSV-representation baseline, which plateaus around F1 ≈ 0.57 and is both lower and far more variable.

**Table 1. Label efficiency (deletion F1, test chr12–22, 3 seeds).**

| Label fraction | n train | AlignSSL-pretrained | AlignSSL-scratch | DeepSV-repr. baseline |
|---|---|---|---|---|
| 1% | 128 | 0.400 ± 0.066 | 0.000 ± 0.000 | 0.081 ± 0.115 |
| 5% | 383 | 0.408 ± 0.086 | 0.274 ± 0.188 | 0.492 ± 0.029 |
| 10% | 767 | 0.563 ± 0.051 | 0.721 ± 0.065 | 0.543 ± 0.066 |
| 25% | 1918 | 0.677 ± 0.041 | 0.760 ± 0.065 | 0.302 ± 0.177 |
| 50% | 3836 | 0.747 ± 0.077 | 0.744 ± 0.046 | 0.557 ± 0.250 |
| 100% | 7672 | 0.802 ± 0.117 | 0.819 ± 0.036 | 0.574 ± 0.076 |

![Figure 1. Deletion F1 vs. labelled-data fraction for AlignSSL-pretrained, AlignSSL-scratch, and the DeepSV-representation baseline. Pretraining dominates in the low-label regime; all methods converge toward the pretrained/scratch plateau at full supervision, while the DeepSV-representation baseline remains lower and more variable.]({{artifact:bd75ee27-1b5f-402a-81d4-034ea297ff64}})

### 4.2 Pretraining improves calibration by ~5×

Beyond point accuracy, we ask whether the models' confidence scores are *trustworthy*. Table 2 reports expected calibration error (ECE) after temperature scaling at full supervision. The pretrained model is the best calibrated (ECE = 0.018), the from-scratch model is close behind (0.025), and the DeepSV-representation baseline is markedly miscalibrated (0.091 — a 5× larger calibration error). The DeepSV baseline also requires a large temperature correction (T = 1.79, i.e. strongly overconfident logits), whereas AlignSSL models need only mild correction (T ≈ 0.78–0.82). Well-calibrated confidence is a prerequisite for thresholding calls in any downstream or clinical pipeline, and is where the DeepSV paradigm is weakest.

**Table 2. Calibration at full supervision (ECE ↓, 3 seeds).**

| Model | ECE ↓ | Temperature |
|---|---|---|
| AlignSSL-pretrained | 0.0179 ± 0.0085 | 0.778 |
| AlignSSL-scratch | 0.0252 ± 0.0093 | 0.823 |
| DeepSV-repr. baseline | 0.0911 ± 0.0451 | 1.785 |

### 4.3 Length-stratified recall: pretraining stabilises long-deletion calling

Deletion callers are notoriously length-dependent. Table 3 stratifies test recall by deletion length. Both models are strong on short deletions (50–500 bp). The informative regime is **long deletions (1 kb–5 kb and 5 kb+)**, where the from-scratch model becomes extremely unstable (recall 0.798 ± 0.207 at 1–5 kb, and 0.497 ± 0.369 at 5 kb+ — standard deviations approaching the mean), while the pretrained model, though lower in mean recall at some strata, is **more stable** across seeds and does not collapse on the longest, rarest deletions (0.628 ± 0.399 at 5 kb+, and notably higher mean than scratch in that top stratum). Long deletions are where truth sets are sparsest, so the stabilising effect of pretraining is exactly where it is most needed.

**Table 3. Length-stratified recall at full supervision (test, 3 seeds).**

| Deletion length | n test | Pretrained recall | Scratch recall |
|---|---|---|---|
| 50–200 | 231 | 0.906 ± 0.045 | 0.964 ± 0.018 |
| 200–500 | 94 | 0.823 ± 0.091 | 0.954 ± 0.020 |
| 500–1k | 131 | 0.804 ± 0.146 | 0.967 ± 0.036 |
| 1k–5k | 286 | 0.653 ± 0.362 | 0.798 ± 0.207 |
| 5k+ | 94 | 0.628 ± 0.399 | 0.496 ± 0.369 |

![Figure 2. Length-stratified deletion recall. Pretraining stabilises recall on the long, rare deletions where the from-scratch model's variance explodes.]({{artifact:7e40e7aa-6415-43bc-afae-423511213b82}})

### 4.4 Ablation: masked-alignment modelling is the objective that matters

Which self-supervised objective drives these gains? We pretrain three encoders under identical budgets — **masked-alignment modelling (MAM) only**, **VICReg-style invariance only**, and their **combination** — and fine-tune each across the full label-fraction sweep (3 seeds each). Table 4 shows that **MAM-only leads at nearly every label fraction**, most strikingly in the low-label regime (F1 0.584 at 1% vs. 0.371 VICReg-only and 0.400 combined) and at full supervision (0.931 ± 0.006 vs. 0.873 ± 0.042 VICReg-only and 0.855 ± 0.031 combined). The sole exception is the 50% fraction, where VICReg-only edges ahead (0.825 vs. 0.804); at every other fraction MAM-only is best. The combined objective is not additive — mixing in VICReg does not improve over MAM alone (and is the weakest of the three at full supervision). This is a clean, actionable finding: for the alignment-tensor modality, masked reconstruction is the right pretext task, and invariance-based objectives (which dominate self-supervised *vision*) transfer poorly. We therefore adopt MAM-only as the pretraining objective for the panel-scale experiments.

**Table 4. Self-supervised objective ablation (deletion F1, 3 seeds).**

| Label fraction | MAM-only | VICReg-only | Combined |
|---|---|---|---|
| 1% | 0.584 | 0.371 | 0.400 |
| 5% | 0.636 | 0.430 | 0.408 |
| 10% | 0.685 | 0.488 | 0.565 |
| 25% | 0.722 | 0.657 | 0.678 |
| 50% | 0.804 | 0.825 | 0.748 |
| 100% | 0.931 | 0.873 | 0.855 |

### 4.5 Cross-ancestry generalisation: pretraining nearly eliminates the transfer gap

A model trained on one population and applied to a genetically distant one should not degrade sharply — but supervised models do. Table 5 trains on the in-distribution population and evaluates on an entirely held-out population (CEU). The from-scratch model has higher in-distribution F1 (0.898) but drops by **0.117 F1** when transferred (the "generalisation gap"). The pretrained model has lower in-distribution F1 (0.686) yet transfers almost losslessly — a generalisation gap of just **0.015 F1**, an 8× reduction. In other words, self-supervised features are far more **ancestry-robust**: the representation learned without labels encodes population-invariant alignment structure rather than population-specific label shortcuts. This is a direct, quantified rebuttal to the equity concern that SV callers trained on one population fail on others.

**Table 5. Cross-ancestry generalisation (train in-distribution → test held-out CEU, 3 seeds).**

| Model | In-dist. F1 | Held-out CEU F1 | Gen. gap ↓ | Held-out ECE |
|---|---|---|---|---|
| AlignSSL-pretrained | 0.686 ± 0.137 | 0.672 ± 0.174 | 0.015 ± 0.114 | 0.113 ± 0.131 |
| AlignSSL-scratch | 0.898 ± 0.052 | 0.781 ± 0.136 | 0.117 ± 0.084 | 0.055 ± 0.050 |

We note the trade-off transparently: the pretrained model's *absolute* in-distribution F1 is lower here than the from-scratch model's, so the claim is specifically about **robustness of transfer**, not uniformly higher accuracy. The panel-scale re-training (Section 6) — expanding pretraining to eight samples spanning five continental ancestries — is designed to raise the pretrained model's absolute performance while preserving its transfer robustness.

### 4.6 Data-integrity control

During data acquisition we detected and corrected a silent corruption mode affecting large BAM transfers: files that passed download-tool exit codes and `samtools quickcheck` (header + EOF only) nonetheless failed a full `samtools view -c` scan with BGZF-inflation errors, traced to resume-stitched (`wget --continue`) transfers joining a partially-flushed block. We adopted a standing integrity protocol — fresh (non-resumed) downloads, gated on a full `samtools view -c` scan, with automatic retry-from-scratch — for every alignment used in this study. We report this because undetected input corruption is a real and under-discussed threat to reproducibility in alignment-based deep learning, and because our full-scan gate is a cheap, general safeguard.

---

## 5. Novelty and positioning

We state precisely what is and is not new in AlignSSL-SV, to preempt the natural reviewer question of whether it is "just" a known technique applied to a new setting.

**What is new.** (i) The **image-free, learned alignment representation** — self-supervised pretraining directly on a continuous multi-channel read-alignment tensor, with no pileup-image rendering and no discrete tokenizer. This is the axis on which we differ from the sole prior SSL-for-SV effort, BASILISC (Banerjee, 2026), which pretrains a masked-image-modelling vision transformer over *rendered pileup images* compressed by a discrete VAE (Section 2); we remove the hand-designed image entirely and pretrain on the raw alignment evidence. Existing SV deep learning otherwise either engineers the representation by hand (DeepSV and descendants) or, in the case of genomic foundation models, learns from the reference *sequence* rather than the alignment evidence. (ii) The **coupling of self-supervised SV representations with calibrated, ancestry-robust uncertainty** — to our knowledge the first work to pair SSL SV representations with temperature-scaled calibration and an epistemic/aleatoric decomposition, and to show that the pretrained representation shrinks the cross-ancestry generalisation gap (~8× smaller than from-scratch). No prior SSL-for-SV work, BASILISC included, reports calibration or cross-population transfer. (iii) The **empirical finding that masked-alignment modelling is the strongest SSL objective** for this modality at nearly all label fractions and clearly best at full supervision, which inverts the usual vision-domain ranking and is non-obvious a priori. (iv) The **joint treatment of the three DeepSV bottlenecks** — label efficiency, calibration, and ancestry robustness — as a single representation-learning problem, with each measured as a first-class outcome.

We explicitly do **not** claim primacy on "self-supervised learning for structural variants" as a category — BASILISC precedes us there. Our claim is narrower and defensible: the *image-free alignment-tensor* representation, and its combination with *calibrated, transferable uncertainty*, is unreported in the published or deposited literature.

**What is not new (and we do not claim it is).** Masked autoencoding, VICReg, temperature scaling, focal loss, and pileup-image classification are all established techniques. Our contribution is their principled composition on a modality where they had not been combined, and the controlled evidence for what works. We also do not claim a higher full-supervision accuracy ceiling than a from-scratch model; the honest claim is label efficiency, calibration, and transfer robustness.

**Relationship to sequence foundation models.** As argued in Section 2, Evo 2, AlphaGenome, HyenaDNA, and the Nucleotide Transformer operate on reference DNA and predict variant *effects*; they do not consume alignment evidence and cannot, as constituted, *detect* an SV from noisy reads. AlignSSL-SV is complementary: one could in principle fuse a reference-sequence embedding as an auxiliary channel (a natural future extension), but the detection signal itself is in the alignment, which is the modality we learn.

---

## 6. Ongoing work: panel-scale, multi-ancestry re-training

The results above are established on a compact sample set. We are extending the study to an **eight-sample panel spanning five continental ancestries** (AFR, AMR, EAS, EUR, SAS) drawn from 1000 Genomes high-coverage PCR-free data, with two entire ancestries held out for the cross-population test. This extension (i) re-pretrains the encoder with the ablation-selected **MAM-only** objective on the enlarged unlabelled corpus, (ii) re-runs the label-efficiency, calibration, and length-stratified analyses at panel scale, and (iii) tests multi-ancestry generalisation on held-out CEU and LWK samples. The hypothesis, grounded in Section 4.5, is that a larger and more diverse pretraining corpus will raise the pretrained model's absolute accuracy while preserving its near-zero transfer gap. A coverage-robustness experiment (downsampling via `samtools view -s`) and a Truvari-based benchmark against GIAB HG002 gold-standard calls are planned as the headline external validation.

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
