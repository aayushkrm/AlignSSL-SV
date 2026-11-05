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

## Result

The protocol was pushed as research commit `f4a0e5c` before the source
request. The local route returned HTTP 206 with `Content-Range: bytes
0-262143/1753712867`; the 262,144-byte prefix decoded a complete header.
Its local SHA256 is
`47cd75d7fede0c0cb6a51a7f61638233617cf4670e86faa4354a671c059a809e`.
The prefix is retained outside Git and may contain compressed variant rows;
none were inspected. The release's whole-file MD5 remains unverified.

The header has 3,202 sample columns with no duplicate names. Exactly **56 of
the 60** RNA titles appear as identical VCF column names; the full sample/run
row mapping was not needed. The four absent are `HG00098`, `HG00104`,
`HG00124` and `HG00249`. The first and third have long-read DNA metadata
matches from the earlier crosswalk. Consequently 58 RNA titles have either
an HGSVC2 VCF column or a long-read DNA metadata match; this union combines
different kinds of evidence and is not a count of verified DNA/RNA pairs.

The [receipt and header summary](../../results/hgsvc2_vcf_header_20261106_run01/)
record all columns, mapping modes, unmatched titles, response metadata and
hashes. A separate header reread reproduced 3,202 distinct columns, and five
saved source/script/output hashes matched. No VCF data row, genotype quality,
allele, expression value, reference agreement or cell-line identity was
evaluated. This observation does not establish power or a novel contribution.
