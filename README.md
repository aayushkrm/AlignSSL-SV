# AlignSSL-SV

**A self-supervised method to find structural-variant deletions from read alignments. The method gives calibrated uncertainty.**

AlignSSL-SV is a caller for structural-variant (SV) deletions. It uses short-read whole-genome sequencing data. It is a direct extension of **DeepSV** (Cai, Wu & Gao, *BMC Bioinformatics* 2019, 20:665). This project also shows the limits of DeepSV and compares the two methods directly.

DeepSV changes the read pileup into a hand-made RGB image. Then it trains a fully supervised CNN. AlignSSL-SV uses a different method with three parts:

1. **An alignment tensor with no image.** AlignSSL-SV changes the reads directly into a tensor with many channels. The tensor has the shape `(C=18, R=64, W=256)`. The channels hold alignment features: depth, mapping quality, insert-size difference, orientation, clip signal, and base identity. AlignSSL-SV does not make an RGB image, so it does not lose data in that step.
2. **Self-supervised pretraining.** A masked-alignment-modeling (MAM) task learns a representation of the pileup from *unlabeled* windows. This lets the deletion caller use fewer labels.
3. **Calibrated uncertainty.** Temperature scaling and MC-dropout give a confidence value for each call. The confidence value is well-calibrated across different sequencing depths and different ancestries.

## Headline results (1000 Genomes phase-3 deletions; test = chr12–22)

All arms below use a harmonized fine-tuning batch size of 96, with error bars across 3–4 seeds (pretraining seeds for the SSL arm).

**Label efficiency.** The SSL-pretrained encoder gets a usable **F1 ≈ 0.51** at the smallest label budget (1% ≈ 210 windows). At the same budget, the from-scratch encoder collapses (F1 ≈ 0.05) — a ~10× gap that is the headline result. The two alignment-tensor models converge at full supervision (0.934 pretrained vs. 0.944 from-scratch), while the DeepSV-style RGB+CNN baseline is the weakest and most unstable at full labels (0.707 ± 0.140).

| Labels | AlignSSL (pretrained) | AlignSSL (scratch) | DeepSV baseline |
|-------:|:---------------------:|:------------------:|:---------------:|
|   1%   | **0.514 ± 0.055**     | 0.050 ± 0.040      | 0.434 ± 0.022   |
|   5%   | 0.655 ± 0.035         | **0.734 ± 0.107**  | 0.591 ± 0.063   |
|  10%   | **0.813 ± 0.007**     | 0.763 ± 0.088      | 0.662 ± 0.048   |
|  25%   | 0.846 ± 0.064         | **0.854 ± 0.055**  | 0.834 ± 0.012   |
|  50%   | **0.913 ± 0.014**     | 0.912 ± 0.022      | 0.856 ± 0.033   |
| 100%   | 0.934 ± 0.004         | **0.944 ± 0.003**  | 0.707 ± 0.140   |

**Calibration.** The alignment-tensor models are much better calibrated than the DeepSV baseline. A lower expected calibration error (ECE) is better.

| Model | ECE | Temperature |
|---|:---:|:---:|
| AlignSSL, pretrained | **0.008 ± 0.002** | 0.634 |
| AlignSSL, from scratch | 0.007 ± 0.000 | 0.586 |
| DeepSV baseline | 0.072 ± 0.068 | 1.411 |

**Cross-population generalization.** The models train on non-European ancestries, then are evaluated on held-out CEU (NA12878) across the label-fraction sweep. The pretrained encoder's transfer advantage is concentrated in the **low-label regime**: at 1% labels it reaches held-out CEU **F1 0.518 ± 0.062** (near-lossless from its in-distribution 0.542), while the from-scratch model has not learned to call deletions (CEU F1 0.179). At full supervision the two paradigms transfer comparably — pretraining's ancestry-robustness benefit is specifically a low-label phenomenon.

**Which SSL objective matters.** A 3-seed ablation shows a crossover: masked-alignment modeling (MAM) drives the low-label benefit (F1 0.588 at 1% labels vs. 0.554 VICReg-only, 0.514 combined), while the combined MAM+VICReg objective is strongest from 25% labels upward and at full supervision (0.934 vs. 0.915 MAM-only). MAM is indispensable for label efficiency; combining it with VICReg is the right default when moderate-to-full supervision is available.

For the source CSVs and the figures, see `results/`. For the full report, see `docs/AlignSSL_SV_manuscript.md`.

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
