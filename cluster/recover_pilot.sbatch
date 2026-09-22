#!/bin/bash
#SBATCH --job-name=alignssl-recover
#SBATCH --account=stud
#SBATCH --partition=amd_256M
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=04:00:00
set -euo pipefail
: "${ALIGNSSL_CODE:?Set ALIGNSSL_CODE to the versioned source snapshot}"
: "${ALIGNSSL_RUN:?Set ALIGNSSL_RUN to a fresh absolute output directory}"
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
cd "$ALIGNSSL_CODE"
/home/igorno/miniconda3/envs/deepsv2_new/bin/python scripts/recover_pilot_inputs.py \
  --out-dir "$ALIGNSSL_RUN" --reference
