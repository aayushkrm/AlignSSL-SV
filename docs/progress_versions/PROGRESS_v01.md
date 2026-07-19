# AlignSSL-SV — Progress Tracker & Checkpoint

_Last updated: 2026-07-13. Maps to the Phase 0–5 plan in `project.md`._

**Legend:** ✅ done & verified · 🟡 in progress · ⬜ not started · ⚠️ decision/caveat for you

---

## Where I am right now (one line)

Foundation code is **built and unit-tested on synthetic data**; I am **wiring it to the real 1000G BAMs + SV truth VCF** (the last step before the first real cluster job). NA12878 download is running in the background (~27%).

---

## STAGE A — Foundation (prerequisite for Phase 0; not a numbered phase in project.md)

| # | Task | Status | Evidence |
|---|------|--------|----------|
| A1 | 7-part literature review + research proposal delivered | ✅ | `DeepSV_research_proposal.md`, `DeepSV_survey_table.csv` (62 papers) |
| A2 | Amendment 2 — verify CSV-Filter/VICReg claim | ✅ | Confirmed: CSV-Filter (Xia et al. 2024) uses VICReg (Bardes et al. 2021, arXiv:2105.04906). Citable. |
| A3 | Cluster access + environment map (SLURM, conda, partitions) | ✅ | `ssh:scc`; envs base/bioinfo/deepsv2_new; GPU on `gpu_A100` |
| A4 | Locate + verify real data on cluster | ✅ | hs37d5.fa, SV VCF (40,975 DELs), NA19238+NA19625 high-cov BAMs |
| A5 | Confirm per-sample DEL labels exist | ✅ | NA19238 = 1,469 non-ref DEL; NA19625 = 1,456 (~2,900 total) |
| A6 | Scratch workspace allocated | ✅ | `/scratch/igorno-alignssl_sv` (30 days) |
| A7 | Codebase scaffold: tensorize / encoder / ssl / heads / synth / data | ✅ | `alignssl_sv/alignssl/*.py`, package v0.1.0 |
| A8 | End-to-end smoke test on synthetic BAM | ✅ | SSL loss 23.4→21.5, FT acc 1.0, ECE 0.115→0.037 (PASS) |
| A9 | Multi-scale tensorizer (`bin_size`) — amendment 1 | ✅ | Verified bin=1 (256 bp) & bin=64 (16,384 bp) both give finite `(18,64,256)` |
| A10 | Real-data `data.py`: VCF truth loader + chrom split + multi-scale | ✅ | Verified today: loader gets correct het/hom-alt per sample; DUP/tiny-DEL filtered |
| A11 | NA12878 (CEU) download for cross-population test | 🟡 | Job 1514554, ~27% (66.8 GB / ~250 GB), ETA ~8–9 h |

---

## PHASE 0 — Baseline & harness (project.md weeks 1–3)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 0.1 | BAM→tensor pipeline built & cached | 🟡 | Code done (A9/A10); **extraction sbatch job not yet run on real BAMs** ← *next task* |
| 0.2 | Truvari evaluation harness + stratification scripts | ⬜ | ⚠️ see caveat C2 (Truvari vs genotype-VCF eval) |
| 0.3 | Reproduce a DeepSV-like baseline F1 on our split | ⬜ | Needed for the head-to-head claim |

## PHASE 1 — Supervised skeleton, no SSL (weeks 3–6)

| # | Task | Status |
|---|------|--------|
| 1.1 | Train encoder + cls + breakpoint heads fully supervised | ⬜ |
| 1.2 | "Learned channels vs DeepSV RGB" ablation | ⬜ |

## PHASE 2 — Self-supervised pretraining (weeks 6–12) — _scientific heart_

| # | Task | Status |
|---|------|--------|
| 2.1 | MAE objective pretraining on 1000G (code exists, not run at scale) | ⬜ |
| 2.2 | Contrastive/VICReg objective + coverage & cross-sample views | ⬜ |
| 2.3 | **Label-efficiency "money plot"** (pretrained vs scratch, 1–100% labels) | ⬜ |

## PHASE 3 — Uncertainty & calibration (weeks 12–16)

| # | Task | Status |
|---|------|--------|
| 3.1 | Uncertainty head (MC-dropout/ensemble) — code exists | 🟡 code / ⬜ at scale |
| 3.2 | Temperature scaling + conformal — code exists | 🟡 code / ⬜ at scale |
| 3.3 | Reliability diagrams, ECE, Brier, risk–coverage curves | ⬜ |

## PHASE 4 — Full evaluation & ablations (weeks 16–22)

| # | Task | Status |
|---|------|--------|
| 4.1 | All baselines, all strata (size/coverage/region/ancestry/label) | ⬜ |
| 4.2 | Full ablation matrix | ⬜ |
| 4.3 | Cross-population test (needs NA12878, A11) | ⬜ |
| 4.4 | Length-stratified multi-scale ablation (amendment 1) | ⬜ |
| 4.5 | Coverage-robustness via `samtools view -s` downsampling | ⬜ |

## PHASE 5 — Writing, release, submission (weeks 22–34)

| # | Task | Status |
|---|------|--------|
| 5.1 | Manuscript draft | ⬜ |
| 5.2 | Adversarial novelty re-check before submission | ⬜ |
| 5.3 | Release code + pretrained weights; submit | ⬜ |

---

## ⚠️ Open decisions / caveats for you

- **C1 — Truth set deviates from project.md.** project.md §2.2 specifies **GIAB HG002** (gold-standard Tier-1 benchmark) as the fine-tune/test truth. We are currently using the **1000G phase-3 genotyped SV VCF** (Sudmant et al. 2015) because that's what's on the cluster with matching high-cov BAMs. The 1000G call set is a *genotype* set, not a curated benchmark — reviewers will note this. Options: (a) proceed with 1000G now, add GIAB HG002 later for the headline benchmark; (b) locate/download GIAB HG002 GRCh37 high-cov data first. I lean (a) to keep momentum, GIAB as a Phase-4 addition.
- **C2 — Evaluation matching.** With a genotype VCF we can score per-locus genotype accuracy directly; Truvari (project.md §7) is designed for call-set-vs-benchmark matching. I'll likely use both: direct genotype scoring on 1000G + Truvari when GIAB is added.
- **C3 — Download location.** Per your correction, all *future* downloads go to the datasets path (`/datasets/…`), not scratch; NA12878 stays in scratch (already 27% in).

---

## ▶️ What I'm working on next (immediate)

1. **Tensor-extraction sbatch job** (CPU, `amd_256M`): tile NA19238 + NA19625, build 18-channel tensors around truth DELs + E3 negatives, shard to `/scratch/igorno-alignssl_sv/tensors/`. ← _starting now_
2. SSL pretraining sbatch (`gpu_A100`).
3. Fine-tune + calibrate sbatch → the label-efficiency money plot + length-stratified ablation.
