# Four defects in the deep structural-variant evaluation design, and what survives when they are corrected

**Running title:** An audit of deep deletion-calling evaluation

**Ayush Kumar**

Correspondence: aayush.kumarm.3myself@gmail.com · Code: https://github.com/aayushkrm/AlignSSL-SV

**Keywords:** structural variant detection; deletion calling; benchmark separability; evaluation methodology; decision thresholds; self-supervised learning; read alignment; 1000 Genomes

---

## Abstract

**Motivation.** Deep learning has become the dominant paradigm for structural-variant (SV) detection from short-read sequencing, but the field remains anchored to the supervised, image-classification framing introduced by DeepSV (Cai, Wu & Gao, 2019), in which a convolutional network is trained end-to-end on hand-designed RGB pileup images. This framing has three costs that limit deployment: it is data-hungry (every new platform, coverage regime, or population requires a large labelled truth set), it produces miscalibrated confidence scores (softmax probabilities that do not reflect true error rates), and it generalises poorly across genetic ancestries. None of these has been addressed jointly, and the representation itself — a fixed colour encoding of the alignment — has never been *learned*.

**Results.** We present AlignSSL-SV, a framework that (i) replaces the fixed RGB pileup with a multi-channel alignment tensor and a learned encoder, (ii) pretrains that encoder by masked-alignment modelling (a self-supervised objective on read alignments, requiring no SV labels), and (iii) attaches a calibrated deletion head. Evaluated on 1000 Genomes high-coverage PCR-free data (a six-sample panel spanning five continental ancestries) under the conventions this literature inherits from DeepSV, the framework appears to deliver a large low-label gain: deletion F1 of 0.48 at 1% of labels (210 windows) against 0.04 for an identically-architected from-scratch model, a ≈11× improvement attributable to self-supervised initialisation alone (*p* = 0.009).

**That result does not survive scrutiny, and neither do several others.** We identify four defects in the evaluation design and correct each:

1. **The benchmark is separable without a model.** Twelve hand-crafted alignment features fed to a gradient-boosted tree reach AUPRC = 0.937 from the same 210 labels and gain only +0.038 across a 100× increase in labels; the single centre-versus-flank read-depth ratio separates the classes at ROC-AUC = 0.955 untrained. The uniformly-sampled negatives are a depth heuristic, saturated before any deep model is trained.
2. **Scoring at a fixed probability cut manufactures the low-label gap.** Re-scoring the identical runs at a threshold selected on a validation split, the 11× advantage becomes 1.17× and loses significance (0.483 vs 0.413, *p* = 0.407); threshold-free, it is 1.23× (*p* = 0.348). At every one of the five larger label budgets the from-scratch arm is *ahead*. The from-scratch model was never degenerate — it ranks competently, and its scores simply are not centred where a fixed cut expects them.
3. **The label budgets were not equal.** A batch-size floor in the deep evaluators granted the deep arms 96 labels where the classical control received 35 on the candidate-filtered benchmark — a 2.8× advantage in exactly the cell carrying the headline claim.
4. **No significance claim carried a multiplicity adjustment.** Every *p*-value in this literature, ours included, is drawn from a sweep of six or more simultaneous tests and reported as if it were one. Under Holm–Bonferroni within pre-declared families (67 tests, 11 families), 20 nominal hits fall to 10; the headline low-label *p* = 0.009 becomes 0.055, and the cross-ancestry effect we had already declined to claim is settled as chance (Holm *p* = 0.169).

We then repair the benchmark itself: quantile-matched candidate negatives attenuate the depth shortcut from ROC-AUC 0.955 to 0.717, and the same twelve-feature control that was saturated on the uniform benchmark now starts at chance (AUPRC 0.250) and climbs +0.619 across the label range, confirming that headroom is restored.

Re-run under all three corrections, what survives is narrow. Self-supervised pretraining confers no threshold-free advantage at any label budget on either benchmark. The hand-crafted control is not beaten where labels are scarce — the regime the deep method is proposed for — though its lead is significant at only two of six budgets per benchmark rather than at all of them, and at full supervision on the uniform benchmark the from-scratch network does edge ahead (AUPRC 0.979 vs 0.975, *p* = 0.003) by a margin too small to matter in practice.

**Conclusion.** We report this as a methodological result rather than a method paper. Each defect is individually mundane and each is, by a coded audit of 14 papers from this literature (Section 7), the field's default: benchmarks built from randomly-sampled negatives, F1 reported at a fixed cut, and label budgets computed per-arm are all standard practice in this literature. Together they were sufficient to produce a confident, statistically significant, entirely artefactual headline. We publish the corrections, the controls, and the code that implements them so that the next paper in this lineage can be checked against them.

**Availability.** Code, the tensor-extraction pipeline, result tables and figures are at https://github.com/aayushkrm/AlignSSL-SV (MIT licence).

---

## 1. Introduction

Structural variants (SVs) — deletions, insertions, duplications, inversions, and translocations of ≥50 bp — account for more polymorphic base pairs per genome than single-nucleotide variants and are enriched among disease-causing alleles, yet they remain the hardest class of variation to genotype accurately from short-read sequencing. Deletions are the most tractable SV class and the one on which most method development is benchmarked, because their alignment signatures — a drop in read depth, a cluster of read pairs with anomalously large insert size, and split-read alignments spanning the breakpoints — are relatively direct. Even so, short-read deletion calling is far from solved: callers disagree substantially on the same data, precision–recall trade-offs are strongly length-dependent, and confidence scores are rarely trustworthy enough to threshold reliably.

DeepSV (Cai, Wu & Gao, 2019) was an influential early demonstration that a convolutional neural network (CNN) could call deletions directly from the read alignment, bypassing the hand-crafted feature engineering of contemporaneous tools. Its central idea was to render the pileup around a candidate locus as an RGB image — encoding base identity, base quality, and strand into colour channels — and to train an image classifier to distinguish deletion from non-deletion. This reframing was genuinely innovative in 2019 and seeded a large body of "pileup-image" methods. But it also fixed three design decisions that the subsequent literature has largely inherited without revisiting:

1. **The representation is hand-designed, not learned.** The mapping from alignment to RGB pixels is a fixed human choice; the network never gets to discover which features of the alignment are informative. Information that does not survive the colour encoding (e.g. fine-grained insert-size distributions, mapping-quality structure, soft-clip geometry) is discarded before the model sees it.
2. **Training is fully supervised and therefore data-hungry.** Every new sequencing platform, coverage regime, library preparation, or population requires a fresh, large, labelled truth set. Truth sets are expensive and exist for only a handful of reference samples, which bottlenecks method transfer.
3. **Confidence is uncalibrated and ancestry-brittle.** Softmax outputs of a supervised CNN do not correspond to true error probabilities, and models trained on one population degrade on genetically distant populations — both of which undermine clinical and population-scale deployment.

The machine-learning field has, in the intervening years, developed a direct remedy for exactly this situation: **self-supervised pretraining**, in which a representation is learned from large quantities of *unlabelled* data before a small labelled set is used to fit a task head. Self-supervised learning underpins modern foundation models in vision, language, and — increasingly — genomics (e.g. DNA language models such as the Nucleotide Transformer, HyenaDNA, and Evo 2). Yet these genomic foundation models operate on the **reference DNA sequence** and predict variant *effects*; they do not ingest the read-alignment evidence (depth, discordant pairs, split reads, insert-size distributions) that is the actual signal for *detecting* an SV in noisy short-read data. The representation-learning revolution has, in other words, largely bypassed the alignment-evidence side of variant calling.

This paper set out to ask a focused question: **if we learn the alignment representation and pretrain it without labels, do the three DeepSV bottlenecks — data hunger, miscalibration, and ancestry brittleness — improve together?** We built the framework, ran the evaluation, and obtained an affirmative answer with a large effect size and a convincing *p*-value. We then subjected that answer to controls it should have faced first, and it did not survive any of them.

What follows is therefore an audit rather than a method paper. We report the framework because the corrections are only legible against a concrete instance of the design, and because the same four defects are, as far as we can determine, standard practice in this literature rather than idiosyncratic to our implementation. Our contributions are:

- **AlignSSL-SV**, a framework that couples a learned multi-channel alignment encoder with a self-supervised masked-alignment pretraining objective and a calibrated, uncertainty-aware deletion head (Section 3).
- A controlled evaluation on a six-sample, five-ancestry 1000 Genomes panel which, scored by the conventions this literature inherits, shows a large low-label gain from pretraining (≈11× F1 at 1% labels, *p* = 0.009) — the result the rest of the paper dismantles (Section 4).
- **A hand-crafted-feature control that bounds what the benchmark can show** (Section 4.2): twelve alignment features reach AUPRC 0.937 from 210 labels and gain +0.038 across a 100× label increase, and one depth-ratio feature reaches ROC-AUC 0.955 untrained. We report this as a negative result about the random-negative evaluation protocol, which is widely used in this literature and, to our knowledge, has not previously been subjected to such a control.
- **A demonstration that F1 at a fixed probability cut manufactures initialisation gaps** (Section 4.8): the headline result exists under that cut and under no other scoring rule, because a from-scratch network trained on 210 labels ranks competently while scoring timidly. Any label-efficiency claim scored this way is measuring calibration, not representation quality.
- **A protocol correction establishing equal label budgets across arms** (Section 3.8): a batch-size floor in the deep evaluators had granted them up to 2.8× the labels the classical control received in the low-label cells that carry the headline claims.
- **A family-wise multiplicity audit of every significance claim in the paper** (Section 4.9): a label-efficiency sweep is a multiple-comparison procedure whether or not it is analysed as one. Under Holm–Bonferroni within pre-declared families, the 20 nominally significant tests across this paper fall to 10, and the headline claim is not among the survivors.
- A controlled ablation (3–4 seeds, error bars computed across *pretraining* seeds) isolating the contribution of each self-supervised objective (Section 4.5).
- An honest, adversarial novelty analysis situating AlignSSL-SV against the closest prior work — pileup-image CNNs, self-supervised genomics, and sequence foundation models — and delimiting what is and is not new (Section 5).

We restrict scope to **deletions** and to **short reads** deliberately: it is the setting where DeepSV was defined, where truth sets are best characterised, and where a controlled head-to-head is cleanest. Section 7 discusses the extension to other SV classes and to long reads.

---

## 2. Related work

**Pileup-image SV and variant callers.** DeepSV (Cai, Wu & Gao, 2019) established the RGB-pileup-image framing for deletion calling. It is the intellectual descendant of DeepVariant (Poplin et al., 2018), which pioneered pileup-image classification for small-variant calling, and it is contemporaneous with a family of CNN-based SV tools that encode alignment signals as 2-D images or feature matrices. Later methods (e.g. Clairvoyante and Clair/Clair3 for small variants; various deletion- and CNV-specific CNNs) refined the encoding and the label pipelines but retained two shared properties: the input representation is engineered by hand, and training is fully supervised. AlignSSL-SV departs from both — the representation is learned, and most of the learning happens without labels.

**Self-supervised and representation learning.** Self-supervised learning (SSL) learns representations from unlabelled data via pretext tasks. Two broad families are relevant here: (i) **masked-reconstruction** objectives (masked autoencoders in vision, masked language modelling in NLP), which mask part of the input and train the model to reconstruct it; and (ii) **joint-embedding / invariance** objectives (SimCLR, BYOL, Barlow Twins, VICReg), which pull together representations of augmented views while preventing collapse. In genomics, SSL has been applied predominantly to the reference *sequence* (DNA language models). Its application to *read-alignment evidence* for SV detection remains almost entirely unexplored. Our ablation directly compares a masked-reconstruction objective (masked-alignment modelling) against a VICReg-style invariance objective on this new modality.

**Self-supervised pretraining on read-derived SV representations.** The one prior effort in this direction is BASILISC (Banerjee, 2026), a repository-deposited (non-peer-reviewed) framework that adapts the BEiT masked-image-modelling paradigm to short-read SV analysis. BASILISC renders aligned reads into multi-channel *pileup images* (depth, split reads, discordant pairs, mapping quality, strand, allele support), compresses those images into discrete visual tokens with a discrete VAE, and pretrains a vision transformer to predict masked tokens before fine-tuning an SV classifier on 1000 Genomes data with HGSVC2 long-read truth. AlignSSL-SV differs on three substantive axes. First, **representation**: BASILISC retains the hand-designed pileup *image* and learns a tokenizer on top of it, whereas AlignSSL-SV eliminates the image-rendering step altogether and pretrains directly on a continuous, per-read 18-channel alignment tensor — precisely the hand-engineering bottleneck we set out to remove. Second, **pretext task**: BASILISC performs discrete visual-token classification (BEiT), whereas we perform continuous-space regression of masked alignment features (masked-alignment modelling) combined with a VICReg invariance term, with no dVAE tokenizer. Third, BASILISC reports no calibration or uncertainty component and no cross-ancestry analysis. BASILISC therefore corroborates the field-level premise that learned SV representations are worth pursuing, while leaving the image-free alignment-tensor formulation unexplored. We note that BASILISC's evaluation, like DeepSV's and like ours, is built on negatives that are not candidate-derived — the separability question raised in Section 4.2 applies to it as well, and we raise it as a property of the shared benchmark design rather than a criticism of any single paper.

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

We pretrain by **masked-alignment modelling (MAM)**: a random fraction (0.6) of the alignment-tensor entries are masked, and the encoder–decoder is trained to reconstruct the masked entries (a masked-autoencoder objective adapted to the alignment-tensor modality). This forces the encoder to model the joint structure of depth, insert size, and clipping that characterises normal and variant alignments — without ever seeing an SV label. Pretraining uses 120,000 unlabelled windows drawn from three samples (NA19238, NA19625, NA20845; AFR × 2 + SAS) restricted to the pretraining chromosomes, consolidated into a flat float16 memory-mapped array (65.9 GiB) for throughput. No SV labels enter this stage: every window carries label = −1.

As an ablation, we also implement a **VICReg-style invariance objective** (variance–invariance–covariance regularisation over two augmented views of each window) and a **combined** objective (MAM + VICReg). Section 4.5 compares the three; all deliver the low-label effect, and the available seed count does not support ranking them against one another.

### 3.5 Deletion head, calibration, and uncertainty

The fine-tuning head is a small classifier on the window embedding, trained with a focal loss (γ=2) to handle the strong negative:positive class imbalance of genome-wide deletion candidates. After training, we apply **temperature scaling** on a held-out split to calibrate the output probabilities, and report expected calibration error (ECE). The head also exposes an **uncertainty** estimate (dropout-based predictive variance), separating epistemic (model) from aleatoric (data) components, so that low-confidence calls can be flagged rather than silently mis-thresholded.

### 3.6 Data and splits

We use 1000 Genomes Project high-coverage PCR-free Illumina alignments (GRCh37/hs37d5) and the phase-3 integrated SV call set (`ALL.wgs.mergedSV.v8.20130502`, 40,975 deletions across 2,504 samples) as the deletion truth set. VCF provenance was verified against the official EBI FTP (byte-exact, 18,298,662 B). The chromosome split is the DeepSV convention: chr1–11 for training, chr12–22 for testing. Self-supervised pretraining draws its unlabelled windows from the **training** chromosomes only (`cluster/extract_pretrain.sbatch`), so the encoder never sees chr12–22 at any stage — pretraining, fine-tuning and evaluation are arranged so that no test chromosome enters any training objective. Pretraining and fine-tuning are therefore *not* disjoint from each other, and deliberately so: they share chr1–11, which is what makes the pretrained representation relevant to the fine-tuning distribution. What is disjoint is training from test. For the cross-ancestry experiment, models are trained on the six-sample panel (NA19238 YRI, NA19625 ASW, NA18525 CHB, NA19648 MXL, NA20502 TSI, NA20845 GIH; five continental ancestries) and evaluated both in-distribution — on chr12–22 of those same samples — and on an entirely held-out sample from a population absent from training (NA12878, CEU). The held-out arm is therefore held out by sample *and* by ancestry; the in-distribution arm is held out by chromosome only. Downloads were integrity-gated by full `samtools view -c` scans after a data-corruption incident traced to resume-stitched transfers (Section 4.7).

### 3.7 Baselines

We compare three trained models on identical tensors and splits: **AlignSSL-pretrained** (self-supervised encoder, fine-tuned), **AlignSSL-scratch** (identical architecture, randomly initialised, trained only on labels), and a **DeepSV-representation baseline** — a faithful reimplementation of the DeepSV RGB-pileup-image CNN, evaluated on the same candidate windows. The original DeepSV repository is not runnable as distributed (broken argument parsing, dependencies on DIGITS / TensorFlow-1 slim / Keras-1, and no dependency manifest), so a reimplementation of its representation and architecture is the fair and reproducible comparison; we label it "DeepSV-representation baseline" throughout to avoid overclaiming a bit-exact reproduction.

### 3.8 Evaluation protocol: equal budgets, budgeted thresholds

A label-efficiency curve is interpretable only if every arm is handed the same number of labels at each point on the x-axis. An earlier version of this work did not satisfy that condition, and the defect is worth stating explicitly because it is easy to introduce and invisible in results.

The deep evaluators computed the budget as `max(batch_size, int(frac × n_pool))` while the classical evaluator used `max(2, round(frac × n_pool))`. On the uniform benchmark (n_pool = 21,016) the batch-size floor never binds and the two agree. On the candidate-filtered benchmark (n_pool = 3,452) the 1% cell is 34 examples, below the floor of 96 — so the deep arms received 96 labels while the control received 35, a **2.8× advantage in exactly the cell carrying the headline low-label claim.** The floor was not arbitrary: a `DataLoader` configured to drop incomplete batches yields *zero* batches when the subset is smaller than one batch, so simply removing the floor trains the low-label cells on nothing. The correct fix honours the true budget and adapts the loader to it — dropping incomplete batches only when at least one full batch exists — rather than inflating the budget to suit the loader.

A second defect shared that root cause. The validation split used to select the decision threshold was gated on `n_val ≥ batch_size`, so on the filtered benchmark no split was carved below 25% of labels and those cells silently fell back to a fixed 0.5 cut — again precisely the cells of interest. The gate is now a small absolute minimum (12 examples per side) independent of batch size.

We also changed where the validation labels come from. They are now carved **out of** the budget rather than granted in addition to it: a curve in which every arm receives an unbudgeted validation set on top of its stated budget is not a label-efficiency curve. At the 1% point on the uniform benchmark an arm therefore sees 210 labels in total — 168 for gradient steps and 42 for threshold selection — not 210 plus a free 42. The visible consequence is intended: full supervision now fits on 16,813 of 21,016 windows, so absolute scores sit below the previously published fixed-threshold numbers, while across-arm comparisons remain exact because every arm pays the identical cost.

All three rules live in a single module (`alignssl/protocol.py`) imported by every evaluator, with unit tests, so the arms cannot drift apart again. Sections 4.1, 4.2, 4.8 and 6 all report numbers produced under this protocol: Table 1 and Table 7 were regenerated from `results/table12_label_efficiency_fixed.csv` at equal budgets (Table 1 simply reads its fixed-0.5-cut columns, which is what makes it comparable to the pre-correction literature), and Tables 13 and 14 are corrected-protocol by construction. Sections 4.3–4.7 — calibration, length strata, the objective ablation and cross-ancestry transfer — predate the correction, and every table in that range (Tables 2–5) says so in its caption. Two distinct mechanisms are involved and the captions name the applicable one. Tables 2–4 come from full-supervision runs that received an unbudgeted validation split, which lifts their absolute values slightly above corrected-protocol equivalents. Table 5 is a label *sweep*, where the consequential defect is instead the batch-size floor: its generating evaluator granted `batch_size` labels at the smallest fractions rather than the nominal share, so the low-label cells of that sweep are not comparable to the corrected curves of Section 4.8. That evaluator now imports the shared module, and a static test (`tests/test_evaluator_protocol_adoption.py`) fails if any label-sweep evaluator reintroduces the floor or stops calling the shared budget function — the omission that let this one drift, which a unit test on the module itself could not detect.

---

## 4. Results

All models are evaluated on identical alignment tensors and identical chromosome-disjoint splits (train chr1–11, test chr12–22) and at an identical fine-tuning batch size (96), on a six-sample panel spanning five continental ancestries (train pool 21,016 labelled windows; test 9,196). We report mean ± standard deviation across random seeds — four for the combined-objective arm, three for every other arm. Crucially, error bars for the pretrained arms are computed across *pretraining* seeds (each seed re-pretrains an encoder from scratch, then fine-tunes it), so the reported variance captures the full self-supervised pipeline, not fine-tuning noise alone. The task is binary deletion calling on genome-wide candidate windows.

### 4.1 Under the conventional scoring rule, pretraining appears strongly label-efficient

We report this section as it stood before the corrections of Sections 4.8 and 3.8, because the corrections are only interpretable against the claim they overturn. Every number here is scored the way this literature scores: deletion F1 obtained by thresholding the positive-class probability at a fixed 0.5.

Table 1 reports that F1 as a function of the fraction of the labelled training set made available to the fine-tuning head. The apparent result is in the **low-label regime**: at 1% of labels (210 windows), the pretrained model reaches F1 = 0.478 ± 0.100, whereas the identically-architected from-scratch model all but collapses to 0.044 ± 0.041 — a **≈11× improvement in F1** from self-supervised initialisation alone, significant at *p* = 0.009 — a figure Section 4.9 shows does not survive multiplicity correction either (though not after correcting for the six budgets of the sweep — Section 4.9). As labels increase the from-scratch model catches up and overtakes; by 5% it is already ahead (0.714 vs 0.576).

Two features of the table are worth noting before it is dismantled, because neither is compatible with the story it is usually told to support. First, the DeepSV-representation baseline matches the pretrained tensor model at 1% (0.479 ± 0.035) — whatever the pretrained arm is doing at the smallest budget, a hand-designed RGB encoding does it too, which already argues against a representation-quality explanation. Second, the from-scratch arm's collapse is confined to that single cell: one budget later it leads every arm in the table. A representation deficit that vanishes between 210 and 1,051 labels is a strange kind of deficit.

Read on its own, this table says that pretraining supplies a usable detector from a truth set two orders of magnitude smaller than is conventionally required. It says nothing of the kind. Section 4.2 shows the benchmark is separable without any model, and Section 4.8 shows the 11× gap is a property of the threshold rather than of the representation — the from-scratch model at 210 labels ranks nearly as well as the pretrained one and merely scores below 0.5 while doing it.

**Table 1. Label efficiency as conventionally scored (deletion F1 at a fixed 0.5 probability cut, test chr12–22, batch 96, 3 seeds per arm). Table 12 reports the same runs under threshold selection and threshold-free scoring; the two tables disagree, and Table 13 quantifies the disagreement.**

| Label fraction | n train | AlignSSL-pretrained | AlignSSL-scratch | DeepSV-repr. |
|---|---|---|---|---|
| 1% | 210 | 0.478 ± 0.100 | 0.044 ± 0.041 | **0.479 ± 0.035** |
| 5% | 1,051 | 0.576 ± 0.050 | **0.714 ± 0.094** | 0.477 ± 0.107 |
| 10% | 2,102 | 0.740 ± 0.038 | **0.818 ± 0.081** | 0.581 ± 0.078 |
| 25% | 5,254 | **0.814 ± 0.107** | 0.803 ± 0.129 | 0.672 ± 0.180 |
| 50% | 10,508 | 0.887 ± 0.032 | **0.930 ± 0.006** | 0.770 ± 0.115 |
| 100% | 21,016 | 0.888 ± 0.053 | **0.921 ± 0.027** | 0.702 ± 0.136 |

![Figure 1. Deletion F1 vs. labelled-data fraction on the uniform benchmark, scored the way this literature scores it: a fixed 0.5 probability cut. Source is the `f1_at_half` columns of the corrected-protocol runs (`results/table12_label_efficiency_fixed.csv`, uniform rows), so the panel plots exactly the values tabulated in Table 1. The bracket marks the 10.9× pretrained-over-scratch ratio at the smallest budget; that ratio is a property of the fixed cut and not of the representation, and it does not survive threshold selection or threshold-free scoring (Figure 6). Note also that the pretrained arm does not lead the DeepSV baseline at this budget — the two are tied.]({{artifact:art_6b3657d8-5b3f-4b2c-b2ad-1df2139e7a24}})

### 4.2 A hand-crafted-feature control bounds what this benchmark can demonstrate

Every deep-learning SV paper we are aware of, DeepSV included, compares deep architectures against one another or against signature-based callers, but not against a *deliberately minimal* learned baseline on the identical windows. We ran that control, and it is the most consequential result in this paper.

From the same alignment tensors, identical shards, identical chromosome split, identical label fractions and identical seeds, we computed twelve scalar summary features per window — mean, standard deviation and minimum of the depth profile; centre-versus-flank depth ratio; maximum sustained depth drop; discordant-pair rate; soft-clip rate; mean and maximum insert-size |z|; mean mapping quality; occupied read-row count; and valid-base fraction — and fitted an ℓ2-regularised logistic regression and a gradient-boosted tree (`Classical-logreg`, `Classical-GBT`; Table 14 and `results/table11_control_threshold_free.csv`). The tree is at its ceiling from the smallest label budget onward. At 1% labels (210 windows), where the paper's headline claim lives, it reaches **AUPRC = 0.937 ± 0.009** against 0.524 ± 0.052 for the pretrained network and 0.427 ± 0.138 from scratch. Increasing its labels one hundred-fold, to the full 21,016 windows, buys it **+0.038** (0.975 ± 0.001). A benchmark on which twelve scalar features are 96% of the way to their asymptote after 210 examples cannot discriminate between representation-learning methods, because there is almost nothing left for a representation to contribute. Its variance across seeds is one to two orders of magnitude smaller than any deep arm's.

**Table 14. Control versus best deep arm, threshold-free, corrected protocol (uniform benchmark; AUPRC, 3 seeds; leader named only where Welch's *t* clears 0.05).**

| Label fraction | n labels | Classical-GBT | Best deep arm | its AUPRC | *p* | Leader |
|---|---|---|---|---|---|---|
| 1% | 210 | 0.937 ± 0.009 | AlignSSL-pretrained | 0.524 ± 0.052 | 0.005 | control |
| 5% | 1,051 | 0.958 ± 0.006 | AlignSSL-scratch | 0.866 ± 0.022 | 0.016 | control |
| 10% | 2,102 | 0.967 ± 0.004 | AlignSSL-scratch | 0.912 ± 0.030 | 0.087 | tie |
| 25% | 5,254 | 0.971 ± 0.002 | AlignSSL-scratch | 0.936 ± 0.023 | 0.121 | tie |
| 50% | 10,508 | 0.974 ± 0.002 | AlignSSL-scratch | 0.974 ± 0.001 | 0.671 | tie |
| 100% | 21,016 | 0.975 ± 0.001 | AlignSSL-scratch | 0.979 ± 0.001 | 0.003 | **deep** |


We initially reported this control as dominating every deep arm at every budget. Under corrected scoring that statement is too strong, and Table 14 replaces it: on the uniform benchmark the control's lead is statistically significant at 1% and 5%, indistinguishable at 10%, 25% and 50%, and *reversed* at full supervision, where the from-scratch network reaches AUPRC 0.979 ± 0.001 against the tree's 0.975 ± 0.001 (*p* = 0.003) — a margin that is statistically clear and practically negligible. The defensible claim is narrower than the one we first made and is sufficient for the argument: **where labels are scarce, which is the regime self-supervised pretraining is proposed for, the deep arms do not beat twelve hand-crafted features.**

We then localised the cause. Scoring each feature individually on the held-out test set, *with no training whatsoever* and no fitted parameter of any kind, the **centre-versus-flank read-depth ratio alone attains ROC-AUC = 0.955** (Table 6). The benchmark is therefore separable by a single depth heuristic that requires no model at all.

**Table 6.** Untrained single-feature discrimination on the held-out test split (chr12–22, *n* = 9,196; 2,299 deletions). ROC-AUC is the exact rank statistic. A feature can be informative with either polarity — for depth-like features the *low* tail is deletion-like — so the oriented column reports max(AUC, 1 − AUC), the magnitude of the information leak; 0.5 is uninformative. Reproduced by `scripts/single_feature_auc.py`.

| Feature | ROC-AUC | Oriented | Deletion side |
|---|---|---|---|
| centre-vs-flank depth ratio | 0.045 | **0.955** | low |
| soft-clip rate | 0.802 | 0.802 | high |
| discordant-pair rate | 0.732 | 0.732 | high |
| insert-size \|z\| (max) | 0.694 | 0.694 | high |
| depth s.d. | 0.686 | 0.686 | high |
| max sustained depth drop | 0.680 | 0.680 | high |
| insert-size \|z\| (mean) | 0.678 | 0.678 | high |
| depth minimum | 0.343 | 0.657 | low |
| mean mapping quality | 0.450 | 0.550 | low |
| occupied read rows | 0.538 | 0.538 | high |
| valid-base fraction | 0.517 | 0.517 | high |
| mean depth | 0.502 | 0.502 | high |

Two features of this table are worth drawing out. First, **mean depth is uninformative** (0.502) while the centre-versus-flank *ratio* is near-perfect: what leaks is not coverage level but the localised contrast between a window's middle and its edges, which is exactly the geometry the extraction protocol builds into every positive. Second, the leak is not confined to depth — soft-clip and discordant-pair rates independently reach 0.73–0.80, so a benchmark repair that neutralises only the depth statistic would leave two further shortcuts intact. This is why the remediation in Section 6 matches on the depth ratio and then re-runs the full arm set, including the classical controls, rather than assuming one matched feature makes the task hard.

The mechanism is the negative-sampling protocol, which we inherited from standard practice in this literature and which our own extraction code implements: positive windows are centred on truth deletions, while negatives are drawn **uniformly at random** from the same chromosomes, rejected only if they overlap or abut a truth deletion. A uniformly-drawn genomic window does not resemble a deletion. The resulting task is "does a coverage dip exist here?", not "is this proposed candidate a real deletion?" — and the former is answerable by a threshold.

This does not invalidate the comparisons in Section 4.1, which are internally controlled and reproducible; it re-scopes what they measure. Even so, the separability control is not the only reason to distrust the pretrained-versus-scratch gap: Section 4.8 shows that the gap at 1% labels is an artefact of the fixed 0.5 probability cut and does not survive threshold-free scoring (*p* = 0.407 on F1 at a validation-selected threshold, *p* = 0.348 on AUPRC). What the control adds is an explanation of why even a surviving gap would have been uninformative — it would show that a randomly-initialised network needs more labelled examples than a pretrained one to learn a depth threshold, not that self-supervised pretraining confers deployable label efficiency for deletion calling. We attempted a partial remedy by re-selecting the most deletion-like negatives from the existing pool and re-scoring: the shortcut feature's discrimination fell only from ROC-AUC 0.955 to 0.920, confirming that a uniformly-sampled pool contains no genuinely hard negatives to recover. The proper fix is to change the candidate set, not the subset; we build and report that benchmark in Section 6, where the shortcut falls to ROC-AUC 0.717 and the hand-crafted control still leads wherever labels are scarce.

**We therefore report the benchmark-separability finding as a first-class contribution.** The control costs minutes of CPU time, applies to any pileup-style SV benchmark, and to our knowledge has not previously been run. Its implication is that published low-label and architecture-comparison results on random-negative SV benchmarks — a family that includes DeepSV's own evaluation and much of what followed — may be measuring threshold-learning speed rather than caller quality.

![Figure 2. Left: deletion AUPRC versus labelled-data fraction for all five arms on the uniform benchmark, scored threshold-free under the corrected protocol (Table 12). The gradient-boosted 12-feature control (heavy line) leads by +0.413 AUPRC at 1% and +0.091 at 5%, converges to a tie by 50%, and is marginally overtaken at full supervision (0.975 versus 0.979); the earlier claim of dominance at every budget is withdrawn (Table 14). Right: single-feature discrimination on the held-out test set with no training — the centre-versus-flank depth ratio alone reaches ROC-AUC 0.955.]({{artifact:art_38410a53-1025-43c4-a9af-0a3521eb07d9}})

### 4.3 Calibration is a property of the representation, not of self-supervision

Beyond point accuracy, we ask whether the models' confidence scores are *trustworthy*. Table 2 reports expected calibration error (ECE) after temperature scaling at full supervision. Both learned-tensor models are well calibrated (pretrained ECE = 0.0078 ± 0.0017, from-scratch 0.0072 ± 0.0004) and require only a mild temperature correction (T ≈ 0.6). The DeepSV-representation baseline is worse, but the size of the gap depends on the summary statistic and rests on a small sample: its per-seed ECEs are 0.033, 0.168 and 0.016, so the mean (0.072 ± 0.068) is driven by a single outlier seed while the **median is 0.033** — roughly four-fold worse than the tensor models rather than the order of magnitude a mean-only reading suggests. We report both statistics and draw no order-of-magnitude claim from three seeds. The baseline also needs a large and erratic temperature correction (T = 1.41 ± 0.88), consistent with its unstable F1 (Section 4.1).

The defensible reading is that calibration tracks the *representation* rather than self-supervision: pretrained and from-scratch tensor models are indistinguishable here, so the difference is attributable to the multi-channel encoding versus the fixed RGB pileup, not to the pretraining objective.

**Table 2. Calibration at full supervision, pre-correction protocol (ECE ↓ after temperature scaling; pretrained/scratch = 4 seeds, DeepSV = 3 seeds). Per-seed values given because the DeepSV mean is outlier-driven.**

| Model | ECE mean ↓ | ECE median ↓ | Temperature | ECE per seed |
|---|---|---|---|---|
| AlignSSL-pretrained | 0.0078 ± 0.0017 | 0.0077 | 0.634 ± 0.070 | 0.0070; 0.0101; 0.0083; 0.0056 |
| AlignSSL-scratch | 0.0072 ± 0.0004 | 0.0071 | 0.586 ± 0.055 | 0.0073; 0.0078; 0.0067; 0.0069 |
| DeepSV-repr. baseline | 0.0724 ± 0.0681 | 0.0327 | 1.411 ± 0.881 | 0.0327; 0.1683; 0.0163 |

### 4.4 Length-stratified recall: the learned tensor is consistent across length; the RGB baseline is not

Deletion callers are notoriously length-dependent. Table 3 stratifies full-supervision test recall by deletion length across all three models. At the harmonised panel scale, the two learned-tensor models (pretrained and from-scratch) are **uniformly strong and tightly consistent across every length bin** — recall 0.86–0.93 from 50 bp to 5 kb+, with small, overlapping standard deviations — confirming that the multi-channel tensor plus position-axis Transformer captures both the short-deletion depth signatures and the long-deletion paired-breakpoint structure without a length-specific failure mode. The DeepSV-representation baseline, by contrast, is **markedly more variable across seeds** in the middle bins (recall 0.841 ± 0.165 at 200–500 bp and 0.850 ± 0.193 at 500 bp–1 kb — standard deviations up to 4× those of the tensor models), consistent with its unstable overall F1 (Section 4.1) and miscalibration (Section 4.3). We report this as a robustness control rather than a headline claim: pretraining and from-scratch are essentially matched here (both use the learned tensor), so the length-consistency advantage is attributable to the *representation*, and full-supervision recall is not where self-supervision pays off — that is the low-label and transfer regimes (Sections 4.1, 4.6).

**Table 3. Length-stratified recall at full supervision, pre-correction protocol (recall at a fixed 0.5 cut; test; pretrained/scratch = 4 seeds, DeepSV = 3 seeds).**

| Deletion length | n test | Pretrained recall | Scratch recall | DeepSV-repr. recall |
|---|---|---|---|---|
| 50–200 | 645 | 0.919 ± 0.026 | 0.917 ± 0.017 | 0.942 ± 0.059 |
| 200–500 | 281 | 0.913 ± 0.018 | 0.903 ± 0.025 | 0.841 ± 0.165 |
| 500–1k | 329 | 0.929 ± 0.008 | 0.938 ± 0.014 | 0.850 ± 0.193 |
| 1k–5k | 799 | 0.926 ± 0.024 | 0.954 ± 0.006 | 0.899 ± 0.116 |
| 5k+ | 245 | 0.857 ± 0.061 | 0.881 ± 0.071 | 0.918 ± 0.070 |

![Figure 3. Length-stratified deletion recall at full supervision. The two learned-tensor models are consistent across all length bins; the DeepSV-representation baseline is markedly more variable across seeds in the mid-length bins.]({{artifact:art_cf7645c0-8b8d-46e9-9a50-95509162a99d}})

### 4.5 Ablation over self-supervised objectives: all three help, but they cannot be ranked at this seed count

Which self-supervised objective drives the fixed-cut gains of Section 4.1? The question is worth answering even though Section 4.8 shows those gains do not survive threshold-free scoring, because the answer turns out to be that the objectives are indistinguishable — which is itself evidence against a representation-quality explanation. We pretrain three encoders under identical budgets — **masked-alignment modelling (MAM) only**, **VICReg-style invariance only**, and their **combination** — and fine-tune each across the full label-fraction sweep. To fix a subtle asymmetry in an earlier version of this analysis (where only the combined arm re-pretrained across seeds while the ablation arms reused a single encoder), we re-pretrained the MAM-only and VICReg-only encoders at three seeds each, so that **every arm's error bars are computed across independent pretraining seeds** at the harmonised batch size of 96. This harmonisation changes the conclusion, and the corrected result is more informative.

All three self-supervised arms deliver the low-label effect, and each is individually significant against from-scratch training at 1% labels (Welch's *t*: MAM-only *p* = 0.017, VICReg-only *p* = 4.2 × 10⁻⁵, combined *p* = 4.2 × 10⁻⁵). That is the robust conclusion: the low-label gain does not depend on which objective is used.

Ranking the objectives *against one another*, however, is **not supported at the available seed count**. The ordering of means in Table 4 suggests MAM leads below 10% labels and the combined objective leads above 25%, but neither contrast reaches significance: MAM-only versus combined at 1% gives *t* = 0.83, *p* = 0.48, and combined versus MAM-only at 100% gives *t* = 1.77, *p* = 0.21. With three to four pretraining seeds and per-seed spreads of 0.01–0.12 F1, the study is underpowered to separate the objectives, and we state the crossover as an **ordering of means requiring more seeds to confirm**, not as a finding. We report the table because the mean ordering is stable and informative for future work, and because concealing it would misrepresent what we observed; but no claim in this paper rests on it. The combined objective was carried into the main experiments because it was selected before the ablation was run, not because it was shown to be best.

Two caveats bound how far this section's significance statements should be read. Both scoring defects diagnosed in Sections 3.8 and 4.8 apply to every number in Table 4: F1 is taken at a fixed 0.5 cut, and the runs predate the equal-budget correction, so the 1%-label significance of each objective against from-scratch training inherits exactly the artefact that dissolved the headline claim. The visible symptom is that the combined arm's 1% entry here (0.514 ± 0.055) does not match the pretrained arm's 1% entry in Table 1 (0.478 ± 0.100), which is the same objective under the corrected budget. We did not re-run the ablation under the corrected protocol because its only surviving conclusion is a negative one — that the objectives cannot be separated at this seed count — and that conclusion is robust to the scoring rule, since it rests on overlapping error bars rather than on any arm's absolute score.

**Table 4. Self-supervised objective ablation (deletion F1 at a fixed 0.5 cut, pre-correction protocol; combined = 4 seeds, MAM-only / VICReg-only = 3 seeds; error bars across pretraining seeds).**

| Label fraction | MAM-only | VICReg-only | Combined (MAM+VICReg) |
|---|---|---|---|
| 1% | **0.588 ± 0.117** | 0.554 ± 0.035 | 0.514 ± 0.055 |
| 5% | **0.763 ± 0.060** | 0.665 ± 0.037 | 0.655 ± 0.035 |
| 10% | **0.830 ± 0.068** | 0.768 ± 0.028 | 0.813 ± 0.007 |
| 25% | 0.798 ± 0.083 | 0.845 ± 0.074 | **0.847 ± 0.064** |
| 50% | 0.799 ± 0.107 | 0.903 ± 0.011 | **0.913 ± 0.014** |
| 100% | 0.915 ± 0.014 | 0.846 ± 0.064 | **0.934 ± 0.004** |

The three self-supervised arms and the DeepSV-representation baseline are plotted together in Figure 4. The mean ordering — MAM ahead below 10% labels, the combined objective ahead above 25% — is visible, and so are the overlapping error bars that are the reason we do not claim it.

![Figure 4. Self-supervised objective ablation: MAM-only, VICReg-only, and combined (MAM+VICReg), with the DeepSV-representation baseline for reference. Error bars are standard deviations across independent pretraining seeds. All three self-supervised arms separate clearly from the baseline; they do not separate from one another.]({{artifact:art_c7f8fab3-85e1-4313-9025-0bf9cd1f94e1}})

### 4.6 Cross-ancestry transfer: a suggestive but statistically weak effect

We train on the in-distribution panel and evaluate both in-distribution and on an entirely held-out population (CEU), sweeping the full label fraction (Table 5). These runs predate the label-accounting correction of Section 3.8, and for a label sweep that matters: the low-fraction cells received a batch-size-floored budget rather than the nominal share, so they overstate how little supervision each arm consumed. We report the sweep as it was run and claim nothing from it. Reporting only the extremes, as an earlier version of this analysis did, conceals the structure of the result; we therefore give all six fractions.

Across the sweep, the pretrained model's held-out CEU F1 exceeds the from-scratch model's at five of six fractions — every fraction except 50%, where the direction inverts — but the difference is nominally significant at **only one**: 10% labels (*t* = 3.38, *p* = 0.028) — and that single hit does not survive correction for the six simultaneous tests of the sweep (Holm *p* = 0.169; Section 4.9). We therefore report no significant cross-ancestry effect at any budget. At 1% labels the direction favours pretraining by a wide margin of means (0.518 vs. 0.179) but the from-scratch variance is enormous (± 0.185, one seed of three learning nothing), so the contrast does not reach significance (*p* = 0.11). At 50% labels the direction **inverts** — from-scratch transfers better (0.834 vs. 0.679, *p* = 0.084) — and the generalisation gap likewise inverts at 1% and 50%. With three seeds this analysis is underpowered, and we make no claim that pretraining confers ancestry robustness. The honest summary is that the effect is suggestive at intermediate label budgets, inconsistent in sign across the sweep, and requires a larger multi-ancestry panel with more seeds to establish. It is stated as a limitation (Section 7), not a contribution.

**Table 5. Cross-ancestry transfer, pre-correction protocol (train in-distribution → test held-out CEU, 3 seeds), all label fractions. *p* from Welch's *t*-test on held-out CEU F1 at a fixed 0.5 cut, pretrained vs. from-scratch. These runs predate the label-accounting correction of Section 3.8 in the specific way that matters for a label sweep: the generating evaluator (`scripts/cross_pop_lowlabel.py`) applied a batch-size floor to the budget and drew no validation split, so the low-fraction cells received more labels than the nominal fraction. The evaluator now imports the shared protocol; the table is not regenerated here because the conclusion of Section 4.6 is that no cross-ancestry effect is claimed at any budget.**

| Label fraction | Pretrained CEU F1 | Scratch CEU F1 | *p* | Gap (pre) | Gap (scr) |
|---|---|---|---|---|---|
| 1% | 0.518 ± 0.062 | 0.179 ± 0.185 | 0.110 | +0.024 | −0.074 |
| 5% | 0.638 ± 0.038 | 0.596 ± 0.076 | 0.537 | +0.022 | +0.166 |
| 10% | 0.727 ± 0.057 | 0.542 ± 0.052 | **0.028** | +0.035 | +0.161 |
| 25% | 0.689 ± 0.134 | 0.625 ± 0.057 | 0.584 | +0.107 | +0.204 |
| 50% | 0.679 ± 0.075 | 0.834 ± 0.030 | 0.084 | +0.224 | +0.081 |
| 100% | 0.784 ± 0.028 | 0.742 ± 0.022 | 0.182 | +0.148 | +0.124 |

![Figure 5. Cross-ancestry transfer across the label-fraction sweep. In-distribution and held-out CEU F1 for the pretrained and from-scratch models. The difference is significant at only one fraction (10% labels, p = 0.028); at 1% the means favour pretraining but the from-scratch variance is large (one seed of three learning nothing), and at 50% the direction inverts. Read as a suggestive, underpowered effect, not a robustness claim.]({{artifact:art_9c67fdcc-feb9-4135-86b2-87196632fc61}})

### 4.7 Data-integrity control

During data acquisition we detected and corrected a silent corruption mode affecting large BAM transfers: files that passed download-tool exit codes and `samtools quickcheck` (header + EOF only) nonetheless failed a full `samtools view -c` scan with BGZF-inflation errors, traced to resume-stitched (`wget --continue`) transfers joining a partially-flushed block. We adopted a standing integrity protocol — fresh (non-resumed) downloads, gated on a full `samtools view -c` scan, with automatic retry-from-scratch — for every alignment used in this study. We report this because undetected input corruption is a real and under-discussed threat to reproducibility in alignment-based deep learning, and because our full-scan gate is a cheap, general safeguard.

### 4.8 The label-efficiency result is an artefact of the decision threshold

Every number in Section 4.1 is an F1 obtained by cutting the positive-class probability at 0.5 — the convention this literature inherits from DeepSV. A fixed cut conflates two distinct properties. A model can rank every positive above every negative and still score F1 ≈ 0 if all its probabilities happen to sit below the cut; conversely a model whose scores are well centred can post a respectable F1 while ranking poorly. Label-efficiency claims are claims about representation quality, which is a ranking property, so scoring them at a fixed cut is a category error whenever the arms differ in calibration — and a randomly-initialised network trained on 210 examples differs in calibration from a pretrained one almost by construction.

We therefore re-scored the identical runs and seeds three ways: at the fixed 0.5 cut; at a threshold τ selected to maximise F1 on a validation split carved from the *training* labels (never from test); and threshold-free, by area under the precision–recall curve.

**Table 13. The 1%-label contrast under three scoring rules (uniform benchmark, 210 labels, 3 seeds per arm; *p* from Welch's *t*-test over seeds).**

| Scoring rule | AlignSSL-pretrained | AlignSSL-scratch | Ratio | *p* |
|---|---|---|---|---|
| F1 at fixed 0.5 cut | 0.478 | 0.044 | **10.89×** | **0.009** |
| F1 at selected τ | 0.483 | 0.413 | 1.17× | 0.407 |
| AUPRC (threshold-free) | 0.524 | 0.427 | 1.23× | 0.348 |

The advantage exists under the fixed cut and nowhere else. Under both alternatives the two arms are statistically indistinguishable at the smallest budget, and at each of the five larger budgets the from-scratch arm is *ahead* — significantly so at 5% under both rules (*p* = 0.023 at τ, *p* = 0.015 threshold-free). The from-scratch model was never degenerate: at 210 labels it reaches AUPRC 0.427 against the pretrained model's 0.524, which is a modest deficit, not a collapse. It ranks competently and scores timidly, and the fixed cut reads timidity as failure.

![Figure 6. Pretrained-to-scratch ratio by label budget under two thresholding rules (left), and absolute scores at the smallest budget under all three (right). The ratio departs from parity at exactly one budget under exactly one rule.]({{artifact:art_72cb364e-16f1-446e-9c35-db499a6b8fb3}})

The consequence extends past this paper. Any comparison of initialisation schemes, architectures, or pretraining objectives that reports F1 at a fixed probability cut, and whose arms plausibly differ in calibration, is at risk of reporting a calibration difference as a representation difference. The remedy is cheap: report a threshold-free ranking metric alongside, and select any threshold on held-out training data rather than fixing it a priori. We supply both in `analysis/threshold_sensitivity.py`.

### 4.9 A fourth defect: none of the significance claims carried a multiplicity adjustment

The three defects above are defects of *measurement*. There is a fourth, of *inference*, and it applies to every *p*-value quoted anywhere in this paper including the ones introduced by the corrections themselves.

Each of this paper's significance claims is drawn from a sweep. The label-efficiency contrast is tested at six budgets; the cross-ancestry contrast at six; each candidate-filtered arm pair at six, under two scoring rules. A single nominal hit at α = 0.05 within a family of six simultaneous tests is close to what one expects when nothing is happening — the probability of at least one false positive in such a family is 1 − 0.95⁶ ≈ 0.26. We had reported these tests one at a time.

We therefore pre-declared families — one per sweep, per contrast, per scoring rule — and applied both Holm–Bonferroni, which controls the family-wise error rate, and Benjamini–Hochberg, which controls the false discovery rate (`analysis/apply_multiplicity.py`, output `results/stats_multiplicity.csv`). Across 67 tests in 11 families, 20 are nominally significant, 16 survive BH, and 10 survive Holm.

**Table 16. Claims whose significance does not survive family-wise correction (Holm–Bonferroni at α = 0.05 within the stated family). Full output in `results/stats_multiplicity.csv`.**

| Claim | Family size | Raw *p* | Holm *p* | BH *q* | Fate |
|---|---|---|---|---|---|
| Headline low-label gain, pretrained vs scratch @1%, F1 at fixed 0.5 cut | 6 | 0.009 | 0.055 | 0.055 | lost to multiplicity |
| Scratch ahead @5%, F1 at selected τ | 6 | 0.023 | 0.139 | 0.139 | lost to multiplicity |
| Scratch ahead @5%, AUPRC | 6 | 0.015 | 0.092 | 0.092 | lost to multiplicity |
| Cross-ancestry transfer @10% labels (Section 4.6) | 6 | 0.028 | 0.169 | 0.169 | lost to multiplicity |
| MAM-only vs scratch @1% (Section 4.5) | 7 | 0.017 | 0.069 | 0.030 | survives BH only |
| Convergence at full supervision, combined vs scratch @100% | 7 | 0.025 | 0.074 | 0.034 | survives BH only |

Three consequences, and none of them is comfortable.

First, **the headline claim fails twice over.** Section 4.8 showed that the 1%-label advantage exists only under a fixed probability cut. Table 16 shows that even under that favourable cut, its *p* = 0.009 does not survive correction against the five other budgets it was selected from (Holm *p* = 0.055). The result was never a single test; it was the largest of six, reported alone.

This claim is the one place where the family assignment changes the verdict, and we state it plainly rather than choose. Grouped with the objective-ablation contrasts as `results/stats_multiplicity.csv` also reports it — a family of seven heterogeneous tests, which is how the pre-correction analysis of Section 4.5 was organised — the pre-correction paired-*t* version survives Holm at 0.005. Grouped with the five other budgets of its own sweep, it does not (0.055). The second grouping is the correct one, for a reason that has nothing to do with which answer it gives: the claim was selected *by* being the strongest cell of a budget sweep, so the budget sweep is the family it was selected from. A claim must be corrected against the comparisons that could have produced it, not against a neighbouring set of different questions. We report both numbers so a reader who prefers the other convention can see exactly what it buys.

Second, **the cross-ancestry effect is withdrawn outright.** Section 4.6 already declined to claim ancestry robustness on the grounds that the effect reached significance at only one of six label fractions. Correction settles it: that one fraction was what a family of six produces by chance (Holm *p* = 0.169, BH *q* = 0.169). The ordering of means remains as reported; the significance claim does not.

Third, and pulling the other way, **the corrections' own findings are not immune, but the strongest of them hold.** Two of the three findings of Section 6.3 survive Holm within their own families: the from-scratch arm's advantage over the DeepSV representation on the candidate-filtered benchmark at the three largest budgets (AUPRC Holm *p* = 0.049, 0.049, 0.005), and the pretrained arm's at full supervision (Holm *p* = 0.035). What does *not* survive is any pretrained-versus-scratch contrast on that benchmark under any rule at any budget — consistent with Section 6.3's conclusion that the two are tied there.

The general point is the same one Section 4.8 makes about thresholds, in a different register. A label-efficiency sweep is a multiple-comparison procedure whether or not it is analysed as one. Reporting the single budget at which a difference reaches *p* < 0.05, out of six tested, is a garden-of-forking-paths result presented as a confirmatory one. We have found no deep SV-detection paper that corrects for this, ourselves included until this audit.

---

## 5. Novelty and positioning

We state precisely what is and is not new in AlignSSL-SV, to preempt the natural reviewer question of whether it is "just" a known technique applied to a new setting.

**What is new.** (i) The **benchmark-separability control and its consequence** (Section 4.2). We are not aware of prior work in the SV deep-learning literature that tests a pileup-style benchmark against a deliberately minimal hand-crafted-feature model on identical windows, splits, label fractions and seeds, nor of prior work that measures untrained single-feature discrimination on such a benchmark. The finding — that twelve features reach 96% of their asymptotic AUPRC from 210 labels, and that one depth ratio reaches ROC-AUC 0.955 untrained — is a methodological result that applies beyond this paper, and the candidate-filtering protocol of Section 6 is a concrete, tested partial remedy: it attenuates the shortcut from ROC-AUC 0.955 to 0.717 without changing the positives. (ii) The **image-free, learned alignment representation** — self-supervised pretraining directly on a continuous multi-channel read-alignment tensor, with no pileup-image rendering and no discrete tokenizer. This is the axis on which we differ from the closest prior SSL-for-SV effort, BASILISC (Banerjee, 2026), which pretrains a masked-image-modelling vision transformer over *rendered pileup images* compressed by a discrete VAE (Section 2). Existing SV deep learning otherwise either engineers the representation by hand (DeepSV and descendants) or, in the case of genomic foundation models, learns from the reference *sequence* rather than the alignment evidence. (iii) The **matched-conditions label-efficiency measurement** with error bars computed across independent *pretraining* seeds rather than fine-tuning seeds alone, and with every reported comparison accompanied by an explicit significance test (`results/stats_tests.csv`) — including the tests that fail.

**What we do not claim.** We do not claim a new SV caller, nor deployable accuracy: the control forbids it. We do not claim primacy on "self-supervised learning for structural variants" as a category — BASILISC precedes us. We do not claim that self-supervision improves calibration (the effect is attributable to the representation, and pretrained and from-scratch models are indistinguishable), that one self-supervised objective beats another (*p* > 0.2), that pretraining confers ancestry robustness (significant at 1 of 6 label fractions, with the gap inverting at two), or — following Section 4.8 — that pretraining confers label efficiency at all. Each of these was claimed in an earlier draft of this work and withdrawn when the appropriate test was run. The last of them was this paper's headline.

**What is not new (and we do not claim it is).** Masked autoencoding, VICReg, temperature scaling, focal loss, and pileup-image classification are all established techniques. Their composition on a modality where they had not been combined is a modest engineering contribution, and we do not rest the paper on it.

**No performance claim survives.** An earlier draft of this work claimed label efficiency as the one result that had survived every control. Section 4.8 withdraws it: the effect exists at a fixed 0.5 probability cut and under no other scoring rule. What the paper contributes is therefore the three corrections themselves, the controls that expose them, and the evidence that each is a property of the standard evaluation design rather than of our implementation.

**Relationship to sequence foundation models.** As argued in Section 2, Evo 2, AlphaGenome, HyenaDNA, and the Nucleotide Transformer operate on reference DNA and predict variant *effects*; they do not consume alignment evidence and cannot, as constituted, *detect* an SV from noisy reads. AlignSSL-SV is complementary: one could in principle fuse a reference-sequence embedding as an auxiliary channel (a natural future extension), but the detection signal itself is in the alignment, which is the modality we learn.

---

## 6. A candidate-filtering benchmark: the shortcut is attenuated, and the conclusions change

The control in Section 4.2 identifies the single change that would make results of this kind interpretable, and it is a change to the *task*, not to the model. We therefore re-extracted the labelled set under a **candidate-filtering protocol**: negatives are no longer drawn uniformly from the genome but are chosen to be as close as possible to the positives *on the shortcut statistic itself*. This section reports that benchmark and its outcome. We committed in advance to reporting the result whichever way it fell; it falls partly for and partly against the paper's own method, and we report both halves.

### 6.1 The selection rule

The obvious version of the rule fails. Retaining the windows with the most deletion-like (lowest) centre-versus-flank depth ratio does not remove the shortcut but **inverts** it: a genome-wide lower tail is dominated by mappability dropouts at ratio ≈ 0, whereas heterozygous deletions sit near 0.5, so a classifier learns "very low ratio ⇒ negative" and the feature remains diagnostic with its sign flipped. We measured this directly — extreme-tail selection yields ROC-AUC 0.016 for the depth ratio, as separable as the uniform benchmark and merely reversed.

The rule we adopt instead is **quantile matching within each multi-scale bin**: for every positive, a negative is drawn whose depth ratio falls in the same quantile stratum of the candidate pool, with strata computed separately per window scale because the ratio's meaning depends on span (pooling scales would leak the label through span alone). Candidates come from a one-pass binned coverage profile per chromosome, scored by prefix sums so that exhaustive stride scanning is affordable and the pool genuinely contains mid-range candidates — a uniformly drawn pool does not, which is why the matching must draw from a scan rather than a sample. On the matched training pool the depth ratio measures ROC-AUC 0.504 with near-identical class medians, and this property is asserted by a unit test that gates the extraction job. Positives, window geometry, channel layout, multi-scale binning, chromosome split and shard format are unchanged. The question the benchmark asks becomes the one a caller actually faces: *given that a coverage anomaly was proposed here, is it a real deletion?*

Two constraints on scope must be stated before the numbers. First, a loss of the shared reference directory mid-study left only two of the six panel alignments recoverable, so this benchmark is single-sample: NA20845 (GIH) for training and in-distribution test, with NA12878 (CEU) held out. Second, because both the sample scope and the definition of the negative class differ, absolute F1 is **not** comparable to Table 1; what is comparable is the *ordering* of the arms. The candidate-filtered test set contains 1,516 windows of which 379 are deletions, against 9,196/2,299 for the uniform benchmark, so the error bars here are correspondingly wider.

### 6.2 The shortcut is attenuated, not eliminated

Table 9 repeats the untrained single-feature measurement of Table 6 on the candidate-filtered test set. The headline shortcut falls substantially: the centre-versus-flank depth ratio drops from orientation-corrected ROC-AUC 0.955 to **0.717**. Every other depth-derived feature falls with it (`depth_sd` 0.686 → 0.542, `depth_max_drop` 0.680 → 0.575, `depth_min` 0.657 → 0.597), as do the paired-end signatures that co-vary with a genuine coverage drop (`clip_rate` 0.802 → 0.630, `discordant_rate` 0.732 → 0.607). No single feature now exceeds 0.72, and the strongest is no longer close to solving the task.

But 0.717 is not 0.5. Quantile matching equalises the depth ratio *on the training pool*, and residual separability survives into the held-out chromosomes — partly because matching is per-stratum rather than exact, partly because the matched negatives are real coverage anomalies whose depth profile is similar to but not identical to a deletion's. We report the benchmark as **substantially harder**, not as shortcut-free. A benchmark on which one raw statistic reaches 0.717 still admits a threshold baseline that any deep method should be required to beat.

**Table 9.** Untrained single-feature separability, uniform versus candidate-filtered negatives (orientation-corrected ROC-AUC; source `results/table9_hardneg_single_feature_auc.csv`).

| Feature | Uniform | Candidate-filtered | Change |
|---|---|---|---|
| depth_centre_flank_ratio | 0.955 | **0.717** | −0.239 |
| clip_rate | 0.802 | 0.630 | −0.173 |
| discordant_rate | 0.732 | 0.607 | −0.125 |
| isize_absz_max | 0.694 | 0.566 | −0.128 |
| depth_sd | 0.686 | 0.542 | −0.145 |
| depth_max_drop | 0.680 | 0.575 | −0.105 |
| isize_absz_mean | 0.678 | 0.558 | −0.119 |
| depth_min | 0.657 | 0.597 | −0.059 |
| mapq_mean | 0.550 | 0.558 | +0.008 |
| n_read_rows | 0.538 | 0.508 | −0.030 |
| valid_frac | 0.517 | 0.505 | −0.012 |
| depth_mean | 0.502 | 0.517 | +0.015 |

The clearest statement of why the uniform benchmark could not have measured label efficiency is to run one control on both benchmarks and compare the *shapes* of the two curves (Figure 7). On the uniform benchmark the twelve-feature gradient-boosted tree already reaches AUPRC 0.937 ± 0.009 from 210 labelled windows and gains only **+0.038** over a hundredfold increase in supervision, ending at 0.975 ± 0.001. A benchmark that a cheap baseline nearly saturates at its smallest label budget has no headroom in which any method's label efficiency can be resolved: whatever differences appear between arms are differences in how they behave inside that residual 0.04, not in how much supervision they need. On the candidate-filtered benchmark the same control starts *at* chance (0.250 ± 0.000 with 35 windows, the positive rate being 0.25) and climbs **+0.619** to 0.869 ± 0.006 across a 99-fold budget increase. Supervision buys something there, which is the minimum property a benchmark must have before a label-efficiency claim is even well-posed.

![Figure 7. One hand-crafted-feature control (gradient-boosted tree on twelve alignment statistics), scored threshold-free, on both benchmarks; source `results/table11_control_threshold_free.csv`. On the uniform negatives the control is near-saturated at the smallest budget and gains +0.038 AUPRC over 100x more labels; on candidate-filtered negatives it starts at chance and gains +0.619 over 99x more labels. The argument rests on the shape of the two curves, not their absolute height, so they share a single axis.]({{artifact:art_841002b1-2cf5-4bec-bc28-306c4aef0d7d}})

### 6.3 Every arm falls; two of the three original findings do not survive correction

Table 7 reports the full arm set re-run under the candidate-filtering protocol at identical label budgets and seeds, scored threshold-free (AUPRC) and at a validation-selected threshold. The numbers below are the **corrected** ones: they were regenerated after the protocol and scoring fixes of Sections 3.8 and 4.8, so unlike the earlier version of this subsection they are directly comparable with Tables 12–14. Absolute performance falls for every arm relative to the uniform benchmark — the pretrained model from AUPRC 0.962 to 0.844 at full supervision, the gradient-boosted tree from 0.975 to 0.869 — confirming that the task is genuinely harder and not merely re-labelled.

**Table 7.** Candidate-filtered benchmark, corrected protocol: AUPRC (mean ± sd over 3 seeds for the deep arms, 10 for the classical controls; source `results/table12_label_efficiency_fixed.csv`). Bold marks the best arm at each budget.

| Labels | *n* | AlignSSL (pretrained) | AlignSSL (scratch) | DeepSV repr. | Classical logreg | Classical GBT |
|---|---|---|---|---|---|---|
| 1% | 35 | 0.302 ± 0.053 | 0.283 ± 0.046 | 0.330 ± 0.025 | **0.476 ± 0.076** | 0.250 ± 0.000 |
| 5% | 173 | 0.368 ± 0.072 | 0.359 ± 0.095 | 0.411 ± 0.036 | 0.596 ± 0.025 | **0.626 ± 0.054** |
| 10% | 345 | 0.446 ± 0.024 | 0.510 ± 0.140 | 0.419 ± 0.018 | 0.615 ± 0.026 | **0.719 ± 0.029** |
| 25% | 863 | 0.649 ± 0.024 | 0.734 ± 0.065 | 0.511 ± 0.043 | 0.624 ± 0.016 | **0.803 ± 0.013** |
| 50% | 1726 | 0.722 ± 0.010 | 0.763 ± 0.063 | 0.538 ± 0.040 | 0.629 ± 0.007 | **0.845 ± 0.012** |
| 100% | 3452 | 0.844 ± 0.032 | **0.885 ± 0.022** | 0.656 ± 0.009 | 0.631 ± 0.005 | 0.869 ± 0.006 |

Every arm-versus-arm contrast is tested over seeds in `results/table15_hardneg_arm_contrasts.csv`, on both AUPRC and F1 at the selected threshold. Three findings follow, and only one is the finding this subsection originally reported.

**(i) The pretrained-versus-scratch gap does not survive. This is the second independent failure of the paper's original headline.** Under the corrected protocol the two arms are statistically indistinguishable at *every* label budget on the candidate-filtered benchmark: AUPRC 0.302 ± 0.053 versus 0.283 ± 0.046 at 35 labels (*p* = 0.666), and 0.844 ± 0.032 versus 0.885 ± 0.022 at full supervision (*p* = 0.148), with the from-scratch arm nominally ahead in four of six cells. The earlier version of this subsection reported the opposite — a gap that "survives and sharpens", with the from-scratch model degenerate at 0.000 below 10% labels — and Section 4.8 predicted exactly this outcome: an arm scoring 0.000 at a fixed 0.5 cut is the signature of a model whose probabilities sit below the cut, not of a model that cannot rank. The prediction is confirmed here. At 35 labels the from-scratch arm's F1 is 0.008 at the fixed cut and identical, 0.008, at the “selected” threshold — the two coincide because 35 labels cannot form a validation split, so no selection actually occurs (see the protocol caveat below) — but its AUPRC of 0.283 is within noise of the pretrained arm's 0.302, so the ranking was never the deficient part. The uniform benchmark and the candidate-filtered benchmark now agree: **on this task, self-supervised pretraining does not buy label efficiency.**

**(ii) The learned tensor beats the DeepSV representation, and this finding strengthens under correction.** From 25% labels upward both tensor arms significantly exceed the RGB encoding: at full supervision AUPRC 0.844 ± 0.032 (pretrained) and 0.885 ± 0.022 (scratch) against 0.656 ± 0.009 (*p* = 0.006 and *p* = 0.0008 respectively). This is the one Section 6.3 claim that the correction leaves intact and sharpens — on the uniform benchmark the corresponding contrast at full supervision is smaller. The interpretation is unchanged: the RGB encoding degrades more than the tensor does under candidate filtering, which is what one expects of a representation whose discriminative content was largely the coverage drop the protocol has now equalised. Note that the credit belongs to the *representation*, not to the pretraining — the from-scratch tensor arm carries this result as strongly as the pretrained one.

**(iii) The hand-crafted control leads where labels are scarce, and only there.** Table 14 reduces both families by best-of-family at each budget and tests the difference over seeds. On the candidate-filtered benchmark the control leads significantly at 1% (AUPRC 0.476 ± 0.076 versus 0.330 ± 0.025 for the best deep arm, *p* = 0.0003) and at 5% (0.626 ± 0.054 versus 0.411 ± 0.036, *p* = 0.0004), and the remaining four budgets are ties — including full supervision, where the best deep arm is nominally ahead (0.885 versus 0.869, *p* = 0.329). This is the same shape as the uniform benchmark, where the control also leads at exactly 2 of 6 budgets. The original claim that a hand-crafted control "leads at every label budget" is therefore withdrawn on both benchmarks. What remains — and it is still the paper's most consequential negative result — is that **twelve scalar features remain competitive with a pretrained convolutional–attention encoder across the whole curve, and beat it outright when labels are scarce**, on a benchmark specifically constructed so that no single one of those features exceeds ROC-AUC 0.72.

One protocol caveat must be stated. At the smallest candidate-filtered budget (35 labels) there are too few examples to hold out a validation split, so the threshold-selection rule of Section 3.8 degenerates and F1 at the selected threshold equals F1 at the fixed cut by construction, not by result. That cell's F1 columns are therefore uninformative about thresholding; its AUPRC column is not, and the finding above rests on AUPRC.

![Figure 8. Left: AUPRC versus labelled-data fraction on the candidate-filtered benchmark under the corrected protocol, the direct analogue of Figure 7 on the harder task. Right: untrained single-feature separability on the uniform and candidate-filtered benchmarks, paired per feature; the depth shortcut is attenuated from 0.955 to 0.717 but not removed.]({{artifact:art_0b8b1b59-6de7-4036-bebf-cef7955b70ed}})

### 6.4 What this changes

The pre-registered question was whether pretraining's low-label advantage would survive a benchmark in which the depth shortcut is uninformative. With the corrected protocol the answer is unambiguous and negative on both counts: **the advantage over from-scratch training does not survive, and the advantage over hand-crafted features does not appear.** The candidate-filtered benchmark was built to be the fair test of the paper's original claim, and the claim fails it — independently of, and consistently with, the thresholding analysis of Section 4.8 on the uniform benchmark. Two independent lines of evidence now reach the same conclusion, which is stronger grounds for withdrawal than either alone.

Three things survive, and they are what the paper contributes.

First, **the benchmark-construction result**: quantile-matched candidate negatives attenuate the depth shortcut from orientation-corrected ROC-AUC 0.955 to 0.717 without altering the positive set, and the naive version of the same rule — selecting the most deletion-like negatives — *inverts* the shortcut rather than removing it (Section 6.1). This does not depend on any scoring or budget convention and is directly reusable by anyone building a short-read SV benchmark.

Second, **the representation result**: a continuous multi-channel alignment tensor significantly outperforms a DeepSV-style RGB pileup encoding from 25% labels upward on the harder benchmark, and the effect is carried by the representation rather than by the pretraining.

Third, **the negative result about hand-crafted controls**, in its corrected and narrower form: on a benchmark where no single feature exceeds ROC-AUC 0.72, twelve scalar features still lead every deep arm in the label-scarce regime and tie it elsewhere. A field that reports deep SV callers without this control cannot distinguish a learned representation from a threshold.

Candidate filtering by quantile matching is a necessary but not sufficient benchmark repair; a fully shortcut-free protocol will likely require matching on a vector of alignment statistics rather than on the single strongest one. Two extensions remain deferred: a coverage-robustness experiment (downsampling via `samtools view -s`) and a Truvari-based comparison against GIAB HG002 curated calls, which provides an orthogonal truth set free of the consensus-caller circularity of the 1000 Genomes call set. Both become worthwhile now that a non-degenerate benchmark exists; neither would have been informative on the uniform one.

---

## 7. How general are these defects? A coded audit of the deep short-read SV literature

Sections 4, 6 and 8 report defects in *our own* pipeline. That is only worth a
reader's time if the defects are properties of the field's default evaluation
design rather than of one implementation. Elsewhere in this manuscript we
previously asserted that they are widespread. An assertion is not evidence, so
we measured it.

### 7.1 Population and inclusion rule

We started from the 62-paper survey assembled for this project's related-work
review and applied a pre-registered two-part rule: include a paper if and only
if (a) it trains a classifier — deep or shallow — whose input is derived from
read alignments, and (b) its prediction target is a structural variant. Papers
were excluded for a recorded reason: target is SNV or short indel rather than SV
(9, including one correction made after reading the full text of a paper whose
survey row had filed it under the SV theme); no trained classifier, i.e.
heuristic, statistical, assembly- or *k*-mer-based (9); benchmark or truth-set
paper rather than a method (5); review or survey (10); genomic language model
whose target is not SV (10). The rule admits 19 papers spanning 2017–2025,
including the DeepSV paper this work extends. Of these, 14 had a
full text we could retrieve through open-access routes; 5 were paywalled
with no available route and are recorded as uncoded rather than guessed at. The
coded set spans 7 venues (BMC Bioinformatics × 4, Briefings in Bioinformatics × 3, Nature Methods × 2, Bioinformatics × 2, Frontiers in Genetics × 1, bioRxiv (preprint) × 1, Nature Biotechnology × 1).
The full population with per-row inclusion status and reason is
`results/table17_audit_population.csv`.

### 7.2 Coding procedure

Each paper was coded on the four axes corresponding to the four defects
documented here: (A) how negative training examples were obtained
(matched / caller candidates / simulated / uniform-random / not stated);
(B) how the decision threshold behind the headline metric was chosen
(threshold-free / tuned on a validation split / fixed default / not stated);
(C) whether any model-free control — a hand-crafted-feature classifier, a
single-feature separability measurement, or an equivalent non-learned reference —
was reported (comparison against another published *learned* caller does not
count); (D) whether multiple significance claims received any family-wise
correction. Codes were constrained to the enumerated values by a forced output
schema rather than parsed from free text, and every code was required to carry a
supporting quotation. Each of the 56 quotations was then verified
mechanically to be a literal span of its own source document after Unicode and
line-break normalisation; codes whose quotation could not be located were
re-coded against a stricter verbatim instruction and re-verified, and the three
that changed under re-coding were changed toward *less* confident codes, never
toward a defect. All 56 codes in the final table carry a verified
quotation; the quotations are released in
`results/table19_field_audit_quotes.csv` so that every code in this section can
be checked against its source.

Coding a paper as omitting a safeguard means the paper does not report it. We
distinguish this from *not stating* a protocol, which we count separately rather
than folding into the defect count.

### 7.3 Result

| Paper | Year | Venue | Negative sampling | Threshold rule | Model-free control | Multiplicity | Safeguards omitted |
|---|---|---|---|---|---|---|---|
| Cai et al. 2019 | 2019 | BMC Bioinformatics | not stated | not stated | no | none | 2 |
| Luo et al. 2021 | 2021 | BMC Bioinformatics | not stated | fixed 0.5 | no | none | 3 |
| Lin et al. 2022 | 2022 | Nature Methods | not stated | fixed 0.5 | no | none | 3 |
| Luo et al. 2023 | 2023 | Frontiers in Genetics | not stated | fixed 0.5 | no | none | 3 |
| Ma et al. 2023 | 2023 | BMC Bioinformatics | caller candidates | fixed 0.5 | no | none | 3 |
| Popic et al. 2023 | 2023 | Nature Methods | not stated | fixed 0.5 | no | none | 3 |
| Zheng & Shang 2023 | 2023 | BMC Bioinformatics | matched | fixed 0.5 | yes | none | 2 |
| Hu et al. 2024 | 2024 | Briefings in Bioinformatics | not stated | fixed 0.5 | no | none | 3 |
| Linderman et al. 2024 | 2024 | Bioinformatics | simulated | fixed 0.5 | no | seeds, uncorrected | 4 |
| Santuari et al. 2024 | 2024 | bioRxiv (preprint) | caller candidates | fixed 0.5 | no | none | 3 |
| Wang et al. 2024 | 2024 | Nature Biotechnology | not stated | fixed 0.5 | yes | none | 2 |
| Xia et al. 2024 | 2024 | Bioinformatics | simulated | fixed 0.5 | no | none | 4 |
| Gao et al. 2025 | 2025 | Briefings in Bioinformatics | not stated | not stated | no | none | 2 |
| Guo et al. 2025 | 2025 | Briefings in Bioinformatics | not stated | not stated | no | none | 2 |

**Table 17. Coded evaluation design of the 14 retrievable papers in the audit
population. "Safeguards omitted" counts the strict defects only — documented
easy negatives, a documented fixed threshold, absence of a model-free control,
and absence of multiplicity correction — and does not penalise a paper for
failing to state its protocol. Full quotations in
`results/table19_field_audit_quotes.csv`.**

The four axes behave differently.

**No coded paper corrects for multiplicity.** All 14 coded
papers apply no family-wise correction to any significance claim.
1 reports multi-seed variability without correcting; the remaining
13 report neither.

**A model-free control is nearly as rare.** 12 of 14
report no non-learned reference of any kind. The 2 exceptions are
Zheng & Shang 2023 and Wang et al. 2024. Without such a control, a paper cannot
distinguish what its architecture contributes from what its benchmark gives
away — which is exactly the measurement that changed this project's conclusion
(Section 4.2).

**Thresholding is dominated by the fixed 0.5 cut.** 11 of 14
papers report their headline metric at a fixed default probability cut, and
3 do not state a rule. No paper in the population reports its headline
comparison threshold-free. As an independent mechanical check, we searched each
full text for any mention of a threshold-free metric (AUC, AUROC, AUPRC,
average precision, precision–recall curve):
10 of 14
never mention one anywhere in the paper.

**Negative-sampling protocol is most often simply not stated.** Only
5 of 14 papers state how their negative
training examples were obtained: 2 draw them from
caller candidates, 2 from simulation, and
1 — Zheng & Shang 2023 — matches negatives to positives.
The remaining 9 do not say. We count non-statement as a
reporting failure rather than as evidence of easy negatives, which is why the
strict defect count in Table 17 is conservative: it credits a paper with the
safeguard whenever the text is silent.

Taken together, no coded paper reports all four safeguards, and none
omits fewer than two. 9 of 14 omit at
least three on the strict count, and 2 omit all four.
Under the lenient count that treats non-statement as omission,
10 of 14 omit all four.

![Figure 9. Left: the fraction of audited papers exhibiting each of the four evaluation practices. Right: per-paper count of safeguards omitted on the strict definition, which does not penalise a paper for failing to state its protocol. Population: 14 retrievable full texts from the 19 papers that meet the inclusion rule, 2019–2025. Sources and quotations in `results/table18_field_audit.csv` and `results/table19_field_audit_quotes.csv`.]({{artifact:art_50ca4ee6-e9c3-41f5-a745-8eed2ac1ff40}})

### 7.4 What this does and does not license

It licenses the generality claim in a bounded form: the four defects documented
in this manuscript are not idiosyncratic to our pipeline. Among the 14 papers we
could retrieve and code, three of the four axes are absent in at least 11.

Three boundaries on that statement. First, the population is a **convenience
sample** drawn from this project's related-work survey rather than a systematic
search; an independent 2,334-record corpus screen identified five apparently
eligible short-read SV papers absent from it, which leaves the *majority* claim
below provisional (Section 8). Second, 5 of the 19 eligible papers were
paywalled and are uncoded, so the coded set may be non-representative in an
unmeasured direction. Third, "the paper does not report it" is not "the authors
did not do it": coding is bounded by what a paper states. Accordingly we claim
that these safeguards are **rarely reported** in this literature, not that they
are never performed, and the per-axis counts should be read as statements about
the 14 coded papers rather than as field-wide rates.

It does not license a claim that the affected papers' *conclusions* are wrong.
We did not re-run any of them. Section 4.2 shows that a benchmark can be
substantially solvable by a single untrained scalar without that being visible
in any reported number; the audit shows that most papers in this literature
would not have detected such a leak had it been present, because they report no
control that could. Those are different claims and only the second is supported
here.

Three further limits apply. The population is drawn from one project's survey
and is therefore not a systematic PRISMA-style review; a differently-assembled
corpus would give somewhat different counts, though the near-unanimity on axes
C and D leaves little room for the direction to reverse.
5 eligible papers were paywalled and are uncoded, so the denominator
is retrievable papers, not eligible papers. And a coding of what a paper
*reports* is not a coding of what its authors *did*: a paper may have matched
its negatives and not said so. Every consequence of that ambiguity has been
resolved in the audited papers' favour.

## 8. Limitations

- **Benchmark separability (governing limitation).** The evaluation task, built with uniformly-sampled negatives as is standard in this literature, is separable by a single depth heuristic at ROC-AUC 0.955, and twelve hand-crafted features reach 96% of their asymptotic AUPRC from 210 labels (Section 4.2). Every accuracy number in this paper must be read as a measurement on that task, not as deployable caller performance. This is the reason the paper's contribution is framed as a representation-learning and benchmarking result rather than as a new SV caller.
- **No comparison against production callers.** We compare learned representations under matched conditions; we do not compare against Manta, DELLY, LUMPY, GRIDSS or similar, because a comparison on a separable benchmark would favour whichever method best exploits the shortcut and would be uninformative.
- **Statistical power and multiplicity.** Three to four pretraining seeds per arm are not sufficient to rank the self-supervised objectives against one another (*p* > 0.2, Section 4.5), to establish cross-ancestry transfer (nominally significant at 1 of 6 label fractions and not after correction, Sections 4.6 and 4.9), or — as Section 4.8 shows — to distinguish the pretrained and from-scratch arms at any budget once scoring is threshold-free. Those analyses are reported as orderings of means, not findings. The one contrast that *did* reach significance at this seed count is the one we withdraw, which is itself a caution: a small-*n* design that produces a *p* = 0.009 under one scoring rule and *p* = 0.348 under another — and 0.055 once corrected for the sweep it was selected from — has not measured a stable effect. A related limitation of the correction itself: Holm and BH assume the tests within a family are exchangeable, whereas budgets within a sweep share seeds, encoders and test windows and are therefore positively dependent. Both procedures remain valid under positive dependence (BH provably so, Holm conservatively), but the adjusted values should be read as conservative bounds rather than exact.
- **Scope.** Deletions and short reads only. Insertions, duplications, inversions, translocations and long-read data are out of scope, though the framework is not deletion-specific by construction.
- **Truth set.** The 1000 Genomes phase-3 integrated SV call set is itself a consensus of callers and carries its own error; a curated orthogonal benchmark (GIAB HG002) remains deferred (Section 6.4).
- **No demonstrated value from pretraining.** Under the corrected protocol and threshold-free scoring, the pretrained arm does not significantly exceed from-scratch training at *any* label budget on the uniform benchmark, and is significantly behind at 5% (Section 4.8). We report the pretraining machinery because it is the object the paper set out to evaluate, not because the evaluation vindicated it.
- **Single-panel pretraining corpus.** The unlabelled pretraining corpus comes from three samples; corpus-size and diversity scaling are untested.
- **Candidate filtering is a partial repair, and its benchmark is single-sample.** The repaired benchmark of Section 6 attenuates the depth shortcut to ROC-AUC 0.717 but does not eliminate it; a threshold baseline on the residual signal remains available to any method. It is also single-sample — NA20845 (GIH) for train and in-distribution test, NA12878 (CEU) held out — with 1,516 test windows against 9,196 for the uniform benchmark, because a mid-study loss of the shared reference directory left only two of the six panel alignments recoverable. Section 6's error bars are correspondingly wider than Section 4's, and with three seeds per deep arm its ties should be read as *underpowered* rather than as demonstrated equivalence: the pretrained-versus-scratch contrast at full supervision (*p* = 0.148) would need more seeds to exclude a small effect. What that section can support is the absence of the *large* low-label advantage originally claimed, which the uniform benchmark independently rejects at ten times the test-set size.
- **The field audit's population is a convenience sample, and its majority claim is not robust to that.** The 19-paper audit population of Section 7 was derived from the 62-paper related-work survey assembled for this project, not from a systematic pre-registered search. To test its completeness we screened an independently assembled 2,334-record corpus (OpenAlex phrase queries, citation-graph expansion from anchor callers, and PubMed, restricted to 2018+) against Section 7's own inclusion rule, and found five short-read SV papers that appear eligible and are absent from the population: `10.1093/bib/bbaa370`, `10.1534/g3.119.400596`, `10.1038/s41551-022-00980-5`, `10.1101/gr.274845.120`, and `10.1186/s12920-020-00733-w` (eligibility judged from abstracts only; full-text coding would be required to confirm). This matters for one specific claim. The universal findings are unaffected in direction — an additional five papers cannot make "14 of 14 apply no multiplicity correction" false for the papers already coded — but the *majority* claim is fragile: "9 of 14 omit at least three safeguards" (0.64) becomes 9/19 = 0.47 if all five newly identified papers turn out to omit none, and 14/19 = 0.74 if all five omit three or more. Because the adversarial case crosses one half, **Section 7's majority claim should be read as provisional pending full-text coding of those five papers**, while its per-axis counts remain statements about the 14 papers actually coded. We report this rather than re-running the audit because the five full texts were not retrievable within this study, and a partial re-code would substitute a different unquantified bias for a stated one. The screen is released as `results/table21_audit_completeness_screen.csv`.
- **Single coverage regime.** All alignments are high-coverage (~30x) PCR-free Illumina. Robustness to lower coverage, PCR-positive libraries, or different read lengths is untested; the depth-derived channels are the ones most likely to be coverage-sensitive.
- **One held-out population.** Cross-ancestry generalisation is measured against a single held-out population (NA12878, CEU). A single held-out ancestry cannot distinguish population-specific transfer loss from sample-specific idiosyncrasy.

---

## 9. Conclusion

We set out to test whether learning the alignment representation and pretraining it without labels improves the bottlenecks DeepSV left open. The first answer we obtained was affirmative and quantitatively striking: at 1% of labels, self-supervised initialisation delivered roughly a ten-fold F1 improvement over the identical architecture trained from scratch, significant at *p* = 0.009. That is the result this paper was written to report, and it does not survive.

It fails four controls, none of which is exotic:

1. **Benchmark separability.** Twelve scalar alignment features on the identical windows reach AUPRC 0.937 from 210 labels and gain only +0.038 from a hundred-fold increase in supervision, and a single centre-versus-flank depth ratio separates the classes at ROC-AUC 0.955 with no training at all. The cause is the uniformly-sampled negatives standard in this benchmark family. A task that is 96% solved by twelve features after 210 examples cannot discriminate between representations.
2. **Unequal label budgets.** A batch-size floor in our own deep evaluators granted the deep arms up to 2.8× the labels the classical control received, concentrated in precisely the low-label cells that carry the headline claim.
3. **The decision threshold.** Scoring F1 at a fixed 0.5 probability cut — the convention inherited from DeepSV — conflates ranking quality with calibration. Re-run under equal budgets and re-scored at a validation-selected threshold or threshold-free, the ten-fold gap becomes 1.17× (*p* = 0.407) and 1.23× (*p* = 0.348) respectively; at every larger budget the from-scratch arm is ahead. The from-scratch model was never degenerate. It ranked competently and scored timidly, and a fixed cut reads timidity as failure.
4. **Multiplicity.** The *p* = 0.009 was the strongest cell of a six-budget sweep, reported as though it were a single test. Corrected for the family it was selected from, it is 0.055 — so even under the favourable scoring rule that produces it, it does not clear 0.05. Across the whole paper, 20 nominally significant tests in 11 pre-declared families reduce to 10 under Holm–Bonferroni, and the cross-ancestry effect reduces to chance.

Each defect is individually mundane, each is the default in this literature — no paper in the audited population reports all four safeguards and 9 of 14 omit at least three (Section 7) — and each is invisible without the control that exposes it. Three concern how the numbers were measured; the fourth concerns how they were tested. Jointly they were sufficient to manufacture a large, statistically significant, entirely artefactual headline result — one we believed, wrote up, and would have submitted.

What survives is narrower and, we think, more useful. Where labels are scarce — the regime self-supervised pretraining is proposed for — no deep arm we trained beats twelve hand-crafted features on either benchmark. Repairing the benchmark helps but does not rescue the claim: quantile-matched candidate negatives attenuate the shortcut from ROC-AUC 0.955 to 0.717 and restore headroom (the same control now starts at chance and climbs +0.619 across the label range), yet the control still leads where it matters. And the corrections cut in both directions: at full supervision on the uniform benchmark the from-scratch network narrowly *beats* the control (AUPRC 0.979 vs 0.975, *p* = 0.003), a reversal of an earlier claim of ours that the control dominated everywhere.

We therefore do not offer a new SV caller, and we make no performance claim. We offer four controls, the code that implements them, and a worked demonstration of what their absence costs. Before the next architecture is proposed for short-read deletion calling, we would ask of it the four questions this paper failed: what does a hand-crafted-feature model score on the same windows, do all arms receive the same labels, does the result survive a change of decision threshold, and does its significance survive correction for the sweep it was selected from.

---

## Data and code availability

The tensor-extraction pipeline, encoder and head implementations, pretraining and fine-tuning scripts, cluster job scripts, aggregation and manuscript-reconciliation tooling, result tables, and figures are available at https://github.com/aayushkrm/AlignSSL-SV under the MIT licence. Trained encoder checkpoints are available from the author on request pending a Zenodo deposit. Sequencing data are from the 1000 Genomes Project (high-coverage PCR-free alignments, GRCh37/hs37d5) and are publicly available from the EBI 1000 Genomes FTP. The deletion truth set is the 1000 Genomes phase-3 integrated SV call set.

The full texts coded in Section 7 are the published articles cited in Table 17; they are not redistributed here. `results/table19_field_audit_quotes.csv` releases the verbatim span supporting each of the 56 codes so that every coding decision can be checked against its source without access to a subscription.

## Declarations

**Ethics approval and consent to participate.** Not applicable. This study analyses only publicly released, de-identified sequencing data from the 1000 Genomes Project, for which consent for open data release was obtained by the original consortium. No new human or animal data were collected.

**Consent for publication.** Not applicable.

**Competing interests.** The author declares no competing interests.

**Funding.** This work received no dedicated funding. Computation was performed on a university high-performance-computing cluster under a standard student allocation.

**Author contributions.** A.K. conceived the study, implemented the pipeline, designed and executed the evaluation and its corrections, performed the literature coding of Section 7, and wrote the manuscript.

**Acknowledgements.** The author thanks the operators of the university HPC facility. A partial loss of a shared scratch filesystem during the study restricted the candidate-filtered benchmark to two samples; this is recorded in Section 8.

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
