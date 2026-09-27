# Reassessment of the Manta engineering-fixture signal 53 failures

**Date:** 2026-09-24. **Status:** cause unresolved; no caller result.

Jobs `1598015` and `1598016` were marked `FAILED|0:53` after four seconds on
different nodes, with their `.batch` steps marked `CANCELLED|0:53`. A separate
GIAB staging job, `1598013`, received the same signal on `hydra-n12` seven
minutes before `1598015`. Later project jobs completed on both affected nodes:
reference-map job `1598070` on `hydra-n12`, and frozen-map job `1598267` on
`hydra-n1`. The raw [read-only accounting and configuration recheck](../../results/cluster_jobs/2026-09-24-manta-signal53-recheck.txt)
records these states and timestamps.

The accounting records signal termination of the batch step, but do **not**
prove whether the script began or who or what sent the signal.
`sacct` gives no explanatory reason, the expected output files were absent,
and no Manta candidate directory or VCF was found in the scoped scratch
inspection. Current SLURM configuration reports `Prolog=(null)` and
`PrologSlurmctld=(null)`, so a configured SLURM prolog is not supported as the
cause. These checks do not exclude a transient node-side service, SLURM step
startup, application-side signal, or another sender. The earlier descriptions
"failed before startup" and "scheduler signal" were too strong.

No third identical Manta submission is justified. If a caller run becomes
scientifically necessary, first request the node `slurmd`/`slurmstepd` and
controller events for the recorded start times, or use a revised, explicitly
instrumented minimal batch diagnostic with a fresh output path. In parallel,
look for existing matched candidate VCFs that can answer the cheap
candidate-recall question without relying on this fixture. The 3-Mb HG002
slice remains development-only even if Manta eventually runs.
