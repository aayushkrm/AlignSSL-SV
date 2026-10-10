#!/usr/bin/env bash
# One reviewed CPU-only batch job; never submit twice after unknown status.
set -euo pipefail
run_dir=/scratch/igorno-alignssl_restart_20260922/original-ref-validation-20261008-throughput01
cd "$run_dir"
test ! -e launched
test ! -e launch_tree.time.log
test ! -e launch.stdout.log
test ! -e launch.stderr.log
printf '%s\n' \
 'd763f6e7a3c9e6af87cbdfa826fd44d2ef3d5fcdbf57ce975d80f86fbe10a6e9  analysis/check_released_truth_reference_gate.py' \
 '72155ac81968fb83db370613da54d3aa18efca11abf77780e9a49039af7cf0a4  analysis/check_released_truth_reference.py' \
 '2fb977a24b4d027ee4508f2f45eb07d11866cc4dd8101ab340cf95983de1f523  analysis/diagnose_released_truth_metadata.py' \
 '8b4acc8fa8b9a86d71c9847dd3a175e6816f24a1e2827f231ddf6cf244a05fa0  analysis/check_released_truth_metadata.py' \
 '4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93  analysis/released_truth_units.py' \
 '67136a5d47a13ca48d59e26d7f674b403b1113455fd5b0f9067b65ee023a5bd2  tests/test_check_released_truth_reference_gate.py' \
 '9222f371bd87f364ba9712a9f240032558fd6c461d11b8e5cbd4b5b42654e0e8  protocol.json' \
 '345899f3cabc47e62ad6167b75ee86c295184b04942d058eacc090a76da66331  run_reference_throughput.sh' | sha256sum -c -
ulimit -S -t 60
ulimit -H -t 600
ulimit -v 4194304
exec /usr/bin/time -v -o launch_tree.time.log timeout --signal=KILL 1100s \
 bash run_reference_throughput.sh > launch.stdout.log 2> launch.stderr.log
