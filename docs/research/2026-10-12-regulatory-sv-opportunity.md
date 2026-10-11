# Regulatory SV effects: bounded opportunity check

Date: 2026-10-12. Main's separate source check; not a selected study.

## Current position

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
- Exa: four scientific queries requested 10, 10, 10, and 8 results; a fifth
  source-location query requested 5. Total 43 slots, not 43 unique papers read.
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
