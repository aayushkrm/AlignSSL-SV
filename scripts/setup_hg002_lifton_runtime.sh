#!/usr/bin/env bash
# Routine isolated software setup; no genomic inputs or analysis.
set -euo pipefail
project_home=/beegfs/datasets/home/igorno/alignssl_restart_20260922
project_scratch=/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922
runtime="$project_scratch/venvs/lifton1014_20261010"
record="$project_scratch/experiments/hg002_lifton_setup_20261010_02"
python_bin="$project_home/venvs/sniffles281_20261010/bin/python"
source_commit=8378f8e4a3d8404c94d801c285a2c74291e893b7

# Never reuse or overwrite a previous attempt, including a partial venv.
test ! -e "$runtime"
test ! -e "$record"
test -x "$python_bin"
mkdir -p "$project_scratch/venvs" "$project_scratch/experiments"
mkdir "$record"
exec > >(tee "$record/setup.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$record/exit-status.txt"' EXIT
date -u
sha256sum "$0"
printf 'source_commit=%s\nSLURM_JOB_ID=%s\n' "$source_commit" "${SLURM_JOB_ID:-unset}"
"$python_bin" -VV
"$python_bin" -m venv "$runtime"
"$runtime/bin/python" -m pip --disable-pip-version-check wheel --no-cache-dir \
  --wheel-dir "$record/wheelhouse" \
  "https://github.com/Kuanhao-Chao/LiftOn/archive/$source_commit.tar.gz"
"$runtime/bin/python" -m pip --disable-pip-version-check install --no-index \
  --find-links "$record/wheelhouse" lifton==1.0.14
"$runtime/bin/python" -m pip check
"$runtime/bin/python" -m pip freeze > "$record/pip-freeze.txt"
"$runtime/bin/lifton" -V > "$record/version.txt"
"$runtime/bin/lifton" -h > "$record/help.txt"
"$runtime/bin/python" -c 'import parasail, pysam, pyarrow, duckdb, Bio, numpy, gffutils; print("native-extension imports OK")'
for flag in polish cds copies validate-output; do
  if ! grep -q -- "-$flag" "$record/help.txt"; then
    printf 'Required native interface flag missing: %s\n' "$flag" >&2
    exit 1
  fi
done
date -u
# Version/help/imports do not establish successful native genome annotation.
# Back up records/wheels off expiring scratch after completion. Reinstall the
# wheels into a home venv on the writable login host; do not relocate shebangs.
