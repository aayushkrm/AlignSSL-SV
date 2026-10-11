#!/usr/bin/env bash
# One exact Linux launch. Code, helper and JSON must have separately approved pins.
set -euo pipefail
run_dir=/scratch/igorno-alignssl_restart_20260922/svpg_metadata_census_20261008_01
cd "$run_dir"
test ! -e metadata_census.json
test ! -e command_run.log
test ! -e stdout.log
test ! -e stderr.log
printf '%s\n' \
 'deae6f39416eabc5dd7b65131b24dc5d57a9a2341bc16153d013d743cd193649  diagnose_released_truth_metadata.py' \
 '4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93  released_truth_units.py' \
 'e0a8cdf1605c3f37d9fde2302702180bfea704e1f9f941120ded705e633c9cb8  metadata_census_protocol_v1.json' | sha256sum -c -
ulimit -t 60
ulimit -v 4194304
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
/usr/bin/time -v -o command_run.log timeout -k 5s 120s \
 /home/igorno/miniconda3/envs/truvari_env/bin/python diagnose_released_truth_metadata.py \
 --truth-path /scratch/igorno-alignssl_restart_20260922/svpg_truth_prepare_20261007_02/prepared/eligible_truth.vcf \
 --protocol-path metadata_census_protocol_v1.json \
 --protocol-sha256 e0a8cdf1605c3f37d9fde2302702180bfea704e1f9f941120ded705e633c9cb8 \
 --report-path metadata_census.json > stdout.log 2> stderr.log
test "$(stat -c %s metadata_census.json)" -le 65536
test "$(stat -c %s stdout.log)" -le 65536
test "$(stat -c %s stderr.log)" -le 16384
test "$(stat -c %s command_run.log)" -le 16384
