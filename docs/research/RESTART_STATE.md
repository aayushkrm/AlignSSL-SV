# Research restart — 2026-09-22

## Objective and evidence standard

Improve self-supervised read-alignment learning for structural-variant deletion
calling and develop publication-worthy evidence. Seek a reproducible gain over
matched from-scratch and strong classical controls, without guaranteeing that
the hypothesis will succeed. Keep the original representation, label-efficiency,
calibration, generalization and eventual call-set evaluation aims visible.
Infrastructure repairs alone do not satisfy that objective.

## Verified starting state

- Repository cloned into `/Users/akm/aayushkrm-AlignSSL/repo` from
  `https://github.com/aayushkrm/AlignSSL-SV`.
- Starting commit: `fa3e3b482e15b5f0c7aa0d96ef3a0843bb425a28`.
- SSH login to the documented cluster/account succeeds on 2026-09-22.
- `ws_list` returns no active workspaces; `ws_restore -l` lists no recovery
  snapshots. `/scratch/igorno-alignssl_sv` does not exist.
- `squeue -u igorno` shows no jobs at initial inspection.
- Existing conda environments include `deepsv2_new`, `bioinfo`, and `truvari_env`.
  A home-directory `deletion_calling` tree is being inventoried for usable data.
- Prior results include negative SSL findings and useful benchmark/protocol
  diagnoses. Historical test sets have been inspected extensively and are
  development evidence for this restart, not pristine confirmation sets.

## Current implementation and review state

- The depth diagnostic and independent audit have been persisted in this
  directory. The audit found a coarse-bin representation defect, biologically
  questionable coverage-view semantics, and direct calibration leakage.
- The depth correction is opt-in and covered by analytic tests. Shards,
  memmaps, checkpoints, and evaluation records now carry `depth_mode`; mixed
  representations are rejected.
- Temperature scaling now uses validation labels only. The validation subset
  remains inside the declared labelled budget; missing or single-class
  validation sets produce an explicit skipped-calibration record.
- The literature worker reached its usage limit after persisting a preliminary
  note. Its external paper verification is incomplete and the note says so.
- The extraction and review workers also reached their usage limit after
  persisting code/tests. Their output is being independently inspected and
  tested before inclusion.
- The `alignssl-scientific-review` automation remains active every six hours and
  requests an independent Luna/max audit at meaningful milestones.

## Cluster recovery state

- Fresh scratch workspace: `/scratch/igorno-alignssl_restart_20260922`, expiring
  2026-10-22 unless extended.
- SLURM job `1597945` failed before application startup on `hydra-n4` with
  signal 53 and produced no application logs.
- A bounded probe, job `1597946`, completed on `hydra-n1` and verified the
  scratch mount and the `deepsv2_new` Python environment.
- Recovery job `1597947` completed on `hydra-n1` in 7m24s. It produced
  1,293,795 reads from three preselected 1-Mb regions plus public GIAB truth and
  hs37d5 reference inputs. All ten manifest file hashes passed, no partial files
  remained, and `pysam.quickcheck` accepted the BAM. The BAM header declares
  hs37d5 and its reference lengths agree with the downloaded reference. The
  source BAM omits `M5` sequence checksums, so exact sequence identity cannot be
  independently proven from its header; retain that limitation in run
  manifests. This dataset is development-only and cannot establish a
  publication claim.

## Verification checkpoint

- Baseline before edits: 289 passed, 29 skipped.
- Current suite from the repository root: 330 passed, 29 skipped in 130.08s.
- `analysis/check_manuscript.py`: passed.
- Released checkpoint archive: 52,913,192 bytes; SHA-256 matches the release
  manifest.
- Real-read depth oracle: job `1597949` checked 63 HG002 windows at bin sizes
  1–64; corrected maximum absolute error 0 and zero mismatched columns. Raw
  record: `results/diagnostics/depth_oracle_hg002_20260923.json`. Failed launch
  `1597948` is retained in the record and produced no scientific output.

## Immediate next gates

1. Resolve the audit's coverage-view and mask-aware pooling finding before
   treating VICReg results as biological evidence.
2. Finish primary-source literature verification and freeze one pilot endpoint.
3. Run diagnostics, then a fair matched pilot; retain per-example predictions,
   every seed, timings, environment, source hash, and split provenance.
4. Reviewer assesses pilot before expanding to independent samples and testing
   a frozen primary hypothesis on an untouched confirmation set.

Scientific improvement and publication readiness remain unproven.
