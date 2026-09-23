#!/bin/bash
#SBATCH --job-name=alignssl-reference-map
#SBATCH --account=stud
#SBATCH --partition=amd_256M
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/igorno-alignssl_restart_20260922/hgsvc-noalt-reference/full_difference_map_%j.out
set -euo pipefail

scratch=/scratch/igorno-alignssl_restart_20260922
export ALIGNSSL_HGSVC_FASTA="$scratch/hgsvc-noalt-reference/hg38.no_alt.fa.gz"
export ALIGNSSL_OUT="$scratch/hgsvc-noalt-reference"
export ALIGNSSL_AUDIT_SCRIPT="$scratch/compare_reference_contig.py"
export ALIGNSSL_SAMTOOLS=/home/igorno/miniconda3/envs/bioinfo/bin/samtools

bash "$scratch/audit_reference_differences.sh"
