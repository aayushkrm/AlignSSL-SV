# Matched GENCODE50 input staging

Routine S0 preparation, independently released in the
[staged investment review](2026-10-10-public-paired-falsifier-review.md#hg002-concrete-s0s1-investment-review).
This is not a donor-genome experiment, annotation result or P1 assessment.
Main prepares references while the existing S1a transfer runs; no duplicate
HG002 intake. RNA remains untouched.

Five exact comprehensive primary-assembly products and published MD5s are
fixed in the [source recipe](2026-10-10-hg002-dna-input-recipe.md).
Expected compressed bytes1,152,186,383. The
[stager](../../scripts/stage_hg002_gencode.py) reuses the corrected, reviewed
transfer loop with deferred cancellation,1MiB counted reads, exclusive
publication and a **separate reference ledger**, prior0, cap2GiB. Live HEAD
must match fixed size/identity encoding; its ETag pins each full206 download.
Whole SHA256 and the fixed published MD5 must pass for every object. A legal
complete transfer with a checksum mismatch remains INCOMPLETE. No native
mapping, decompression, donor alignment, annotation or allele classification.

No automatic retries or reference substitution. Source/data-pin drift stops;
partial and failed outputs stay. Count returned bytes before writing, including
exception partials. Signal handlers defer exceptions to safe points; the
network timeout bounds inactivity, not absolute read duration. Slurm provides
the hard allocation stop. S1 genomic bytes/CPU do not pay for this S0 stage.

One CPU/4GiB/65min direct srun on hydra-n1/amd_256M; script deadline60min.
This can use about1.1allocatedCPUh of S0's4h, with prior setup/control attempts
also charged. Require32GiB free. Compressed raw in scratch plus matching home
custody is about2.3decimalGB; expanded reference/annotation is a later step,
not assumed free storage. Keep total S0 peak within32GiB and summed live
allocations within the staged global limits. No idle whole node or GPU.

S0 prior pip transfers were not byte-metered. Logs report one191.3MB source
archive and a119,817,989B apparent wheelhouse, plus small test dependencies.
For planning reserve1GiB for existing software; this is conservative bookkeeping,
**not** an exact observed transfer or formally metered bound. The independent
2GiB reference body cap and that reservation fit within S0's4GiB ceiling.
Do not claim an exact combined software/reference body total.

Immutable bundle:
`/beegfs/datasets/home/igorno/alignssl_restart_20260922/bundles/hg002_gencode_s0_20261010_01`.
Exclusive writable output:
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/hg002_gencode_s0_20261010_01`.
Module command: `python -m scripts.stage_hg002_gencode --output` with that
exact output path. Back up all raw/manifests through writable login I/O to
non-expiring home and verify hashes; scratch expiresOctober22.

| Frozen file | SHA256 |
|---|---|
| stage_hg002_gencode.py | `e104b7506f674e78248335328b4b6d9b352d74630b44e94e6953c5d01cb096ed` |
| test_stage_hg002_gencode.py | `ca46eb4c9de45f275a27703af8169b2f61b7efc9f88c0f996ad2e62ac39b20ce` |
| reused acquire_hg002_dna.py | `57524ec840fdd08a9cd25505e230fbe1063ae0e4ade70f2f9dbba77f237aef35` |
| unchanged acquire_parent_sva_region.py | `c0f47e522d4f88b2e068f035b78eb558e63e4abc94839b4a78e32f3c6f09034b` |

Seven local mocked controls pass, zero skips,0.10s. Current combined selection
of stage, DNA intake, cohort, parental acquisition/census/acceptance tests
passes90tests plus9subtests, zero skips,0.98s. Tests cover independent prior0, hashes,
published mismatch, low space, HEAD size/encoding, cancellation-accounting and
existing-output refusal. These mocks do not attest remote206 support, real
checksums or native annotation compatibility.

Linux control job1604254 completed0:0,1s elapsed/0.487s measured CPU;
its direct terminal output was lost across a context transition. This was not
a data-acquisition attempt. One explicit output-recovery verification1604255
also completed: all four deployed source/test hashes above match,39 controls
pass, zero skips,0.25s. Both allocations count against S0; neither downloaded
genomic/reference bodies.1604255 also used1s elapsed/0.483s measuredCPU,
MaxRSS16552K. The default macOS system Python lacked pytest;
use the existing project venv, not a new installation.

## Actual launch

Job1604257 is RUNNING on hydra-n1/amd_256M with the fixed1CPU/4GiB/65min
allocation and immutable source bundle above, corresponding to research
commit9f80613. It started after the deployed controls and separate new-leaf
check. This books at most65allocatedCPUmin within S0, not an additional free
allowance. It is concurrent with, not a replacement for, S1a1604251.
No complete reference object, successful checksum or native run is yet
claimed by this launch record.

Later:1604257 completes0:0 with all five MD5s passing; complete journal and
home custody are checked. See [actual intake result](2026-10-10-hg002-intake-result.md).
Earlier preparation/live entries remain historical snapshots, not current status.
