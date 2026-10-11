# Final distinct standard-tool feasibility decision

Date: October 7, 2026. Current status: the one independently reviewed
standard transport/compatibility attempt completed successfully. Checkpoint `d11f04a` is pushed; the remote
branch SHA was verified. The scientific goal is active and unachieved.

## Decision and firm limit

Faraday, requested Sol6.1/max, chooses one finite standard-tool alternative
over immediate abandonment. Main accepts the direction subject to Dirac's
independent code/protocol/reservation review. This is an explicit new decision
after stage-04 failed, not a retroactive approval or fifth custom-stager pass.
The previous custom route stays closed. Its failure and all charges stay in
the record. No earlier size/parser limit is changed.

The two unfinished ZIP members total 30,307,146 bytes. Transport them exactly
with standard `zipfile`, full member EOF/CRC and raw SHA-256 checks. Reuse the
four completed files instead of decoding their archived members again. One
standard HTSlib text-parser pass checks **all six** files and verifies their
SHA values. A length-bounded pipe feeds the parser, so file growth cannot
extend a genomic read beyond its reservation. No record is rewritten, filtered,
clamped, shifted, sorted, split or compared to truth. A raw newline census for
the two new files and the existing record counts for the four completed files
must agree with standard-parser counts. An unsupported count stops this route;
do not discard a troublesome row.

| Charge | Reserved bytes |
|---|---:|
| Historical source charge | 4,094,310,110 |
| Two-member transport, including two one-byte EOF probes | 30,307,148 |
| New cumulative source charge | 4,124,617,258 |
| Unchanged source ceiling | 4,294,967,296 |
| Historical aggregate charge | 4,153,131,060 |
| All-six compatibility/SHA pass | 1,036,400,535 |
| New cumulative aggregate charge | 5,219,838,743 |
| Unchanged aggregate engineering ceiling | 12,884,901,888 |

Keep complete reservations even on failure; no historical refund. The two EOF
probe allowances add two bytes to the decision agent's transport-only total,
not to the unchanged ceilings. No separate hash pass rereads the four completed
genomic files. Full compressed archive verification is recorded separately;
it is not silently relabelled as decoded source traffic.

**Limit: 15 minutes wall time and ten combined CPU-minutes** for this one
transport/compatibility attempt. The existing supervisor retains its sampled
three-GiB RSS stop and own-process-group control. A 550-second child CPU limit
is a hard child limit. The new launcher also
samples live child CPU plus launcher and completed-helper CPU, stopping at
580 seconds to keep sampling/cleanup headroom below 600. Check final measured
combined CPU too. This is not a hard combined-process CPU/RAM guarantee;
the runtime sampler fails closed if owned child CPU cannot be read.
Fresh output/log directories, ten-GiB free-space headroom and immutable reports
are required. Never stop unrelated jobs or overwrite previous partials.

**Failure, or a need for further bespoke infrastructure, ends this dataset
route and triggers a research pivot.** Success must move directly to the fixed
six-caller diagnostic in the next working day, after the already identified
preparation controls pass review and within the remaining resource budget.
It is not permission for another open-ended source/provenance campaign.

## Tool and scientific scope

The local installed parser is pysam **0.24.1**, reporting bundled samtools
**1.24**. This differs from the cluster control audit's pysam **0.24.0** and
bundled bcftools/HTSlib **1.23.1**. The local compatibility finding cannot be
claimed for the cluster installation without checking it. Do not upgrade a
historical environment in place or silently change scientific tool versions.
Freeze the eventual preparation/scoring environment in its separate review.

The implementation calls standard ZIP and HTSlib readers. It imports only
the frozen caller selection, repository location and snapshot helper from the
old stager; it never calls that stager's custom VCF validator. The bounded
feeder is an I/O guard, not another biological parser or coordinate repair.

No truth preparation, scientific sorting/decomposition, matching, refinement,
union coverage, residual adjudication, training or superiority claim is
approved by this stage. Shared header dictionaries/path strings still do not
prove equal raw reads, depth, run, reference-base or graph identity. The
released-callset development estimand remains the limit; HG002 is not an
untouched test donor. Publication significance and a recoverable residual
mechanism remain unproven.

Frozen protocol and reservation are append-only under
`results/data_audits/svpg_2026/2026-10-07/standard_transport_*.json`.
Internal independent review is Sol6.1/high requested; the synthetic-test worker
is Luna/max requested. Actual runtime model configurations are not independently
attested. No new sidebar chat was created.

## Final synthetic safeguards submitted for review

The Luna/max-requested test worker supplied the initial synthetic tests, then
reported model capacity failure. Main closed it and finished the required
mutation/digest/read-failure and CPU-guard cases, without changing worker model
or creating a sidebar chat. Main read the entire supplied test file first.
The integrated transport and existing resource-guard target passed **29 tests
in 0.94 seconds**. These are synthetic cases, not source feasibility evidence.
The full suite is running; do not infer its final count before completion.

Pins submitted to Dirac:

| Artifact | SHA-256 |
|---|---|
| `analysis/transport_svpg_standard.py` | `68f1072d3972f54681c274c476fc787888ef8064e53128a3ff9f46ae4276a202` |
| `scripts/run_svpg_standard_bounded.py` | `b55ea2d2609c2f6341a02568b552e7698b1e7be9aced2d94fe6c855cc516d58a` |
| `tests/test_transport_svpg_standard.py` | `f97bd1e307e1020124c2391d37690f1a240ed194f3454135cf946621fc39ea7c` |
| `standard_transport_protocol.json` | `6c39249b38d990304251f19b16f14c5a632b123443f38d4426990542a2a0a472` |
| `standard_transport_reservation.json` | `700b340a27bc374b11db7135f8607349675723fafe8223ce970d5996427c7662` |

Both pysam and bundled samtools version are checked before archive access.
The combined-CPU sampler rejects malformed CPU values and stops at 580
seconds. If the owned child exits during `ps`, missing CPU time returns zero
RSS to the existing supervisor: a still-live child fails closed, while an
exited child is reaped for the final measured CPU check. This avoids declaring
a successfully exited child a parser failure due only to the sampling race.
The old supervisor file and the closed custom stager are unchanged.

No new genomic read has run at this entry. Fresh output/log paths were checked
absent; current free space is approximately eleven GiB. Recheck at execution.

### Review correction: inherited CPU hard limit

Dirac withheld approval of launcher `b55ea2d...`: it lowered the parent's hard
CPU limit to 50 seconds before a child tried to set 550 seconds. A child
cannot raise its inherited hard limit. Mocked resource tests did not catch
this real launch defect. No genomic source was run with that launcher.

Main removed the parent limit; the child retains its own hard 550-second limit,
and parent/helper CPU is still counted in the runtime combined sampler and
final check. A new **actual** synthetic child-launch regression uses the real
supervisor and OS limits, asserts `(550, 550)` in the child and exits normally.
The corrected integrated target passed **30 tests in 1.53 seconds**.
Launcher pin is now `4e406d7a54fb704accf1747f3fc53d7b8945a6c1167400731bf40994b10baab5`;
test pin is `f2ab3a30d709f3a3586fbd8748b91ceb48d10f939a2e97e681387059325de77f`.
Transport code, protocol and reservation pins remain unchanged. These final
pins are submitted for independent approval; no approval is inferred here.

The earlier full run completed **641 passed, 29 skipped in 124.08 seconds**.
It did not collect the subsequently added actual-child test. Its separate
passing target is reported above; a final all-inclusive run is required.

## Final independent stage-only approval

Dirac reviewed the corrected transport `68f1072d...`, launcher `4e406d7a...`,
unchanged protocol `6c39249b...` and reservation `700b340a...`, plus the real
child-launch regression. It approved **one** byte-preserving SVIM/SVPG
transport and one bounded SHA-verifying local HTSlib compatibility pass over
all six callers. Main supplied the 30-test result; the pending full suite is
not claimed complete. Use fresh output/log paths and immediate disk preflight.
Keep child CPU=550, sampled combined stop=580, final combined ceiling=600,
wall=900 and existing memory/disk guards. Keep full source 4,124,617,258-byte
and aggregate 5,219,838,743-byte charges on failure. Any failure ends this
dataset route, without retry, repair or caller omission. Approval is local
pysam 0.24.1 / bundled samtools 1.24 only. All scientific execution stays closed.

## Actual standard-01 result

The approved attempt completed. Full-member CRC and raw SHA checks passed for
SVIM and SVPG. The four previous derivatives were reused, not decoded from
ZIP again. Standard parser counts match all source censuses; no coordinate,
GT, record or header repair was performed. The original archive and all
failed-stage partials/logs remain outside Git.

| Caller | Parsed original records | POS=0 | POS=contig length+1 |
|---|---:|---:|---:|
| cuteSV | 51,561 | 0 | 13 |
| DeBreak | 26,421 | 0 | 1 |
| Sawfish | 43,944 | 0 | 0 |
| Sniffles | 32,567 | 0 | 0 |
| SVIM | 49,512 | 41 | 0 |
| SVPG | 31,720 | 0 | 0 |

The SVIM file now demonstrably contains 41 position-zero records. The exact
position at the previous validator's failure was not retained; this aggregate
does not establish that row's value. Do not call legal sentinels malformed,
shift them to position one or treat parser acceptance as scientific eligibility.
The emitted `AF should be declared as Number=A` warning remains in the external
stderr log. No header was changed to suppress it. Allele-dependent INFO and
boundary records need explicit handling in the known preparation review.

| New raw member | SHA-256 |
|---|---|
| SVIM | `efb823e8d4022290279400ff632a529d4adcc4c7081479fe2a76456e736f81ce` |
| SVPG | `8a50b1213be4878801f2466b907f5357e1e5bcc9478053a3e75b7d176f916b7f` |

Combined CPU: **29.154969 seconds**; wall: **26.181658 seconds**. Child rusage
peak RSS: **197,115,904 bytes**; sampled peak: **186,675,200 bytes**. No CPU,
memory, disk or wall guard tripped. Full conservative source **4,124,617,258**
and aggregate **5,219,838,743** byte charges remain; two unused EOF-probe
allowances are not refunded. Small immutable report, resource and CPU-guard
JSONs are copied into the dated audit directory. They contain metadata and
counts, not raw alleles/read names. No data or useful partial was removed.

Final full suite: **642 passed, 29 skipped in 129.66 seconds**, including the
actual child-limit regression. This supersedes the earlier 641-case run without
rewriting its recorded count. The source/compatibility gate is complete; the
scientific experiment is not. No truth unit census, coverage comparison,
residual, refinement, training result or publication contribution is claimed.
Proceed directly to the already specified preparation controls and reviewed
fixed diagnostic by the next working day; do not resume source-wrapper work.
