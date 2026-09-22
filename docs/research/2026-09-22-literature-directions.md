# Literature-grounded research directions for AlignSSL-SV

**Date:** 2026-09-22  
**Scope:** primary-source directions for improving self-supervised learning on
short-read read-alignment evidence for structural-variant deletion calling.  
**Status:** living research note; the source ledger and recommendations will be
updated as papers are verified.

## Starting evidence from this repository

This note starts from the corrected project record, not from the withdrawn
headline. The repository reports that:

- AlignSSL-SV uses an 18-channel continuous `(C=18, R=64, W=256)`
  read-alignment tensor and masked-alignment modelling (MAM), with VICReg-style
  and combined objectives as ablations.
- On the constructed-negative benchmark, threshold-free scoring removes the
  apparent low-label pretraining advantage: at 1% labels AUPRC is 0.504 for
  pretrained versus 0.495 from scratch. On the repaired quantile-matched
  benchmark, the corresponding values are 0.300 versus 0.278, with overlapping
  seed variation; the classical GBT control leads through the sparse-label
  regime.
- On the GIAB HG002/Manta candidate benchmark, pretraining leads from scratch
  only at 1% labels (ROC-AUC 0.778 ± 0.045 versus 0.545 ± 0.041; Holm-adjusted
  *p* = 0.017 within that six-budget family), then does not persist and reverses
  at larger budgets. Both deep arms remain behind hand-crafted controls.
- The untrained centre-versus-flank depth ratio is highly predictive on the
  original and candidate-generated benchmarks. Therefore every proposed pilot
  below must use candidate-derived or distribution-matched negatives and must
  report the depth-only control, equal labels, threshold-free metrics, and
  per-example predictions.

These facts are from `README.md` and
`docs/AlignSSL_SV_novelty_verdict.md`; they are the motivation and protocol
constraints, not new external validation.

## Questions this literature check must answer

1. What exactly did BASILISC, CSV-Filter, and DeepSV do, and where do they
   constrain the novelty claim?
2. Which nearby primary methods expose a testable opportunity for a *short-read,
   read-alignment* SSL caller rather than a long-read filter or an image-only
   classifier?
3. Which three experiments can falsify a useful improvement over DeepSV-style
   RGB input, a matched from-scratch tensor encoder, and strong classical
   alignment-feature controls under the same label and compute budgets?

## Verification ledger — initial entries

The entries below are repository-sourced leads. External paper-index
verification, full citations, and primary-source links will be added before the
recommendations are treated as literature-verified.

| Lead | Repository citation | Why it matters | Verification state |
|---|---|---|---|
| DeepSV | Cai, Wu & Gao, “DeepSV: accurate calling of genomic deletions from high-throughput sequencing data using deep convolutional neural network,” *BMC Bioinformatics* 20, 665 (2019), DOI `10.1186/s12859-019-3299-y` | Direct ancestor: hand-designed RGB pileup image plus supervised CNN for short-read deletions | Local lead; external verification pending |
| BASILISC | Banerjee, “Self-Supervised Learning with Masked Images for Structural Variant Analysis in Short-Read Genome Sequencing,” Stanford Digital Repository (2026), DOI `10.25740/jj829qd2843` | Closest SSL-SV approach; appears to retain pileup images and use dVAE/BEiT-style masked visual tokens | Local lead; external verification pending |
| CSV-Filter | Xia et al., “CSV-Filter: a deep learning-based comprehensive structural variant filtering method for both short and long reads,” *Bioinformatics* (2024), DOI `10.1093/bioinformatics/btae539` | Close learned alignment-image filter; tests whether filtering is transferable to discovery/candidate classification | Local lead; external verification pending |
| Cue | Popic et al., “Cue: a deep-learning framework for structural variant discovery and genotyping,” *Nature Methods* (2023), DOI `10.1038/s41592-023-01799-x` | Close multi-signal image-based SV caller; useful representation and call-set evaluation comparator | Local lead; external verification pending |

## Planned external verification

The Firecrawl research index will be used for paper records, citation-graph
expansion, and targeted in-body checks. The initial set will cover the three
named papers, DeepSV's close image-based descendants, self-supervised alignment
or SV-filtering methods, and primary benchmark/baseline papers. A paper will be
kept when its primary source supports a concrete comparison or exposes a gap;
reviews will be used only for landscape context, not as evidence for a method
claim.

## Candidate experiments (protocol skeleton; to be sharpened after verification)

### E1 — Matched candidate hard-negative SSL

**Falsifiable claim:** masked-alignment pretraining improves threshold-free
ROC-AUC/AUPRC over a parameter-matched from-scratch tensor encoder at 1–5% of
labels *when candidate negatives are matched on depth contrast and the test
chromosomes are untouched*. A null or scratch win falsifies the claim.

**Equal-budget pilot:** use the same candidate pool, chromosome split, optimizer
steps, fine-tuning updates, batch-size schedule, and encoder parameter count for
pretrained and scratch arms; count validation labels inside the stated budget;
match each negative to a positive on centre/flank depth-ratio quantile and
coverage stratum; use 1%, 5%, 10%, 25%, 50%, and 100% labels. Primary endpoint:
ROC-AUC plus AUPRC with bootstrap confidence intervals; F1 only at a threshold
selected on validation data. Include MAM-only, VICReg-only, combined, random
initialisation, and the 12-feature GBT/logistic controls.

### E2 — Multi-scale alignment context against RGB and single-scale tensor

**Falsifiable claim:** a multi-scale tensor encoder improves length-stratified
recall or breakpoint-localisation accuracy for deletions spanning short to
kilobase scales, at matched compute, without relying on the depth shortcut. A
single-scale tensor, DeepSV-style RGB, or classical control winning on all
strata falsifies the claim.

**Equal-budget pilot:** hold the MAM checkpoint and classifier head fixed;
compare 1×/4×/16× genomic-context branches against a single 256-bp tensor and
the DeepSV RGB reimplementation, with equal input bases, optimizer updates,
parameter-count reporting, and wall-clock/GPU-memory caps. Test deletion-length
strata and breakpoint error, not only pooled classification. Use candidate or
quantile-matched negatives and the depth-only control.

### E3 — Uncertainty as a useful decision rule, not a calibration add-on

**Falsifiable claim:** alignment SSL plus an uncertainty estimator reduces
review burden at fixed sensitivity (or improves sensitivity at fixed review
rate) and remains calibrated across held-out ancestry/sample strata, compared
with scratch, DeepSV RGB, and classical controls. If calibration or triage
benefit disappears under held-out samples or equal compute, the claim is
falsified.

**Equal-budget pilot:** freeze the representation arms after identical training
budgets; compare temperature scaling, MC dropout/deep ensemble, and a scratch
counterpart using the same validation-label allocation. Pre-register sensitivity
targets and report ECE/Brier, risk--coverage/AURC, selective AUPRC, and
cross-sample/ancestry calibration drift. Do not use fixed 0.5 F1 as the primary
endpoint; keep call-set yield and review-rate curves.

## What remains to verify before treating these as directions

- Exact BASILISC metadata, task definition, training objective, truth set,
  negative construction, and reported baselines.
- Whether CSV-Filter is a short-read-capable filter in practice, what upstream
  calls it consumes, and whether its evaluation supports a fair candidate-level
  comparison.
- DeepSV's exact input channels, candidate-generation protocol, split, and
  baselines, rather than relying on the repository's reimplementation.
- Primary evidence for Cue, LSnet, sv-channels, NPSV-deep, and the strongest
  classical short-read callers/filters that should be in the pilot.
- Which gaps are genuinely untested versus merely not indexed by the research
  corpus; this note is not intended to be an exhaustive novelty proof.

