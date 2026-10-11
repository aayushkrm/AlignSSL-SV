#!/usr/bin/env bash
# One exact-reviewed bundle; exclusive claims prevent replay.
set -euo pipefail
unset POSIXLY_CORRECT
run_dir=/scratch/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01
cd "$run_dir"
mkdir launched
printf 'LAUNCH_CLAIMED\n' > launched/state.txt
ulimit -S -t 120
ulimit -v 4194304
ulimit -f 131072
test "$(ulimit -H -t)" = 300
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$run_dir:/scratch/igorno-alignssl_restart_20260922/svpg_validation_controls_20261007_01/test_deps"
sha256sum -c bundle.sha256
mkdir launched/controls.claimed
test ! -e control_fixtures
set +e
(
 ulimit -S -t 60
 ulimit -H -t 60
 exec /usr/bin/time -v -o controls.time.log timeout --foreground -k 5s 120s \
 /home/igorno/miniconda3/envs/truvari_env/bin/python -m pytest -q -p no:cacheprovider \
 --basetemp "$run_dir/control_fixtures" \
 tests/test_prepare_released_callers.py tests/test_prepare_released_callers_rnames.py
) > controls.stdout.log 2> controls.stderr.log
control_status=$?
set -e
control_bytes=$(( $(stat -c %s controls.stdout.log) + $(stat -c %s controls.stderr.log) + $(stat -c %s controls.time.log) ))
if [[ "$control_status" != 0 || "$control_bytes" -gt 262144 ]] || \
 ! grep -Eq '^48 passed in ' controls.stdout.log || \
 grep -Eq 'skipped|deselected|failed|error' controls.stdout.log; then
 printf 'INCOMPLETE_CONTROL\n' >> launched/state.txt
 exit 2
fi
printf 'CONTROL_PASS\n' >> launched/state.txt
mkdir prepared
for caller in cutesv debreak sawfish sniffles svim svpg; do
 mkdir "launched/$caller.claimed"
 printf 'CALLER_RUNNING %s\n' "$caller" >> launched/state.txt
 protocol_sha=$(grep -F "  protocols/$caller.json" bundle.sha256)
 protocol_sha="${protocol_sha%% *}"
 set +e
 (
  ulimit -S -t 300
  exec /usr/bin/time -v -o "$caller.time.log" timeout --foreground -k 5s 600s \
  /home/igorno/miniconda3/envs/truvari_env/bin/python analysis/prepare_released_callers.py \
  --source-path "inputs/$caller.vcf" --outdir "prepared/$caller" \
  --protocol-path "protocols/$caller.json" --protocol-sha256 "$protocol_sha"
 ) > "$caller.stdout.log" 2> "$caller.stderr.log"
 caller_status=$?
 set -e
 report="prepared/$caller/caller_preparation_report.json"
 if [[ "$caller_status" != 0 || ! -f "$report" ]]; then
  printf 'INCOMPLETE_CALLER %s\n' "$caller" >> launched/state.txt
  exit 2
 fi
 output_bytes=$(( $(stat -c %s "$caller.stdout.log") + $(stat -c %s "$caller.stderr.log") + $(stat -c %s "$caller.time.log") + $(stat -c %s "$report") ))
 if [[ "$output_bytes" -gt 1310720 ]] || ! grep -q '"status": "complete"' "$report"; then
  printf 'INCOMPLETE_CALLER_OUTPUT %s\n' "$caller" >> launched/state.txt
  exit 2
 fi
 printf 'CALLER_COMPLETE %s\n' "$caller" >> launched/state.txt
done
printf 'COMPLETE\n' >> launched/state.txt
