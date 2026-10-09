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

## Replacement 02: prepared, not yet submitted

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

Goal remains active and unmet. Next: run the bounded replacement, retain all
partial artifacts on failure, then interpret complete evidence only.
