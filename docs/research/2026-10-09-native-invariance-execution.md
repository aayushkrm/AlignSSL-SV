# Native CIGAR diagnostic: exact launch candidate

2026-10-09. Status: **UNBOOKED, UNSTAGED, UNEXECUTED; REVIEW PENDING**.
This implements the selected synthetic diagnostic, not a paper campaign.
No real read/reference/callset data are inputs. Keep the old released-callset
STOP, historical failures and full retained charges.

## Source correction before outcomes

Main fetched and read FULL tagged `src/cli/discover.rs` through the connected
Firecrawl plugin. `DiscoverSettings` derives Serialize and is written directly
with serde_json: the saved fields are flat snake_case. The same file's data
validator always requires a match to `coverage_est_regex`, including when
CNV is disabled. The default numeric-chromosome regex does not match
chrSynthetic. All four arms therefore add the common input-validation option
`--cov-regex '^chrSynthetic$'`. This precedes any caller outcome; no read,
reference, allele, threshold or between-arm contrast changes.
[Pinned author source](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/discover.rs).

The new settings validator checks the actual resolved reporting minimum35,
noise margin10 or30, ordinary MAPQ/identity/QUAL values, disabled CNV, no fast
mode, no cluster target or external annotation input, the common regex, and
exact BAM/reference/output paths. Every other serialized setting must agree
across all arms. It does not infer defaults from a successful version query.

## Immutable execution identity

ID/root: `native-cigar-invariance-20261009-01` under
`/scratch/igorno-alignssl_restart_20260922/`.
One fresh root, one submission claim before sbatch, one timed payload claim,
one exact-stack control suite, at most four discover and four joint-call
commands. Each command writes an exclusive argv claim and log before starting.
Unknown acknowledgement consumes the submission claim; inspect that job/root
rather than submit again. No retries, threshold sweeps or selective arm replay.

The fixed Python is `/home/igorno/miniconda3/envs/truvari_env/bin/python`:
3.10.20, pysam0.24.0, HTSlib1.23.1, pytest8.4.2 from the retained test-deps
path. Require all70 controls to pass with no skip. The new integrity sidecar
tests corrupt/truncated BGZF/BAM, a malformed VCF tail and missing/wrong GT.
Main's local70 tests pass0skip0.79s; that is not exact-stack verification.

The timed payload runs controls, creates the frozen fixture, downloads only
the pinned Sawfish v2.2.1 asset, checks actual stored bytes/digest, safely
extracts only its executable, verifies its measured version and records the
binary hash. No system/conda environment or old artifact is overwritten.
The archive is capped at4MiB/64 members/16MiB expanded, with no absolute,
parent-traversal, link or special member. Native executable compatibility is
an explicit runtime gate, not already established evidence.

Full miniature reference; one CPU; four arms in the frozen order. Every arm
checks settings, complete output parse, immutable fixture before/after, and
the observation STATES. Individually unresolved-record count can be zero
while joint edits are UNRESOLVED. Canonical exact+PASS+heterozygous failure
stops remaining arms. REF-only requires resolved absence in candidate AND
final outputs. Known exact positives remain visible alongside other unknowns.
Missing required files or unresolved endpoint stops incomplete, not negative.

## Containment and complete proposed allowance

Outer taskset binds the complete child tree to one allowed CPU. GNU time
measures that waited tree once; do not add inner or Slurm CPU again. Outer
timeout480s with5s kill grace; per-command subprocess timeout120s; inherited
CPU soft300/hard450 seconds per process, address-space4GiB. Slurm requests
one task/CPU,4GiB and9 minutes on amd_256M. No GPU. Directories/claims/logs
are exclusive. Native file limit1MiB and per-arm output-tree postchecks1MiB
with64 files; successful command logs capped64KiB, fixture launch cap64KiB.
Tests intentionally make links, so the
bounded32MiB control-tree check counts without following those test links.
Native outputs never permit links.

This is a **named conservative allowance**, not measurement or proof of
physical/opaque total I/O. Native tree checks occur after each command and
do not prevent transient aggregate growth during that command. Per-file,
time, CPU and memory controls remain active; a failed tree check stops use
and keeps the full charge. No unsupported physical-I/O bound is claimed.

| Named component, including failed paths | MiB |
|---|---:|
| Asset transfer, stored hash, bounded archive/executable materialization and verification | 64 |
| Code staging/checks, exact-stack controls and generated test artifacts | 32 |
| Eight native-command opaque allowance; not measured engine I/O | 96 |
| Frozen fixture passes, bounded native output writes, original reads, parser materialization/reads and posthashes | 24 |
| Raw outputs/logs/metadata source hashes, local transfer and local hash verification | 24 |
| Failure/metadata/timing margin | 16 |
| Total retained on booking, no refund | **256** |

Native per-arm output cap1MiB implies at most4MiB across completed arms;
five explicit output passes total at most20MiB, with4MiB for fixture/settings
and code checks. Fixture cap64KiB bounds repeated fixture passes within that
margin. The32MiB control-tree cap includes the existing approximately24MiB
oversize-input unit fixtures. Selected raw archive is capped at8MiB aggregate;
source hash, transfer and destination hash fit24MiB. Runtime libraries,
buffering, decompression and native passes are not measured physical I/O;
their allowance must not be described as an observed total.

Book268,435,456 bytes BEFORE staging: prior40,235,307,915 becomes
40,503,743,371 under68,719,476,736. Retain the full byte charge even on setup
or positive-control failure. CPU600 seconds covers this timed tree plus
bounded metadata/collection; prior556.722707, prospective1,156.722707 under
7,200. Only actual measured outer CPU is added after completion. Preserve
every earlier charge; do not transfer the old unbooked screen margin.

## Exact submission and archive boundary

Create root only after reviewer accepts the complete candidate and ledger is
booked locally. Stage exact analysis/test files and the two scripts under
`code/analysis`, `code/tests`, and root. Freeze `bundle.sha256` and its measured
hash; verify the same pins remotely before submission. No scientific source
body is copied. Author asset acquisition occurs only inside the timed payload.

Literal submission shape, with the measured bundle hash inserted only after
pinning (the placeholder is not a ready submission command):

```sh
set -C
printf 'native-cigar-invariance-20261009-01 <bundle-sha256>\n' > /scratch/igorno-alignssl_restart_20260922/native-cigar-invariance-20261009-01/submission.claim
sbatch --parsable --partition=amd_256M --ntasks=1 --cpus-per-task=1 --mem=4096M --time=00:09:00 --job-name=alignssl-native-cigar01 --output=/scratch/igorno-alignssl_restart_20260922/native-cigar-invariance-20261009-01/slurm.stdout.log --error=/scratch/igorno-alignssl_restart_20260922/native-cigar-invariance-20261009-01/slurm.stderr.log /scratch/igorno-alignssl_restart_20260922/native-cigar-invariance-20261009-01/run_outer.sh <bundle-sha256>
```

Check timestamped live account jobs first; never cancel unrelated jobs.
Collect only this root's named command/log/result files and all native arm
outputs, after regular-file/type/size checks. Preserve raw incomplete arms
as well as successful ones. Do not archive asset, binary or control fixtures
as scientific results. Archive hash manifest and every selected output must
agree locally/remotely. Review actual raw results before any scientific
conclusion; no BED/candidate absence is a complete seed trace.

Preflight09:40:44+07: account queue empty; root absent; scratch expiry remains
Oct22/one extension. This is metadata, not a continuing state guarantee.
At09:52:20+07 a metadata-only import confirms the stated cluster versions,
taskset and GNU time. The initial draft had incorrectly copied local
pytest9.1.1 into the cluster version assertion; corrected to observed8.4.2
before staging/outcomes. No dependency upgrade or environment mutation.
No reservation, staging, asset download, version execution or native outcome
has occurred at this candidate-writing stage.
