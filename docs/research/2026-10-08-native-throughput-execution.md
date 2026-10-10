# New durable native experiment — completed once

Date: October 8, 2026. The completed
[Sol6.1/max-requested decision](2026-10-08-empirical-throughput-decision.md)
selects one native compatibility observation before the reference/ALL-SIX
development kill test. Generic benchmarking remains weak novelty, not a
publication lead. This note implements that decision, not a reduced goal.

## Preserve the expired attempts

The prior active allowance remains UNVERIFIED/UNEXECUTED. Its reviewed fixed
wall replacement remains EXPIRED/UNEXECUTED. No staging or input reservation
was booked. Do not count an imaginary run or refund historical charges.
The new policy uses one pinned experiment ID, fixed payload launch slots and
process limits. Product interruptions permit status inspection/collection,
not replay or slot renewal. Unknown launch status forbids another launch.

ID: `native-truth-compatibility-20261008-throughput01`.
Root: `/scratch/igorno-alignssl_restart_20260922/native-truth-compatibility-20261008-throughput01`.
The [manifest](../../results/data_audits/svpg_2026/2026-10-08/native_throughput_manifest.json),
[protocol](../../results/data_audits/svpg_2026/2026-10-08/native_throughput_protocol.json)
and [launcher](../../results/data_audits/svpg_2026/2026-10-08/run_native_throughput.sh)
freeze the two payload slots and commands. Configuration flags are not review approval.

## Prospective metadata correction, not extra scientific reads

The decision initially carried forward a 65-MiB proposal with only 1 MiB for
metadata. A concrete count disproves that allowance for its required native
controls: each of ten endpoint cases hashes all four local code files once
in its protocol fixture and again in the gate. At the corrected pre-budget
source sizes, **10 × 2 × 61,257 = 1,225,140 bytes**, already over 1 MiB before
staging, real-run pins or output archival. Do not ignore those reads or drop
controls to pretend the smaller allowance fits.

Propose **2 MiB metadata**, with unchanged 32-MiB scientific-source and
32-MiB sealed parser envelopes: **66 MiB = 69,206,016 bytes** once.
8,623,306,013 + 69,206,016 = **8,692,512,029** retained bytes, below unchanged
64 GiB. The previous unbooked 65-MiB proposal is not added as a second charge.
One utility constant changes; source/parser byte limits, fields, population,
versions, outcome and no-repair policy do not. Exact reviewer approval is
required for this accounting correction before booking or staging.

Metadata plan: staged bundle <=96 KiB; two copy/hash envelopes <=192 KiB;
20 control code-pin passes plus one real pass <=1.3 MiB; <=128 KiB for
synthetic fields/protocol/launch metadata; up to six archival/hash/readback
passes over the 8-KiB control and 16-KiB native output caps <=144 KiB. These
fit 2 MiB with headroom. Runtime-library/cache/physical I/O are not measured.
The real utility still enforces its own much smaller summed code/protocol/
report cap; cumulative control pin reads are the reason for this amendment.

## Fixed slots and interpretation

| Slot | Exact scope | Required completion |
|---|---|---|
| Controls: one process | Four native sign/kind positive cases, four bad-literal cases, two native integrity cases, four contradiction/mutation cases, five paired-parser drift cases, one actual Linux seal control | **20 passed, zero skipped**; <=8-KiB raw output bundle |
| Prepared truth: one process | Same pinned 11,490 unchanged rows; direct literal/native relevant-field comparison, native size/type, source/count/order/posthash and net serialized invariance | Complete native metadata report, <=16-KiB raw output bundle; no REF/denominator/scoring claim |

Control failure prevents the real slot. Exclusive claim directories precede
spawning. No repeated control or real slot; preserve INCOMPLETE if either
fails. Keep all raw logs, fields and rows. PASS only tests H_N: native
compatibility, not standards compliance, independent biological truth or
caller performance. REF/original mapping/phase/callability/denominator stay
unassessed. Source/parsers share dependencies, not independent truth evidence.

Each payload: <=60 CPU seconds, <=120 process wall seconds plus five-second
kill grace, <=4 GiB Linux address space. Outer launcher: <=60 own CPU seconds,
<=300 process wall seconds; use uncatchable KILL at that outer deadline,
stronger than the five-second grace maximum. Inner timeouts use
`--foreground` so they retain the outer process group, rather than create
separate descendant groups. These pinned Python payloads/tests contain no
child-process spawning; their native threads belong to the same process.
Installed GNU timeout help was read as software metadata, not a runtime
termination test. This exact containment recipe is pending reviewer scrutiny.
GNU time records the outer waited process tree once; inner timings describe
components and are not charged twice. Reserve 180 named CPU seconds; prior
422.552707 plus reservation = 602.552707, below unchanged 7,200. If observed
tree use exceeds the reservation, flag incomplete accounting rather than
silently raise it or claim cap compliance. This is not total historical CPU.
If an outer kill prevents descendant wait/reaping, tree accounting is
INCOMPLETE, not a complete measured-CPU claim; retain its reservation.

Current code SHA:
`f97dcf0051e09f799b689be66903f88c3fceef3dd6281043ab92e8a762616214`.
Tests/helper pins are in the manifest and launcher. Only the reservation
constant/comment changed from the independently accepted literal fix.
Local focused check after that change: **101 passed, 13 skipped in 0.87s**;
shell syntax passes. Skips are not exact-stack endpoint validation.

## Original prospective state, preserved

No reservation, cluster staging, control or real-data run is claimed here.
The maintained Sol6.1/high-requested reviewer must accept the new policy,
66-MiB accounting, exact code/test/protocol/launcher/manifest hashes and the
outer recipe. Main then checks account jobs, scratch lifetime, fresh paths
and staged pins without an extra genomic-source hash pass. No new package,
raw data or genomic transfer is required. Small raw outputs will be preserved
off scratch after their caps/hashes are checked. No unrelated job is affected.

## Completed execution and archival

The maintained reviewer approved the replacement launcher/manifest before
the one reservation, staging and launch. The initial held bundle was never
run. [Exact review and result acceptance](2026-10-08-native-throughput-review.md)
preserve both sets of pins and the process-group correction.
The approved bundle completed once: 20 controls passed with zero skips,
followed by native compatibility PASS for all 11,490 unchanged rows.
Both launch slots are consumed. Outer waited-tree CPU is 4.07 seconds,
wall 5.95 seconds; inner timings are not charged again. Full retained
reservation is 69,206,016 bytes, cumulative 8,692,512,029 bytes.
All 11 small outputs (6,988 bytes) are copied locally and hash-verified;
the same copy handle completed exit zero after an initial partial transfer.
[Result and boundaries](2026-10-08-native-throughput-result.md): REF remains
UNASSESSED, denominator NOT_VALIDATED, scoring false. No next-stage execution
or publication claim follows from this completed engineering check.
