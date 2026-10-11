# One original-REF check — prospective, not launched

Date: October 8, 2026. Native compatibility completed and its raw result was
independently accepted. The selected development falsifier now needs an
original anchored REF check before caller preparation. This is a technical
precondition, not a new method, biological truth or a validated denominator.
No real REF read, reservation or staging is claimed by this draft.

ID: `original-ref-validation-20261008-throughput01`.
Root: `/scratch/igorno-alignssl_restart_20260922/original-ref-validation-20261008-throughput01`.
Keep one synthetic-controls slot and one real slot, with an exclusive durable
claim before either spawn. No retry, slot renewal, source repair, discarded
row, normalization, caller input or scoring. Lost handles permit status and
log collection, not another launch. Preserve every historical attempt.

## Exact input and semantics

Use the existing prepared `eligible_truth.vcf`: 11,490 unchanged rows,
11,853,747 bytes, source `c908…68d2`, order `13db…e37`. The completed native
report binds that same population and native code/protocol/helper pins.
The [prospective protocol](../../results/data_audits/svpg_2026/2026-10-08/reference_throughput_protocol.json)
records full hashes; its approval flag is configuration, not reviewer approval.
The prior native report stays at its completed cluster path; no native rerun.

Reference: existing `recovery-pilot-v1/hs37d5.fa.gz`, 892,326,179 compressed
bytes, SHA `e915…0285`; FAI SHA `1eab…630c`. No GZI/random faidx fetch.
Read compressed bytes into an immutable bounded payload, hash that payload,
parse the pinned FAI dictionary, and decode standard gzip sequentially to EOF.
Check every complete contig and its length, including unqueried contigs;
check all original anchored REF spans, retaining exact prepared identities.
Posthash sources, FAI, native report and code; recheck the protocol snapshot.
Exceptions invalidate the whole observation; never report prefix validation.

PASS means anchored REF agrees with this reference. It does not establish
ALT/phase/source-map/callability validity, biological allele truth, or a
denominator. The result must retain NOT_VALIDATED and scoring false.

## Complete prospective resource account

Reserve **7 GiB = 7,516,192,768 bytes** once only after exact approval and
before staging. Current retained 8,692,512,029 would become **16,208,704,797**,
below the unchanged 64-GiB ceiling. No historical charge is refunded.

| Named envelope | Bytes |
|---|---:|
| Three encoded passes at the pinned reference size: acquisition, gzip input, posthash | 2,676,978,537 |
| Delivered decoded FASTA cap | 4,294,967,296 |
| Failed decode overflow/read-ahead allowance | 65,536 |
| Three truth envelopes, each 16 MiB | 50,331,648 |
| FAI/code/tests/protocol/native-report/control-fixture/staging/log metadata | 67,108,864 |
| Sum | 7,089,451,881 |
| Reserved headroom | 426,740,887 |

The compressed acquisition cap is 1 GiB, but decoding only begins after the
exact pinned size/hash pass. Acquisition failure can therefore read up to
1 GiB without also consuming the complete decoded envelope; that failure
path is below the same reservation. Posthash reads no more than its cap,
with no cap-plus-one EOF probe. Concurrent reference growth could add at
most 181,415,645 bytes above its pinned-size envelope before failure, inside
the 426,740,887-byte headroom. Opaque cache/runtime/physical I/O is not measured.
The three encoded envelopes count named logical consumption, not a claim
that every buffered compressed byte is read exactly once internally.
Any extra metadata/readback must stay inside the stated envelope/headroom.

Hard code limits: 4-GiB delivered decode, 256-MiB single contig, 1-MiB FASTA
line, 30,000 queries, 16-MiB total query REF, 1-MiB FAI, 64-KiB protocol and
native/result reports, 1-MiB pinned code/protocol metadata.
Main inspected the installed Python 3.10.20 gzip read1/read implementation:
8192-byte default buffers, bounded decompress output, CRC before next member.
The production protocol now binds CPython 3.10.20, 8192-byte default buffer,
and gzip module SHA `fb13…a907`; the library source is checked before truth
reads and posthashed afterward. This is source/runtime binding, not executed
bytecode attestation or proof on all Python releases. It supports a conservative
64-KiB failure allowance, not measured traffic or a new decoder. Independent
review must challenge that bound.

Prospective controls: full synthetic new-gate suite, zero skips, 60 CPU/
120 wall seconds plus five-second kill grace. Real REF payload: 600 CPU/
900 wall seconds plus five-second kill grace, Linux address space 4 GiB.
Outer launcher: 60 own CPU/1100 wall seconds, same address-space limit.
Use outer default-group uncatchable KILL at 1100; inner foreground timeouts
retain that group. Only the real payload subshell raises its soft CPU limit
to 600 within the inherited hard ceiling of 600. No payload child spawning.
Reserve 720 named CPU seconds: prior 426.622707 +720 =1146.622707 <7200.
Measure normal waited tree once; inner time is descriptive, not added twice.
Abnormal loss of waited descendants or measured use beyond reservation is
INCOMPLETE accounting, with the reserve retained; never replay a slot.

Bundle <=128 KiB; controls output <=16 KiB; REF report/stdout/stderr/time
bundle <=256 KiB; outer/state <=16 KiB. Size-check failure outputs too before
copy/readback. Six copies/readbacks of all capped outputs use under 2 MiB.
Synthetic fixture/code-pin operations must fit the 64-MiB metadata envelope;
freeze exact tests/counts/hashes in the final manifest, not this draft.

The current nine-file staged bundle is **115,269 bytes** below 131,072.
Five gate-pinned code files total 79,090 bytes; the installed gzip source adds
21,849. A conservative 64 synthetic case/fixture envelopes, each at most
three code/runtime passes plus 16 KiB small fields, consume under 21 MiB.
Two staging envelopes, real pin/posthash/FAI/native-report checks and six
capped output copy/readback envelopes still fit below the 64-MiB metadata
allowance. This is a count/budget bound for the fixed synthetic code, not a
generic claim about arbitrary future tests or physical traffic.

## Review and current state

Worker initial handoff: 52 combined synthetic passes in new-gate and unchanged
reference test files, zero skips. Main integrated those files with focused
historical tests: 118 passed/13 skipped in 4.34s;
manuscript reconciliation passes. Neither is a real reference observation.
Main requested four targeted synthetic regressions in the new gate suite.
The maintained reviewer accepts REF semantics but found a cap-plus-one
posthash EOF probe and unpinned decoder assumption. Main removed that probe
without changing historical helpers, bound the runtime, and requested focused
growth/CRC/member/read-ahead controls. Correction review remains required;
no launch authority is supplied by the first code review.
Exact final protocol/launcher/manifest/test pins and controls count still need
separate independent execution approval before reservation or cluster staging.

Final worker handoff: **62 combined passed, zero skips**; main collection
separates **41 new-gate tests +21 unchanged reference tests**. Main integrated
the corrected code/tests: **128 passed/13 skipped in 4.80s**, manuscript
reconciliation PASS; shell syntax PASS. No real REF observation.
Current source `d763…a6e9`, tests `6713…5bd2`, protocol `9222…e0e8`, launcher
`3458…6331`, manifest `2158…a935` are frozen for exact review in the
[manifest](../../results/data_audits/svpg_2026/2026-10-08/reference_throughput_manifest.json).
This is one 41-test cluster controls process and then, conditionally, one
real reference process. The unchanged reference tests are not replayed in
that new cluster controls slot.

Local free space about 15 GiB, unchanged safety guard. Large work stays on
the cluster. Read-only cluster check at 18:18:46 +07: account queue empty;
scratch expires October 22 at 23:02:50 +07, one extension available. No
unrelated jobs, source sequences, genomic transfer, install or training used.
This advances preparation for the finite ALL-SIX development rejection test,
not a publication claim. The broader publication goal remains unachieved.

## Exact approval, then CPU-only scheduler addendum

The maintained reviewer accepts corrected code/runtime, the exact bundle
above, its 7-GiB account and 720-second CPU reserve. No slot was launched,
staged or booked under that direct-launch approval. Preserve its original
[manifest](../../results/data_audits/svpg_2026/2026-10-08/reference_throughput_manifest_direct_reviewed.json)
at the exact `2158…a935` hash.

Preflight at 18:41:19 +07: account queue empty, scratch still October 22;
fresh experiment root absent; prepared truth/reference/FAI/native report
stat as regular files at 11,853,747 /892,326,179 /2,813 /1,610 bytes.
No additional scientific-source hash was performed. Existing test deps exist.
Slurm lists `amd_256M` up. Use one CPU and 4096 MiB, 20-minute batch cap,
no GPU. The reviewed outer time/timeout/limits are unchanged inside a short
batch wrapper; it only verifies small frozen bundle pins before invoking
that recipe. Scheduler logs add a 16-KiB envelope within existing metadata.
An exclusive submission claim precedes sbatch; uncertain acknowledgment
forbids resubmission. Inner payload claims and both slots remain unchanged.
Outer waited CPU is charged once; sacct provides descriptive reconciliation,
not a second charge. Abnormal incomplete tree accounting retains reservation.

This scheduler wrapper and modified manifest require focused exact addendum
approval before booking or staging. The scientific inputs, source/protocol/
tests/launcher pins and caps are unchanged. No real REF read occurred here.

## Approved scheduler scope and booked reservation

The reviewer accepted manifest `24aa…3a0b` and batch wrapper `807b…837a`
for one CPU-only submission, without extra payload slots or scientific scope.
At 11:46:42 UTC main booked the full 7-GiB reservation in the separate
[ledger](../../results/data_audits/svpg_2026/2026-10-08/reference_throughput_reservation.json)
before creating the fresh experiment directory or staging the ten small files.
Full retained total is now **16,208,704,797 bytes**, no refund. The proposed
720-second named CPU reserve is still prospective, not a measured run.
Staging is in progress; neither complete controls nor a REF result is claimed.
The reviewed outer time scope excludes batch-wrapper prehash overhead and
Slurm allocation CPU; it is not total physical/job/project CPU. Sacct is a
descriptive reconciliation, not an additional copy of the same timing charge.

Staging completed; at 18:49:11 +07 all ten remote hashes match the exact
approved files and byte counts total 118,021. Neither `submitted` nor
`launched` existed at that check. No scientific-source rehash occurred.

One exclusive submission claim and one `sbatch` acknowledged job **1604025**.
At 18:53:12 +07, sacct records COMPLETED/exit 0:0, elapsed 1:48,
allocation TotalCPU 1:46.076; durable state ends COMPLETE. One controls
and one REF slot are consumed, no replay. TotalCPU is descriptive here,
not another charge on top of the pending outer waited-tree log inspection.
All 13 small outputs exist, totaling 12,383 bytes; output bundles fit the
reviewed caps. Raw report/log retrieval and independent result review are
pending. No caller, scoring or denominator claim follows job completion.

The complete [report and cost reconciliation](2026-10-08-reference-throughput-result.md)
now record 41 controls, zero skips, all 11,490 original anchored REF spans
matching, 86 complete contigs/EOFCRC, and outer106.04 CPU/108.72 wall.
All 13 files copied locally and five hashes match; independent raw review
pending. Retained bytes remain16,208,704,797; measured namedCPU532.662707,
inner/Slurm timings not added again. No denominator or caller result follows.

Independent raw-result review now accepts technical completion after reading
all 13 local files and verifying the five recorded hashes. Historical defects,
direct-route approval, scheduler addendum and consumed slots remain preserved.
No new caller, denominator, scoring or publication approval follows.
