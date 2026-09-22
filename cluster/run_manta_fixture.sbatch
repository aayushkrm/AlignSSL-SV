#!/bin/bash
#SBATCH --job-name=alignssl-manta-fixture
#SBATCH --account=stud
#SBATCH --partition=debug
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
set -euo pipefail

: "${ALIGNSSL_FIXTURE:?Set ALIGNSSL_FIXTURE to the HG002 pilot directory}"
: "${ALIGNSSL_IMAGE:?Set ALIGNSSL_IMAGE to the pinned Manta SIF}"
: "${ALIGNSSL_REGIONS:?Set ALIGNSSL_REGIONS to pilot_call_regions.bed}"
: "${ALIGNSSL_OUT:?Set ALIGNSSL_OUT to a fresh output directory}"
if [[ -e "$ALIGNSSL_OUT" ]]; then
  echo "Refusing to overwrite existing output: $ALIGNSSL_OUT" >&2
  exit 1
fi

bioinfo_bin=/home/igorno/miniconda3/envs/bioinfo/bin
mkdir -p "$ALIGNSSL_OUT"
gzip -dc "$ALIGNSSL_FIXTURE/hs37d5.fa.gz" > "$ALIGNSSL_OUT/hs37d5.fa"
"$bioinfo_bin/samtools" faidx "$ALIGNSSL_OUT/hs37d5.fa"
"$bioinfo_bin/bgzip" -c "$ALIGNSSL_REGIONS" > "$ALIGNSSL_OUT/call_regions.bed.gz"
"$bioinfo_bin/tabix" -p bed "$ALIGNSSL_OUT/call_regions.bed.gz"

singularity exec --bind /scratch:/scratch "$ALIGNSSL_IMAGE" configManta.py \
  --bam "$ALIGNSSL_FIXTURE/HG002.pilot.bam" \
  --referenceFasta "$ALIGNSSL_OUT/hs37d5.fa" \
  --callRegions "$ALIGNSSL_OUT/call_regions.bed.gz" \
  --runDir "$ALIGNSSL_OUT/manta"
singularity exec --bind /scratch:/scratch "$ALIGNSSL_IMAGE" \
  python "$ALIGNSSL_OUT/manta/runWorkflow.py" -m local -j "${SLURM_CPUS_PER_TASK:-4}"

for name in candidateSV.vcf.gz diploidSV.vcf.gz; do
  vcf="$ALIGNSSL_OUT/manta/results/variants/$name"
  test -s "$vcf"
  gzip -t "$vcf"
  gzip -dc "$vcf" | awk -v name="$name" '!/^#/ {n++} END {print name, n}'
done

sha256sum "$ALIGNSSL_IMAGE" "$ALIGNSSL_FIXTURE/HG002.pilot.bam" \
  "$ALIGNSSL_REGIONS" "$ALIGNSSL_OUT/hs37d5.fa" \
  "$ALIGNSSL_OUT/manta/results/variants/candidateSV.vcf.gz" \
  "$ALIGNSSL_OUT/manta/results/variants/diploidSV.vcf.gz" \
  > "$ALIGNSSL_OUT/SHA256SUMS"
printf 'purpose=engineering_fixture_only\ncaller=Manta 1.6.0\nreference=hs37d5\n' \
  > "$ALIGNSSL_OUT/SOURCE.txt"
