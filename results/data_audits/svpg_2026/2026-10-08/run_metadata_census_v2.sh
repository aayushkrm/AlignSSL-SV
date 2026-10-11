#!/usr/bin/env bash
# One exact Linux launch after the read-cap correction; v1 was never launched.
set -euo pipefail
run_dir=/scratch/igorno-alignssl_restart_20260922/svpg_metadata_census_20261008_02
cd "$run_dir"
test ! -e metadata_census.json
test ! -e command_run.log
test ! -e stdout.log
test ! -e stderr.log
printf '%s\n' \
 '2fb977a24b4d027ee4508f2f45eb07d11866cc4dd8101ab340cf95983de1f523  diagnose_released_truth_metadata.py' \
 '4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93  released_truth_units.py' \
 'b1f619bccc1d6728048da6165a5c872d0f4d6e38c2b4b5fd43dd42134acdf0d4  metadata_census_protocol_v2.json' | sha256sum -c -
ulimit -t 60
ulimit -v 4194304
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
/usr/bin/time -v -o command_run.log timeout -k 5s 120s \
 /home/igorno/miniconda3/envs/truvari_env/bin/python diagnose_released_truth_metadata.py \
 --truth-path /scratch/igorno-alignssl_restart_20260922/svpg_truth_prepare_20261007_02/prepared/eligible_truth.vcf \
 --protocol-path metadata_census_protocol_v2.json \
 --protocol-sha256 b1f619bccc1d6728048da6165a5c872d0f4d6e38c2b4b5fd43dd42134acdf0d4 \
 --report-path metadata_census.json > stdout.log 2> stderr.log
test "$(stat -c %s metadata_census.json)" -le 65536
test "$(stat -c %s stdout.log)" -le 65536
test "$(stat -c %s stderr.log)" -le 16384
test "$(stat -c %s command_run.log)" -le 16384
output_bundle_bytes=$(( $(stat -c %s metadata_census.json) + $(stat -c %s stdout.log) + $(stat -c %s stderr.log) + $(stat -c %s command_run.log) ))
test "$output_bundle_bytes" -le 131072
