# Native throughput bundle: independent exact review

2026-10-08. **ACCEPT technical completion of ONE approved replacement bundle**, with the narrow result limits below. Both slots are consumed; this grants no next-stage approval. The initial HOLD and superseded pins remain historical.
The initial review granted no staging, reservation or execution approval. The replacement approval is prospective; it renews no expired attempt or operator timer and grants no broader scientific scope.
Requested maintained reviewer configuration: GPT-6.1 Sol/high; runtime model/effort is not independently attested.
The full goal was read earlier. Read the full execution note, completed 106-line throughput decision, protocol, manifest, launcher, current utility and both staged test files. Independently hashed all nine local bundle files and measured their sizes; no tests or launcher were executed.
Earlier helper implementation reviews remain applicable to their unchanged pins. Cluster state, installed versions, scratch lifetime, local test results and absence of staging remain main-reported, not independently observed here.

## Initial held artifacts inspected: superseded launcher/manifest

| Artifact | Independently verified SHA256 |
|---|---|
| Protocol | `8eaf621e8ccf752417aa0286b2451298e46e17831e6bb85ca0fd4798163c630a` |
| Manifest | `ea852942f339ce31a97e4b3b13350c9372dd17123c347876a1477fda87a6b482` |
| Launcher | `65f09cda29828bb762634645534d70fb177c20144cc9d57a35e3f588acd86e79` |
| Utility | `f97dcf0051e09f799b689be66903f88c3fceef3dd6281043ab92e8a762616214` |
| Native tests | `0d1faed1c397c2acbc3d172a3855b732e0dd7918abaf1b38724e5d720206354e` |
| Prior metadata/seal tests | `65ffd119d382eaba1c3101d4736d3c89d66c707b67b5300b6c6aefffda3e4f67` |
| Frozen truth-unit helper | `4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93` |
| Bounded census helper | `2fb977a24b4d027ee4508f2f45eb07d11866cc4dd8101ab340cf95983de1f523` |
| Sealed-buffer helper | `8b4acc8fa8b9a86d71c9847dd3a175e6816f24a1e2827f231ddf6cf244a05fa0` |

## Accepted policy and scientific boundaries

Accept one NEW immutable ID `native-truth-compatibility-20261008-throughput01`, with one controls slot and one real slot. Removing operator appointment timers is prospective, not approval of an expired launch.
The original active allowance remains UNVERIFIED/UNEXECUTED; the 08:39:01–09:09:01 UTC replacement remains EXPIRED/UNEXECUTED. Preserve the prior native-contract review, old hashes, literal-preservation gap and subsequent accepted software fix. Do not book the expired 65-MiB proposal.
Exclusive `launched`, `controls.claimed` and `real.claimed` directories prevent ordinary replay. Unknown launch status permits reconciliation/collection only, not a fresh slot. Changed pins require exact re-review without slot replenishment.
The six selected test names expand to 4 complete endpoints + 4 bad literals + 2 integrity cases + 4 mocked contradiction/mutation cases + 5 mocked shared-stream drift cases + 1 actual Linux seal case = 20. Do not call all 20 actual native endpoints.
The script requires zero exit status, a 20-pass summary without skip/failure markers, and a controls bundle ≤8 KiB before real launch. The real success path requires a complete report and bundle ≤16 KiB. These are static guards, not observed native passes.
The current utility retains the accepted literal-to-parser field/GT/phase/FORMAT comparisons, scalar absolute-SVLEN rule, full population/order checks, sealed input and acquisition/posthash guards. No new scientific-code defect found in this read.
Keep exactly 11,490 rows, 11,853,747 bytes, source SHA `c908217f7ec8eba1efe93f51605675a8a8b9676d9c9ca443d1348ad0a00f68d2`, order SHA `13db07d2c659f578144067d45eea85684816cce6482230e190a1b01b8d627e37`, and the VCFv4.2 header schema. No source read occurred here.
Either SVLEN sign is accepted uniformly for analysis compatibility, not VCF standards compliance. Retain all global sign flags; equal marginal counts do not establish a type-by-sign cross-tab.
Shared pysam/INFO dependencies are not independent biological evidence. Net serialized invariance is not absence of transient/private changes. REF, mapping, phase, callability and denominator remain unvalidated; no performance effect or score follows.
A is accepted as a development kill-test path with weak publication novelty. Later REF/ALL-SIX work needs separate exact review; this bundle permits no REF/map/BED/caller bodies, scoring, genomic transfer, installation or wider campaign.

## Accounting accepted, not booked or measured

Nine actual staged files total 86,041 bytes <98,304. The four gate-pinned code files now total 61,408 bytes; the execution note's 61,257 was explicitly the earlier pre-comment-change size, not this bundle's measured size.
Ten endpoint fixture hashes plus ten gate hashes read 20×61,408 = 1,228,160 bytes, already >1 MiB. One real code-pin pass adds 61,408. This confirms the need for the metadata amendment without enlarging genomic scope.
Using actual sizes, two bundle envelopes + 21 code-pin passes + 128-KiB synthetic/protocol/launch metadata + six passes over 8+16-KiB outputs = 1,740,178 bytes <2,097,152, leaving 356,974 bytes. Additional outer/internal hash reads and state/log collection must be counted within that headroom, not omitted.
Accepted reservation: 32-MiB source + 32-MiB parser envelopes + 2-MiB metadata = 66 MiB = 69,206,016 bytes. Retained total would be 8,623,306,013 + 69,206,016 = 8,692,512,029 <68,719,476,736. No refund or duplicate expired charge.
Failure outputs need a size guard before any transfer/readback too; success-path script checks do not bound failed log writes. Do not fetch an oversized bundle under the small-output account. Runtime-library/cache/opaque parser/physical I/O remains explicitly excluded, not measured.
Accept each payload's 60 CPU /120 wall +5-second grace /4-GiB address-space limits and launcher's 300 wall /60 own CPU /4-GiB envelope. RLIMIT_CPU is per process, not an aggregate tree cap.
Reserve 180 named CPU seconds: prior 422.552707 +180 =602.552707 <7,200. Inner timings are descriptive, not added to a valid outer tree measurement. Measured over-reservation requires INCOMPLETE accounting, not a silently increased limit.

## Blocking finding: nested timeout groups can escape outer supervision

The manifest's outer recipe runs `timeout -k 5s 300s bash run_native_throughput.sh`. Launcher lines 26 and 49 then run additional GNU `timeout` commands in default process-group mode. There is no termination/cleanup trap or explicit active-payload group tracking.
Default nested timeout groups separate the active payload from the outer group. If the outer launcher is terminated while waiting, its signal/group kill need not terminate that nested payload; the payload can continue under its own watchdog. The existing inner limit bounds continuation but does not prove outer-tree termination.
The same path can break the claimed outer CPU measurement: an orphaned, no-longer-waited descendant can finish after outer GNU time records its result. Do not treat that timing as complete waited-tree CPU merely because both commands use GNU time.
Required narrow correction: keep the payloads in the outer supervised group or explicitly forward termination to the active payload group and reap it; ensure the kill-grace path cannot leave a live payload. A path that cannot recover complete waited-tree CPU must retain INCOMPLETE accounting and the full reservation, not claim a complete measurement.
Use the same two slots and input/resource caps. This asks for launch-supervision correctness, not more genomic reads, another experiment, new workers or renewal of an old timer. Changed launcher/manifest pins need focused exact review before staging/booking/launch.
No Linux termination behavior was exercised here; this is a static process-group/supervision finding, not an observed cluster failure. Local 101-pass/13-skip/0.87-second and shell-syntax results are reported only and do not cover this launcher termination path.

## Initial disposition: preserved

Current exact bundle NOT APPROVED. Policy, rule and corrected account stand; resolve the specific launcher defect and preserve all unexecuted history. Main's account/scratch/fresh-path/staged-pin preflight remains required after exact approval, without another genomic hash pass.
Only this new owned review note changed for this request. No cluster/network/genomic read, test, job, install or Git action occurred. Requested Sol6.1/high remains unattested; the broader publication goal remains unmet.

## Focused replacement review: exact approval

Read the full CURRENT launcher, manifest and execution note; independently rehashed all nine bundle files and checked their sizes. No Linux termination test, cluster inspection or genomic read occurred.
APPROVED replacement launcher SHA256: `0fd887fdf134b3ab1365b35096bf95694204dd4a206dec5c7747be787f3b780d`.
APPROVED replacement manifest SHA256: `8e0a7f83a326adbf129c84eb1894544a863922beb3501504ce7a885efdc0a0a1`.
Protocol stays `8eaf621e8ccf752417aa0286b2451298e46e17831e6bb85ca0fd4798163c630a`; utility, tests and all three helper pins remain exactly those in the initial table. The old `65f09c…` launcher and `ea8529…` manifest are NOT approved and, main reports, were never staged/launched.
The two inner commands now use `timeout --foreground -k 5s 120s`, keeping the outer process group. The approved outer recipe uses `/usr/bin/time -v -o launch_tree.time.log timeout --signal=KILL 300s bash run_native_throughput.sh` with the manifest's exclusive-path/hash checks, redirections, and inherited 60-CPU/4-GiB limits.
For these fixed Python payloads/tests with no explicit child-process launch, this resolves the separate-group defect. The outer default group receives uncatchable KILL at 300 seconds, stricter than 300+5; payload native threads share their PID. This is static acceptance of declared containment, not proof that an uninspected library can never fork, detach or change groups.
Installed timeout-help and Truvari delegation-source observations are main-reported, not inspected anew here. They support the declared mode/shared backend but do not constitute a runtime containment test or independent truth validation.
Accept the manifest's explicit CPU qualification: an outer kill with incomplete wait/reaping yields INCOMPLETE accounting and retains the full 180-second reservation. Apply the same rule to any other abnormal termination that loses waited-descendant accounting; do not report a partial outer timing as complete tree CPU or replay a consumed slot.
Current nine-file bundle =86,494 bytes <98,304; four gate-pinned code files remain 61,408 bytes. The prior plan recalculates to 1,741,084 bytes, leaving 356,068 bytes within 2 MiB for additionally counted metadata operations. Small-output transfer/readback guards and declared read counts remain required, including failure paths.
Scientific source/parser envelopes stay 64 MiB; metadata stays 2 MiB; the ONE full reservation remains 69,206,016 bytes, prospective retained total 8,692,512,029. Named CPU reserve remains 180, prospective total 602.552707. No expired 65-MiB charge, refund, new input or retry is added.
Main may proceed ONCE with this immutable ID after the declared account/scratch/fresh-directory preflight, one full reservation before staging, and staged-pin checks without an additional genomic hash pass. Approve exactly one 20-control process and, only on its complete zero-skip pass, one pinned prepared-input process under the manifest/launcher limits.
No direct/unlimited launcher invocation, replacement worker, renewed slot, REF/map/BED/caller/scoring operation or experiment extension is approved. Lost handles permit reconciliation/collection only; changed pins, environment or unavailable scratch require revalidation, not automatic retry. Existing historical allowances remain UNVERIFIED/UNEXECUTED and EXPIRED/UNEXECUTED.
Only this owned note changed. This reviewer performed no staging, booking, test, cluster/network/genomic read, job or Git action. Approval is not an executed native result, cap-enforcement observation, validated denominator or publication advance; requested Sol6.1/high remains unattested.

## Completed result: accepted within the engineering contract

Read all 11 completed local raw output files under `results/data_audits/svpg_2026/2026-10-08/native-throughput01/`. Earlier partial local-copy availability was a transfer-readiness issue, not experimental absence; no second launch or data pass is inferred. Main reports the same SCP handle completed exit 0.
Independently verified native report SHA `3f86568e741577ebaccec12dc5860f515c8e27eb2e25914c7a4bef8c93525d9a`, controls stdout `463888af8aa6add0b45abfc5395a7bb78f3b887879fed8a0f9b66d55a0217f4f`, controls time `058705fa60c2a6f1ed4c4d9bb24ac029d2330865d5e923f9186172da30f71e6f`, native time `eb08579f509c45f17068dd28110fa8aee5c3cbb7f64c9e35ea9a7dd0908ce264`, outer time `34779ee829cf52c88b2dfa5562392169c2c8bc88ab1fbb7a4de011d2631802a8`; all match the supplied pins.
Local byte counts reconcile: controls 99+0+1,525=1,624 ≤8,192; native 1,610+1,516+0+1,112=4,238 ≤16,384; outer time/stdout/stderr/state 788+288+0+50=1,126 ≤16,384. Total 6,988 bytes across 11 files; all three stderr files are empty.
State records `LAUNCH_CLAIMED -> CONTROL_PASS -> REAL_RUNNING -> COMPLETE`. Launcher stdout records seven code/test/protocol hash checks OK; nine-file prelaunch verification and booked-before-staging reservation remain main-reported, not independently observed remotely.
Controls stdout records 20 passed, zero skips, in 1.54 pytest seconds. This is ten native endpoint cases, nine mocked contradiction/drift cases and one actual Linux seal case, not 20 independent native endpoints.

| Logged process | User + system CPU seconds | Wall seconds | Exit / delivered signals |
|---|---:|---:|---|
| Controls | 0.67+0.45=1.12 | 2.34 | 0 / 0 |
| Native | 2.50+0.37=2.87 | 3.52 | 0 / 0 |
| Outer waited run | 3.18+0.89=4.07 | 5.95 | 0 / 0 |

Accept normal-completion outer CPU accounting ONCE: 422.552707+4.07=426.622707 named seconds. Inner 3.99 seconds are descriptive, not charged again. Logs display CPU to 0.01 second; the seven-decimal ledger sum does not imply seven-decimal new measurement precision. Observed use is below the 180-second reservation and 7,200-second ceiling.
Outer/native maximum RSS is 118,172 KiB =121,008,128 bytes, distinct from address space and total physical RAM. Normal times are below the reviewed process limits; this result does not exercise CPU/address-space/timeout enforcement or prove abnormal-kill containment or absence of every possible orphan.
Report and native stdout reconcile: 11,490 records/unique IDs, 11,853,747 input bytes, the approved source/order/protocol/helper pins and exact stack, native PASS, stable snapshot, sealed parser input, zero repairs/drops and net serialized invariance. Reviewed completed code-path checks support direct literal/native relevant-field, GT/phase/FORMAT, type and absolute-length agreement; this reviewer did not re-read/hash genomic input.
Canonical counts 6,960 INS +4,530 DEL =11,490; 4,530 global sign-only flags are retained. Still no type-by-sign joint table: do not conclude all DEL signs disagree. Shared pysam/INFO inputs do not supply independent biological validation or VCFv4.2 compliance.
Accept full retained charge arithmetic: 8,623,306,013+69,206,016=8,692,512,029 bytes, no refund and no duplicate expired 65-MiB charge. Actual booking order/transfer counts remain main-reported; this review verifies the local outputs and reconciliation, not all physical/runtime I/O or a newly inspected reservation ledger.
Technical completion ACCEPTED, not publication progress or proof of biological truth. REF remains UNASSESSED, denominator NOT_VALIDATED, scoring false; no REF/map/BED/caller read, native rerun, scientific extension or next-stage launch is approved. Both approved slots are exhausted; historical expired attempts remain unchanged.
Only this review note changed. No source/cluster/network read, test, job, install or Git action occurred; requested Sol6.1/high remains unattested.
