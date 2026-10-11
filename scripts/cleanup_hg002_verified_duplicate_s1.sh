#!/usr/bin/env bash
# Main's exact, recoverable duplicate cleanup after accepted S1 custody QA.
# Run on the SAME compute host as QA, so device/inode/stat receipts compare.
set -Eeuo pipefail
umask 077
project=/beegfs/datasets/home/igorno/alignssl_restart_20260922
scratch=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922
qa="$scratch/experiments/hg002_s1_custody_verify_20261011_01"
reads="$scratch/experiments/hg002_read_extract_20261010_01"
out="$scratch/experiments/hg002_duplicate_cleanup_s1_20261011_01"
target="$scratch/experiments/hg002_dna_s1a_20261010_01/HG002_WGS.haplotagged.bam"
original="$project/experiments/hg002_dna_s1a_20261010_01/HG002_WGS.haplotagged.bam"
[[ -n "${SLURM_JOB_ID:-}" && "${SLURM_CPUS_PER_TASK:-}" == 1 && "${SLURM_JOB_NUM_NODES:-}" == 1 ]]
[[ "$(hostname -s)" == hydra-n1 && ! -e "$out" && ! -L "$out" ]]
mkdir "$out"
finish() { local rc=$?; trap - EXIT; printf 'exit_code=%s\n' "$rc" > "$out/exit-status.txt"; exit "$rc"; }
trap finish EXIT
printf 'job_id=%s\nscript_sha256=%s\nstarted_utc=%s\n' "$SLURM_JOB_ID" "$(sha256sum "$0" | awk '{print $1}')" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$out/execution.txt"
sacct -j 1604300 --allocations --noheader --format=State,ExitCode -P > "$out/prerequisite-slurm.txt"
grep -qx 'COMPLETED|0:0' "$out/prerequisite-slurm.txt"
grep -qx 'job_id=1604300' "$qa/execution.txt"
grep -qx 'script_sha256=dc6bc3daa1c68f726610cc752518609634eee14537ca3332a3303fe7befabbd0' "$qa/execution.txt"
grep -qx 'exit_code=0' "$qa/exit-status.txt"
[[ "$(grep -c ': OK$' "$qa/raw-pair-hash-check.txt")" == 4 ]]
grep -qx "$reads/source_reads.fastq.gz: OK" "$qa/readset-hash-check.txt"
grep -qx 'whole_gzip_eof_crc=PASS' "$qa/gzip-crc.txt"
[[ -f "$target" && ! -L "$target" && -f "$original" && ! -L "$original" ]]
[[ "$(stat -c '%s %h' "$target")" == '48727325910 1' ]]
[[ "$(stat -c '%s' "$original")" == 48727325910 ]]
files=("$reads/source_reads.fastq.gz" "$reads/identities.sqlite" "$reads/stats.jsonl" "$reads/manifest.initial.json" "$reads/readiness.json")
for parent in "$project" "$scratch"; do
  dir="$parent/experiments/hg002_dna_s1a_20261010_01"
  [[ -f "$dir/HG002_WGS.haplotagged.bam.bai" && ! -L "$dir/HG002_WGS.haplotagged.bam.bai" ]]
  files+=("$dir/HG002_WGS.haplotagged.bam" "$dir/HG002_WGS.haplotagged.bam.bai")
done
cmp "$qa/stat.before.txt" "$qa/stat.after.txt"
stat -c '%d %i %s %y %z %n' "${files[@]}" > "$out/stat.current.txt"
cmp "$qa/stat.after.txt" "$out/stat.current.txt"
"$project/venvs/hg002_intake_check_20261010/bin/python" -B -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r=={"sqlite_quick_check":[["ok"]],"original_ids_emitted_ids_bases_conflict_bad_constraint_bad":[5359077,5359077,80344827828,0,0,0]}' "$qa/sqlite-check.json"
du -sb "$project/experiments/hg002_dna_s1a_20261010_01" "$scratch/experiments/hg002_dna_s1a_20261010_01" "$reads" "$qa" "$out" > "$out/inventory.before.tsv"
total=$(awk '{sum+=$1} END {printf "%.0f",sum}' "$out/inventory.before.tsv")
readset_bytes=$(du -sb "$reads" | awk '{print $1}')
# Include the full future readset copy plus1GiB for QA/log/bundle/receipt
# copies and temporaries beyond the finite named inventory.
projected=$(( total - 48727325910 + readset_bytes + 1073741824 ))
printf 'named_before_bytes=%s\nprojected_after_cleanup_and_full_copy_bytes=%s\ncap_bytes=171798691840\nother_small_material_reserve_bytes=1073741824\n' "$total" "$projected" > "$out/disk-contract.txt"
(( projected < 171798691840 ))
(( $(df -Pk "$project" | awk 'END {print $4}') * 1024 > readset_bytes + 1073741824 ))
[[ ! -e "$project/experiments/hg002_read_extract_20261010_01" && ! -L "$project/experiments/hg002_read_extract_20261010_01" ]]
# Fresh identical stat receipts and terminal QA are prerequisites above.
# THIS is the only deletion. Original HOME bytes, BAI and all logs stay.
unlink -- "$target"
[[ ! -e "$target" && ! -L "$target" && -f "$original" && ! -L "$original" ]]
printf 'removed_exact_target=%s\nremoved_bytes=48727325910\nrecoverable_from=%s\noriginal_sha256=b7edeb4bbc2589039c6148a912857f26924ca8fd5971cd3141337d0ce24bbde4\ncompleted_utc=%s\n' "$target" "$original" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$out/cleanup-receipt.txt"
