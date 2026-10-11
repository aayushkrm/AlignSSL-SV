# Centromere outcome crosswalk: three ROB lines

Date: 2026-10-07. Full goal and prior screen/independent review read. Scope: DOI 10.1038/s41586-025-09540-8 and its two supplements only.
Requested worker: GPT-6 Luna/max. Runtime model/effort is not independently attested; no alternate model was launched.

## Decision and claim limit

STOP this paper as the anchor for balanced-carrier activity-to-segregation prediction. Both balanced t(13;14) lines show cen14 activity; neither supplies a measured derivative-specific segregation outcome. GM03417 is mosaic, not a clean unbalanced-only comparator. Its imaged derivatives are not assigned to a baseline dosage class.
Missing lagging, loss and daughter-segregation evidence is **UNRESOLVED**, not a biological null. This does not reject the paper's assembly/activity findings or establish field-wide absence, novelty, risk prediction or a selected lead.

## Source pins and page key

- M: [Nature article/PDF](https://www.nature.com/articles/s41586-025-09540-8.pdf), de Lima et al., Nature 647, 952–961; online 2025-09-24, issue 2025-11-27. 29 PDF pages, 21,966,768 bytes; SHA256 `cb11570d69d64f72c2d8d4a8c0bfa029054a3911b5947386e5e9e91f95b9370b`.
- S: [Supplementary Information, MOESM1](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-025-09540-8/MediaObjects/41586_2025_9540_MOESM1_ESM.pdf), 9 PDF pages, 13,598,778 bytes; SHA256 `d2b926e946a09d461095db353dc9c84a07272bdccb074f4428fb02b2e03c5210`.
- R: [Reporting Summary, MOESM2](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-025-09540-8/MediaObjects/41586_2025_9540_MOESM2_ESM.pdf), updated 2025-07-16; 4 pages, 80,163 bytes; SHA256 `561a7417c5e5db8b8e81bb4cc9652964183787dbeb5a4bf15d170cd2bfb97437`.
Page numbers below are 1-based PDF pages. M2 = journal p953; M3 = p954; M7–9 = pp958–960. S7–9 have printed pages 8–10. R is also appended at M26–29. All pins accessed 2026-10-07.

## Baseline and junction crosswalk

| Exact line ID | Reported karyotype / baseline | Derivative-specific junction evidence |
|---|---|---|
| GM03786 | 45,XX,t(13;14); balanced long-arm dosage, not haploidy; clinically normal (M2). Baseline cell-frequency denominator UNRESOLVED. | `haplotype1-0000026`; SST1 fusion, two arrays, no rDNA; chromosome paints/FISH plus de novo assembly, breakpoint HiFi/ONT coverage and Hi-C (M2–3,19; S3–4,8). Normal chr14 lacks SST1 (M2,19). |
| GM04890 | 45,XX,t(13;14); balanced long-arm dosage; clinically normal, five miscarriages (M2). Baseline cell-frequency denominator UNRESOLVED. Miscarriages are not measured derivative loss. | `haplotype1-0000023`; same structural assay types and SST1/rDNA findings (M2–3,19; S3–4,8). Different donor and derivative, not a matched replicate. |
| GM03417 | 45 or 46,XX,t(14;21), Down-syndrome features (M2). R3 source description: 32% balanced 45,XX,t(14;21) cells. Study culture: about 10% with three chr21 copies (M2; M19C shows two dosage states). These are different snapshots; denominators, passages and their relationship are UNRESOLVED. | `haplotype1-0000006`; same structural assay types and SST1/rDNA findings (M2–3,19; S3–4,8). Mixed disomic/trisomic chr21 dosage must not be treated as a fixed balanced baseline. |

## Activity and outer-kinetochore crosswalk

| Line | Junction-linked activity assay and finding | Outer-kinetochore interpretation |
|---|---|---|
| GM03786 | Fixed-spread CENP-C immunoFISH/SIM: cen14 localization. ONT/HiFi methylation dip (CDR) and bulk CENP-A CUT&RUN/CUT&Tag agree at cen14; low cen13 enrichment without a CDR (M7–8,24; S8). | Functionally monocentric interpretation from inner-centromere/chromatin evidence. No line-specific NDC80 image/count in these sources; microtubule attachment geometry UNRESOLVED. |
| GM04890 | Same assays: cen14 activity, despite cen14 being smaller than cen13 (M7–8,24; S8). No opposite activity state is established in this balanced line. | Same monocentric interpretation; line-specific NDC80/attachment geometry UNRESOLVED. |
| GM03417 | CENP-C can overlap both arrays; CENP-A imaging and CDR/enrichment at both arrays support dual inner activity, with heterogeneity (M7–8,23–24; S8). | CENP-A/NDC80 co-imaging on the same fixed derivative (M23C): signals often lie within one outer signal, with variable profiles. One attachment site is the authors' interpretation, not a measured attachment/error rate. Four examples do not quantify “often”; two inner signals do not prove opposed kinetochores. |

For all lines, CENP-B binds both arrays (S7); it does not establish two active kinetochores. Short-read CENP-A mapping is challenged by array homology (M8); long-read methylation and imaging provide separate support. Structural validation is not functional outcome truth.

## Actual outcomes and temporal link

| Line | Derivative-specific lagging | Derivative loss | Daughter segregation | Same-cell / lineage temporal link |
|---|---|---|---|---|
| GM03786 | UNRESOLVED | UNRESOLVED | UNRESOLVED | Activity is localized on fixed spreads; no activity-to-later-fate pairing or lineage count reported. |
| GM04890 | UNRESOLVED | UNRESOLVED | UNRESOLVED | Same limit. Donor reproductive history supplies no mitotic temporal link. |
| GM03417 | UNRESOLVED | UNRESOLVED | UNRESOLVED | Same-fixed-chromosome CENP-A/NDC80 localization only. Baseline copy heterogeneity is not a tracked loss event; activity is not linked to dosage class or daughter fate. |

M5–8 states/infer stable mitotic propagation; it supplies no counted derivative fate series here. M9 discusses meiotic drive and possible transmission effects, not measured meioses for these donors. Fixed, mitotically blocked preparations (M12–13) cannot supply later daughter observations.

## Counts: assay units, not segregation trials

| Line | Fig.1 structural profiles (M3) | Fig.4 CENP-C profiles (M8 caption) | CENP-B profiles (S7) | Additional activity controls |
|---|---|---|---|---|
| GM03786 | 10 ROBs | 22 sister-kinetochore profiles from 11 ROBs | 12 ROBs | M25: 22 profiles each for 11 normal chr13 and 11 normal chr14. |
| GM04890 | 20 ROBs | 26 profiles from 13 ROBs | 13 ROBs | M25: 24 profiles each for 12 normal chr13 and 12 normal chr14. |
| GM03417 | 11 ROBs | 24 profiles from 12 ROBs | 11 ROBs | M23A: 20 ROBs; B: caption reports 11 normal copies of chr14/chr21. C: four NDC80 examples, not a frequency denominator. M25: 24 profiles each for 12 normal chr14 and 12 normal chr21. |

Distinct cell/spread counts and balanced-versus-trisomic denominators are not given for these profiles. Sister profiles are not independent cells. Outcome event counts and trial denominators remain UNRESOLVED for all three lines, not zero.
R2 reports three lines and no study-design replicates; R4 lists three chromatin-assay replicates per line, while M24 shows two CUT&RUN replicates. Keep these assay-specific statements separate; replicate identity is not resolved here. M14 inputs of 250,000 CUT&RUN or 500,000 CUT&Tag cells are bulk assay inputs, not tracked cells.
R3 describes untransformed fibroblasts; M11 calls the lines lymphoblastoid, while M12–13 describes fibroblast preparations. This internal provenance inconsistency is UNRESOLVED; do not silently assign one cell type to all assays.

## Validation feasibility and read limits

The bounded paper-only kill test is complete and meets its stop rule: no activity contrast in the two balanced t(13;14) lines plus no independent derivative-fate outcome. No independent outcome-validation set is established by these sources. Karyotype/paints/FISH support structure within this study; neither sequence nor bulk occupancy replaces a paired segregation label. Donor, derivative, culture and chr21 dosage confounding remain.
Read scope: all S1–9 and R1–4 text/captions; relevant M2–3,5–9,11–15,19,23–25 passages/captions. All 29 M pages had an outcome-term scan; this is not full visual inspection. Visually checked six pages: M7,19,23; S7–8; R3. No raw microscopy or genomic data were inspected. The listed supplements are S and R; no supplementary video was listed.
Source calls: Exa 1 known-URL fetch (Nature + PMC; 100,000 characters/page cap); Firecrawl 1 live article scrape with links. Large text responses were truncated in display; stored text was inspected in bounded sections. No discovery search or territory expansion.
Web: 3 calls—1 article open; 3 failed in-page finds; 3 failed PDF opens (main exceeded web size limit). Direct public PDF retrieval: 3 files, 35,645,709 bytes total, each capped at 25 MB; no retry. Local readers: bundled pypdf; six PDF page renders, not a raw-image download campaign. Optional fitz was unavailable; nothing installed. No quota error occurred.
Only this new repository note was written. Temporary public PDF/page-render cache is outside the repository. No raw genomes, private keys, subscription/signup, data application, assays, jobs, cluster actions, Git, commit or push. Main's ecDNA/history work is not duplicated. No new reviewer approval or novelty selection is claimed.
