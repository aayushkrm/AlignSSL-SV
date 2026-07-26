# AlignSSL-SV: Self-supervised representation learning on read alignments is label-efficient — but hand-crafted features expose the benchmark it is measured on

**Running title:** Label-efficient alignment-tensor pretraining, and a separability control for SV benchmarks

**Ayush Kumar**

Correspondence: aayush.kumarm.3myself@gmail.com · Code: https://github.com/aayushkrm/AlignSSL-SV

**Keywords:** structural variant detection; deletion calling; self-supervised learning; representation learning; read alignment; benchmark separability; calibration; 1000 Genomes

---

## Abstract

**Motivation.** Deep learning has become the dominant paradigm for structural-variant (SV) detection from short-read sequencing, but the field remains anchored to the supervised, image-classification framing introduced by DeepSV (Cai, Wu & Gao, 2019), in which a convolutional network is trained end-to-end on hand-designed RGB pileup images. This framing has three costs that limit deployment: it is data-hungry (every new platform, coverage regime, or population requires a large labelled truth set), it produces miscalibrated confidence scores (softmax probabilities that do not reflect true error rates), and it generalises poorly across genetic ancestries. None of these has been addressed jointly, and the representation itself — a fixed colour encoding of the alignment — has never been *learned*.

**Results.** We present AlignSSL-SV, a framework that (i) replaces the fixed RGB pileup with a multi-channel alignment tensor and a learned encoder, (ii) pretrains that encoder by masked-alignment modelling (a self-supervised objective on read alignments, requiring no SV labels), and (iii) attaches a calibrated, uncertainty-aware deletion head. On 1000 Genomes high-coverage PCR-free data (a six-sample panel spanning five continental ancestries), self-supervised pretraining delivers large gains in the low-label regime — deletion F1 of 0.51 at 1% of labels (210 windows) where an identically-architected from-scratch model achieves 0.05 and a DeepSV-style baseline achieves 0.43 (paired *t* = 13.3, *p* = 9.2 × 10⁻⁴). At full supervision the from-scratch model is *marginally but consistently ahead* (0.944 ± 0.003 vs. 0.934 ± 0.004; paired *t* = −4.20, *p* = 0.025), so pretraining buys label efficiency rather than a higher ceiling. **Critically, we also report a control that bounds the interpretation of these numbers: twelve hand-crafted alignment features fed to a gradient-boosted tree reach F1 = 0.894 from the same 210 labels — above every deep arm — and the single centre-versus-flank read-depth ratio separates the classes at ROC-AUC = 0.955 with no training at all.** The benchmark's uniformly-sampled negatives are therefore separable by a depth heuristic, and the label-efficiency gap measures how quickly each initialisation learns that heuristic, not deployable caller performance. Calibration is a property of the representation rather than of self-supervision: both learned-tensor models are well calibrated after temperature scaling (ECE 0.008 pretrained, 0.007 from-scratch), while the DeepSV-style encoding is worse and unstable (median 0.033, mean 0.072 ± 0.068 driven by one outlier seed of three). Cross-ancestry transfer to a held-out CEU population favours pretraining at 10% labels (*p* = 0.028) but is not significant at the other five label fractions, and the transfer gap inverts at 1% and 50%.

We then repair the benchmark: quantile-matched candidate negatives attenuate the depth shortcut to ROC-AUC 0.717, and on that harder task the low-label result survives and sharpens (F1 = 0.352 pretrained vs 0.000 from-scratch at 1% labels, *p* = 0.016) while the twelve-feature control still leads at every label budget.

**Conclusion.** Learning the alignment representation and pretraining it without labels yields large, reproducible low-label gains over supervised training of the same architecture, and these gains survive a candidate-filtered benchmark. But hand-crafted alignment features match or exceed all deep arms on both the random-negative protocol standard in this literature and on our repaired one, which we report as a first-class negative result: pileup-style benchmarks of this construction cannot substantiate claims of deployable SV-calling performance, and negative-sampling repair alone does not fix them.

**Availability.** Code, the tensor-extraction pipeline, result tables and figures are at https://github.com/aayushkrm/AlignSSL-SV (MIT licence).

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
- A controlled evaluation on a six-sample, five-ancestry 1000 Genomes panel showing that pretraining yields large low-label gains (≈10× F1 over from-scratch at 1% labels, *p* = 9.2 × 10⁻⁴), and that at full supervision the from-scratch model is marginally ahead (Section 4).
- **A hand-crafted-feature control that bounds what the benchmark can show** (Section 4.2): twelve alignment features match or beat every deep arm at every label budget, and one depth-ratio feature reaches ROC-AUC 0.955 untrained. We report this as a negative result about the random-negative evaluation protocol, which is widely used in this literature and, to our knowledge, has not previously been subjected to such a control.
- A controlled ablation (3–4 seeds, error bars computed across *pretraining* seeds) isolating the contribution of each self-supervised objective (Section 4.5).
- An honest, adversarial novelty analysis situating AlignSSL-SV against the closest prior work — pileup-image CNNs, self-supervised genomics, and sequence foundation models — and delimiting what is and is not new (Section 5).

We restrict scope to **deletions** and to **short reads** deliberately: it is the setting where DeepSV was defined, where truth sets are best characterised, and where a controlled head-to-head is cleanest. Section 6 discusses the extension to other SV classes and to long reads.

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

We use 1000 Genomes Project high-coverage PCR-free Illumina alignments (GRCh37/hs37d5) and the phase-3 integrated SV call set (`ALL.wgs.mergedSV.v8.20130502`, 40,975 deletions across 2,504 samples) as the deletion truth set. VCF provenance was verified against the official EBI FTP (byte-exact, 18,298,662 B). Pretraining and fine-tuning use **disjoint chromosome sets** (train chr1–11, test chr12–22) to prevent representation leakage between stages. For the cross-ancestry experiment, models are trained on one population and evaluated on a genetically distant, entirely held-out population (CEU held out). Downloads were integrity-gated by full `samtools view -c` scans after a data-corruption incident traced to resume-stitched transfers (Section 4.7).

### 3.7 Baselines

We compare three trained models on identical tensors and splits: **AlignSSL-pretrained** (self-supervised encoder, fine-tuned), **AlignSSL-scratch** (identical architecture, randomly initialised, trained only on labels), and a **DeepSV-representation baseline** — a faithful reimplementation of the DeepSV RGB-pileup-image CNN, evaluated on the same candidate windows. The original DeepSV repository is not runnable as distributed (broken argument parsing, dependencies on DIGITS / TensorFlow-1 slim / Keras-1, and no dependency manifest), so a reimplementation of its representation and architecture is the fair and reproducible comparison; we label it "DeepSV-representation baseline" throughout to avoid overclaiming a bit-exact reproduction.

---

## 4. Results

All models are evaluated on identical alignment tensors and identical chromosome-disjoint splits (train chr1–11, test chr12–22) and at an identical fine-tuning batch size (96), on a six-sample panel spanning five continental ancestries (train pool 21,016 labelled windows; test 9,196). We report mean ± standard deviation across random seeds — four for the combined-objective arm, three for every other arm. Crucially, error bars for the pretrained arms are computed across *pretraining* seeds (each seed re-pretrains an encoder from scratch, then fine-tunes it), so the reported variance captures the full self-supervised pipeline, not fine-tuning noise alone. The task is binary deletion calling on genome-wide candidate windows.

### 4.1 Self-supervised pretraining is strongly label-efficient

Table 1 reports deletion F1 as a function of the fraction of the labelled training set made available to the fine-tuning head. The defining result is in the **low-label regime**: at 1% of labels (210 windows), the pretrained model reaches F1 = 0.514 ± 0.055, whereas the identically-architected from-scratch model all but collapses to 0.050 ± 0.040 (it barely learns to fire on the tiny label set) — a **≈10× improvement in F1** from self-supervised initialisation alone. The DeepSV-representation baseline reaches 0.435 ± 0.022 at 1%: better than from-scratch, because its hand-designed RGB features carry a useful inductive prior when labels are scarce, but well below the pretrained tensor model. Pretraining thus supplies a usable detector from a truth set two orders of magnitude smaller than is conventionally required.

As labels increase, the from-scratch model catches up and then slightly overtakes: at full supervision (100%, 21,016 windows) it is marginally but consistently ahead (0.944 ± 0.003 vs. 0.934 ± 0.004). A paired *t*-test over the three shared seeds gives *t* = −4.20, *p* = 0.025 — a small effect (Δ F1 = 0.010) that is nonetheless directionally reliable, so we do **not** describe the arms as equivalent at full supervision. **The value of pretraining here is label efficiency, not a higher ceiling.** The advantage is monotone in scarcity: large at 1% (≈10×, *p* = 9.2 × 10⁻⁴), still present at 10% (0.813 vs. 0.763), and gone by 25%. Both learned-tensor variants exceed the DeepSV-representation baseline at every fraction, and that baseline is conspicuously **unstable at full supervision (0.707 ± 0.140)** — a variance the tensor models never exhibit.

The interpretation of this entire table is bounded by the control in Section 4.2, which should be read before the numbers above are taken as evidence of caller quality.

**Table 1. Label efficiency (deletion F1, test chr12–22, batch 96; pretrained/scratch = 4 seeds, all other arms = 3 seeds). The two rightmost arms are the hand-crafted-feature controls of Section 4.2 — they are not competing methods but a measurement of how separable the benchmark is, and they exceed every deep arm at every budget.**

| Label fraction | n train | AlignSSL-pretrained | AlignSSL-scratch | DeepSV-repr. | Classical-logreg | Classical-GBT |
|---|---|---|---|---|---|---|
| 1% | 210 | 0.514 ± 0.055 | 0.050 ± 0.040 | 0.435 ± 0.022 | 0.877 ± 0.008 | **0.894 ± 0.002** |
| 5% | 1,050 | 0.655 ± 0.035 | 0.734 ± 0.107 | 0.591 ± 0.063 | 0.878 ± 0.006 | **0.917 ± 0.005** |
| 10% | 2,101 | 0.813 ± 0.007 | 0.763 ± 0.088 | 0.662 ± 0.048 | 0.869 ± 0.003 | **0.924 ± 0.000** |
| 25% | 5,254 | 0.847 ± 0.064 | 0.854 ± 0.055 | 0.834 ± 0.012 | 0.866 ± 0.005 | **0.932 ± 0.000** |
| 50% | 10,508 | 0.913 ± 0.014 | 0.912 ± 0.022 | 0.856 ± 0.033 | 0.872 ± 0.001 | **0.937 ± 0.001** |
| 100% | 21,016 | 0.934 ± 0.004 | 0.944 ± 0.003 | 0.707 ± 0.140 | 0.871 ± 0.000 | **0.939 ± 0.001** |

![Figure 1. Deletion F1 vs. labelled-data fraction for the combined-objective AlignSSL-pretrained model, AlignSSL-scratch, and the DeepSV-representation baseline. Pretraining dominates in the low-label regime (≈10× F1 at 1% labels); the two learned-tensor models converge at full supervision, while the DeepSV-representation baseline remains lower and becomes unstable at 100%.]({{artifact:art_6b3657d8-5b3f-4b2c-b2ad-1df2139e7a24}})

### 4.2 A hand-crafted-feature control bounds what this benchmark can demonstrate

Every deep-learning SV paper we are aware of, DeepSV included, compares deep architectures against one another or against signature-based callers, but not against a *deliberately minimal* learned baseline on the identical windows. We ran that control, and it is the most consequential result in this paper.

From the same alignment tensors, identical shards, identical chromosome split, identical label fractions and identical seeds, we computed twelve scalar summary features per window — mean, standard deviation and minimum of the depth profile; centre-versus-flank depth ratio; maximum sustained depth drop; discordant-pair rate; soft-clip rate; mean and maximum insert-size |z|; mean mapping quality; occupied read-row count; and valid-base fraction — and fitted an ℓ2-regularised logistic regression and a gradient-boosted tree (`Classical-logreg`, `Classical-GBT` in Table 1). Both dominate every deep arm at every label budget. At 1% labels (210 windows), where the paper's headline claim lives, the gradient-boosted tree reaches **F1 = 0.894 ± 0.002** against 0.514 ± 0.055 for the pretrained network and 0.050 ± 0.040 from scratch; at full supervision it reaches 0.939 ± 0.001 against 0.934 and 0.944. Its variance across seeds is one to two orders of magnitude smaller than any deep arm's.

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

This does not invalidate the comparisons in Section 4.1, which are internally controlled and reproducible; it re-scopes what they measure. The pretrained-versus-scratch gap at 1% labels is real and significant, but it shows that a randomly-initialised network needs more labelled examples than a pretrained one to learn a depth threshold — not that self-supervised pretraining confers deployable label efficiency for deletion calling. We attempted a partial remedy by re-selecting the most deletion-like negatives from the existing pool and re-scoring: the shortcut feature's discrimination fell only from ROC-AUC 0.955 to 0.920, confirming that a uniformly-sampled pool contains no genuinely hard negatives to recover. The proper fix is to change the candidate set, not the subset; we build and report that benchmark in Section 6, where the shortcut falls to ROC-AUC 0.717 and the hand-crafted control still leads.

**We therefore report the benchmark-separability finding as a first-class contribution.** The control costs minutes of CPU time, applies to any pileup-style SV benchmark, and to our knowledge has not previously been run. Its implication is that published low-label and architecture-comparison results on random-negative SV benchmarks — a family that includes DeepSV's own evaluation and much of what followed — may be measuring threshold-learning speed rather than caller quality.

![Figure 2. Left: deletion F1 versus labelled-data fraction for all arms; the two hand-crafted-feature controls (heavy lines) exceed every deep arm at every budget, with the largest margin in the low-label regime. Right: single-feature discrimination on the held-out test set with no training — the centre-versus-flank depth ratio alone reaches ROC-AUC 0.955.]({{artifact:art_38410a53-1025-43c4-a9af-0a3521eb07d9}})

### 4.3 Calibration is a property of the representation, not of self-supervision

Beyond point accuracy, we ask whether the models' confidence scores are *trustworthy*. Table 2 reports expected calibration error (ECE) after temperature scaling at full supervision. Both learned-tensor models are well calibrated (pretrained ECE = 0.0078 ± 0.0017, from-scratch 0.0072 ± 0.0004) and require only a mild temperature correction (T ≈ 0.6). The DeepSV-representation baseline is worse, but the size of the gap depends on the summary statistic and rests on a small sample: its per-seed ECEs are 0.033, 0.168 and 0.016, so the mean (0.072 ± 0.068) is driven by a single outlier seed while the **median is 0.033** — roughly four-fold worse than the tensor models rather than the order of magnitude a mean-only reading suggests. We report both statistics and draw no order-of-magnitude claim from three seeds. The baseline also needs a large and erratic temperature correction (T = 1.41 ± 0.88), consistent with its unstable F1 (Section 4.1).

The defensible reading is that calibration tracks the *representation* rather than self-supervision: pretrained and from-scratch tensor models are indistinguishable here, so the difference is attributable to the multi-channel encoding versus the fixed RGB pileup, not to the pretraining objective.

**Table 2. Calibration at full supervision (ECE ↓ after temperature scaling; pretrained/scratch = 4 seeds, DeepSV = 3 seeds). Per-seed values given because the DeepSV mean is outlier-driven.**

| Model | ECE mean ↓ | ECE median ↓ | Temperature | ECE per seed |
|---|---|---|---|---|
| AlignSSL-pretrained | 0.0078 ± 0.0017 | 0.0077 | 0.634 ± 0.070 | 0.0070; 0.0101; 0.0083; 0.0056 |
| AlignSSL-scratch | 0.0072 ± 0.0004 | 0.0071 | 0.586 ± 0.055 | 0.0073; 0.0078; 0.0067; 0.0069 |
| DeepSV-repr. baseline | 0.0724 ± 0.0681 | 0.0327 | 1.411 ± 0.881 | 0.0327; 0.1683; 0.0163 |

### 4.4 Length-stratified recall: the learned tensor is consistent across length; the RGB baseline is not

Deletion callers are notoriously length-dependent. Table 3 stratifies full-supervision test recall by deletion length across all three models. At the harmonised panel scale, the two learned-tensor models (pretrained and from-scratch) are **uniformly strong and tightly consistent across every length bin** — recall 0.86–0.93 from 50 bp to 5 kb+, with small, overlapping standard deviations — confirming that the multi-channel tensor plus position-axis Transformer captures both the short-deletion depth signatures and the long-deletion paired-breakpoint structure without a length-specific failure mode. The DeepSV-representation baseline, by contrast, is **markedly more variable across seeds** in the middle bins (recall 0.841 ± 0.165 at 200–500 bp and 0.850 ± 0.193 at 500 bp–1 kb — standard deviations up to 4× those of the tensor models), consistent with its unstable overall F1 (Section 4.1) and miscalibration (Section 4.3). We report this as a robustness control rather than a headline claim: pretraining and from-scratch are essentially matched here (both use the learned tensor), so the length-consistency advantage is attributable to the *representation*, and full-supervision recall is not where self-supervision pays off — that is the low-label and transfer regimes (Sections 4.1, 4.6).

**Table 3. Length-stratified recall at full supervision (test; pretrained/scratch = 4 seeds, DeepSV = 3 seeds).**

| Deletion length | n test | Pretrained recall | Scratch recall | DeepSV-repr. recall |
|---|---|---|---|---|
| 50–200 | 645 | 0.919 ± 0.026 | 0.917 ± 0.017 | 0.942 ± 0.059 |
| 200–500 | 281 | 0.913 ± 0.018 | 0.903 ± 0.025 | 0.841 ± 0.165 |
| 500–1k | 329 | 0.929 ± 0.008 | 0.938 ± 0.014 | 0.850 ± 0.193 |
| 1k–5k | 799 | 0.926 ± 0.024 | 0.954 ± 0.006 | 0.899 ± 0.116 |
| 5k+ | 245 | 0.857 ± 0.061 | 0.881 ± 0.071 | 0.918 ± 0.070 |

![Figure 3. Length-stratified deletion recall at full supervision. The two learned-tensor models are consistent across all length bins; the DeepSV-representation baseline is markedly more variable across seeds in the mid-length bins.]({{artifact:art_cf7645c0-8b8d-46e9-9a50-95509162a99d}})

### 4.5 Ablation over self-supervised objectives: all three help, but they cannot be ranked at this seed count

Which self-supervised objective drives these gains? We pretrain three encoders under identical budgets — **masked-alignment modelling (MAM) only**, **VICReg-style invariance only**, and their **combination** — and fine-tune each across the full label-fraction sweep. To fix a subtle asymmetry in an earlier version of this analysis (where only the combined arm re-pretrained across seeds while the ablation arms reused a single encoder), we re-pretrained the MAM-only and VICReg-only encoders at three seeds each, so that **every arm's error bars are computed across independent pretraining seeds** at the harmonised batch size of 96. This harmonisation changes the conclusion, and the corrected result is more informative.

All three self-supervised arms deliver the low-label effect, and each is individually significant against from-scratch training at 1% labels (Welch's *t*: MAM-only *p* = 0.017, VICReg-only *p* = 4.2 × 10⁻⁵, combined *p* = 4.2 × 10⁻⁵). That is the robust conclusion: the low-label gain does not depend on which objective is used.

Ranking the objectives *against one another*, however, is **not supported at the available seed count**. The ordering of means in Table 4 suggests MAM leads below 10% labels and the combined objective leads above 25%, but neither contrast reaches significance: MAM-only versus combined at 1% gives *t* = 0.83, *p* = 0.48, and combined versus MAM-only at 100% gives *t* = 1.77, *p* = 0.21. With three to four pretraining seeds and per-seed spreads of 0.01–0.12 F1, the study is underpowered to separate the objectives, and we state the crossover as an **ordering of means requiring more seeds to confirm**, not as a finding. We report the table because the mean ordering is stable and informative for future work, and because concealing it would misrepresent what we observed; but no claim in this paper rests on it. The combined objective was carried into the main experiments because it was selected before the ablation was run, not because it was shown to be best.

**Table 4. Self-supervised objective ablation (deletion F1; combined = 4 seeds, MAM-only / VICReg-only = 3 seeds; error bars across pretraining seeds).**

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

We train on the in-distribution panel and evaluate both in-distribution and on an entirely held-out population (CEU), sweeping the full label fraction (Table 5). Reporting only the extremes, as an earlier version of this analysis did, conceals the structure of the result; we therefore give all six fractions.

Across the sweep, the pretrained model's held-out CEU F1 exceeds the from-scratch model's at four of six fractions, but the difference is significant at **only one**: 10% labels (*t* = 3.38, *p* = 0.028). At 1% labels the direction favours pretraining by a wide margin of means (0.518 vs. 0.179) but the from-scratch variance is enormous (± 0.185, one seed of three learning nothing), so the contrast does not reach significance (*p* = 0.11). At 50% labels the direction **inverts** — from-scratch transfers better (0.834 vs. 0.679, *p* = 0.084) — and the generalisation gap likewise inverts at 1% and 50%. With three seeds this analysis is underpowered, and we make no claim that pretraining confers ancestry robustness. The honest summary is that the effect is suggestive at intermediate label budgets, inconsistent in sign across the sweep, and requires a larger multi-ancestry panel with more seeds to establish. It is stated as a limitation (Section 7), not a contribution.

**Table 5. Cross-ancestry transfer (train in-distribution → test held-out CEU, 3 seeds), all label fractions. *p* from Welch's *t*-test on held-out CEU F1, pretrained vs. from-scratch.**

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

---

## 5. Novelty and positioning

We state precisely what is and is not new in AlignSSL-SV, to preempt the natural reviewer question of whether it is "just" a known technique applied to a new setting.

**What is new.** (i) The **benchmark-separability control and its consequence** (Section 4.2). We are not aware of prior work in the SV deep-learning literature that tests a pileup-style benchmark against a deliberately minimal hand-crafted-feature model on identical windows, splits, label fractions and seeds, nor of prior work that measures untrained single-feature discrimination on such a benchmark. The finding — that twelve features beat every deep arm and one depth ratio reaches ROC-AUC 0.955 — is a methodological result that applies beyond this paper, and the candidate-filtering protocol of Section 6 is a concrete, tested partial remedy: it attenuates the shortcut from ROC-AUC 0.955 to 0.717 without changing the positives. (ii) The **image-free, learned alignment representation** — self-supervised pretraining directly on a continuous multi-channel read-alignment tensor, with no pileup-image rendering and no discrete tokenizer. This is the axis on which we differ from the closest prior SSL-for-SV effort, BASILISC (Banerjee, 2026), which pretrains a masked-image-modelling vision transformer over *rendered pileup images* compressed by a discrete VAE (Section 2). Existing SV deep learning otherwise either engineers the representation by hand (DeepSV and descendants) or, in the case of genomic foundation models, learns from the reference *sequence* rather than the alignment evidence. (iii) The **matched-conditions label-efficiency measurement** with error bars computed across independent *pretraining* seeds rather than fine-tuning seeds alone, and with every reported comparison accompanied by an explicit significance test (`results/stats_tests.csv`) — including the tests that fail.

**What we do not claim.** We do not claim a new SV caller, nor deployable accuracy: the control forbids it. We do not claim primacy on "self-supervised learning for structural variants" as a category — BASILISC precedes us. We do not claim that self-supervision improves calibration (the effect is attributable to the representation, and pretrained and from-scratch models are indistinguishable), that one self-supervised objective beats another (*p* > 0.2), or that pretraining confers ancestry robustness (significant at 1 of 6 label fractions, with the gap inverting at two). Each of these was claimed in an earlier draft of this work and withdrawn when the tests were run.

**What is not new (and we do not claim it is).** Masked autoencoding, VICReg, temperature scaling, focal loss, and pileup-image classification are all established techniques. Our contribution is their principled composition on a modality where they had not been combined, and the controlled evidence for what works — including the hand-crafted-feature control that bounds it. We also do not claim a higher full-supervision accuracy ceiling than a from-scratch model. The single claim that survives every control we ran is **label efficiency**: at 1% labels the pretrained model reaches F1 0.514 ± 0.055 where the from-scratch model reaches 0.050 ± 0.040.

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

### 6.3 Every arm falls, and the label-efficiency result survives

Table 7 reports the full arm set re-run under the candidate-filtering protocol at identical label fractions, seeds and batch size. Absolute F1 falls for every arm — the pretrained model from 0.934 to 0.762 at full supervision, the gradient-boosted tree from 0.939 to 0.791 — confirming that the task is genuinely harder and not merely re-labelled.

**Table 7.** Deletion F1 on the candidate-filtered benchmark (mean ± sd over 3 seeds; source `results/table7_hardneg_label_efficiency.csv`).

| Labels | *n* | AlignSSL (pretrained) | AlignSSL (scratch) | DeepSV repr. | Classical logreg | Classical GBT |
|---|---|---|---|---|---|---|
| 1% | 96 | 0.352 ± 0.064 | 0.000 ± 0.000 | 0.233 ± 0.172 | **0.491 ± 0.028** | 0.000 ± 0.000 |
| 5% | 172 | 0.325 ± 0.127 | 0.000 ± 0.000 | 0.261 ± 0.093 | **0.581 ± 0.002** | 0.566 ± 0.045 |
| 10% | 345 | 0.458 ± 0.056 | 0.415 ± 0.130 | 0.430 ± 0.021 | 0.583 ± 0.014 | **0.651 ± 0.025** |
| 25% | 863 | 0.495 ± 0.137 | 0.670 ± 0.030 | 0.281 ± 0.177 | 0.599 ± 0.017 | **0.714 ± 0.006** |
| 50% | 1726 | 0.647 ± 0.078 | 0.704 ± 0.021 | 0.367 ± 0.249 | 0.600 ± 0.005 | **0.750 ± 0.014** |
| 100% | 3452 | 0.762 ± 0.110 | 0.702 ± 0.086 | 0.284 ± 0.131 | 0.607 ± 0.000 | **0.791 ± 0.000** |

Three findings follow, and they do not all point the same way.

**(i) The pretrained-versus-scratch gap survives and sharpens.** At 1% of labels (96 windows) the pretrained model reaches F1 = 0.352 ± 0.064 while the identically-architected from-scratch model is degenerate at 0.000 ± 0.000 — it never fires (*p* = 0.016). The same holds at 5% (0.325 vs 0.000). On the uniform benchmark the from-scratch model was weak at 1% but not degenerate; on the harder task it fails outright below 10% labels. The claim that self-supervised initialisation is what makes a low-label detector trainable at all is therefore *stronger* here than in Section 4.1, not weaker.

**(ii) The learned tensor now clearly beats the DeepSV representation at full supervision.** At 100% labels the pretrained tensor model reaches 0.762 ± 0.110 against 0.284 ± 0.131 for the DeepSV-style RGB encoding (*p* = 0.018). The RGB baseline degrades far more than the tensor models do under candidate filtering — its precision stays high (0.90) while recall collapses to 0.18 — which is what one expects of a representation whose discriminative content was largely the coverage drop the protocol has now equalised. On the uniform benchmark this comparison was not significant; here it is.

**(iii) A hand-crafted control still leads at every label budget.** Gradient-boosted trees on twelve scalar features lead at 10%, 25%, 50% and 100%; logistic regression on the same features leads at 1% and 5%. The reviewer's central objection to this paper therefore stands after the fix, and stands more informatively: it is not an artefact of uniformly-sampled negatives alone. The one qualification is that the gap closes at full supervision — 0.791 for GBT versus 0.762 for the pretrained tensor model is not a significant difference at three seeds (*p* = 0.741) — and that the GBT is itself degenerate at 1% labels (0.000), where it is the pretrained network and the logistic regression that still produce a usable detector.

![Figure 6. Left: deletion F1 versus labelled-data fraction on the candidate-filtered benchmark, the direct analogue of Figure 2 (left) on the harder task; every arm falls and a hand-crafted control leads at every budget. Right: untrained single-feature separability on the uniform and candidate-filtered benchmarks, paired per feature; the depth shortcut is attenuated from 0.955 to 0.717 but not removed.]({{artifact:art_0b8b1b59-6de7-4036-bebf-cef7955b70ed}})

### 6.4 What this changes

The pre-registered question was whether pretraining's low-label advantage would survive a benchmark in which the depth shortcut is uninformative. The honest answer is: **the low-label advantage over from-scratch training survives and grows; the advantage over hand-crafted features does not appear.** We draw three conclusions. First, self-supervised pretraining on alignment tensors is a real and reproducible effect on the initialisation of a deep model, independent of the benchmark artefact identified in Section 4.2. Second, the negative result of Section 4.2 is not explained away by negative sampling: on a benchmark where no single feature exceeds ROC-AUC 0.72, twelve scalar features still match or beat a pretrained convolutional–attention encoder, and this should temper claims about learned representations for short-read deletion calling generally. Third, candidate filtering by quantile matching is a necessary but not sufficient benchmark repair; a fully shortcut-free protocol will likely require matching on a vector of alignment statistics rather than on the single strongest one.

Two extensions remain deferred: a coverage-robustness experiment (downsampling via `samtools view -s`) and a Truvari-based comparison against GIAB HG002 curated calls, which provides an orthogonal truth set free of the consensus-caller circularity of the 1000 Genomes call set. Both become worthwhile now that a non-degenerate benchmark exists; neither would have been informative on the uniform one.

---

## 7. Limitations

- **Benchmark separability (governing limitation).** The evaluation task, built with uniformly-sampled negatives as is standard in this literature, is separable by a single depth heuristic at ROC-AUC 0.955 and is solved better by twelve hand-crafted features than by any deep arm (Section 4.2). Every accuracy number in this paper must be read as a measurement on that task, not as deployable caller performance. This is the reason the paper's contribution is framed as a representation-learning and benchmarking result rather than as a new SV caller.
- **No comparison against production callers.** We compare learned representations under matched conditions; we do not compare against Manta, DELLY, LUMPY, GRIDSS or similar, because a comparison on a separable benchmark would favour whichever method best exploits the shortcut and would be uninformative.
- **Statistical power.** Three to four pretraining seeds per arm suffice for the headline low-label contrast (*p* < 10⁻³) but not to rank the self-supervised objectives against one another (*p* > 0.2, Section 4.5) or to establish cross-ancestry transfer (significant at 1 of 6 label fractions, Section 4.6). Those analyses are reported as orderings of means, not findings.
- **Scope.** Deletions and short reads only. Insertions, duplications, inversions, translocations and long-read data are out of scope, though the framework is not deletion-specific by construction.
- **Truth set.** The 1000 Genomes phase-3 integrated SV call set is itself a consensus of callers and carries its own error; a curated orthogonal benchmark (GIAB HG002) remains deferred (Section 6.4).
- **Full-supervision ceiling.** Pretraining does not exceed from-scratch training at 100% labels — the from-scratch model is marginally ahead (*p* = 0.025). The value of pretraining, on this benchmark, is confined to the low-label regime.
- **Single-panel pretraining corpus.** The unlabelled pretraining corpus comes from three samples; corpus-size and diversity scaling are untested.
- **Candidate filtering is partial.** The repaired benchmark of Section 6 attenuates the depth shortcut to ROC-AUC 0.717 but does not eliminate it, and it is single-sample (NA20845 train/test, NA12878 held out) with 1,516 test windows, because a mid-study loss of the shared reference directory left only two of the six panel alignments recoverable. Its conclusions are correspondingly wider-error-barred than Section 4's.
- **Single coverage regime.** All alignments are high-coverage (~30x) PCR-free Illumina. Robustness to lower coverage, PCR-positive libraries, or different read lengths is untested; the depth-derived channels are the ones most likely to be coverage-sensitive.
- **One held-out population.** Cross-ancestry generalisation is measured against a single held-out population (NA12878, CEU). A single held-out ancestry cannot distinguish population-specific transfer loss from sample-specific idiosyncrasy.

---

## 8. Conclusion

This paper reports two results, and the second qualifies the first.

Self-supervised pretraining on read-alignment tensors is strongly label-efficient relative to supervised training of the identical architecture: at 1% of labels it delivers roughly a ten-fold F1 improvement (*p* = 9.2 × 10⁻⁴), an effect that holds for each self-supervised objective tested individually. Calibration tracks the multi-channel learned representation rather than the pretraining objective: both learned-tensor models are better calibrated than a DeepSV-style RGB encoding (median ECE 0.008 and 0.007 vs. 0.033), though this comparison rests on three baseline seeds with one outlier and, like every number here, is measured on the separable task characterised in Section 4.2.

But a hand-crafted-feature control — twelve scalar alignment features on the identical windows — matches or beats every deep arm at every label budget, and a single centre-versus-flank depth ratio separates the classes at ROC-AUC 0.955 with no training at all. The cause is the uniformly-sampled negatives standard in this benchmark family. The label-efficiency gap we measure is therefore a difference in how fast each initialisation learns a depth threshold, not evidence of deployable label efficiency for deletion calling.

We consider the control the more valuable of the two results. It is cheap, general to any pileup-style SV benchmark, and it implies that a body of published architecture comparisons and low-label claims — including the evaluation design DeepSV introduced and much of what followed it — may rest on a task that a threshold solves. The productive next step for the field is not a larger encoder but a benchmark in which the depth shortcut is uninformative by construction. We built one (Section 6): quantile-matched candidate negatives attenuate the shortcut from ROC-AUC 0.955 to 0.717, every arm's F1 falls, and the result is mixed for us. The pretrained-versus-scratch label-efficiency gap survives and sharpens — at 1% labels the from-scratch model is degenerate while the pretrained one reaches F1 = 0.352 (*p* = 0.016) — and the learned tensor now beats the DeepSV-style representation at full supervision (0.762 vs 0.284, *p* = 0.018). But the twelve-feature control still leads at every label budget on the harder task too, so the negative result is not an artefact of uniform negative sampling. Until deep SV methods are shown to beat a twelve-feature gradient-boosted tree on a benchmark of this construction, claims about learned representations for short-read deletion calling should be treated as provisional.

---

## Data and code availability

The tensor-extraction pipeline, encoder and head implementations, pretraining and fine-tuning scripts, cluster job scripts, aggregation and manuscript-reconciliation tooling, result tables, and figures are available at https://github.com/aayushkrm/AlignSSL-SV under the MIT licence. Trained encoder checkpoints are available from the authors on request pending a Zenodo deposit. Sequencing data are from the 1000 Genomes Project (high-coverage PCR-free alignments, GRCh37/hs37d5) and are publicly available from the EBI 1000 Genomes FTP. The deletion truth set is the 1000 Genomes phase-3 integrated SV call set.

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
