# Released call sets: independent staging review and unresolved science gates

Date: October 7, 2026. This note records a source-staging gate, not a positive
scientific result or publication direction. The full goal was read again.
The prior goal pass made progress: checkpoint `e357a5f9a45023de521ef55dee1a60b058715b89`
was pushed and its remote SHA verified. It did not achieve the research goal.

## Independent review and amendments

Anscombe, Sol6.1/high requested, accepted only the weaker development estimand:
coverage of eligible current-v5.0q HG002 truth by six fixed released full-HiFi
call sets. Exact common raw inputs and historical run/reference/graph identity
remain unresolved. No controlled same-input ceiling or independent replication.

Its subsequent outcome-protocol review required:

- Full-context original truth/caller inputs for refinement; an eligible-only
  VCF cannot restore removed small variants via `--use-original-vcfs`.
- Collision-safe source-hash plus ordinal truth identities; duplicate record
  multiplicity preserved for screening, distinct from reconstruction handling.
- Explicit purity trimming, diploid GT rules and phase/overlap/REF/boundary guards.
- Correct endpoint naming: `-p 0` inherited by refinement gives geometry
  compatibility after POA harmonization, not exact sequence equivalence.
- Process-tree resource control, installed-source hashes, sample mappings and
  fixed joint bootstrap/zero-denominator handling.

These findings changed the draft in
[`2026-10-04-released-callset-outcome-protocol.md`](2026-10-04-released-callset-outcome-protocol.md).
The screening/refinement stages remain closed until executable safeguards and
exact mappings are frozen. A regional summary cannot stand in for target-record
assignment. Five clean unmatched clusters would permit a separately reviewed
read/truth adjudication only, not a generator or training campaign.

Anscombe separately accepted **stage-only body parsing**, conditional on all
six source members/pins, failed-read accounting, 32-MiB lines, bounded metadata,
two-GiB source decoding, six-GiB aggregate traffic, 30-minute local CPU limit
and external RSS monitoring with headroom below four GiB. Memory monitoring on
macOS is not a hard RAM guarantee. No truth parsing, filtering, matching or
scientific screen was approved by that decision.

After the runtime reset, the previous agent handles returned `not_found`.
Dirac was started as a fresh independent Sol6.1/high-requested reviewer; Kepler
was started as a Luna/max-requested synthetic truth-unit worker. No new sidebar
chat was created. Actual execution configuration is not independently attested.
Dirac independently approved one stage-only run after checking the corrected
protocol, guard and reservation. Protocol SHA-256:
`d44bdeea2142bb6dae2e61f7bc6b29947beb9627199bdd28e0b1d5a70e83c4ae`;
reservation SHA-256:
`93c8200e8f201fb2fe66f8167670b1f04ed99d838abfa21db3589003fd08a838`.
The approval requires a fresh output-filesystem check, full reservation retained
on failure, preserved partials/logs and no automatic retry. Truth parsing,
scientific joining, matching, screening and refinement remain closed.

## Executable staging state

`analysis/stage_svpg_callsets.py` verifies exact whole archive identity and all
selected member CRCs, strips only INFO/RNAMES values, and preserves original
line endings and all other fields. It refuses overwrite and undeclared records;
the default rejects unsorted records, while the reviewed stage-02 policy keeps
and reports them. Failed outputs and charged-byte evidence remain outside Git;
no automatic cleanup/retry. Thirty synthetic staging tests pass. No released body
was opened by these tests.

`scripts/run_svpg_stage_bounded.py` uses an external single-process RSS guard,
stopping at three GiB, plus a 1,800-second child CPU limit and wall limit.
It inspects child creation and stops only its newly owned process group. Logs
and partial outputs remain. Five guard tests pass. Free-space preflight reserves
ten GiB plus the 1,037,019,267-byte selected source output; the run also checks
free-space headroom. At the fresh check, about twelve GiB is free, down from
eighteen on October 4; no unrelated user files were removed.

The frozen stage JSON and a pre-read traffic reservation are under
`results/data_audits/svpg_2026/2026-10-07/`. Prior header reads are conservatively
charged six MiB, not just their 33,048 returned bytes. This accounts for decoder
prefetch without pretending it was measured. Reserve the entire selected
source decoded size even on a failed attempt. Scientific truth/matching traffic
is not reserved or approved yet.

## Source-provenance sidecar and its limits

Sagan reported a partial first-party trail after 16 Exa queries / 87 requested
slots, including four stalled queries / 20 slots. It checked two Methods
subsections and Data/Code Availability plus GIAB/HPRC records, not 87 papers.
Firecrawl also stalled; Exa supplied the alternative. No genomic acquisition
or outcome scoring was performed by this sidecar.

The [2018 CCS 15-kb README](https://ftp-trace.ncbi.nlm.nih.gov/giab/ftp/data/AshkenazimTrio/HG002_NA24385_son/PacBio_CCS_15kb/README_PacBio_CCS_15kb_HG002.md)
describes roughly 28-fold Q20 data. The
[2023 Revio directory](https://ftp-trace.ncbi.nlm.nih.gov/giab/ftp/data/AshkenazimTrio/HG002_NA24385_son/PacBio_HiFi-Revio_20231031/)
lists 48-fold alignment files. Main checked both first-party records. The
reference-directory label `HG002_PacBio_CCS_15kb` in caller headers does **not**
prove which raw reads were used: an old reference directory could be reused
with new reads. Do not convert this family-level inference into a proven
2018-versus-2023 mismatch, exact depth or archive error.

The sidecar reports published HPRC graph exclusions of HG002 and its parents;
the VCFs do not pin the actual graph bytes used. Treat published graph membership
and exact run membership as different evidence. No graph was acquired.
Header dates and the public SVPG tag date likewise do not prove binary identity.

## Operational state

A fresh account queue is empty. Restart scratch remains available until
October 22 at 23:02:50 cluster-local, with fifteen days reported and one
extension available. No cluster job was started or cancelled by this check.
Existing Truvari 5.4.0 uses pyabpoa 1.5.6; the paper's 5.3 is a different
execution version. Indexed hs37d5 access was verified separately. Preserve
raw data outside Git and source/summary provenance inside Git.

## Stage-01 failure and separately reviewed stage-02 amendment

Stage-01 stopped at the first cuteSV contig-order disagreement with the header
dictionary. It completed no caller. It delivered 9,593,544 decoded bytes before
failure; the full 1,037,019,267-byte source reservation remains charged. This
is an engineering failure, not a biological null result. The original protocol,
failure report, resource report, partial VCF and logs remain preserved.

Dirac approved exactly one additional **stage-only** pass with the reviewed
`preserve_and_report` order policy. It retains all records in their original
order and reports order violations; it does not sort, filter or deduplicate.
Protocol SHA-256:
`d2c496f0366ea29bc041e680ff1c86134c6f5a8990a8c42c831e61a2447d32a0`.
Reservation SHA-256:
`71d22f5a94f2c4c276e7aa337404d3f2bbf57fb95b906e1c694ebe64e8d128ed`.
The cumulative reserved source traffic is 2,080,329,990 bytes, below two GiB.
The reviewed stager and supervisor hashes were checked again before execution;
the fresh filesystem check showed about twelve GiB free. Fresh sibling output
and log directories are required. Keep the full charge on failure. No automatic
retry or further archive pass is approved. Sorting, truth parsing, scientific
joining, matching, screening and refinement remain closed.

The user reported an updated goal. Main read the complete current goal file
again before continuing. The publication objective, permission to pivot, DeepSV
exclusion, fit-for-purpose connected research tools, independent review and
requested model roles govern this continuation. No model switch or scientific
success is inferred from this acknowledgement.

### Stage-02 execution outcome

The amended pass failed closed on DeBreak's first line above 33,554,432 bytes.
It completed cuteSV: 51,561 records, source member CRC checked, 23 contig-order
violations reported and no position-order violations. This file needs a
separately frozen sort view before indexed scientific use. No other caller
completed. The complete cuteSV source SHA-256 is
`a96fd63588c1457a1762d01219bb1220ffb782f31ff36e0072f05d1e13902b43`;
its RNAMES-removed derivative SHA-256 is
`9603595adebb54e656513c3ffba416e0d2173763030abef20f804e1c877209c1`.
These counts are inventory evidence, not truth coverage or accuracy.

Delivered decoded traffic was 64,141,374 bytes; conservative reservation remains
the full 1,037,019,267 bytes for this pass, for 2,080,329,990 bytes including the
prior charge. Combined CPU was 14.579766 seconds, wall time 14.306621 seconds,
sampled RSS peak 45,428,736 bytes and child rusage peak 90,456,064 bytes. No
supervisor resource guard tripped. Reports are under
`results/data_audits/svpg_2026/2026-10-07/stage_02_{failure,resources}.json`.
Original archive, completed/partial VCFs and logs remain outside Git. No third
read was started. Do not omit DeBreak, change scientific rules or interpret
this processing failure as a null research result.

Kepler implemented only `analysis/released_truth_units.py` and its tests.
Main reviewed the changes: source-hash/ordinal identities retain duplicate-row
multiplicity; maximal suffix/prefix trimming uses linear scans; immutable BED
indexes support repeated containment; strict autosome names avoid aliases;
the fixed paired-block bootstrap retains zero-denominator draws. All inputs
in these tests are synthetic. This code does not authorize reading truth or
claim statistical validity for a future biological result.

The targeted helper suite actually collected 27 parameterized cases, all
passing (the worker's initial “16 tests” was not the collected case count).
The full integrated suite passed **545 tests, 29 skipped** in 133.49 seconds.
Manuscript consistency and whitespace checks passed. Tests establish software
behavior only, not biological accuracy.

### Next engineering gate: recommendation, not execution approval

Dirac read only aggregate stage-02 metadata and recommends one bounded repair.
It explicitly did not authorize a new read. Reuse completed cuteSV only after
its derivative hash is verified and that read is charged. Keep its sort flag.
The five unfinished source members total 1,006,990,060 bytes. Retained prior
charges plus that reservation would be 3,087,320,050 bytes: the two-GiB source
reservation is now an engineering blocker. A separately frozen amendment
could use a three-GiB cumulative source ceiling while retaining six-GiB
aggregate traffic, two combined CPU hours and four-GiB memory. Additional
verification/preparation reads require separate reservations.

Oversized raw lines may pass only through a tested bounded streaming
INFO/RNAMES-removal route; retained records must remain within 32 MiB. The
failure does not prove RNAMES caused the oversized line. No whole raw line or
discarded value may be buffered. Preserve other fields, order, multiplicity,
line endings, source hashes and selected-member CRCs. Required synthetic
checks cover chunk-boundary delimiters, all RNAMES positions, similar keys,
duplicate INFO, oversized retained fields, truncation and CRC failure. If the
contract cannot be met, stop this acquisition route as infeasible. Do not
omit DeBreak or accept a five-caller union. Sorting, truth, screening and
refinement gates remain separate and closed.
