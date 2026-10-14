# Native Breakinator interface qualification

14 October 2026. Small software/setup check, separate from the prospective
Tier 2 real-input screen. No study alignment body is accessed by this job.
The publication goal remains active and unmet.

## Author artifact and actual acquisition

The official release API reports v1.1.1, published10November2025. The Linux
musl tarball is3,547,379B and its publisher SHA256 is
`00747b208e25887eac9e61db57496085d2a593cb6899e1b2940ca9ab1c9c2310`.
The first laptop curl attempt times out at the fixed90s limit, exit28, with
111,117B retained at `runs/tier2-geometry-screen-20261014.PCdiR9/`.
An early in-flight hash/list probe saw an empty output buffer; it is not
evidence of completion or the final partial's checksum. No file was replaced.

Alternative cluster-side transfer completes once. Exact size and publisher
SHA match. The archive contains only two safe relative directories and one
9,225,032B regular executable. It is unpacked in a new permanent software leaf:

```text
/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/breakinator_runtime_20261014_01
```

Executable SHA256 is
`049948306338709b9b4e3fa7e9750770bbbb659558723472c1507b821b84e29a`.
This binds the actual executable; it is not a reproducible-build attestation.
No report archive, PAF, genomic read or reference was downloaded.

## Exact ABI-only packet

The source tag resolves to `2a5b7138aee9368c6c613c0837f3d8152437957c`.
The worker inspects the tagged CLI, BAM parser and report implementation.
The source still prints `breakinator 1.0`; preserve the actual version string
and separate it from the release tag. The source's symmetry check also uses
the second query location twice. Do not repair or tune this third-party code;
record native behavior, not an inferred whole-program defect or paper claim.

| Local frozen file | SHA256 |
|---|---|
| `analysis/breakinator_native_controls.py` |`8ad7ac003fbbefd680d51cf98e83bd70b8e3c8c2400ec1921e7a5bdf0c9382bf`|
| `tests/test_breakinator_native_controls.py` |`13418662357ad35fbcf9168f774aa79469b131e27702b40cd98cfdb9c5b05d87`|
| `scripts/run_breakinator_abi_20261014_01.sh` |`50d1bb87d249b3eb9e60989858bfc34ac5b62cbbfc1a7c9726840bcc54c007bf`|

All11 local controls pass in0.43s, no skips; main reads the full implementation
and tests. Mock execution tests do not establish native runtime behavior.
The real tiny name-sorted BAM has four synthetic groups/seven alignments:
contiguous reference, central foldback, noncentral foldback and two-chromosome
join. Expected outcomes are no breakpoint, Foldback, Pass and Chimeric.
Pass/TrueBreak is a native geometry category, not biological truth.

The native command uses BAM input, `--rcoord` and one I/O thread with unchanged
classification defaults. Record exact stdout/stderr/report, executable hash,
version, fixture hash and all coordinates. A mismatch stops qualification;
it is not a zero study result. Exclusive-output guards prevent replay.

## Planned allocation and preservation

One direct `srun` allocation on hydra-n1/amd_256M:1CPU,512MiB,5min, noGPU.
Synthetic helper outer timeout130s plus10s termination grace; each subprocess
has its own60s timeout. This small ABI allocation is separate from, and does
not spend or reset, the later real-input screen's1CPU/2GiB/15min envelope.

New writable output leaf:
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/breakinator_abi_20261014_01`.
The software stays in read-only compute HOME; logs and controls go to scratch.
Main preserves every success/failure through login into a new permanent HOME
leaf and verifies bytes before22October. Job ID and actual resource/result
must be added after submission. Preparation is not evidence that it ran.
