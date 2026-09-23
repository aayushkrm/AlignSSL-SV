#!/bin/bash
# Recompare the 18 HGSVC/IGSR-distinct contigs using both frozen FASTAs.
# Output is separate from the historical URL-based map; never overwrite it.
#SBATCH --job-name=alignssl-frozen-reference-map
#SBATCH --account=stud
#SBATCH --partition=amd_256M
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/igorno-alignssl_restart_20260922/reference-ambiguity/frozen_compare_%j.out
set -euo pipefail

scratch=/scratch/igorno-alignssl_restart_20260922
hgsvc="$scratch/hgsvc-noalt-reference/hg38.no_alt.fa.gz"
igsr_dir="$scratch/igsr-reference"
igsr="$igsr_dir/GRCh38_full_analysis_set_plus_decoy_hla.fa"
out="$scratch/reference-ambiguity/frozen-comparison-${SLURM_JOB_ID}"
samtools=/home/igorno/miniconda3/envs/bioinfo/bin/samtools
comparison="$scratch/compare_reference_contig.py"

test ! -e "$out"
test -s "$comparison"
(cd "$igsr_dir" && sha256sum --check SHA256SUMS)
printf '%s  %s\n' \
  90f1dcdb28a81ac26f6eaa1afc285e7ec459c195c2134fb25af0e82be2f11729 \
  "$hgsvc" | sha256sum --check
mkdir -p "$out"

for contig in chr1 chr2 chr3 chr5 chr6 chr7 chr9 chr10 chr12 chr13 \
              chr14 chr16 chr17 chr19 chr21 chr22 chrX chrY; do
  timeout 1200 nice -n 10 python3 "$comparison" \
    --samtools "$samtools" --left-fasta "$hgsvc" \
    --right-fasta "$igsr" --contig "$contig" \
    --out "$out/${contig}_base_differences_full.json" \
    --out-bed "$out/${contig}_base_differences.bed"
done

(cd "$out" && sha256sum -- *.bed *.json > SHA256SUMS)
printf 'purpose=frozen-reference-provenance-rerun\nhgsvc_sha256=%s\nigsr_sha256=%s\njob_id=%s\n' \
  90f1dcdb28a81ac26f6eaa1afc285e7ec459c195c2134fb25af0e82be2f11729 \
  3b103f4742abfd54938fb0333e19ad067635c8eb86f1dbf0ce44b165c4292b50 \
  "$SLURM_JOB_ID" > "$out/SOURCE.txt"
echo "Frozen comparison complete: $out"
