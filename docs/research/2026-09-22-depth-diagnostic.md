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

### Real-read oracle — 2026-09-23

`scripts/validate_depth_oracle.py` compared tensor depth with a distinct pysam
pileup traversal on the recovered HG002 BAM. The grid comprised 63 deterministic,
label-blind windows: three positions in each of three 1-Mb regions, crossed with
bin sizes 1, 2, 4, 8, 16, 32 and 64. Both paths applied the tensorizer's exclusion
of unmapped, secondary and supplementary alignments, while the oracle counted
non-deletion/non-reference-skip query bases from pileup columns.

SLURM job `1597948` failed before analysis because the repository root was
absent from `PYTHONPATH`; it produced no result. The corrected retry, job
`1597949`, completed in 61 seconds on `hydra-n1` with 111,140 KiB maximum RSS.
Corrected mean-base coverage matched the oracle exactly: maximum absolute error
0 and zero mismatched columns at tolerance 1e-7. Legacy depth matched at bin
size 1, then diverged with mean absolute error 0.427, 0.681, 0.801, 0.874,
0.904 and 0.927 at bin sizes 2, 4, 8, 16, 32 and 64 respectively.

The raw 63-window record is
`results/diagnostics/depth_oracle_hg002_20260923.json` (SHA-256
`511d6d98f1bd3eb2e5040676aaf31bba8191f220949715b3570387265d160e3b`).
This is strong real-read evidence that the corrected channel implements its
declared quantity. It is not independent software—the two paths both use
pysam—but pileup traversal is separate from the tensorizer's aligned-pair path.
It does not establish improved classification or SSL transfer.

## Required experiment

Re-extract identical loci from identical BAMs into paired legacy/corrected
representations with identical row sampling and all other settings fixed.
Train classical, scratch, and pretrained controls separately for each encoding;
do not apply corrected depth to a legacy checkpoint and call the difference
an SSL effect. Cross encoding and initialization in a factorial comparison.
The legacy default preserves compatibility, but new runs must record their
chosen encoding and reject mixed shard encodings.

This error is one plausible contributor to weak learned representations. It
does not prove that it caused the historical negative result, nor does fixing
it establish a novel method or a publication claim.
