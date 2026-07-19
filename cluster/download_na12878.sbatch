#!/bin/bash
#SBATCH --job-name=dl_na12878
#SBATCH --partition=amd_256M
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=12:00:00
#SBATCH --output=/scratch/igorno-alignssl_sv/logs/dl_na12878_%j.out
#SBATCH --error=/scratch/igorno-alignssl_sv/logs/dl_na12878_%j.err

set -euo pipefail
WS=/scratch/igorno-alignssl_sv
DEST=$WS/bam_extra
mkdir -p $DEST
cd $DEST

BASE="https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/data/NA12878/high_coverage_alignment"
BAM="NA12878.mapped.ILLUMINA.bwa.CEU.high_coverage_pcr_free.20130906.bam"

echo "[$(date)] START download $BAM"
# -c = resume if partially downloaded; retry on transient failures
wget -c --tries=20 --waitretry=15 --read-timeout=60 -O "$BAM"     "$BASE/$BAM"
echo "[$(date)] BAM done, size: $(stat -c %s "$BAM") bytes"
wget -c --tries=20 --waitretry=15 --read-timeout=60 -O "$BAM.bai" "$BASE/$BAM.bai"
echo "[$(date)] index done"

# integrity: samtools quickcheck (from bioinfo env)
source /home/igorno/miniconda3/etc/profile.d/conda.sh
conda activate bioinfo
samtools quickcheck "$BAM" && echo "[$(date)] quickcheck PASS" || { echo "quickcheck FAIL"; exit 1; }
echo "[$(date)] ALL DONE"
