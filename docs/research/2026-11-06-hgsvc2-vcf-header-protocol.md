# HGSVC2 PanGenie VCF: bounded sample-header check

## Decision and purpose

The [sample-list crosswalk](2026-11-04-paired-dna-rna-feasibility.md) found
56 of 60 RNA sample-title tokens in the HGSVC2 PanGenie source lists, but
sample-list membership is not proof of a VCF column. This check asks only
whether the named biallelic, no-SNV VCF header contains the corresponding
samples. It does not inspect variant records, genotypes, RNA values or labels.
The VCF was genotyped from high-coverage short reads against an assembly-based
panel; it is not a long-read callset for every individual or ground truth.

## Fixed source and retrieval limits

Use only the official HGSVC2 freeze-3 release file
`https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC2/release/v1.0/PanGenie_results/pangenie_merged_bi_nosnvs.vcf.gz`.
The adjacent saved release manifest declares 1,753,712,867 bytes and MD5
`003c94d1249b946f2276787dfad93e99`. Do not download or claim to verify the
whole-file checksum. Request bytes 0–262143, or at most 0–1048575 if the
first prefix cannot contain the complete header. Require HTTP 206 with the
expected starting offset; reject an unbounded 200 response without reading
its body. Record response metadata, local prefix SHA256, all route failures,
and whether the full `#CHROM` header was decoded. A cluster route may be used
if direct retrieval fails, with the same bounds. Retain any binary prefix
outside Git because it may include variant records; retain only header fields,
source metadata, hashes and matching summaries in the repository.

Match each of the 60 RNA titles by either exact VCF column equality or exact
equality to the full sample/run row already mapped to that title in the fixed
HGSVC2 sample-list crosswalk. Do not infer aliases or strip arbitrary suffixes
from VCF columns. Report duplicate columns, both mapping modes, all unmatched
titles and the overlap with the 24 long-read metadata candidates. If the
header is absent, malformed or ambiguously mapped, report an incomplete check
instead of assuming that sample-list membership implies VCF membership.

No data-dependent case selection, quality filters or outcome comparison is
permitted in this check. Biological sample identity, reference reconciliation,
SV callability, genotype accuracy and the value or novelty of a downstream
question remain separate unresolved issues. This protocol is committed before
the first bounded VCF-prefix request.
