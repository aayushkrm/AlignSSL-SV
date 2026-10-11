#!/usr/bin/env bash
# Submit once under the manifest; pass its exact bundle.sha256 hash.
set -euo pipefail
run_dir=/scratch/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01
cd "$run_dir"
[[ "${1:-}" =~ ^[0-9a-f]{64}$ ]]
printf '%s  bundle.sha256\n' "$1" | sha256sum -c -
sha256sum -c bundle.sha256
test ! -e launched
test ! -e launch_tree.time.log
test ! -e launch.stdout.log
test ! -e launch.stderr.log
ulimit -S -t 120
ulimit -H -t 300
ulimit -v 4194304
exec /usr/bin/time -v -o launch_tree.time.log timeout --signal=KILL 3900s \
 bash run_caller_preparation.sh > launch.stdout.log 2> launch.stderr.log
