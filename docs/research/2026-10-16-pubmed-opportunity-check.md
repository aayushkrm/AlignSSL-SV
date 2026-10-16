# Targeted PubMed discovery check, not a selected direction

16 October2026. Main complements the separate new-evidence scout; no experiment
is selected by this check. Today minus one calendar year gives16October2025.
The explicit publication-date window is2025-10-16 through2026-10-16.

Life Sciences Literature's `ncbi_entrez.py` submits a PubMed query for structural
variant/variation plus benchmark, mosaic or single-cell terms, sorted by
publication date, with10 returned IDs. This is a finite discovery sample, not
an exhaustive literature review. The query also returns off-topic material;
such hits do not count as SV evidence. ESummary supplies titles and dates.
Three candidate IDs are then fetched with EFetch; metadata is not taken as
proof of useful public data, independent labels or novelty.

| Candidate | Discovery value | Unresolved before investment |
|---|---|---|
| Accurate characterization of CRISPR-Cas9 genome editing outcomes and mosaicism with near-perfect long reads; Genome Medicine,15September2026, PMID42754893, DOI10.1186/s13073-026-01772-1 | The abstract reports targeted amplification-free PacBio sequencing in edited zebrafish and offspring,30 samples, over1,100× mean target coverage and inherited edited outcomes. | Public accession/actual files, target-enrichment ascertainment, independent allele labels and a contribution beyond existing mosaic/edit-outcome analysis. |
| Characterization of structural variants in KOLF2.1J iPSCs and their potential impact on forebrain organoid differentiation; Stem Cell Reports,8October2026, PMID42849453, DOI10.1016/j.stemcr.2026.103112 | Title/metadata identify a reference-cell-line structural/phenotype study. | Full scientific result, public material and causal contrast not established in this pass. Do not infer a failed differentiation mechanism from the title. |
| Structural variation in repeat elements is widespread in normal human tissues and in tumorigenesis; bioRxiv,28September2026, PMID42856253, DOI10.64898/2026.09.22.753313 | Metadata identify a recent repeat/mosaicism preprint. | Full methods, public versus controlled access, validation independence and method overlap not established here. Preprint, not peer-reviewed confirmation. |

Scientific details in the first row are supported by the retrieved
[primary abstract](https://pubmed.ncbi.nlm.nih.gov/42754893/), not metadata alone.
The reader also returns older mosaic/edit-outcome work in its references, so
generic accurate event counting is not presumed novel. The other two rows
are discovery identifiers only, not substantive evidence for a new result.

## Retrieval limits and handoff

Exa fetch succeeds for42754893. It returns SOURCE_NOT_AVAILABLE for the two
other PubMed pages. Main uses Entrez EFetch as an alternative; it succeeds and
confirms IDs/DOIs plus PMC13587479 for the CRISPR paper and PMC13648449 for
the repeat preprint. No unavailable page is cited as evidence. The compact
Entrez XML summary truncates long text strings and cannot substitute for a
full-paper read. Its first over-compact preview omitted needed article fields;
the second uses the article-list record path and a larger per-node item cap.
Neither retry saves raw JSON/XML or changes scientific material.

The scout receives these identifiers and the retrieval limits, then checks
primary methods/data availability using the connected research tools. It may
reject all three and select stronger evidence instead. No dataset, reference,
model, caller, assembly or native experiment is downloaded or run here.

Checked sources: successful PubMed ESearch/ESummary and EFetch for the three
candidate IDs; successful Exa abstract reader42754893; unsuccessful Exa readers
42849453 and42856253. Only the supported first-row abstract carries a scientific
claim in this note. Full research goal remains active and unmet.
