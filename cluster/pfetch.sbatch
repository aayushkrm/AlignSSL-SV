#!/bin/bash
#SBATCH --job-name=pf_SAMPLE
#SBATCH --partition=amd_256M
#SBATCH --account=stud
#SBATCH --time=0
#SBATCH --cpus-per-task=16
#SBATCH --mem=8G
#SBATCH --output=/scratch/igorno-alignssl_sv/logs/pfetch_SAMPLE_%j.out
#SBATCH --error=/scratch/igorno-alignssl_sv/logs/pfetch_SAMPLE_%j.err
set -u
source /home/igorno/miniconda3/etc/profile.d/conda.sh
conda activate bioinfo
which samtools; samtools --version | head -1
BASE=/scratch/igorno-alignssl_sv
bash $BASE/code/scripts/pfetch_bam.sh "SAMPLE" "FNAME" "$BASE/bam_extra" 16
