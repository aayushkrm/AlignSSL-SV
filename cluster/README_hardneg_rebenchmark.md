# Hard-negative re-benchmark: job chain

The uniform-negative benchmark is close to trivially separable (a single
untrained depth ratio reaches ROC-AUC 0.955; a 12-feature GBT beats every deep
arm at every label budget). This chain rebuilds the labelled set as a
*candidate-filtering* task and re-runs every arm on it.

## Chain (each stage fires on `afterok` of the previous)

1. **`getref2.sbatch`** — re-download `hs37d5.fa` + the phase-3 SV VCF after the
   beegfs source directory was lost. Indexing goes through pysam, because the
   conda `samtools` has a broken `libcrypto.so.1.0.0` link (exit 127) and
   `tabix`/`bgzip` are absent from the environment.
2. **`hnextract3.sbatch`** — `scripts/extract_tensors_hardneg.py` on the two
   surviving BAMs. Runs `tests/test_match_strata.py` first as a gate, so a
   regression in the matching logic fails in seconds instead of after hours.
3. **`hn_classical.sbatch`** — the classical control, 3 seeds, CPU. This is the
   diagnostic that decides whether the remediation worked; it runs *before* the
   GPU arms so that a still-separable benchmark is caught cheaply.
4. **`hn_deep.sbatch`** — array job, one seed per task: pretrained (combined
   objective, a distinct pretraining seed per fine-tune seed), from-scratch, and
   the DeepSV representation baseline.

## Sample scope

Only `NA20845` (GIH) and `NA12878` (CEU) survived the data loss, so the
hard-negative benchmark trains and tests within NA20845 (chr1-11 / chr12-22)
and uses NA12878 as the held-out cross-population sample. The original
six-sample panel cannot be re-extracted; the uniform-negative results retain
their six-sample scope and the two benchmarks are therefore reported
separately rather than as a before/after on identical data.

## Reading the result

Success is **not** "the deep arms improved". Success is that the classical
control no longer dominates. Report whichever way it falls: if the GBT still
wins, the honest conclusion is that alignment-tensor deep learning does not
beat hand-crafted features on this task at this scale.

## Uniform settings

Batch size 96 everywhere (128 OOMs the T4 on 18x64x256 tensors), 30 epochs,
lr 3e-4, 3 seeds per arm.
