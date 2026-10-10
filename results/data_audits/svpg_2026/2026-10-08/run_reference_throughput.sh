#!/usr/bin/env bash
# One durable bundle. Run only under its independently approved outer recipe.
set -euo pipefail
run_dir=/scratch/igorno-alignssl_restart_20260922/original-ref-validation-20261008-throughput01
cd "$run_dir"
mkdir launched
printf 'LAUNCH_CLAIMED\n' > launched/state.txt
printf '%s\n' "$$" > launched/launcher.pid
ulimit -S -t 60
ulimit -v 4194304
test "$(ulimit -H -t)" = 600
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$run_dir:/scratch/igorno-alignssl_restart_20260922/svpg_validation_controls_20261007_01/test_deps"
printf '%s\n' \
 'd763f6e7a3c9e6af87cbdfa826fd44d2ef3d5fcdbf57ce975d80f86fbe10a6e9  analysis/check_released_truth_reference_gate.py' \
 '72155ac81968fb83db370613da54d3aa18efca11abf77780e9a49039af7cf0a4  analysis/check_released_truth_reference.py' \
 '2fb977a24b4d027ee4508f2f45eb07d11866cc4dd8101ab340cf95983de1f523  analysis/diagnose_released_truth_metadata.py' \
 '8b4acc8fa8b9a86d71c9847dd3a175e6816f24a1e2827f231ddf6cf244a05fa0  analysis/check_released_truth_metadata.py' \
 '4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93  analysis/released_truth_units.py' \
 '67136a5d47a13ca48d59e26d7f674b403b1113455fd5b0f9067b65ee023a5bd2  tests/test_check_released_truth_reference_gate.py' \
 '9222f371bd87f364ba9712a9f240032558fd6c461d11b8e5cbd4b5b42654e0e8  protocol.json' | sha256sum -c -
mkdir launched/controls.claimed
test ! -e control_fixtures
set +e
(
 ulimit -H -t 60
 exec /usr/bin/time -v -o controls.time.log timeout --foreground -k 5s 120s \
 /home/igorno/miniconda3/envs/truvari_env/bin/python -m pytest -q -p no:cacheprovider \
 --basetemp "$run_dir/control_fixtures" tests/test_check_released_truth_reference_gate.py \
) > controls.stdout.log 2> controls.stderr.log
control_status=$?
set -e
control_bundle_bytes=$(( $(stat -c %s controls.stdout.log) + $(stat -c %s controls.stderr.log) + $(stat -c %s controls.time.log) ))
if [[ "$control_status" != 0 || "$control_bundle_bytes" -gt 16384 ]] || \
 ! grep -Eq '^41 passed in ' controls.stdout.log || \
 grep -Eq 'skipped|deselected|failed|error' controls.stdout.log; then
 printf 'INCOMPLETE_CONTROL\n' >> launched/state.txt
 exit 2
fi
printf 'CONTROL_PASS\n' >> launched/state.txt
mkdir launched/real.claimed
printf 'REAL_RUNNING\n' >> launched/state.txt
set +e
(
 ulimit -S -t 600
 exec /usr/bin/time -v -o reference.time.log timeout --foreground -k 5s 900s \
 /home/igorno/miniconda3/envs/truvari_env/bin/python analysis/check_released_truth_reference_gate.py \
 --truth-path /scratch/igorno-alignssl_restart_20260922/svpg_truth_prepare_20261007_02/prepared/eligible_truth.vcf \
 --reference-path /scratch/igorno-alignssl_restart_20260922/recovery-pilot-v1/hs37d5.fa.gz \
 --fai-path /scratch/igorno-alignssl_restart_20260922/recovery-pilot-v1/hs37d5.fa.gz.fai \
 --native-report-path /scratch/igorno-alignssl_restart_20260922/native-truth-compatibility-20261008-throughput01/native_report.json \
 --protocol-path protocol.json --protocol-sha256 9222f371bd87f364ba9712a9f240032558fd6c461d11b8e5cbd4b5b42654e0e8 \
 --report-path reference_report.json
) > reference.stdout.log 2> reference.stderr.log
reference_status=$?
set -e
if [[ "$reference_status" != 0 || ! -f reference_report.json ]]; then
 printf 'INCOMPLETE_REFERENCE\n' >> launched/state.txt
 exit 2
fi
reference_bundle_bytes=$(( $(stat -c %s reference_report.json) + $(stat -c %s reference.stdout.log) + $(stat -c %s reference.stderr.log) + $(stat -c %s reference.time.log) ))
if [[ "$reference_bundle_bytes" -gt 262144 ]] || \
 ! grep -q '"original_anchored_REF_validation": "PASS"' reference_report.json; then
 printf 'INCOMPLETE_REFERENCE_OUTPUT\n' >> launched/state.txt
 exit 2
fi
printf 'COMPLETE\n' >> launched/state.txt
