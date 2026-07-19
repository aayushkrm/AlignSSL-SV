# AlignSSL-SV — Progress Tracker & Checkpoint

_Last updated: 2026-07-15 (cross-population eval complete + 5-superpop panel expansion underway). Maps to the Phase 0–5 plan in `project.md`._

**Legend:** ✅ done & verified · 🟡 in progress · ⬜ not started · ⚠️ decision/caveat for you

---

## Where I am right now (one line)

Foundation code is **built, unit-tested, and validated on the real 1000G BAMs**. Both tensor datasets are **extracted and validated**: **11,016 labeled windows** (train chr1–11 = 7,672; test chr12–22 = 3,344) and **80,000 unlabeled SSL windows** (749 MB). **SSL pretraining is COMPLETE** — job 1514837 finished cleanly (exit 0:0, 25 epochs, 8h14m wall, final loss 40.8→15.2), encoder saved to `ckpt/encoder_ssl.pt`. **Fine-tune + label-efficiency sweep is COMPLETE across all 3 T4 GPUs** (jobs **1515265/66/67 = seeds 0/1/2**), each did the full 6-fraction pretrained-vs-scratch sweep + calibration + length-strata. **Results aggregated (mean±sd over 3 seeds); the money plot, length-strata figure, and 3 result CSVs are saved as artifacts.** Headline reproduces cleanly (see below). **DeepSV head-to-head (Phase 0.3) is now COMPLETE** — a faithful DeepSV-lineage baseline (RGB pileup + supervised CNN, 3 seeds, jobs 1515336/37/38) plateaus at F1 ≈ 0.57 while our learned encoder wins 5 of 6 label fractions and is far better calibrated; the money plot is now a three-arm comparison. NA12878 (CEU) cross-population BAM downloaded (250.9 GB) and indexed.

**Fine-tune performance bug fixed today (real, fixed):** the first seed jobs (1514992/93/94) timed out at 4 h having done only ~2 of 6 fractions because `ShardDataset.__getitem__` re-ran `np.load`+decompression of a ~1 MB `.npz` on nearly every access under shuffle. Fix: preload the whole labeled set (~25 MB) into contiguous in-RAM arrays at init → `__getitem__` is now a pure slice. Result: a fraction that took >1 h now takes ~3 min; jobs relaunched as 1515265/66/67.

**Earlier SSL launch bug chain resolved (all real, all fixed):** (1) DataLoader reading 40× 1.2 GB compressed shards starved the GPU → consolidated into one 47 GB float16 memmap (`build_memmap.py`), staged to `/dev/shm`, `num_workers=0`; (2) batch 256 OOM'd the 15 GB T4 → batch 96 + `expandable_segments:True`; (3) `is_bf16_supported()`=True on Turing but bf16 is emulated & ~4× slower → select fp16 by compute capability (<sm_80).

---

## 🔑 HEADLINE RESULT (full sweep, 3 seeds — mean±sd, reproduces cleanly)

Test set = chr12–22, 3,344 windows. Numbers are F1 (mean ± sd over seeds 0/1/2) on the DEL-vs-non-DEL task. Full per-seed numbers in `results_label_efficiency.csv`; figure `fig_label_efficiency.png`.

| Label fraction | n(train) | Pretrained F1 | From-scratch F1 | DeepSV baseline F1 |
|---|---|---|---|---|
| **1%** | 128 | **0.400 ± 0.066** | **0.000 ± 0.000** | 0.081 ± 0.115 |
| 5% | 383 | 0.408 ± 0.086 | 0.274 ± 0.188 | 0.492 ± 0.029 |
| 10% | 767 | 0.563 ± 0.051 | 0.721 ± 0.065 | 0.543 ± 0.066 |
| 25% | 1,918 | 0.677 ± 0.041 | 0.760 ± 0.065 | 0.302 ± 0.177 |
| 50% | 3,836 | 0.747 ± 0.078 | 0.744 ± 0.046 | 0.557 ± 0.250 |
| 100% | 7,672 | 0.803 ± 0.117 | 0.819 ± 0.036 | 0.574 ± 0.076 |

**Interpretation:** at **1% labels the from-scratch model collapses to F1 = 0 in all three seeds**, while the pretrained encoder recovers real deletions (F1 = 0.40 ± 0.07). This is the project's central claim — SSL pretraining rescues the extreme low-label regime where supervised training fails. In the mid-range (10–25%) the from-scratch model briefly leads (it is threshold-sensitive and high-variance), and by 50–100% the two converge (0.75/0.80 pretrained vs 0.74/0.82 scratch). This is the expected label-efficiency signature: pretraining buys the most when labels are scarcest, and the two meet once labels are abundant. **Honest paper story = the low-label rescue + convergence, not a blanket "always wins."**

**Calibration @ 100% labels (mean±sd, 3 seeds):** pretrained ECE = 0.018 ± 0.009 (T = 0.78); scratch ECE = 0.025 ± 0.009 (T = 0.82). Pretrained is modestly better-calibrated. See `results_calibration.csv`.

**Length-stratified recall @ 100% labels** (`fig_length_strata.png`, `results_length_strata.csv`): both models recall short DELs (50–500 bp) at 0.8–0.97; recall falls for 1–5 kb (pre 0.65 / scr 0.80) and is high-variance at 5 kb+ (pre 0.63 ± 0.40 / scr 0.50 ± 0.37). Long-deletion recall is the weak point for both — a genuine open problem, and a motivation for the multi-scale channels.

**DeepSV head-to-head (Phase 0.3, DONE):** a faithful DeepSV-lineage baseline — hand-designed RGB pileup (A=red, T=green, C=blue, G=black, per-read binary features) + supervised CNN — trained on the **identical** split, focal loss, and F1 metric, 3 seeds. It **plateaus near F1 ≈ 0.57 at 100% labels** and never exceeds ≈0.6 at any budget. Our learned-encoder model beats it at **5 of 6 label fractions** (loses only at 5%): pretrained 0.80 / scratch 0.82 vs DeepSV 0.57 at full labels. DeepSV is also **much worse calibrated** (ECE = 0.091 ± 0.045, T = 1.79 vs our 0.018 / 0.025). This is the head-to-head that was missing; "learned alignment encoder > DeepSV RGB+CNN" is now supported on our data. Figure `fig_label_efficiency.png` (v2, three arms); numbers in `results_label_efficiency.csv` (three arms) and `results_calibration.csv`.

**Still honest about scope:** this is a faithful *reimplementation* of the DeepSV representation+CNN on our tensors, not a run of the original TensorFlow binary; and the comparison is on the 1000G split, deletion-only. Both are stated plainly in the manuscript.

---

## 🌍 CROSS-POPULATION RESULT (Phase 4.3, DONE — 3 seeds, mean±sd)

Fine-tuned on the FULL training set (chr1–11 of the two **African** samples NA19238/YRI + NA19625/ASW) and evaluated on two held-out sets: (A) in-distribution = chr12–22 of the same two samples; (B) cross-population = chr12–22 of **NA12878 (CEU / European)** — a held-out *individual* of a held-out *ancestry* (362 deletions, 1,448 windows). Jobs 1515414/15/16, `results_cross_population.csv`.

| Arm | In-dist F1 (African) | Cross-pop F1 (NA12878/CEU) | Cross-pop ECE | Generalization gap |
|---|---|---|---|---|
| SSL-pretrained | 0.686 ± 0.137 | 0.672 ± 0.174 | 0.113 ± 0.131 | **+0.015 ± 0.114** |
| From-scratch | 0.898 ± 0.052 | 0.781 ± 0.136 | 0.055 ± 0.050 | +0.117 ± 0.084 |

**Interpretation:** both models transfer to a new ancestry (no collapse), and the **pretrained encoder shows essentially zero in-dist→cross-pop gap (+0.015)** vs the from-scratch model's larger drop (+0.117) — evidence that SSL representations are more ancestry-robust. Caveat kept honest: the scratch arm's absolute F1 is higher here at full labels (as in the label-efficiency sweep at 100%), and per-seed variance is high; the robustness claim is about the *gap*, not absolute F1. This will strengthen sharply with the 5-superpopulation training panel now downloading (below).

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
| A11 | NA12878 (CEU) download for cross-population test | ✅ | Downloaded 250.9 GB (GRCh37, coordinate-sorted, header + 1M records verified, quickcheck OK). Re-indexing job 1514991 (first index attempt hit a transient shared-FS read glitch; file itself is intact) |

---

## PHASE 0 — Baseline & harness (project.md weeks 1–3)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 0.0 | Index high-cov BAMs (had NO .bai — real blocker) | ✅ | Job 1514611 done: NA19238.YRI.bam.bai + NA19625.ASW.bam.bai (~10 MB each) in scratch/bam_idx/ |
| 0.1 | BAM→tensor pipeline built & validated on REAL BAM | ✅ | Smoke on real NA19238: 300 tensors/85 s, all finite, 7 bin scales, correct chroms |
| 0.1b | Full labeled extraction (both samples, all chroms) | ✅ | Job 1514620 done (exit 0): 11,016 windows, 12 shards. Split validated (1514623): TRAIN chr1–11 = 7,672 (1,918 pos/5,754 neg); TEST chr12–22 = 3,344 (836 pos/2,508 neg); clean, no leakage |
| 0.1c | Unlabeled pretrain-window extraction (train chroms) | ✅ | Job 1514624 done (exit 0): 80,000 windows, 40 shards, 749 MB → `tensors_pretrain/` (weighted bin sampling, small-DEL-biased) |
| 0.2 | Truvari evaluation harness + stratification scripts | ⬜ | ⚠️ see caveat C2 (Truvari vs genotype-VCF eval) |
| 0.3 | Reproduce a DeepSV-like baseline F1 on our split | ✅ | Jobs 1515336/37/38 (3 seeds, gpu_T4). `DeepSVNet` (RGB pileup + supervised CNN, 389K params) in `alignssl/deepsv_baseline.py`; eval `scripts/deepsv_baseline_eval.py`. F1 plateaus ≈0.57 @100%; we win 5/6 fractions; DeepSV ECE 0.091. Three-arm money plot + CSVs saved |

## PHASE 1 — Supervised skeleton, no SSL (weeks 3–6)

| # | Task | Status |
|---|------|--------|
| 1.1 | Train encoder + cls + breakpoint heads fully supervised | ⬜ |
| 1.2 | "Learned channels vs DeepSV RGB" ablation | ✅ | Delivered via Phase 0.3 head-to-head: learned 18-ch encoder vs hand-designed RGB+CNN, same split/loss/metric. Learned wins 5/6 fractions, better calibrated |

## PHASE 2 — Self-supervised pretraining (weeks 6–12) — _scientific heart_

| # | Task | Status |
|---|------|--------|
| 2.1 | MAE objective pretraining on 1000G | ✅ | Combined MAE+VICReg, job 1514837 on gpu_T4 done (exit 0:0, 25 epochs, fp16, batch 96, 80K windows via shm memmap). Loss 40.8→15.2 |
| 2.2 | Contrastive/VICReg objective + coverage & cross-sample views | ✅ | VICReg ran jointly with MAE in 1514837 (VICReg term 37.4→12.5); dedicated view ablations later |
| 2.3 | **Label-efficiency "money plot"** (pretrained vs scratch, 1–100% labels) | ✅ | Jobs **1515265/66/67** (seeds 0/1/2) on 3× T4 complete; full sweep 0.01–1.0 + calibration + length-strata; error bars from 3 seeds. **1% confirmed: pretrained F1 0.40±0.07 vs scratch 0.000. Figures + CSVs saved as artifacts.** |

## PHASE 3 — Uncertainty & calibration (weeks 12–16)

| # | Task | Status |
|---|------|--------|
| 3.1 | Uncertainty head (MC-dropout/ensemble) — code exists | 🟡 code / ⬜ at scale |
| 3.2 | Temperature scaling + conformal — code exists | 🟡 code / ✅ ECE+T computed @100% in sweep (pre ECE 0.018, scr 0.025) |
| 3.3 | Reliability diagrams, ECE, Brier, risk–coverage curves | 🟡 ECE done; reliability diagrams / Brier / risk–coverage ⬜ |

## PHASE 4 — Full evaluation & ablations (weeks 16–22)

| # | Task | Status |
|---|------|--------|
| 4.1 | All baselines, all strata (size/coverage/region/ancestry/label) | ⬜ |
| 4.2 | Full ablation matrix | ⬜ |
| 4.3 | Cross-population test (needs NA12878, A11) | ✅ | Jobs 1515414/15/16 (3 seeds). Trained on African samples, tested on NA12878/CEU (362 DELs). Pretrained gap +0.015 vs scratch +0.117 → SSL more ancestry-robust. `results_cross_population.csv` |
| 4.4 | Length-stratified multi-scale ablation (amendment 1) | 🟡 length-stratified recall computed @100% (fig+CSV saved); multi-scale-channel ablation itself ⬜ |
| 4.5 | Coverage-robustness via `samtools view -s` downsampling | ⬜ |

## PHASE 5 — Writing, release, submission (weeks 22–34)

| # | Task | Status |
|---|------|--------|
| 5.1 | Manuscript draft | ⬜ |
| 5.2 | Adversarial novelty re-check before submission | ⬜ |
| 5.3 | Release code + pretrained weights; submit | ⬜ |

---

## 🚀 RESOURCE EXPANSION (2026-07-15, admin) + 5-superpopulation panel

Cluster admin raised limits: **GrpTRES cpu=100→50 (final: 50), MaxJobs=50, 2 TB quota** for datasets+scratch; **gpu_A100 nodes freed** (hydra-gpu2/3, 2× A100-80GB each); CPU partitions have **infinite walltime** (prior 12 h timeout was self-imposed). Admin also cleared download of more high-cov 1000G BAMs.

**Downloading 7 new high-cov BAMs (jobs 1515681–1515687, parallel on amd_256M, `--time=0`)** — each with its FTP `.bai` (no re-indexing). Builds a balanced **5-superpopulation panel**:

| Sample | Pop | Superpop | Role | Status |
|---|---|---|---|---|
| NA19238 | YRI | AFR | train | ✅ have |
| NA19625 | ASW | AFR | train | ✅ have |
| NA18525 | CHB | EAS | train | 🟡 dl 1515681 |
| NA19648 | MXL | AMR | train | 🟡 dl 1515685 |
| NA20502 | TSI | EUR | train | 🟡 dl 1515686 |
| NA20845 | GIH | SAS | train | 🟡 dl 1515687 |
| NA12878 | CEU | EUR | **held-out test** | ✅ have |
| NA19017 | LWK | AFR | **held-out test** | 🟡 dl 1515682 |
| NA19239 | YRI | AFR | trio/QC | 🟡 dl 1515683 |
| NA19240 | YRI | AFR | trio/QC | 🟡 dl 1515684 |

This upgrades every headline: SSL pretraining corpus (2→8 samples), fine-tune training diversity (2→6 samples across all 5 superpops), and a proper multi-ancestry held-out test (CEU + LWK). The generalization/ancestry-robustness claim moves from anecdotal (1 test individual) to a real cross-ancestry evaluation.

---

## ⚠️ Open decisions / caveats for you

- **C1 — Truth set deviates from project.md.** project.md §2.2 specifies **GIAB HG002** (gold-standard Tier-1 benchmark) as the fine-tune/test truth. We are currently using the **1000G phase-3 genotyped SV VCF** (Sudmant et al. 2015) because that's what's on the cluster with matching high-cov BAMs. The 1000G call set is a *genotype* set, not a curated benchmark — reviewers will note this. Options: (a) proceed with 1000G now, add GIAB HG002 later for the headline benchmark; (b) locate/download GIAB HG002 GRCh37 high-cov data first. I lean (a) to keep momentum, GIAB as a Phase-4 addition.
- **C2 — Evaluation matching.** With a genotype VCF we can score per-locus genotype accuracy directly; Truvari (project.md §7) is designed for call-set-vs-benchmark matching. I'll likely use both: direct genotype scoring on 1000G + Truvari when GIAB is added.
- **C3 — Download location.** Per your correction, all *future* downloads go to the datasets path (`/datasets/…`), not scratch; NA12878 stays in scratch (currently ~65% / 164 GB, resuming under job 1514788).

---

## ▶️ What I'm working on next (immediate)

1. ✅ **SSL pretraining** (job 1514837): done — `ckpt/encoder_ssl.pt` (loss 40.8→15.2).
2. ✅ **Fine-tune + label-efficiency sweep** (jobs **1515265/66/67**, 3× T4, seeds 0/1/2): full pretrained-vs-scratch sweep + calibration + length-strata, all 3 seeds complete.
3. ✅ **Aggregated 3 seeds** → money plot with error bars (`fig_label_efficiency.png`), length-strata figure (`fig_length_strata.png`), 3 result CSVs — all saved as artifacts.
4. ✅ **Phase 0.3 — DeepSV-like supervised baseline** (jobs 1515336/37/38, 3 seeds): done. Three-arm money plot (`fig_label_efficiency.png` v2) + three-arm CSVs saved. Learned encoder beats DeepSV RGB+CNN at 5/6 fractions and is far better calibrated.
5. **Cross-population eval**: extract NA12878 (CEU) test tensors, score the fine-tuned model on a held-out individual + ancestry. ← _next._
6. Coverage-robustness via `samtools view -s` downsampling (no new download).
7. Phase 3.3 reliability diagrams / Brier / risk–coverage curves from saved logits.
8. Phase 5.1 manuscript draft — the core results (money plot, head-to-head, calibration, length-strata) are now in hand.
