# HG002 S1b: full-source read extraction

Development sidecar only. S1b is UNBOOKED and has not read the study BAM.
S1a must finish first. Its running partial is not an extraction input.
Use only the complete, verified original DNA BAM and its acquisition SHA256.
This tool does not align, call variants, qualify phase/copy, inspect RNA, or
change D. READY_FOR_DNA_INPUT_REVIEW means extraction checks passed; it is
not a release of S2–S4 or a scientific positive/negative.

## Interface and algorithm

Run scripts/extract_hg002_source_reads.py with --bam, --output,
--input-sha256, --remaining-s1-cpu-seconds, and --preexisting-s1-disk-bytes. Output must be a new leaf
under an existing writable parent. No existing output, input, or historical
result is replaced. The source stays read-only. Require pysam 0.24.1.
Main must supply the remaining S1 account from measured allocated cost after
S1a completes. The total account is 8 allocated CPU hours, including failed
attempts; S1a's booked maximum is 4 hours, not its actual cost. Unused time
can be reclaimed after completion, not presumed now. No job is booked here.

Pass 1 decodes the whole BAM through EOF, including unmapped, secondary,
supplementary, duplicate-flagged and QC-fail records. Each original QNAME
has one SQLite identity row. Full no-hard-clip records store only sequence
and quality SHA256 plus length and the first valid full-record ordinal.
Hard clips store forward offsets, fragment length, expected full length,
and sequence/quality hashes. Reverse FLAG swaps hard-clip ends; pysam restores
forward sequence and reverses qualities. Soft clips remain part of a full read.
Missing sequence/quality records retain every available constraint. No bases
are stitched. Full sequence or quality conflicts make that identity UNKNOWN.

Pass 2 is another full sequential decode. A canonical full record must match
all available fragment constraints before one forward FASTQ entry is written.
All valid original molecules are retained; there is no primary-only, phased,
mapped, expression, genomic-region, or alignment-FILTER subset.
FASTQ streams into level-1 gzip, with no uncompressed FASTQ on disk.
Missing HP/PS alone does not fail extraction. FLAG and RG/HP/PS counters are
reported; those tags are not validated phase assignments.

## State, custody, and limits

readiness.json, stats.jsonl, and identities.sqlite retain observed counts and
constraints on error, SIGINT/SIGTERM, or deadline. Deferred signal handlers
stop at safe boundaries, including after a returned FASTQ write. Missing
original names, unresolved identities, malformed query/CIGAR, empty input,
truncated BAM/EOF/decode errors, conflicts, or budget stops mean INCOMPLETE.
An incomplete gzip/read subset remains .partial; it is not a complete genome
readset. Observed-prefix counts do not estimate unseen identities.
Original bases are reported only for complete extraction; resolved bases,
restored hard-clip/missing identities, UNKNOWN counts and examples remain visible.
Archive differences use 5,359,077 IDs and 80,344,827,828 bases as comparisons,
not forced equality or an independent source census.

The complete input and completed gzip are each SHA256-read once, in bounded
1-MiB loops. Input inode/size/mtime/ctime are checked between passes and before
publication. Main must keep the input frozen throughout both passes.
SQLite has a 32-MiB page cache, file-backed temporary storage, a 2-GiB database
page cap, and a 5-GiB index-plus-journal budget. File sizes are observed at
checkpoints/finalization; the reported peak is sampled, not continuous.
Growth does not cause difficult identities to be removed. Cap failure stops.

Use one CPU and 16 GiB RAM prospectively. Wall time cannot exceed main's
explicit remaining S1 CPU seconds (one CPU); process CPU and RSS are reported.
The code never books a job or raises the S1 account. Main/reviewer must accept
the actual command, resource packet and independent controls before execution.

## Required launch disk ledger and scaling assumptions

S1's 160-GiB limit is summed peak storage, not this output directory's limit.
BAM+BAI total 48,748,908,838 B = 45.401 GiB per retained copy. Main must record
source, scratch/home custody copies, extracted gzip copies, SQLite/journal,
temp files and other S1 artifacts at launch, then track their joint peak.
Main's correction requires an explicit CLI preexisting-byte account covering
BAI, other retained raw/custody copies, and all other S1 artifacts, **excluding**
the one source BAM and this new output. Add these to the source size and all
own output files at startup, checkpoints and after publication; stop above
160GiB or below1GiB physical free space. Keep external accounted bytes frozen
during the stage. The code does not discover external copies. These are
sampled size checks, not continuous disk enforcement; journal/final metadata
and checkpoint growth require launch headroom. No160GiB fit claim.

With a full 5-GiB index allowance, one raw copy leaves at most 109.599 GiB for
gzip and other artifacts; two raw copies leave 64.198 GiB. With two raw and two
gzip custody copies, each gzip has at most 32.099 GiB before further overhead.
These are ceilings, not compression estimates or evidence that the stage fits.
The alternative ENA FASTQ's 33-GB size cannot certify this BAM's gzip size.
Keep one verified non-expiring home copy. Removing redundant scratch requires
custody verification and explicit main action; this tool never deletes it.
S0 references have a separate 32-GiB peak; global summed peak remains 512 GiB.

One input hash plus two BAM passes requires about 146.182 GB of raw BAM reads.
At archive-scale counts, sequence+qualities alone are about 160.690 GB streamed
through gzip, plus names/separators. Counts and duplicate-fragment work may differ.
SQLite work scales with all records and distinct fragment constraints, not only
5.36 million full IDs. Compression, hashing, decoding and SQLite all share one
CPU. For a hypothetical 4-hour remainder, raw reads alone require >10 MB/s and
gzip input alone >11 MB/s, before other work; those are lower bounds, not a
throughput or completion prediction. No whole-source timing/size is attested.
Do not reserve a second idle CPU or crop reads to fit a failed account.

## Synthetic verification and explicit gaps

Existing project venv, pysam 0.24.1 and pytest: worker35 controls pass, main
independently reproduces35 in0.57s. After main's finite disk/quality changes,
41 pass in0.69s; no real genome,
network, install, cluster connection, job, or Git operation was used.
Tests cover all full/fragment orientations, earlier/later full restoration,
quality reversal, duplicates, unmapped/QC/secondary records, missing payload,
conflicts, malformed CIGAR, corrupt/EOF/empty BAM, exclusive outputs, hashes,
index cap, deadline, and cancellation after record/write/publication.
Command: python -m pytest -q -p no:cacheprovider tests/test_extract_hg002_source_reads.py.
Main uses equivalent C-level byte translation for Phred33 and max-quality
validation, avoiding Python work per quality base. All0–93 scores in both
orientations and invalid94/255 controls pass; no source timing claim.
Whole-source performance, externally supplied custody-account validation, scheduler limits,
reference/phase/copy qualification and read-identity provenance beyond QNAME
are not implemented or certified here. SIGKILL or a full filesystem can prevent
a final manifest; preserve initial manifest, SQLite and flushed stats instead.
A fragment without a matching full record cannot be recovered by this code.
An error/cancel at the exclusive-publication boundary can leave a completed
filename with an INCOMPLETE manifest. Filenames alone never authorize use.
This is full BAM sequence extraction, **not** BAI parsing or alignment/index
qualification. The earlier independent reviewer stopped with a reported usage
limit; a replacement Sol6.1/high reviewer is requested. Concrete independent
code acceptance and actual launch packet remain pending. S1b stays UNBOOKED.

Replacement reviewer Gibbs reproduces two defects and HOLDs launch: reverse
records without QUAL become malformed despite recoverable full records;
final accounting can cross the deadline and still report READY. Main checks
raw payload presence before orientation calls and keeps deferred cancellation
active through final accounting, with a late status check. Nine regression
controls cover restoration/order/disagreement and final accounting expiry/
cancellation. Updated50 tests pass0.81s; independent recheck pending.
Linux01 control1604281 passed41 in3.55s but does not clear these defects.
That bundle stays preserved and has never processed the study BAM.

## Concrete corrected execution packet — UNBOOKED

Immutable corrected bundle:
`/beegfs/datasets/home/igorno/alignssl_restart_20260922/bundles/hg002_read_extract_20261010_02`.
Source SHA40679be522fbf2dd582a6826d72cfc02b9d77443f60095dcabb5a9d4efec681a;
test SHA81bebb128622925bb677cde26e12bfdd2f2b833f4e0622d994b06ce635159aee.
Use isolated intake-check CPython3.12.1 with pysam0.24.1, installed offline
from the preserved LiftOn wheelhouse; pip check passes. This is an added
isolated dependency, not a shared-environment or prior native run change.

One CPU/16GiB/5h direct srun, hydra-n1/amd_256M, no GPU/whole node. From
that bundle, `python -B -m scripts.extract_hg002_source_reads`:

```text
--bam /beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/hg002_dna_s1a_20261010_01/HG002_WGS.haplotagged.bam
--output /beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/hg002_read_extract_20261010_01
--input-sha256 b7edeb4bbc2589039c6148a912857f26924ca8fd5971cd3141337d0ce24bbde4
--remaining-s1-cpu-seconds 17940
--preexisting-s1-disk-bytes 48818418098
```

No existing output at preflight. Script deadline is one minute below the
18000s allocation. Current S1allocated8080s leaves20720s; a full5h leaves2720s.
Charge actual scheduler cost, not process-wall estimates. Routine mock/runtime
controls stay in S0. Both DNA raw directories have apparent48756094788B:
raw-other excluding the source BAM48784863666B. Add32MiB reserve for small
prior/control/final artifacts to declare48818418098B; this margin is not an
observed file total. Source plus external packet97,545,744,008B leaves
74,252,947,832B for extraction/index/remaining overhead below160GiB.
Future gzip custody copies must still fit this account; no extra free budget.
Keep these external bytes fixed and preserve both raw copies during S1b.
Outputs go only to scratch; back up new results with hashes afterward.

This packet does not release actual execution until the maintained reviewer
clears both reproduced HOLDs and the corrected frozen Linux controls pass.
No second library, crop, read subset, retry, calling, assembly, P1 or RNA.
Current combined local selection146tests+9subtests passes; see actual test
output for timing:1.85s, zero skips. These synthetic controls are not a study readset result.

Corrected frozen Linux02 job1604282 verifies both matching hashes and passes
all50 tests, zero skips,4.32s. This is mock-only qualification, not a real BAM
census or clearance of the independent HOLD. Initial01 remains preserved.

The maintained replacement reviewer now independently clears both defects
at these exact corrected hashes and accepts this packet conditional on50
matching Linux controls. Its50existing+41additional synthetic cases pass,
including reverse missing-payload restoration/disagreement and21late-accounting
expiry/cancellation injections. Frozen02 job1604282 satisfies the remaining
condition: both hashes match and50 controls pass. Both control jobs1604281/82
complete0:0,5s allocated each, measuredCPU0.678/0.625s, MaxRSS23216/25456K;
charge them to routine S0. This permits the exact S1b launch below, not S2–S4
or RNA. Historical HOLD and01 bundle stay preserved.
