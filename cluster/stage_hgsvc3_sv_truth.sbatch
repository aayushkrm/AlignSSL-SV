#!/bin/bash
#SBATCH --job-name=alignssl-hgsvc3-truth
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

release_url=https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0
vcf_name=variants_GRCh38_sv_insdel_alt_HGSVC2024v1.0.vcf.gz
mkdir -p "$ALIGNSSL_OUT"
cd "$ALIGNSSL_OUT"
if [[ "${ALIGNSSL_VERIFY_ONLY:-0}" != 1 ]]; then
  for name in README_Variant_Calls_1.0.md MANIFEST_Variant_Calls_1.0; do
    curl --silent --show-error --fail --location --retry 4 \
      --output "${name}.download" "${release_url}/${name}"
    mv "${name}.download" "$name"
  done
  for name in "$vcf_name" "$vcf_name.tbi"; do
    curl --silent --show-error --fail --location --retry 4 \
      --output "${name}.download" "${release_url}/GRCh38/${name}"
    mv "${name}.download" "$name"
  done
fi

awk -v vcf="$vcf_name" '$1 == "./GRCh38/" vcf ||
  $1 == "./GRCh38/" vcf ".tbi" ||
  $1 == "./README_Variant_Calls_1.0.md" {
  name=$1; sub(/^.*\//, "", name); print $3 "  " name
}' MANIFEST_Variant_Calls_1.0 | md5sum --check
gzip -t "$vcf_name"
sha256sum "$vcf_name" "$vcf_name.tbi" \
  README_Variant_Calls_1.0.md MANIFEST_Variant_Calls_1.0 > SHA256SUMS
printf 'source=%s\nrelease=HGSVC3 Variant Calls 1.0\nassembly=GRCh38-NoALT\npurpose=cohort_feasibility\n' \
  "$release_url" > SOURCE.txt
echo "Verified HGSVC3 GRCh38 SV VCF and index at $ALIGNSSL_OUT"
