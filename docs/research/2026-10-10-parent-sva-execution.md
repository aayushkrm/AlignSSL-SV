# Parental SVA diagnostic: execution record

Science and endpoints remain frozen in the [protocol](2026-10-10-parent-sva-diagnostic-protocol.md).
The [independent review](2026-10-10-public-paired-falsifier-review.md) applies.

## Attempt 01: failed before Python

Source commit: `07dc731e8d8c8689d93e271a6a36a3af4f7a33e6`.
Slurm job `1604234` failed on hydra-n1 after one second, exit `0:53`
(signal 53). No stdout/stderr file or run directory was created. No Python,
BAI, regional acquisition, census or caller result ran. This is an execution
failure, not a scientific null. Slurm reports zero measured CPU; this does
not mean that no resources were requested or allocated. No historical result
was changed or job cancelled by the agent.

Raw accounting returned after the job left the live controller:

```text
slurm_load_jobs error: Invalid job id specified
1604234|FAILED|00:00:01|00:00:00||0:53
1604234.batch|CANCELLED|00:00:01|00:00:00||0:53
1604235|COMPLETED|00:00:02|00:00.864||0:0
1604235.0|COMPLETED|00:00:01|00:00.864|4784K|0:0
```

The columns after JobID are State, Elapsed, TotalCPU, MaxRSS and ExitCode.
Job `1604235` was a two-second read-only `srun` preflight on the same node.
Both the `/home` alias and physical BeeGFS bundle path were accessible. Base
and isolated-venv Python both ran as CPython 3.12.1. Thus the `/home` alias
is not shown to be absent. Pre-task batch I/O is suspected, but the root
cause is not established.

## Replacement 02: ran once, acquisition incomplete

Use direct `srun` with streamed stdout, avoiding the failed batch-file I/O
route. Use verified physical bundle, runtime and scratch paths. The exact
scratch base is `/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922`.
An alternative Slurm script is retained, but is not itself a submitted job.
The runner now records `SLURM_JOB_ID`; no scientific parameter changed.
The original 01 runner snapshot is restored from its source commit.

The allocation stays three useful CPUs, 4 GiB RAM and ten minutes. Once
acquisition completes, the two native policies and census run in parallel.
No GPU or whole idle node is needed. The 4-GiB genomic HTTP-body read limit
includes the prior 65,536-byte header prefix conservatively; fresh bytes are
reported separately. No whole-BAM fallback or caller tuning is authorized.

Acquisition worker completed and closed. Main corrected HTS open-ended range
handling and added a loopback control before any genomic attempt. The full
local check returned 33 passed plus six subtests, zero skips, in 4.47 seconds;
the exact deployed acquisition snapshot passed seven cluster controls.
These are software checks, not genomic evidence.

Direct-srun job `1604236` reached the public source and verified both frozen
HEAD checks and the full BAI. Its regional extraction failed before target
reads or native calls could be assessed:

```text
[E::test_and_fetch] Failed to create file NA12878.CHM13.haplotagged.bam.bai in the working directory
[main_samview] random alignment retrieval only works for indexed BAM or CRAM files.
1604236|FAILED|00:00:27|00:01.599||1:0
1604236.0|FAILED|00:00:26|00:01.599|39440K|1:0
```

The runner reports 25.964383 seconds wall time and 1.592349 CPU seconds.
The measured fresh HTTP-body read is **39,159,756 bytes**. With the earlier
65,536-byte prefix, the cumulative charge is **39,225,292 bytes**. Index
bytes are 37,783,472, SHA256
`14ee0700cf338cfde7e201b70ec0f285942677dffc32b805aa2080f2301795ff`.
Loopback index bytes are reported separately, not added as new upstream reads.
The 4,650-byte partial regional BAM is not a qualified read packet. Do not
score it, run callers on it, or interpret it as biological absence.

All partial data and complete manifests/journal/logs remain in scratch and
are copied to the project's non-expiring home experiment tree under
`experiments/parent_sva_native_20261010_02/raw-archive`.
No file in 02 is repaired or replaced. Original source snapshots remain.

## Replacement 03: narrow cache-directory correction

Samtools 1.9 caches a remote index in its working directory. Set each samtools
subprocess's working directory to its new acquisition output directory, where
the run already writes its outputs. The scientific window, two native modes,
census and acceptance predicates are unchanged. This directly addresses the
observed cache-creation error; it does not claim to diagnose the earlier
Slurm pre-task signal.

Pass prior-body charge **39,225,292** to the new acquisition. The same global
4-GiB cap is retained, not reset on retry. New manifests distinguish prior
body bytes from the original prefix. The correction and prior-budget controls
pass: 27 tests plus nine subtests, zero skips, in 0.71 seconds with the project
venv. Two mistaken local verification invocations are retained in this record:
system-Python unittest lacked pytest; a subsequent pytest command named a
nonexistent docs test. Neither ran a genomic experiment. The corrected command
uses existing `.venv` and the actual two README test files; no fixture changed.

Goal remains active and unmet. Next: run 03 once, retain partial artifacts on
failure, then interpret complete evidence only. No whole-BAM fallback.

## Replacement 03: completed once

Job1604237 completed, exit0:0. Acquisition, both native calls and census all
exited0; complete result, resources, limitations and custody are in the
[result note](2026-10-10-parent-sva-result.md). This supersedes the prospective
03 next step above. No additional replay or scientific parameter change.
