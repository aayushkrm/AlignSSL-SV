#!/bin/bash
#SBATCH --job-name=ft_eval
#SBATCH --partition=gpu_A100
#SBATCH --gres=gpu:1
#SBATCH --time=480
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --output=/scratch/igorno-alignssl_sv/logs/ft_%j.out
#SBATCH --error=/scratch/igorno-alignssl_sv/logs/ft_%j.err
set -eo pipefail
source /home/igorno/miniconda3/etc/profile.d/conda.sh
conda activate deepsv2_new
WS=/scratch/igorno-alignssl_sv
cd $WS/code; export PYTHONPATH=$WS/code
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

# Headline experiment: label-efficiency curve (pretrained vs scratch) +
# temperature calibration + length-stratified recall (amendment 1).
python scripts/finetune_eval.py \
    --shard-dir $WS/tensors \
    --encoder $WS/ckpt/encoder_ssl.pt \
    --out $WS/ckpt/results_alignssl.json \
    --epochs 30 \
    --batch-size 128 \
    --lr 3e-4 \
    --label-fracs 0.01,0.05,0.1,0.25,0.5,1.0 \
    --num-workers 4 \
    --seed 0
echo "FT DONE"
cat $WS/ckpt/results_alignssl.json | python -c "import sys,json; r=json.load(sys.stdin); [print(x['frac'], {k:round(v.get('F1',0),3) for k,v in x.items() if isinstance(v,dict)}) for x in r['label_efficiency']]"
