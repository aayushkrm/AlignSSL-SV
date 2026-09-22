# AlignSSL-SV research renewal

Version: 2026-09-22, preliminary protocol before new biological outcomes.
The literature and independent audit will refine hypotheses before a pilot is
frozen. Historical numbers are preserved and are not targets to optimize against.

## Intended outcome

Demonstrate reproducible value from alignment representations and self-supervised
pretraining for deletion calling, with calibrated uncertainty, robust evaluation,
and released reproducible evidence. A useful negative result remains evidence,
but does not fulfill the requested performance-improvement objective. Scientific
claims follow data, including outcomes unfavorable to the preferred method.

## 1. Re-establish trustworthy inputs and execution

- Restore reference, truth and alignments from canonical public sources. The
  previous scratch workspace and its recovery snapshots are absent.
- First infrastructure pilot: HG002 hs37d5 at 0-based half-open intervals
  chr1:10,000,000–11,000,000, chr10:10,000,000–11,000,000 and
  chr20:10,000,000–11,000,000. These coordinates precede inspection of labels.
  This small slice tests retrieval, reference concordance and tensorization;
  it is not sufficiently representative for a performance claim.
- Download GIAB Tier1 v0.6 and reference from their canonical NCBI/EBI listings.
  Record URL, timestamp, byte count, SHA-256, BAM header, exact coordinates,
  software environment, source snapshot and job ID. Verify coordinate systems
  and reference identity before scientific extraction.
- Preserve original caller evidence and regenerate pre-filter candidates using
  a frozen Manta version/configuration. Do not use truth to construct candidate
  windows or to tune candidate generation. Measure production caller filtering
  as an additional baseline; do not compare learned filtering only to weak CNNs.
- Mirror per-seed predictions, manifests, histories and small checkpoints into
  durable project storage plus local copies; checkpoint expiry and verify hashes.

## 2. Diagnose before spending GPU time

1. **Depth fidelity**: paired legacy/corrected tensors at identical coordinates.
   Test each against analytic coverage and an independent real-read oracle.
2. **Augmentation fidelity**: inspect whether row dropout changes reference and
   depth channels inconsistently with the retained reads. Compare representations
   and downstream signal under valid read thinning versus current augmentation.
3. **Objective optimization**: measure per-term gradients, not just scalar losses;
   validate numerical finiteness in mixed precision and check embedding rank,
   covariance, variance and masked-target prediction against trivial predictors.
4. **Read order and coordinate information**: measure row-permutation sensitivity
   and determine whether spatial/scale information needed for breakpoints survives
   pooling. These are hypotheses, not yet confirmed causes of failure.

## 3. First controlled learning pilot

Start with a factorial representation/initialization test: legacy vs corrected
depth, each trained from scratch and with the existing SSL objective. Retrain
SSL for the changed representation rather than reusing incompatible weights.
Keep samples, windows, train/validation/test assignments, label budgets, training
steps, optimizer search budget, row sampling, seeds and scoring identical.

Include logistic regression and boosted trees on the 12 handcrafted features,
an untrained depth feature, the original caller score/filter, and the existing
DeepSV representation. Add a supervised feature-plus-embedding control when
evaluating feature distillation or fusion. A representation change that improves
both scratch and SSL equally is not an SSL advantage.

Explore only a small, recorded hypothesis set: corrected inputs; physically
consistent augmentation; and an objective predicting task-relevant evidence
(including existing statistic-anchored SSL as a control). Treat feature fusion
as a baseline/engineering improvement unless independent literature establishes
a substantive methodological contribution. Do not tune indefinitely until a
favorable seed or label fraction appears.

## 4. Freeze a confirmatory protocol

- Historical HG002 and prior panel tests are now development evidence. Choose
  fresh independent donors and verified truth/confident regions for confirmation;
  family relatedness, genomic overlap and reference build must be recorded.
- Disjoint samples and genomic groups prevent supervised and SSL contamination.
  Fit normalization and augmentation parameters on training data only. Group
  overlapping/multiscale windows at a locus before any splitting.
- Choose the primary operating endpoint before observing new test outcomes.
  Candidate filtering should include precision at a fixed sensitivity and end-to-end
  call-set precision/recall, alongside ROC-AUC and PR curves at the real prevalence.
  ROC-AUC alone does not establish useful rare-error filtering. Thresholds and
  calibration are fitted exclusively with budgeted development labels.
- Count all validation labels and model-selection attempts. Paired seeds share
  label subsets; training seeds are not independent patients. Use donor/locus
  grouped uncertainty, predeclare comparisons and multiplicity correction, and
  size the confirmatory sample using development effect/variance estimates and
  a meaningful minimum gain. No fixed sample-size claim is made yet.
- Freeze an explicit stopping rule, primary label budget, minimum useful gain,
  candidate generator, genotype/matching policy, exclusions and final test IDs
  before opening confirmation results. Independent reviewer approval is a
  methodological gate, not a user permission request.

## 5. Deliver the full research product

Validate calibrated uncertainty (Brier/NLL, reliability curves and appropriate
calibration uncertainty), independent-donor performance, length/coverage strata,
and computational cost. Distinguish candidate classification from a complete
caller: preserve caller breakpoints/genotypes for filtering experiments, and
separately evaluate any learned refinement/genotype head. Use a verified
Truvari matching protocol for emitted VCFs, including duplicates and no-call
handling. Release code, environment, raw predictions, split IDs, weights,
model/data documentation, figures and manuscript with independently reviewed
claims. A pilot gain is not publication readiness.

## Review and stopping decisions

An independent Luna/max agent reviews each material data/protocol/code/result
milestone; the six-hour task heartbeat triggers review when new evidence exists.
Reject contaminated or unfair comparisons before interpreting their scores.
If a hypothesis fails its predeclared criterion, record the result and move to
the next justified hypothesis; do not change the scoring rule after seeing the
test. Report unresolved evidence honestly and keep the overall goal active.
