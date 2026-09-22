#!/bin/bash
#SBATCH --job-name=alignssl-giab-v5
#SBATCH --account=stud
#SBATCH --partition=amd_256M
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=01:00:00
set -euo pipefail

: "${ALIGNSSL_OUT:?Set ALIGNSSL_OUT to a fresh output directory}"
if [[ -e "$ALIGNSSL_OUT" && "${ALIGNSSL_VERIFY_ONLY:-0}" != 1 ]]; then
  echo "Refusing to overwrite existing output: $ALIGNSSL_OUT" >&2
  exit 1
fi
if [[ ! -d "$ALIGNSSL_OUT" && "${ALIGNSSL_VERIFY_ONLY:-0}" == 1 ]]; then
  echo "No staged directory to verify: $ALIGNSSL_OUT" >&2
  exit 1
fi

release_url=https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q
mkdir -p "$ALIGNSSL_OUT"
cd "$ALIGNSSL_OUT"
if [[ "${ALIGNSSL_VERIFY_ONLY:-0}" != 1 ]]; then
  for name in \
    HG002_GRCh37_v5.0q_stvar.benchmark.bed \
    HG002_GRCh37_v5.0q_stvar.vcf.gz \
    HG002_GRCh37_v5.0q_stvar.vcf.gz.tbi \
    NIST_HG002_v5.0q_variant-benchmarksets_README.md \
    checksum.md5; do
    curl --fail --location --retry 4 --retry-delay 5 \
      --output "${name}.download" "${release_url}/${name}"
    mv "${name}.download" "$name"
  done
fi

grep -E 'HG002_GRCh37_v5\.0q_stvar\.(benchmark\.bed|vcf\.gz|vcf\.gz\.tbi)' \
  checksum.md5 | md5sum --check --status
expected_readme_md5=$(awk '$2 == "NIST_HG002_v5.0q_variant-benchmarksets_README.md" {print $1}' checksum.md5)
actual_readme_md5=$(md5sum NIST_HG002_v5.0q_variant-benchmarksets_README.md | cut -d ' ' -f 1)
if [[ "$actual_readme_md5" != "$expected_readme_md5" ]]; then
  printf 'NIST README checksum mismatch; data files verified.\nexpected_md5=%s\nactual_md5=%s\n' \
    "$expected_readme_md5" "$actual_readme_md5" | tee README_CHECKSUM_NOTE.txt >&2
fi
gzip -t HG002_GRCh37_v5.0q_stvar.vcf.gz
sha256sum HG002_GRCh37_v5.0q_stvar.benchmark.bed \
  HG002_GRCh37_v5.0q_stvar.vcf.gz \
  HG002_GRCh37_v5.0q_stvar.vcf.gz.tbi \
  NIST_HG002_v5.0q_variant-benchmarksets_README.md \
  checksum.md5 > SHA256SUMS
printf 'source=%s\nversion=v5.0q\nassembly=GRCh37\npurpose=development_benchmark\n' "$release_url" > SOURCE.txt
echo "Verified three GIAB HG002 v5.0q GRCh37 SV data files at $ALIGNSSL_OUT"
