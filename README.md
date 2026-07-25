# AlignSSL-SV

**Self-supervised representation learning on read-alignment tensors for structural-variant deletion calling — and a negative control that shows why the standard benchmark cannot support the usual claims.**

AlignSSL-SV is a deletion caller for short-read whole-genome sequencing and a direct extension of **DeepSV** (Cai, Wu & Gao, *BMC Bioinformatics* 2019, 20:665). DeepSV renders the read pileup as a hand-designed RGB image and trains a fully supervised CNN. AlignSSL-SV replaces both halves of that design:

1. **An alignment tensor instead of an image.** Reads are encoded directly into a `(C=18, R=64, W=256)` tensor whose channels carry depth, mapping quality, insert-size deviation, orientation, clip signal and base identity. Nothing is quantised into three colour planes, so no information is discarded at the encoding step.
2. **Self-supervised pretraining.** A masked-alignment-modelling (MAM) objective learns a pileup representation from *unlabelled* windows, so the supervised classifier needs far fewer labels. A VICReg-style invariance objective and a combined objective are evaluated as ablations.

The project's second, and in practice more important, contribution is methodological: a set of controls establishing what the widely-used benchmark construction can and cannot demonstrate.

## Headline results (1000 Genomes phase-3 deletions; test = chr12–22)

All deep arms use a harmonised fine-tuning batch size of 96. Error bars span 3–4 seeds (independent *pretraining* seeds for the SSL arms).

### The claim that survives every control: label efficiency

At the smallest label budget (1% ≈ 210 windows) the SSL-pretrained encoder reaches a usable **F1 ≈ 0.51** while the identical from-scratch encoder collapses to **F1 ≈ 0.05** — a ~10× gap, and the result that every control leaves standing. The two converge under full supervision, and the DeepSV-style RGB+CNN baseline is weakest and least stable there.

| Labels | AlignSSL (pretrained) | AlignSSL (scratch) | DeepSV baseline |
|-------:|:---------------------:|:------------------:|:---------------:|
|   1%   | **0.514 ± 0.055**     | 0.050 ± 0.040      | 0.434 ± 0.022   |
|   5%   | 0.655 ± 0.035         | **0.734 ± 0.107**  | 0.591 ± 0.063   |
|  10%   | **0.813 ± 0.007**     | 0.763 ± 0.088      | 0.662 ± 0.048   |
|  25%   | 0.846 ± 0.064         | **0.854 ± 0.055**  | 0.834 ± 0.012   |
|  50%   | **0.913 ± 0.014**     | 0.912 ± 0.022      | 0.856 ± 0.033   |
| 100%   | 0.934 ± 0.004         | **0.944 ± 0.003**  | 0.707 ± 0.140   |

### The control that reframes the paper: the benchmark is shortcut-solvable

A twelve-feature gradient-boosted tree on hand-computed summary statistics **beats every deep arm at every label fraction**, including at 1% labels where it reaches F1 0.894 ± 0.002. Worse, a *single untrained feature* — the ratio of mean depth in the window centre to its flanks — separates the classes at **ROC-AUC = 0.955** with no fitting at all.

| Labels | Classical GBT | Classical logreg | AlignSSL (pretrained) |
|-------:|:-------------:|:----------------:|:---------------------:|
|   1%   | **0.894 ± 0.002** | 0.877 ± 0.008 | 0.514 ± 0.055 |
| 100%   | **0.939 ± 0.001** | 0.871 ± 0.000 | 0.934 ± 0.004 |

This is a property of how positive and negative windows are drawn, not of any model. Uniformly sampled negatives sit at background depth while heterozygous and homozygous deletions sit below it, so the centre-versus-flank depth contrast is nearly sufficient on its own. Mean depth alone is uninformative (AUC 0.502) — the leak is specifically in the *localised* contrast that the extraction protocol builds into every positive window. Two non-depth features also reach substantial discrimination independently, so neutralising depth alone would not be enough.

Consequently **we do not claim state-of-the-art deletion calling on this benchmark**, and two claims that earlier drafts made are formally withdrawn: superior calibration and cross-ancestry robustness. Both are measured on the same shortcut-solvable task and neither survives the classical control. A hard-negative re-benchmark using per-scale quantile-matched negatives is in progress; see `docs/AlignSSL_SV_manuscript.md` §6.

### Self-supervised objective ablation

MAM-only leads at 1% labels (0.588 ± 0.117) and the combined objective leads at full supervision (0.934 ± 0.004 vs 0.915 ± 0.014), but the seed-level intervals overlap throughout, so **we do not claim an ordering** among the three objectives. All three deliver the low-label effect.

For the source CSVs and figures see `results/`; for the full report see `docs/AlignSSL_SV_manuscript.md`.

## Repository layout

```
alignssl/            Core package
  tensorize.py         BAM window -> (18,64,256) alignment tensor
  encoder.py           Multi-scale CNN + transformer encoder (d_model=128)
  ssl.py               Self-supervised objective (masked-alignment-modeling)
  heads.py             Deletion classifier + calibration (temperature, MC-dropout)
  data.py              Truth-VCF loading, window datasets, chrom splits
  synth.py             Synthetic BAM / reference generator for unit tests
  deepsv_baseline.py   DeepSV-style RGB-pileup CNN reimplementation (baseline)
scripts/             Runnable drivers
  pfetch_bam.sh          Parallel chunked BAM fetcher (16-way range, integrity-gated)
  extract_tensors.py     Labeled tensor extraction
  extract_pretrain.py    Unlabeled SSL-window extraction
  build_memmap.py        Consolidate shards -> flat float16 memmap for GPU training
  pretrain_ssl.py        SSL pretraining driver
  finetune_eval.py       Fine-tune + label-efficiency + calibration sweep
  cross_pop_eval.py      Cross-population eval (full labels)
  cross_pop_lowlabel.py  Cross-population eval across the label sweep
  deepsv_baseline_eval.py  DeepSV RGB+CNN representation baseline
  classical_baseline_eval.py  12-feature GBT / logistic-regression controls
  single_feature_auc.py  Untrained single-feature separability control
  extract_tensors_hardneg.py  Quantile-matched hard-negative extraction
analysis/            Aggregation, figures, and manuscript reconciliation
  aggregate_all.py       Per-seed JSON -> canonical results tables
  aggregate_hardneg.py   Hard-negative re-benchmark aggregation
  check_manuscript.py    Asserts every manuscript number matches results/
cluster/             SLURM sbatch templates (fetch, extract, pretrain, finetune, controls)
tests/               Unit and end-to-end tests (`python -m pytest tests/`)
docs/                Manuscript, proposal, literature survey, reviewer report, decks
  AlignSSL_SV_manuscript.md  The paper
  REVIEWER_REPORT.md     Internal adversarial review and its resolutions
  CLUSTER.md             Cluster, filesystem, and full reproduction guide
  project.md             As-built project record
results/             Canonical numbered tables (table1–table8) and figures
  raw_json/              Per-seed raw evaluation output
PROGRESS.md          Development log (latest)
requirements.txt     Python dependencies
```

## Data

- **Reference:** GRCh37 (`hs37d5.fa`).
- **Truth set:** the 1000 Genomes phase-3 merged SV genotypes (`ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz`). The set has 40,975 deletions across 2,504 samples.
- **BAMs:** the 1000 Genomes high-coverage PCR-free alignments. The samples give a mix of ancestries. Training uses YRI, ASW, CHB, MXL, TSI, and GIH. The cross-population test holds out CEU.
- This repository does not hold the BAM files, because each file is 150–260 GB. To get the BAM files again, use `scripts/pfetch_bam.sh` and `cluster/*.sbatch`.
- To reproduce the full pipeline on the cluster — filesystem layout, conda environments, job submission, and all practical steps — read `docs/CLUSTER.md`.

The Phase-4 headline evaluation will use GIAB HG002 and Truvari. For more data, see `docs/project.md` §15.

## Relationship to prior work

AlignSSL-SV does **not** claim to be the first to use self-supervised learning for structural variants. BASILISC (Banerjee, Stanford Digital Repository 2026, doi:10.25740/jj829qd2843) did this before AlignSSL-SV. The contribution of AlignSSL-SV is more specific: the **image-free alignment-tensor representation** for short-read deletion calling, and the **negative controls** establishing that the standard uniform-negative benchmark is separable by an untrained depth heuristic and therefore cannot support calibration or ancestry-transfer claims. For the full novelty analysis, see `docs/AlignSSL_SV_novelty_verdict.md`.

## Status

Research code under active development; a preprint is in preparation. The results above come from the six-sample multi-ancestry panel with CEU held out. The hard-negative re-benchmark that follows from the separability control is running. For current state and open items see `PROGRESS.md`.
