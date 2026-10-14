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
