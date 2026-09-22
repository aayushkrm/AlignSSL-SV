#!/usr/bin/env bash
# Stage the first-party HGSVC No-ALT FASTA for reference-identity checks.
set -euo pipefail

: "${ALIGNSSL_OUT:?Set ALIGNSSL_OUT to a dedicated reference directory}"
source_url=https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC2/technical/reference/20200513_hg38_NoALT
mkdir -p "$ALIGNSSL_OUT"
cd "$ALIGNSSL_OUT"

for name in README_20200513_hg38_NoALT.txt MANIFEST_20200513_hg38_NoALT.txt \
            hg38.no_alt.fa.gz hg38.no_alt.fa.gz.fai hg38.no_alt.fa.gz.gzi; do
  if [[ ! -s "$name" ]]; then
    curl --silent --show-error --fail --location --retry 4 --retry-delay 5 \
      --continue-at - \
      --output "${name}.download" "${source_url}/${name}"
    mv "${name}.download" "$name"
  fi
done

# The published manifest refers to the README without its .txt suffix.
awk '$1 == "hg38.no_alt.fa.gz" || $1 == "hg38.no_alt.fa.gz.fai" ||
     $1 == "hg38.no_alt.fa.gz.gzi" {print $3 "  " $1}' \
  MANIFEST_20200513_hg38_NoALT.txt | md5sum --check
expected_readme_md5=$(awk '$1 == "README_20200513_hg38_NoALT" {print $3}' \
  MANIFEST_20200513_hg38_NoALT.txt)
actual_readme_md5=$(md5sum README_20200513_hg38_NoALT.txt | cut -d ' ' -f 1)
if [[ "$actual_readme_md5" != "$expected_readme_md5" ]]; then
  echo "Published README MD5 mismatch" >&2
  exit 1
fi
gzip -t hg38.no_alt.fa.gz
sha256sum hg38.no_alt.fa.gz hg38.no_alt.fa.gz.fai hg38.no_alt.fa.gz.gzi \
  > SHA256SUMS
printf 'source=%s\npurpose=HGSVC3_reference_reconciliation_only\n' \
  "$source_url" > SOURCE.txt
echo "Verified HGSVC no-ALT reference in $ALIGNSSL_OUT"
