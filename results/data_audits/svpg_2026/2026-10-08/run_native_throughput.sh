#!/usr/bin/env bash
# One durable claim, two fixed payload slots. Never replay after a lost handle.
# Invoke under the reviewed outer time/timeout/ulimit recipe, not directly.
set -euo pipefail
run_dir=/scratch/igorno-alignssl_restart_20260922/native-truth-compatibility-20261008-throughput01
cd "$run_dir"
mkdir launched
printf 'LAUNCH_CLAIMED\n' > launched/state.txt
printf '%s\n' "$$" > launched/launcher.pid
ulimit -t 60
ulimit -v 4194304
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$run_dir:/scratch/igorno-alignssl_restart_20260922/svpg_validation_controls_20261007_01/test_deps"
printf '%s\n' \
 'f97dcf0051e09f799b689be66903f88c3fceef3dd6281043ab92e8a762616214  analysis/check_released_truth_native.py' \
 '2fb977a24b4d027ee4508f2f45eb07d11866cc4dd8101ab340cf95983de1f523  analysis/diagnose_released_truth_metadata.py' \
 '8b4acc8fa8b9a86d71c9847dd3a175e6816f24a1e2827f231ddf6cf244a05fa0  analysis/check_released_truth_metadata.py' \
 '4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93  analysis/released_truth_units.py' \
 '0d1faed1c397c2acbc3d172a3855b732e0dd7918abaf1b38724e5d720206354e  tests/test_check_released_truth_native.py' \
 '65ffd119d382eaba1c3101d4736d3c89d66c707b67b5300b6c6aefffda3e4f67  tests/test_check_released_truth_metadata.py' \
 '8eaf621e8ccf752417aa0286b2451298e46e17831e6bb85ca0fd4798163c630a  protocol.json' | sha256sum -c -
mkdir launched/controls.claimed
test ! -e control_fixtures
set +e
/usr/bin/time -v -o controls.time.log timeout --foreground -k 5s 120s \
 /home/igorno/miniconda3/envs/truvari_env/bin/python -m pytest -q -p no:cacheprovider \
 --basetemp "$run_dir/control_fixtures" \
 tests/test_check_released_truth_native.py::test_exact_native_complete_endpoint \
 tests/test_check_released_truth_native.py::test_exact_native_rejects_bad_literal_without_report \
 tests/test_check_released_truth_native.py::test_exact_native_integrity_failure_no_report \
 tests/test_check_released_truth_native.py::test_native_contradictions_and_mutation \
 tests/test_check_released_truth_native.py::test_agreeing_parser_streams_cannot_hide_literal_field_drift \
 tests/test_check_released_truth_metadata.py::test_actual_kernel_blocks_writes_and_keeps_independent_positions \
 > controls.stdout.log 2> controls.stderr.log
control_status=$?
set -e
control_bundle_bytes=$(( $(stat -c %s controls.stdout.log) + $(stat -c %s controls.stderr.log) + $(stat -c %s controls.time.log) ))
if [[ "$control_status" != 0 || "$control_bundle_bytes" -gt 8192 ]] || \
 ! grep -Eq '^20 passed in ' controls.stdout.log || \
 grep -Eq 'skipped|deselected|failed|error' controls.stdout.log; then
 printf 'INCOMPLETE_CONTROL\n' >> launched/state.txt
 exit 2
fi
printf 'CONTROL_PASS\n' >> launched/state.txt
mkdir launched/real.claimed
printf 'REAL_RUNNING\n' >> launched/state.txt
set +e
/usr/bin/time -v -o native.time.log timeout --foreground -k 5s 120s \
 /home/igorno/miniconda3/envs/truvari_env/bin/python analysis/check_released_truth_native.py \
 --truth-path /scratch/igorno-alignssl_restart_20260922/svpg_truth_prepare_20261007_02/prepared/eligible_truth.vcf \
 --protocol-path protocol.json \
 --protocol-sha256 8eaf621e8ccf752417aa0286b2451298e46e17831e6bb85ca0fd4798163c630a \
 --report-path native_report.json > native.stdout.log 2> native.stderr.log
native_status=$?
set -e
if [[ "$native_status" != 0 || ! -f native_report.json ]]; then
 printf 'INCOMPLETE_NATIVE\n' >> launched/state.txt
 exit 2
fi
native_bundle_bytes=$(( $(stat -c %s native_report.json) + $(stat -c %s native.stdout.log) + $(stat -c %s native.stderr.log) + $(stat -c %s native.time.log) ))
if [[ "$native_bundle_bytes" -gt 16384 ]] || \
 ! grep -q '"native_metadata_consistency": "PASS"' native_report.json; then
 printf 'INCOMPLETE_NATIVE_OUTPUT\n' >> launched/state.txt
 exit 2
fi
printf 'COMPLETE\n' >> launched/state.txt
