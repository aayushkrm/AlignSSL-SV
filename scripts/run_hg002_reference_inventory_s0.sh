#!/usr/bin/env bash
# S0 reference declarations/index-cost diagnostic only. No DNA/RNA/caller.
set -Eeuo pipefail
umask 077
ulimit -c 0
project=/beegfs/datasets/home/igorno/alignssl_restart_20260922
scratch=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922
bundle="$project/bundles/hg002_reference_inventory_s0_20261011_01"
out="$scratch/experiments/hg002_reference_inventory_s0_20261011_01"
[[ -n "${SLURM_JOB_ID:-}" && "${SLURM_CPUS_PER_TASK:-}" == 1 && "${SLURM_JOB_NUM_NODES:-}" == 1 ]]
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && ! -e "$out" && ! -L "$out" ]]
cd "$bundle"
printf '%s  %s\n' \
  55babef7ad53e0908162b7d4f1dfd668450cc86b0ba254ffa05b152d0cb03f0e analysis/hg002_reference_inventory.py \
  7ee2c052e9b0c112bf75e6a2fdddbfd63ca49d3665ca5725ed4befed30001b30 tests/test_hg002_reference_inventory.py \
  197a54c9dbf6dd3f7f9264a3eb090d0646f08d05fdb7dfe99ae2c337f0064f4e analysis/hg002_cds_overlap_cohort.py | sha256sum -c
scontrol show job "$SLURM_JOB_ID" --oneliner
printf 'wrapper_sha256=%s\nstarted_utc=%s\n' "$(sha256sum "$0" | awk '{print $1}')" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
export PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0
python="$project/venvs/hg002_intake_check_20261010/bin/python"
"$python" -B -m unittest discover -s tests -p test_hg002_reference_inventory.py -v
# Linux Bash -f units are KiB. A too-large JSON fails rather than overflowing
# the reserved small-artifact account. Preserve partials; do not rerun/crop.
ulimit -f 2048
"$python" -B -m analysis.hg002_reference_inventory \
  --source "$project/experiments/hg002_reference_expand_20261010_01/gencode.v50.primary_assembly.annotation.gtf" \
  --output-dir "$out" --deadline-seconds 840 --checkpoint-seconds 15 \
  --measure-existing-index
du -sb "$out"
sha256sum "$out/manifest.json" "$out/inventory.json"
