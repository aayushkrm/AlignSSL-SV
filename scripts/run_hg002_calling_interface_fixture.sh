#!/usr/bin/env bash
#SBATCH --job-name=hg002-calling-interface-s0
#SBATCH --partition=amd_256M
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=3
#SBATCH --mem=4G
#SBATCH --time=00:05:00
# No submission, genome inputs, downloads, retry, PATH edits or policy tuning.
set -Eeuo pipefail
umask 077
ulimit -c 0
ulimit -f 8192  # Linux Bash KiB; per-file guard, not a whole-leaf quota.
[[ $# == 5 ]] || { printf 'Need BUNDLE OUT REMAINING_S0_CPU_SECONDS OTHER_8G_MATERIAL_BYTES BUNDLE_MANIFEST_SHA256\n' >&2; exit 2; }
hg2_bundle=$1; hg2_out=$2; hg2_cpu=$3; hg2_other=$4; hg2_manifest_sha=$5
hg2_parent=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments
hg2_project=/beegfs/datasets/home/igorno/alignssl_restart_20260922
hg2_python="$hg2_project/venvs/hg002_intake_check_20261010/bin/python"
hg2_tools="$hg2_project/experiments/hg002_dna_callers_s0_20261010_01/bin"
[[ "$hg2_cpu" =~ ^[1-9][0-9]{0,4}$ && "$hg2_other" =~ ^(0|[1-9][0-9]{0,10})$ && "$hg2_manifest_sha" =~ ^[0-9a-f]{64}$ ]]
(( hg2_cpu >= 900 && hg2_cpu <= 14400 && hg2_other + 67108864 <= 8589934592 ))
# New strict <32-MiB leaf plus HOME copy fits INSIDE the existing 8-GiB reserve.
[[ "$hg2_bundle" == /* && "$(readlink -f "$hg2_bundle")" == "$hg2_bundle" ]]
[[ "$(readlink -f "$0")" == "$hg2_bundle/scripts/run_hg002_calling_interface_fixture.sh" ]]
[[ "$hg2_out" == "$hg2_parent"/hg002_calling_interface_s0_20261011_[0-9][0-9] ]]
[[ "$(readlink -f "$hg2_parent")" == "$hg2_parent" && ! -e "$hg2_out" && ! -L "$hg2_out" ]]
[[ "${SLURM_JOB_ID:-}" =~ ^[0-9]+$ && "${SLURM_CPUS_PER_TASK:-}" == 3 ]]
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]]
for hg2_prereq in sha256sum scontrol cp mkdir readlink awk grep df; do command -v "$hg2_prereq" >/dev/null; done
[[ -x "$hg2_python" && -x "$hg2_tools/pbmm2" && -x "$hg2_tools/pbsv" ]]
printf '%s  %s\n' "$hg2_manifest_sha" "$hg2_bundle/source-sha256sums.txt" | sha256sum -c
(cd "$hg2_bundle" && sha256sum -c source-sha256sums.txt)
printf '%s  %s\n' \
  197a54c9dbf6dd3f7f9264a3eb090d0646f08d05fdb7dfe99ae2c337f0064f4e "$hg2_bundle/analysis/hg002_cds_overlap_cohort.py" \
  f8a583d27a6232706c8ffe31dab3e52815455032517e9c1399940d4a3ea612bc "$hg2_tools/pbmm2" \
  01d83ec77ce40a5416b2a591f98090c51870b25d66650eccc7d7c493e1da5ae6 "$hg2_tools/pbsv" | sha256sum -c
(( $(df -Pk "$hg2_parent" | awk 'END {print $4}') >= 65536 ))
mkdir "$hg2_out"  # Exclusive fresh leaf, never mkdir -p or reuse.
hg2_fixture="$hg2_bundle/scripts/make_hg002_calling_interface_fixture.py"
hg2_deadline=$(( SECONDS + 270 ))
hg2_finish() {
  hg2_exit=$?
  trap - EXIT INT TERM
  set +e
  "$hg2_python" -B "$hg2_fixture" finalize --root "$hg2_out" --exit-code "$hg2_exit"
  hg2_final=$?
  (( hg2_final == 0 )) || hg2_exit=2
  printf 'packet=%s exit=%s; synthetic-only, main owns HOME custody\n' "$hg2_out" "$hg2_exit"
  exit "$hg2_exit"
}
trap hg2_finish EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
cp "$0" "$hg2_out/runner-source.sh"
cp "$hg2_bundle/source-sha256sums.txt" "$hg2_out/frozen-source-sha256sums.txt"
printf 'remaining_s0_allocated_seconds=%s\nmax_new_allocated_seconds=900\nother_8g_material_bytes=%s\nnew_leaf_plus_home_inside_8g_bytes=67108864\nsoftware_genomic_body_bytes=0\n' "$hg2_cpu" "$hg2_other" > "$hg2_out/budget.txt"
sha256sum "$0" "$hg2_python" "$hg2_tools/pbmm2" "$hg2_tools/pbsv" > "$hg2_out/runtime-path-sha256sums.txt"
hg2_run() {
  local hg2_label=$1 hg2_limit=$2 hg2_left=$(( hg2_deadline - SECONDS ))
  shift 2
  (( hg2_left > 0 )) || return 2
  (( hg2_limit <= hg2_left )) || hg2_limit=$hg2_left
  "$hg2_python" -B "$hg2_fixture" step --root "$hg2_out" --label "$hg2_label" --seconds "$hg2_limit" -- "$@"
}
hg2_run allocation 8 scontrol show job "$SLURM_JOB_ID" --oneliner
for hg2_field in NumCPUs=3 NumNodes=1 NumTasks=1 TimeLimit=00:05:00; do
  grep -Eq "(^|[[:space:]])$hg2_field([[:space:]]|$)" "$hg2_out/allocation.log"
done
grep -Eq '(^|[[:space:]])MinMemoryNode=(4G|4096M)([[:space:]]|$)' "$hg2_out/allocation.log"
! grep -Eqi 'gres/gpu|Gres=gpu|TresPer(Node|Task)=.*gpu' "$hg2_out/allocation.log"
cd "$hg2_bundle"
hg2_run environment 8 "$hg2_python" -B -c 'import sys,pysam; print(sys.executable,sys.version,pysam.__version__)'
hg2_run pbmm2-version 8 "$hg2_tools/pbmm2" --version
hg2_run pbsv-version 8 "$hg2_tools/pbsv" --version
grep -Eq '^pbmm2 26\.2\.0$' "$hg2_out/pbmm2-version.log"
grep -Eq '^pbsv 2\.11\.0 ' "$hg2_out/pbsv-version.log"
mkdir "$hg2_out/test-tmp" "$hg2_out/sort-tmp"
# TemporaryDirectory fixtures remain under this small leaf; no bytecode/cache.
hg2_run make-inputs 20 "$hg2_python" -B "$hg2_fixture" make --output "$hg2_out/inputs" --source-root "$hg2_bundle"
TMPDIR="$hg2_out/test-tmp" hg2_run unit-tests 30 "$hg2_python" -B -m unittest discover -s tests -p test_hg002_calling_interface_fixture.py -v
# Three allocated CPUs: one align thread + one sort thread + BAM I/O allowance.
TMPDIR="$hg2_out/sort-tmp" hg2_run remap 120 "$hg2_tools/pbmm2" align \
  "$hg2_out/inputs/reference.fa" "$hg2_out/inputs/reads.fastq" "$hg2_out/remapped.bam" \
  --preset CCS --sort --unmapped --bam-index BAI --sample SYNTHETIC_CCS_V1 \
  --rg '@RG\tID:toy_ccs_v1\tSM:SYNTHETIC_CCS_V1\tPL:PACBIO\tDS:READTYPE=CCS' -j 1 -J 1 -m 256M
[[ -s "$hg2_out/remapped.bam.bai" ]]
hg2_run bam-audit 20 "$hg2_python" -B "$hg2_fixture" audit-bam --fixture "$hg2_out/inputs" --bam "$hg2_out/remapped.bam" --output "$hg2_out/bam-audit.json"
hg2_run discover 60 "$hg2_tools/pbsv" discover --hifi "$hg2_out/remapped.bam" "$hg2_out/signatures.svsig.gz"
hg2_run call 60 "$hg2_tools/pbsv" call --hifi -j 1 "$hg2_out/inputs/reference.fa" "$hg2_out/signatures.svsig.gz" "$hg2_out/calls.vcf"
# No BED, regions, type restriction, threshold changes or PASS-only selection.
hg2_run cohort 20 "$hg2_python" -B "$hg2_bundle/analysis/hg002_cds_overlap_cohort.py" \
  --vcf "$hg2_out/calls.vcf" --gtf "$hg2_out/inputs/cds.gtf" --sample SYNTHETIC_CCS_V1 --output "$hg2_out/cohort.jsonl"
hg2_run comparison 20 "$hg2_python" -B "$hg2_fixture" compare --fixture "$hg2_out/inputs" \
  --vcf "$hg2_out/calls.vcf" --cohort "$hg2_out/cohort.jsonl" --output "$hg2_out/comparison.json"
(cd "$hg2_bundle" && sha256sum -c source-sha256sums.txt)
# Any nonzero/timeout/guard/comparison error preserves the leaf via EXIT trap.
