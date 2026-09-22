# Read-thinning and row-pooling semantics

Date: 2026-09-23. Status: opt-in engineering correction; downstream benefit
unknown.

## Verified defect

The historical `subsample_rows` augmentation zeroed every channel in a dropped
read row. That changed broadcast reference composition and physical depth even
though those quantities are column-level properties of the original locus. The
historical encoder then averaged every row, including padding, without using the
valid-read mask. Convolutional biases and row-neighbour propagation therefore
made padding amount and dropout layout part of the representation.

This is a semantic inconsistency, not evidence that it caused the historical
negative SSL result.

## Opt-in correction

Two explicit experimental modes were added while retaining historical defaults:

- `row_view_mode=preserve_globals_compact` keeps depth and reference channels
  bitwise unchanged, selects a subset of real reads, preserves their relative
  order, compacts their row-local evidence, and converts removed rows to normal
  padding.
- `row_pool_mode=mask_aware` gates padded rows before the convolutional stem,
  after each convolution, and inside each residual block; it then averages only
  valid read rows. The internal gating prevents activations created in padding
  from propagating back into valid rows.

The pretraining checkpoint records both choices. Fine-tuning records its
row-pooling choice and rejects a pretrained checkpoint produced under different
pooling semantics. Missing metadata means `legacy`, preserving released
checkpoints and prior experiments.

## Verification

Focused behavioural tests establish that:

1. corrected row thinning preserves `Q_DEPTH` and all reference channels;
2. retained read-local rows are contiguous and retain relative order;
3. keep-fraction 1.0 is a bitwise identity in both view modes;
4. mask-aware encoder output is invariant to appended padded rows carrying the
   broadcast global channels;
5. legacy and corrected encoders have identical state-dict schemas; and
6. released SSL and SAS checkpoints strict-load under `legacy` semantics.

## Required ablation

Use corrected-depth tensors and matched seeds/budgets to compare at least:

1. legacy view + legacy pool;
2. corrected view + legacy pool;
3. corrected view + mask-aware pool; and
4. MAE-only/no-row-thinning controls.

Log the VICReg invariance, variance and covariance terms separately. A claim
requires threshold-free improvement over matched scratch and strong classical
controls on untouched evaluation data. Passing the semantics tests is not a
positive biological result.
