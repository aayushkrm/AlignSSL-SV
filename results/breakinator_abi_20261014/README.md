# Breakinator native ABI: actual synthetic controls

Job1604874 **COMPLETED0:0**. All four synthetic groups pass the native interface
expectations: contiguous reference (no report row), central Foldback, noncentral
Pass and cross-chromosome Chimeric. These are geometry controls, not biological
artifact truth or a real-input study.

The [run manifest](run.json), [raw report](native-report.tsv),
[native stdout](native-stdout.txt), [execution](execution.txt) and
[exit receipt](exit-status.txt) are unchanged small copies. Full output,
including the synthetic BAM and empty stderr, stays outside Git in permanent
cluster HOME `experiments/breakinator_abi_20261014_01` and the local
`runs/tier2-geometry-screen-20261014.PCdiR9/breakinator_abi_20261014_01` leaf.
Scratch/HOME copies compare byte-for-byte. The software asset separately matches
the publisher SHA; the native executable is bound by its own hash.

Allocation:1CPU/512MiB/1s elapsed; measuredCPU0.294s, MaxRSS22088K. No GPU or
study BAM access. See [execution and exact pins](../../docs/research/2026-10-14-breakinator-runtime-execution.md).
The prospective Tier2 input screen remains a separate, unexecuted experiment.
