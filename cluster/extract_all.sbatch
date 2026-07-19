#!/bin/bash
#SBATCH --job-name=extract_tensors
#SBATCH --partition=amd_256M
#SBATCH --time=720
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --output=/scratch/igorno-alignssl_sv/logs/extract_%j.out
#SBATCH --error=/scratch/igorno-alignssl_sv/logs/extract_%j.err
set -eo pipefail
source /home/igorno/miniconda3/etc/profile.d/conda.sh
conda activate deepsv2_new

WS=/scratch/igorno-alignssl_sv
CODE=$WS/code
DATA=/beegfs/datasets/ws/ws1/igorno-genomes_1000_2
REF=$DATA/fasta/hs37d5.fa
VCF=$DATA/vcf/ALL.wgs.mergedSV.v8.20130502.svs.genotypes.vcf.gz
B1=$DATA/bam/high_coverage/NA19238.mapped.ILLUMINA.bwa.YRI.high_coverage_pcr_free.20130924.bam
B2=$DATA/bam/high_coverage/NA19625.wgs.ILLUMINA.bwa.ASW.high_cov_pcr_free.20140203.bam
IDX1=$WS/bam_idx/NA19238.YRI.bam.bai
IDX2=$WS/bam_idx/NA19625.ASW.bam.bai
OUT=$WS/tensors
mkdir -p $OUT
cd $CODE
export PYTHONPATH=$CODE

echo "=== NA19238 (YRI) all chroms ==="
python scripts/extract_tensors.py \
    --bam "$B1" --bai "$IDX1" --fasta "$REF" --vcf "$VCF" \
    --sample NA19238 --split all --out-dir $OUT \
    --win-width 256 --max-rows 64 --n-neg-per-pos 3 --shard-size 1024 &
p1=$!

echo "=== NA19625 (ASW) all chroms ==="
python scripts/extract_tensors.py \
    --bam "$B2" --bai "$IDX2" --fasta "$REF" --vcf "$VCF" \
    --sample NA19625 --split all --out-dir $OUT \
    --win-width 256 --max-rows 64 --n-neg-per-pos 3 --shard-size 1024 &
p2=$!

wait $p1; r1=$?
wait $p2; r2=$?
echo "DONE NA19238=$r1 NA19625=$r2"
ls -la $OUT | head -30
cat $OUT/manifest_*.tsv 2>/dev/null | tail -20
test $r1 -eq 0 && test $r2 -eq 0
