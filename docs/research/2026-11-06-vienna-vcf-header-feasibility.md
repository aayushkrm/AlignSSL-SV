# Vienna phased SV callset: header feasibility

Checked 2026-11-06 on branch `research/genotype-confidence-contracts-20261001`.

## Finding

The earlier note found 11 exact RNA-title matches in Vienna alignment manifests. The later phased multisample VCF has only **9 of those 11 sample IDs** in its `#CHROM` header. `HG00098` and `HG00124` are absent. The other nine are present.

The official release identifies the file as the SHAPEIT5-phased SAGA/Giggles callset, with 908 unrelated samples. The published methods connect this callset to graph-based SV genotyping and a CHM13 haplotype panel. The paper says the SV calls were later lifted to GRCh38 for comparisons. The official phased VCF header has no `##reference` or `##assembly` line, and its contig records have no lengths. Therefore, the file header alone cannot establish its assembly. The release and paper indicate that this named phased file is the CHM13/graph-context callset, not a GRCh38-native phased VCF.

I found no separately named GRCh38-phased multisample VCF in the official v1.0 and v1.1 release listings reviewed. The v1.0 `final-vcf.phased.vcf.gz` and the v1.1 `shapeit5-phased-callset_final-vcf.phased.vcf.gz` have the same MD5 in their respective official manifests. The GRCh38-lifted representation is not the file whose header was checked here.

## Exact sample-title comparison

I compared the 60 distinct ENA `sample_title` values in the retained [RNA title report](../../results/paired_dna_rna_ena_titles_20261104_run01/ena_titles.tsv) with the 908 VCF sample columns. The exact intersection is nine IDs:

| RNA sample title | VCF sample column |
|---|---|
| HG00098 | absent |
| HG00099 | present |
| HG00100 | present |
| HG00101 | present |
| HG00103 | present |
| HG00111 | present |
| HG00117 | present |
| HG00124 | absent |
| HG00128 | present |
| HG00149 | present |
| NA10851 | present |

This is an exact metadata-name comparison. It does not prove that DNA and RNA came from the same aliquot or cell-line passage, or that a particular SV is present and measurable.

## Release and callset identification

The official [IGSR release index](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/) lists v1.0 and v1.1. The v1.1 index contains `shapeit5-phased-callset/`; its [directory listing](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/shapeit5-phased-callset/) names `shapeit5-phased-callset_final-vcf.phased.vcf.gz`.

The official [v1.1 README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/shapeit5-phased-callset/shapeit5-phased-callset_README.md) says the phased VCF was produced by ShapeIt5 from `giggles-genotyping/final-vcf.unphased.vcf.gz`, and contains 908 unrelated samples selected from 967 samples. The [Giggles README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/giggles-genotyping/giggles-genotyping_README.md) describes genotyping on augmented graph `HPRC_mg_44+966`.

The primary [2025 paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12350158/) describes the final SAGA callset as graph-aware Giggles genotypes statistically phased with SHAPEIT5 using a CHM13 haplotype panel. It describes later lift-over of the SV calls to GRCh38 for comparisons. The official [graph-augmentation README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/graph-augmentation/graph-augmentation_README.txt) separately labels input Sniffles, DELLY and SVarp callsets as GRCh38-coordinate files. Those input labels do not make the phased graph-genotyping output a GRCh38-native VCF.

The VCF header reports `VCFv4.2`, `##source=shapeit5 phase 1 v0.1`, and `##fileDate=23/01/2024 - 20:35:34`. It lists 23 contigs (`chr1`–`chr22`, `chrX`) without lengths. It does not declare an assembly. The phasing method and 908-sample count come from the official README; no genotype records were read to inspect phase delimiters.

## Retrieval and checks

All scratch files are under `/tmp/vienna-vcf-header-check/`. No project files were written during retrieval.

The phased VCF is 73,830,605 bytes according to the official v1.1 manifest and the HTTP `Content-Range`. I made two guarded range requests to the [official VCF URL](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/shapeit5-phased-callset/shapeit5-phased-callset_final-vcf.phased.vcf.gz):

```text
Range: bytes=0-17       -> HTTP 206, Content-Range: bytes 0-17/73830605
Range: bytes=18-2879    -> HTTP 206, Content-Range: bytes 18-2879/73830605
```

The first request read the BGZF block-size field. The second completed that one 2,880-byte BGZF block. Decompression yielded 10,132 bytes, all VCF header text through `#CHROM`; the block contained zero non-header lines. I compared only its 908 sample columns with ENA `sample_title` values. No variant rows, alignments, RNA reads, expression data, or test labels were fetched or inspected.

The file’s full-body MD5 was **not** recomputed. The value below is the MD5 listed by both official manifests.

## Source URLs, commands, and hashes

The small directory indexes, READMEs and manifests were saved outside the repository. Index SHA256 values are for the retrieved HTML response bodies. Manifest SHA256 values are for the complete downloaded manifests.

| Source | Bytes | SHA256 / checksum |
|---|---:|---|
| [Release index](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/) | 1,173 | `5f6deab41aafb7c9a79de7afb919fecedce08ede57dd89e7cf2dd97a59802b52` |
| [v1.0 final-vcf index](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.0/final-vcf/) | 1,992 | `b836f0fabc3d08b61302ee66053c9bcd4488f5f5e5a3a0f9c45f6e2b8c87bf9b` |
| [v1.1 index](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/) | 3,021 | `5b0036e2a74e135f8d865466aacb570eb681fccd053cecf486a39b753101ea62` |
| [v1.1 phased-callset index](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/shapeit5-phased-callset/) | 1,386 | `4d09bbace2acf1970692bb6d67fa739141f0f7b4dd62d21867b9139796b359c8` |
| [v1.0 manifest](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.0/1KG_ONT_VIENNA_manifest_20240409.tsv) | 487,972 | `f67c50d063ae6683f55786f703e76d7fed03a7dac8b3f6cf9505adbd6827302a` |
| [v1.1 manifest](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/1KG_ONT_VIENNA_manifest_20241216.tsv) | 3,637 | `55de63dc102f05f0530eb71f68ec3d74b81a30d220a521f0ab840e78e86385a2` |
| v1.0 and v1.1 phased-file manifest MD5 | — | `4a2139a8313060fb5e30bfe15d4d12bc` (same in both manifests) |
| [v1.1 SHAPEIT5 README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/shapeit5-phased-callset/shapeit5-phased-callset_README.md) | 380 | `861372aa26d980fefa99226c22a7591151a89deab6166ae726ced96bdd8b71bd` |
| [v1.0 final-vcf README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.0/final-vcf/final-vcf_README.txt) | 221 | `a1196d7fe392175768b9f2a394ac87bcd4f45b7bbdfecd371159cc3a00707dec` |
| [v1.1 Giggles README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/giggles-genotyping/giggles-genotyping_README.md) | 1,756 | `cc5a0d5bd30f641a1cffe47074c19769cdade2baa908312cb31ceaf9203e8f55` |
| [v1.1 graph-augmentation README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1KG_ONT_VIENNA/release/v1.1/graph-augmentation/graph-augmentation_README.txt) | 678 | `41aa8cdc2a3655d24456e4c11660b72a2661f7c79a7ac432dbc89ab935cdc382` |
| VCF first BGZF block, bytes 0–2879 | 2,880 | SHA256 `5488b0caf0d2f81e82f069b5a6d6f5b2a611222d821f4b3984f6f09eafc92d08` |
| VCF header through `#CHROM` | 10,132 uncompressed | SHA256 `f0147bb55ed25f47d7a1564aaa00789ae7b3a5046303cd7ae5547dc7b102ad3e` |
| [ENA PRJEB76585 title report](../../results/paired_dna_rna_ena_titles_20261104_run01/ena_titles.tsv) | 6,007 | SHA256 `7bcd97862f8849e5175af270bb980fc66a05da7123ed634f9c7c77f3b8f67d80` |

The RNA report came from the [ENA read-run metadata API](https://www.ebi.ac.uk/ena/portal/api/filereport?accession=PRJEB76585&result=read_run&fields=study_accession%2Crun_accession%2Csample_accession%2Csample_alias%2Csample_title%2Csample_description%2Csecondary_sample_accession%2Clibrary_strategy&format=tsv&limit=0), retrieved 2026-11-03T19:12:12Z. Its receipt records HTTP 200 and the same SHA256.

After the worker completed, the orchestrator copied its small source files and
header-only BGZF block to the [preserved packet](../../results/vienna_vcf_header_20261106_run01/).
An independent offline reread verified all 13 preserved file hashes, confirmed
the decompressed block contains only header lines, and reproduced the 908
unique VCF columns and nine exact RNA matches. All nine also appear in the
separately checked HGSVC2 VCF header. The two Vienna alignment-only names do
not thereby acquire a confirmed genotype in either checked multisample VCF.
`analysis/check_vienna_vcf_header_packet.py` reproduces this offline check.

Metadata fetches used `curl --fail --silent --show-error --location --max-time 20 '<source URL>' --output '/tmp/vienna-vcf-header-check/<filename>'`, followed by `shasum -a 256 '/tmp/vienna-vcf-header-check/<filename>'`. Directory indexes were also fetched with Python `urllib`. The VCF used HTTP `Range` requests above; each response was checked for status 206 and an exact `Content-Range` before its bytes were read.

## Scope and tools

The initial repository check found no applicable `AGENTS.md`. At first read, the working tree had unrelated edits and untracked research artifacts. At final read, the branch showed commit `f4a0e5c` (`Audit paired metadata and preregister VCF header check`), plus untracked `analysis/check_hgsvc2_vcf_header.py`, `results/hgsvc2_vcf_header_20261106_run01/`, and this report. The earlier status showed a different set of untracked artifacts. I did not run `git commit`, `git push`, `git add`, reset, or cleanup commands. I cannot identify the source of the shared-worktree changes. This task wrote only this report; I left the other paths untouched. No tests or expensive jobs were run.

Exa and Parallel Search were available and used to find the official release and primary paper. Scite was available but was not needed. NCBI literature skills were visible; direct official release pages and the primary paper on PMC supplied the needed evidence. No Firecrawl tool was exposed in this session, so the available search tools and official sources were used. The session did not expose independently verifiable runtime model/effort metadata; no such claim is made.
