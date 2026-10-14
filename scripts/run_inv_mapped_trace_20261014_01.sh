#!/usr/bin/env bash
# One read-only regional census; no caller, model or study-index creation.
set -Eeuo pipefail
umask 077
bundle=/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/inv_mapped_trace_20261014_01
python=/beegfs/datasets/home/igorno/alignssl_restart_20260922/venvs/hg002_intake_check_20261010/bin/python
bam=/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/hg002_dna_s1a_20261010_01/HG002_WGS.haplotagged.bam
[[ -n "${SLURM_JOB_ID:-}" && "${SLURM_CPUS_PER_TASK:-}" == 1 && "${SLURM_JOB_NUM_NODES:-}" == 1 ]]
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && -d "$bundle" && ! -e "$bundle/case" && ! -e "$bundle/fixture" ]]
cd "$bundle"
finish() {
  local rc=$?
  trap - EXIT
  printf 'exit_code=%s\ncompleted_utc=%s\n' "$rc" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > exit-status.txt
  exit "$rc"
}
trap finish EXIT
printf 'job_id=%s\nstarted_utc=%s\nnode=%s\n' "$SLURM_JOB_ID" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(hostname)" > execution.txt
sha256sum -c SHA256SUMS > bundle-check.txt
[[ "$(stat -c %s "$bam")" == 48727325910 && "$(stat -c %s "$bam.bai")" == 21582928 ]]
"$python" -B -c 'import sys,pysam; assert pysam.__version__=="0.24.1"; print(sys.version); print(pysam.__version__)' > runtime.txt
mkdir fixture
timeout --signal=TERM --kill-after=10s 90s "$python" -B check_inv_trace_pysam_fixture.py \
  --extractor extract_inv_mapped_case_input.py --reference-json reference.json --output-dir fixture > fixture.stdout.txt 2> fixture.stderr.txt
mkdir case
timeout --signal=TERM --kill-after=10s 140s "$python" -B extract_inv_mapped_case_input.py \
  --bam "$bam" --reference-json reference.json --output-dir case > case.stdout.txt 2> case.stderr.txt
"$python" -B -c 'import json,pathlib; p=pathlib.Path("case"); m=json.loads((p/"manifest.json").read_text()); assert m["status"]=="COMPLETE" and m["case_region_eof_reached"]; assert sum(x.stat().st_size for x in p.iterdir())<=10*1024**2; print("complete_region_and_total_output_cap=PASS")' > case-check.txt
sha256sum case/alignments.jsonl case/manifest.json fixture/fixture-check.json > output-sha256sums.txt
