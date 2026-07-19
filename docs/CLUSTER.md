# Cluster & Compute Guide — AlignSSL-SV

This document gives a new contributor everything needed to continue the project
from its exact current state. It covers the SLURM cluster, the filesystem layout,
the reference data, the conda environments, the end-to-end training and evaluation
workflow, what was trained before versus now, and the practical gotchas that were
learned the hard way. Read it together with the top-level `README.md` (method and
results) and `PROGRESS.md` (chronological log).

> Nothing in this repository requires cluster access to *read*. But to *reproduce*
> the pipeline (download BAMs, extract tensors, pretrain, fine-tune) you need an
> account on the cluster described below or an equivalent SLURM system with GPUs.

---

## 1. The cluster at a glance

| Property | Value |
|---|---|
| Host | `scc.icgbio.ru`, SSH port `8122` |
| Account (user) | `igorno` |
| Group / SLURM account | `stud` (submit with `--account=stud`) |
| OS | AlmaLinux 9.7 |
| Scheduler | SLURM |
| Login node | `hydra-eye1` |
| conda root | `/home/igorno/miniconda3` |
| CPU limit (personal) | 10 CPUs concurrently (association cap for `igorno`) |
| CPU limit (group `stud`) | 100 CPUs (`GrpTRES cpu=100`) |

### GPU partitions

| Partition | Node(s) | GPUs/node | GPU model | VRAM | Notes |
|---|---|---|---|---|---|
| `gpu_A100` | hydra-gpu2, hydra-gpu3 | 2 | NVIDIA A100 80GB PCIe | 80 GB | fastest; supports bf16 |
| `gpu_T4` | hydra-gpu1 | 4 | NVIDIA Tesla T4 | 15 GB | fp16 only; batch ≤ 96 for our tensors |

Both GPU partitions have `MaxTime=UNLIMITED` (default 1 day). Each GPU node has
96 CPUs, ~514 GB RAM, and therefore ~257 GB of `/dev/shm` tmpfs — large enough to
stage our 70.8 GB training memmap.

### CPU partitions (for downloads, extraction, indexing, memmap building)

`amd_256M`, `amd_1Tb`, `amd_2Tb`, `gpunode`, `debug`, `galaxy`. We mostly use
`amd_256M` for I/O-bound and single-threaded CPU jobs (download, extract, memmap
consolidation).

### How to submit jobs

**Important:** on this provider, the platform's `submit_job()` API does **not**
work (no scratch_root configured). All jobs are submitted with **raw `sbatch`**
through `c.call_command()`. Because multi-line scripts get mangled by shell
quoting over SSH, the reliable pattern is: **base64-encode the script, decode it
into a file on the cluster, then act on that file.**

```python
import base64
c = host.compute.create("ssh:scc")
script = b'''#!/bin/bash
#SBATCH --partition=gpu_T4
#SBATCH --account=stud
... your job ...
'''
b64 = base64.b64encode(script).decode()
c.call_command(f"bash -lc 'echo {b64} | base64 -d > /scratch/igorno-alignssl_sv/myjob.sbatch'",
               intent="write sbatch")
out = c.call_command("sbatch /scratch/igorno-alignssl_sv/myjob.sbatch", intent="submit")
```

Raw sbatch jobs are **not** tracked by the platform notification system — poll
their state manually with `sacct -j <jobid>` and tail the log files. Each SSH
command has a 60-second wall-clock cap; keep remote commands short (a long
`du -sh` over a huge tree will time out — scope it to specific directories).

---

## 2. Filesystem layout

There are two storage areas: **scratch** (fast, per-user working space, where all
job I/O happens) and **beegfs** (shared read-only reference datasets).

### 2.1 Reference data (read-only) — `beegfs`

Base path: `/beegfs/datasets/ws/ws1/igorno-genomes_1000_2/`

| Path | Size | What it is |
|---|---|---|
| `fasta/hs37d5.fa` (+`.fai`) | 3.2 GB | GRCh37/hs37d5 reference genome — the coordinate system for all tensors |
| `vcf/ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz` (+`.tbi`) | 18 MB | 1000 Genomes Phase-3 structural-variant truth set: **40,975 deletions across 2,504 samples** — the labels |
| `bam/high_coverage/NA19238.*.bam` | 246 GB | high-coverage BAM, YRI/AFR (already on beegfs) |
| `bam/high_coverage/NA19625.*.bam` | 158 GB | high-coverage BAM, ASW/AFR (already on beegfs) |

The two beegfs BAMs (NA19238, NA19625) were the original pair available without
downloading. Everything else had to be fetched from EBI (see §5).

### 2.2 Working space (scratch) — `BASE=/scratch/igorno-alignssl_sv`

| Subdir / file | Size | Contents |
|---|---|---|
| `code/` | 210 KB | The `alignssl/` Python package + `scripts/` + `cluster/` sbatch templates. **This is a mirror of this repo's code** — sync it here before running. |
| `tensors/` | 89 MB | Labeled tensors for the two beegfs samples (NA19238, NA19625) — 12 shards |
| `tensors_panel/` | 157 MB | Labeled tensors for the downloaded panel samples (NA18525, NA19648, NA20502, NA20845) — 20 shards (5 each) |
| `tensors_na12878/` | 12 MB | Labeled tensors for held-out **test** sample NA12878/CEU — 2 shards |
| `tensors_pretrain/` | 68 GB | **Unlabeled SSL pretrain windows** (60 shards) + the consolidated flat memmap `pretrain_mm.f16` (70.8 GB) and `pretrain_mm.meta.npz` |
| `ckpt/` | 13 MB | Encoder checkpoints (`encoder_ssl*.pt`) + all results JSON (label-efficiency, calibration, cross-pop, ablations, DeepSV baseline) |
| `bam_extra/` | 445 GB | Large BAMs kept on scratch: NA12878 (251 GB, test) and NA20845 (226 GB, GIH/SAS) with their `.bai` |
| `bam_idx/` | 20 MB | `.bai` index files and symlinks (named `<sample>.<pop>.bam.bai`) |
| `logs/` | 2.9 GB | 183 SLURM `.out`/`.err` files — the full job history |
| `*.sbatch` (root) | — | ~50 job scripts accumulated over the project (download, extract, index, QC, pretrain, fine-tune, ablation). The canonical/current templates live in `code/cluster/` and this repo's `cluster/`. |
| `integrated_call_samples.panel` | 55 KB | 1000G sample→population→super-population map |

**Scratch is not backed up.** Treat tensors and checkpoints as the durable
products; BAMs are large and re-downloadable and are deleted after their tensors
are validated (NA12878 and NA20845 are currently retained as insurance).

---

## 3. Conda environments

`source /home/igorno/miniconda3/etc/profile.d/conda.sh` then `conda activate <env>`.

| Env | Purpose | Key packages |
|---|---|---|
| `deepsv2_new` | **Main training env** — all pretrain/fine-tune/eval jobs use this | torch 2.5.1+cu121 (CUDA 12.1), pysam 0.23.3, numpy 2.2.6, scikit-learn 1.7.2 |
| `bioinfo` | samtools / htslib utilities (indexing, `view -c` integrity scans) | samtools |
| `nt_embeddings` | Nucleotide-Transformer embedding experiments (not used by AlignSSL-SV core) | torch 2.1.2+cu118 |
| `base` | login shell only | — |

Every GPU sbatch script begins with:
```bash
source /home/igorno/miniconda3/etc/profile.d/conda.sh
conda activate deepsv2_new
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

---

## 4. The data panel (who is used for what)

The **labeled** set (fine-tune + test) spans six 1000G super-populations; the
**unlabeled** SSL pretrain corpus is a subset.

| Sample | Population | Super-pop | Role | Has pretrain windows? | BAM source |
|---|---|---|---|---|---|
| NA19238 | YRI | AFR | fine-tune (train) | **yes** (20 shards) | beegfs |
| NA19625 | ASW | AFR | fine-tune (train) | **yes** (20 shards) | beegfs |
| NA20845 | GIH | SAS | fine-tune (train) | **yes** (20 shards) | downloaded (kept on scratch) |
| NA18525 | CHB | EAS | fine-tune (train) | no (labeled only) | downloaded (BAM deleted) |
| NA19648 | MXL | AMR | fine-tune (train) | no (labeled only) | downloaded (BAM deleted) |
| NA20502 | TSI | EUR | fine-tune (train) | no (labeled only) | downloaded (BAM deleted) |
| **NA12878** | CEU | EUR | **held-out TEST** | no | downloaded (kept on scratch) |

- **Fine-tune / labeled training panel = 6 samples** (all but NA12878).
- **Held-out generalization test = NA12878 (CEU)** only.
- **SSL pretrain corpus = 3 samples** (NA19238, NA19625, NA20845) = AFR + AFR + SAS,
  **120,000 unlabeled windows / 60 shards**.

> Three samples originally planned for the panel — NA19017 (LWK), NA19240 (YRI trio),
> NA19239 (YRI trio) — were **discarded**: their EBI downloads repeatedly failed the
> BGZF integrity gate (see §5) and, to save time, the panel was frozen at what was
> already validated. If a future contributor wants a larger or more balanced
> pretrain corpus, the path is to re-download NA18525/NA19648/NA20502 (their BAMs
> are gone) and extract pretrain windows, or add fresh samples.

### Tensor format

- **Labeled tensors**: shape `(C=18, R=128, W=256)` float16 — 18 alignment-derived
  channels, up to 128 reads, 256 columns across the window. Stored in `.npz` shards
  with arrays `X` (windows), `chrom`, `bin_size`, `start`, `label` (genotype 0/1/2).
- **Pretrain windows**: shape `(18, 64, 256)` float16, `label = -1` (unlabeled).
- **Chromosome split**: train = chr1–11, test = chr12–22. The *same* shard directory
  serves both splits; `--split train|test` filters by chromosome at load time.

---

## 5. Downloading BAMs (the hard part)

BAMs come from EBI's 1000 Genomes FTP over HTTPS. EBI **throttles per TCP
connection** (~1.6 MB/s single-stream), so a 200 GB BAM is ~1.5 days single-stream.
The fix is `scripts/pfetch_bam.sh`: a **16-way parallel range fetcher** (16
simultaneous `curl --range` chunk downloads, per-chunk byte-length verification,
in-order concatenation) that reaches ~8 MB/s (~5× speedup).

**Critical gotcha:** running **multiple** 16-way jobs at once (e.g. 3 samples ×
16 = 48 simultaneous range requests) triggers **BGZF block corruption at EBI's
cache/proxy layer** — the assembled BAM fails a `samtools view -c` scan. This is
not a script bug. Downloads must be **serialized** (one 16-way job at a time), which
`pfetch_bam.sh` v3 enforces with a cluster-wide mutex. Every download is followed
by a **mandatory full `samtools view -c` BGZF integrity scan** before the BAM is
trusted for extraction.

---

## 6. End-to-end workflow

```
                 beegfs ref (hs37d5.fa, truth VCF)
                         │
   BAM ──pfetch_bam.sh──►│  (16-way, integrity-gated)     [CPU: amd_256M]
                         ▼
   extract_tensors.py  → tensors_panel/  (labeled (18,128,256))   [CPU]
   extract_pretrain.py → tensors_pretrain/ (unlabeled (18,64,256))[CPU]
                         │
   build_memmap.py     → pretrain_mm.f16 (flat float16, 70.8 GB)  [CPU: amd_256M]
                         │
   pretrain_ssl.py     → ckpt/encoder_ssl_seed*.pt  (MAE + VICReg)[GPU: A100/T4]
                         │  (stage memmap → /dev/shm, num_workers=0)
                         ▼
   finetune_eval.py    → ckpt/ft_results_seed*.json               [GPU]
       label-efficiency curve · calibration (ECE, temperature) · length-strata
   cross_pop_eval.py   → ckpt/xpop_results_seed*.json  (NA12878 held-out) [GPU]
   deepsv_baseline*.py → ckpt/deepsv_results_seed*.json (RGB-CNN comparator)[GPU]
```

### Key scripts (all in `scripts/`, mirrored to `code/scripts/` on the cluster)

| Script | Role |
|---|---|
| `pfetch_bam.sh` | parallel integrity-gated BAM download |
| `extract_tensors.py` | BAM → labeled alignment tensors (uses truth VCF for labels) |
| `extract_pretrain.py` | BAM → unlabeled pretrain windows |
| `build_memmap.py` | consolidate `.npz` shards → one flat float16 memmap (`--shard-dir --glob --out`) |
| `pretrain_ssl.py` | SSL pretraining (masked reconstruction + VICReg); `--memmap` uses `MemmapDataset`, `num_workers=0` |
| `finetune_eval.py` | supervised fine-tune + label-efficiency + calibration + length-strata |
| `cross_pop_eval.py` | evaluate on held-out CEU (NA12878) |
| `deepsv_baseline.py` / `deepsv_baseline_eval.py` | DeepSV RGB-pileup CNN comparator on the identical split/metric |

### SSL pretraining specifics

- **Objective**: masked reconstruction (MAE, weight 1.0) + VICReg (sim 25, var 25,
  cov 1). Scheduler OneCycleLR (`pct_start=0.05`).
- **Memmap staging**: the 70.8 GB `pretrain_mm.f16` is copied into the node's
  `/dev/shm` at job start (fits in the ~257 GB tmpfs), then read with
  `mmap_mode='r'` and `num_workers=0` — this avoids per-shard decompression thrash
  and the CUDA-fork deadlock that DataLoader workers cause.
- **T4**: batch 96 fits (peak ~14.1 GB); batch 128 OOMs. fp16 GradScaler (a benign
  `lr_scheduler.step() before optimizer.step()` warning appears — ignore it).
- **A100**: uses bf16 (detected via compute capability ≥ 8); faster, larger batch
  headroom.
- **Runtime**: ~21 min/epoch on T4 (~1.5 s/step); 25 epochs ≈ 8.7 h. A100 is
  substantially faster (finishes the same 25 epochs in ~1.5 h).

---

## 7. What was trained before vs. now

### Before (through Jul 16)
- **SSL encoder**: `encoder_ssl.pt` — pretrained on **2 AFR samples** (NA19238,
  NA19625), **80,000 windows / 40 shards**, single seed, on T4 (25 epochs).
- **Fine-tune sweep**: label-efficiency (pretrained vs from-scratch at label
  fractions 0.01/0.05/0.1/0.25/0.5/1.0), calibration (temperature scaling, ECE),
  length-stratified recall — 3 seeds. Headline: pretrained ECE ≈ 0.018 vs scratch
  ≈ 0.025; both dominate the DeepSV RGB-CNN baseline (F1 ≈ 0.57, ECE ≈ 0.091).
- **Cross-population eval**: NA12878/CEU held-out — 3 seeds (`xpop_results_seed*`).
- **Ablations**: MAE-only vs VICReg-only vs combined SSL objective
  (`encoder_abl_*.pt`, `abl_ft_*` results) — 3 seeds.
- **DeepSV baseline**: RGB pileup + supervised CNN (`deepsv_results_seed*`) — 3 seeds.

### Now (Jul 19, in progress)
- **NA20845 (GIH/SAS) added** to the pretrain corpus → **3 samples, 120,000 windows,
  60 shards**, memmap rebuilt to 70.8 GB. This adds South-Asian ancestry to the
  previously AFR-only pretraining pool.
- **Re-pretraining with 4 seeds** on all 4 free GPUs simultaneously:
  `encoder_ssl_seed0.pt` (A100, hydra-gpu3) + `encoder_ssl_seed{1,2,3}.pt`
  (T4, hydra-gpu1), identical hyperparameters (25 epochs, batch 96, lr 1.5e-4,
  mask 0.6, view-keep 0.5), differing only by random seed — this yields genuine
  **pretraining-seed variance** for the paper.
- **Next**: re-run the full fine-tune / label-efficiency / calibration / length-strata
  sweep and the CEU held-out cross-population eval against the new seed-averaged
  encoders.

---

## 8. Gotchas & lessons (save yourself the debugging)

1. **Submit via base64→file→sbatch.** Multi-line scripts and redirects get mangled
   over the SSH transport; the `submit_job()` API is unavailable here.
2. **60-second SSH command cap.** Scope `du`/`find` to specific directories; a
   full-tree `du` will time out and return empty.
3. **EBI per-connection throttle + concurrent-corruption.** Parallel range fetch is
   fast but must be serialized across samples, and every BAM needs a full
   `samtools view -c` scan before use.
4. **Stage the memmap to `/dev/shm`, `num_workers=0`.** Reading compressed shards
   directly, or using DataLoader workers, thrashes and/or deadlocks (CUDA fork).
5. **T4 batch 96, not 128.** 15 GB VRAM; 128 OOMs on the (18,64,256) tensors.
6. **bf16 only on A100.** The code auto-selects bf16 when compute capability ≥ 8,
   else fp16 GradScaler.
7. **Rebuild the memmap after adding samples.** The consolidated `pretrain_mm.f16`
   is a snapshot; new shards are invisible until `build_memmap.py` is re-run with the
   shard glob `pretrain_*_train_shard*.npz` (do **not** use a bare `*.npz` glob — it
   would swallow the old `pretrain_mm.meta.npz`).
8. **`--account=stud` on every job**, and mind the 10-CPU personal cap (jobs asking
   for more sit in `PENDING (AssocGrpCpuLimit)`).

---

## 9. Related but separate work on the same account

The cluster home/scratch also contains material that is **not** part of AlignSSL-SV
and is intentionally excluded from this repo:

- **CADC (Context-Aware Deletion Caller)** — a separate deletion-calling project of
  the user's, with its own `deepsv/` package and README. Distinct from AlignSSL-SV.
- **Third-party DeepSV repository** (Cai et al. 2019) — the published reference
  implementation, used only for the baseline comparison. Not our code.
- **Copyrighted article full-text** (e.g. the CSV-Filter paper) — kept locally for
  reading, never committed.
- **SSH private keys** — never committed (`.gitignore` excludes `*.ppk`,
  `*_openssh`, `*private*`, `*.pem`, `id_rsa*`).

---

## 10. Quick-start for a new contributor

1. Get an account on `scc.icgbio.ru:8122` (or adapt paths to your own SLURM+GPU host).
2. Clone this repo; `pip install -r requirements.txt` in a Python 3.10/3.11 env with
   PyTorch (or replicate `deepsv2_new`).
3. Sync `alignssl/`, `scripts/`, `cluster/` to `$BASE/code/` on the cluster.
4. Reference data is on beegfs (§2.1); the truth VCF supplies deletion labels.
5. To extend the pretrain corpus: `pfetch_bam.sh` a new BAM → `samtools view -c`
   gate → `extract_pretrain.py` → `build_memmap.py` → `pretrain_ssl.py`.
6. To reproduce results: run `finetune_eval.py`, `cross_pop_eval.py`, and the DeepSV
   baseline; compare against `results/*.csv` in this repo.
7. Poll jobs with `sacct -j <id>` and `tail logs/<name>_<id>.out`.

For the scientific narrative, method design, and novelty positioning, see
`README.md`, `docs/AlignSSL_SV_manuscript.md`, and `docs/project.md`.
