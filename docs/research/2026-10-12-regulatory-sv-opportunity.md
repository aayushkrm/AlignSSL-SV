# Regulatory SV effects: bounded opportunity check

Date: 2026-10-12. Main's separate source check; not a selected study.

## Current position

Later primary-source finding: the October9 [Swap-seq preprint](https://www.biorxiv.org/content/10.64898/2026.10.08.756856v1.full.pdf)
already benchmarks actual edited alleles with AlphaGenome, Borzoi and Enformer.
Main stops the **generic regulatory-deletion effect benchmark** as a proposed
new contribution. The source-table reproduction below is retained as a completed
bounded check, not a paper lead. A distinct structural/context question would
need evidence beyond this new prior art and Xu's earlier engineered MYC study.

Latest finite source check: [actual result and complete small audit](../../results/sven_source_table_audit_20261012/README.md)
reproduces the reported absolute-expression correlation. The two plotting
sheets have no identifiers or reference predictions; the proposed effect-
specific contrast is not identifiable from them. This does not demonstrate
model failure. Independent [premise review](2026-10-12-opportunity-screen-independent-review.md)
accepts one cheap discriminating check, defers study selection, and corrects
the scouts' overly strict clinical-outcome requirement. Review of the exact
actual table result and the intervention-data worker remain pending here.

Keep the HG002 annotation-exclusion study stopped. Its accepted DNA and software
are reusable inputs, not a reason to continue that study. Two completed scouts
found no supported clinical lead in [breakpoint uncertainty](2026-10-12-breakpoint-uncertainty-opportunity.md)
or [balanced rearrangements](2026-10-12-balanced-rearrangement-opportunity.md).
Their narrow clinical endpoints do not close molecular or methodological research.

One different question remains under scrutiny: do current models predict the
expression change caused by a DNA structural allele, beyond the gene's usual
expression? A useful negative result would delimit an actual model-use claim;
a useful positive result would establish reliable SV-effect prediction on
independent interventions. Neither outcome is established. Generic criticism of
sequence-to-function expression models is already strong prior art.

## Evidence and competing interpretations

| Primary source | What was checked | Implication |
|---|---|---|
| [SVEN, 2024](https://www.nature.com/articles/s41467-024-55392-7) | Main text, methods, data/code availability. The 94,366 SV–gene pair benchmark compares predicted absolute log10 expression with observed carrier RNA; reported Spearman correlation is 0.921. Its output includes reference–alternate fold changes. The gene-expression regression test holds out chromosome 8. Five selected, predicted-upregulating deletions were tested with CRISPR: four correct directions, two significant; qPCR uses four technical wells. | The large correlation does not alone measure causal effect-size accuracy. The CRISPR tests are genuine additional evidence and must not be erased. This is an estimand limitation, not an observed model failure or misconduct claim. |
| [AlphaGenome, published 2026-01-28](https://www.nature.com/articles/s41586-025-10014-0) | Main benchmark sections, discussion, and availability read. Actual eQTL magnitude and sign evaluation and CRISPRi enhancer-link tests are present. Personal-genome evaluation is explicitly left open. Detailed protocols are in the supplement, not the short main Methods. | It would be false to say all modern evaluations score only absolute expression. No supplementary training/leakage audit completed here. CRISPRi is not a DNA deletion assay. |
| [Tu et al., posted 2026-02-03, preprint](https://www.biorxiv.org/content/10.64898/2026.02.01.702969v1.full) | Main results and Online Methods read, including splits and personal-sequence construction. Across-individual expression is weak relative to a cohort-trained cis-genotype model; accessibility performs much better. The construction excludes SVs, symbolic alleles, and copy-number variants. | Generic personal-expression failure, pooled-versus-within-gene metrics, and supervised readout rescue are not new. The explicit SV exclusion leaves a task boundary, not proof of novelty or data readiness. The trained cohort baseline has more supervision than zero-shot models. |
| [SVEN author repository](https://github.com/gao-lab/SVEN) | README and full recursive tree metadata checked at tree `29ac42b49ac13d2e1d09fe71f86f3aa92a44fdc0`. | Full and fast modes differ; authors require full mode to reproduce the paper. No installation or model download. Figure-level controls should precede hundreds of GB of model resources. |
| [Swap-seq, posted 2026-10-09, preprint](https://www.biorxiv.org/content/10.64898/2026.10.08.756856v1.full.pdf) | Relevant full-PDF Results, actual-edit definition, model scoring, discussion and availability read. Direct RNA FlowFISH effects and reference–alternate predictions are compared. | A generic exact-deletion effect benchmark or distal expression-model failure is already present. Preserve the preprint's limits; this is not independently replicated here. |

## Cheapest discriminating check

First inspect the published small figure-source tables, if accessible. Ask
whether they include reference and alternate predictions, gene and sample
identifiers, and the observed values. A plot-only pair of absolute values can
reproduce its correlation but cannot identify a causal SV effect. Do not invent
a reference outcome or use other carriers as unadjusted counterfactual truth.
If the necessary fields exist, compare the unchanged reference prediction with
the alternate prediction on the same rows, and report a gene-balanced summary.
That is a finite benchmark-specific audit, not an intervention result.

In parallel, a bounded worker checks exact engineered SVs with matched reference
or sham expression outcomes in [Xu et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9810360/).
Its separate data-feasibility note is pending at this checkpoint. No clinical
diagnosis endpoint is required for a meaningful regulatory-mechanism study.
Measured intervention effects, independent clones, appropriate context, and
genuine negative controls are required for the causal version of this question.

Before any inference campaign, independent review must establish a question
beyond the published personal-genome limitation, identify strongest permitted-
input controls, and separate training-locus exposure from intervention-outcome
reuse. Match cell context and map gene coordinates on each actual alternate
allele. Do not turn coordinate/cropping errors into biological findings. Missing
assays are UNKNOWN, not zero effects. Replicates from one clone or gene cannot
be counted as independent alleles. Test labels must remain untouched during
selection and tuning. Null, contrary, and out-of-scope outcomes remain visible.

Stop or redirect if the public material cannot support a valid contrast, if
only the already-known generic expression limitation remains, or if a stronger
existing method already establishes the proposed contribution. Do not require
a pre-proved failure before a cheap test; require a meaningful answer either way.

## Search and access limits

- Discovery window calculated before searching: 2026-10-12 minus 12 calendar
  months = 2025-10-12. Older strong controls allowed.
- Exa: four initial scientific queries requested 10, 10, 10, and 8 results;
  a fifth source-location query requested 5; a sixth exact-DNA-edit screen
  requested 10. Total 53 slots, not 53 unique papers read.
  Many results repeat AlphaGenome or concern SNPs and CRISPRi. No field-wide
  absence claim. Full load-bearing SVEN sections and Tu main/Online Methods
  were read; AlphaGenome main benchmark sections were read, not its supplement.
- Life Sciences Literature / NCBI: one broad date-limited search returned 10
  PubMed IDs; compact summary truncation prevented a complete ten-item review.
  PMID42842680 identifies an October 2026 myeloma enhancer-rewiring paper,
  DOI10.1126/sciadv.aeg9610, PMC13644794. Mixed XML abstract text was incomplete;
  its results are not relied on here. No raw NCBI response was saved.
- Publisher Source Data ZIP is linked, but web fetch failed with cache miss.
  A 30-second HTTP HEAD attempt timed out with zero bytes. Author GitHub
  metadata was the working alternative; it does not establish ZIP contents.
  This access failure is not evidence of absent data. No scientific data body
  or source-table values have been downloaded or analyzed.
- Maintained Sol6.1/high-requested reviewer is checking the scientific premise
  separately; no acceptance is claimed at this checkpoint. Worker Luna/max
  and orchestrator/reviewer settings are requested, not independently attested.
- No jobs, model acquisition, installs, historical-result edits, or billing
  changes. Full publication goal remains active and unmet.

## Later access recovery and completed source-table check

The source-location attempt initially used PMID39738006, an unrelated antibody
paper; it was excluded. A DOI-based Europe PMC API lookup established the
correct PMID39738063 / PMC11685779. Its fullTextXML lists the embedded source
ZIP size and MD5. Europe PMC supplementaryFiles supplied a 14.14MB wrapper;
the 10.11MB Source Data member matches that listed MD5. This working alternative
supersedes the earlier access limit above, without erasing either failed attempt.

The read-only, capped script and six synthetic rank/cap controls use bundled
Python/openpyxl, preserve every numeric pair, and alter no author workbook.
First draft SciPy import failed before analysis; standard-library average-tie
ranks resolved it with no install. Actual rho0.9208479244746964 for Figure3a
rounds to0.921; FigureS4 rho0.8410704403295711. Each sheet contains94,366 pairs
and exactly two columns. No gene-balanced, reference-only, or causal contrast
can be constructed from those columns. Do not download the full model merely
to produce a comparison lacking measured counterfactual truth. Small audit,
reproduction command, original-source hashes and failure transcription are
tracked; original14MB archive stays outside Git. No new study is selected.

## Fresh prior art changes the proposed contribution

A distinct exact-deletion-screen query recovered Swap-seq and a 2025 paired
prime-editing study. The latter reports a genome-wide fitness screen, not
matched endogenous RNA changes; its reporter assay primarily measures editing
efficiency. It is not silently substituted as an expression truth set.
[Weller et al., posted 2025-11-04](https://www.biorxiv.org/content/10.1101/2025.11.03.686307v1.full).
Only its abstract, initial Results and data/code section were read here.

Swap-seq, posted2026-10-09, is directly load-bearing. It designs208 edits,
measures117, and benchmarks48 significant edits across18 elements at one
PPIF locus in THP-1 cells. The allele replaces50–250bp with a71bp barcode
cassette: it is not a pure deletion. Its scoring explicitly includes that
actual cassette and maps alternate outputs back to reference coordinates.
AlphaGenome uses1Mb context; Borzoi and Enformer use their own windows, with
two distal elements outside Enformer's window excluded. The published positive
subset shows strong proximal prediction and poor distal prediction. These
findings are authors' reported results, not our reproduced model runs.

Relevant model choices, actual-edit sequence, subset selection, biological
versus barcode/technical replication, and missing edits would matter for any
reuse. Nonsignificant edits are not proven zero effects. Expanding the subset
from48 to117 at one locus alone is not established as a new contribution.
The paper lists GEO GSE348496, GSE347552 and
[EngreitzLab/Swap-seq](https://github.com/EngreitzLab/Swap-seq); body/table access
and complete coordinate/replicate joins are not verified by that listing.

The first HTML fetch returned only abstract/front matter, so it was not treated
as full methods. Initial PDF extraction reached its110,000-character cap;
expanded extraction returned149,396characters through the reference end.
Main read the load-bearing benchmark, edit-definition, model-scoring,
discussion and availability sections, not every wet-lab protocol or supplement.
Exa's January1 timestamp is wrong for both preprints; their actual posting
dates were read from primary text. This additional evidence prevents an
unsupported generic novelty claim before any model download or inference.
The retained independent reviewer was informed. Its extension and the Xu
worker's finite crosswalk are pending; no global field closure follows.

## Completed integration

The maintained review extension now accepts the **scoped reported** table
reproduction and independently accepts STOP for the generic deletion-effect
contribution after reading relevant Swap-seq primary sections. It read code,
tests and audit.json and independently ran synthetic controls; it did not
independently reopen the real workbook or recompute its correlations. Original
review text and its earlier six-test checkpoint remain intact. Main's later
expanded eight controls pass. Do not promote that acceptance to causal accuracy.

The [Xu intervention-data worker](2026-10-12-regulatory-sv-intervention-data.md)
completed its finite metadata check. It identifies37 clone RNA accessions,
two parental RNA records and15 partner regions, but does not make a verified
clone–exact-junction–numeric-expression join. A large104.5GB series archive is
not acquired merely because its metadata exists. No distinct runnable
translocation contrast beyond published work was defined by this check.
Measured post-edit contact ABC has extra information; it is an oracle-style
control, not a fair sequence-only baseline. A future question would need matched
permitted-input controls, including predicted-contact approaches where relevant.
These source limits do not establish that exact alleles are absent everywhere.

Main accepts non-selection of these bounded candidates and the review's
clinical-gate correction. No study, model acquisition or inference job follows
from this pass. No positive/model-failure result or field-wide closure is
claimed. The publication objective remains active and unmet; fresh meaningful
directions may still be pursued, without reopening the stopped HG002 premise.
