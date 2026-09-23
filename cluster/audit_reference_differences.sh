#!/usr/bin/env bash
# Stream only contigs whose HGSVC and IGSR reference M5s differ.
set -euo pipefail

: "${ALIGNSSL_HGSVC_FASTA:?Set the publisher-verified HGSVC FASTA}"
: "${ALIGNSSL_OUT:?Set a dedicated output directory}"
: "${ALIGNSSL_AUDIT_SCRIPT:?Set the compare_reference_contig.py path}"
: "${ALIGNSSL_SAMTOOLS:?Set the samtools executable path}"
igsr_fasta=https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/GRCh38_full_analysis_set_plus_decoy_hla.fa
mkdir -p "$ALIGNSSL_OUT"

for contig in chr1 chr2 chr3 chr5 chr6 chr7 chr9 chr10 chr12 chr13 \
              chr14 chr16 chr17 chr19 chr21 chr22 chrX chrY; do
  result="$ALIGNSSL_OUT/${contig}_base_differences_full.json"
  bed="$ALIGNSSL_OUT/${contig}_base_differences.bed"
  if [[ -s "$result" && -f "$bed" ]]; then
    echo "Existing full result retained: $result and $bed"
    continue
  fi
  timeout 900 nice -n 10 python3 "$ALIGNSSL_AUDIT_SCRIPT" \
    --samtools "$ALIGNSSL_SAMTOOLS" \
    --left-fasta "$ALIGNSSL_HGSVC_FASTA" \
    --right-fasta "$igsr_fasta" \
    --contig "$contig" --out "$result" --out-bed "$bed"
done
