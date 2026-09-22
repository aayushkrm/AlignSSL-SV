# HGSVC3 and IGSR/NYGC reference compatibility audit

**Checked:** 2026-09-23
**Finding:** the published reference metadata fails an exact shared-contig M5 check. Do not treat the HGSVC3 GRCh38-NoALT SV VCF and the IGSR/NYGC 30x CRAMs as reference-identical or begin cohort transfer until the discrepancy is resolved.

## Evidence

The HGSVC3 v1.0 [README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/README_Variant_Calls_1.0.md) says the GRCh38 calls use **GRCh38-NoALT**, described as primary assembly chromosome scaffolds plus unplaced and unlocalized contigs. It reports calls from 65 phased genomes and explains that `.` in a genotype marks a haplotype not callable at that variant because its assembly did not align there; this is not a genome-wide confident-negative mask. The [release manifest](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/MANIFEST_Variant_Calls_1.0) lists the [sequence-resolved SV VCF](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/GRCh38/variants_GRCh38_sv_insdel_alt_HGSVC2024v1.0.vcf.gz) (53,014,672 bytes; MD5 `5dbd0b1ccdf277eae4a93b1e79d2510a`), its [CSI](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/GRCh38/variants_GRCh38_sv_insdel_alt_HGSVC2024v1.0.vcf.gz.csi), and [TBI](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/GRCh38/variants_GRCh38_sv_insdel_alt_HGSVC2024v1.0.vcf.gz.tbi). The VCF header identifies its reference as `hg38.no_alt.fa.gz` and supplies per-contig lengths and MD5s. The manifest does not provide that FASTA or a separate reference dictionary.

The [2019 NYGC/IGSR README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/20190405_1000G_2504_high_cov_README.md) describes 30x Illumina NovaSeq data generated at NYGC and aligned to GRCh38. The [2020 README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/20200526_1000G_2504plus698_high_cov_data_reuse_README.txt) says the additional 698 related samples were also sequenced to 30x at NYGC using the same process. The official [2,504-sample index](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/1000G_2504_high_coverage.sequence.index) and [698-sample index](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/1000G_698_related_high_coverage.sequence.index) identify the public CRAM paths. The latter lists `HG00512` as run `ERR3988780`, study `ERP120144`, file MD5 `2d2d368c0524c49063e5720e593272c4`, with path [`HG00512.final.cram`](https://ftp.sra.ebi.ac.uk/vol1/run/ERR398/ERR3988780/HG00512.final.cram) and index [`HG00512.final.cram.crai`](https://ftp.sra.ebi.ac.uk/vol1/run/ERR398/ERR3988780/HG00512.final.cram.crai).

The official [IGSR GRCh38 reference README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/README.20150309.GRCh38_full_analysis_set_plus_decoy_hla) says the full-analysis-set-plus-decoy-HLA FASTA is based on `GCA_000001405.15_GRCh38_full_plus_hs38d1_analysis_set.fna`, with HLA sequences added; it includes ALT, patch, decoy, unlocalized, and unplaced sequences. Its [sequence dictionary](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/GRCh38_reference_genome/GRCh38_full_analysis_set_plus_decoy_hla.dict) gives `SN`, `LN`, `M5`, and the FASTA URI.

I compared the HGSVC VCF `##contig` metadata (read with an HTTP byte range of 0–524,287, not by downloading the full VCF) against that official dictionary. The [SAM specification](https://github.com/samtools/hts-specs/blob/master/SAMv1.tex) defines M5 after removing whitespace/non-printing characters and uppercasing; the [VCF specification](https://github.com/samtools/hts-specs/blob/master/VCFv4.3.tex) explicitly uses that same calculation for `contig.md5`. Results:

- All 194 contig names shared by the VCF header and dictionary have equal lengths; 176 have equal M5 and 18 differ.
- For the 25 canonical contigs (`chr1`–`chr22`, `chrX`, `chrY`, `chrM`), lengths all agree, but only 7 M5 values agree. Matches: `chr4`, `chr8`, `chr11`, `chr15`, `chr18`, `chr20`, `chrM`. Mismatches: `chr1`, `chr2`, `chr3`, `chr5`, `chr6`, `chr7`, `chr9`, `chr10`, `chr12`, `chr13`, `chr14`, `chr16`, `chr17`, `chr19`, `chr21`, `chr22`, `chrX`, `chrY`.
- For example, HGSVC reports `chr1` length 248,956,422, MD5 `2648ae1bacce4ec4b6cf337dcae37816`; the IGSR dictionary reports the same length but M5 `6aef897c3d6ff0c78aff06ac189178dd`.

The project’s prior [data decision](2026-09-23-data-decision.md) records a bounded remote `samtools view -H` check of this `HG00512` CRAM: its `chr1` length and M5 are `248956422` and `6aef897c3d6ff0c78aff06ac189178dd`, matching the IGSR dictionary. In this audit, HTTP metadata checks confirmed byte-range support and reported CRAM size 15,737,734,304 bytes and CRAI size 1,401,728 bytes; no CRAM body was fetched. `samtools` is not installed in the current shell, so I did not repeat the header read.

## Compatibility assessment and limits

At the published metadata level, shared names and lengths are insufficient: 18 primary contigs have different canonical M5s. Because the SAM and VCF standards use the same case-normalized digest, lowercase soft-masking alone cannot explain these differences. This initial audit could not distinguish true sequence differences from stale header metadata; the later publisher-verified FASTA check below resolves that identity question. A base-by-base difference map and REF-allele validation have not yet been done.

Only the `HG00512` sample row and its prior recorded header check were used here; I did not read every donor’s CRAM header. The 698 cohort is related-sample data, so the technical pilot donor is not evidence of independent-donor eligibility. The HGSVC `.` genotype annotation is not a callable-region mask. Reads aligned to IGSR-only ALT, patch, decoy, or HLA contigs need explicit handling. This initial audit downloaded no full CRAM or reference FASTA and did not inspect VCF records beyond the header; the later reconciliation separately obtained and checked the first-party HGSVC FASTA.

## Original M5 comparison plan and next transfer gate

The sequence-identity portion of steps 1–2 below is now completed by the later
reconciliation; the list is retained to show the decision path. Base-level
difference mapping and the callability gate remain open.

1. **Hold bulk transfer.** First obtain the exact HGSVC `hg38.no_alt.fa.gz` used for call generation, or an authoritative dictionary/checksum tied to it. The HGSVC v1.0 manifest currently does not supply either.
2. **Reconcile references without reads.** Compare the exact HGSVC reference and IGSR dictionary on the intersection of contig names using SAM M5 normalization (remove whitespace/non-printing bytes, uppercase, MD5); report missing names, length differences, and M5 differences separately. Preserve `chr` aliases explicitly rather than silently renaming. Resolve the 18 primary-contig differences before using VCF coordinates or REF alleles against these CRAMs.
3. **Only after that passes or a remapping plan is fixed, run one bounded donor pilot.** Read the complete `@SQ` header of an indexed CRAM with htslib, then process one predeclared small interval using the exact agreed reference. Check interval REF alleles, callable labels, and caller output. HG00512 is suitable for this technical pilot only; account for its trio relationships before any train/validation split.
4. **Open cohort transfer only if the pilot demonstrates the chosen path.** Require either exact shared-contig M5 identity or a documented remapping/reference-conversion procedure validated on the bounded pilot. If neither is available, stop the HGSVC3/IGSR pairing and select a compatible reference/data source.

**Later resolution of the identity question:** The first-party HGSVC no-ALT
FASTA was subsequently downloaded and publisher-MD5 verified. Its canonical
M5 matches all 194 HGSVC VCF contigs shared with the IGSR dictionary, whereas
18 IGSR M5s differ. Thus the discrepancy is a real difference between the
available reference sequences, not simply a stale HGSVC header or masking-case
artifact. See [the reproducible reconciliation](2026-09-23-reference-reconciliation.md).
The *positions and effect* of the differences still need measurement; the
callable-negative gate also remains unresolved. **No cohort CRAM transfer.**
