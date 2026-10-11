#!/usr/bin/env bash
# Read-only COMPLETE readset and small QA/cleanup packet custody comparison.
# Prior whole gzip CRC/census is inherited only through identical SHA bytes.
set -Eeuo pipefail
umask 077
project=/beegfs/datasets/home/igorno/alignssl_restart_20260922
scratch=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922
out="$scratch/experiments/hg002_home_readset_verify_s1_20261011_01"
[[ -n "${SLURM_JOB_ID:-}" && "${SLURM_CPUS_PER_TASK:-}" == 1 && "${SLURM_JOB_NUM_NODES:-}" == 1 ]]
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && ! -e "$out" && ! -L "$out" ]]
mkdir "$out"
finish() { local rc=$?; trap - EXIT; printf 'exit_code=%s\n' "$rc" > "$out/exit-status.txt"; exit "$rc"; }
trap finish EXIT
printf 'job_id=%s\nscript_sha256=%s\nstarted_utc=%s\n' "$SLURM_JOB_ID" "$(sha256sum "$0" | awk '{print $1}')" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$out/execution.txt"
sacct -j 1604300,1604303 --allocations --noheader --format=JobID,State,ExitCode -P > "$out/prerequisite-slurm.txt"
grep -qx '1604300|COMPLETED|0:0' "$out/prerequisite-slurm.txt"
grep -qx '1604303|COMPLETED|0:0' "$out/prerequisite-slurm.txt"
for leaf in hg002_read_extract_20261010_01 hg002_s1_custody_verify_20261011_01 hg002_duplicate_cleanup_s1_20261011_01; do
  source="$scratch/experiments/$leaf"
  home="$project/experiments/$leaf"
  [[ -d "$source" && ! -L "$source" && -d "$home" && ! -L "$home" ]]
  [[ -z "$(find "$source" "$home" -mindepth 1 ! -type f -print -quit)" ]]
  (cd "$source"; find . -type f -printf '%P\n' | LC_ALL=C sort) > "$out/$leaf.source-names.txt"
  (cd "$home"; find . -type f -printf '%P\n' | LC_ALL=C sort) > "$out/$leaf.home-names.txt"
  cmp "$out/$leaf.source-names.txt" "$out/$leaf.home-names.txt"
  stat -c '%d %i %s %y %z %n' "$source"/* "$home"/* > "$out/$leaf.stat.before.txt"
  (cd "$source"; find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) > "$out/$leaf.source-sha256sums.txt"
  (cd "$home"; sha256sum -c "$out/$leaf.source-sha256sums.txt") > "$out/$leaf.home-hash-check.txt"
  stat -c '%d %i %s %y %z %n' "$source"/* "$home"/* > "$out/$leaf.stat.after.txt"
  cmp "$out/$leaf.stat.before.txt" "$out/$leaf.stat.after.txt"
done
reads="$scratch/experiments/hg002_read_extract_20261010_01"
[[ "$(wc -l < "$out/hg002_read_extract_20261010_01.source-names.txt")" == 5 ]]
printf '%s  %s\n' \
  42dcd54a2aeb59951fbea8bed4e92aa8d5661bdfb0aabaef3610eb795ab519ae ./identities.sqlite \
  12ed8f3f373f80efee99a3f0b5c3d4d62f88eb5367019848df5acbd0c9c9e0dc ./manifest.initial.json \
  4355f3b3d5392c41f0ca92da94e389a66907bf6297d8d3fa13f2996ccf641acc ./readiness.json \
  fd9fd85d7dfadca083cd101aad00932e16d23d8b5d90db4ddec7523abaabae88 ./source_reads.fastq.gz \
  fa7a7ae213df6cccd6f6b92f7c550fe68452390c0369510c473352c895b347da ./stats.jsonl > "$out/accepted-source-sha256sums.txt"
cmp "$out/accepted-source-sha256sums.txt" "$out/hg002_read_extract_20261010_01.source-sha256sums.txt"
printf 'complete_home_readset_and_both_evidence_packets=PASS\nwhole_gzip_crc_and_census=INHERITED_VIA_IDENTICAL_SHA_FROM_1604300\ncompleted_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$out/custody-result.txt"
