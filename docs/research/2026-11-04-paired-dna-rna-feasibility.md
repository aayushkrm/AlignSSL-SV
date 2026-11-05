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
In version 2, the authors report 87 significant transcript-SNP QTLs and
describe excluding 42,065 discovered transcripts that did not align to a
GENCODE gene from subsequent analysis. They also describe multi-sample Bambu
discovery. These are the authors' reported analysis choices, not validation of
the contents of the downloaded FLAIR matrix. Any new analysis must account
for transcript ascertainment and determine whether a discovery catalogue used
held-out samples before presenting an independent evaluation.

The earlier [Ebert et al. HGSVC study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8026704/)
also genotyped assembly-discovered SVs in 1000 Genomes short-read genomes and
tested expression and splicing associations in a combined set of 427 donors.
It is direct prior art for population-scale SV/QTL analysis, as already noted
in the project's [October prior-art decision](2026-10-09-public-paired-falsifier-decision.md).
Its short-read-genotyped release has exact VCF header matches for 56 of the
60 RNA titles in the later check below. Per-allele accuracy has not been
verified for this purpose. A new study would need a specific residual beyond
that work and controls for linked small variants and mapping bias.
The [2025 HGSVC3 study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12350169/)
also compares haplotype-phased Iso-Seq isoforms for SV-containing genes and
examines nearby differential expression in 12 individuals. Merely combining
phased SVs with long-read isoforms is therefore established prior work; this
does not rule out a precisely defined, independently tested residual.

The [Lu et al. 2026 bioRxiv preprint](https://doi.org/10.64898/2026.07.01.735728)
also compares pangenome-derived and standard calls for expression association,
fine-mapping and prediction using 430 1000 Genomes samples with short-read
RNA-seq. Its question and assay are not identical to the 60 direct-RNA data,
but they directly narrow any generic claim that pangenome SVs add information
beyond standard variants. The same preprint also reports a control analysis
of 201 HPRC samples with PacBio Kinnex long-read RNA; those samples contributed
to the graph used in that control. This is close prior art, with a different
assay and a different sample/graph relationship. The Life Sciences Literature bioRxiv metadata
lookup retrieved the preprint; its publication-link lookup returned no entry
on 2026-11-05 UTC, which does not prove that no later publication exists.

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

A separate [Vienna phased-callset header check](2026-11-06-vienna-vcf-header-feasibility.md)
found nine of those 11 titles among its 908 sample columns; `HG00098` and
`HG00124` are absent. All nine are also among the HGSVC2 VCF-header matches.
The Vienna header does not declare its assembly; the release and paper place
the phased callset in a CHM13/graph context and describe later GRCh38 lift-over.
Alignment-list membership must not be treated as membership in this particular
phased callset, and assembly reconciliation remains essential.

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

The linked 2024 paper describes the first 100 samples, whereas the archive
README and table describe 500. The paper does not by itself validate the
additional rows or the 13 object pairs. An [independent audit](2026-11-06-paired-source-independent-audit.md)
reproduced the original 11 and 13 exact matches and checked their receipts;
its findings do not attest to allele identity, quality, passage or outcomes.

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

## Processed RNA products: metadata-only protocol

Before inspecting the deposit, the RNA authors' pinned repository README
names Zenodo DOI `10.5281/zenodo.18763244` as a source of BAMs and derived
quantifications. Retrieve only the corresponding public Zenodo record metadata
and inspect its file names, sizes, declared checksums, version and license.
Retain the source response and a local SHA256; do not download file contents
or claim that a named product contains usable sample-level outcomes. Declared
checksums are not verified without downloading the corresponding files. This
check does not select a scientific endpoint or authorize a training campaign.

The [Zenodo record](https://zenodo.org/records/18763244) was retrieved on
2026-11-05 UTC. Its metadata identifies version V2, license CC-BY-4.0 and
81 files. Sixty distinct `sorted_alignment_<sample>.bam` names cover all 60
RNA titles, including the 24 titles matched to DNA metadata. The listing has
no `.bai` or `.csi` filenames. It also names FLAIR transcript counts
(`Geuvadis_60EUR_Transcripts_FLAIR_COUNTS.tsv.gz`, 7,577,751 bytes), three
transcript TPM files and gene-level quantifications. The listed names do not
verify the file contents, reference, identity or coverage; no deposited file
was downloaded for this inventory. The source response, local SHA256, and
retrieval command are preserved in the [metadata packet](../../results/rna_zenodo_record_20261106_run01/).

## Processed RNA count header: separate planned check

After the metadata-only inventory, fetch the one named FLAIR count file to
the project `runs` directory, verify its full size and publisher-declared MD5,
and inspect only its first decompressed row. Compare exact header fields with
the 60 ENA titles and the 24 DNA-matched titles, retaining unmatched names.
Keep the compressed file out of Git; record the source URL, commands, hashes,
header and matching summary. Do not inspect expression values or use the
matches as evidence of measured alleles, biological significance or power.
If the first row is not a sample header, report that limit rather than guessing.

The local download succeeded: 7,577,751 bytes, publisher MD5
`3b841d33a7c7bfe4b250f700d1053b03`, local SHA256
`6e8566ebb772125769ad417e305e21bafde6597666ec228d03f22c209acf960c`.
The first row has 61 fields: `ids` followed by 60 distinct fields matching
all 60 ENA titles exactly, including all 24 names matched to the DNA metadata.
No matched sample field is duplicated. The [receipt and header summary](../../results/rna_flair_header_20261106_run01/)
retain the full first row and every exact match. The compressed public matrix
is retained outside Git in the project `runs` directory. No expression rows
were inspected. A sample name in a count header is not evidence that any
particular transcript, structural allele or sequencing molecule is usable.

## Additional short-read-genotyped SV source: planned metadata check

The [HGSVC2 source page](https://internationalgenome.org/data-portal/data-collections/hgsvc2/)
describes PanGenie genotypes in 3,202 high-coverage 1000 Genomes samples.
The [release listing](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC2/release/v1.0/PanGenie_results/)
names two small sample lists, with 2,504 and 698 in their filenames, alongside
large VCFs. Retrieve only those lists and the adjacent README and manifest;
preserve responses and hashes. Compare exact sample identifiers to all 60 RNA
titles, report duplicates and unmatched names, and separately identify the
subset outside the prior 24 long-read DNA metadata matches. Do not retrieve VCF
bodies or interpret listed samples as verified genotypes, long-read DNA,
callability, biological identity, or statistical power. This source is older
and its discovery/calling biases require appropriate comparison with newer
long-read callsets. Inspect the lists' format before choosing a parsing field.

The source README calls the two files its complete deep-coverage sample list.
Each observed row has exactly two underscore-separated fields matching
`(HG|NA)[0-9]{5}_ERR[0-9]+`. Before calculating overlap, use the left field
as the source's sample-name token and retain the full sample/run row. Reject
any rows outside this format and report token duplicates across both lists.
This is still a sample-list join, not a check of VCF sample-column names.

All four small text responses were retrieved locally. The release manifest's
declared sizes and MD5 values match the README and both sample-list files.
The two lists contain 3,202 rows with 3,202 distinct sample-name tokens and
no duplicates. Of the 60 RNA titles, **56** exactly match a token; **34** of
those matches are outside the earlier 24-title long-read DNA metadata union.
Thus **58** RNA titles match at least one of these three source lists, with
22 appearing in both the short-read PanGenie list and the earlier 24-title
union. The four absent from PanGenie are `HG00098`, `HG00104`, `HG00124`,
and `HG00249`; the first and third have a prior long-read metadata match.
The [packet](../../results/hgsvc2_sample_lists_20261106_run01/) retains all
60 comparisons and full matching sample/run rows. These counts do not prove
VCF-column membership, SV genotype quality or identity of cell-line aliquots.
The protocol was written before these checks during this session, but was
first committed afterward; the repository cannot independently prove its
pre-execution state.

A separately preregistered [VCF-header check](2026-11-06-hgsvc2-vcf-header-protocol.md)
then confirmed that those same 56 RNA titles appear as exact columns in the
HGSVC2 biallelic no-SNV VCF; the other four do not. The header had 3,202
distinct sample columns. No VCF variant or genotype row was inspected.
