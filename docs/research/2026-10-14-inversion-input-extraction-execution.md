# Fixed inversion input extraction execution

14 October 2026, Asia/Tomsk. One bounded read-only input diagnostic, not a
caller run or proof of inversion support. Full publication goal remains unmet.

The preceding goal pass was interrupted at a failed multi-file patch. No case
run or successful correction occurred then. Main reapplies the two corrections
on October14:9MiB JSONL plus1MiB metadata (total10MiB), and explicit UNKNOWN
for stored query/CIGAR length disagreement. Original14offline controls pass
again in0.26s. No earlier actual-case outcome exists to overwrite.

The old maintained reviewer and code-worker handles now return not_found;
their completed code/reviews remain evidence. New maintained Sol6.1/high-
requested reviewer Avicenna independently reviews the extractor, full tests,
protocol and preceding scientific result. Its six in-memory check groups pass;
it accepts one bounded extraction after a real-library synthetic fixture passes.
Configurations are requests, not independent backend attestation.

Main's actual local native pysam0.24.1 fixture passes:3synthetic records,
known forward/reverse hashes,70'=' base comparisons/0conflicts, duplicate
QNAME retention, MAPQ0, omitted kinetic arrays, exclusive output and missing-
index refusal. No study BAM is opened by that fixture. This verifies the native
interface, not scientific allele truth. A separate fresh four-record fixture
also passes at `runs/inv-native-fixture-v2-20261014.twdiRO`, adding a hard-clipped
alignment with absent SEQ/QUAL. The final four-record fixture runs first on the
compute node; only then can the actual input be opened. The earlier three-record
control remains preserved at `runs/inv-native-fixture-20261014.YEMX5x`.

## Exact frozen packet

The [hash list](../../results/inv_mapped_trace_20261014/SHA256SUMS) binds:
extractor27287805842e46ad3651f2e222d6ec85737bc9104fa43e126704c24123b336ef,
fixture2627c848b4b6b91eb8aa86bab5a1c13efb43e8ed6a09a78fbfd786867f2f5649,
launcher92216086a83a4696e47e81e1f2dad430a834badf3f556ee56e9b79e468372fc8,
and unchanged regional reference JSONd28acc720fd15ca939a1e9f5d885ed3da0970ff4edbfdf93bea081ed71036656.

Permanent new output leaf:
`/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/inv_mapped_trace_20261014_01`.
Existing whole BAM/BAI stay untouched in hg002_dna_s1a_20261010_01. Fresh
sizes48,727,325,910B/21,582,928B agree with accepted custody. No whole-file
hash is newly recomputed. This is a separate CCS/Revio study track, not a
reproduction of the benchmark20-result input. HP/PS remain observed tags only.

Resources:1node/1task/1CPU,1GiB RAM,15min, noGPU, amd_256M/hydra-n1.
One serial indexed fetch uses these resources; no idle whole-node reservation.
Inner fixture timeout90s, extraction timeout140s plus10s termination grace;
extractor also observes its120s soft processing cap. A blocked native call
cannot claim completion. Region chr2[240675000,240704000), at most1000records,
no MAPQ/flag/genotype filtering. At a cap or error, preserve partials as
incomplete/failed; never infer absence. Native source index creation is disabled;
only the four-record synthetic fixture gets a new tiny index.

Fresh own queue is empty. Scratch reports8days0hours and one unused extension;
all accepted source data and this diagnostic output are on permanent HOME.
No obsolete project job is found or cancelled. No other user's jobs are touched.
Job identity/status must be recorded after actual submission; preparation here
is not evidence that it ran. Raw sequence/quality JSONL stays outside Git.

## First launch failure and separate execution correction

Frozen source commit `e4bfe5b1b98b34984f1c3cddb407ce8bca8a773a` was pushed
before source access. Batch job1604869 FAILED0:53 at22:25:35 local time,
reported elapsed00:00:00 and measuredCPU00:00:00; its batch step CANCELLED0:53.
No stdout/stderr, execution, fixture or case file exists. No case alignment
body was read. This is pre-task failure, not a scientific null or zero
allocation claim. Signal cause is unproved. The first bundle remains unchanged.
An initial accounting query also rejected unsupported `StdOut`/`StdErr`
fields; the corrected query and controller state establish the outcome.

Previous October10 records already show the same pre-task batch signal,
successful direct `srun` recovery and read-only compute HOME. The original
01 output path incorrectly reused HOME despite that known restriction.
Separate02 uses writable physical scratch for every new output and direct
`srun`, while retaining the exact extractor, fixture, reference, source BAM/BAI,
limits and endpoints. This addresses execution paths, not a proven cause of
signal53. [02 hashes](../../results/inv_mapped_trace_20261014/SHA256SUMS-02)
freeze launcher `d71dbaaf4acee6ae069b6c3297fdbd3ee766e42e1de30fa4f9fd0c3164182a47`.

New exclusive output:
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/inv_mapped_trace_20261014_02`.
One direct allocation, unchanged1CPU/1GiB/15min on hydra-n1/amd_256M, noGPU.
Main will preserve all outputs, even failures, in a separate non-expiring HOME
leaf through writable login I/O and verify the copies before October22.
No automatic retry, case repair, scientific parameter change or old-result
overwrite is allowed. Both attempts stay in resource accounting.

## Actual02 completion and custody

Direct job1604870 COMPLETED0:0. Execution15:28:10–15:28:11UTC on hydra-n1;
Slurm allocation elapsed2s, step1s, measuredCPU0.907s, MaxRSS17424K.
AllocatedCPU×elapsed is2CPU-s (plus01 reported0s; not zero setup overhead).
The extractor reports0.608538806438446s. No GPU or idle whole node allocated.
Both failure and replacement remain in accounting, not just the success.

The four-record native fixture PASS precedes the case. The actual case is
COMPLETE with regionEOFtrue,52records/47QNAMElabels, no decoder/finalization
failure. JSONL4,527,955B plus manifest462,702B =4,990,657B, below10MiB.
JSONL SHA256 `ca77cd139dcb8344cf0697dc7468e97db35344c3d10dfdb42d28eedcbd43df18`;
manifest `80f29373616a355ce4c2b23dbba49ade7796ac28a094032c4598b65f508aae3a`;
native receipt `e905bbd688d4084e475998c4f4da4aff3a2469223a7502af4764d80eb854c2b9`.
Historical BAM/BAI hashes remain historical; no whole48GB reread occurred.

Main copies the entire02 leaf through login into permanent HOME
`experiments/inv_mapped_trace_20261014_02` without changing scratch output.
Both bundle/output SHA checks pass there; recursive byte comparison of HOME
and scratch reports no differences. The complete leaf is also retained outside
Git locally at `runs/inv-mapped-trace-20261014-02.SEsMRo/inv_mapped_trace_20261014_02`.
It includes full sequences/qualities and all synthetic controls, not merely a
selected read screenshot. No sole copy depends on October22 scratch expiry.

Main initially attempted to inspect the local manifest before SCP completed:
FileNotFoundError, then waited for the same transfer; no case rerun. A first
ad-hoc tag print assumed tuple tags and raised KeyError0; actual schema is
name/type/value objects. Corrected read-only inspection uses that schema and
does not mutate rows. These inspection errors are not genomic failures.

Actual interpretation and maintained independent review follow separately;
completion alone accepts no inversion, genotype, mechanism or publication claim.
