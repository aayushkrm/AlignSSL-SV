# Prospective native metadata contract — no scoring permission

Date: October 8, 2026. Status: fixed implementation window expired,
**UNEXECUTED**. Code is preserved; no native pass or launch permission.
Main read the full current goal. Prior checkpoint `d8e6f7b` is pushed and the
worktree was clean before this protocol. The previous interrupted turn left
one implementation worker and the maintained reviewer active; neither was
replaced. No new genomic scan has run.

## Decision question

Can the existing native tools read every unchanged prepared truth row and
return the same type and absolute length as the literal-allele calculation?
This is the next necessary engineering observation after the completed
[metadata census](2026-10-08-metadata-census-result.md). It is not a paper,
a truth-certification test, or approval to reopen the old screen.

The census retained all 11,490 rows. All lexical type and absolute-length
comparisons agree; 4,530 global sign-only mismatches remain recorded. That
is not a type-by-sign table. Do not scan again just to strengthen that claim.
The original strict signed gate, its failure and its resource charge stay
unchanged. The actual annotation producer remains unknown.

## Uniform rule, frozen before caller outcomes

| Property | Required result |
|---|---|
| Population | Every one of the same 11,490 prepared IDs, in the same order; no repair, drop, decomposition, normalization or exclusion mask |
| Eligibility | Existing `classify_truth_record` rule, including literal pure INS/DEL, diploid non-reference GT and >=50-bp size; no genotype imputation |
| INFO type | Scalar SVTYPE equals the allele-derived kind |
| INFO size | Scalar integer SVLEN; its absolute value equals allele-derived size; accept either sign without changing the raw field |
| Native metadata | Truvari `var_size()` and `var_type()` equal canonical size and kind for every row |
| Mutation guard | Pysam/native serialized whole rows agree before calls; neither serialized row may change after native calls |
| Header/sample | Observed VCF 4.2, scalar Integer SVLEN and scalar String SVTYPE; both parsers have exactly HG002 |
| Integrity | Pinned source hash/size before parse, stable named/opened snapshots, complete bounded posthash, row count and ordered-ID digest |

Accepting either sign is an explicit **analysis compatibility convention**,
not a finding that positive deletion SVLEN complies with VCF 4.2. All raw
fields and historical flags remain. Missing values, multiple values, wrong
types/magnitudes, invalid eligibility, native disagreement, row mutation or
integrity failure prevent a complete pass. Do not patch one failing row.
This rule is fixed before any released-caller comparison; no scores exist.

## Exact input and implementation scope

Input only:
`/scratch/igorno-alignssl_restart_20260922/svpg_truth_prepare_20261007_02/prepared/eligible_truth.vcf`.
Size 11,853,747 bytes; SHA256
`c908217f7ec8eba1efe93f51605675a8a8b9676d9c9ca443d1348ad0a00f68d2`.
Ordered-ID SHA256:
`13db07d2c659f578144067d45eea85684816cce6482230e190a1b01b8d627e37`.
These pins come from the completed census; no new source pass is claimed.

New utility `analysis/check_released_truth_native.py` and focused synthetic
tests only. Reuse the census's strict bounded readers/snapshots and the old
checker's Linux sealed buffer. Pin all imported local helper bytes and the
new source. Do not reuse the old cap+1 readers. Both native parsers must see
the same kernel-sealed payload, not reopen the scientific source.

Installed stack required: Python 3.10.20, pysam 0.24.0, Truvari 5.4.0,
bundled bcftools 1.23.1 and HTSlib 1.23.1. No new package or tool installation.
The protocol flag is configuration, not independent reviewer approval.
The CLI must retain production input pins; synthetic overrides belong only
to test helpers. An exclusive report outside Git must contain no allele
strings, genotype values, read names or complete rows.

Prohibited inputs/actions: original truth or identity-map body, confidence
BED, FASTA/reference, caller VCFs, archives, new downloads, matching, caller
execution, training, SLURM campaign, source repair or score computation.
Existing historical source/control files remain unchanged.

## Finite execution and accounting

One allowance: <=60 active minutes for specification, implementation,
synthetic controls, independent review, exact execution and result review.
The allowance started with the first dispatch/cluster check around 13:48
cluster-local time. Interruption does not silently restart or refill it.
At 15:33 cluster-local time, the main continuation found a ~105-minute
wall-time gap. Wall time is not active work time, but the worker/reviewer
active-time balance is not established. Two waits on the same handles timed
out; neither returned a terminal status. Main asked those agents to finish
and preserve their existing work, not restart. Exact launch is on hold
until both implementation/review and the remaining active allowance are
established; do not interpret this note as an extension or real-run approval.

### Explicit operational amendment, before any new scientific read

At **08:39:01 UTC / 15:39:01 cluster-local**, both original handles returned
terminal responses. The worker reports no implementation edits, tests or
genomic reads; its active time remains unknown. Main closed that completed
worker, without a replacement. The reviewer accepts only the uniform rule.
Close the original interrupted effort allowance as **unverified, unexecuted**.
Do not claim that it met its 60-active-minute cap.

Main prospectively replaces that unverifiable timer with ONE fixed wall-time
attempt ending **09:09:01 UTC / 16:09:01 cluster-local**, 30 minutes later.
Main owns the critical-path implementation; use the known project virtualenv
for local synthetic tests, not the worker's default system Python. No further
worker dispatch, timer reset or real retry. Independent amendment and exact
implementation review are still required. If approval, controls, real command
and result review do not fit, preserve incomplete status instead of extending.
This is an explicit engineering-effort policy revision, not a changed science
endpoint, retroactive compliance claim or hidden retry. Source/row contract,
CPU/wall/address-space process caps, full 65-MiB charge, aggregate ceilings,
prohibited inputs and no-scoring boundary stay unchanged. No reservation is
booked and no staging/data scan is permitted until independent approval.

### Final disposition of that fixed window: UNEXECUTED

At **10:21:42 UTC** the next continuation checked the clock. The fixed
09:09:01 UTC deadline had expired. Do not launch it, refill it or retroactively
claim that it fit. No cluster staging, reservation, native control process,
real genomic read or report occurred under this window. The prospective
65-MiB addition remains **unbooked**; retained charge stays 8,623,306,013 bytes.

Main saved the new utility and tests before the intervening continuation
gap. The earlier local test command returned a live process handle and only
partial output; that handle was missing on resumption. Its final test count
is not known. Do not call the partial output a completed test run.
A **separate software-only verification** subsequently completed: **91
passed, 13 skipped in 0.69s**, exit zero. It exercised the new native tests
plus census/old metadata/classifier tests using the existing project
virtualenv. The 13 skips require Linux or the exact native cluster stack;
they do not validate actual native endpoints or any prepared genomic input.
This verification is not an expired-attempt data run or a new input allowance.

The independent reviewer accepted the rule and explicit original timer
amendment, but exact code/launch approval did not occur before expiry.
Code review may still identify reusable defects; it cannot revive this launch.
The main-owned utility keeps the historical checker/census/classifier intact,
requires pins for every imported local helper, and uses the corrected strict
bounded readers rather than old cap+1 acquisition loops. No biological,
caller-performance or publication result is established. The next operational
decision must use the actual interruptions and scientific payoff, not another
silent timer reset. Broader goal remains active and unachieved.

Separate final tracking checks: **18 passed in 4.11s**; manuscript tables and
quoted p-values reconcile with unchanged `results/`; whitespace check passes.
These checks do not resolve the preserved legacy smoke failure, constitute
a full-suite run, or supply a scientific outcome. Current source/test pins:
`a53b135696b65503ffe65056c11bc419289a2941ef5785ade81348ff8025f46e`
and `d04360a2e9b6ce7cc8391a2d91191813e2d152516cad0822a6ea7e92c6decd95`.

Proposed real run: one process on the existing cluster stack, <=60 CPU
seconds, <=120 wall seconds plus five-second kill grace, <=4 GiB address
space. Use Linux limits and `/usr/bin/time -v`. One synthetic-only cluster
test process may get the same bounds before launch; count its actual CPU
separately. Do not confuse address-space limit, peak RSS and physical RAM.
No real retry is proposed. Preserve partial logs if the one run fails.

Reserve **65 MiB = 68,157,440 bytes**, comprising two <=16-MiB scientific
source passes, two <=16-MiB sealed parser-input envelopes and <=1 MiB of
code/protocol/test/report metadata. This is a conservative named-artifact
reservation; native parser seeks, runtime-library I/O, caches and physical
I/O are not measured by it. All staging, pin checks, test-artifact copies,
report transfer and readback must fit the metadata allowance. Do not book
or refund an inferred physical-I/O saving.

Prior full retained charge: 8,623,306,013 bytes. Proposed new total:
**8,691,463,453 bytes**, below unchanged 64 GiB = 68,719,476,736 bytes.
Book the full addition only after independent approval and before staging;
retain it even if a control or real command fails. Named prior empirical/
diagnostic CPU: 422.552707 seconds; two proposed 60-second process limits
would give <=542.552707 seconds, below unchanged 7,200 seconds. This is not
total historical software-suite or physical project CPU.

Output caps: report/stdout <=64 KiB each, stderr/time log <=16 KiB each,
and the complete four-file output bundle <=128 KiB before transfer. The
code/protocol/report reader must also enforce its summed 1-MiB cap. No
genomic transfer to local disk. Recheck account jobs/scratch before launch;
the 13:48:26 +07 read-only check found no account jobs. Scratch expiry is
October 22, 23:02:50 cluster-local; one extension remained. Preserve small
raw reports off scratch. Do not alter unrelated users' jobs.

## Controls and independent scrutiny

Require synthetic positive and negative controls for both INS and DEL
signs, absent/scalar/magnitude/type/GT/eligibility contradictions, native
wrong size/type and mutation, source integrity, strict read caps, schema
and pin validation before scientific reads. Local native-stack skips are
not native validation. Run the exact-stack Linux endpoint controls before
the real command. Independent reviewer owns a separate note, not this
implementation. Rule acceptance alone is not exact-launch permission.

## What a complete pass buys

Only native/canonical metadata consistency for this unchanged prepared file.
It does **not** certify REF, original-source mapping, alternate haplotypes,
phase, biological truth, callability or a scoring denominator. Label these
UNASSESSED/NOT_VALIDATED in the report. No caller-performance result follows.

The next empirical hypothesis remains a controlled, recoverable native
candidate-generation failure, not final-VCF absence. A released-callset
falsifier can reject that archived motivation cheaply, but positive residuals
are hypotheses until independent allele/read support and same-input native
candidate traces distinguish discovery, filtering and representation.
Unrelated donors and a strong native recovery control remain prerequisites
for publication claims. REF and the empirical protocol require separate
review before further input reads; no automatic screen restart is selected.

Requested worker configuration: GPT-6 Luna/max. Maintained reviewer request:
GPT-6.1 Sol/high. These are requests, not backend attestations. No expensive
campaign or high-impact new scientific direction is selected by this note.
