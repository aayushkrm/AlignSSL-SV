# AlignSSL-SV

**Three controls for evaluating deep structural-variant callers, and a worked demonstration that their absence manufactured our own headline result.**

AlignSSL-SV is a deletion caller for short-read whole-genome sequencing and a direct extension of **DeepSV** (Cai, Wu & Gao, *BMC Bioinformatics* 2019, 20:665). DeepSV renders the read pileup as a hand-designed RGB image and trains a fully supervised CNN. AlignSSL-SV replaces both halves of that design:

1. **An alignment tensor instead of an image.** Reads are encoded directly into a `(C=18, R=64, W=256)` tensor whose channels carry depth, mapping quality, insert-size deviation, orientation, clip signal and base identity. Nothing is quantised into three colour planes, so no information is discarded at the encoding step.
2. **Self-supervised pretraining.** A masked-alignment-modelling (MAM) objective learns a pileup representation from *unlabelled* windows, so the supervised classifier needs far fewer labels. A VICReg-style invariance objective and a combined objective are evaluated as ablations.

We built this to test whether that design improves label efficiency, calibration and ancestry robustness. It appeared to: at 1% of labels the pretrained encoder beat the identical from-scratch encoder ~11-fold in F1 (*p* = 0.009). **That result does not survive our own controls, and this repository now exists mainly to document why.** Every performance claim the project once made has been withdrawn. What remains is the three controls, the code that implements them, and the evidence that each defect is a property of the standard evaluation design rather than of this implementation.

## Headline results (1000 Genomes phase-3 deletions; test = chr12–22)

All deep arms use a harmonised fine-tuning batch size of 96. Error bars span 3–4 seeds (independent *pretraining* seeds for the SSL arms).

### The headline result, and why it is an artefact

At the smallest label budget (1% ≈ 210 windows) the pretrained encoder reaches F1 0.478 while the identical from-scratch encoder collapses to 0.044 — a 10.89× gap at *p* = 0.009. Those F1s are computed by cutting the positive-class probability at a fixed 0.5, the convention this literature inherits from DeepSV.

A fixed cut conflates ranking quality with calibration. Re-scoring the identical runs three ways:

| Scoring rule | pretrained | scratch | ratio | *p* |
|---|---:|---:|---:|---:|
| F1 at fixed 0.5 cut | 0.478 | 0.044 | **10.89×** | **0.009** |
| F1 at validation-selected τ | 0.483 | 0.413 | 1.17× | 0.407 |
| AUPRC (threshold-free) | 0.524 | 0.427 | 1.23× | 0.348 |

The advantage exists under one scoring rule and no other. At every larger label budget the from-scratch arm is *ahead*. It was never degenerate — it ranked competently and scored timidly, and a fixed cut reads timidity as failure.

A second, independent defect was in our own evaluators: a batch-size floor granted the deep arms up to **2.8× the labels** the classical control received, concentrated in exactly the low-label cells carrying the claim. Both are corrected in `alignssl/protocol.py` (equal budgets, validation labels carved out of the budget rather than granted free) and `analysis/threshold_sensitivity.py`.

### The control that reframes the paper: the benchmark is shortcut-solvable

A twelve-feature gradient-boosted tree on hand-computed summary statistics is **at its ceiling from the smallest label budget onward**: AUPRC 0.937 ± 0.009 at 1% labels, gaining only **+0.038** from a hundred-fold increase in supervision. Worse, a *single untrained feature* — the ratio of mean depth in the window centre to its flanks — separates the classes at **ROC-AUC = 0.955** with no fitting at all. A task that twelve scalars solve to 96% of asymptote after 210 examples cannot discriminate between learned representations.

| Labels | Classical GBT | Best deep arm | its AUPRC | *p* | Leader |
|-------:|:-------------:|:--------------|:---------:|----:|:------|
| 1% | 0.937 ± 0.009 | AlignSSL-pretrained | 0.524 ± 0.052 | 0.005 | control |
| 5% | 0.958 ± 0.006 | AlignSSL-scratch | 0.866 ± 0.022 | 0.016 | control |
| 10% | 0.967 ± 0.004 | AlignSSL-scratch | 0.912 ± 0.030 | 0.087 | tie |
| 25% | 0.971 ± 0.002 | AlignSSL-scratch | 0.936 ± 0.023 | 0.121 | tie |
| 50% | 0.974 ± 0.002 | AlignSSL-scratch | 0.974 ± 0.001 | 0.671 | tie |
| 100% | 0.975 ± 0.001 | AlignSSL-scratch | 0.979 ± 0.001 | 0.003 | **deep** |

Scored threshold-free under the corrected protocol. An earlier draft claimed the control dominated at every budget; it does not. Its lead is significant where labels are scarce — which is the regime pretraining is proposed for — decays to a tie by 10%, and reverses at full supervision.

This is a property of how positive and negative windows are drawn, not of any model. Uniformly sampled negatives sit at background depth while heterozygous and homozygous deletions sit below it, so the centre-versus-flank depth contrast is nearly sufficient on its own. Mean depth alone is uninformative (AUC 0.502) — the leak is specifically in the *localised* contrast that the extraction protocol builds into every positive window. Two non-depth features also reach substantial discrimination independently, so neutralising depth alone would not be enough.

Consequently **we make no performance claim on this benchmark.** Three claims earlier drafts made are formally withdrawn: superior calibration, cross-ancestry robustness, and — as of the thresholding analysis above — label efficiency, which was the headline.

### The repaired benchmark: the shortcut is attenuated, and the result is mixed

We re-extracted the labelled set with **per-scale quantile-matched candidate negatives**, so that a negative window has a centre-versus-flank depth ratio drawn from the same stratum as the positive it is matched to. On the matched training pool that feature measures ROC-AUC 0.504; on the held-out chromosomes it falls from 0.955 to **0.717** — attenuated, not eliminated. Every arm's F1 falls, confirming a genuinely harder task. Because the shared reference directory was lost mid-study and only two alignments were recoverable, this benchmark is single-sample (NA20845 train/in-distribution test, NA12878 held out), with 3,452 training and 1,516 test windows.

| Labels | AlignSSL (pretrained) | AlignSSL (scratch) | DeepSV repr. | Classical GBT | Classical logreg |
|-------:|:---:|:---:|:---:|:---:|:---:|
| 1% (n=35) | 0.302 ± 0.053 | 0.283 ± 0.046 | 0.330 ± 0.025 | 0.250 ± 0.000 | **0.476 ± 0.076** |
| 5% (n=173) | 0.368 ± 0.072 | 0.359 ± 0.095 | 0.411 ± 0.036 | **0.626 ± 0.054** | 0.596 ± 0.025 |
| 10% (n=345) | 0.446 ± 0.024 | 0.510 ± 0.140 | 0.419 ± 0.018 | **0.719 ± 0.029** | 0.615 ± 0.026 |
| 25% (n=863) | 0.649 ± 0.024 | 0.734 ± 0.065 | 0.511 ± 0.043 | **0.803 ± 0.013** | 0.624 ± 0.016 |
| 50% (n=1726) | 0.722 ± 0.010 | 0.763 ± 0.063 | 0.538 ± 0.040 | **0.845 ± 0.012** | 0.629 ± 0.007 |
| 100% (n=3452) | 0.844 ± 0.032 | **0.885 ± 0.022** | 0.656 ± 0.009 | 0.869 ± 0.006 | 0.631 ± 0.005 |

AUPRC on the held-out chromosomes, scored threshold-free under the corrected protocol with equal label budgets across arms (Table 12); bold marks the best arm at each budget. Three findings:

1. **The shortcut repair does not rescue the pretraining claim.** At 1% labels the pretrained encoder (0.302 ± 0.053) is indistinguishable from from-scratch (0.283 ± 0.046), and from 10% upward the from-scratch arm is *ahead* at every budget. Pretraining buys nothing once the fixed-threshold artefact is removed.
2. **The hand-crafted control still leads where labels are scarce.** It wins significantly at 1% and 5% (*p* = 0.0003, 0.0004) and ties at the remaining four budgets, including full supervision where the from-scratch network is nominally ahead (0.885 ± 0.022 versus 0.869 ± 0.006, *p* = 0.329). Twelve scalars remain competitive with a pretrained convolutional–attention encoder on a benchmark built so that no single feature exceeds ROC-AUC 0.72.
3. **The learned tensor beats the RGB encoding only once labels suffice.** DeepSV-representation is *ahead* of both tensor arms at the two sparsest budgets (0.330 and 0.411) and only falls behind from 10% upward — so the encoding comparison, the one original claim that survives, is itself budget-dependent.

What does not depend on any scoring convention: quantile-matched candidate negatives attenuate the depth shortcut from ROC-AUC 0.955 to 0.717 without changing the positive set, and every arm's score falls, confirming a genuinely harder task. See `docs/AlignSSL_SV_manuscript.md` §6.

### Self-supervised objective ablation

MAM-only leads at 1% labels (0.588 ± 0.117) and the combined objective leads at full supervision (0.934 ± 0.004 vs 0.915 ± 0.014), but the seed-level intervals overlap throughout, so **we do not claim an ordering** among the three objectives. These are F1 at a fixed 0.5 cut on the uniform benchmark, so both defects above apply: the "low-label effect" all three appeared to deliver is the thresholding artefact, and the benchmark they are measured on is shortcut-solvable. The ablation is reported for completeness and supports no claim about the objectives.

For the source CSVs and figures see `results/`; for the full report see `docs/AlignSSL_SV_manuscript.md`.

## Preprint

`docs/AlignSSL_SV_preprint.pdf` is the typeset manuscript (17 pages, figures
inlined). Rebuild it from source with:

```bash
python analysis/make_figures.py --results-dir results   # regenerate figures
python analysis/check_manuscript.py                     # reconcile numbers vs results/
python analysis/build_preprint.py                       # render the PDF
```

`build_preprint.py` derives the figure mapping from the manuscript's own
`Figure N.` captions and fails the build if a figure file is missing,
duplicated, or the numbering is non-contiguous — so the PDF cannot silently
ship a stale or wrong image.

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
  aggregate_fixed.py     Corrected-protocol aggregation (equal budgets, threshold-free)
  threshold_sensitivity.py  F1@0.5 vs F1@selected-tau vs AUPRC re-scoring
  control_vs_deep.py     Best-of-family control-vs-deep contrasts
  hardneg_arm_contrasts.py  Pairwise arm contrasts on the repaired benchmark
  make_figures.py        All manuscript figures from results/ CSVs
  build_preprint.py      Renders the typeset PDF, gated on figure numbering
  check_manuscript.py    Asserts every manuscript number matches results/
cluster/             SLURM sbatch templates (fetch, extract, pretrain, finetune, controls)
tests/               Unit and end-to-end tests (`python -m pytest tests/`)
docs/                Manuscript, proposal, literature survey, reviewer report, decks
  AlignSSL_SV_manuscript.md  The paper
  REVIEWER_REPORT.md     Internal adversarial review and its resolutions
  CLUSTER.md             Cluster, filesystem, and full reproduction guide
  project.md             As-built project record
results/             Canonical numbered tables (table1–table15) and figures
                       table12–15 are the corrected protocol and supersede table1/table7
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

Research code under active development; a preprint is in preparation. The Section 4 results come from the six-sample multi-ancestry panel with CEU held out; the candidate-filtered benchmark is single-sample for the data-availability reason above. For current state and open items see `PROGRESS.md`.
