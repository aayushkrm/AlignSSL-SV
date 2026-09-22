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
- Read thinning and row pooling now have opt-in corrected modes with checkpoint
  provenance and compatibility guards. Historical modes remain the default;
  the required objective ablation has not run.
- The core external literature ledger is verified in
  `2026-09-22-literature-directions.md`; BASILISC's full methods remain
  inaccessible and are marked unresolved.
- The extraction and review workers also reached their usage limit after
  persisting code/tests. Their output is being independently inspected and
  tested before inclusion.
- The `alignssl-scientific-review` automation remains active every two hours and
  requests a GPT-6 Sol/high scientific audit at meaningful milestones. The
  automation prompt records actual model dispatch because the heartbeat itself
  does not expose a model selector.

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
- The three regions contain 30 Tier1 records marked `SVTYPE=DEL`, but only 14
  are at least 50 bp. That is insufficient for a credible train/test learning
  comparison and confirms the slice must remain a representation/infrastructure
  diagnostic. Expansion must be selected by a label-blind rule and use an
  upstream candidate set rather than truth-centred windows for the main pilot.
- The current NIST HG002 v5.0q GRCh37 structural-variant VCF/BED is staged in
  `/scratch/igorno-alignssl_restart_20260922/giab-hg002-v5-grch37`. The three
  data files match NIST MD5 values. The README MD5 disagrees with NIST's own
  checksum listing and is documented in `2026-09-23-data-decision.md`. The
  three pilot windows contain only 11 v5.0q deletion records of at least 50 bp.
- The final Manta 1.6.0 container is frozen at
  `/home/igorno/alignssl_restart_20260922/tools/manta-1.6.0--py27h9948957_6.sif`
  (SHA-256 `283022f0b46085579be8f13c356e7b513763cbb3d4f01fd3be392260d0ab330f`).
  No new candidate pool has been generated yet.
- The HGSVC3 v1.0 GRCh38 sequence-resolved SV VCF, index, README, and manifest
  are staged at `/scratch/igorno-alignssl_restart_20260922/hgsvc3-v1-grch38-sv`
  and pass the release MD5 checks. It contains 65 sample columns; 63 have exact
  public 30× Illumina CRAM index matches, with NA21487 and NA24385 unmatched.
  A remote HG00512 CRAM/CRAI availability and header check passed (15.7 GB CRAM).
  Full reference compatibility, pedigree-safe splits, and per-donor
  confident-negative regions remain to be verified before cohort selection.
  A reproducible `scripts/audit_hgsvc3_genotypes.py` pass counted 64,428 DEL
  records ≥50 bp and 9,003–12,165 carrier records per donor, with substantial
  missing genotype calls. See `2026-09-23-hgsvc3-genotype-audit.md`; these
  record-level counts do not define confident-negative regions.
- The inspected HGSVC3 v1.0 release inventories have no donor-wide callable
  BED, although PAV documents callable output and the larger working archives
  are not yet inspected. A primary-source metadata comparison found 18 of 25
  canonical contigs with matching lengths but mismatched M5s between the HGSVC
  VCF and IGSR/NYGC reference; chr1 was reproduced independently. Read the
  paired `2026-09-23-hgsvc3-callability-audit.md` and
  `2026-09-23-hgsvc3-reference-audit.md`. Do not bulk-download the matched
  CRAMs until the reference and negative-region gates resolve.
- Manta fixture job `1598015` failed before application startup on `hydra-n12`
  with signal 53. Its replacement `1598016` is pending on `hydra-n1`; no
  candidate output exists yet. Do not duplicate that job while it is live.

## Verification checkpoint

- Baseline before edits: 289 passed, 29 skipped.
- Current suite from the repository root: 337 passed, 29 skipped in 132.12s.
- `analysis/check_manuscript.py`: passed.
- Released checkpoint archive: 52,913,192 bytes; SHA-256 matches the release
  manifest.
- Real-read depth oracle: job `1597949` checked 63 HG002 windows at bin sizes
  1–64; corrected maximum absolute error 0 and zero mismatched columns. Raw
  record: `results/diagnostics/depth_oracle_hg002_20260923.json`. Failed launch
  `1597948` is retained in the record and produced no scientific output.

## Immediate next gates

1. Obtain independent review of the corrected view/pooling implementation and
   freeze its ablation before treating VICReg results as biological evidence.
2. Select independent donors using assembly-derived truth, compatible short
   reads, and validated callable regions. Then freeze the pilot endpoint.
3. Run diagnostics, then a fair matched pilot; retain per-example predictions,
   every seed, timings, environment, source hash, and split provenance.
4. Reviewer assesses pilot before expanding to independent samples and testing
   a frozen primary hypothesis on an untouched confirmation set.

Scientific improvement and publication readiness remain unproven.
