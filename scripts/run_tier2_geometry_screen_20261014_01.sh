#!/usr/bin/env bash
# One bounded existing-input geometry screen; no genomic acquisition or remapping.
set -Eeuo pipefail
umask 077
bundle=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/tier2_geometry_screen_20261014_01
python=/beegfs/datasets/home/igorno/alignssl_restart_20260922/venvs/hg002_intake_check_20261010/bin/python
binary=/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/breakinator_runtime_20261014_01/breakinator-v1.1.1/bin/breakinator
bam=/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/hg002_dna_s1a_20261010_01/HG002_WGS.haplotagged.bam
[[ -n "${SLURM_JOB_ID:-}" && "${SLURM_CPUS_PER_TASK:-}" == 1 && "${SLURM_JOB_NUM_NODES:-}" == 1 ]]
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && -d "$bundle" && ! -e "$bundle/execution.txt" && ! -e "$bundle/collection" ]]
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
[[ "$(sha256sum "$binary" | cut -d ' ' -f 1)" == 049948306338709b9b4e3fa7e9750770bbbb659558723472c1507b821b84e29a ]]
[[ "$(stat -c %s "$bam")" == 48727325910 && "$(stat -c %s "$bam.bai")" == 21582928 ]]
"$python" -B -c 'import sys,pysam; assert pysam.__version__=="0.24.1"; print(sys.version); print(pysam.__version__)' > runtime.txt
mkdir controls
timeout --signal=TERM --kill-after=10s 130s "$python" -B breakinator_native_controls.py \
  --binary "$binary" --output-dir controls > controls.stdout.txt 2> controls.stderr.txt
mkdir collection
timeout --signal=TERM --kill-after=10s 360s "$python" -B collect_tier2_geometry_screen.py \
  --bam "$bam" --plan plan.json --output-dir collection > collection.stdout.txt 2> collection.stderr.txt
"$python" -B -c 'import json,pathlib; m=json.loads(pathlib.Path("collection/manifest.json").read_text()); assert m["status"]=="COMPLETE" and m["fetch_complete"] and m["groups_complete"] and m["source_stats_stable"]; assert len(m["events"])==53; print("complete_collection_gate=PASS")' > collection-check.txt
timeout --signal=TERM --kill-after=10s 180s "$binary" -i collection/namesorted.bam \
  -o native-report.txt --rcoord -t 1 > native.stdout.txt 2> native.stderr.txt
"$python" -B -c 'import json,pathlib; from breakinator_native_controls import parse_native_report; p=pathlib.Path("native-report.txt"); assert p.stat().st_size<=32*1024**2; calls=parse_native_report(p.read_bytes()); print(json.dumps({"native_report_rows":len(calls),"interpretation":"Native geometry classifications only; no authenticated artifact or allele-support claim"})); total=sum(x.stat().st_size for x in pathlib.Path(".").rglob("*") if x.is_file()); assert total<=1024**3' > native-parse-check.json
sha256sum collection/raw_subset.bam collection/namesorted.bam collection/groups.jsonl \
  collection/manifest.json native-report.txt native.stdout.txt native.stderr.txt \
  controls/run.json > output-sha256sums.txt
