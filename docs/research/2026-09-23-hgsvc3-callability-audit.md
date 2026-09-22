# HGSVC3 v1.0 callability audit

**Date:** 2026-09-23
**Question:** Does the assembly-derived HGSVC3 v1.0 release provide donor-specific callable/high-confidence negative regions for DEL candidate filtering?

## Finding

The inspected GRCh38 `Variant_Calls/1.0` and `Assembly_Info/1.0` inventories do not distribute a donor-specific callable or high-confidence-negative BED. The callset supports variant positives; a missing VCF row is not evidence of callable reference. This finding is limited to these release directories, not all HGSVC3 working data or source outputs.

## Release files and fields

The [release README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/README_Variant_Calls_1.0.md) describes 65 phased genomes called with PAV 2.4.0.1, merged with SV-Pop, and QC’d using support from other callers; unreliable regions including centromeres and telomeres were discarded. The reference is GRCh38-NoALT. The [manifest](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/MANIFEST_Variant_Calls_1.0) and [GRCh38 directory listing](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/GRCh38/) enumerate VCFs, indexes, and annotations, including `variants_GRCh38_sv_insdel_alt_HGSVC2024v1.0.vcf.gz`, `variants_GRCh38_sv_insdel_sym_HGSVC2024v1.0.vcf.gz`, and `variants_GRCh38_sv_inv_sym_HGSVC2024v1.0.vcf.gz`. No callable BED appears in these inventories.

The `sv_insdel_alt` VCF is 53,014,672 bytes (manifest MD5 `5dbd0b1ccdf277eae4a93b1e79d2510a`). Its header, read via a bounded byte range, has `CHROM POS ID REF ALT QUAL FILTER INFO FORMAT` and 65 sample columns. Only `GT` is declared under FORMAT; INFO fields are `ID`, `VARTYPE`, `SVTYPE`, `SVLEN`, `SAMPLE`, `REF_SD`, and `REF_TRF`. No `END`, `DP`, or `GQ` is declared. These fields describe variants, not genome-wide callability. The header’s `##source=PAV (HGSVC2)` differs from the release README’s PAV 2.4.0.1 provenance; use the release README for version attribution.

The README defines allele order as h1 then h2 (`0|1` means h2 carries the variant); `.` means that assembly haplotype was not aligned at the represented site. It is not a reference block for unreported sequence. The [Assembly_Info/1.0 listing](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Assembly_Info/1.0/) has only a README, manifest, `supp-table_verkko_assembly-data.2024v1.0.tsv`, and `supp-table_verkko_qv-estimates-detail.2024v1.0.tsv`. The assembly table’s `sample`, `Verkko assembly accession`, `file accession`, coverage, and `use data` fields describe assembly/read provenance and QC, not callable intervals.

## First-party route to callable intervals

The [HGSVC Phase 3 repository](https://github.com/hgsvc/phase3-main-pub) distinguishes production `release/` data from the broader `working/` area. Its frozen [PAV 2 README](https://github.com/hgsvc/phase3-main-pub/blob/main/sources/pav/plain/README.md) documents `results/{asm_name}/callable/` BEDs of regions where contigs aligned, smoothed by 500 bp. This is a plausible sample-scoped source, but the README gives no filenames/schema and does not establish inclusion in the v1.0 release. It also accepts per-haplotype `FILTER_h1`/`FILTER_h2` BEDs in **assembly coordinates** for unreliable regions; overlapping variants get `TIG_FILTER`. These input QC masks are not reference-coordinate callable masks.

The current [PAV README](https://github.com/BeckLaboratory/pav/blob/main/README.md) documents later PAV 3 Parquet outputs `results/NAME/call_hap/callable_ref` and `callable_qry`, in reference and query coordinates. This is a possible rerun route, not evidence that these PAV 3 tables are bundled with a PAV 2.4.0.1 release.

The official [working `20240307_PAV_VCF` directory](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/working/20240307_PAV_VCF/) lists two ~12 GB tar archives, a README, and a manifest. Its [README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/working/20240307_PAV_VCF/README_20240307_PAV_VCF) says these are intermediate calls from 65 phased assemblies and omit PAV-QC failures. Archive members were not inspected; whether they contain `callable/` BEDs is unresolved.

## Falsifiable negative-label gate

Do not turn a missing VCF record into a negative DEL label. Freeze candidate normalization and donor/haplotype masks first. A negative requires the full interval plus prespecified breakpoint flanks to be callable on **both** haplotypes, with no assembly-QC filter, alignment break, matching DEL, or overlapping complex event after representation-aware comparison. Missing haplotypes, gaps, QC-filtered intervals, and ambiguous representations remain **unknown**.

Before training, audit at least 100 stratified proposed negatives against independent, blinded assembly/long-read truth, plus all held-out confirmed DEL controls. Pass only with zero supported DELs among proposed negatives and zero confirmed DEL controls admitted as negatives. Any such event fails; report counts and the one-sided 95% binomial bound (0/100 gives an upper error bound of about 3%).

## Scope boundary

**Unresolved:** This audit covers only the listed v1.0 release directories. It does not establish whether callable BEDs are inside the uninspected `working/` tar archives or other external assembly repositories. PAV documents callable output, but availability as a ready-to-use HGSVC3 file remains unverified.
