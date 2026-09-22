# Independent scientific audit — AlignSSL-SV

**Date:** 2026-09-22  
**Scope:** `alignssl/ssl.py`, `alignssl/encoder.py`, `alignssl/tensorize.py`,
`scripts/pretrain_ssl.py`, and `scripts/finetune_eval.py`. This is a code and
protocol audit, not evidence of a performance gain. `Verified` means directly
established from the current source; `Hypothesis` means a biologically or
statistically plausible consequence that still requires an experiment.

## Bottom line

Do not claim improved SSL yet. Three gates are actionable: make the corrected
depth representation the explicit, provenance-tracked experimental factor;
repair the coverage view/pooling semantics before interpreting VICReg; and
remove test-label use from calibration. A valid gain must beat a matched
from-scratch encoder and be compared against strong non-SSL controls under the
same label budget, split, and scoring rule.

## 1. Multi-scale depth is confounded by bin width; the correction is not yet the benchmark

**Verified.** In the legacy branch, each read contributes one count to every
bin it touches (`alignssl/tensorize.py:120-136`), then the count is divided by
`depth_norm * bin_size`. Thus a read covering one base and a read covering a
whole coarse bin both contribute `1 / bin_size` to that bin. The resulting
channel is not mean per-base coverage and changes with scale. The new
`mean_base_coverage` branch instead accumulates `row["cnt"]`, where `cnt` is
the number of aligned bases per bin (`tensorize.py:193-206`), then divides by
bin width (`tensorize.py:128-137`). That formula is correct for mean aligned
coverage before row truncation, and the opt-in API preserves legacy outputs
(`tensorize.py:64, 95-96`).

The correction is therefore technically credible, but the default remains
`legacy`. The extraction tools already expose the choice and write shard
metadata (`scripts/extract_pretrain.py:32-35, 95-98`;
`scripts/extract_tensors.py:110-113, 189-197`), and the shard loader rejects
mixed modes (`alignssl/data.py:514-521`; `alignssl/encoding.py:7-21`). The
remaining provenance gap is at run level: the requested training/evaluation
entrypoints consume precomputed tensors but do not surface the mode in their
own checkpoint/result configuration (`scripts/pretrain_ssl.py:47-58`;
`scripts/finetune_eval.py:170-178`). Existing checkpoints and any new tensors
must not be mixed across modes.

**Hypothesis.** Legacy multi-scale depth can make the model learn bin-size or
read-touching artifacts instead of comparable coverage evidence, especially in
length-stratified SSL. The corrected mode may change results in either
direction; static inspection cannot establish a gain.

**Acceptance criteria.**

- Carry the already-selected `depth_mode` into the run manifest/checkpoint,
  together with `depth_norm`, `bin_size`, reference hash, and source revision.
  Re-extract all SSL, train, validation, and test tensors before comparing
  modes; retain legacy only as a compatibility arm.
- Keep the supplied synthetic coverage tests as a representation gate: full,
  partial, boundary-crossing, deletion/skipped CIGAR, bin-phase, and row-cap
  cases must pass. I independently reproduced all 16 focused tests with an
  ephemeral `pysam` environment (`16 passed`); no repository code was changed.
- On the recovered label-blind GIAB 3x1 Mb pilot, compare corrected and legacy
  tensors with identical windows and labels. A claim of SSL improvement
  requires the corrected combined arm to beat matched scratch on the
  pre-registered primary metric (threshold-free AUPRC or ROC-AUC) across
  independent seeds, with uncertainty intervals, and to be reported against
  the best 12-feature GBT/logistic and single-depth controls. A representation
  change alone is not an SSL win.

## 2. The VICReg coverage view changes column-level biology and is pooled through padding

**Verified.** `subsample_rows` zeros *all* channels of dropped rows
(`alignssl/ssl.py:140-152`). This includes `Q_DEPTH` and the broadcast
reference channels, even though those are column-level signals in
`tensorize.py:105-117, 134-137`; a lower-coverage view therefore changes the
reference/depth encoding, not just the set of read rows. The encoder then does
an unmasked mean over rows after convolutions (`alignssl/encoder.py:74-83`),
so padded/dropped rows can contribute through convolution bias, BatchNorm, and
neighbouring-row context. The same transformation is used as the VICReg view
pair in `scripts/pretrain_ssl.py:91-96`.

**Hypothesis.** The invariance loss may suppress real depth evidence (a primary
deletion cue), or exploit keep-fraction/padding artifacts. Either outcome can
look like a pretraining effect while reducing transfer to a biologically
different coverage regime. This is a testable risk, not a verified claim of
performance harm.

**Acceptance criteria.**

- Add tensor-level tests that a coverage view preserves `Q_DEPTH` and
  `REF_ONEHOT` exactly, zeros only row-local evidence, and preserves the valid
  row mask semantics. Add an encoder test showing output invariance to adding
  padded rows when the valid rows are unchanged; use mask-aware row pooling or
  an equivalent explicit mask treatment.
- Run a pre-registered ablation with the same encoder, budgets, and seeds:
  scratch, MAE-only, VICReg-only, combined objective; for the latter compare
  the current view against the semantics-preserving view and a no-coverage-
  augmentation control. Log VICReg invariance/variance/covariance terms, not
  only their sum (`ssl.py:118-137`).
- Accept an SSL claim only if the corrected combined method improves the
  primary threshold-free metric over matched scratch at the low-label target
  and does not lose to the strongest classical control; report deletion-length
  and coverage strata. A fixed-0.5 F1 improvement alone is insufficient.

## 3. Calibration is fit on the test set, so the reported ECE is unusable

**Verified.** `collect_logits` first obtains logits and labels from
`test_dl` (`scripts/finetune_eval.py:226`). On the full-label run,
`TemperatureScaler.fit(logits, labels)` then fits temperature on those same
test labels, and ECE is computed on the same data (`finetune_eval.py:237-253`).
That is direct test-label leakage. `ConformalBinary` is imported but never
calibrated or evaluated in this script (`finetune_eval.py:21-22, 237-253`), so
the docstring’s conformal-coverage promise is not verified by this entrypoint.

**Hypothesis.** ECE and the selected temperature are optimistically biased and
cannot support a pretrained-versus-scratch or deep-versus-classical calibration
claim. The size-stratified recall uses the validation-selected threshold and is
separate from this leakage, but it still does not repair the calibration result.

**Acceptance criteria.**

- Fit temperature and any conformal quantile only on a calibration split carved
  from the labelled training budget (or nested cross-fitting). Use the test
  chromosomes once, after all model, threshold, and calibration choices are
  frozen; add a regression test that test labels are not read by calibration.
- Evaluate every arm, including scratch and classical controls, on the same
  untouched test set with held-out NLL/Brier/ECE, reliability plots, and
  conformal marginal coverage/interval size if conformal output is retained.
  Report coverage by deletion length and coverage regime, with seed-level
  uncertainty.
- If the conformal path is not implemented, remove that claim from the result
  contract rather than reporting an imported-but-unused class.

## Minimum scientific plan before expansion

1. Freeze the data manifest for the recovered GIAB 3x1 Mb pilot: candidate
   coordinates, full-reference hash, tensor configuration, train/calibration/
   test assignment, and no test-driven mode or hyperparameter choice.
2. Re-extract with corrected depth and run representation sanity tests before
   training. Keep legacy as a labelled compatibility arm, not as an unnoticed
   mixture.
3. Run matched label budgets and chromosome/sample splits for scratch,
   MAE-only, VICReg-only, combined SSL, the 12-feature GBT/logistic controls,
   and the simplest single-depth control. Use at least three independent seeds
   for the pilot gate; use more before making a publication-level claim.
4. Make threshold-free ranking the primary low-label endpoint; choose any
   operating threshold and calibration only on training-side data. Preserve
   per-example predictions, seed manifests, timing, source revision, and all
   negative/failed runs.

**Decision gate:** proceed to larger recovery only if the corrected, semantics-
preserving combined SSL arm has a reproducible advantage over matched scratch
and is competitive with the strongest classical control on untouched data. If
not, report the negative result and investigate the representation/objective
without converting infrastructure repairs into a scientific claim.

## Resolution status — 2026-09-22

- **Depth provenance: implemented, experiment pending.** Extraction tools expose
  the mode; shards and memmaps record it; loaders reject mixtures; pretraining
  checkpoints and evaluation configurations record it; fine-tuning rejects a
  checkpoint whose representation differs from its tensors.
- **Calibration leakage: repaired in code, historical outputs unchanged.** The
  evaluation entrypoint fits temperature on the in-budget validation subset and
  applies it once to test logits. It explicitly skips calibration when that
  subset is absent or single-class. Historical calibration numbers must still
  be treated as invalid until rerun.
- **Coverage-view/pooling semantics: unresolved.** No claim relying on VICReg
  coverage invariance should be promoted until this gate has tests and an
  ablation.

These resolutions are engineering status only. No biological performance gain
has yet been measured.
