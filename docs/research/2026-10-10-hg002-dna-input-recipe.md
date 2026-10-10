# HG002: exact DNA inputs and finite qualification

2026-10-10. Main's source and header check; no whole-genome experiment yet.
The [frozen DNA-first selection](2026-10-09-public-paired-falsifier-decision.md)
still governs the cohort and endpoint. RNA remains untouched. A filename,
same donor or successful annotation does not prove source identity or an
adequately resolved coding-path negative.

## Source chain and selected representation

The [primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC12077378/)
separates genomic DNA from MAS-seq RNA. The
[original preprint, data availability](https://www.biorxiv.org/content/10.1101/2023.09.26.559521v1.full)
links the public `HG002_WGS.haplotagged.bam`. The
[ENA run SRR29438434](https://www.ebi.ac.uk/ena/browser/api/xml/SRR29438434)
has exactly that submitter alias; experiment SRX24951052, BioSample
SAMN41878946 and BioProject PRJNA1124997. The experiment describes HG002
genomic Revio material. The archive reports80,344,827,828 bases and5,359,077
spots; these are not compressed bytes or an independent read census.

Public object root:
`https://stergachis-manuscript-data.s3.us-west-1.amazonaws.com/2023/Vollger_et_al_long-read_multi-ome/`.
HEAD/range observations, not whole-file checksums:

| Product under that root | Bytes | ETag |
|---|---:|---|
| `HG002_WGS.haplotagged.bam` | 48,727,325,910 | `8c384718d3e41cbe000453b6846a7451-5809` |
| `HG002_WGS.haplotagged.bam.bai` | 21,582,928 | `b45b35aa8fd900989a2798ed22faec3c-3` |
| `hg002.hap1.p_ctg.split.GRCh38.bam` | 1,065,426,280 | `eb5b5d0f7b113dd37e695d5476d86091-128` |
| `hg002.hap2.p_ctg.split.GRCh38.bam` | 1,075,219,729 | `73b109924ce95e8aa54079690daf5714-129` |

The run also exposes `SRR29438434_subreads.fastq.gz` at the ENA public FTP,
33,155,968,933B, archive MD5`6005ab626a327f082337a66bb9704465`.
That FASTQ is a different representation; its name alone does not establish
read type, base equality, phasing or equivalence to the processed BAM.
Prefer the study's processed DNA when its records qualify; do not download
both representations without a concrete need. Multipart ETags are not MD5s.

## What the capped headers establish

Each object received one exact65,536-byte HTTP206 prefix; only the BAM text
header was decoded. Actual new genomic body charge is196,608B. A prefix can
contain later bytes, so this is not a zero-data check. No alignment, HP/PS
tag, assembly contig sequence, RNA record or entire file was inspected.

| Prefix | SHA256 | Header result |
|---|---|---|
| DNA | `46775aefa7f2958ebf6a1d76df4078f32c87ae8d3ac683b7563a8ed4d5bbeb90` | SM/ID`HG002_WGS`; Revio CCS, ccs7.0, pbmm2 1.10.0;195 SQ, GRCh38 chr1/chr3 lengths; no SQ M5 |
| Haplotype1 mapped split contigs | `3bf32e0b4eb6435aa4937cc8c62c03f69f9038e215796f0c020e1ae01b392849` | SM`UnnamedSample`, pbmm2 1.4.0; input name`hg002.hap1.p_ctg.split.fasta` |
| Haplotype2 mapped split contigs | `6d571149b2abf9c1592ec5af688cf8fc818649103d6d187875a77415d46271af` | Same generic sample/program fields; hap2 split FASTA input name |

The DNA header records the alignment input reference`hg38.analysisSet.fa`
and an `--unmapped` alignment command. It contains no haplotagging program
record. The filename and ENA alias support provenance, not tested phase-tag
correctness or whole-file integrity. Reference names/lengths are insufficient
to establish base identity with the selected GENCODE FASTA. Check actual REF
and dictionary compatibility before using called variants.

The two assembly BAMs do **not** yet qualify as complete, same-source
haplotypes. Their headers give neither hifiasm/read inputs nor complete
original-contig retention. Extracted split/mapped sequences cannot silently
replace complete native targets, especially for a negative call at a gap,
copy or competing locus. No two-gigabyte acquisition has occurred.

Finite S3 metadata checks: the uppercase HG002 prefix has331 keys, complete
for that prefix; a separate complete root/delimiter listing exposed the
lowercase assembly names. Neither is an exhaustive recursive search.
No FASTA/VCF was present in the listed root objects. One exact ENA analysis
query for this BioProject returned a header only; not global product absence.

## Matched annotation and pinned native control

[GENCODE50 primary-assembly release](https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_50/)
HEAD sizes and its published MD5SUMS were read. Bodies have not been acquired
or checksum-verified. Comprehensive annotation, not basic/canonical only:

| File | Bytes | Published MD5 |
|---|---:|---|
| `GRCh38.primary_assembly.genome.fa.gz` | 845,635,028 | `da1a11258be075cfa7af718162c894e7` |
| `gencode.v50.primary_assembly.annotation.gff3.gz` | 160,763,187 | `bfa97cfbd5fe76ce5fb19ac08c16f25b` |
| `gencode.v50.primary_assembly.annotation.gtf.gz` | 124,650,284 | `289b91e5e95e8b0450d223246f10a12e` |
| `gencode.v50.metadata.Selenocysteine.gz` | 893 | `cf5f185bdfa2dcd0582e2f747f3a4e9b` |
| `gencode.v50.pc_translations.fa.gz` | 21,136,991 | `509a89a4c3bb8c594baac50d4d57e589` |

LiftOn v1.0.14 resolves to
[commit8378f8e4a3d8404c94d801c285a2c74291e893b7](https://github.com/Kuanhao-Chao/LiftOn/tree/8378f8e4a3d8404c94d801c285a2c74291e893b7),
not its annotated-tag object`d8abbe115c34337bf306b159de995ce8b646987b`.
The live manual/main may differ from that pin. Verify the installed native
interface and outputs before executing the frozen complete-target commands.
Retain native ORF/rescue/copy behavior; do not handicap the control by using
exon crops. A coding model with a new downstream start is not automatically
a retained-reference-termini path. Missing, partial, ambiguous or exceptional
paths must remain UNKNOWN, with every reference coding isoform accounted for.

The [current hifiasm README](https://github.com/chhylp123/hifiasm#assembling-hifi-reads-without-additional-data-types)
describes two **partially phased** HiFi-only contig sets with possible switch
errors, distinct from primary/alternate output. Its`--h1/--h2` inputs are
Hi-C read files, not HP-tag partitions. Thus a new same-source assembly still
needs local gene/allele phase, sequence and copy qualification. No parental
genomes are required merely to name haplotypes; names alone cannot phase RNA.
The native purging limitation also matters for copy-sensitive negatives.
Main read the complete short HiFi-only tutorial (labelled0.16.0) and selected
complete README usage/output/limitations sections via Firecrawl. These are
documentation checks, not a pinned hifiasm runtime or a tested assembly.

## Custody, scope and next stage

Raw listing, three unchanged prefixes, decoded headers, summaries and the
capped-check scripts are off Git at
`/Users/akm/aayushkrm-AlignSSL/runs/hg002-dna-input-recipe-20261010/`.
This196,608B prospective HG002 qualification charge is separate from the
parental SVA90,836,888B charge and historical experiment accounts.
No whole DNA/assembly/index download, new installation, batch job or RNA
processing occurred for these checks. No600CPU-hour campaign is released.
Routine software setup is separate: job1604238 failed pre-task with signal53
and no stdout/venv; direct1604239 failed before pip because hydra-n12 exposed
project home read-only. No software body was acquired in these failed tasks.
A default-partition request for hydra-n1 was rejected without allocation;
that node belongs to`amd_256M`, not the default`debug` partition. The next
direct setup uses that explicit partition and the previously working node.
The batch signal's cause is not proven by the later read-only observation.

### Superseding cached-record check

After the text-header check, main decoded only complete BGZF blocks from the
same unchanged prefixes, then used pysam0.24.1 to read selected complete
records. No new network body or RNA. Missing EOF warnings are expected for
prefixes and do not imply corruption of the remote whole object.

DNA's first three records contain two original CCS identities, full query
sequence and qualities of18,725/21,969 bases, RG`HG002_WGS`, HP1, PS1 and
rq approximately0.99586/0.99351. All three are supplementary alignments,
with large soft clips and no hard clips. Two records share one name; they
are not independent molecules. This demonstrates recoverable sequence and
observed tags for these records, not representative coverage, usable phase
at candidate genes, completeness of the whole read set or a primary-read
certificate. Correct forward orientation/deduplication remain intake tasks.

The first complete hap1 split query is65,834 bases; the first two hap2 queries
are62,920/112,484 bases. Sequence is present, qualities absent, RG`default`,
no HP/PS, no hard clips. One hap2 record is supplementary with MAPQ1.
The next hap1 query declares250,000 bases but is incomplete in the prefix.
These observations support recoverable **split fragments**, not complete
original contigs, source-read linkage or whole-target qualification. Do not
download these BAMs to manufacture primary-control negatives.

The [staged investment decision](2026-10-10-hg002-dna-stage-investment.md)
selects the exact study DNA route, with separate accounts/reviews. It does
not release calling, assembly, P1 or RNA by implication. Routine setup is
now [actually completed](2026-10-10-hg002-runtime-setup.md); the chronology
above remains the intact failed-attempt record.

Read scope: Exa one five-result targeted query plus one known author page;
Firecrawl selected data/method passages from the primary article and v1
preprint, and selected native-manual passages; Life Sciences Literature two
exact-DOI bioRxiv details/publication-linkage requests, one record each.
A truncated initial preprint display was recovered by the same URL with
selected passages; an oversized S3 listing was similarly recovered. Neither
is another discovery sweep or an exhaustive literature/absence claim.

Next: resolve the concrete DNA-stage investment and independent review,
test the cohort parser, and stage matched references/native runtime on the
cluster. Use useful parallelism; do not reserve idle GPUs/nodes. The complete
same-source DNA control and adequately resolved negatives still precede RNA.
