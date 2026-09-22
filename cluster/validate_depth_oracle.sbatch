#!/bin/bash
#SBATCH --job-name=alignssl-depth-oracle
#SBATCH --account=stud
#SBATCH --partition=amd_256M
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
set -euo pipefail
: "${ALIGNSSL_CODE:?Set ALIGNSSL_CODE to the source snapshot}"
: "${ALIGNSSL_DATA:?Set ALIGNSSL_DATA to the recovered pilot directory}"
: "${ALIGNSSL_OUT:?Set ALIGNSSL_OUT to a new result JSON path}"
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export PYTHONPATH="$ALIGNSSL_CODE${PYTHONPATH:+:$PYTHONPATH}"
cd "$ALIGNSSL_CODE"
/home/igorno/miniconda3/envs/deepsv2_new/bin/python \
  scripts/validate_depth_oracle.py \
  --bam "$ALIGNSSL_DATA/HG002.pilot.bam" \
  --fasta "$ALIGNSSL_DATA/hs37d5.fa.gz" \
  --out "$ALIGNSSL_OUT"
