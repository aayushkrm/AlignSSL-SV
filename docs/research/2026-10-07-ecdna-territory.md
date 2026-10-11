# ecDNA structure–cell assignment: bounded prior-art check

**Date and scope.** 2026-10-07. Discovery window: 2025-04-07 through 2026-10-07; retain older seminal work as prior art. This note covers ecDNA/amplicon structure mixtures and quantity-versus-structure identifiability only. It does not select a method or claim a field-wide gap.

## Finding

| Evidence class | Bounded conclusion |
|---|---|
| Prior art | Bulk long-read methods already reconstruct multiple cycles and estimate or constrain their contributions. Recent single-cell methods already assign ecDNA prevalence, breakpoint evidence, or locus copy to cells. This is a substantial threat to any broad “mixture” or “quantity versus structure” novelty claim. |
| Candidate residual question | In the named A32_P/A32_R glioblastoma pair in ecLego3, does the reported EGFR change specifically assign the 18-kb EGFR exon 2–7 deletion (EGFRvIII) ecDNA to a changing cell fraction, or does it quantify total EGFR-locus ecDNA/copy without variant-specific cell identity? This is a question to check, not an established failure or novelty claim. |
| Independent truth | No public, same-sample A32_P/A32_R barcode-resolved assay with an independent EGFR-deletion label was verified in this review. The question is not presently validation-ready on the evidence found. |

## Prior-art threat and boundary

- **CoRAL** ([2024 paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11529860/)) uses long-read breakpoint graphs, cycle/walk reconstruction, subwalk constraints, copy number, and parsimony. Its paper notes that high multiplicity and overlapping amplicons can admit multiple paths consistent with aggregate copy number. It is a direct threat to broad structure-mixture claims, but does not establish exact per-cell identity for every reconstructed circle.
- **Decoil** ([2024 paper](https://pubmed.ncbi.nlm.nih.gov/39111816/)) deconvolves co-occurring ecDNA from bulk long reads, including overlapping genomic footprints, and estimates relative proportions. This closes a generic “bulk mixtures are not separated” framing. It is outside the new-window dates and retained as seminal prior art.
- **Cycle Extractor** ([2026 preprint](https://doi.org/10.64898/2026.03.10.710955); [official code and examples](https://github.com/AmpliconSuite/CycleExtractor)) reports a concrete limit: two true cycles with shared segments and very similar copy number can merge into one heavier cycle; differing copy numbers can separate them. The authors describe exact heterogeneity as difficult to formulate for cycle extraction and leave conflicting subwalk constraints for future work. This is a specific algorithmic boundary, not evidence that no other method resolves it. The preprint is unreviewed.
- **ecLego3** ([2025 preprint](https://doi.org/10.64898/2025.12.24.696443); [official code](https://github.com/cheehongsg/ecLego)) reports long-read-defined ecDNA subspecies and single-nucleus RNA/ATAC analyses in longitudinal glioblastoma models. Its cell-level abundance estimates use 3-Mb locus windows and a Gaussian-mixture model; the accessed methods do not document assigning each cell to the exact long-read-defined subspecies at that locus. It reports FISH confirmation of ecDNA status in three models and targeted PCR/Sanger for one MDM4 isoform, not an independent, cell-resolved EGFR-deletion truth set. The accessed version says data deposition was in progress. The paper is an unreviewed preprint.
- **Recent single-cell methods narrow the space further.** [ecSingle](https://pmc.ncbi.nlm.nih.gov/articles/PMC12853921/) infers ecDNA-bearing segments and copy heterogeneity from single-cell RNA allelic imbalance/outlier expression, with some WGS/AmpliconArchitect comparison. [scAmp](https://pmc.ncbi.nlm.nih.gov/articles/PMC12919090/) classifies single-cell copy-number distributions and estimates prevalence, but at locus/gene level. [scCirclehunter](https://pmc.ncbi.nlm.nih.gov/articles/PMC12686523/) uses scATAC breakpoint-positive cells as an internal reference for cell assignment; its paper states patient-level FISH validation is lacking. These are real close threats, but none of the accessed evidence establishes exact long-read-defined circle identity in each cell.
- **eccDNAscope** ([2026 article](https://doi.org/10.1016/j.canlet.2026.218735); [official code](https://github.com/Leelab-Kmmu/Single-cell-mapping-of-extrachromosomal-circular-DNA)) is a close possible challenger: its abstract/repository describe single-cell breakpoint, copy-number, and eccDNA features, with orthogonal validation of some circles. PubMed first-online date is 2026-07-15; issue date is 2026-10-10, after this cutoff. Full text and a complete workflow audit were unavailable here. Do not treat it as absent or resolved.
- Older AmpliconArchitect remains seminal short-read graph/cycle prior art. Cross-orientation flux in the native recurrence implementation is already controlled and is explicitly out of scope; no generic recurrence/error-mixture lead is reopened here.

## One cheap kill test

Before proposing analysis, inspect the ecLego3 A32_P/A32_R methods, deposited-data links, and official code for any **same-cell barcode plus EGFR exon 2–7 deletion-specific** measurement. Kill this candidate if the available cell-level signal is only total EGFR-locus copy/abundance, or if no independent deletion label and matching raw data are available. The accessed methods do not document such an assignment, and the accessed version says deposition was in progress. This is a paper/code feasibility check only; no data download or experiment was done. It tests this named question, not universal absence.

## Independent-validation feasibility

**Current status: not verified / not executable from the located public evidence.** ecLego3’s reported FISH establishes ecDNA status in selected models, not the EGFRvIII sequence in individually identified A32_P/A32_R cells. Its targeted PCR/Sanger validation concerns an MDM4 isoform. scCirclehunter’s breakpoint-positive cells are an internal assignment reference, and the paper reports no patient-level FISH validation; this is not independent truth for A32 EGFRvIII. Public scAmp/ecSingle/scCirclehunter resources may support locus-level prevalence or copy checks, but the reviewed records did not establish matched A32 samples with a variant-specific cell label. A future independent test would need matched A32 material, a per-cell EGFR deletion assay, and an orthogonal sequence/structure confirmation. That material and route are not verified here.

## Read scope and audit trail

- Search window: 2025-04-07–2026-10-07 inclusive. Dates checked through PubMed/NCBI; eccDNAscope is in-window by first-online date, not by issue date. Decoil and older graph-based work are retained as prior art.
- Exa: 3 distinct-angle searches × 10 requested results (30 slots); 3 fetch calls, 5 URLs. Firecrawl paper search: 2 × 10 requested results (20 slots); duplicates included. Result slots are not papers read; combined search output was truncated, so not all results are claimed reviewed.
- NCBI Entrez: 4 successful requests (9-record summary; exact-title Decoil search; Decoil summary; 2-record summary). One local launch attempt used an unavailable `python` command and was corrected with `python3`; it was not an Entrez call.
- Firecrawl: 4 paper inspections; 3 full-text-read attempts returned no passages; 12 direct URL scrapes. Eleven returned useful content; one HGSOC page returned title only. Scite: 1 search attempt stopped at a paid-plan/free-trial requirement; no evidence from Scite is used.
- Full/relevant methods were read for Cycle Extractor, ecLego3, scCirclehunter, scAmp, ecSingle, and CoRAL. Decoil was checked via metadata/abstract/method excerpt. eccDNAscope was checked via abstract/snippets, repository README, and two scripts—not full text. HGSOC long-read/methylation work was checked via abstract/metadata only; its article page yielded title only. It is not used to support a topology claim.
- Requested worker configuration (GPT-6 Luna/max) is **not attested**; this worker did not subdelegate. No raw genomic data, installation, cluster use, experiment, test, commit, or push occurred. Only this assigned note is authored by this work; other dirty-worktree files were left untouched.

**Disposition.** Retain only the named A32 EGFR-variant-to-cell question as a conditional, cheap-to-kill residual. It is not novelty-cleared, not independently validated, and not a selected workstream. No inference of novelty is drawn from search absence.

## Main follow-up: reported S3 merge and exact-input gate

Main independently fetched the [Cycle Extractor v1 full text](https://www.biorxiv.org/content/10.64898/2026.03.10.710955v1.full)
at a 42,000-character limit, reading optimization/subwalk/traversal, the
heterogeneity paragraph and S3 caption, and Discussion. The payload ends
during supplemental Lemma S1.1; no complete supplement/PDF coverage claim.
It reports merging two simulated shared-segment cycles at **similar**, not
necessarily exactly equal, copy numbers. Cell-line exact circle sequences
are unknown; their LWCNR is objective-related, not independent structure truth.
No native failure was reproduced here. One further Exa repository-page fetch
was only cached README content; live immutable files below supersede it.

The [independent review](2026-10-07-territory-independent-review.md) and
[max-effort-requested decision](2026-10-07-inversion-centromere-decision.md)
allow considering the original synthetic example as a native comparator
falsifier, provided its exact generating cycles, graph, CNs and supplied
subwalk evidence are recovered. Human clinical labels are not needed to
test recovery on this original synthetic input, but empirical accuracy,
per-cell identity and a new method require separate evidence. Equal-fitting
decompositions, objective mismatch and a solver failure are different claims.
CoRAL/Decoil must get the same evidence; another simulation panel is not
a comparison on this exact case. Known-limit replication is not novelty.

Main public API check pinned [CycleExtractor](https://github.com/AmpliconSuite/CycleExtractor/tree/1b29b338fc2bab437ce56b48b1829bf28f73601a)
at `1b29b338fc2bab437ce56b48b1829bf28f73601a` (August 3, 2026).
Recursive tree returned `truncated=false`: exactly three blobs, `CE.py`
(182,143 bytes), `README.md` (9,985), and `GBM39EC_EGFR_graph.txt` (1,480).
Read README and graph in memory, verifying Git blob SHA-1 respectively
`250defa886833cb276fcce4f1c724371a4a44452` and
`7c72f72575608b8c9800af9715e07ea20c48f21a` before display.
The graph contains seven sequence edges and two subwalk constraints, but
no pair of generating S3 cycles or S3-case provenance. README's sample-data
links are not files in this complete pinned tree. Its example cycle is a
prediction, not generating truth. Do not substitute GBM39 for the S3 case.
`CE.py` was inventoried, not read or executed; solver availability is not a
scientific outcome. README advertises HiGHS as an option, so do not infer
that a paid solver/license is the only route from cached text.

The exact-input gate is **UNRESOLVED in the inspected pinned repository**.
No comparator run, invented graph, solver install, biological download or
campaign follows. This is not evidence that no S3 inputs exist elsewhere,
or that the reported study is invalid. CLI access stalled; direct public
API/raw-source access succeeded as the alternative. Only this run's own
stalled local diagnostic processes were stopped; no cluster/user jobs.
