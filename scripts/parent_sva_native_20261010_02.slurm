#!/usr/bin/env bash
#SBATCH --job-name=alignssl-parent-sva-02
#SBATCH --partition=amd_256M
#SBATCH --cpus-per-task=3
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --chdir=/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/parent_sva_native_20261010_02/bundle
#SBATCH --output=/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/parent_sva_native_20261010_02/bundle/slurm.%j.out
#SBATCH --error=/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/parent_sva_native_20261010_02/bundle/slurm.%j.err
set -euo pipefail
exec /beegfs/datasets/home/igorno/alignssl_restart_20260922/venvs/sniffles281_20261010/bin/python -u \
  scripts/run_parent_sva_diagnostic.py \
  --samtools /beegfs/datasets/home/igorno/miniconda3/envs/bioinfo/bin/samtools \
  --output /beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/parent_sva_native_20261010_02
