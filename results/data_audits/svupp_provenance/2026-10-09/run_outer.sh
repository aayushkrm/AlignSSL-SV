#!/usr/bin/env bash
set -euo pipefail
cd /beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/svupp-provenance-20261009-01
[[ "${1:-}" =~ ^[0-9a-f]{64}$ ]]
printf '%s  bundle.sha256\n' "$1" | sha256sum -c -
sha256sum -c bundle.sha256
test ! -e outer.claim.json
test ! -e launch_tree.time.log
test ! -e launch.stdout.log
test ! -e launch.stderr.log
set -C
printf '{"phase":"CLAIMED_TIMED_PROVENANCE_HEADERS"}\n' > outer.claim.json
mkdir -m 700 tmp
export TMPDIR="$PWD/tmp"
export PYTHONPATH="$PWD/code:/scratch/igorno-alignssl_restart_20260922/svpg_validation_controls_20261007_01/test_deps"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PY_COLORS=0 NO_COLOR=1
provenance_cpu="$(/home/igorno/miniconda3/envs/truvari_env/bin/python -c 'import os; print(min(os.sched_getaffinity(0)))')"
ulimit -S -t 20
ulimit -H -t 30
ulimit -v 2097152
ulimit -f 2048
exec /usr/bin/taskset -c "$provenance_cpu" /usr/bin/time -v -o launch_tree.time.log \
 timeout --signal=TERM --kill-after=5s 45s bash run_payload.sh \
 > launch.stdout.log 2> launch.stderr.log
