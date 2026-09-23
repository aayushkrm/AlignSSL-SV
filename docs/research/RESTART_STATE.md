# Research restart — 2026-09-22

## Objective and evidence standard

Develop a genuinely novel, scientifically rigorous structural-variant research
contribution with meaningful evidence. The 2026-09-23 objective revision
explicitly permits leaving SSL, the current architecture, benchmark, and even
candidate filtering; it rules out using DeepSV as the new scientific
foundation. Preserve prior negative results and infrastructure as evidence,
but compare alternative research questions before substantial compute. No
positive result is guaranteed. Infrastructure repairs alone do not satisfy
the objective.

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
- The 2026-09-22 SSL-focused [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md) is now a
  suspended preliminary option, not the approved next experiment. The
  primary-source comparison in `2026-09-23-research-pivots.md` ranks
  candidate-recall failure in difficult strata as a lead for a cheap
  falsification test, not an approved method or positive result.

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
  BED. A reported member-header survey of both named `20240307_PAV_VCF`
  working TARs found no callable BED member; independent replay is pending,
  and this says nothing about other archives or rerunning PAV. PAV's smoothed
  `_500` BED can bridge unaligned gaps, so raw alignment coverage is required
  for any negative label. A primary-source metadata comparison found 18 of 25
  canonical contigs with matching lengths but mismatched M5s between the HGSVC
  VCF and IGSR/NYGC reference. A publisher-MD5-verified HGSVC no-ALT FASTA
  matches all 194 HGSVC VCF shared-contig digests but only 176 IGSR digests;
  the difference is genuine. A complete 18-contig base-difference map from
  completed job `1598070` records 13,923,221 unequal bases in 152 verified
  BED intervals, mirrored with JSON, hashes, and job logs in
  `results/reference_reconciliation/2026-09-23/`. An independent review found
  shared-`N` sequence between mismatch intervals; the BED is not a callability
  or safe-exclusion mask. Job `1598069` failed before comparison because its
  `samtools` executable lacked a runtime library; that log is preserved.
  Read `2026-09-23-hgsvc3-callability-audit.md`,
  `2026-09-23-hgsvc3-reference-audit.md`, and
  `2026-09-23-reference-reconciliation.md` and the map review. Do not
  bulk-download the matched CRAMs until the reference and negative-region gates
  resolve.
- Manta fixture jobs `1598015` (`hydra-n12`) and `1598016` (`hydra-n1`) both
  failed in four seconds with scheduler signal 53 before application startup.
  No Manta-named output directory was found in the scratch workspace. The
  `sacct` evidence is in `results/cluster_jobs/2026-09-24-manta-fixture-sacct.txt`.
  No candidate set exists; do not submit a third identical fixture without a
  revised scientific need and launch-failure diagnosis.
- IGSR full-reference snapshot job `1598077` and dependent ambiguity-scan job
  `1598079` completed and verified the 3,263,683,042-byte IGSR FASTA, all
  3,366 IGSR and 194 HGSVC sequence M5s, and separate complete non-ACGT BEDs.
  On the 194 shared contigs, the 165,046,090-base joint ambiguity BED contains
  all 13,923,221 unequal bases; it is **not** a donor-callability or safe SV
  exclusion mask. The source FASTAs and indexes were hash-verified after
  preservation in `/home/igorno/alignssl_restart_20260922/references/`.
  SLURM preserve job `1598082` failed on a compute-node read-only home mount;
  the login-node copy succeeded and the archive hashes passed again on
  2026-09-24. An independent reviewer accepted only the narrow saved-map
  sequence claim and left cohort selection blocked; its requested Sol/high
  configuration was not independently attested by the reviewer runtime.
  Frozen-input re-comparison job `1598267` completed in 1m29s and exactly
  reproduced all 18 BEDs and scientific summary fields from hashed FASTAs:
  13,923,221 unequal bases in 152 intervals. This closes the saved map's
  earlier live-URL provenance gap, not the cohort-compatibility gate. See
  `2026-09-23-reference-ambiguity.md`,
  `2026-09-24-frozen-reference-replay.md`, and
  `2026-09-24-scientific-review-reference-ambiguity.md`.

## Verification checkpoint

- Baseline before edits: 289 passed, 29 skipped.
- Current suite from the repository root: 357 passed, 29 skipped in 174.64s
  using `../.venv/bin/python -m pytest -q`.
- `analysis/check_manuscript.py`: passed.
- Released checkpoint archive: 52,913,192 bytes; SHA-256 matches the release
  manifest.
- Real-read depth oracle: job `1597949` checked 63 HG002 windows at bin sizes
  1–64; corrected maximum absolute error 0 and zero mismatched columns. Raw
  record: `results/diagnostics/depth_oracle_hg002_20260923.json`. Failed launch
  `1597948` is retained in the record and produced no scientific output.
- A first-party feasibility check found no GIAB v5.x SV truth/BED pair for
  HG005 or HG007 despite public large WGS BAMs and v4.2.1 **small-variant**
  benchmarks. These related donors are no-go as independent v5.x SV truth for
  the proposed cheap recall pilot; see `2026-09-24-giab-multidonor-feasibility.md`.

## Immediate next gates

1. Compare several important SV research directions and their closest prior
   art; choose a high-information, cheap falsification diagnostic before any
   large training campaign. Obtain independent Sol/high review of that choice.
2. Finish reference provenance/ambiguity and donor-callability gates before
   using HGSVC3/IGSR for candidate labels. The ambiguity BED is not a
   confident-negative mask.
3. Diagnose the two scheduler-startup failures before any revised Manta
   fixture. Do not relaunch the same job unchanged or assume the eventual
   research question is SSL candidate filtering.
4. Once a direction is chosen, freeze its baselines, split/test protection,
   label and compute budgets, metrics, uncertainty, and reproducible artifacts
   before confirmatory experiments.

Scientific improvement and publication readiness remain unproven.
