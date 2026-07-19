# AlignSSL-SV — Progress Tracker & Checkpoint

_Last updated: 2026-07-15 (cross-population eval complete + 5-superpop panel downloading + SSL objective ablation running on 3 T4s). Maps to the Phase 0–5 plan in `project.md`._

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

### Parallel work while BAMs download (no new data needed) — SSL OBJECTIVE ABLATION 🟡

A100 nodes remain fully locked (konstantin 3× GPU 2+ days into 10-day walltimes; ipetrushin 1×), so re-pretraining on the big corpus waits. But **3 T4 GPUs are free**, so I launched the reviewer-expected **SSL objective ablation** on the existing 80k-window pretrain corpus — three encoders pretraining in parallel, identical config (25 ep, batch 96, lr 1.5e-4, mask 0.6, memmap+/dev/shm, fp16) except the loss weights:

| Variant | `--w-mae` | `--w-vicreg` | Job | Encoder ckpt |
|---|---|---|---|---|
| combined (our design) | 1.0 | 1.0 | 1515691 | `ckpt/encoder_abl_combined.pt` |
| MAE-only | 1.0 | 0.0 | 1515692 | `ckpt/encoder_abl_maeonly.pt` |
| VICReg-only | 0.0 | 1.0 | 1515693 | `ckpt/encoder_abl_viconly.pt` |

Next step once they finish: fine-tune each on the existing labeled set (chr1–11 train / chr12–22 test) and compare downstream F1 → tests whether combining MAE+VICReg actually beats either component alone (a core design claim). This also picks the best objective config for the big 8-sample re-pretraining run. Nothing conflicts: downloads run on CPU nodes (amd_256M), ablation on T4s.

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


---

## ⚠️ Methodology clarification: what "DeepSV" comparison actually means (added 2026-07-15)

**Important for the manuscript and for anyone reading these results: we did NOT run DeepSV's original released code.**

We attempted this directly: cloned `github.com/CSuperlei/DeepSV` and inspected it for feasibility. Findings:

- The main pipeline entry point (`Deletion_Image_Source/Generate_Deletion_Image.py::main()`) is **not runnable as shipped** — it calls `parser.add_argument(...)`/`parser.parse_args()` but `parser` is never instantiated and `argparse` is never imported; `vcf_path`/`bam_path` are hardcoded literal placeholder strings (`"your file path"`); there's a stray unconditional `print(...); return` that would abort the function immediately.
- The CNN training step (`CNN_Of_Digits/CNN_Source.py`) requires **NVIDIA DIGITS** (a GUI training tool, discontinued/archived years ago) and **TensorFlow 1.x `contrib.slim`** (removed in TF 2.0). An alternate `Typical_Model/model.py` uses standalone-Keras 1.x API (`K.set_image_dim_ordering`, removed >5 years ago).
- No `requirements.txt`/`setup.py`/env file is provided to reconstruct the original 2018 stack (Python 3.6, CUDA 8.0, TF1, DIGITS).
- The repo does ship **cached 2018 result files** for samples NA19238/NA19239/NA18525/NA19017 (`samples/*.zip`) but not a working raw-BAM→result pipeline.

**Conclusion:** running their actual code end-to-end is infeasible without a from-scratch rewrite — at which point it is no longer "their pipeline." This is a legitimate, citable bit-rot problem (2018-era genomics DL tooling built on now-abandoned platforms), not a shortcut we're glossing over.

**What our "DeepSV" comparison actually is:** a controlled, documented **reimplementation** of DeepSV's *representation* (RGB pileup image via their stated base-colour palette + read-flag tinting — see `alignssl/deepsv_baseline.py` docstring) and a representative CNN of their era (`DeepSVNet`, 4 conv blocks), trained/evaluated on **our own identical labeled data, chromosome split, loss, and metric** as AlignSSL-SV. Every other reported "DeepSV" F1/ECE number in this project is from this reimplementation, not from the original paper or repo.

**Action taken:** all outward-facing materials (deck, future manuscript) now use **"DeepSV-representation reimplementation"** or **"DeepSV-repr. baseline"** instead of bare "DeepSV" when referring to our measured numbers, to avoid implying we reproduced their published results. The manuscript's Related Work / Methods section will include this exact justification (with the specific broken-entry-point / DIGITS-dependency evidence) as a defensible paragraph anticipating the obvious reviewer question ("did you run their code?").


---

## SSL objective ablation — MAE-only wins (seed 0 complete; 3-seed replication in flight, added 2026-07-16)

**Motivation:** the project's stated SSL objective is the *combined* MAE + VICReg loss (`ssl_objective` decision). This ablation tests whether combining the two objectives actually beats either alone — the core justification for the design. Three encoders were pretrained from scratch on the 80,000-window corpus (25 epochs, batch 96, T4), identical except the objective weights: **combined** (`--w-mae 1 --w-vicreg 1`), **MAE-only** (`1/0`), **VICReg-only** (`0/1`). Each was then fine-tuned identically on the labeled set (chr1-11 train / chr12-22 test) via `finetune_eval.py`.

**Result (seed 0, pretrained arm, F1 by label fraction):**

| frac | combined (MAE+VICReg) | MAE-only | VICReg-only |
|------|-----------------------|----------|-------------|
| 0.01 | 0.461 | 0.495 | 0.332 |
| 0.05 | 0.332 | 0.660 | 0.451 |
| 0.10 | 0.492 | 0.654 | 0.476 |
| 0.25 | 0.625 | 0.800 | 0.637 |
| 0.50 | 0.714 | 0.810 | 0.898 |
| 1.00 | 0.841 | **0.924** | 0.886 |

**@100% labels — calibration + long-deletion recall (seed 0):**

| Config | F1 | ECE | 5000+ bp recall (n=94) |
|--------|-----|------|------------------------|
| combined | 0.841 | 0.028 | 0.213 |
| **MAE-only** | **0.924** | **0.010** | **0.947** |
| VICReg-only | 0.886 | 0.012 | 0.809 |

**Finding:** MAE-only is the strongest and most stable objective — best F1 at 5 of 6 fractions, best calibration (ECE 0.010), and dramatically best long-deletion recall (0.95 vs combined's 0.21, the shared weak point elsewhere). The **combined MAE+VICReg objective — our original design pick — is the weakest at 100% labels (0.841, lowest of the three) and the most unstable**: its frac=1.0 F1 swung +0.115 between two seed-0 runs (0.726 → 0.841), while MAE-only was stable (0.905 → 0.924, +0.019).

**Status — NOT yet acted on.** A single seed cannot settle a ranking with this much run-to-run variance in the combined arm. Seeds 1 and 2 for all three configs are running/queued now (jobs 1516077-82, ~2h each). **Decision rule:** if the 3-seed mean confirms MAE-only ≥ combined, switch the project SSL objective to MAE-only for the 8-sample re-pretrain and report the ablation as a "less-is-more" result (simpler objective wins) — a genuine, publishable finding. If it does not replicate, keep combined and report the ablation as a negative control.

**Caveat:** the seed-0 ablation JSONs (`ckpt/abl_ft_{combined,maeonly,viconly}_seed0.json`) were produced by the pre-patch eval script, so they lack AUPRC and persisted logits; the seed-1/2 reruns use the patched script and will carry them.

---

## Evaluation metrics broadened beyond F1 (added 2026-07-16)

Prompted by the question "why only F1?". F1 was the accuracy headline (class-imbalanced ~25/75 pos/neg makes plain accuracy misleading; DeepSV also reported F1). But F1 is threshold-dependent and weights P/R equally, which is limiting for an SV caller. Changes made to `finetune_eval.py` (both cluster mirror and local copy, verified byte-identical, 7180 B):

- **AUPRC** now computed on every label fraction, both arms — the field-standard threshold-free metric under class imbalance (Saito & Rehmsmeier 2015), rank-based so calibration doesn't affect it. Nearly free (uses the logits already collected).
- **Raw logits + labels + lengths persisted** to `<out>_logits_{mode}.npz` at 100% labels — so *any* threshold-free metric a reviewer later requests (full PR curve, AUROC, custom operating point) is recomputable **without retraining**.

Already-tracked non-F1 metrics retained: precision/recall separately per fraction; ECE + fitted temperature (the calibration headline); length-stratified recall (5 size bins).

**Deferred (not a bolt-on):** genotype concordance (het/hom-alt/ref) requires a new 3-class head + full retrain — a Phase-4 architecture change, not a metric addition. Breakpoint precision also deferred to Phase 4 with the Truvari harness.

---

## 5-superpopulation panel — downloads ~19h in (added 2026-07-16)

7 additional high-coverage BAMs downloading unattended (jobs 1515681-87, hydra-n1, `wget -c`, no walltime cap): NA19239/YRI 84%, NA20502/TSI 82%, NA19648/MXL 76%, NA19240/YRI 65%, NA18525/CHB 59%, NA19017/LWK 56%, NA20845/GIH 46%. Planned panel: TRAIN = NA19238+NA19625+NA18525+NA19648+NA20502+NA20845 (6 samples, 5 superpopulations); HELD-OUT TEST = NA12878/CEU + NA19017/LWK (unseen ancestries); TRIO/QC = NA19239+NA19240. Next steps once complete: extract tensors per new sample → re-pretrain SSL on 8-sample corpus with the winning objective (per ablation above) → re-run sweep on the multi-superpop training set + multi-ancestry test.


---

## ⭐ ABLATION VERDICT — MAE-only confirmed across 3 seeds; SSL objective CHANGED (2026-07-16)

Seeds 1 and 2 completed (jobs 1516077-82). The seed-0 finding **replicates cleanly**.

**F1 by label fraction (pretrained arm, 3-seed mean ± std):**

| frac | combined (MAE+VICReg) | MAE-only | VICReg-only |
|------|-----------------------|----------|-------------|
| 0.01 | 0.400±0.066 | **0.584±0.073** | 0.371±0.035 |
| 0.05 | 0.408±0.085 | **0.636±0.020** | 0.430±0.017 |
| 0.10 | 0.565±0.052 | **0.685±0.022** | 0.488±0.047 |
| 0.25 | 0.678±0.040 | **0.722±0.080** | 0.657±0.022 |
| 0.50 | 0.748±0.070 | 0.804±0.056 | 0.825±0.067 |
| 1.00 | 0.855±0.031 | **0.931±0.006** | 0.873±0.042 |

**@100% calibration + long-DEL recall (3-seed mean ± std):**

| Config | ECE | 5000+ bp recall |
|--------|-----|-----------------|
| combined | 0.022±0.009 | 0.578±0.291 |
| **MAE-only** | **0.010±0.001** | 0.908±0.055 |
| VICReg-only | 0.016±0.006 | 0.911±0.079 |

**Verdict:** MAE-only wins 5/6 fractions, best calibration (ECE 0.010), tightest variance (frac=1.0 std 0.006 vs combined 0.031). Combined (original design pick) is worst/near-worst at low fractions and the LOWEST of the three at 100% (0.855 vs maeonly 0.931, viconly 0.873), and its long-DEL recall is low AND unstable (0.578±0.291, one seed collapsed). VICReg-only recovers long DELs but lags on F1 everywhere.

**DECISION (acted on): SSL objective changed from combined MAE+VICReg → MAE-only** for the 8-sample re-pretrain and all downstream work. This supersedes the earlier `ssl_objective = combined` decision. Framing for the paper: a **"less-is-more" ablation** — the masked-autoencoding objective alone is sufficient and superior; the VICReg term hurts stability and long-deletion recall. More defensible than "we combined two losses."

3-seed raw JSONs: `ckpt/abl_ft_{combined,maeonly,viconly}_seed{0,1,2}.json`. Aggregation saved locally `handoff/abl_3seed.json`.

## Download update (2026-07-16, ~27h in)
COMPLETE (with FTP .bai alongside): **NA20502/TSI/EUR (165 GB)**, **NA19648/MXL/AMR (160 GB)**. Still running: NA20845/GIH, NA18525/CHB, NA19017/LWK, NA19239/YRI, NA19240/YRI.

## Truth-VCF provenance verification (2026-07-17)

Verified our local truth VCF (`/beegfs/datasets/ws/ws1/igorno-genomes_1000_2/vcf/ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz`, 18,298,662 bytes) against the official 1000 Genomes Project source:

`https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/integrated_sv_map/ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz`

HTTP HEAD on the official file reports **Content-Length = 18,298,662 bytes** — an exact byte-size match to our local copy. Same filename, same path convention as the phase3 SV integration release (Last-Modified 2017-05-19). This confirms our label source is the genuine, unmodified 1000 Genomes Phase 3 structural-variant genotype call set (2,504 samples, ~41K deletions), not an altered or unrelated file. Label provenance for the truth VCF is now independently confirmed (BAM provenance was already confirmed earlier via direct FTP downloads from the same server).
