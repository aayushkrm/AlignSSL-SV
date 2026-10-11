# Synthetic native calling interface fixture — S0 only, unexecuted natively

2026-10-11. Requested Luna/max remains a request, not backend evidence.
Only the two new scripts, their unittest file and this note are owned here.
Main owns review, frozen upload, execution, allocation and HOME custody.
No real DNA/reference/RNA body, subset, asset, install, job or Git operation
was performed by this worker. CLI job1604301 is existing main evidence.

```text
whole synthetic reference + all synthetic CCS identities
  → pbmm2 CCS remap → source/strand/RG BAM audit
  → pbsv discover --hifi → pbsv call --hifi
  → unchanged CDS cohort → fixed truth/REF/accounting comparison
  → COMPLETE or preserved missing/extra/unresolved/failure packet
```

## Fixed input and finite comparison

Version `synthetic-calling-interface-v1` uses independent seeds11001/22002/
33003 for three complete30,000bp ACGT contigs. No annotation gaps or external
sequence. At zero-based boundary15000, deletion removes[15000,15120), insertion
adds150bp from seed44004. Reference-only contig has no alternate allele.
No search for seeds or tuning after native results. Exact sequences and hashes,
FASTA/FAI, every expected whole allele and truth rows are retained before calling.

Each variant has10 reference and10 alternate full-length reads, five per strand
per allele. Reference-only contig has20 full-length reference reads, ten per
strand. Sixty unique `toyfixture_v1/ZMW/ccs` identities have Q40 Phred+33 quality,
explicit orientation, sequence/quality SHA, sample `SYNTHETIC_CCS_V1`, RG
`toy_ccs_v1`; no input HP/PS. BAM audit checks every primary source identity,
forward input sequence/quality, mapping contig/orientation, header lengths,
RG/sample and absence of read phase; supplements do not create molecules.
The main native audit needs existing pysam; local unittest uses a fake interface.

Two broad CDS isoforms per contig cover[9000,21000) with versioned gene/transcript
IDs and protein_coding attributes. This annotation tests the cohort schema;
it is not a verified ORF, biological gene or coding-chain/P1 example.
The unchanged cohort merges isoforms within a gene: expected **two rows**, not
four isoform rows. Both contain both transcript IDs, unphased_GT/UNKNOWN,
OVERLAPS_CDS, NOT_ASSESSED and final_D=null. The reference-only control should
emit no variant. Reference GT records, other types, every FILTER and all source
ALT exclusions remain in the comparison/counters, not silently discarded.

Prospective comparison permits exact whole-alternate-sequence equivalence of
literal anchored DEL/INS, including equivalent anchor shifts. No numeric window,
size tolerance or fuzzy matching. Symbolic DEL requires exact consistent END/
SVLEN and reconstructable whole alternate sequence. Symbolic INS without sequence
is unresolved, not a success. Every REF substring must match this fixture FASTA.
Exactly one non-reference PASS unphased0/1 call per event is expected. Missing,
duplicate or extra calls, changed sequence/size, FILTER, genotype or phase make
the control incomplete. No test outcome can change truth or recover thresholds.
All raw records and comparison rows are retained. Malformed outputs retain raw
files and diagnostic logs even when comparison cannot parse them.

## Native contract from actual receipts

The five local help/version receipts in `results/hg002_caller_setup_20261011`
are pinned by exact hashes in the writer and copied into inputs/sources.
No web lookup is needed. pbmm2 version26.2.0, binary SHA
`f8a583d27a6232706c8ffe31dab3e52815455032517e9c1399940d4a3ea612bc`;
pbsv2.11.0, **observed** binary SHA
`01d83ec77ce40a5416b2a591f98090c51870b25d66650eccc7d7c493e1da5ae6`.
pbsv's release-API digest remainsNULL. Absolute HOME tools are under
`/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/hg002_dna_callers_s0_20261010_01/bin`.

Frozen remap: `align --preset CCS --sort --unmapped --bam-index BAI`, explicit
sample/RG/PACBIO/READTYPE=CCS, `-j 1 -J 1 -m 256M`. Three CPUs allow one align
thread, one sort thread and I/O; this is not a measured scaling claim.
Discover uses `--hifi` (native97% gap-compressed identity), no BED/region or
threshold override. Call uses `--hifi -j 1` (native `-S 0 -P 10`), all native types,
all FILTERs, native minimum20bp and other defaults unchanged. The downstream
unchanged cohort applies DEL/INS≥50bp; neither caller is restricted to CDS.
No tandem-repeat BED is needed for this unannotated random toy control; this
does not resolve the real reference's repeat annotation or sensitivity policy.

## Boundaries and main handoff

Runner requests3CPU/4GiB/5min/noGPU, sequential commands, ≤900 allocated S0
seconds. It checks the actual Slurm record, binary hashes/versions, frozen
bundle manifest and unchanged cohort hash
`197a54c9dbf6dd3f7f9264a3eb090d0646f08d05fdb7dfe99ae2c337f0064f4e`.
No PATH/shared-environment change, retry, dependency install or submission.
Shared270s timeout budget bounds new steps; Slurm bounds the entire job.
Each process group has a timeout and a sampled50ms aggregate byte guard;
per-file Linux limit8MiB. These checks are not a filesystem quota or proof of
zero transient overshoot. Reaching a guard preserves outputs and stops.
The unit-test monitor counts temporary symlink-refusal fixtures under test-tmp
without following them; only links targeting that same temporary tree qualify.
Completed steps and final packets still reject retained symlinks.

Fresh scratch leaf must be
`.../experiments/hg002_calling_interface_s0_20261011_NN` under the fixed project
scratch parent. Existing output/symlinks are refused; no cleanup/reuse of failed
native packets. Each leaf and HOME copy must remain strictly below32MiB.
Reserve64MiB **inside the existing8GiB other-S0-material reservation**, not
another128MiB outside32GiB. Main supplies all other material bytes within8GiB,
remaining allocated CPU seconds≥900 and checks concurrent RAM/disk/custody.
The existing external34,204,497,850B reservation is not increased by this task.
Software/genomic body transfer is0. Actual CPU/RSS/disk remain main observations.

Main freezes the four owned files, unchanged cohort and five small receipts into
a bundle preserving repository-relative paths. Main writes `source-sha256sums.txt`
for those ten files, records its SHA separately, verifies upload, and uses fresh
outer Slurm logs under an existing writable parent. Runner arguments are:

```sh
bash /ABS/FROZEN/scripts/run_hg002_calling_interface_fixture.sh \
  /ABS/FROZEN_BUNDLE /ABS/FRESH_SCRATCH_LEAF \
  REMAINING_S0_ALLOCATED_SECONDS ALL_OTHER_8G_MATERIAL_BYTES MANIFEST_SHA256
```

The runner captures source/runtime hashes, command/log/exit/timing records,
original synthetic inputs, all native BAM/index/signatures/VCF/cohort outputs,
independent comparison and a final per-artifact byte/SHA manifest. It leaves
failed/partial files. Main preserves the whole packet plus outer logs through
writable login I/O to non-expiring HOME and independently verifies hashes.
SIGKILL/node failure can bypass finalization; no status line substitutes for
complete custody or comparison. Hash lists do not include their own digest.
Hash-publication/late guard failure records finalization-failure.json where
possible and fails the job; an earlier status alone must not be accepted.

## Local verification and unresolved native observations

Local existing venv: **28 standard-library unittests pass in3.499s**. The guarded
process wrapper independently runs the same28 successfully in3.520s; synthetic
temporary trees are cleaned by the test harness, not native failure cleanup.
Combined new fixture plus unchanged cohort regression: **59 tests and10 subtests
pass in3.96s**. Bash syntax passes. Input+source preparation measured below4MiB;
native packet size remains unmeasured. Controls cover complete FASTA/FAI, fixed
event/FASTQ SHA pins, all60 IDs/qualities/orientations/support balances, unrelated
unique31mers, exact alternative anchors and symbolic DEL, retained failures/
extras/duplicates/filters/GT/phase, REF/size/sequence disagreements, all isoforms,
exclusive publication, byte/symlink guards, mock BAM census, launch failure,
timeouts, logs/exits and failure artifact hashes. No native author binary ran.

```sh
/Users/akm/aayushkrm-AlignSSL/.venv/bin/python -B -m unittest discover \
  -s tests -p test_hg002_calling_interface_fixture.py -v
```

Only synthetic inputs and mock BAM/process controls were used. Native output
representation, BAM/index/signature validity, actual sample/RG propagation,
filters, balanced GT and successful cohort comparison remain unobserved here.
Synthetic success would qualify only this ordinary interface, not real-data
sensitivity, source/reference compatibility, phase/copy readiness, P1,
causation, whole-genome biology or S2 release.

## Main pre-execution review and frozen upload

Main read all four files in full. Independent local reruns pass28 fixture
tests and18 reference-parser tests. Pytest, which also collects the legacy
cohort's function-style tests, passes77 tests and34 subtests in4.48s, zero
skips. A unittest-only invocation of that legacy cohort collects0 tests and
is **not** cohort regression evidence.

Code is committed in `da9d0eb` and pushed to the research branch. Frozen HOME
bundle `bundles/hg002_calling_interface_s0_20261011_01` has ten complete
source/receipt entries, all verified after upload. Its source manifest SHA is
`7d99a04510bcc635c954cf845f58e0e4952078412ddb57438c617c7d919fb73e`;
whole bundle apparent bytes81,171. The frozen copy of this note predates this
append. No native toy job has run at this checkpoint.

Conservative remaining S0 account is9157 allocated seconds; a900-second
booking would leave8257 before actual runtime reconciliation. For the runner's
other-material guard, main will reserve7GiB for the already named other S0
material and headroom, rather than claim an exhaustive measured total. This
is **inside**, not additional to, the existing8GiB reserve. The64MiB new
scratch+HOME toy pair also fits inside that reserve. Both expanded reference
copies and the separate caller128MiB pair remain charged. Physical scratch
space exceeds the required64MiB. No body transfer or useful genomic download
is needed. Independent reviewer acceptance remains pending at this checkpoint.

## Independent HOLD and finite comparator correction

The independent prelaunch review reproduces five false passes in the original
28-test comparator: empty or swapped cohort source records, incorrect cohort
spans or sample, and duplicate FORMAT `GT:GT` with `1/1:0/1`. Original source,
test and bundle01 hashes stay retained; no native run used that bundle.

Main adds explicit source-observation joins. Each cohort row now matches a
unique accepted native VCF observation, its native event identity and alternate,
its independently trimmed record geometry, and its complete nonempty source
record (native ID, line, POS, REF, FILTER, GT, phase, ALT index and raw INFO).
Native IDs need not equal truth IDs. Equivalent anchor shifts remain accepted.
Summary and row samples must match the synthetic sample. Duplicate FORMAT keys
and unequal FORMAT/value cardinality are rejected before genotype interpretation.
The unchanged cohort source and fixed input truth are not modified.

All32 local unittest cases pass in4.136s. New controls reproduce all five
reviewer failures, add seven other source/alternate/event-link mutations,
cardinality refusal, and acceptance of arbitrary native record IDs. The prior
symbolic DEL and suffix-anchor positives still pass. A fresh bundle02 and
independent correction recheck are required before any native launch.

Read scope: FULL governing objective; DNA-stage investment, caller preflight,
cohort implementation and complete cohort source; captured native helps/versions
and CLI custody note. No repeated metadata retrieval or broad research.
