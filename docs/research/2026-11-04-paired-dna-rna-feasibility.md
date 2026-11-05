# Paired long-read DNA/RNA opportunity: metadata feasibility

## Motivation and prior art

The [IGSR announcement](https://www.internationalgenome.org/announcements/New-ONT-data-release/)
describes direct RNA sequencing of 60 1000 Genomes/GEUVADIS lymphoblastoid
cell lines, ENA project `PRJEB76585`. A separate
[1KG ONT Vienna resource](https://internationalgenome.org/data-portal/data-collections/1kg_ont_vienna/)
describes 1,019 long-read genomes and sequence-resolved, phased SV callsets.
These descriptions do not establish how many donors overlap, whether sample
identities or cell-line passages match, whether the relevant insertions and
RNA outcomes are measurable, or whether a new method would be useful.

This is an exploratory alternative to the current interoperability study,
not a selected research direction. Existing work is substantial: a
[2020 GTEx analysis](https://link.springer.com/article/10.1186/s13059-020-02101-4)
studied 20,545 polymorphic mobile-element insertions in 639 donors across 48
tissues, including expression/splicing associations and some reporter
assays; a [2025 rare-disease study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12047269/)
integrated long-read SVs with expression for prioritization. The direct RNA
resource itself has [an associated research manuscript](https://discovery.dundee.ac.uk/en/datasets/project-prjeb76585-direct-long-read-rna-sequencing-from-lcls-form/).
Generic claims that insertions alter splicing or that RNA helps prioritize SVs
are therefore not novel. A possible sequence-resolved, allele-linked
transcript question needs a precise endpoint, nearest baselines, held-out
samples and evidence of a meaningful residual beyond those studies.
The RNA authors' [public analysis repository](https://github.com/aline2593/DRS-LCLs-qtl-analysis)
already describes FLAIR, SQANTI3 and transcript-level QTL analysis for these
60 cell lines. The associated [2026 manuscript](https://doi.org/10.21203/rs.3.rs-4613444/v2)
is a preprint. A repeat of its generic transcript-QTL workflow would not be
a new contribution.

## Source-only check, specified before fetching metadata

Retrieve small public source manifests for the Vienna resource and an ENA
`PRJEB76585` read-run report, recording URLs, timestamps, hashes and missing
fields. Count named samples and exact identifier overlaps only. Preserve RNA
run-to-sample multiplicity; do not treat multiple runs, transcripts or
relatives as independent individuals. If identifiers do not match exactly,
leave them unresolved unless an official crosswalk is obtained. Separately
record any access/reuse conditions, reference assembly and assay differences.

No genomic reads, RNA reads, RNA expression matrices, models or cluster
campaign are authorized by this metadata check. No overlap count will be
interpreted as allele-level truth, statistical power, RNA coverage or
publication readiness. If sufficient paired material exists, define a novel
falsifiable question and get independent scientific review before expensive
work. If not, retain the limitation and pivot.

## Result

The two ENA reports have 60 consistent run rows. Their `sample_alias` values
are labels such as `LCLs-9`; the official `sample_title` field supplies
1000 Genomes-style names. All 60 distinct titles exactly match the 60 IDs
listed in the [RNA authors' code](https://github.com/aline2593/DRS-LCLs-qtl-analysis/blob/70f64b309fd3325ec518857270b78d5f4e2a80f9/scripts/02_transcript_quantification/04_bambu_transcript_quantification.R).
The three retrieved Vienna manifests contain 1,019 distinct alignment IDs.
Only **11 of the 60** RNA titles exactly match those manifests; the other 49
remain unmatched in this specific DNA resource. A second independent simple
metadata parsing check reproduces 1,019, 60 and 11. The matched IDs are
`HG00098`, `HG00099`, `HG00100`, `HG00101`, `HG00103`, `HG00111`, `HG00117`,
`HG00124`, `HG00128`, `HG00149`, and `NA10851`. All 11 have hg38, T2T and
graph alignment filenames listed. Listing a file does not verify its bytes
or sample identity.

The [crosswalk packet](../../results/paired_dna_rna_crosswalk_20261104_run01/)
retains all RNA rows, non-matches, source hashes, modes and author-code pin.
The original small [source manifests](../../results/paired_dna_rna_metadata_20261104_run01/)
and [expanded ENA titles](../../results/paired_dna_rna_ena_titles_20261104_run01/)
are preserved. No DNA or RNA reads were retrieved. The RNA authors' repository
describes Gencode v46 lifted to GRCh37/hg19, while the Vienna manifests list
hg38, T2T and graph alignments. Any locus comparison needs an explicit,
verified reference and coordinate reconciliation. Shared sample title does
not prove the same aliquot, cell-line passage or a usable SV/RNA allele.

The Vienna data-reuse statement is included in the source packet. It asks
users to cite the study and reserves certain global analyses until the first
major paper; the [major paper was published in 2025](https://doi.org/10.1038/s41586-025-09290-7).
Review the source policy and any RNA data conditions for a specific future
study; this metadata check does not settle every reuse condition.

Eleven matched titles alone do not establish power, validated positives or
negatives, suitable held-out tests, or novelty. The other 49 may have DNA
data in a separate collection; absence from Vienna is not absence of DNA.

## Additional DNA source check, specified before reading its manifest

The separately published [1KGP ONT sequencing resource](https://pmc.ncbi.nlm.nih.gov/articles/PMC11610458/)
has a public S3 metadata file at
`PROCESSED_DATA/1kGP_LRSC_500_ONT_Metadata.tsv`. Retrieve the small file and
its adjacent README, then compare exact sample names to the same 60 RNA titles
and label its availability fields according to the source schema. Deduplicate
overlap with the 11 Vienna matches; never sum cohort counts without a set
union. Presence in metadata will not by itself verify usable SV calls, reads,
matching reference, independently sequenced aliquots or a useful endpoint.
No raw genomic data or large job is authorized by this check.

The local Python retrieval attempt timed out; its failure receipt is retained.
The local curl retry and a separate cluster-curl route both retrieved the
same 14,811-byte metadata file and 2,252-byte README, with matching SHA256s.
The table uses `NHGRI_ID`, with both `HG...` and `GM...` prefixes. The ENA
titles use `HG...` and `NA...`; **do not infer `GM`↔`NA` aliases from matching
digits**. The next comparison counts exact strings only. Any candidate alias
would need a separately documented authoritative crosswalk.

The exact join found 13 RNA titles in the 500-row metadata table, none also in
the 11 Vienna matches: 24 unique exact titles across both sources. Thirty-six
titles have no exact match to either metadata set; this is not proof that no
other DNA data exist. The ONT-500 table contains 461 `HG` and 39 `GM` labels,
but no `NA` labels. It is not itself a per-sample SV-call manifest.

## ONT-500 file-list check, specified before matching samples

The public bucket exposes a named `ALIGNED_TO_HG38/SNIFFLES_v2.6.2/` prefix.
An exploratory preview returned 1,000 keys and showed its first 15 names; the
RNA-sample intersection was not checked. Retrieve its full listing, then
check exact metadata labels for a
`.vcf.gz` and corresponding `.csi` among the 13 ONT-500 exact matches.
Record pagination, object sizes/ETags as supplied, missing or duplicate objects
and the source response hash. Do not download the variant files or interpret
object metadata as evidence that calls, genotypes or biological identity are
correct. The exact `HG` matches remain separate from unverified `GM`/`NA`
aliases and from the Vienna resource.

The [complete single-page listing](../../results/paired_dna_rna_ont500_s3_listing_20261104_run01/)
contains 1,000 objects and reports `IsTruncated=false`. Each of the 13 exact
ONT-500 labels has one listed Sniffles 2.6.2 VCF and its corresponding CSI.
No file body or index was downloaded, and the S3 ETags are treated as opaque.
Thus these are 13 candidate file pairs, not 13 verified allele datasets.
The full [two-resource crosswalk](../../results/paired_dna_rna_ont500_crosswalk_20261104_run01/)
retains the other 36 names and does not infer aliases. All 24 candidates still
need sample provenance, allele presence, read coverage, reference and outcome
checks. They may not be statistically independent; relatives and correlated
haplotypes require explicit handling.
