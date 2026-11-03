# MEI splice interpretation: prior-art and evidence check

## Decision

Do not launch a new model or claim novelty for the generic idea of applying
insertion sequence to predict splicing. Two clinical case studies already
apply SpliceAI to a resolved mobile-element insertion. Neither case provides
an independent unbiased evaluation of generalization. A possible more specific
gap—reliably localizing consequences of long insertions when a current tool
does not return usable positions—remains a hypothesis, not a selected study.
It would need a named independent cohort, negative controls, a strong
existing-tool baseline, and a clinically meaningful endpoint.

## Primary evidence

| Study | What the authors already did | Limit for a new benchmark |
|---|---|---|
| [APC LINE-1, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11968988/) | Applied command-line SpliceAI to the full insertion; the study reports predicted aberrant splicing but no delta positions for the acceptor and donor gains. RNA assays then resolved the effect. | One selected family. The insertion consensus is supplied in Supplementary Material 1. The paper says qualified researchers may contact the authors for sequencing data. This is not an open, blinded test cohort. |
| [TCOF1 SVA, online 2025 / issue 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC12816837/) | Used SpliceAI on the SVA sequence to predict donor and acceptor sites. The study reports incorporation of roughly 750 bp of the SVA into transcripts at the predicted sites. | Two affected half-siblings share one familial allele; they are not independent variant examples. RNA had already flagged abnormal TCOF1 expression. The paper states that underlying genetic data are restricted by privacy rules. |
| [SMARCB1 SVA-E, 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8519051/) | Optical mapping and long reads identified a familial insertion; blood RNA showed abnormal splicing. | Another selected familial case. The checked text does not establish a reusable open case-level DNA/RNA dataset or a negative cohort. |

The APC and TCOF1 studies are direct prior art for sequence-aware splice
interpretation. Their reported results do not prove SpliceAI is sufficient
for all insertions, and a literature search cannot establish that no useful
gap remains. These cases were not selected prospectively as a complete panel.
Do not count relatives or reads as independent alleles; do not use these
published outcomes as a blinded final test.

The earlier [conditional scout](2026-11-03-independent-opportunity.md)
identifies additional case reports and a rare-disease MEI table. That table
does not by itself establish sample-linked RNA outcomes for every entry. A
new investment requires a broader, explicitly ascertained public inventory of
resolved insertions **with and without** measured effects, sample linkage,
sequence completeness, tissue and assay details. Unavailable patient data
must remain unavailable; do not manufacture negative examples.

## Search and tool record

On 2026-11-03 UTC, the Life Sciences Literature `ncbi-entrez-skill` searched
PubMed for mobile-element insertions, RNA/splicing and disease, and separately
for prediction and transcript-assembly terms. The first ten results of the
first query included TCOF1, BRCA1, LDLR and ATP7A reports. The follow-up
focused on primary full text, not search snippets. The `ncbi-pmc-skill`
resolved open-access metadata and text URLs for the APC, TCOF1 and SMARCB1
articles. Its lookup for the ATP7A identifier returned HTTP 429; that is a
failed lookup, not evidence that the article or data are unavailable. A web
fetch of the TCOF1 PMC page hit a CAPTCHA; the public PMC cloud text URL
returned by the skill supplied the primary text instead. Search was bounded
and is not a systematic review.

The same PubMed check found [Invas](https://pmc.ncbi.nlm.nih.gov/articles/PMC13484493/)
(2026), which already combines DNA SV calls and RNA evidence for inversion-
aware transcript assembly. It is a separate relevant baseline for any
inversion-transcript direction; it does not resolve the MEI question.
No new biological claims are accepted and no cluster job was started.
Independent challenge of this investment decision remains pending.
