#!/usr/bin/env bash
# Run on the cluster login node. Compute nodes cannot write to this home path.
set -euo pipefail

if [[ -n ${SLURM_JOB_ID:-} ]]; then
  echo 'Run from a login-node shell, not inside a SLURM job.' >&2
  exit 1
fi

scratch=/scratch/igorno-alignssl_restart_20260922
archive=/home/igorno/alignssl_restart_20260922/references
igsr_source="$scratch/igsr-reference"
hgsvc_source="$scratch/hgsvc-noalt-reference"
igsr_archive="$archive/igsr-3b103f4742ab"
hgsvc_archive="$archive/hgsvc-noalt-90f1dcdb28a8"

(cd "$igsr_source" && sha256sum --check SHA256SUMS)
(cd "$hgsvc_source" && sha256sum --check SHA256SUMS)
mkdir -p "$igsr_archive" "$hgsvc_archive"

ionice -c3 nice -n 19 rsync -a --partial \
  "$igsr_source/GRCh38_full_analysis_set_plus_decoy_hla.fa" \
  "$igsr_source/GRCh38_full_analysis_set_plus_decoy_hla.fa.fai" \
  "$igsr_source/GRCh38_full_analysis_set_plus_decoy_hla.dict" \
  "$igsr_source/SHA256SUMS" "$igsr_source/MD5SUMS" \
  "$igsr_source/SOURCE.txt" "$igsr_archive/"
(cd "$igsr_archive" && sha256sum --check SHA256SUMS)

ionice -c3 nice -n 19 rsync -a --partial \
  "$hgsvc_source/hg38.no_alt.fa.gz" \
  "$hgsvc_source/hg38.no_alt.fa.gz.fai" \
  "$hgsvc_source/hg38.no_alt.fa.gz.gzi" \
  "$hgsvc_source/SHA256SUMS" "$hgsvc_source/SOURCE.txt" \
  "$hgsvc_source/MANIFEST_20200513_hg38_NoALT.txt" \
  "$hgsvc_source/README_20200513_hg38_NoALT.txt" "$hgsvc_archive/"
(cd "$hgsvc_archive" && sha256sum --check SHA256SUMS)
echo "Verified durable reference snapshots in $archive"
