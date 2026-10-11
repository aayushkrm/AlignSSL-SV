#!/usr/bin/env bash
#SBATCH --job-name=alignssl-parent-sva-01
#SBATCH --partition=amd_256M
#SBATCH --cpus-per-task=3
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --chdir=/home/igorno/alignssl_restart_20260922/experiments/parent_sva_native_20261010_01/bundle
#SBATCH --output=/home/igorno/alignssl_restart_20260922/experiments/parent_sva_native_20261010_01/bundle/slurm.%j.out
#SBATCH --error=/home/igorno/alignssl_restart_20260922/experiments/parent_sva_native_20261010_01/bundle/slurm.%j.err
set -euo pipefail
exec /home/igorno/alignssl_restart_20260922/venvs/sniffles281_20261010/bin/python -u \
  scripts/run_parent_sva_diagnostic.py \
  --samtools /home/igorno/miniconda3/envs/bioinfo/bin/samtools \
  --output /scratch/igorno-alignssl_restart_20260922/experiments/parent_sva_native_20261010_01
