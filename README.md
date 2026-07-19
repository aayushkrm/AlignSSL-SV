# AlignSSL-SV

**A self-supervised method to find structural-variant deletions from read alignments. The method gives calibrated uncertainty.**

AlignSSL-SV is a caller for structural-variant (SV) deletions. It uses short-read whole-genome sequencing data. It is a direct extension of **DeepSV** (Cai, Wu & Gao, *BMC Bioinformatics* 2019, 20:665). This project also shows the limits of DeepSV and compares the two methods directly.

DeepSV changes the read pileup into a hand-made RGB image. Then it trains a fully supervised CNN. AlignSSL-SV uses a different method with three parts:

1. **An alignment tensor with no image.** AlignSSL-SV changes the reads directly into a tensor with many channels. The tensor has the shape `(C=18, R=128, W=256)`. The channels hold alignment features: depth, mapping quality, insert-size difference, orientation, clip signal, and base identity. AlignSSL-SV does not make an RGB image, so it does not lose data in that step.
2. **Self-supervised pretraining.** A masked-alignment-modeling (MAM) task learns a representation of the pileup from *unlabeled* windows. This lets the deletion caller use fewer labels.
3. **Calibrated uncertainty.** Temperature scaling and MC-dropout give a confidence value for each call. The confidence value is well-calibrated across different sequencing depths and different ancestries.

## Headline results (1000 Genomes phase-3 deletions; test = chr12–22)

**Label efficiency.** The SSL-pretrained encoder gets a usable **F1 ≈ 0.40** at the smallest label budget (1% ≈ 128 windows). At the same budget, the from-scratch encoder and the DeepSV-style RGB+CNN baseline both fail (F1 = 0.00 and 0.08). The DeepSV-representation baseline stops at about **F1 ≈ 0.57** at full labels. This value is much lower than the two alignment-tensor models (≈ 0.80–0.82).

| Labels | AlignSSL (pretrained) | AlignSSL (scratch) | DeepSV baseline |
|-------:|:---------------------:|:------------------:|:---------------:|
|   1%   | **0.400 ± 0.066**     | 0.000 ± 0.000      | 0.081 ± 0.115   |
|   5%   | 0.408 ± 0.086         | 0.274 ± 0.188      | **0.492 ± 0.029** |
|  10%   | 0.563 ± 0.051         | **0.721 ± 0.065**  | 0.543 ± 0.066   |
|  25%   | 0.677 ± 0.041         | **0.760 ± 0.065**  | 0.302 ± 0.177   |
|  50%   | **0.747 ± 0.078**     | 0.744 ± 0.046      | 0.557 ± 0.250   |
| 100%   | 0.803 ± 0.117         | **0.819 ± 0.036**  | 0.574 ± 0.076   |

**Calibration.** The alignment-tensor models are much better calibrated than the DeepSV baseline. A lower expected calibration error (ECE) is better.

| Model | ECE | Temperature |
|---|:---:|:---:|
| AlignSSL, pretrained | **0.018 ± 0.009** | 0.778 |
| AlignSSL, from scratch | 0.025 ± 0.009 | 0.823 |
| DeepSV baseline | 0.091 ± 0.045 | 1.785 |

**Cross-population generalization.** The models train on non-European ancestries. Then they are evaluated on held-out CEU (NA12878). SSL pretraining makes the generalization gap smaller. This gap is the drop in F1 from the in-distribution test to the cross-population test. The gap goes from **+0.117** (scratch) to **+0.015** (pretrained).

For the source CSVs and the figures, see `results/`. For the full report, see `docs/AlignSSL_SV_manuscript.md`.

## Repository layout

```
alignssl/            Core package
  tensorize.py         BAM window -> (18,128,256) alignment tensor
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
  cross_pop_eval.py      Cross-population generalization eval
  deepsv_baseline_eval.py  Baseline training/eval
cluster/             SLURM sbatch templates (download, extract, pretrain, finetune)
tests/               End-to-end pipeline test on synthetic data
docs/                Manuscript, research proposal, literature survey, slide decks
  CLUSTER.md             Cluster, filesystem, and full reproduction guide
  project.md             As-built project record (current)
  project_versions/      project.md v1 (plan) and v2 (as-built)
  progress_versions/     PROGRESS.md v01–v20 (full development log history)
results/             Result CSVs and publication figures
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

AlignSSL-SV does **not** claim to be the first to use self-supervised learning for structural variants. BASILISC (Banerjee, Stanford Digital Repository 2026, doi:10.25740/jj829qd2843) did this before AlignSSL-SV. The contribution of AlignSSL-SV is more specific. It has two parts: the **alignment-tensor representation with no image**, and **calibrated uncertainty that transfers across ancestries**, for short-read deletion calling. For the full novelty analysis, see `docs/AlignSSL_SV_novelty_verdict.md`.

## Status

This is research code in active development. The results above come from the first multi-ancestry panel. For the current state and the open items, see `PROGRESS.md`.
