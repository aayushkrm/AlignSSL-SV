#!/usr/bin/env bash
set -euo pipefail
unset POSIXLY_CORRECT
run_dir=/scratch/igorno-alignssl_restart_20260922/caller-projection-diagnosis-20261009-01
cd "$run_dir"
mkdir launched
printf 'LAUNCH_CLAIMED\n' > launched/state.txt
ulimit -S -t 30
ulimit -v 4194304
ulimit -f 128
test "$(ulimit -H -t)" = 180
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$run_dir:/scratch/igorno-alignssl_restart_20260922/svpg_validation_controls_20261007_01/test_deps"
sha256sum -c bundle.sha256
mkdir launched/controls.claimed
test ! -e control_fixtures
set +e
(
 ulimit -S -t 30
 ulimit -H -t 30
 exec /usr/bin/time -v -o controls.time.log timeout --foreground -k 5s 60s \
 /home/igorno/miniconda3/envs/truvari_env/bin/python -m pytest -q -p no:cacheprovider \
 --basetemp "$run_dir/control_fixtures" \
 tests/test_diagnose_caller_projection.py tests/test_caller_projection_serialization_diagnostic.py
) > controls.stdout.log 2> controls.stderr.log
control_status=$?
set -e
if [[ "$control_status" != 0 ]] || ! grep -Eq '^17 passed in ' controls.stdout.log || \
 grep -Eq 'skipped|deselected|failed|error' controls.stdout.log; then
 printf 'INCOMPLETE_CONTROL\n' >> launched/state.txt
 exit 2
fi
printf 'CONTROL_PASS\n' >> launched/state.txt
mkdir launched/diagnosis.claimed
printf 'DIAGNOSIS_RUNNING\n' >> launched/state.txt
set +e
(
 ulimit -S -t 120
 ulimit -H -t 120
 exec /usr/bin/time -v -o diagnosis.time.log timeout --foreground -k 5s 180s \
 /home/igorno/miniconda3/envs/truvari_env/bin/python analysis/diagnose_caller_projection.py \
 --root /scratch/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01 \
 --report "$run_dir/diagnosis.json"
) > diagnosis.stdout.log 2> diagnosis.stderr.log
diagnosis_status=$?
set -e
if [[ "$diagnosis_status" != 0 || ! -f diagnosis.json ]]; then
 printf 'INCOMPLETE_DIAGNOSIS\n' >> launched/state.txt
 exit 2
fi
printf 'COMPLETE\n' >> launched/state.txt
