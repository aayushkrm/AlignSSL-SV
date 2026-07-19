#!/bin/bash
#SBATCH --job-name=extract_pretrain
#SBATCH --partition=amd_256M
#SBATCH --time=720
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --output=/scratch/igorno-alignssl_sv/logs/extractpt_%j.out
#SBATCH --error=/scratch/igorno-alignssl_sv/logs/extractpt_%j.err
set -eo pipefail
source /home/igorno/miniconda3/etc/profile.d/conda.sh
conda activate deepsv2_new

WS=/scratch/igorno-alignssl_sv
CODE=$WS/code
DATA=/beegfs/datasets/ws/ws1/igorno-genomes_1000_2
REF=$DATA/fasta/hs37d5.fa
B1=$DATA/bam/high_coverage/NA19238.mapped.ILLUMINA.bwa.YRI.high_coverage_pcr_free.20130924.bam
B2=$DATA/bam/high_coverage/NA19625.wgs.ILLUMINA.bwa.ASW.high_cov_pcr_free.20140203.bam
IDX1=$WS/bam_idx/NA19238.YRI.bam.bai
IDX2=$WS/bam_idx/NA19625.ASW.bam.bai
OUT=$WS/tensors_pretrain
mkdir -p $OUT
cd $CODE
export PYTHONPATH=$CODE

# unlabeled windows on TRAIN chroms only (pretraining must not see test chroms)
echo "=== NA19238 pretrain windows ==="
python scripts/extract_pretrain.py \
    --bam "$B1" --bai "$IDX1" --fasta "$REF" \
    --sample NA19238 --split train --out-dir $OUT \
    --n-windows 40000 --win-width 256 --max-rows 64 \
    --bin-sizes 1,2,4,8,16,32,64 \
    --bin-weights 0.35,0.25,0.15,0.10,0.08,0.05,0.02 --shard-size 2048 &
p1=$!
echo "=== NA19625 pretrain windows ==="
python scripts/extract_pretrain.py \
    --bam "$B2" --bai "$IDX2" --fasta "$REF" \
    --sample NA19625 --split train --out-dir $OUT \
    --n-windows 40000 --win-width 256 --max-rows 64 \
    --bin-sizes 1,2,4,8,16,32,64 \
    --bin-weights 0.35,0.25,0.15,0.10,0.08,0.05,0.02 --shard-size 2048 &
p2=$!
wait $p1; r1=$?
wait $p2; r2=$?
echo "DONE NA19238=$r1 NA19625=$r2"
ls -la $OUT | head; cat $OUT/pretrain_manifest_*.tsv 2>/dev/null | tail
test $r1 -eq 0 && test $r2 -eq 0
