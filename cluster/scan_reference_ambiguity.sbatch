#!/bin/bash
#SBATCH --job-name=alignssl-reference-ambiguity
#SBATCH --account=stud
#SBATCH --partition=amd_256M
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/igorno-alignssl_restart_20260922/reference-ambiguity/scan_%j.out
set -euo pipefail

scratch=/scratch/igorno-alignssl_restart_20260922
out="$scratch/reference-ambiguity"
igsr="$scratch/igsr-reference"
hgsvc="$scratch/hgsvc-noalt-reference"
name=GRCh38_full_analysis_set_plus_decoy_hla.fa

cd "$igsr"
sha256sum --check SHA256SUMS
printf '%s  %s\n' \
  90f1dcdb28a81ac26f6eaa1afc285e7ec459c195c2134fb25af0e82be2f11729 \
  "$hgsvc/hg38.no_alt.fa.gz" | sha256sum --check

python3 "$scratch/scan_reference_ambiguity.py" \
  --fasta "$hgsvc/hg38.no_alt.fa.gz" \
  --expected-m5-json "$hgsvc/all_contig_m5.json" \
  --out-bed "$out/hgsvc_non_acgt.bed" --out-json "$out/hgsvc_non_acgt.json"
python3 "$scratch/scan_reference_ambiguity.py" \
  --fasta "$igsr/$name" --expected-dict "$igsr/${name%.fa}.dict" \
  --out-bed "$out/igsr_non_acgt.bed" --out-json "$out/igsr_non_acgt.json"
sha256sum "$out"/*.bed "$out"/*.json > "$out/SHA256SUMS"
