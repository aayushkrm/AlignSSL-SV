# Cluster ownership audit

**Audit time:** 2026-11-22 12:34:54 UTC. Cluster metadata was read through
`/Users/akm/aayushkrm-AlignSSL/tools/cluster.sh` at about 12:32 UTC.

## Scope

Read-only checks: `scontrol show job`, `sacct`, `ws_list`, and project Markdown
documentation. No workspace contents or job scripts were read. No job or
workspace was changed, copied, extended, deleted, or cancelled.

The project goal requests GPT-6.1 Terra Max effort. The requested model and
effort are not independently attested.

## Findings

| Resource | Live metadata | AlignSSL-SV ownership assessment |
|---|---|---|
| SLURM array task `1637246_1`, `1000g_wget` | `RUNNING`; user `igorno`, account `stud`, partition `amd_256M`, node `hydra-n4`, 2 CPUs and 8 GiB. Submitted 2026-11-20 01:07:15; started 01:07:17. `scontrol` maps it to job `1637247`, array `1637246`, task 1. Command: `/home/igorno/Alice_train_data/download_new_samples_wget.sbatch`. Standard output and error paths are under `/scratch/igorno-Alice_cnn_baseline/download_new_samples/`. `sacct` also reports `RUNNING`. | **Not established as AlignSSL-SV.** Scheduler paths associate it with the `Alice_train_data` / `Alice_cnn_baseline` workflow. AlignSSL-SV documentation discusses historical 1000 Genomes data, but does not connect this job or Alice workflow to the project. The shared 1000 Genomes topic is not enough to establish ownership. Left running and untouched. |
| Scratch workspace `pairsv-baseline-Cx2BFe` | `/scratch/igorno-pairsv-baseline-Cx2BFe`; `ws_list` reports 0 days, 2 hours remaining, expiration 2026-11-22 22:18:54, one extension available. No comment was present in the listing. | **Unresolved.** The name suggests a PairSV baseline, but project Markdown contains no matching workspace or project reference. Name alone cannot establish ownership. It is near expiry; no extension or other action was taken. |
| Scratch workspace `Alice_cnn_baseline` | `/scratch/igorno-Alice_cnn_baseline`; comment: “1000 Genomes deletion CNN baseline tensors and model”; expiration 2026-12-13 01:56:59, 20 days 6 hours remaining. The job's output paths name this workspace. | **Not established as AlignSSL-SV.** Its metadata strongly links it to `1000g_wget`, but project Markdown does not link the Alice baseline to AlignSSL-SV. The dataset topic overlaps with historical AlignSSL-SV work; that does not establish project ownership. |
| Scratch workspace `MCF7_replicates_SRA` | `/scratch/igorno-MCF7_replicates_SRA`; comment: “MCF7 replicate SRA processing”; expiration 2026-11-25 02:47:50, 2 days 7 hours remaining. | **Unrelated to AlignSSL-SV** in the project record. `PROGRESS.md` and `docs/research/RESTART_STATE.md` explicitly describe the MCF7 workspace as unrelated and untouched. No action was taken. |

`ws_list` showed these three active scratch workspaces. It showed no active
workspace named for AlignSSL-SV. The project guide records that the former
`/scratch/igorno-alignssl_sv` workspace expired on 2026-08-13
(`docs/CLUSTER.md`, lines 84–95). The restart record names
`/scratch/igorno-alignssl_restart_20260922`, with an October 22, 2026 expiry
(`docs/research/RESTART_STATE.md`, lines 1381–1386). These historical paths do
not establish ownership of the currently listed `pairsv` or Alice workspaces.

## Evidence and limits

- `scontrol show job --oneliner 1637246_1` returned the running job, array
  mapping, command path, working directory, resources, and output paths.
- `sacct -n -P -j 1637246_1 --format=JobID,JobName,User,Account,Partition,State,Submit,Start,End,Elapsed,ExitCode,NodeList,WorkDir`
  confirmed the task was still running and gave its accounting metadata.
- `ws_list` supplied workspace names, paths, comments where present, remaining
  time, expiration, and extension counts. No workspace contents were listed.
- A search of project Markdown found no reference to `pairsv-baseline`,
  `Alice_cnn_baseline`, `Alice_train_data`, or `1000g_wget`. The project docs do
  record historical 1000 Genomes inputs (`docs/CLUSTER.md`, lines 126–133) and
  identify MCF7 as unrelated (`PROGRESS.md`, lines 238–241;
  `docs/research/RESTART_STATE.md`, lines 160–165). A missing documentation
  reference is not proof of unrelated ownership.

**Disposition:** Treat the job and Alice workspace as associated with the Alice
CNN baseline workflow, with AlignSSL-SV ownership unproven. Keep
`pairsv-baseline-Cx2BFe` ownership unresolved and note its same-day expiry.
Leave all resources unchanged unless project ownership is established through
appropriate records.

## Subsequent user-authorized extension

The user explicitly requested extension of `pairsv-baseline-Cx2BFe` to preserve
its contents. After checking the cluster's `ws_extend` usage, the orchestrator
ran `ws_extend pairsv-baseline-Cx2BFe 30`. The command succeeded and a fresh
`ws_list` showed expiration **2026-12-22 19:44:39 cluster time**, with zero
extensions remaining. The command also reported updating the local reminder
settings. The workspace's project ownership remains unresolved; no workspace
contents were read or changed. The Alice-associated download job was not
modified.

## Subsequent project-input metadata check

On 2026-11-22 UTC, a read-only `stat` of the previously recorded HG002 home
BAM and BAI found them present at 48,727,325,910 and 21,582,928 bytes. Their
modification times match the earlier [custody record](../../results/hg002_read_extract_20261010/custody_qa/stat.before.txt).
This is a presence, size and timestamp check, not a new file-hash or biological
integrity verification. A fresh queue check still showed only the unrelated
Alice-associated `1000g_wget` task; no job was modified.
