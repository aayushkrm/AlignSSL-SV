# Platinum pedigree SVA: original source check

10 October 2026, local time. Main's read-only evidence check, in parallel with
scientific selection and the current Sniffles input check. The initial phase
had no caller or genomic acquisition. The later addendum records one actual
BAM-prefix acquisition for text-header inspection, not a regional assay.

## Original workbook

The [published Supplementary Table 10](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-025-08922-2/MediaObjects/41586_2025_8922_MOESM12_ESM.xlsx)
returned HTTP200. The unchanged file is249,138bytes, SHA256
`34279cdd3bf16e250ea25edde1e2d1e5d26e7deb0ca140a24558acebb67b413f`.
It is preserved outside Git at
`runs/literature/platinum-sva-source-check-20261010/supplementary-table-10.xlsx`
in the parent workspace. The read-only inspector sits beside it.

The spreadsheet skill required source-preserving inspection: bundled
Artifact Tool imported the original file, without edits, recalculation,
normalization or export. Main inspected the sheet inventory, matched the
exact SV ID, and read `Legend!A1:B10`, `SVs (T2T-CHM13)!A1:R4`, and
`SVs (T2T-CHM13)!A26:R26`. Other variant rows were not audited.

| Field, header row3 | Exact value, row26 |
|---|---|
| sample | NA12887 |
| chromosome | chr3 |
| start |71589909|
| end |71593317|
| SV ID | `>687695>687698;>630134>630136;chr3-71589910-INS-3407` |
| SV type | INS |
| SV size |3407|
| inheritance | maternal |
| Source caller | `pggb-hifiasm;pggb-verkko;pav` |
| Mechanism | SVA |

This confirms the scout's specific event, not a current-caller failure.
The inspected legend, headers and row do not state the coordinate convention
or supply the inserted sequence. `end-start=3408` must not be treated as an
established reference deletion span for an insertion. The ID's position is
one greater than start, consistent with a BED/VCF convention, but that is an
inference, not a source definition. An event-centered query can safely include
both positions; exact breakpoint/allele identity needs further evidence.
Without an independently supplied insertion sequence, a call is at most
compatible with the published event by location, size and read evidence. It
is not proven sequence-identical to the child's assembly allele.

## Public sample and source scope

Firecrawl supplied the entire current GitHub front-page markdown
(10,409characters). Main then read the complete raw README pinned to
[`2a5ed4a57f0a15966a4d8beb146ef9ed98cafa7e`](https://github.com/Platinum-Pedigree-Consortium/Platinum-Pedigree-Datasets/blob/2a5ed4a57f0a15966a4d8beb146ef9ed98cafa7e/README.md).
It identifies NA12878 as G2, mother of NA12887; NA12887 is explicitly
controlled-access. Public parent data are not permission to acquire the
controlled child's reads or rerun the full trio. The separately named
NA12878-cell-line-revio GRCh38 BAM is a technical truthset benchmark sample;
it must not silently replace the reported parent material.

The [primary article](https://www.nature.com/articles/s41586-025-08922-2)
reports about11% parental read support and a maternal child haplotype.
Earlier main inspection covered selected complete results, sample/material,
HiFi preparation, de novo SV methods and data/code paragraphs, not the whole
paper or supplementary validation. This check adds original-row verification,
not independent biological validation or a complete sequence truthset.

## Runtime and next decision

Fresh cluster check at2026-10-10T00:05:56+07 found the own account queue empty.
Scratch expires22October at23:02:50+07, with one extension available; no job,
cancellation or extension action. The previous runtime check found working
samtools1.9 and Truvari5.4.0, not an installed/qualified Sniffles runtime.

The Sol6.1/max-requested scientific decision and separate Luna/max-requested
native input/source check are pending. A regional BAM must not cripple the
ordinary baseline through altered global-coverage or support thresholds.
No acquisition or launch follows from the table check alone. One-case native
success can reject a new-method rationale; one-case failure cannot establish
prevalence, clinical risk or publication readiness. The full goal is unmet.

## Actual capped header check, 00:12 local

After the source-only checkpoint, main made one request for BAM bytes 0–65535.
HTTP206 returned exactly 65,536 bytes of the 203,640,216,494-byte object,
with the same multipart ETag observed by HEAD. The unchanged prefix SHA256 is
`a6a24cbcd3fa664bfe552be5532eb4c81fbf661af771e7af036dae623bba0114`.
Prefix and HTTP headers are preserved beside the workbook, outside Git.
This is an actual public BAM-body prefix acquisition, not zero downloaded
data. It can contain bytes after the header; no alignment record was parsed,
scored or used to choose a result. Additional source-prefix charge: 65,536 B.
No whole BAM, BAI, regional alignment set, caller or cluster job was acquired.

The bounded Node helper decompressed only complete BGZF blocks needed for
the BAM text header (4,640 compressed bytes, 49,275 text-header bytes). It
found 113 text-header lines and 25 SQ records. Main read the compact field
summary: coordinate-sorted; chr3 length 201,105,948; all 13 read groups have
sample NA12878 and PACBIO platform, with SEQUELII and REVIO instruments.
pbmm2 program records name `human_chm13v2.0_maskedY_rCRS.fasta` and
version 1.10.0; whatshap 1.4 and samtools 1.14 merge provenance are recorded.
The first display of selected raw header lines was clipped. A bounded field
summary recovered the relevant metadata. The chr3 SQ record has no checksum
field. The program filename is provenance for CHM13v2.0, not independent
verification of every reference base or the paper's blood-source attribution.
Whole-file integrity and regional index access remain untested.

Main also read the complete `Calling de novo TRs` opening/method paragraphs
in the primary body: parent NA12878 is reported at 109-fold HiFi depth, and
G1 cell-line DNA is explicitly a potential artefact source. This is reported
study depth, not measured locus coverage in the public BAM.
