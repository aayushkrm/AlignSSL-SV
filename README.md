# AlignSSL-SV

**Self-supervised pretraining on read alignments with calibrated uncertainty for structural-variant (deletion) calling.**

AlignSSL-SV is a deletion-focused structural-variant (SV) caller for short-read whole-genome sequencing. It is designed as a direct, head-to-head extension of and critique of **DeepSV** (Cai, Wu & Gao, *BMC Bioinformatics* 2019, 20:665). Where DeepSV encodes the read pileup as a hand-designed RGB image and trains a fully supervised CNN, AlignSSL-SV replaces that with:

1. **An image-free alignment tensor** — reads are encoded directly into a multi-channel `(C=18, R=128, W=256)` tensor of alignment features (depth, mapping quality, insert-size deviation, orientation, clip signal, base identity), with no lossy RGB rasterization step.
2. **Self-supervised pretraining** — a masked-alignment-modeling (MAM) objective learns a transferable representation of the pileup from *unlabeled* windows, so downstream deletion calling needs far fewer labels.
3. **Calibrated uncertainty** — temperature scaling plus MC-dropout give per-call confidence that is well-calibrated across sequencing depth and ancestry.

## Headline results (1000 Genomes phase-3 deletions; test = chr12–22)

**Label efficiency** — at the smallest label budget (1% ≈ 128 windows) the SSL-pretrained encoder recovers a usable **F1 ≈ 0.40** while both the from-scratch encoder and the DeepSV-style RGB+CNN baseline collapse (F1 = 0.00 and 0.08). The DeepSV-representation baseline plateaus around **F1 ≈ 0.57** at full labels, well below either alignment-tensor variant (≈ 0.80–0.82).

| Labels | AlignSSL (pretrained) | AlignSSL (scratch) | DeepSV baseline |
|-------:|:---------------------:|:------------------:|:---------------:|
|   1%   | **0.400 ± 0.066**     | 0.000 ± 0.000      | 0.081 ± 0.115   |
|   5%   | **0.408 ± 0.086**     | 0.274 ± 0.188      | 0.492 ± 0.029   |
|  10%   | 0.563 ± 0.051         | **0.721 ± 0.065**  | 0.543 ± 0.066   |
|  25%   | 0.677 ± 0.041         | **0.760 ± 0.065**  | 0.302 ± 0.177   |
|  50%   | **0.747 ± 0.078**     | 0.744 ± 0.046      | 0.557 ± 0.250   |
| 100%   | 0.803 ± 0.117         | **0.819 ± 0.036**  | 0.574 ± 0.076   |

**Calibration** — the alignment-tensor models are far better calibrated than the DeepSV baseline (lower expected calibration error is better):

| Model | ECE | Temperature |
|---|:---:|:---:|
| AlignSSL, pretrained | **0.018 ± 0.009** | 0.778 |
| AlignSSL, from scratch | 0.025 ± 0.009 | 0.823 |
| DeepSV baseline | 0.091 ± 0.045 | 1.785 |

**Cross-population generalization** — trained on non-European ancestries, evaluated on held-out CEU (NA12878). SSL pretraining shrinks the generalization gap (in-dist → cross-pop F1 drop) from **+0.117** (scratch) to **+0.015** (pretrained).

See `results/` for the raw CSVs and figures, and `docs/AlignSSL_SV_manuscript.md` for the full write-up.

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
  project.md             As-built project record (current)
  project_versions/      project.md v1 (plan) and v2 (as-built)
  progress_versions/     PROGRESS.md v01–v20 (full development log history)
results/             Result CSVs and publication figures
PROGRESS.md          Development log (latest)
requirements.txt     Python dependencies
```

## Data

- **Reference:** GRCh37 (`hs37d5.fa`).
- **Truth set:** 1000 Genomes phase-3 merged SV genotypes (`ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz`), 40,975 deletions across 2,504 samples.
- **BAMs:** 1000 Genomes high-coverage PCR-free alignments, selected for ancestry diversity (YRI, ASW, CHB, MXL, TSI, GIH for training; CEU held out for cross-population test).
- BAM files themselves are not committed (each is 150–260 GB). `scripts/pfetch_bam.sh` and `cluster/*.sbatch` reproduce their retrieval.

GIAB HG002 + Truvari benchmarking is planned as the Phase-4 headline evaluation (see `docs/project.md` §15).

## Relationship to prior work

AlignSSL-SV does **not** claim primacy on "self-supervised learning for structural variants" as a category — BASILISC (Banerjee, Stanford Digital Repository 2026, doi:10.25740/jj829qd2843) precedes us there. Our contribution is narrower and specific: the **image-free alignment-tensor representation**, combined with **calibrated, ancestry-transferable uncertainty**, for short-read deletion calling. See `docs/AlignSSL_SV_novelty_verdict.md` for the full adversarial novelty analysis.

## Status

Research code, active development. Results above are from the initial multi-ancestry panel; see `PROGRESS.md` for the current state and open items.
