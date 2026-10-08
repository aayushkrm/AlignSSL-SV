#!/usr/bin/env bash
set -euo pipefail
cd /scratch/igorno-alignssl_restart_20260922/caller-projection-diagnosis-20261009-01
[[ "${1:-}" =~ ^[0-9a-f]{64}$ ]]
printf '%s  bundle.sha256\n' "$1" | sha256sum -c -
sha256sum -c bundle.sha256
test ! -e launched
test ! -e launch_tree.time.log
test ! -e launch.stdout.log
test ! -e launch.stderr.log
ulimit -S -t 30
ulimit -H -t 180
ulimit -v 4194304
exec /usr/bin/time -v -o launch_tree.time.log timeout --signal=KILL 300s \
 bash run_diagnosis.sh > launch.stdout.log 2> launch.stderr.log
