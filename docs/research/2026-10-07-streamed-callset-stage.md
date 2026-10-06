# Five unfinished call sets: bounded streaming repair

Date: October 7, 2026. Current status: stage-03 and final stage-04 failed;
the custom-stager route is closed. No scientific comparison is approved.

The prior pass made progress: checkpoint `5739924` was pushed and the remote
SHA matched. It preserved two failed staging passes and explicit scientific
limits. The publication goal remains active and unachieved. Main read its full
current objective again before this continuation.

## Engineering change, not a new scientific hypothesis

Stage-02 completed cuteSV but stopped when a DeBreak raw line exceeded 32 MiB.
The failure does not establish which field caused the oversized line. Do not
omit DeBreak or call this a biological null. The independent reviewer
recommended one bounded streaming repair, not its execution.

`analysis/stream_vcf_rnames.py` reads chunks of at most 65,537 bytes. It hashes,
UTF-8-validates and charges all raw bytes, including discarded INFO/RNAMES.
Only the exact INFO key is removed. It does not buffer the discarded value
or the whole raw line. Retained lines remain capped at 32 MiB, and INFO-key
metadata at four MiB. Duplicate keys and truncated records fail. The parser
preserves all other bytes, order, multiplicity and line endings. A complete
ten-column last record need not have a final LF.

The stager retains its original default behavior and two-GiB cap. Only the
explicit `remaining-five-stream-rnames-v1` protocol permits the proposed
three-GiB cumulative source ceiling and streaming route. It requires exactly
the five unfinished callers and verified reuse of cuteSV. The reused object
must match its pinned completion report, source member metadata and derivative
SHA-256; verify the derivative bytes once and charge that read. No sort,
normalization, GT imputation, allele split or biological filter is performed.

Main's fixed-seed synthetic check compared 1,000 legal records against the
legacy route. Bytes, source and derivative hashes, decoded counts, RNAMES
counts and inventory categories agreed. It is now a regression test, not an
unrecorded interactive claim. The initial integrated parser/legacy/guard run
passed 36 collected cases. A separate Luna/max-requested worker adds
adversarial delimiter, duplicate, oversized, truncation and CRC cases.

## Frozen proposed reservations

| Item | Bytes |
|---|---:|
| Preserved previous source charges | 2,080,329,990 |
| Five unfinished source members | 1,006,990,060 |
| Cumulative reserved source charge | 3,087,320,050 |
| Proposed source ceiling | 3,221,225,472 |
| cuteSV derivative hash-verification read | 29,410,475 |
| Cumulative reserved aggregate charge | 3,116,730,525 |
| Aggregate ceiling, unchanged | 6,442,450,944 |
| Unreserved aggregate allowance | 3,325,720,419 |

The new protocol and reservation are append-only siblings under
`results/data_audits/svpg_2026/2026-10-07/`. They do not edit prior protocols,
results or charges. Resource limits remain two combined CPU hours and four
GiB RAM; the unchanged local supervisor stops at three GiB sampled RSS and
1,800 seconds CPU/wall. Sampling is not a hard macOS RAM guarantee. Fresh
output/log directories, a fresh free-space check and at least ten GiB retained
free space are required. Preserve full reservations and partials on failure.
No automatic fourth pass is permitted by this proposal.

The fresh account queue is empty. Restart scratch expires October 22 at
23:02:50 cluster-local, with one extension available. No cluster job was
started or cancelled. Main implements the critical-path parser. Internal
workers handle disjoint adversarial tests, sample/normalization controls and
synthetic truth preparation. The independent reviewer uses Sol6.1/high as
requested; workers use Luna/max as requested. Actual runtime configurations
are not independently attested. No sidebar chats were created.

## Scientific gates still separate

The weaker released-callset development estimand remains authoritative.
Common raw reads/depth, run/reference/graph identity and independent replication
remain unproven. Completion of this stage would establish six available
derivatives, not accuracy, candidate completeness or novelty. Exact sample
mapping, source/ALT identity, deterministic sort and multiallelic rules,
truth eligibility and executable downstream traffic accounting still need
review before the first scientific screen. No training campaign is selected.

## Independent review finding before execution

Dirac rejected the initial stager pin for a concrete reservation bug: reused
file verification read until EOF, so a growing file could exceed its reserved
length before the final snapshot rejected it. Its synthetic probe reserved
four bytes and consumed one hundred. Main changed verification to hash exactly
the pinned byte count using remaining-length-capped reads, reject premature
EOF and retain the final descriptor/path snapshot and SHA check. A separate
growth test is required before the final approval. No real source body was
read for this review or repair. The previous failed attempts remain unchanged.

## Final stage-only approval before execution

Fermat completed thirty adversarial synthetic cases, including actual
growth-after-preflight and truncation checks. Main reviewed its test changes;
the integrated staging/parser/legacy/guard suite passed **66 cases in 1.48
seconds**. Dirac then approved one pass over the five unfinished members and
exactly 29,410,475 bytes of cuteSV verification. It independently checked the
repaired loop using synthetic growth/truncation probes. The final pins are:

- Stager: `94ecdd68bf63a9463889600eff2c2ee644f74980659baf36a511c53b29fa80bc`.
- Parser: `5cca0dd5832b26b17a6ae1bf83a178cbbcd700e16e7cc612f3cd06d314cc70bf`.
- Unchanged supervisor: `97b70cf7cea3c78649a4446d54af97638f0f56237d169f6eaefd251e6b1adcbd`.
- Stage-03 protocol: `049e2e2b8281b20362bca0696a39cbea68e1070f0479ba56d2bbe5207ac0a1f5`.
- Stage-03 reservation: `2681460f9ad7a62d8e3d3b9bbdd304acbf742d9ef697daf6abe4aea6bf257699`.

Use fresh sibling outputs/logs and an immediate free-space preflight, then the
unchanged resource supervisor. Keep full reservations and partials on failure.
No automatic retry or additional source pass is covered. Truth parsing,
normalization, sorting, screening, matching and refinement remain closed.

## Stage-03 execution: retained-content failure

The approved pass verified the completed cuteSV derivative within its
29,410,475-byte reservation, then stopped on DeBreak: retained content exceeded
33,554,432 bytes even with the exact INFO/RNAMES streaming route. This rules
out the proposed RNAMES-only repair as sufficient. It does **not** identify
the offending field, contig or biological mechanism. The frozen DeBreak
header declares no RNAMES field. A contig length above the limit in that
header does not prove that contig caused the failure.

Delivered new source bytes were 34,144,777. Keep the full 1,006,990,060-byte
source reservation, giving 3,087,320,050 cumulative source bytes and
3,116,730,525 aggregate bytes including cuteSV verification. Combined CPU
was 13.930435 seconds, wall time 13.761307 seconds, sampled RSS peak
40,660,992 bytes and child rusage peak 52,649,984 bytes. No resource guard
tripped. Failure and resource reports are saved as stage-03 siblings under
the dated audit directory; original files and partials remain outside Git.
No fourth pass was started. All six callers are still required for this
particular diagnostic; do not accept a five-caller union.

An independent reviewer is considering feasibility, and a separately
requested Sol6.1/max decision agent is comparing a bounded larger-record
route, a scientifically prespecified autosomal view and stopping this
acquisition route. The six-GiB traffic limit is an engineering budget, not a
user-imposed scientific label budget. Any amendment must be explicit before
outcomes, retain historical charges and preserve the resource/fairness
controls; do not credit back failed passes or change scientific rules to
obtain a favorable result. No decision or new read is inferred from this
request. The wider publication objective remains active and unachieved.

## High-impact decision: one final larger-record attempt

Faraday (Sol6.1/max requested) selects A: one final 128-MiB retained-record
attempt, then existing bcftools preparation if feasible. Main accepts that
bounded engineering decision. It retains all six callers, nonautosomal
records, source/member identities, multiplicity, alleles and GTs. No scientific
population, matching rule or acceptance threshold changes. No inference is
made about the offending field or contig. B, an autosome-only staged view,
adds omission risk and is not known to avoid the failure. C, stopping this
route, is premature while the cheap standard-tool attempt remains untested.

The proposed cumulative source reservation is 4,094,310,110 bytes under four
GiB; the aggregate reservation after another bounded cuteSV verification is
4,153,131,060 bytes. The explicit **engineering** aggregate allowance proposed
for staging and later fixed downstream work is twelve GiB. Historical charges
are retained. Later preparation/truth/screen/refinement reservations must be
frozen before outcomes, not silently assumed approved by this source decision.
Memory remains four GiB and combined experimental compute two CPU-hours.

Firm stop: at most two hours for implementation/review and thirty minutes
for staging/preparation. A record above 128 MiB, integrity failure, unsupported
input, preservation failure or resource overrun stops this archive route.
No further cap increase or parser redesign. It is a feasibility failure, not
a biological rejection or permission to drop a caller. A successful stage
should lead directly to the fixed diagnostic once executable safeguards pass
review; no extra broad literature/provenance campaign is needed beforehand.

The synthetic probe tests exact 128-MiB retained ALT and INFO fields and
one-byte overflow for both, using bounded lazy inputs under the unchanged
supervisor. The initial run passed at 819,613,696-byte child peak RSS and
9.658496 CPU seconds. After removing one unused import, the exact final probe
pin `8644873b66f1b63ad552bc8129d615ae7496e5efd01ea5d1a08a8844666862e8`
was rerun into a fresh sibling log directory: passed at 828,129,280-byte child
peak RSS, 826,945,536-byte sampled peak, 9.413908 combined CPU seconds and
9.937017 wall seconds. Both raw reports are preserved. These synthetic bytes
are not biological observations or genomic-input budget credit.

The proposed final stager pin is
`257516f4added0207f8f6d966e9e6109244c18346b6d65b744d1529f2f18ca11`;
protocol `4858cd824ea81a9be998a62043d3c2eb1736d724ea34b09ceb86e5973aab95ac`;
reservation `45ed6a42c5e8dab3be60c9c7fe4051725bbcb9eb7e81993b41718279676998d2`.
The parser and supervisor remain at their stage-03 approved pins. The targeted
suite passed 73 cases. The full suite before the seven final-protocol cases
passed 610 with 29 skipped; a new integrated run is still required for the
final checkpoint. No fourth source read has begun at this entry.

Schrodinger supplied a separate synthetic-only truth-preparation driver and
34 tests. Main read its complete implementation and tests. Review caught and
fixed source mutation protection, BED overflow accounting, valid trailing
FORMAT omissions and duplicate non-GT fields. The driver does not approve
itself: no real truth/BED preparation has run. Exact sample-label and
contig/reference gates remain distinct from a source hash or software test.

### Final stage-04 independent approval

Dirac independently verified the final stager, unchanged parser/supervisor,
protocol and reservation pins above, inspected the exact-current-pin synthetic
resource report and approved **one final remaining-five source pass plus
bounded cuteSV verification only**. The reported 73-test pass was supplied by
main, not independently rerun by the reviewer. Fresh outputs/logs, immediate
disk preflight and unchanged guards are required. Retain 4,094,310,110 source
bytes and 4,153,131,060 aggregate bytes even on failure. Any size, integrity,
preservation, unsupported-input or resource failure ends this route: no retry,
cap increase, parser redesign or five-caller union. The twelve-GiB allowance
does not authorize future scientific stages. No truth/sort/normalization/
screen/matching/refinement execution is approved.

## Final stage-04 outcome: stop this custom-stager route

The final approved attempt ended with `Invalid VCF position` in SVIM.
The offending position was not recorded. This is an unsupported-input failure
under our parser, not evidence that the publisher's VCF is malformed or a
biological null. No fifth custom-stage attempt, cap increase, parser redesign
or reduced five-caller union follows from this failure.

Four complete files remain available outside Git:

| Caller | Source records | Complete source bytes | Status |
|---|---:|---:|---|
| cuteSV | 51,561 | 30,029,207 | Reused stage-02 derivative; bounded SHA verification passed |
| DeBreak | 26,421 | 935,962,599 | Full member CRC passed; source and derivative SHA agree |
| Sawfish | 43,944 | 25,716,015 | Full member CRC passed; source and derivative SHA agree |
| Sniffles | 32,567 | 15,004,300 | Full member CRC passed; source and derivative SHA agree |
| SVIM | Not established | Not complete | Partial retained; failure preserved |
| SVPG | Not read | Not complete | Member unopened |

DeBreak's largest retained line is 60,480,492 bytes, with zero removed RNAMES.
This measures the actual size, but does not identify the field or contig that
caused earlier failures. DeBreak has 17 contig-order violations against its
header; cuteSV has 23. Both need a separate standard sorting stage. Source
order was not changed here. Sawfish and Sniffles have partial/missing GT and
reference-only GT records: they must not silently become alternate genotypes.

The stage delivered 980,484,060 new decoded source bytes. All conservative
reservations remain charged: cumulative source **4,094,310,110 bytes** and
aggregate **4,153,131,060 bytes**. No refund uses the smaller delivered amount.
Combined CPU was 78.557736 seconds; wall time was 76.783519 seconds. Both
child rusage and sampled peak RSS were 385,282,048 bytes. No resource guard
tripped. `stage_04_failure.json` and `stage_04_resources.json` preserve the
small reports in the dated audit directory; original files, partials and logs
remain outside Git. No historical report was overwritten.

### Compatibility caveat and separate alternative

The [official VCF 4.2 specification, section 1.4.1](https://samtools.github.io/hts-specs/VCFv4.2.pdf)
permits telomeric positions zero and N+1, where N is the contig length.
Our custom validator rejects positions below one. Dirac tested the installed
pysam 0.24.1 text parser with synthetic memory pipes: it preserves positions
zero and 101 for a contig of length 100, while rejecting negative and
nonnumeric positions. POS=0 yields `record.start=-1`; a record constructor
rejects that start. Constructor-only tests are thus not a valid text-parser
compatibility check. Never clamp, shift or omit these boundary records.
These tests do not identify the actual rejected SVIM value.

The Firecrawl plugin returned HTTP 200 for the official PDF but its targeted
four-page extraction answered that the information was absent. That answer
is not evidence against the specification. The ordinary web reader supplied
the primary section text instead. No Firecrawl CLI was used or installed.

The reviewer recommends evaluating a **distinct byte-preserving transport
and standard HTSlib-parser route**, using only the two unfinished members
and the four verified completed files. It does not reopen the custom stager.
No new source read is approved at this entry; a separate high-impact direction
decision and independent bounded protocol review are required. Truth/sort/
normalization/screen/refinement gates stay closed. Do not extend engineering
work indefinitely or infer scientific eligibility from transport success.

Final integrated validation: **617 tests passed, 29 skipped in 143.23 seconds**;
manuscript consistency passed. The separate truth-preparation driver remains
synthetic-only. Publication significance, residual recoverability and an
independent-donor result are still unproven.
