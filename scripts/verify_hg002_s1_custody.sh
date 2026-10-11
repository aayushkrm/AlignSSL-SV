#!/usr/bin/env bash
# Read-only S1 custody QA. No genomic mutation, caller, phase claim or deletion.
set -Eeuo pipefail
umask 077
project=/beegfs/datasets/home/igorno/alignssl_restart_20260922
scratch=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922
out="$scratch/experiments/hg002_s1_custody_verify_20261011_01"
reads="$scratch/experiments/hg002_read_extract_20261010_01"
[[ -n "${SLURM_JOB_ID:-}" && "${SLURM_CPUS_PER_TASK:-}" == 1 && "${SLURM_JOB_NUM_NODES:-}" == 1 ]]
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && ! -e "$out" && ! -L "$out" ]]
mkdir "$out"
finish() { local rc=$?; trap - EXIT; printf 'exit_code=%s\n' "$rc" > "$out/exit-status.txt"; exit "$rc"; }
trap finish EXIT
printf 'job_id=%s\nscript_sha256=%s\nstarted_utc=%s\n' "$SLURM_JOB_ID" "$(sha256sum "$0" | awk '{print $1}')" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$out/execution.txt"
files=("$reads/source_reads.fastq.gz" "$reads/identities.sqlite" "$reads/stats.jsonl" "$reads/manifest.initial.json" "$reads/readiness.json")
for parent in "$project" "$scratch"; do
  dir="$parent/experiments/hg002_dna_s1a_20261010_01"
  files+=("$dir/HG002_WGS.haplotagged.bam" "$dir/HG002_WGS.haplotagged.bam.bai")
done
stat -c '%d %i %s %y %z %n' "${files[@]}" > "$out/stat.before.txt"
for parent in "$project" "$scratch"; do
  dir="$parent/experiments/hg002_dna_s1a_20261010_01"
  printf '%s  %s\n' \
    b7edeb4bbc2589039c6148a912857f26924ca8fd5971cd3141337d0ce24bbde4 "$dir/HG002_WGS.haplotagged.bam" \
    5106ac6339847460842a528a312471785d9348f59cc65cca02b55b15e157e546 "$dir/HG002_WGS.haplotagged.bam.bai" | sha256sum -c >> "$out/raw-pair-hash-check.txt"
done
printf '%s  %s\n' fd9fd85d7dfadca083cd101aad00932e16d23d8b5d90db4ddec7523abaabae88 "$reads/source_reads.fastq.gz" | sha256sum -c > "$out/readset-hash-check.txt"
gzip -t "$reads/source_reads.fastq.gz" 2> "$out/gzip-crc.txt"
printf 'whole_gzip_eof_crc=PASS\n' >> "$out/gzip-crc.txt"
"$project/venvs/hg002_intake_check_20261010/bin/python" -B -c 'import json,sqlite3,sys; c=sqlite3.connect("file:"+sys.argv[1]+"?mode=ro",uri=True); q=c.execute("pragma quick_check").fetchall(); assert q==[("ok",)],q; row=c.execute("select count(*),sum(emitted),sum(case when emitted=1 then length else 0 end),sum(conflict),sum(bad),sum(constraint_bad) from reads").fetchone(); assert row==(5359077,5359077,80344827828,0,0,0),row; print(json.dumps({"sqlite_quick_check":q,"original_ids_emitted_ids_bases_conflict_bad_constraint_bad":row})); c.close()' "$reads/identities.sqlite" > "$out/sqlite-check.json"
(
  cd "$reads"
  sha256sum identities.sqlite stats.jsonl manifest.initial.json readiness.json > "$out/metadata-sha256sums.txt"
)
stat -c '%d %i %s %y %z %n' "${files[@]}" > "$out/stat.after.txt"
cmp "$out/stat.before.txt" "$out/stat.after.txt"
printf 'completed_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$out/execution.txt"
# Requires authoritative Slurm COMPLETED0:0 as well as these receipts.
