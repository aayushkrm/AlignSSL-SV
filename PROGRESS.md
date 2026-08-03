# AlignSSL-SV — Progress Tracker & Checkpoint

_Last updated: **2026-08-03**. Structure: **Part I** is the current, authoritative
status — read this. **Part II** is the dated chronological log, kept for
provenance; where Part I and Part II disagree, Part I is correct. Maps to the
Phase 0–5 plan in `docs/project.md`, whose §16 carries the matching
audit outcome._

**Legend:** ✅ done & verified · 🟡 in progress · ⬜ not started · ⚠️ decision/caveat for you

---

# PART I — CURRENT STATUS (authoritative)

## I.1 One-paragraph state of the project

Every experiment the plan called for has run, and the plan's central hypothesis
has been **falsified by our own data**. Self-supervised pretraining
(masked-reconstruction + VICReg) on read-alignment tensors does **not** improve
label efficiency for deletion calling once (a) the decision threshold is
selected on validation data rather than fixed at 0.5, (b) every arm receives an
equal label budget, and (c) the benchmark's trivial depth shortcut is closed.
The paper's contribution is therefore a **negative result with a diagnosed
mechanism**, plus two findings of independent value: the standard
uniform-negative deletion benchmark is solvable by a single untrained scalar
feature (ROC-AUC 0.955), and fixed-threshold F1 at small label budgets
manufactures apparent label-efficiency gains. Manuscript, figures, tables and
tests are consistent with this account; `analysis/check_manuscript.py` gates
every number in the prose against `results/`.

## I.2 The three claims that were withdrawn, and why

| Claim | Status | Cause |
|---|---|---|
| ~10x label-efficiency gain from pretraining at 1% labels | **WITHDRAWN 2026-07-31** | Artefact of a fixed 0.5 probability cut plus unequal label budgets; the gap exists at one budget under one scoring rule (*p* = 0.348 on AUPRC) |
| Learned tensor arms are ~10x better calibrated than DeepSV | **WITHDRAWN** | Not reproducible under the corrected scoring path; ECE is now reported without a superiority claim |
| Hand-crafted 12-feature control leads at *every* label budget | **WITHDRAWN 2026-08-03** | True at the two sparsest budgets only; ties at four, marginally behind at full supervision |

The third withdrawal is worth noting explicitly: it cuts *against* the paper's
own preferred framing, not just against its headline. Both corrections were
applied.

## I.3 What survives, and is what the paper argues

1. **The negative result.** On the repaired (candidate-filtered) benchmark under
   the corrected protocol, pretraining does not beat from-scratch training at any
   label budget. `results/table12_label_efficiency_fixed.csv`,
   `results/table15_hardneg_arm_contrasts.csv`.
2. **The benchmark diagnosis.** One untrained feature — centre-versus-flank read
   depth — reaches ROC-AUC 0.955 on the uniform benchmark; the leak is not
   confined to depth (soft-clip rate 0.802, discordant-pair rate 0.732), so repairing only the depth statistic would leave two shortcuts intact.
   `results/table6_single_feature_auc.csv`.
3. **The protocol diagnosis.** The same runs, re-scored three ways at 210 labels:
   F1@0.5 ratio 10.9x (*p* = 0.009), F1@selected-tau 1.17x (*p* = 0.407),
   AUPRC 1.23x (*p* = 0.348). `results/table13_threshold_sensitivity.csv`.
4. **A harder benchmark, released.** Depth-matched negatives attenuate the
   shortcut from 0.955 to 0.717 and drop every arm's absolute score, confirming
   the task is harder rather than relabelled. `results/table9_hardneg_single_feature_auc.csv`.
5. **Learned tensor > DeepSV RGB encoding — with a caveat.** On the uniform
   benchmark the DeepSV-representation arm is **last at five of six budgets**
   (and 4th of 5 at the sparsest). On the candidate-filtered benchmark the
   picture is *not* uniform: at 1% and 5% labels it is mid-pack and actually
   **ahead of both tensor arms** (0.330 versus 0.302/0.283 at 1%), falling behind
   them from 10% upward. The defensible claim is that the learned tensor beats the
   RGB encoding once there are enough labels to train it, not at every budget.
   This is the original comparison that comes closest to holding up, and it is
   still narrower than first reported.
6. **Length-consistent recall** for the tensor models across five length strata,
   where the RGB baseline's per-stratum s.d. is up to 4x larger.

## I.4 Headline numbers (corrected protocol, threshold-free AUPRC)

Candidate-filtered benchmark, held-out chr12–22, best-of-family per budget:

| Budget | *n* labels | Hand-crafted control | Best deep arm | *p* | Leader |
|---|---|---|---|---|---|
| 1% | 35 | 0.476 ± 0.076 | 0.330 ± 0.025 | 0.0003 | control |
| 5% | 173 | 0.626 ± 0.054 | 0.411 ± 0.036 | 0.0004 | control |
| 10% | 345 | 0.719 ± 0.029 | 0.510 ± 0.140 | 0.1211 | tie |
| 25% | 863 | 0.803 ± 0.013 | 0.734 ± 0.065 | 0.2052 | tie |
| 50% | 1726 | 0.845 ± 0.012 | 0.763 ± 0.063 | 0.1484 | tie |
| 100% | 3452 | 0.869 ± 0.006 | 0.885 ± 0.022 | 0.3285 | tie |

Pretrained versus from-scratch on the **uniform** benchmark, the contrast the
project was built to test: 0.524 ± 0.052 versus 0.427 ± 0.138
at 1% labels, and 0.962 ± 0.018 versus 0.979 ± 0.001
at full supervision. Neither difference is significant.

## I.5 Reconciliation against `docs/project.md` (the plan)

| Plan phase | Milestone | Status |
|---|---|---|
| 0 — Baseline & harness | DeepSV reproduced; Truvari harness; tensor pipeline | ✅ tensor pipeline; DeepSV *reimplemented* (original binary not runnable); ⬜ Truvari (caveat C2) |
| 1 — Supervised skeleton | Matches DeepSV without SSL; RGB-vs-learned ablation | ✅ both; the RGB-vs-learned result is one that survived |
| 2 — Self-supervised pretraining | MAE + contrastive; label-efficiency money plot | ✅ built and run; ⚠️ **the money plot's claim is withdrawn** (§I.2) |
| 3 — Uncertainty & calibration | Calibrated caller; ECE + reliability diagrams | ✅ ECE reported; ⬜ reliability diagrams; ⚠️ calibration *advantage* withdrawn |
| 4 — Full eval & ablations | All baselines, strata, ablation matrix, cross-ancestry | ✅ baselines, strata, objective ablation, cross-ancestry, plus two unplanned arms (classical control, candidate-filtered benchmark); ⬜ GIAB HG002 + Truvari (deferred by decision) |
| 5 — Write / release / submit | Manuscript submitted; code + weights released | 🟡 manuscript preprint-ready and internally consistent; code public; ⬜ weights archive; ⬜ submitted |

**Where the plan is now wrong and has been corrected:** `docs/project.md` §5.3,
§11 and §13.1 asserted the withdrawn headline; §12.3 instructed the paper to
lead with it. All four are marked superseded and point at the new §16, which is
the plan document's authoritative status section.

**Two plan decisions that the audit vindicated:** the learnable tensor (§3) and
the DeepSV-representation head-to-head (§1.1) both survived every correction.
**One that it invalidated:** the uniform negative-sampling protocol specified in
§2.3, which is the direct cause of finding 2 above.

## I.6 What is left before preprint

| # | Item | Status |
|---|---|---|
| 1 | Manuscript consistency gate (`analysis/check_manuscript.py`) | ✅ passes |
| 2 | Test suite (26 tests, incl. 20 regression guards for the two protocol defects) | ✅ passes |
| 3 | All 8 figures regenerate from `results/` via one script | ✅ `analysis/make_figures.py` |
| 4 | `docs/project.md` reconciled with the withdrawal | ✅ §16 |
| 5 | Rewrite §12.3-style framing in the manuscript Discussion around the negative result | 🟡 |
| 6 | Zenodo weights + data-availability statement | ⬜ |
| 7 | Phase 4 GIAB HG002 + Truvari external validation | ⬜ deferred to post-preprint by decision |

## I.7 Standing caveats a reviewer will raise

- **Single-sample hard-negative control.** The `/beegfs` datasets workspace
  expired and only two panel BAMs survived, so the candidate-filtered benchmark
  is built from NA20845 (in-distribution) and NA12878 (held-out CEU) alone. A
  genuine scope reduction; documented in the manuscript, not only in
  `cluster/README_hardneg_rebenchmark.md`.
- **Truth set.** 1000G Phase 3 genotypes, not GIAB HG002 (caveat C1).
- **Evaluation.** Direct genotype scoring, not Truvari (caveat C2).
- **Seeds.** 3 per deep arm, 10 per classical arm. Sufficient to *fail* to
  separate arms, and that asymmetry is stated rather than hidden — but it does
  limit how strongly the negative result can be phrased.
- **Deletions only**, short reads only, one reference build (hs37d5).

---

# PART II — CHRONOLOGICAL LOG (provenance; superseded where it conflicts with Part I)

> ⚠️ Everything below is dated and kept for provenance. Numbers in this log were
> correct as recorded under the protocol then in force; most predate the
> 2026-07-31 withdrawal and the 2026-08-03 corrections. **Do not quote from Part
> II.** Part I and `results/` are authoritative.

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
| 0.3 | Reproduce a DeepSV-like baseline F1 on our split | ✅ | Jobs 1515336/37/38 (3 seeds, gpu_T4). `DeepSVNet` (RGB pileup + supervised CNN, 389K params) in `alignssl/deepsv_baseline.py`; eval `scripts/deepsv_baseline_eval.py`. Hardened: DeepSV-repr. is unstable at 100% (0.707 ± 0.140) and **beaten by the pretrained encoder at all six** label fractions; DeepSV ECE 0.072 vs pretrained 0.008 (~10× worse). Three-arm money plot + CSVs saved |

## PHASE 1 — Supervised skeleton, no SSL (weeks 3–6)

| # | Task | Status |
|---|------|--------|
| 1.1 | Train encoder + cls + breakpoint heads fully supervised | ⬜ |
| 1.2 | "Learned channels vs DeepSV RGB" ablation | ✅ | Delivered via Phase 0.3 head-to-head: learned 18-ch encoder vs hand-designed RGB+CNN, same split/loss/metric. Hardened: learned wins **all six** fractions, ~10× better calibrated |

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
| NA19238 | YRI | AFR | train | ✅ have, extracted |
| NA19625 | ASW | AFR | train | ✅ have, extracted |
| NA18525 | CHB | EAS | train | ✅ downloaded (192.4 GB) + extracted (`tensors_panel`, 4,976 tensors) |
| NA19648 | MXL | AMR | train | ✅ downloaded (160.3 GB) + extracted (`tensors_panel`, 4,584 tensors: 1,146 pos / 3,438 neg) |
| NA20502 | TSI | EUR | train | ✅ downloaded (165.3 GB) + extracted (`tensors_panel`, 4,668 tensors) |
| NA20845 | GIH | SAS | train | 🟡 downloading (job 1515687, ~171 GB so far) |
| NA12878 | CEU | EUR | **held-out test** | ✅ have |
| NA19017 | LWK | AFR | **held-out test** | 🟡 downloading (job 1515682, ~176 GB so far) |
| NA19239 | YRI | AFR | trio/QC | ⚠️ **first download was corrupted** — re-downloading (job 1516566) |
| NA19240 | YRI | AFR | trio/QC | 🟡 downloading (job 1515684, ~194 GB so far) |

This upgrades every headline: SSL pretraining corpus (2→8 samples), fine-tune training diversity (2→6 samples across all 5 superpops), and a proper multi-ancestry held-out test (CEU + LWK). The generalization/ancestry-robustness claim moves from anecdotal (1 test individual) to a real cross-ancestry evaluation.

### ⚠️ Data-integrity incident: NA19239 BAM download was corrupted (root-caused, fixed)

The first NA19239 download (253.5 GB, appeared complete with a valid-looking `.bai`) failed tensor extraction twice, at **different byte offsets each time** — first after ~3 shards written, then after 3,500/5,380 loci on retry. Both failures were a BGZF block decompression error (`Inflate operation failed`, `invalid distance too far back`), reproduced independently by **both `pysam` and `samtools view -c`** (samtools additionally confirmed `quickcheck` alone is insufficient — it only validates the header/EOF marker and passed cleanly despite the corrupted block mid-file). Two independent tools failing at real (different) offsets rules out a transient BeeGFS glitch and confirms genuine bit-level corruption in the downloaded file, most likely from an interrupted/incomplete transfer that nonetheless left a file of the expected final size. **Action taken:** quarantined and deleted the corrupted 253.5 GB file (freed scratch quota back to 1.3 TB used), and submitted a fresh `wget --continue` re-download (job 1516566). **Process fix:** future large-BAM downloads should be checksum-verified (e.g. against an MD5/CRC if the FTP mirror publishes one) or at minimum re-scanned with `samtools view -c` (not just `quickcheck`) before being trusted for extraction.

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
4. ✅ **Phase 0.3 — DeepSV-like supervised baseline** (jobs 1515336/37/38, 3 seeds): done. Three-arm money plot (`fig_label_efficiency.png` v2) + three-arm CSVs saved. Learned encoder beats DeepSV RGB+CNN at **all six** fractions (hardened) and is ~10× better calibrated.
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

## SSL objective ablation — MAE-only wins (seed 0 complete; 3-seed replication in flight, added 2026-07-16) — ⚠️ SUPERSEDED

> ⚠️ **Superseded by the hardened ablation of 2026-07-24 (final section).** The "MAE-only wins 5 of 6 fractions" reading below came from a confounded design (one shared seed-0 ablation encoder, batch 128, vs the combined arm's 4 pretraining seeds at batch 96). Corrected result: a crossover — MAM leads at 1–10% labels, **combined wins from 25% upward and at full supervision** and is the adopted default.

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

**Finding (as recorded 2026-07-16 — ⚠️ WRONG, see correction below):** MAE-only is the strongest and most stable objective — best F1 at 5 of 6 fractions, best calibration (ECE 0.010), and dramatically best long-deletion recall (0.95 vs combined's 0.21, the shared weak point elsewhere). The **combined MAE+VICReg objective — our original design pick — is the weakest at 100% labels (0.841, lowest of the three) and the most unstable**: its frac=1.0 F1 swung +0.115 between two seed-0 runs (0.726 → 0.841), while MAE-only was stable (0.905 → 0.924, +0.019).

> ⚠️ **CORRECTION (2026-07-24).** The "5 of 6 fractions" count above does not survive the hardened, single-variable re-run. On seed-matched pretraining encoders with a harmonized batch size of 96, MAM-only is highest at only **3 of 6** fractions (1%, 5%, 10%) and the **combined objective wins the other 3** (25%, 50%, 100%) — including full supervision, where combined is the *best* arm (0.934) rather than the weakest. The claim that combined is "the weakest at 100% labels" is likewise reversed. Full corrected table in the 2026-07-24 section.

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

## ⭐ ABLATION VERDICT — MAE-only confirmed across 3 seeds; SSL objective CHANGED (2026-07-16) — ⚠️ SUPERSEDED

> ⚠️ **This verdict was OVERTURNED by the hardened ablation of 2026-07-24 (see the final section).** The comparison here is confounded: each ablation arm fine-tuned one shared seed-0 encoder (fine-tune variance only) at batch 128, while the combined arm used 4 distinct pretraining seeds at batch 96. On the corrected single-variable design the result is a **crossover** — MAM leads at 1–10% labels, combined wins from 25% upward and at full supervision — and the **combined objective is the adopted default**. Retained below as the auditable record of what was believed and why.

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

> ⚠️ **CORRECTION (2026-07-24) — this verdict and decision are REVERSED.** The "5/6 fractions" count and the "combined is LOWEST at 100%" claim are both artifacts of the confounded design (one shared seed-0 ablation encoder at batch 128 vs the combined arm's 4 pretraining seeds at batch 96). On the hardened, seed-matched, batch-96 re-run: MAM-only is highest at **3 of 6** fractions (1%, 5%, 10%) and **combined wins 25%, 50%, and 100%** — at full supervision combined is the **best** arm (0.934) not the lowest, vs MAM-only 0.915 and VICReg-only 0.846. **The combined MAE+VICReg objective is therefore the adopted default**; MAM-only is preferred only in the extreme low-label regime. The "less-is-more" framing is withdrawn from the paper. Corrected table in the 2026-07-24 section.

3-seed raw JSONs: `ckpt/abl_ft_{combined,maeonly,viconly}_seed{0,1,2}.json`. Aggregation saved locally `handoff/abl_3seed.json`.

## Download update (2026-07-16, ~27h in)
COMPLETE (with FTP .bai alongside): **NA20502/TSI/EUR (165 GB)**, **NA19648/MXL/AMR (160 GB)**. Still running: NA20845/GIH, NA18525/CHB, NA19017/LWK, NA19239/YRI, NA19240/YRI.

## Truth-VCF provenance verification (2026-07-17)

Verified our local truth VCF (`/beegfs/datasets/ws/ws1/igorno-genomes_1000_2/vcf/ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz`, 18,298,662 bytes) against the official 1000 Genomes Project source:

`https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/integrated_sv_map/ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz`

HTTP HEAD on the official file reports **Content-Length = 18,298,662 bytes** — an exact byte-size match to our local copy. Same filename, same path convention as the phase3 SV integration release (Last-Modified 2017-05-19). This confirms our label source is the genuine, unmodified 1000 Genomes Phase 3 structural-variant genotype call set (2,504 samples, ~41K deletions), not an altered or unrelated file. Label provenance for the truth VCF is now independently confirmed (BAM provenance was already confirmed earlier via direct FTP downloads from the same server).


## Manuscript drafted + adversarial novelty re-check (2026-07-18)

**Manuscript.** Wrote a full journal-style draft, `AlignSSL_SV_manuscript.md` (artifact `e2f1fb32-c26f-4ac9-8f5c-b47fb7c8500b`), built entirely from verified result CSVs: Abstract, Introduction (3 DeepSV bottlenecks), Related Work, Methods (18-channel alignment tensor; residual-CNN+Transformer encoder; MAM mask-ratio 0.6; focal loss γ=2; temperature scaling; dropout uncertainty; chr1-11/chr12-22 split; DeepSV-representation baseline), Results (5 tables: label-efficiency, calibration, length-strata, SSL-objective ablation, cross-ancestry), Novelty positioning, Ongoing panel-scale work, Limitations, Conclusion. One correction applied after an internal audit: the original draft claimed MAM "uniformly dominates at every label fraction" — false, since VICReg-only beats MAM-only at the 50% fraction (0.825 vs 0.804); fixed in 3 places to say MAM-only "leads at nearly every fraction, clearly best at full supervision."

**Adversarial novelty re-check.** Searched OpenAlex, PubMed, and arXiv specifically to try to disprove novelty (title-restricted + broad queries across self-supervised/masked/SV/representation-learning terms). Found **one real collision: BASILISC** (Sujay Banerjee, Middlebury College, 2026, Stanford Digital Repository, DOI `10.25740/jj829qd2843`) — a non-peer-reviewed repository deposit that renders read alignments into multi-channel pileup **images**, tokenizes them with a discrete VAE, and pretrains a BEiT vision transformer via masked-**image**-modeling, fine-tuning for SV genotyping on 1000G against HGSVC2 long-read truth. It reports **no calibration and no cross-ancestry analysis**.

Differentiation (now written into the manuscript §2/§5): (1) we pretrain directly on a **continuous 18-channel alignment tensor** — no rendered image, no dVAE tokenizer — while BASILISC keeps the image and learns tokens over it; (2) we are the first to couple SSL-SV representations with **calibrated, ancestry-robust uncertainty** (temperature scaling, ECE, epistemic/aleatoric decomposition, 8× smaller cross-ancestry gap than scratch), which BASILISC does not address at all; (3) MAM as the strongest of three SSL objectives (ablation); (4) joint treatment of all three DeepSV bottlenecks. We now explicitly disclaim primacy on "SSL for SV" as a category (BASILISC precedes us there) and reposition the claim to the specific image-free-representation + calibration/ancestry combination.

A second on-topic hit from the broad sweep, **Cue** (Popic et al. 2023, *Nature Methods*, DOI `10.1038/s41592-023-01799-x`; already catalogued as row 22 of our 62-paper survey), was individually checked and confirmed **not** an SSL collision — it is a fully supervised multi-channel-image + stacked-hourglass-CNN caller with no pretraining component, and if anything reinforces the DeepSV-family "fixed encoding" critique.

The NSR 2024 paper ("Deep-learning based representation and recognition for genome variants," PMID 39606147) was confirmed to be a review/perspective spanning SNV→SV representation learning, not a competing method — cited as a survey reference only.

**Revised novelty scores (post-BASILISC):** Novelty 6/10 (was 7-8), Risk of prior work 5/10 (was 4), Publication potential 7/10, Reviewer confidence 6.5/10 — verdict: **survives novelty review**, contingent on citing BASILISC and repositioning the headline claim, both now done in the manuscript. Full verdict document saved as `AlignSSL_SV_novelty_verdict.md` (artifact `0e640aae-ec3f-4ca7-a6be-b1dd5cbe5981`).

**Download status (poll at 2026-07-18, ~4.9h parallel elapsed / ~28.7h single-stream for NA19239):**

| Sample | Population | Total (GB) | Downloaded (GB) | % | Node |
|---|---|---|---|---|---|
| NA19017 | LWK | 195.6 | 128.9 | 65.9% | hydra-n1 (job 1517108) |
| NA20845 | GIH | 226.0 | 139.8 | 61.9% | hydra-n1 (job 1517109) |
| NA19240 | YRI | 259.3 | 98.4 | 37.9% | hydra-n1 (job 1517110) |
| NA19239 | YRI | 253.5 | 154.4 | 60.9% | hydra-n1 (job 1516567, single-stream) |

All 4 jobs RUNNING, no failures. On completion of each: run `samtools view -c` full-scan integrity gate, then extract into `tensors_panel/` (wipe NA19239's 3 stale shards first).


---

## Update: 2026-07-18 (late) — project.md rewrite completed; pfetch integrity failures root-caused and fixed

**project.md rewrite (previously believed in-progress from an earlier session, actually never saved).** Audited all artifacts named `project.md` and confirmed the saved version was still the original pre-experiment plan (5 separate artifact records existed under this filename from earlier sessions, all pre-implementation). Rewrote it in full: every original section (1–12) retained verbatim with an **"AS IMPLEMENTED"** callout documenting what was actually built, what changed, and why (18-channel tensor vs. planned 8–10; VICReg built directly instead of InfoNCE; MAM-only decision superseding the combined-objective default; classification-only head vs. the planned 3-head design; temperature-scaling+MC-dropout vs. the planned evidential/conformal stack; DeepSV reproduction infeasibility → reimplementation; T4-only compute vs. the A100/H100 assumption; the `/dev/shm` memmap and precision-selection engineering fixes). Added three new sections: §13 Results as of 2026-07-18 (label-efficiency, ablation, length strata, cross-population, panel status), §14 Novelty positioning update (BASILISC differentiation, revised self-assessment scores), §15 Open caveats & deferred work (an explicit 11-item list of scope reductions — breakpoint head, ensembles/evidential/conformal uncertainty, reliability diagrams, coverage-robustness, repeat/segdup stratification, coverage/cross-sample VICReg views, v2 candidate generation, several ablations, experiment tracking, public weight release, linear-probe monitoring). Saved as `project.md` v2 (artifact `1d522a63-7497-4c77-9c12-1dc764711c8b`, version `91581d8b-3f6e-49a3-8291-e4fc6e2358c1`, 49,678 bytes — up from 34,104 bytes). This closes the gap between what the planning document says and what was actually done; PROGRESS.md and project.md are now both current and mutually consistent.

**Confirmed already-saved (no action needed):** `AlignSSL_SV_manuscript.md` (BASILISC differentiation in §2/§5/references, checksum-verified to match the saved artifact `e2f1fb32-c26f-4ac9-8f5c-b47fb7c8500b` exactly) and this file (`PROGRESS.md` itself) were both already saved as of the last session — an earlier continuation summary had incorrectly flagged them as pending unsaved edits.

**pfetch_bam.sh integrity-gate failures — root cause found, fix deployed for future launches.** Both NA20845 (attempt 1) and NA19017 (attempt 1) failed the mandatory `samtools view -c` BGZF integrity scan despite the assembled file's byte count exactly matching the server's Content-Length in both cases — identical failure signature (`bgzf_read` error partway through a compressed block: "506 of 1175 bytes" for NA19017, "645 of 1175 bytes" for NA20845). Investigated by reading `pfetch_bam.sh` end-to-end: the chunk-boundary arithmetic is correct (an exact, non-overlapping, gap-free partition of `[0, TOTAL)`, verified by both the assembled-byte-count check and per-chunk length checks passing). The distinguishing factor: **this was the first production use of pfetch_bam.sh with 3 samples launched simultaneously** (48 concurrent Range requests total against the same EBI host), whereas the earlier 3 successful panel downloads (NA18525, NA19648, NA20502) all used the older single-stream `dl_*` job type, never pfetch. This points to Range-response corruption or cache/proxy confusion under concurrent cross-job load against the same URL — a known failure class for reverse proxies/CDNs whose cache key doesn't vary by Range header — rather than a bug in the script's own logic.

**Fix deployed** (`alignssl_sv/scripts/pfetch_bam.sh`, pushed to cluster at `code/scripts/pfetch_bam.sh` for future launches only — the 3 currently-running retries keep executing their already-loaded script, per standing practice of not disturbing in-flight jobs): (1) a cross-job `mkdir`-based mutex (`.pfetch_download.lock`) so at most one pfetch invocation is in its concurrent-download phase cluster-wide at a time, serializing Range-request contention against the shared host; (2) default parallelism lowered 16→8 chunks per job. Both NA19017 and NA20845 auto-retried per the script's existing 3-attempt logic and are now on attempt 2 (as of this update); NA19240 is still on its first attempt. Will re-check the integrity gate on each as they complete and apply the mutex-patched script to any sample requiring a further retry.

**Download status recheck (2026-07-18, late):** NA19239 (single-stream) at 71% (~176.8 GB), ETA ~13h45m holding steady. NA19240, NA19017 (attempt 2), NA20845 (attempt 2) all RUNNING on hydra-n1.


---

## Update: 2026-07-19 — panel frozen, NA20845 added, GitHub published, 4-seed re-pretrain launched

**Download-discard decision (user-approved).** The EBI concurrent-download corruption (see 2026-07-18 entry) kept failing the BGZF integrity gate for three of the four in-flight samples. Rather than keep fighting the per-connection throttle and cache corruption, the panel was **frozen at what was already validated**. **NA19017 (LWK), NA19240 (YRI trio), and NA19239 (YRI trio) were discarded** — their jobs were cancelled and ~518 GB of orphaned partial data was reclaimed from scratch. The one exception: **NA20845 (GIH/SAS), which had already PASSED integrity** on attempt 2 (`SCAN_OK, reads=560,191,023`), was kept.

**NA20845 extraction complete (job 1517676, COMPLETED 0:0, 01:13:47).** Both tensor sets were extracted from the 226 GB BAM (the BAM is currently retained on scratch at `bam_extra/`, alongside NA12878, as insurance):
- **Labeled tensors** → `tensors_panel/`: 4,968 tensors / 1,242 truth DELs / **5 shards**.
- **SSL pretrain windows** → `tensors_pretrain/`: 40,000 windows / **20 shards**.
Validation gate passed (`labeled_shards_present=True pretrain_shards_present=True`), then the BAM was removed.

**Final frozen panel.**
- **Fine-tune / labeled panel = 6 samples**: NA19238 (YRI/AFR), NA19625 (ASW/AFR), NA18525 (CHB/EAS), NA19648 (MXL/AMR), NA20502 (TSI/EUR), **NA20845 (GIH/SAS)**.
- **Held-out cross-population TEST = NA12878 (CEU/EUR)** only (LWK/NA19017 no longer available).
- **SSL pretrain corpus = 3 samples** (NA19238 + NA19625 + NA20845) = **120,000 unlabeled windows / 60 shards** (compressed `.npz` shards ~2 GiB on disk; consolidated flat float16 memmap `pretrain_mm.f16` = 65.9 GiB / 70.8 GB, so `tensors_pretrain/` totals ~68 GiB) — now spans AFR×2 + **SAS** (previously AFR-only, 2 samples / 80,000 windows).
- ⚠️ Caveat: the SSL pretrain corpus (3 samples) is smaller than the labeled panel (6 samples); the other three labeled samples have no pretrain windows because their BAMs were deleted after labeled-tensor extraction. Re-adding them would require re-downloading three ~200 GB BAMs.

**Memmap rebuilt.** `build_memmap.py` consolidated the 60 pretrain shards (glob `pretrain_*_train_shard*.npz`) into one flat float16 memmap `pretrain_mm.f16` = **70.8 GB, 120,000 windows, shape (18,64,256), all label=−1** (up from 47 GB / 80,000). It stages cleanly into each GPU node's `/dev/shm`.

**4-seed re-pretrain launched on all 4 free GPUs (2026-07-19 16:2x).** The GPU queue was empty (0 pending jobs, any user), so all four seeds started within ~48 s:

| Job | Seed | GPU | Node |
|---|---|---|---|
| 1517715 | 0 | A100 80 GB | hydra-gpu3 |
| 1517716 | 1 | T4 15 GB | hydra-gpu1 |
| 1517717 | 2 | T4 15 GB | hydra-gpu1 |
| 1517718 | 3 | T4 15 GB | hydra-gpu1 |

Identical hyperparameters (25 epochs, batch 96, lr 1.5e-4, mask 0.6, view-keep 0.5), differing only by random seed → gives genuine **pretraining-seed variance** for the paper. A100 (bf16) runs ~3.8× faster per step than the T4s (fp16) — see the completion table below for measured wall times. Loss decreasing cleanly on all four. **Next:** on completion, re-run the full fine-tune / label-efficiency / calibration / length-strata sweep and the CEU held-out cross-population eval against the seed-averaged encoders.

**GitHub repository published.** The complete project is now public at **`github.com/aayushkrm/AlignSSL-SV`** (MIT license, commits authored solely by the user). It contains: the `alignssl/` package (8 modules), `scripts/` and `cluster/` drivers, `tests/`, `results/` (4 CSVs + 2 figures), the full `docs/` set — manuscript, research proposal, 62-paper literature survey, slide decks, novelty verdict, `project.md` v1–v2, and `PROGRESS.md` v01–v20 history. A completeness audit hash-diffed the live clone against the local staging tree: **61/61 tracked files byte-identical**. SSH private keys, large regenerable data (BAMs/tensors/checkpoints), and third-party/copyrighted material are correctly excluded via `.gitignore`.

**README rewritten in ASD-STE100 Simplified Technical English** (commit `1476b0b`): short single-idea sentences, active voice, imperative mood, consistent terminology — all result tables, numbers, technical names, and links preserved verbatim.

**New: `docs/CLUSTER.md`** — a full cluster and reproduction guide so a new contributor can continue from the exact current state: SLURM partitions and limits, the beegfs/scratch filesystem layout, conda environments, the who-is-used-for-what data panel, the integrity-gated download procedure, the end-to-end workflow with an ASCII pipeline diagram, before-vs-now training summary, and the hard-won gotchas (base64→sbatch submission, 60 s SSH cap, EBI throttle/corruption, `/dev/shm` memmap staging, T4 batch-96 limit, bf16-only-on-A100, memmap-rebuild-after-adding-samples).

## Update: 2026-07-20 — 4-seed re-pretrain COMPLETE (all 4 encoders ready)

All four SSL encoders finished the full 25 epochs (1,250 steps/epoch → step 31,200) on the 3-sample corpus (NA19238 + NA19625 + NA20845 = 120,000 windows). Final combined-objective losses are tightly clustered across seeds, confirming stable pretraining:

| Seed | Job(s) | GPU | Wall | Final loss (mae / vic) |
|---|---|---|---|---|
| 0 | 1517715 | A100 80 GB | 03:13:33 | 14.72 (2.64 / 12.08) |
| 1 | 1517730 | T4 15 GB | 12:22:49 | 14.78 (2.67 / 12.11) |
| 2 | 1517732 | T4 15 GB | 12:00:46 | 14.86 (2.66 / 12.21) |
| 3 | 1517731 | T4 15 GB | 12:03:51 | 14.96 (2.66 / 12.29) |

Note: the first T4 launches for seeds 1–3 (jobs 1517716/17/18) were cancelled at epoch 4 and resubmitted as 1517730/31/32, which ran to completion. Checkpoints written to `ckpt/encoder_ssl_seed{0,1,2,3}.pt` (each with a `.hist.json` of 157 log records). **Measured runtime supersedes earlier estimates:** ~3.2 h/A100 and ~12 h/T4 for 25 epochs at batch 96 (A100 ≈ 3.8× faster per step) — see CLUSTER.md §Training. **Next:** run the seed-averaged fine-tune / label-efficiency / calibration (ECE, temperature) / length-strata sweep and the CEU (NA12878) held-out cross-population eval against all four encoders.

## Update: 2026-07-20 (later) — 6-sample fine-tune + cross-population sweep launched

**Consolidated labeled panel.** `ShardDataset` reads a single `shard_dir`, but
the 6 labeled TRAIN samples were split across two directories (`tensors/` for
the 2 beegfs samples, `tensors_panel/` for the 4 downloaded panel samples).
Built `tensors_all6/` — a symlinked union of all 32 shards (6+6+5+5+5+5) — so
one directory serves the full panel. Loading it gives **train=21,016 /
test=9,196** labeled windows, roughly a 2.7× increase over the earlier 2-sample
runs (chr1-11 train / chr12-22 test split, unchanged).

**8 jobs launched** against all 4 seed encoders, on `gpu_T4` (only 3 of 4 GPUs
run concurrently — the 4th is occupied by another user's job, so the queue
processes in pairs):

- **`ft6_s{0,1,2,3}`** (jobs 1517998–1518001): `finetune_eval.py` on
  `tensors_all6/`, label-efficiency (fractions 0.01/0.05/0.1/0.25/0.5/1.0),
  calibration (ECE, temperature scaling), length-stratified recall — same
  protocol as before, now on the full 6-sample panel and all 4 seeds.
- **`xp6_s{0,1,2,3}`** (jobs 1518002–1518005): `cross_pop_eval.py`, trains on
  `tensors_all6/` and evaluates in-distribution vs the held-out CEU sample
  (NA12878, `tensors_na12878/`) — the multi-ancestry generalization check.

**Partial results (seed 0, in progress, label-efficiency arm):** pretrained vs
from-scratch Deletion F1 —

| Label fraction | Pretrained F1 | Scratch F1 |
|---|---|---|
| 1% | 0.531 | 0.021 |
| 5% | 0.635 | 0.560 |
| 10% | 0.809 | 0.878 |
| 25% | 0.884 | 0.791 |

The label-efficiency signal at 1% labels is the headline result: pretraining
reaches F1 ≈ 0.51–0.59 (seeds 0–2) while training from scratch collapses to
F1 ≈ 0.00–0.11 on the same 1% split. At higher label fractions the two arms
converge and occasionally from-scratch edges ahead (expected — with enough
labels, task-specific training closes the gap; the pretraining value proposition
is precisely the low-label regime).

## Update: 2026-07-21 — sweep COMPLETE, 4-seed results aggregated

All 8 jobs finished. The three fine-tune jobs first hit the 5 h walltime and
were killed by SLURM (TIMEOUT) one step short of writing their JSON (the driver
dumps results only at the end); resubmitted with a 12 h limit as `ft6b_s{0..3}`
(jobs 1518335–1518338), all COMPLETED (~5 h 57 m each). Cross-population jobs
`xp6_s{0..3}` all COMPLETED. Aggregated across the 4 pretraining seeds
(mean ± s.d.):

**Label efficiency — Deletion F1 on held-out test (chr12–22).** Train = 6-sample
panel, up to 21,016 windows.

| Labels | n(train) | AlignSSL (pretrained) | From scratch |
|---|---|---|---|
| **1%** | 210 | **0.514 ± 0.055** | **0.050 ± 0.040** |
| 5% | 1,050 | 0.655 ± 0.035 | 0.734 ± 0.107 |
| 10% | 2,101 | 0.813 ± 0.007 | 0.763 ± 0.088 |
| 25% | 5,254 | 0.846 ± 0.064 | 0.854 ± 0.055 |
| 50% | 10,508 | 0.913 ± 0.014 | 0.912 ± 0.022 |
| 100% | 21,016 | 0.934 ± 0.004 | 0.944 ± 0.003 |

**The headline holds and is now 4-seed-robust: at 1% labels pretraining gives a
~10× F1 gain (0.51 vs 0.05).** The arms converge by 50–100% labels — expected,
since with abundant labels supervised training closes the gap; the value of SSL
is precisely the low-label regime. (Note: from-scratch variance is large at
5–25% — it is unstable at low-to-mid label counts, while the pretrained encoder
is consistently tighter, e.g. ±0.007 at 10%.)

**Calibration @100% labels:** pretrained ECE = 0.0078 ± 0.0017 (T = 0.63),
scratch ECE = 0.0072 ± 0.0004 (T = 0.59) — both well-calibrated after
temperature scaling; no meaningful difference at full labels.

**Length-stratified recall @100% labels** (both arms strong; largest deletions
hardest for both): 50–200 bp 0.919/0.917, 200–500 bp 0.913/0.903,
500 bp–1 kb 0.929/0.938, 1–5 kb 0.926/0.954, >5 kb 0.857/0.881
(pretrained/scratch).

**Cross-population (held-out CEU / NA12878):** in-distribution F1 ≈ 0.904 for
both arms; on the unseen CEU sample pretrained F1 = 0.690 ± 0.089 vs
scratch 0.792 ± 0.056. **Honest reading:** at *full* labels the SSL encoder does
**not** improve out-of-distribution transfer here — if anything the from-scratch
model transfers slightly better and is better-calibrated OOD (ECE 0.019 vs
0.068). The multi-ancestry generalization claim therefore rests on the
*low-label* regime (to be run) rather than the 100%-label cross-population
number; the current experiment does not support an OOD-robustness claim at full
supervision, and the manuscript will state this plainly.

Aggregated artifacts saved: `fig_label_efficiency_4seed.png`,
`results_label_efficiency_4seed.csv`, `results_cross_population_4seed.csv`,
`results_length_strata_4seed.csv`.

### Ablation + matched-panel DeepSV head-to-head (also COMPLETE)

A parallel set of jobs (launched separately) finished on the **same 6-sample
panel**, giving the two comparisons the main table needs: (a) does the combined
MAM+VICReg objective beat each single objective, and (b) how does a faithful
DeepSV-lineage baseline (RGB pileup + supervised CNN) do on the *matched* panel.
Ablation encoders `encoder_abl_{maeonly,viconly}_120k.pt` (jobs 1518372/1518371,
~11.9 h each on the 120K corpus); ablation fine-tune `abft6_{mae,vic}_s{0,1,2}`
(jobs 1518382–1518387, ~6 h each); DeepSV `dsv6_s{0,1,2}` (jobs
1518379/1518390/1518391, ~28 min each). Deletion F1 (mean ± s.d.):

| Labels | Combined (MAM+VICReg) | MAM-only | VICReg-only | DeepSV baseline |
|---|---|---|---|---|
| 1% | 0.514 ± 0.055 | **0.547 ± 0.029** | 0.434 ± 0.060 | 0.083 ± 0.059 |
| 5% | 0.655 ± 0.035 | 0.700 ± 0.084 | 0.645 ± 0.025 | 0.551 ± 0.044 |
| 10% | **0.813 ± 0.007** | 0.740 ± 0.128 | 0.732 ± 0.069 | 0.492 ± 0.085 |
| 25% | **0.847 ± 0.064** | 0.809 ± 0.070 | 0.773 ± 0.110 | 0.839 ± 0.001 |
| 50% | **0.913 ± 0.014** | 0.779 ± 0.129 | 0.764 ± 0.046 | 0.827 ± 0.035 |
| 100% | **0.934 ± 0.004** | 0.869 ± 0.102 | 0.832 ± 0.107 | 0.694 ± 0.147 |

**Reading:** masked reconstruction (MAM) drives most of the *low-label* benefit
(MAM-only ≈ combined at 1%; VICReg-only weaker), but the **combined objective
wins clearly at ≥10% labels** and is far tighter (e.g. ±0.007 at 10% vs ±0.13
for MAM-only) — this is the justification for the combined loss. The DeepSV
baseline is worst throughout and unstable at full labels (0.694 ± 0.147). Note
the combined arm has 4 seeds; the ablation and DeepSV arms have 3 seeds each.
Artifacts: `fig_ablation_4arm.png`, `results_ablation_4arm.csv`.

**Next:** (1) run the cross-population eval at *low* label fractions to test
whether the SSL transfer advantage appears where it should; (2) refresh the
length-strata figure for 4 seeds; (3) update `project.md` and the manuscript
draft with these numbers and the honest OOD caveat; (4) fold in GIAB HG002 +
Truvari as the headline benchmark (Phase 4).

## Update: 2026-07-22 — pre-submission HARDENING DAG launched (16 jobs, fixes audit asymmetries A/B/C)

A reviewer-perspective audit (saved as `AUDIT_reviewer_verification.md`) confirmed the results are trustworthy in direction and mechanism, found **no chromosomal leakage** (pretrain shards are chr1–11 only; test is chr12–22), an identical test set across all four arms, and a clean single-variable ablation design. It flagged **three asymmetries** to harmonize before a Q1 submission:

- **(A) Error-bar asymmetry [top priority].** The combined arm's error bars come from **4 distinct pretraining seeds** (`encoder_ssl_seed0–3.pt`), but each ablation arm (MAM-only, VICReg-only) fine-tuned **one shared seed-0 encoder** across 3 fine-tune seeds → ablation bars reflected fine-tune-only variance, not pretraining variance.
- **(B) Seed-count mismatch:** combined = 4 seeds; ablation / DeepSV = 3.
- **(C) Fine-tune batch confound:** combined `ft6` used batch 96; ablation `abft6` and DeepSV `dsv6` used batch 128.

**Fix — one clean single-variable DAG (16 SLURM jobs, all batch 96, num-workers 2, submitted 2026-07-22).** All arms are now harmonized to the combined arm's fine-tune configuration; the only variable that differs between arms is the thing under test.

| Group | Jobs | What | Gating |
|---|---|---|---|
| Pretrain | 1522999–1523002 | MAM-only + VICReg-only, **seeds 1,2** (seed0 encoders reused) → `encoder_abl_{maeonly,viconly}_120k_seed{1,2}.pt` (T4/fp16, 25 ep, batch 96) | none |
| Ablation FT seed0 | 1523003 (MAM), 1523004 (VIC) | fine-tune the existing seed-0 encoders at **batch 96** → `abft6h_{obj}_seed0.json` | none |
| Ablation FT seed1,2 | 1523005–1523008 | fine-tune each **seed-matched** new encoder → `abft6h_{obj}_seed{1,2}.json` | `afterok` on its own pretrain |
| DeepSV rerun | 1523009/11/13 | DeepSV baseline at **batch 96**, seeds 0–2 → `deepsv6h_results_seed{0,1,2}.json` | none |
| Cross-pop low-label | 1523010/12/14 | new `cross_pop_lowlabel.py`: label-fraction sweep evaluating in-dist + NA12878 (CEU) xpop at each fraction, seeds 0–2 → `xpopll_results_seed{0,1,2}.json` | none |

**Startup health check confirmed the objectives are correctly wired** from the live loss decomposition: MAM-only job reports `loss = mae` (VICReg term excluded), VICReg-only job reports `loss = vic` (MAM term excluded). No errors in any log. SLURM self-advances the DAG; the 10-CPU personal cap naturally serializes execution.

**New code (committed, pushed):** `scripts/cross_pop_lowlabel.py` (label-frac cross-population eval) and `analysis/aggregate_hardened.py` (aggregates the 4-arm ablation + cross-pop-low-label JSONs into `results_ablation_4arm_hardened.csv`, `results_crosspop_lowlabel.csv`, `fig_ablation_4arm_hardened.png`, `fig_crosspop_lowlabel.png` — error bars now computed across **pretraining** seeds). GitHub HEAD = `4de3576`.

**On completion:** download the 16 JSONs, run `aggregate_hardened.py`, regenerate the ablation figure with proper per-pretraining-seed error bars, update the manuscript's ablation table + the honest OOD caveat with the low-label cross-population numbers. Then Phase 4 (GIAB HG002 + Truvari) — not yet on the cluster (no HG002 data, Truvari not installed; reference is GRCh37/hs37d5).

---

## ✅ Update: 2026-07-24 — HARDENING DAG COMPLETE (16/16 jobs exit 0); all docs harmonized

The 16-job DAG launched on 2026-07-22 finished with **zero failures** (every job `ExitCode 0:0`). All three audit asymmetries are fixed, results are re-aggregated, and the manuscript, README, deck, `docs/project.md`, and `docs/CLUSTER.md` are harmonized to the final numbers. **The tables in this section are authoritative; earlier tables in this file are pre-hardening and superseded.**

**What the harmonization changed.** Every arm now fine-tunes at **batch 96** with `num_workers 2` (was 128 for the ablation and DeepSV arms), the ablation arms have **seed-matched pretraining encoders** (`encoder_abl_{maeonly,viconly}_120k_seed{0,1,2}.pt`) so their error bars span pretraining variance rather than fine-tune variance, and seed counts are stated explicitly per arm (SSL arms 4 seeds, ablation/DeepSV/cross-pop 3). The only variable differing between arms is the thing under test.

### Objective ablation — the "MAM-only wins" verdict is OVERTURNED; it is a crossover

| Label fraction | MAM-only | VICReg-only | Combined MAM+VICReg |
|---|---|---|---|
| 1% | **0.588** | 0.554 | 0.514 |
| 5% | **0.763** | 0.665 | 0.655 |
| 10% | **0.830** | 0.768 | 0.813 |
| 25% | 0.798 | 0.845 | **0.846** |
| 50% | 0.799 | 0.903 | **0.913** |
| 100% | 0.915 | 0.846 | **0.934** |

**Finding:** MAM drives the low-label benefit (1–10%), but the **combined objective overtakes from 25% labels upward and is best at full supervision**. The earlier 2026-07-16 verdict ("MAE-only wins 5 of 6 fractions; adopt MAM-only; frame as less-is-more") was an artifact of the confounded design — one shared seed-0 ablation encoder plus a different fine-tune batch size. **The combined MAM+VICReg objective is the adopted default** for panel-scale re-training and all moderate-to-full-supervision work; MAM-only is preferred only in the extreme low-label regime. The "less-is-more" framing is withdrawn from the paper. Superseding notes were added in place to `docs/project.md` rather than deleting the original decision, so the record of what was believed and why remains auditable.

### Cross-population, corrected

The earlier full-label-only cross-population run suggested SSL nearly eliminates the ancestry gap (+0.015 vs +0.117). The harmonized low-label sweep shows this **does not hold at full supervision** — pretrained gap +0.148 vs scratch +0.124. What does hold, and is the honest claim, is that at **1% labels the pretrained encoder transfers to held-out CEU at F1 = 0.518** (near its own in-distribution 0.542) while the from-scratch arm is near-collapsed. The multi-ancestry claim therefore rests on the low-label regime, stated that way in the manuscript.

### Documentation corrections made in this pass

- **Tensor shape was wrong in four documents.** `alignssl/tensorize.py` defaults to `max_rows=128`, but extraction was actually run with `--max-rows 64`. Verified against the cluster by loading a real shard: shape is `(18, 64, 256)`. Corrected in README (2 places), `docs/CLUSTER.md`, and `docs/project.md` (2 places, including the dependent per-window byte estimate).
- **Stale "wins 5 of 6 label fractions" claim** (a pre-hardening artifact where DeepSV edged the pretrained arm at 5%) removed from PROGRESS.md, `docs/AlignSSL_SV_deck.md`, and `docs/project.md`. On the harmonized numbers the pretrained arm beats the DeepSV baseline at **all six** fractions.
- Manuscript sections 4.2–4.5 and Section 5/6 rewritten against numbers **recomputed from the raw per-seed JSONs**, not copied between documents. A duplicated figure embed was collapsed to a back-reference.

**Deliverables:** `results/fig_label_efficiency_hardened.png`, `results/fig_cross_population_lowlabel.png`, `results/fig_length_strata_hardened.png`, `results/results_ablation_4arm_hardened.csv`, `results/results_cross_population_lowlabel.csv`, `results/results_length_strata_hardened.csv`, `results/results_calibration_hardened.csv`, `results/results_label_efficiency_4seed.csv`.

**Next:** Phase 4 GIAB HG002 + Truvari headline benchmark. Still blocked on data/tooling: HG002 is not staged on the cluster, Truvari is not installed in `deepsv2_new`, and the reference build is GRCh37/hs37d5 (the GIAB v4.2.1 SV benchmark is distributed for GRCh38, so either a GRCh37-lifted benchmark or a GRCh38 re-alignment path is needed). This requires a storage/staging decision before submission.

---

## ✅ Update: 2026-07-25 — data-loss accounting; figure consolidation; hard-negative chain unblocked

Three defects found and fixed this pass, plus the honest recording of an infrastructure loss.

### The beegfs workspace expired — what it cost and what it did not

`/beegfs/datasets/ws/ws1/igorno-genomes_1000_2/` was a time-limited BeeGFS dataset workspace; it expired and was reclaimed. It held the reference FASTA, the truth VCF, and the NA19238/NA19625 high-coverage BAMs.

**Not lost, and why the results stand:** the reference genome and truth VCF had already been re-staged to `$B/ref/` (`hs37d5.fa`, `ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz`), so every label and coordinate remains reproducible. The extracted tensors — the actual model inputs — were always on scratch. All 32 `tensors_all6/` symlinks were re-verified to resolve; they point into surviving scratch directories, not into the reclaimed workspace. No training or evaluation input was lost.

**Genuinely lost, and it reaches the science:** only two BAMs survive anywhere, both in `$B/bam_extra/` — NA20845 (GIH) and NA12878 (CEU). Any analysis that must re-read *alignments* rather than re-use existing tensors is confined to those two samples. **The hard-negative candidate-filtering control is therefore single-sample** (NA20845 in-distribution, NA12878 held-out CEU) instead of spanning the six-sample panel. This is a real scope reduction, recorded in three places: `docs/CLUSTER.md` §2.1, `cluster/README_hardneg_rebenchmark.md`, and the manuscript's limitations paragraph (§6). Re-obtaining a BAM costs ~40 h single-stream or ~8 h with 16-way parallel chunking.

### The figure markers pointed at pre-hardening images

All five `{{artifact:...}}` embeds in the manuscript resolved to figures generated *before* the hardening pass — Figure 4's pointed at the pre-hardening ablation plot, i.e. the plot showing the overturned "MAM-only wins" pattern. Figure generation was consolidated into `analysis/make_figures.py` (one script, regenerates all five from `results/`) and the markers were repointed to the current artifacts, each replacement guarded by an occurrence-count assertion. Figures are numbered 1–5 contiguously.

Data-fidelity fixes in the same pass: Figure 3's title claimed length *degradation* when the numbers show length *consistency* (recall sd for the DeepSV-representation baseline is up to 4× that of the tensor models — 0.841±0.165, 0.850±0.193 — while both tensor arms hold ~0.86–0.95 across every bin); the top length bin rendered the raw sentinel `1000000000` instead of a `≥` threshold; Figure 2's chance annotation floated away from its reference line; Figure 1's gap annotation was a floating label rather than a bracket spanning the measured gap with the multiplier computed from data.

### The hard-negative chain was dying on a schema mismatch, then on its own gate

**Root cause (silent, expensive).** `scripts/extract_tensors_hardneg.py` wrote `np.savez_compressed(..., x=X, bp0=..., bp1=...)` while `scripts/extract_tensors.py` writes `X=` and a two-column `bp`. Both feed the *same* loader, `alignssl.data.ShardDataset`. So a ~2 h extraction "succeeded" and every downstream evaluator then died with `KeyError: 'X is not a file in the archive'` — job `hncls` (1556879) lasted 9 seconds and the deep array job sat on `DependencyNeverSatisfied`.

**Fix, and a static guard.** The hard-negative extractor now writes the canonical schema. `tests/test_shard_schema.py` (new) parses the single `np.savez_compressed` call in each extractor with `ast`, collects every field `ShardDataset` subscripts out of the archive, and asserts the keyword sets agree and cover every loader field. Verified it fails on the old code and passes on the fix. Because extraction is expensive and the failure is silent at write time, the gate runs *inside* the sbatch before extraction starts.

**Second-order failure.** `deepsv2_new` has no pytest, so the gate's top-level `import pytest` aborted with `ModuleNotFoundError` before the pytest-free `__main__` block could run — job 1556926 died in 7 s with the gate never executing. The import is now optional (a shim supplies the one decorator the module uses). Verified both paths: 9 passed under `pytest tests/`, and the PASS line prints when the file runs as a script with pytest blocked from `sys.meta_path`. Confirmed in `deepsv2_new` on the cluster before resubmitting.

### Chain currently running

`1556929` (hnext4, amd_256M) → `1556930` (hncls2, amd_256M) → `1556931_[0-2]` (hndeep2, gpu_T4, batch 96). Both pre-extraction gates passed in the cluster environment: quantile matching removes the depth-ratio shortcut (uniform-negative AUC 0.951 → quantile-matched 0.504, pos median 0.429 vs matched median 0.429), and the extractors agree on the shard schema. The classical/separability arm is deliberately sequenced *before* the GPU arms so a still-separable benchmark costs ~2 CPU-minutes instead of GPU-hours; `hn_single_feature_auc.csv` compared against `results/table6_single_feature_auc.csv` is the number that says whether the depth leak is closed.

**Next:** on completion run `analysis/aggregate_hardneg.py` (→ table7, table8, `stats_hardneg.csv`), state whether the leak is closed, regenerate figures, and update the manuscript and README — including restoring or permanently withdrawing the two claims currently marked withdrawn (calibration superiority, cross-ancestry robustness). Then Phase 4 (GIAB HG002 + Truvari), still blocked on staging: HG002 is not on the cluster, Truvari is not installed in `deepsv2_new`, and the reference is GRCh37/hs37d5 while the GIAB v4.2.1 SV benchmark ships for GRCh38.
