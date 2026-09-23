#!/bin/bash
#SBATCH --job-name=alignssl-igsr-reference
#SBATCH --account=stud
#SBATCH --partition=amd_256M
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=03:00:00
#SBATCH --output=/scratch/igorno-alignssl_restart_20260922/igsr-reference/stage_%j.out
set -euo pipefail

out=/scratch/igorno-alignssl_restart_20260922/igsr-reference
source_url=https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome
name=GRCh38_full_analysis_set_plus_decoy_hla.fa
dict=GRCh38_full_analysis_set_plus_decoy_hla.dict
expected_fasta_bytes=3263683042
expected_fai_bytes=154196
expected_dict_sha256=91f7a9993b70c9c85b3a51a20b888d866cd55938ce1ccd3a325a38954d2fbdeb
mkdir -p "$out"
cd "$out"

for file in "$name" "$name.fai" "$dict"; do
  if [[ ! -s "$file" ]]; then
    curl --silent --show-error --fail --location --retry 5 --retry-delay 10 \
      --continue-at - --output "$file.download" "$source_url/$file"
    mv "$file.download" "$file"
  fi
done

[[ $(stat -c %s "$name") -eq "$expected_fasta_bytes" ]]
[[ $(stat -c %s "$name.fai") -eq "$expected_fai_bytes" ]]
printf '%s  %s\n' "$expected_dict_sha256" "$dict" | sha256sum --check
sha256sum "$name" "$name.fai" "$dict" > SHA256SUMS
md5sum "$name" "$name.fai" "$dict" > MD5SUMS
printf 'source=%s/%s\nfetched_utc=%s\nexpected_fasta_bytes=%s\nexpected_fai_bytes=%s\n' \
  "$source_url" "$name" "$(date -u +%FT%TZ)" \
  "$expected_fasta_bytes" "$expected_fai_bytes" > SOURCE.txt
echo "Verified IGSR reference snapshot in $out"
