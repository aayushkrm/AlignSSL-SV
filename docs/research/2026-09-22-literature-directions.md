# Literature-grounded directions for AlignSSL-SV

**Opened:** 2026-09-22
**Last verified:** 2026-09-23
**Scope:** self-supervised learning on short-read alignment evidence for
structural-variant (SV) candidate classification and deletion calling.
**Status:** core landscape verified from primary papers, repositories, and
institutional records; this is not an exhaustive novelty proof.

## Decision summary

The broad novelty claim “self-supervised learning for SV filtering” is not
available. CSV-Filter already transfers a VICReg-pretrained image encoder to SV
filtering, while BASILISC applies BEiT-style masked image modelling to
multi-channel short-read pileups. AlignSSL-SV must therefore earn a narrower
claim through evidence, not architecture vocabulary:

1. a read-native continuous tensor and physically valid transformations;
2. a task-aligned pretext objective that adds value beyond the same encoder
   trained from scratch;
3. evaluation on an unmodified, frozen caller-candidate pool at its real class
   prevalence, with donor-level confirmation; and
4. matched classical, caller-score, supervised, and image-model baselines.

No new performance gain is established yet. The immediate scientific gate is a
candidate-level pilot; the current three 1-Mb HG002 regions contain too few
truth deletions to support it.

## Existing project evidence

The corrected repository record already shows why the next protocol must be
strict:

- On the constructed-negative benchmark, threshold-free scoring removes the
  apparent low-label pretraining advantage. At 1% labels, AUPRC is 0.504 for
  pretrained versus 0.495 from scratch.
- On the repaired quantile-matched benchmark, the corresponding values are
  0.300 versus 0.278 with overlapping seed variation, while a classical
  gradient-boosted-tree control leads through the sparse-label regime.
- On the HG002/Manta caller-candidate benchmark, pretraining leads scratch only
  at the smallest label budget and the advantage does not persist. Both learned
  arms remain behind handcrafted controls.
- Centre-versus-flank depth is strongly predictive on the historical tasks.
  Correcting the depth implementation is necessary for representation fidelity,
  but it does not itself establish an SSL benefit.

These values come from the checked result tables described in `PROGRESS.md` and
are development evidence, not external confirmation.

## Primary-source ledger

| Work | Role and verified method | Evaluation fact relevant here | Constraint on AlignSSL-SV |
|---|---|---|---|
| [DeepSV](https://doi.org/10.1186/s12859-019-3299-y) (Cai, Wu & Gao, 2019) | Supervised short-read deletion caller. Candidate regions are converted to 256×256 RGB pileup images containing base/read-pair, discordance, mapping-quality, split-read, and visual depth evidence. | Chromosomes were divided within 20 individuals; NA12891 supplied a separate held-out individual experiment. Positives came from known deletions and negatives from non-deletion genome bins; simulation was also used. | Direct image ancestor, but its convenient negatives do not represent a production caller's false positives. A modern comparison must use candidate-derived negatives and report donor separation. |
| [DeepSVFilter](https://doi.org/10.1093/bib/bbaa370) and [official code](https://github.com/yongzhuangliu/DeepSVFilter) (Liu et al., 2021) | Supervised/transfer-learned CNN filtering of DEL and DUP candidates from short-read callers. The tool explicitly accepts candidates from DELLY, LUMPY, Manta and others, renders alignment images, and scores them. | The paper demonstrates two characterized samples. The public command interface separates positive/negative training and evaluation lists, but the sources inspected did not establish a strong independent-donor confirmation protocol. | A learned filter is not a complete caller. AlignSSL-SV must compare candidate scores and end-to-end retained callsets against the upstream caller and this class of image filter. |
| [CSV-Filter](https://doi.org/10.1093/bioinformatics/btae539) and [official code](https://github.com/xzyschumacher/CSV-Filter) (Xia et al., 2024) | Short- and long-read candidate filter using 224×224 multi-level grayscale CIGAR images, augmentation, and transfer from a VICReg self-supervised ResNet. | Training negatives are synthetically generated using an SV-length distribution rather than consisting solely of upstream-caller false positives. The reported short-read comparisons include DELLY, LUMPY, Manta, SvABA, and Cue. The HG002 HiFi experiment uses a random within-sample split. | This is the closest published overlap with the original “VICReg for SV filtering” framing. AlignSSL-SV needs realistic caller negatives and donor holdout, and cannot claim VICReg or SSL filtering itself as novel. |
| [BASILISC](https://doi.org/10.25740/jj829qd2843) (Banerjee, 2026, undergraduate honors thesis) | BEiT-based Analysis with Self-supervised Image Learning In Structural Variant Classification. It uses multi-channel pileup images, a dVAE tokenizer, and masked image modelling before candidate-locus classification. Channels include depth, split reads, discordant pairs, mapping quality, strand orientation, and allele support. | The institutional abstract states evaluation on 1000 Genomes short reads with HGSVC2 long-read assembly labels across deletions, insertions, and mixed regions. A full methods artifact was not discoverable through Firecrawl, Exa, scite, or the institutional landing page, so split and negative-construction details remain unverified. | Masked alignment-image modelling for short-read SV classification already exists. Remaining differentiation must be empirical and protocol-specific, not simply “masked SSL on richer images.” |
| [Cue](https://doi.org/10.1038/s41592-023-01799-x) and [official code](https://github.com/PopicLab/cue) (Popic et al., 2023) | Direct discovery and genotyping framework. It scans interval pairs and encodes depth difference, split/read-pair support, and discordant pair orientations as channels. A stacked-hourglass network predicts breakpoint keypoints, type, and genotype confidence maps. | It supports DEL, DUP, INV, INVDEL, and INVDUP calls larger than 5 kbp in the released workflow and was evaluated on synthetic and real sequencing data. | Demonstrates that a full caller needs locus/type/genotype output, not only binary filtering. It is a representation/caller comparator, but not a matched SSL baseline. |
| [NPSV-deep](https://doi.org/10.1093/bioinformatics/btae129) (Linderman et al., 2024) | Genotyper rather than discovery system. It compares 100×300×9 tensors from observed reads with genotype-conditioned simulated pileups using paired/contrastive networks. | Training uses 30 unrelated HGSVC2 samples after excluding HG002 and NA12878; evaluation includes HG002 GIAB and NA12878 resources, and subsets discovered by Lumpy or Manta. It is limited mainly to sequence-resolved DEL/INS and depends on simulation fidelity. | Provides a strong example of explicit donor exclusion and task-aware contrast, but should not be misreported as a de novo caller or direct filtering baseline. |
| [LSnet](https://doi.org/10.3389/fgene.2023.1189775) (2023) | Hybrid long/short-read or HiFi deletion detection and genotyping from nine aggregate alignment features over 200-bp windows. | HG002 chromosomes 1–10 train, 11 validation, and 12–22 test; deletion-only. | Useful low-dimensional learned baseline and evidence that genomic split alone is weaker than untouched-donor confirmation. |
| [sv-channels](https://doi.org/10.1101/2024.10.17.618894) (preprint, 2024) | Short-read deletion filtering of Manta candidates using one-dimensional evidence channels for orientation, split/discordant reads, mapping quality, and local CIGAR indels. | Seven 1000 Genomes samples train and HG00420 is held out; Manta and GRIDSS are compared. The paper explicitly discusses leakage risk from shared population deletions. | Closest task-level production comparator for a short-read Manta deletion pilot. Its held-out-sample design and caller-level metrics should be matched or exceeded. |
| [Systematic ML assessment](https://doi.org/10.64898/2026.01.27.702059) (Kalra, Paulin & Sedlazeck, preprint, 2026) | Long-read Sniffles2 filtering benchmark spanning 15-feature random forests, ResNet/VICReg images, diffusion anomaly detection, Evo2 sparse autoencoders, and ensembles. | On HG002/HG005, a random forest (reported F1 95.7%) is effectively tied with ResNet50 (95.9%) and diffusion (95.8%); false Sniffles2 calls are used directly as negatives. It is a preprint, long-read task, and only two donors/one caller. | Complexity must beat a tuned classical model under the same candidates and splits. This is motivation for a baseline, not transferable evidence that the same ranking will hold for short reads. |

### Evidence-quality notes

- Primary publisher/PMC full text and official repositories support the method
  descriptions above. The Stanford record currently exposes the BASILISC
  abstract but not enough body text to verify its complete split or metrics.
- Firecrawl located the initial corpus but did not expose body passages for
  several records. Exa, scite, Europe PMC XML, publisher pages, and official
  repositories were used as independent fallbacks. A failed index lookup was
  never treated as evidence that no prior work exists.
- Citation counts and search-engine summaries are not used to establish method
  claims. Preprints and a thesis are labelled as such.

## Frozen design implications

### Candidate population

The primary task is binary filtering of **all** candidates emitted by one
frozen upstream short-read caller and configuration. Truth is used only after
candidate generation to assign labels and score calls. Do not sample negatives
around truth sites, remove difficult false positives using truth, or depth-match
the primary evaluation set. Depth/length/coverage matching remains a secondary
diagnostic that asks which shortcuts drive a model.

The caller's own score and default filter are baselines. Preserve original
coordinates, genotype fields, support fields, and scores so both candidate-level
ranking and end-to-end retained callsets can be evaluated.

### Splitting and label accounting

- No locus or donor in confirmation may influence pretraining choices,
  normalization, hyperparameters, calibration, or thresholds.
- Group overlapping and multiscale windows at a locus before splitting.
- Count validation labels inside each stated label budget.
- Use paired label subsets and seeds across arms; donors/loci, not training
  seeds, are the units supporting biological generalization.
- Historical HG002 results are development evidence. Confirmation requires
  untouched donors with compatible truth/confident regions.

### Required matched arms

1. Frozen upstream caller score/default filter and a depth-only score.
2. Logistic regression, gradient-boosted trees, and random forest on the same
   predefined alignment features.
3. DeepSV-style RGB and, where feasible, sv-channels/CSV-Filter-style evidence.
4. The corrected AlignSSL encoder trained fully supervised from scratch.
5. The identical encoder initialized from each registered SSL objective.
6. Simple supervised feature-plus-embedding fusion, labelled as an engineering
   baseline rather than an SSL contribution.

Changed input encodings or multiscale layouts require independent matched
pretraining and fine-tuning. A checkpoint trained on one representation cannot
be held fixed to compare a different representation.

### Endpoints

Use AUPRC at the natural candidate prevalence as the primary threshold-free
development endpoint. Also report ROC-AUC, precision at a pre-registered
sensitivity, recall at a fixed review/call budget, calibration (Brier/NLL and
reliability), length/coverage/repeat strata, and complete precision/recall after
applying the filter to the frozen caller output. Thresholds are selected only
with budgeted validation labels. F1 at 0.5 is not a primary endpoint.

Before confirmation, freeze one primary label budget, minimum useful effect,
candidate generator, matching policy, multiplicity family, stopping rule, and
test donors. The development sweep may include several budgets, but confirmation
must not select the most favorable one after viewing results.

## Three falsifiable experiments

### E1 — Real-candidate label efficiency

**Claim under test:** task-aligned pretraining improves candidate-level AUPRC
over the same corrected encoder trained from scratch at the pre-registered low
label budget, and adds value beyond caller, depth, and classical controls.

Use one immutable candidate manifest and paired label subsets. Match optimizer
steps, fine-tuning updates, model-selection allowance, augmentation, and seed
count. A null/scratch win, or a learned arm that remains below classical
controls, falsifies the useful-SSL claim even if one fixed threshold looks good.

### E2 — Representation and row-semantics factorial

**Claim under test:** corrected depth plus physically consistent row handling
improves generalization because it preserves alignment semantics, and SSL adds a
benefit beyond the same correction under supervised training.

Run the registered factorial: legacy versus corrected representation, each from
scratch and with independently trained SSL. Add the legacy versus
global-preserving row view and legacy versus mask-aware pooling ablations. Keep
the candidate manifest and label subsets fixed. Report main effects and
interaction; a correction that helps scratch and SSL equally is an engineering
repair, not an SSL result.

### E3 — Task-aligned objective against generic SSL

**Claim under test:** predicting alignment evidence hidden in a biologically
valid way transfers better than generic VICReg or masked-pixel reconstruction
under identical unlabeled data and compute.

Compare MAM-only, VICReg-only, the existing combination, and one preregistered
task-aligned objective. Measure optimization health before downstream scoring:
finite gradients, per-term gradient norms, embedding variance/rank, and
performance against trivial reconstruction predictors. Retrain every arm and
cap objective exploration. If the task-aligned objective does not beat both
generic SSL and scratch on untouched donors, do not promote it as the method.

## Immediate next gate

1. Freeze a reproducible Manta version/configuration or an explicitly justified
   comparable short-read candidate generator.
2. Expand the label-blind HG002 recovery beyond the current 3 Mb and verify that
   the resulting candidate/truth counts can support a development pilot.
3. Build an immutable candidate manifest with provenance and baseline fields.
4. Run classical/caller/depth baselines before allocating substantial GPU time.
5. Register E1 and the factorial subset of E2 that is affordable from the pilot;
   retain per-example predictions and failed/null runs.

The project should proceed only from this candidate-level gate. More pretraining
on the current tiny truth-centred slice would consume compute without answering
the scientific question.
