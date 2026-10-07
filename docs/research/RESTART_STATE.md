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

- October 7 newest: the exact-approved real metadata gate **failed** on signed
  SVLEN versus canonical allele length. Exit 2; CPU 0.66s, wall 1.27s, RSS
  99,201,024 bytes. No success inventory or failing identity/count was emitted;
  final source rehash was not reached. No validated denominator, caller outcome
  or biological null. The Sol6.1/high reviewer confirms closure of the fixed
  released-callset screen under its further-failure stop rule; main accepts.
  No REF/caller/sort/score/repair/drop/rerun follows. Full retained charge:
  8,588,703,005 bytes. Raw failure and exact pins are in the
  [validation/stop review](2026-10-07-validation-gates.md). Pinned synthetic
  controls pass 38 after a preserved Python memfd-binding failure; failed
  sources/small reports are backed up outside Git. Luna/max caller code is
  synthetic only, not authorized for real data. No cluster jobs at postcheck;
  scratch expires October 22 23:02:50 cluster-local. Optional record-level
  closeout diagnosis is unnecessary for STOP, unapproved and uncharged.
  Broader goal active: compare new questions and credible independent labels,
  not more wrappers to rescue the stopped screen. DeepSV excluded; no selected
  learned method or expensive campaign. Full suite 737 passed, 35 skipped;
  focused 70 passed, four skipped; manuscript consistency passed. The new
  [mosaic-specific identifiability question](2026-10-07-mosaic-identifiability-triage.md)
  is a prior-art/label-feasibility candidate, not a selected method.
  [Competing-opportunity handoff](2026-10-07-competing-opportunities.md) complete;
  main checked primary excerpts, documented correction/early-version limits
  and no inference of absent methods from truncated text. Sol6.1/max-requested
  finite next-direction decision pending; no new acquisition or campaign.
- October 7 historical preparation checkpoint (superseded above): the final separately approved preparation exception
  completed with whole gzip EOF/CRC and source hash/snapshot verification.
  All 5,497,286 source rows reconcile with map entries and classifications.
  Provisionally eligible: 1,430 current-minus-Tier1 plus 10,060 intersection
  records. This is not yet a validated scoring denominator; REF/native metadata
  validation is required. Sol6.1/high review accepts preparation only.
  CPU 168.21s, wall 169.61s, peak RSS 45,101,056 bytes. Complete outputs/logs
  copied off scratch outside Git, originals and failed v2 partials preserved;
  no independent large-output rehash claimed. Full charge with raw-copy
  reservation: 8,519,496,989 bytes. Suite 667 passed, 31 skipped; manuscript
  consistency passed. [Full review and inventory](2026-10-07-finite-preparation-and-control-review.md).
  [Fresh primary-source novelty check](2026-10-07-novelty-recheck.md) challenges
  generic stability/equivalence/ensemble/phasing proposals. No new method,
  caller score or publication finding. Luna/max worker stopped at usage limit,
  no saved caller-preparation code. Sol6.1/max finite direction review pending.
  No real REF/caller/sorting/scoring/refinement or training approval.
- October 7 earlier checkpoint (closed v2 attempt): [expanded controls and finite preparation](2026-10-07-finite-preparation-and-control-review.md)
  passed the pinned synthetic multiplicity/FN/full-row/reader-pairing tests.
  Actual reference controls reject the unsafe `norm -N -c e -f` recipe; the
  verified alternative's normalization output must be discarded. INFO/native
  contradictions are controlled. Both BEDs now require exact truth-header
  names/lengths/bounds before body classification; read-ahead is reserved.
  One separately approved truth-preparation pass failed at its 64-MiB full
  record-map limit after 376,029 source rows. No complete denominator or score.
  Preserve partials/logs and full 6,303,083,290-byte charge. Attempt v2 closed;
  no automatic retry/cap raise. High-impact recommendation allows only one
  proposed metadata-storage exception, subject to explicit independent review
  and fresh pins; no new pass approved or run. The closed artifacts are copied
  off scratch outside Git, with a separate 128-MiB archival reservation giving
  current charge 6,437,301,018 bytes. Full software suite 666 passed,
  31 skipped; manuscript consistency passes. Goal active and unachieved.
- October 7 updated-goal checkpoint: main read the revised objective in full
  and relayed it to the independent reviewer. The separately approved
  [truth header gate](2026-10-07-truth-header-gate.md) passed: sample HG002 and
  compatible declared autosomes; no body record parsed. Aggregate retained
  charge is 5,220,887,319 bytes. The [pinned synthetic cluster controls](2026-10-07-updated-goal-and-synthetic-controls.md)
  passed identity, dot-mode GT, boundary preservation and shared-denominator
  checks. Initial software failure remains preserved. Truth sentinel handling
  is synthetic-tested, not run on real data. Focused 76 passed, one local
  pinned-stack skip; the cluster integration passed separately. Full local
  suite: 657 passed, 30 skipped; manuscript consistency passed. Freeze finite
  truth/reference/caller preparation and all-read reservations for independent
  review next. No real truth preparation, BED denominator, scoring or campaign
  is approved by this checkpoint. Scientific goal remains unachieved.
- October 7 historical transport checkpoint (superseded above): the [distinct standard-tool attempt](2026-10-07-standard-transport-decision.md)
  succeeded. All six preselected callsets are complete and SHA-verified; new
  SVIM/SVPG raw member CRCs passed. Standard local pysam 0.24.1/samtools 1.24
  parsing preserved boundary positions and source counts without repair or
  filtering. SVIM contains 41 POS=0 rows, but the exact prior rejected value
  remains unrecorded. No compatibility claim is extended to the cluster's
  older library. Keep all failed-stage logs/partials and full source
  4,124,617,258-byte / aggregate 5,219,838,743-byte charges. CPU 29.15 seconds,
  wall 26.18 seconds, child RSS 197,115,904 bytes; no guard tripped.
  Full 642 passed, 29 skipped. Custom staging remains closed. Proceed to
  known preparation controls and reviewed fixed diagnostic by next working
  day; no truth/sort/scoring/refinement/training has run. No publication
  contribution is established.
- The [independent preparation review](2026-10-07-preparation-review.md) is
  complete. Its proposed capped truth-header gate subsequently passed under
  separate exact code/protocol/reservation review, as linked above. Then fix boundary classification, caller
  identity/standard preparation, caller-only native filters with identical
  truth IDs, exact cluster environment and all-read reservations. Matching,
  POA/refinement and training remain closed. No user action is required here;
  this is active implementation/review work, not a scientific impasse.
- October 7 historical streaming checkpoint (superseded above): [stage-03 and final stage-04](2026-10-07-streamed-callset-stage.md)
  failed. Four complete caller files are preserved: cuteSV, DeBreak, Sawfish,
  Sniffles. SVIM failed a position check; the actual value is unknown. SVPG
  was unopened. The custom-stager route is closed; no fifth attempt, cap
  raise, parser redesign or reduced union. Official VCF permits telomeric
  sentinels rejected by our validator; do not label the released file invalid.
  Keep full conservative charges of 4,094,310,110 source bytes and
  4,153,131,060 aggregate bytes, and all logs/partials outside Git.
  A separate byte-preserving two-member/HTSlib alternative awaits a direction
  decision and independent review. No truth preparation, sort, normalization,
  screen or refinement has run or is approved by that proposal. The truth
  preparation driver and [control audit](2026-10-07-released-screen-controls.md)
  are synthetic/software work only. Full validation: 617 passed, 29 skipped;
  manuscript consistency passed. No publication contribution is established.
- October 7: main read the current full goal again. The
  [independent staging review](2026-10-07-stage-review.md) records two
  separately reviewed source-only attempts. Stage-01 failed on header contig
  ordering; stage-02 preserved source order, completed cuteSV with CRC checked,
  then failed on a DeBreak line above 32 MiB. All six callers remain required;
  incomplete source staging is not a biological result. Keep original
  protocols, full conservative reservations, partials and logs. No automatic
  third pass is approved. Truth units and bootstrap helpers were implemented
  and tested only on synthetic examples; no truth, screening, matching or
  refinement execution is approved. Exact input/run identity remains
  unresolved, so the weaker released-callset development estimand governs.
  Preserve the 2,080,329,990-byte source charge and obtain a concrete bounded
  alternative before another source pass. No expensive campaign is selected.
- October 4 updated-goal follow-up: the full current objective was read and
  relayed to the active internal workers. The [close-prior-art challenge](2026-10-04-updated-goal-and-prior-art.md)
  checks published COSIGT, SVPG and minisv methods; generic missing-panel
  confidence filtering, graph augmentation and personal-normal assembly
  filtering are not sufficient novelty. Anscombe's independent review recommends
  stopping open-panel confidence as the active publication lead under this
  budget; main accepts the limited stop while the wider goal continues.
  Helmholtz completed the source-only structural-label check and was closed:
  full-span PAFs with MAPQ 255 do not provide confidence-qualified SV truth.
  Aristotle completed the high-impact recommendation and was closed. It selects
  a [modern caller-output completeness falsifier](2026-10-04-modern-callset-falsifier.md),
  conditional on usable inputs and a frozen reviewed protocol. Strict HTTP
  partial reads failed closed; independent review approved one complete SVPG
  archive transfer. Whole size/MD5/SHA-256 passed for 2,879,666,672 bytes, with
  203 entries and six frozen full-HiFi headers. Shared contig declarations do
  not prove exact raw/reference or graph identity. Anscombe accepts the weaker
  released-callset development estimand, not a controlled same-input ceiling.
  Full outcome protocol remains pending; no biological rows or outcomes have
  been parsed. Supporting synthetic source-contract tests pass 15; full suite
  passes 483 with 29 skipped. NIST v5.0q also derives from Q100 assembly V1.1:
  benchmark-generation revision must be distinguished from assembly version.
  Existing cluster Truvari is 5.4.0, not the paper's 5.3; no scoring has run.
  No new method or campaign is selected. Fresh cluster queue is empty; expiry is
  October 22 at 23:02:50 cluster-local, one extension available.
- October 4: [Locityper schema gate](2026-10-04-locityper-schema-gate.md)
  completed on the existing research branch. The verified 14.7-MB archive has
  19 members. Two full-panel/LOO Illumina headers declare all five native
  channels together. The publisher source explained the initial header-reader
  failure; an append-only, independently reviewed amendment allowed exactly
  one command comment, with no content retained. All 36 safety tests pass;
  the final full suite passed 468 tests with 29 skipped.
  Raw metadata, hashes, protocols and an execution ledger are under
  `results/data_audits/locityper_2025/2026-10-04/`. No outcome rows were parsed
  or scored. Sequence-distance summaries do not establish structural
  panel-absence labels, populated/unique joins or independent family holdouts.
  Stop outcome progression on this archive alone; no larger acquisition,
  detector or campaign is selected. Continue broader opportunity triage rather
  than lowering the truth standard. Fresh cluster queue is empty; scratch
  expiry remains October 22, one extension available. Peak RSS was measured,
  not hard-capped: macOS rejected `RLIMIT_AS` before startup. The successful
  scans stayed below 18 MB RSS and the stated byte/CPU budgets.
  Source checkpoint `4cd90b9e36a7ee74b7e010513ea191bc0204baec` was pushed;
  the remote branch SHA matches. PR #2 remains open and requires review; no
  main merge or protection bypass was attempted. A separate internal
  Luna/max-requested literature sidecar is checking the closest recent
  open-panel/adaptive-candidate work. Do not treat that pending search as a
  selected method or a validated novelty claim.
- October 1 updated-goal follow-up: [open-panel preflight](2026-10-01-open-panel-preflight.md)
  records the competing directions and separately requested Sol6.1/max
  decision / Sol6.1/high reviewer. Only one 14,709,179-byte Locityper benchmark
  TAR was approved for bounded inventory/schema inspection. It is outside Git
  and matches the published size/MD5. Native multi-channel controls and
  independent structural panel-absence labels are mandatory before any new
  outcome protocol. Source v0.17.3 is pinned separately from the paper's
  v0.18.0. No new detector or biological scoring is selected. The synthetic
  phase-endpoint bug is not the current biological lead. Use connected tools
  by task and alternatives when one fails, including Life Sciences Literature;
  Firecrawl is a plugin, not an assumed CLI.
- October 1: the [confidence-contract follow-up](2026-10-01-confidence-contracts.md)
  replaces assumptions about pooled GQ/PL with caller-specific source evidence.
  A pinned SVUPP fork accepts exact zero phase probabilities but treats them
  as missing; a synthetic label swap changes GT/GQ. Fourteen tests and hashed
  source/report identities reproduce this input-contract counterexample,
  not biological performance. Real endpoint frequency and execution revision
  remain open. QUILT2 2.0.3 source-formula arithmetic admits an exact endpoint
  without underflow; independent review accepted this conditional construction.
  The two load-bearing files match tag 2.0.4, named by the current wrapper;
  historical run/container identity is still unverified. Full suite: 432 passed,
  29 skipped; latest 14-test diagnostic and 30-test related target pass.
  Source checkpoint `8fe78755ea3b6bb8d4dbc911daff9090864c9b84` is pushed and
  [PR #2](https://github.com/aayushkrm/AlignSSL-SV/pull/2) is open, with one
  approval required. Continue from `research/genotype-confidence-contracts-20261001`;
  do not revert to main and silently lose the unmerged diagnostic. Fresh
  `squeue` was empty; restart scratch expires October 22 at 23:02:50
  cluster-local, one extension available.
  No production caller patch, genotype scoring, new cohort or
  training campaign is selected. Work proceeds on a research branch/PR after
  GitHub reported a PR-only rule bypass on the previous main push.
- The September 30 UTC / October 1 local
  [fresh reassessment](2026-09-30-fresh-assessment.md) supersedes the earlier
  candidate-recall priority, without deleting its evidence. Independent
  repository/history audit and current primary literature do not justify
  resuming SSL or a generic uncertainty/matcher thesis. SVUPP already tests
  quality-ranked genotyping across depths/platforms. The
  [independent high-impact decision/review](2026-09-30-independent-direction-review.md)
  selects **availability checking for conditional known-catalog genotype
  confidence transfer**, not a method, novelty claim or training campaign.
- A single Guo development callset ZIP (434,544,359 bytes) and two SVUPP source/
  assessment ZIPs (118,468 and 47,443,427 bytes) were stored outside Git and
  matched their published MD5s; all passed ZIP integrity tests. The Guo archive
  has 103 members and 14 audited pre-final caller headers. The newer SVUPP
  assessment archive has 26 members and five audited headers, including four
  genotyper outputs on one seven-person pedigree. No GT records, performance
  tables or plots were scored. Source scripts were read, never executed.
  Sample orders differ across SVUPP VCFs; exact sample/allele joins and GT/GQ/PL
  field lineage remain required. Missing records/GTs are not `0/0`.
- Strict Range checks failed closed on omitted HTTP validators; complete
  published-MD5 verification supplied the alternative. Life Sciences Literature
  supplied SVUPP's current PMC full text, while Scite had reached its monthly
  limit. Requested internal-worker roles follow Sol6.1/high, Luna/max and
  Sol6.1/max decisions; actual execution metadata remains unattested. An
  existing automation view rendered a card but returned no machine-readable
  configuration; no scheduler rewrite or duplicate was created.

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
  falsification test, not an approved method or positive result. The
  [conditional direction triage](2026-09-27-direction-triage.md) favors a
  no-training recall audit with truth/matcher sensitivity, but not a campaign
  until caller and reference compatibility are verified. The
  [nine-file Parliament2 header audit](2026-09-28-parliament2-header-gate.md)
  verifies the published bytes but does not establish exact reference,
  sample, or emitted-candidate identity. An independent review left the
  candidate-generation experiment unfrozen. A
  [first-party 2026 package check](2026-09-28-zenodo-sv-package-gate.md) found
  only a concatenated gzip stream behind the 3.33-GB `sv.gz` file and no
  published per-caller member index; the associated paper describes processed
  MetaSV/DRAGEN/Dysgu callsets, not raw component candidates.

## Cluster recovery state

- Read-only `squeue -u igorno` on 2026-09-30 showed no queued or running jobs.
  `ws_list` confirmed the restart scratch directory expires 2026-10-22
  23:02:50 cluster-local time, with one extension available. No cluster job or
  bulk transfer was launched for the Parliament2 header gate.
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
  BED. A [reproducible member-header survey](2026-09-24-pav-tar-header-replay.md)
  of both named `20240307_PAV_VCF` working TARs found no BED or `callable`
  member. This says nothing about other archives or rerunning PAV. PAV's smoothed
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
  terminated in four seconds with signal 53; the execution point and sender
  are unresolved.
  No Manta-named output directory was found in the scratch workspace. The
  `sacct` evidence is in `results/cluster_jobs/2026-09-24-manta-fixture-sacct.txt`;
  a [read-only recheck](2026-09-24-manta-signal53-diagnosis.md) documents a
  related GIAB job with the same signal and corrects the earlier startup claim.
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
- Current suite from the repository root: 418 passed, 29 skipped in 127.83s
  using `../.venv/bin/python -m pytest -q`.
- `analysis/check_manuscript.py`: passed.
- The September 30 UTC availability checkpoint's archive/header and synthetic
  probe checksum sidecars pass. `confidence_fields_2026-09-30.json` combines
  19 source-header semantics audits with zero biological records parsed.
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

1. Read the current objective and retain Aristotle's completed direction
   recommendation with the October 4 independent review. Open-panel confidence
   is no longer the active publication lead under this budget. Do not restart
   the completed literature or Locityper source-feasibility workers, build a
   detector from the QV archive, or acquire its larger database to preserve the
   old direction. This is a limited research stop, not a pause of the goal.
2. Source staging is complete for all six callers; the custom stager stays
   closed. Full eligibility preparation is complete and independently reviewed,
   but not REF/native validated. Resolve the high-impact value review after the
   fresh prior-art challenge. If retained, close essential reference/metadata
   and standard caller-preparation gates, including full-row/identity checks,
   fixed sample-column mappings and finite all-read reservations. Obtain exact
   Sol6.1/high execution review before any real REF/caller/sort/score command.
   Finish the fixed weaker development screen by October 8 or stop this dataset
   route; no open-ended parser/I/O supervisor, further cap change, reduced
   caller panel or deadline extension. Keep the two arms' truth IDs identical.
   Any later recovery claim needs original full variant context, honest
   unresolved labels, a distinct mechanism and unrelated-donor confirmation.
   No large training or publication method is selected.
3. If the inputs or distinct contribution fail, reject the direction and move
   to a stronger question; do not substitute another generic header audit for
   scientific progress. Keep unrelated-donor/locus-family confirmation untouched.
   Pedigree predictions and SVLearn training rows remain development evidence,
   not independent confidence-transfer tests.
4. Prior candidate-stage/callability gates apply **if** candidate recovery is
   selected. Final released calls cannot identify an internal candidate ceiling.
   Diagnose Manta's unresolved signal-53 failures before any justified rerun;
   do not submit a third identical fixture. Scratch expires October 22; preserve
   useful outputs before any expiry or project-only job cancellation.

Scientific improvement and publication readiness remain unproven.
