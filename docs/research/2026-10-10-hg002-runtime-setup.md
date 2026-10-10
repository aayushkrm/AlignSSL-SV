# HG002 native runtime: actual isolated setup

2026-10-10. Routine software work only. No genome or RNA input was acquired
or analyzed by these setup jobs. Native whole-genome annotation is untested.

## Failures preserved

| Attempt | Actual outcome |
|---|---|
| sbatch1604238, default debug/hydra-n12 | FAILED0:53 after1s, no stdout, no measured CPU, no setup folder/venv. Signal cause unproved. |
| direct1604239, default debug/hydra-n12 | FAILED1:0 after1s, measuredCPU0.018s; mkdir of project-home record rejected as read-only before pip. |
| requested hydra-n1 in default partition | Rejected without an allocation: node configuration unavailable. Live membership puts n1 in amd_256M, not debug. |
| direct1604241, amd_256M/hydra-n1 | FAILED1:0 after1s, measuredCPU0.018s; same home mkdir read-only before pip. |
| direct1604242, amd_256M/hydra-n1, writable scratch | COMPLETED0:0,82s elapsed, measuredCPU29.169s, MaxRSS212128K. Requested2CPUs/8GiB/20min; no GPU/idle whole node. |

The three allocated failed attempts plus completed job used170 allocated
CPU seconds (2 CPUs times1+1+1+82 elapsed seconds), separate from29.205s
measured task CPU. No automatic retry or historical result overwrite.
The earlier whole-node/default-partition assumptions are not repeated.

## Exact source and qualification

[Setup script](../../scripts/setup_hg002_lifton_runtime.sh) SHA256
`e25f58a3a206116100b743c589bf21e92ee71e89c52e44e9c70f86c71d387b34`
matches the executed immutable02 upload. LiftOn source commit
`8378f8e4a3d8404c94d801c285a2c74291e893b7` produced a1.0.14 wheel.
CPython3.12.1 on the cluster. Source archive download is reported by pip as
191.3MB; software HTTP bodies were not byte-metered, so this is not an exact
transfer-account total. Software is separate from196,608B genomic prefixes.

The scratch venv passes pip check, version, help and native-extension imports.
The required polish/cds/copies/validate-output flags are present. The original
wheelhouse (119,817,989B apparent bytes including directory entries) and all
setup records are backed up to non-expiring home. A **new** home venv was
installed from those wheels offline on the writable login host; no relocated
venv/shebangs, shared environment change or expensive login-node analysis.
Home pip check and CLI version pass. Separate read-only compute-node job
1604243 also passes pip check, native imports and version from that home
venv on hydra-n1: COMPLETED0:0,2s,1.748 measuredCPU s,102100K MaxRSS,
one requested CPU/1GiB. It adds2 allocatedCPU seconds to S0, giving172
allocatedCPU seconds for the recorded jobs. Version/help/imports do not
attest working alignments or P1.
External minimap2/miniprot executables remain unqualified.

Freeze,18 packages:

```text
argcomplete==3.7.2
argh==0.31.3
biopython==1.88
duckdb==1.5.6
gffutils==0.14
interlap==0.2.7
intervaltree==3.2.1
lifton==1.0.14
networkx==3.7
numpy==2.5.3
packaging==26.3
parasail==1.3.4
pyarrow==26.0.0
pyfaidx==0.9.0.4
pysam==0.24.1
simplejson==4.2.0
sortedcontainers==2.4.0
ujson==6.0.0
```

Home runtime:
`/beegfs/datasets/home/igorno/alignssl_restart_20260922/venvs/lifton1014_20261010`.
Raw custody:
`/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/hg002_lifton_setup_20261010_02`.
Scratch workspace expiresOctober22; no extension used. No raw software wheels
or genomic data enter Git. Small unchanged logs also stay off Git locally.

| Raw record | SHA256 |
|---|---|
| setup.log | `dfb2d3047baf8bd08b130ce122ae857375298ba7e7f5d99931c3f191b75b1108` |
| pip-freeze.txt | `01c4d444836156677b1c06c7c64e2a3214b8d8ca754828169a53d2d010b387e3` |
| version.txt | `0c88370cf0270677ff2aec34fefcd3b8d2ed5160bf0aca56d45c1c0a63483b51` |
| help.txt | `ccba418ba741d84243d4e67a8bf4dc3fb065c1b4bee848924040ff76425cce1d` |
| exit-status.txt | `bde294368bfed77c2cddf8cec271d398aee9cdbab3b26e1059281bd33adb0120` |

Goal remains active and unmet. This runtime is reusable infrastructure, not
a research result. The staged DNA intake needs its concrete acquisition
implementation and independent scrutiny before the large object transfer.
