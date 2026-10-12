# Published INV benchmark: fixed-case feasibility

Date: 2026-10-13  
Scope: published paper and Supplementary File 3; metadata-only check for existing caller outputs. No call records were read or scored.

## Decision

One fixed, source-supported miss is suitable for a later, read-only check against the published callsets: the first HG002 Tier 1 row in Supplementary Table S10, `chr2:240,685,775-240,688,980` (3,205 bp; GRCh38/hg38, as labeled in the figure).

This is a benchmark residual, not a new result. The supplement reports eight Tier 1 inversions missed by its caller panel and says all eight have Strand-seq and assembly signals. It does not establish that this particular allele is free of repeat or assembly-alignment ambiguity. Treat the case as eligible for a bounded follow-up, not as validated novelty. No job or new method is justified here.

The row was fixed by document order before inspecting any caller VCF contents. The table prints coordinates; no coordinate convention conversion is assumed.

## Evidence and limits

| Evidence in the source | Supports | Limit for this case |
|---|---|---|
| Table S10 and its accompanying text | Tier 1 label; all eight listed loci were not detected in the described panel. | “All callers” means this supplement’s 20 results, not every caller in the paper. |
| Figure S15 | chr2 example with four long-read alignment tracks and four phased assembly-alignment tracks; the figure labels GRCh38/hg38. | It does not display Strand-seq tracks or give a case-specific repeat annotation. Its image alone cannot rule out mapping or assembly-alignment artifacts. |
| Supplement text | Authors report clear Strand-seq and assembly signals for all eight Tier 1 cases. Strand-seq is a distinct evidence type for inversion orientation. | Exact per-case Strand-seq support is asserted in prose, not shown in Figure S15. Assembly evidence shares dependence with the assembly-based truth construction; it is not independent confirmation of exact breakpoints, copy state, or haplotype linkage. |

The fixed case therefore has named coordinates and build, and a source claim of orthogonal orientation support plus assembly support. Its precise structure is visually inspectable in the published tracks, but artifact/repeat exclusion is unresolved from the material reviewed. Do not call this an independently validated structural truth.

## Caller panel and output availability

The August 2026 article is the nine-caller publication. Table S10’s all-missed statement is narrower: five callers (cuteSV2, Severus, Sniffles2, SVIM, SVision-pro) × two long-read platforms (ONT, PacBio) × two aligners (Minimap2, VACmap) = 20 calling results. Keep this scope distinct from the seven-caller author preprint and from the broader publication total.

Public GitHub tree metadata contains the matching 20 HG002 VCF paths under [`data_zenodo/inv_call_5samples/30x/hg002/`](https://github.com/jamesc99/INV-Benchmark/tree/ee77a2f336bf055e5234d7565389aafda56b85cd/data_zenodo/inv_call_5samples/30x/hg002) at commit `ee77a2f336bf055e5234d7565389aafda56b85cd`. The files cover all five callers and all four platform/aligner combinations. Listed sizes total 5,980,901 bytes; the largest is 2,436,453 bytes. This confirms metadata-level retrievability only. No VCF body was fetched, so file presence does not establish which calls are present or absent. A later fixed-row comparison can use these files without downloading genomes or launching callers; the main task owns any such interpretation.

## Not the target

Supplementary Table S9 describes seven recurrent calls absent from the benchmark, each found in at least 10 of 20 results. Five are under 1 kb, below the stated Strand-seq detection range; the larger examples are in repeat-rich or centromeric context. These are not missed-presence controls and are not substituted for the fixed Table S10 case.

The earlier preprint’s chr1/chr18 Figure 5 components were detected components, not evidence of a missed allele. The stopped HG008419bp generic lead remains stopped; this case does not revive it. ComplexINV remains conditional. No evaluation scripts, native data, or source data were scored in this work.

## Source ledger

- Published article, 2026-08-01, DOI [10.1186/s13059-026-04223-7](https://link.springer.com/article/10.1186/s13059-026-04223-7). Publisher page exposed article front matter and supplement links, but not full Methods.
- Official Supplementary File 3, [publisher download](https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs13059-026-04223-7/MediaObjects/13059_2026_4223_MOESM3_ESM.docx), named `13059_2026_4223_MOESM3_ESM.docx`. Download: 4,974,841 bytes; publisher Last-Modified: 2026-07-31; SHA-256: `2361934370695d00ef6844d8f77a036bb4313ec45228909b0596d683e9cff5af`. Read-only render succeeded (13 pages); Table S10/Figure S15 visually checked.
- Render tool used bundled LibreOffice at `/Users/akm/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice` with the bundled document workflow. No source document was edited.
- Author repository [INV-Benchmark](https://github.com/jamesc99/INV-Benchmark), pinned tree commit above; tree metadata only for callset availability. Zenodo [record 17624133](https://zenodo.org/records/17624133) provides benchmark/truth-set metadata, not the caller VCFs inspected here.
- Author [bioRxiv v1](https://www.biorxiv.org/content/10.1101/2025.11.28.691176v1.full) / [Europe PMC full text](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12687780/fullTextXML) used only to check methods context and data pointers. It is the seven-caller preprint version; its panel is not transferred to the nine-caller publication.

Source transfer budget: one official DOCX, 4,974,841 bytes total; no genomes, raw reads, caller VCF bodies, or archives downloaded.
