# Acrocentric and centromeric balanced SVs: territory screen

Date: 2026-10-07. Repository HEAD: `9a58e81fbdaff790f2ddb2385ba1a21a8b6d7ca7`.
Scope: balanced Robertsonian translocations and haplotype-specific centromeric junctions. This is a bounded prior-art screen, not a novelty claim or an approved study.
The requested GPT-6 Luna/max worker configuration is not attested by this runtime. No alternate model was launched.

## Decision

No distinct, consequential native failure is established here beyond current complete assemblies and centromere panels. A mapping or junction-calling method would face direct overlap with recent native work.

One residual question, not a selected lead: **In cytogenetically balanced carriers with a sequence-resolved Robertsonian junction, does cell-to-cell activity of the two fused centromere arrays predict mitotic loss or aneuploid mosaicism after the junction and baseline ploidy are held fixed?** This could affect chromosome-stability assessment. DNA sequence alone does not measure CENP-A/C occupancy or kinetochore attachment.

`resolved haplotype-specific junction → centromere activity in cells → derivative loss / mosaicism`

The first two steps have been described. The last link is not established by the papers read here. This is a bounded inference from their reported assays, not evidence that the field has no such study.

## Native prior-art threat

| Primary work | What it already establishes | What remains for the question above |
|---|---|---|
| [de Lima et al., Nature (2025)](https://www.nature.com/articles/s41586-025-09540-8) | Complete assemblies of two t(13;14) and one t(14;21) chromosome. Karyotypes, chromosome paints and FISH support the structures. Imaging and CENP-C/A, NDC80 and chromatin assays characterize centromere activity. Both t(13;14) lines show activity at cen14; the t(14;21) line shows signal at both arrays, often within one outer kinetochore. | This closes generic assembly and junction novelty. The only dual-array example is GM03417, a Down-syndrome line with reported cell-to-cell chr21 copy heterogeneity; it cannot establish a balanced-carrier instability effect. Assembly and sequencing data are controlled in dbGaP (`phs003920.v1.p1`); imaging files are public at the [Stowers repository](https://www.stowers.org/research/publications/libpb-2501). |
| [Logsdon et al., Nature (2025)](https://www.nature.com/articles/s41586-025-09140-6) | 65 diverse genomes, 130 haplotype-resolved assemblies and 1,246 validated centromeres. The study still estimates 21.2 Mb of unresolved segmental duplications in acrocentric short arms. T2T-CHM13 and HPRC remain essential older baselines. | More assemblies or a larger panel alone do not test centromere function or chromosome loss. The unresolved sequence is not evidence for a new mapper. |
| [Gao et al., Nature (2026)](https://www.nature.com/articles/s41586-026-10841-9) | 8,340 centromeres; three chr13/22 hybrid centromeres. The NA20355 junction has HiFi/ONT, FISH and CENP-C support; two further examples come from HPRC assemblies. The authors call for functional tests. | This strongly challenges a new junction-discovery claim. The paper does not establish a clinical or segregation consequence for the hybrid junction. Official data are on [Figshare](https://doi.org/10.6084/m9.figshare.29921990); code includes [CenMAP](https://github.com/logsdon-lab/CenMAP) and [AssemblyRepairer](https://github.com/logsdon-lab/AssemblyRepairer). |
| [Rhie et al., bioRxiv preprint (2026)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13060921/) | DJCounter screens short reads in 4,172 cohort samples and about 490,000 UK Biobank genomes; known cell lines have prior T2T/FISH confirmation. Code is at [DJCounter](https://github.com/marbl/DJCounter); haplotypes are at [Zenodo](https://doi.org/10.5281/zenodo.18895340). | This is a direct detection prior, not a lead to extend. It is a preprint. Four RPC candidates could not be recontacted or declined; UK Biobank recontact was restricted. It supplies no ready, independent outcome cohort. No copy-count method is proposed here. |
| [Complete chromosome 21 centromere study, AJHG (2026)](https://doi.org/10.1016/j.ajhg.2026.05.010) | In eight families with trisomy 21 and 287 controls, small centromeres were not enriched in the case families (`p = 0.72`). | Do not repackage centromere size as the risk signal. This does not test per-cell activity on a balanced derivative. |

## Cheap kill test

Paper-only crosswalk the 2025 Nature paper’s karyotypes, supplementary cell counts and reported centromere images. Confirm whether the only dual-array signal is the unbalanced GM03417 line with chr21 copy mosaicism, while the two balanced t(13;14) lines show one active array. If so, and no balanced line has an independent cell-level missegregation measure, stop this question before any assay. The main text already points to this confound; the supplement was not read in this pass. Do not download raw images or sequence data for this gate.

## Independent validation feasibility

Orthogonal structural truth exists for three assembled ROB cell lines: karyotype, chromosome paint and FISH. This is strong within-study validation, not an independent clinical cohort. Their assemblies and sequencing data require dbGaP access; public FISH/imaging and CUT&RUN/CUT&Tag records may support a limited paper-level or image-level audit. The 2026 global study has orthogonal FISH/CENP-C validation for one of three hybrid-centromere examples, but no reported phenotype or segregation outcome for the carriers.

The biobank preprint did not confirm its four RPC candidates by participant follow-up, and UK Biobank recontact was restricted. Public HGSVC/HPRC sequences and code can validate sequence annotations, not clinical risk. Therefore, independent outcome validation is **not ready from the inspected public sources**. A later test would need consented, karyotype-confirmed balanced carriers with per-cell centromere and segregation measures; no patient-data application or experiment was made here.

## Source and execution record

- Date window verified as 2025-04-07 through 2026-10-07. Older T2T-CHM13/HPRC prior art was retained.
- Exa: three distinct searches, 10 results requested each (30 slots), plus one fetch of two Nature pages. The grouped search output was truncated; not all 30 result cards were screened. Claims above rely on the primary pages and records named here, not on result absence.
- PubMed Entrez: one eSearch returned 10 IDs; two eSummary calls covered 4 and 10 IDs. Two local invocation errors (missing `python` alias and malformed JSON) returned no evidence. No raw response was saved.
- Firecrawl: one paper search (`k=10`, six papers returned), two metadata inspections, four full-text passage requests (three had no passages; one returned 404), and six page scrapes. Main article claims were read selectively; supplements were not read except as a proposed kill-test target.
- Scite: one literature request was blocked because the connected account needs a paid plan or active trial. No Scite result was used.
- Read scope: Nature 2025 ROB article and data statement; Nature 2025 genome paper excerpts; Nature 2026 results and code/data statements; the 2026 bioRxiv preprint’s abstract, results, limitations and code/data statements; AJHG abstract and metadata. No raw genomic or patient data, installations, cluster actions, applications, experiments, commits or pushes. No reviewer approval is claimed; the main agent’s recurrence work and later review remain separate.
