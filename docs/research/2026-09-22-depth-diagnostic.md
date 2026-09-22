# Binned depth diagnostic

Date: 2026-09-22. Status: verified preprocessing defect; downstream benefit unknown.

`build_tensor` historically adds one count per read touching a bin and then
divides by `depth_norm * bin_size`. For a read covering every base in a bin of
width b, this produces `1 / (depth_norm*b)` instead of `1 / depth_norm`. For
fully covered bins below clipping, depth is understated by a factor b. Boundary
reads have a different bias, so a uniform post-hoc multiplication cannot in
general recover the true signal.

The new explicit `depth_mode="mean_base_coverage"` sums aligned-base counts
before division by bin width. Deletions/reference skips in a read's CIGAR do
not contribute aligned bases. Read filtering, normalization, clipping, other
channels, and row sampling remain unchanged. Counts use all eligible reads
before selecting the fixed number of tensor rows. This is aligned-base coverage
under the project's existing filtering policy, not a promise of equivalence
to every `samtools depth` setting.

## Verification

`tests/test_tensor_depth.py`: 16 cases passed on 2026-09-22 in Python 3.11,
NumPy 1.26.4 and pysam 0.24.1. Exact analytic cases cover bin widths
1, 2, 4, 8, 16 and 64; left/right boundaries; bin phases; CIGAR deletions and
reference skips; empty alignments; read-row truncation; invalid modes; and
the historical default. No training or biological performance result is
claimed from these tests.

## Required experiment

Re-extract identical loci from identical BAMs into paired legacy/corrected
representations with identical row sampling and all other settings fixed.
Check depth error against a separate per-base oracle on real read windows.
Train classical, scratch, and pretrained controls separately for each encoding;
do not apply corrected depth to a legacy checkpoint and call the difference
an SSL effect. Cross encoding and initialization in a factorial comparison.
The legacy default preserves compatibility, but new runs must record their
chosen encoding and reject mixed shard encodings.

This error is one plausible contributor to weak learned representations. It
does not prove that it caused the historical negative result, nor does fixing
it establish a novel method or a publication claim.
