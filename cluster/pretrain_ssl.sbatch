#!/bin/bash
#SBATCH --job-name=ssl_pretrain
#SBATCH --partition=gpu_A100
#SBATCH --gres=gpu:1
#SBATCH --time=480
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --output=/scratch/igorno-alignssl_sv/logs/ssl_%j.out
#SBATCH --error=/scratch/igorno-alignssl_sv/logs/ssl_%j.err
set -eo pipefail
source /home/igorno/miniconda3/etc/profile.d/conda.sh
conda activate deepsv2_new
WS=/scratch/igorno-alignssl_sv
cd $WS/code; export PYTHONPATH=$WS/code
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

python scripts/pretrain_ssl.py \
    --shard-dir $WS/tensors_pretrain \
    --glob 'pretrain_*.npz' \
    --split train \
    --out $WS/ckpt/encoder_ssl.pt \
    --epochs 100 \
    --batch-size 256 \
    --lr 1.5e-4 \
    --mask-ratio 0.6 \
    --view-keep 0.5 \
    --num-workers 4 \
    --seed 0
echo "SSL DONE"
ls -la $WS/ckpt/
