# Controlled non-human SV opportunity scout — 2026-10-16

## Decision

**Scoped STOP: no scientific study is nominated from these four search
angles.** This is not an exhaustive resource census and does not mean that no
usable resource exists. Keep one conditional, metadata-only diagnostic for
the Sc2.0 synVII panel: first census all screened derivatives, quantify
missingness, and test whether an eligible same-dosage structural contrast is
identifiable. Missing records are `UNKNOWN`, never negative. A missing field
for one clone does not by itself kill that diagnostic.

The 2025 dosage paper is now full-text checked. It directly covers broad
SCRaMbLE dosage-to-aneuploid-phenotype mechanisms. A narrower structural-
architecture question at matched dosage could remain distinct, but this
scout has not established that the synVII accession contains a usable,
unbiased contrast. No raw data was downloaded.

## Search and source limits

| Item | Count and scope |
|---|---|
| Date window | 2019-01-01 through 2026-10-16 inclusive: 7 years, 9 months, 15 days |
| Distinct search angles | 4: yeast experimental evolution; designed yeast rearrangements; engineered bacterial rearrangements; causal reconstruction in microbial evolution |
| Search requests | 18 search calls: 8 Exa, 4 Parallel Search, 4 Scite attempts, 1 web search, and 1 Firecrawl web search. All 4 Scite attempts were denied by its paid-plan requirement. |
| Query strings / result slots | 23 submitted strings or attempts: 8 Exa, 8 Parallel Search, 4 Scite, 2 web, and 1 Firecrawl. Exa requested 60 result slots; these are not 60 unique sources. Two direct accession-page opens also failed to resolve. |
| Primary full-text retrieval | 7 distinct article URLs: 6 initial URLs (5 readable; the 2025 iterative-SCRaMbLE Nature page returned 303) plus the 2025 dosage paper via PMC. Firecrawl's paper index had no full text for that paper; its PMC full text was retrieved at [PMCID PMC12678449](https://pmc.ncbi.nlm.nih.gov/articles/PMC12678449/). |
| Execution | Source review only. No raw-data download, install, SSH, compute job, or Git write/commit/remote action. Requested Luna/max was not backend-attested; Exa and Parallel Search ran concurrently. |

## Candidate screen

| Resource and public path | What the primary source supports | Why it does not pass |
|---|---|---|
| Sc2.0 synVII SCRaMbLE derivatives, 2023: [Cell Genomics paper](https://www.cell.com/cell-genomics/fulltext/S2666-979X(23)00147-7); data statement names CNGB CNSA accession **CNP0002230** ([CNSA portal](https://db.cngb.org/cnsa/)) | The paper describes many derivatives with varied rearrangements and phenotype screens. Its data statement lists genome, transcriptome, proteome, Hi-C, and synVII design/physical-sequence data under CNP0002230. This is the strongest multi-event yeast candidate in the fetched sources. **The accession's member manifest and clone-level join were not inspected.** | Do not infer a complete cohort from the accession alone. The 2025 primary full text ([PMC12678449](https://pmc.ncbi.nlm.nih.gov/articles/PMC12678449/)) directly overlaps broad SCRaMbLE dosage-to-aneuploid-phenotype inference: phenotype-selected loss-of-function screening on an extra synthetic chromosome; PCRTag screening and WGS of some recovered clones; overlapping deletion regions; targeted deletion and dosage-increase tests. It reports nonlinear multi-gene effects for heat tolerance and rapamycin resistance. This closes broad dosage-mechanism novelty, but does not by itself rule out a distinct architecture-at-matched-dosage question. The paper declares WGS/RNA-seq reads at [PRJNA1212694](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1212694). |
| Yeast SCRaMbLE alkali tolerance, 2019: [Microbial Cell Factories paper](https://doi.org/10.1186/s12934-019-1102-4) | Seven tolerant strains came from independent SCRaMbLE experiments. The study used PCRTag analysis and whole-genome sequencing, found a shared 11,448-bp deletion in four strains, and tested an SPT2 deletion that increased alkali tolerance. | The paper already tests the most direct causal explanation. The fetched source did not establish a public raw-read path or a larger complete clone-by-phenotype panel. A generic rearrangement-to-fitness analysis would add little. |
| Vibrio natriegens chromosome fusion, 2024: [Nature Communications paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11066055/); raw reads and references at [NCBI BioProject PRJNA948340](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA948340); growth/microscopy values in Supplementary Data S4; proteomics [PXD049476](https://www.ebi.ac.uk/pride/archive/projects/PXD049476); PFGE/microscopy record [10.17617/3.BRUKU](https://doi.org/10.17617/3.BRUKU) | The engineered synSC1.0 fusion was checked by Sanger sequencing, pulsed-field gel electrophoresis, and long-read whole-genome assembly. The paper reports growth and microscopy data, proteomics, and replication-pattern analyses. | This is a well-confirmed, public, phenotype-linked event, but it is one fusion genotype. The paper already tests rapid growth and reports little growth or morphology change in the assayed conditions. No distinct, decision-changing mechanism remains for a cheap reanalysis. |
| E. coli insertion-sequence evolution: [primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12065110/); paper-declared DDBJ BioProject PRJDB17574; scripts/plasmid sequence at [Figshare 10.6084/m9.figshare.27800133](https://doi.org/10.6084/m9.figshare.27800133) | The paper describes engineered IS activation, long-read sequencing of accumulated strains, and public raw reads plus assembled genomes. The data statement gives a direct project accession and code deposit. | The fetched evidence did not establish a complete clone-level phenotype join for a specified estimand. This is an access/label uncertainty, not evidence that records are absent; sequence confirmation need not be orthogonal for every clone if assembly evidence supports the chosen event labels. |
| E. coli DOC14 inversion, 2022: [Microbiology Society paper](https://doi.org/10.1099/mic.0.001232) | The primary study reports altered sensitivity to several antimicrobials, with no growth or morphology effect in rich medium without drug. | One inversion-bearing mutant and its parent do not provide a multi-event inference set. The fetched text did not establish an independent sequence-confirmation protocol or an open clone-level data path. The paper itself reports the event’s measured phenotype. |

Two additional search hits were not accepted as evidence. The 2025 iterative
SCRaMbLE article returned 303 on full-page retrieval, so its design and data
cannot be assessed here. A 2025 yeast-hybrid preprint reports Manta-called
structural variants and gamete-viability measurements in its search result;
its evidence and label join were not verified.

## One conditional cheap diagnostic

The only retained diagnostic is a **public-record census and eligible-contrast
audit** for CNP0002230. It is not a selected scientific study and was not run.
It could change the allocation decision: a reconstructable denominator plus
an identifiable, dosage-matched structural contrast would justify one focused
mechanistic review. Incomplete per-clone fields are reported as missing; they
do not automatically close the route.

| Gate field | Frozen definition |
|---|---|
| Public path | Start with the 2023 paper's supplement and its named CNGB CNSA accession CNP0002230. The accession-level file manifest was not validated in this scout. Do not claim a file is present until its record is opened. |
| Population / denominator | Census every derivative included in each phenotype screen, including non-hits, exclusions, and repeated assays where recoverable. Record the full N screened per assay/condition before analyzing clone-level joins. A population claim requires a complete, unbiased denominator for that target population. |
| Endpoint / missingness | Report N screened, N with phenotype, N with assembly-supported structure, N with orthogonal confirmation (if any), and N eligible for each prespecified contrast. Give missingness by field and clone. Missing is `UNKNOWN`, not a negative phenotype or absent rearrangement. Keep assay, condition, replicate, and stable-ID links explicit. |
| Event evidence | Use assembly-supported event labels when they resolve the event needed for the estimand. Track evidence tier per clone. Orthogonal confirmation is required only where the assembly/call is ambiguous or the chosen claim depends on resolving that ambiguity; it is not a universal clone-level gate. |
| Controls | Include the parental synVII strain, synVII disome, euploid BY4741, and any sham/assay controls only where the paper actually measured them in the same relevant assay and condition. Report absent or unmatched controls; do not impute them. |
| Diagnostic threshold | Continue to focused review if the census is reconstructable, field-level missingness and ascertainment are explicit, and at least two distinct assembly-supported structural configurations share the relevant dosage stratum and have replicated phenotype measurements against suitable same-assay controls. This supports only the defined eligible contrast, not an automatic whole-population causal claim. |
| Selection-bias limit | If clone inclusion, sequencing, or phenotype measurement depends on the outcome, report that selection. Do not generalize from recovered/selected clones to all screened derivatives. A conditional eligible-subset diagnostic is acceptable only if its eligibility rule and target estimand are explicit and the selection process does not make that contrast non-identifiable; otherwise treat the contrast as exploratory and do not make a population claim. |
| Kill switch | Close this route if the denominator cannot be reconstructed for the intended claim and no identifiable conditional estimand remains; if no same-dosage structural contrast with usable phenotype/control data exists; if missingness/selection makes that contrast non-identifiable; or if the specific proposed mechanism is already covered by the 2025 study. A missing record for an individual clone alone is not a kill switch. |
| Cost and state | Metadata/supplement audit only; no raw reads, installation, or compute. Not executed in this source-only scout. |

## Scope and ambiguity

The study accessions above are those named by the papers. I did not inspect
their member manifests or download files. Therefore this note does not claim
that each accession contains every clone, breakpoint, or phenotype needed for
the proposed join. The 2025 dosage paper was retrieved in full from PMC after
the publisher page and Firecrawl paper index failed; its broad mechanism
overlap is established, but the CNP0002230 crosswalk and any narrower residual
are not. Scite was unavailable on the connected plan. Conclusions are limited
to the four stated search angles and the primary sources fetched; they do not
establish absence of other resources.
