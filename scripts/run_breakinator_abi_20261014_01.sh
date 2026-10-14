#!/usr/bin/env bash
# Native interface qualification only; no study BAM access.
set -Eeuo pipefail
umask 077
runtime=/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/breakinator_runtime_20261014_01
output=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/breakinator_abi_20261014_01
python=/beegfs/datasets/home/igorno/alignssl_restart_20260922/venvs/hg002_intake_check_20261010/bin/python
[[ -n "${SLURM_JOB_ID:-}" && "${SLURM_CPUS_PER_TASK:-}" == 1 && "${SLURM_JOB_NUM_NODES:-}" == 1 ]]
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && -d "$output" && ! -e "$output/native" && ! -e "$output/execution.txt" ]]
cd "$output"
finish() {
  local rc=$?
  trap - EXIT
  printf 'exit_code=%s\ncompleted_utc=%s\n' "$rc" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > exit-status.txt
  exit "$rc"
}
trap finish EXIT
printf 'job_id=%s\nstarted_utc=%s\nnode=%s\n' "$SLURM_JOB_ID" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(hostname)" > execution.txt
[[ "$(sha256sum "$runtime/breakinator_native_controls.py" | cut -d ' ' -f 1)" == 8ad7ac003fbbefd680d51cf98e83bd70b8e3c8c2400ec1921e7a5bdf0c9382bf ]]
[[ "$(sha256sum "$runtime/breakinator-v1.1.1/bin/breakinator" | cut -d ' ' -f 1)" == 049948306338709b9b4e3fa7e9750770bbbb659558723472c1507b821b84e29a ]]
"$python" -B -c 'import sys,pysam; assert pysam.__version__=="0.24.1"; print(sys.version); print(pysam.__version__)' > runtime.txt
mkdir native
timeout --signal=TERM --kill-after=10s 130s "$python" -B "$runtime/breakinator_native_controls.py" \
  --binary "$runtime/breakinator-v1.1.1/bin/breakinator" --output-dir "$output/native" \
  > controls.stdout.txt 2> controls.stderr.txt
