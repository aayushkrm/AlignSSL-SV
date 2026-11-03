# Candidate independent-callset archive inventory

## Question and planned check

The current representation finding involves one public COLO829 file. An
independent sample and workflow would be needed to study scope. A bounded Exa
search identified the [Zenodo long-read callset archive](https://zenodo.org/records/13293672),
whose description reports 1,100 VCFs from ten named individuals, multiple
platforms, aligners and callers. The single ZIP is 15,234,584,453 bytes.
The description does not establish SnpEff annotation or even which members
contain BND records.

Before considering a download or an experiment, read the ZIP central
directory using HTTP byte-range requests. Record names, compressed and
uncompressed sizes, CRCs, offsets, total bytes requested, and any failure.
The archive body's published MD5 cannot be verified without downloading the
whole archive; do not imply otherwise. Member names alone do not prove sample
independence, variant content, annotation history, successful pipelines, or
eligibility as truth. Do not treat a second copy of COLO829 as an independent
sample. Do not use this archive as a prevalence denominator merely because
it contains many pipelines.

This metadata check is cheap and does not release a large compute campaign.
If the manifest supports a concrete next question, inspect small, explicitly
selected member headers under the archive's actual compression and remote
range constraints. First define the selection and a decision rule. Otherwise
record the gap and pivot; the goal is scientific importance, not enlarging an
unvalidated benchmark.

## Central-directory result

The range reader transferred 148,023 bytes from the 15,234,584,453-byte ZIP.
It saw 1,101 entries: one directory and 1,100 `.gz` member names. Of the
members, 636 are stored without an outer ZIP compression layer and 464 use
outer deflate. No member name contains `snpeff` or `anno`, which says nothing
about annotation recorded inside headers. The
[inventory and receipt](../../results/zenodo_13293672_zip_inventory_20261104_run01/)
retain each central-directory entry and every requested byte range. The full
archive MD5 and every member CRC remain unverified. Its HTTP HEAD returned a
last-modified value; the individual range responses did not supply an ETag
or last-modified value, so this is not a strong immutable-source guarantee.

## Header-only follow-up, specified before reading headers

Select the following four **stored** members by their names, after viewing the
directory but before inspecting their contents. They span four named samples,
two reported sequencing types and three caller labels; they are not a random
or representative sample, and all come from the same benchmark archive.

1. `1100VCF/ONT_HG00096_minimap2_sniffles2_HG00096.vcf.gz`
2. `1100VCF/CCS_HG00512_minimap2_sniffles2_HG00512.vcf.gz`
3. `1100VCF/CCS_NA12878_minimap2_delly_NA12878.vcf.gz`
4. `1100VCF/ONT_HG002_minimap2_svision_HG002.vcf.gz`

Read each local ZIP header plus at most a bounded prefix of its stored gzip
member. Look only for the VCF header and specifically for source, reference,
SnpEff and ANN declarations. Stop if a member is compressed at the outer ZIP
layer, its local filename conflicts with the directory, the server ignores
the range, or the header cannot be read inside the stated budget. A completed
header without SnpEff metadata does not prove the VCF lacks annotation or BND
records; no member body or independent truth is assessed.

## Header result

All four selected headers were reached within the 256 KiB compressed prefix
limit for each member. The four prefixes plus ZIP local headers transferred
1,048,898 bytes. Two headers name `Sniffles2_2.2`, one names `SVision v1.3.8`,
and one contains a reference path but no selected `##source` line. None of
the four inspected headers declares `##SnpEff...` or `##INFO=<ID=ANN,...>`.
Three declare a BND ALT type, but no variant records were examined. Two
Sniffles2 headers use the generic sample label `SAMPLE`, so the member filename
alone does not authenticate its donor identity.

The [header packet](../../results/zenodo_13293672_header_check_20261104_run01/)
records selected lines, header and prefix hashes, byte ranges and limits. The
prefix transfer can contain compressed record bytes, and gzip may decompress
past the header internally; only header lines were inspected and retained.
Member CRCs and the full archive MD5 were not
verified. This selected check does not prove the rest of the archive lacks
SnpEff annotations or BND calls. For the current question, it does not yet
provide a second verified independently annotated dataset. Do not download the
entire archive solely to multiply these unqualified examples.

A second [Severus archive](https://zenodo.org/records/14541057) provides a
15.0 GB callset/benchmark bundle and a separate small scripts bundle. The
small bundle was retrieved and its publisher MD5 matched
`a6d880dbe916d9c87314e1cd9291138c`; its SHA256 is
`ec86c87a4b1215b3da9d5720cc0d04b1f61bcc90a5a5c218a89f431f4ef9eeb7`.
A bounded case-insensitive search of those script files found no `snpeff`
token. That does not establish whether the large bundle contains annotated
calls, a different independent sample or relevant BND records. The large
bundle was not downloaded. These are candidate resources, not a selected
publication experiment or evidence of prevalence.
