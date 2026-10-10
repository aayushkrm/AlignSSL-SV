#!/usr/bin/env bash
# S0 interface check only: tiny wholly synthetic inputs, no donor/RNA input.
set -Eeuo pipefail
umask 077
project=/beegfs/datasets/home/igorno/alignssl_restart_20260922
bundle="$project/bundles/lifton_interface_s0_20261010_01"
parent=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments
out="$parent/lifton_interface_s0_20261010_01"
aligners="$project/experiments/hg002_native_aligners_s0_20261010_02"
runtime="$project/venvs/lifton1014_20261010"
control_python="$project/venvs/hg002_intake_check_20261010/bin/python"
[[ -n "${SLURM_JOB_ID:-}" && "${SLURM_CPUS_PER_TASK:-}" == 1 && "${SLURM_JOB_NUM_NODES:-}" == 1 ]]
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && ! -e "$out" && ! -L "$out" ]]
mkdir "$out"
finish() { local rc=$?; trap - EXIT; printf 'exit_code=%s\n' "$rc" > "$out/exit-status.txt"; exit "$rc"; }
trap finish EXIT
mkdir "$out/tmp"
export TMPDIR="$out/tmp" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH="$runtime/bin:$aligners/bin:$PATH"
printf 'job_id=%s\nscript_sha256=%s\n' "$SLURM_JOB_ID" "$(sha256sum "$0" | awk '{print $1}')" > "$out/execution.txt"
env | grep '^LIFTON_' | sort > "$out/lifton-environment.txt" || true
(
  cd "$aligners"
  sha256sum -c artifact-sha256sums.txt
) > "$out/aligner-custody-check.txt"
printf '%s  %s\n' \
  fb0c6423a1ba19235103d58debca65f921aef355e1ddff0f0a506a0fa09a94e7 "$bundle/analysis/make_lifton_interface_fixture.py" \
  92ee8481d5cd164ed4b8e5c446f066239774445c738b774a0ea0640a649ef0b8 "$bundle/tests/test_make_lifton_interface_fixture.py" | sha256sum -c > "$out/fixture-code-check.txt"
(
  cd "$bundle"
  "$control_python" -B -m pytest -q -p no:cacheprovider tests/test_make_lifton_interface_fixture.py
) > "$out/fixture-tests.txt" 2>&1
"$runtime/bin/python" -B "$bundle/analysis/make_lifton_interface_fixture.py" --output-dir "$out/input" > "$out/fixture-generation.txt"
printf '%s  %s\n' 684b56f9b566e4eb3d100fdd0f07785a7acc09c9bfb354d60a9d1ff70a7c4867 "$out/input/manifest.json" | sha256sum -c > "$out/fixture-manifest-check.txt"
minimap2 --version > "$out/minimap2.version.txt"
miniprot --version > "$out/miniprot.version.txt"
lifton -V > "$out/lifton.version.txt" 2>&1
cmd=("$runtime/bin/lifton" "$out/input/target.fa" "$out/input/reference.fa" -g "$out/input/reference.gff3" -o "$out/lifton.gff3" -dir "$out/work" -t 1 -polish -cds -copies --validate-output)
printf '%s\n' "${cmd[@]}" > "$out/argv.txt"
cd "$out"
"${cmd[@]}" > "$out/native.stdout.txt" 2> "$out/native.stderr.txt"
# Hash all persistent native artifacts after the native process has exited.
find . -type f ! -name artifact-sha256sums.txt -print0 | sort -z | xargs -0 sha256sum > artifact-sha256sums.txt
sha256sum -c artifact-sha256sums.txt > hash-check.txt
# Successful exit means interface execution only, never biological readiness.
