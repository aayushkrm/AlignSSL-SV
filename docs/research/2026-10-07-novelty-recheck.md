# Novelty recheck after complete truth preparation

Date: October 7, 2026. This is a source-based triage, not a selected method,
outcome experiment, systematic review or publication finding. Main read the
full current goal and continued to exclude DeepSV as a scientific foundation.
The 11,490 prepared records do not make the current direction novel.

## Evidence that prevents easy pivots

| Proposed direction | Load-bearing prior work | What a new study would still need |
|---|---|---|
| Generic benchmark stability / parameter sensitivity | Maden et al. compare three frameworks, five callers and two samples, emphasizing framework-dependent classifications and metrics. Published September 23, 2026. [Primary paper](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014824). | A distinct, consequential failure mechanism or estimand; not another parameter sweep or ranking table. |
| Several smaller variants represent a larger SV | ASVBM introduces joint local validation and latent positives. [Primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC12271604/); [PubMed record](https://pubmed.ncbi.nlm.nih.gov/40687987/). vcfdist jointly evaluates small and structural variants, including phased sequence comparison. [Primary paper](https://link.springer.com/article/10.1186/s13059-024-03394-5). | An unaddressed equivalence/identifiability problem and independent evidence; reproducing local harmonization alone is not a contribution. |
| Caller ensemble or confidence ranking | Guo et al. evaluate 14 short-read tools, pedigree truth and ensembles. [Primary paper](https://link.springer.com/article/10.1186/s13059-026-04219-3). SV-MeCa already uses caller-specific quality features with XGBoost for consensus ranking. [Primary paper](https://link.springer.com/article/10.1186/s12859-025-06246-6). | A different useful target or demonstrable generalization/calibration mechanism, fair native/classical baselines and valid independent labels. Ranking probabilities are not proven calibrated risks. |
| Generic pre-phased SV genotype likelihoods | SVUPP combines read phasing with genotype likelihoods and tests against other genotypers. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12771361/); [PubMed record](https://pubmed.ncbi.nlm.nih.gov/41134129/). | A distinct genotype target or identifiable failure mechanism, not merely adding phasing to the same model. |

These are novelty challenges, not proof that every possible contribution in
these domains is exhausted. Main's inference is narrower: none of the four
generic formulations above establishes a new publication contribution.
Do not promote benchmark instability merely because the coverage screen has
not yet yielded a result.

## Implications for the fixed screen

The approved preparation completed, but released-callset coverage remains a
development-only rejection diagnostic. It is not a controlled same-read
candidate ceiling, a new algorithm, caller superiority evidence or independent
confirmation. Finish only essential reviewed validation and the already-fixed
diagnostic within the recorded finite limits/deadline. Do not add an open-ended
pipeline project or broad acquisition to preserve this direction.

In particular, vcfdist's demonstrated dependence on cross-size variant context
strengthens the existing requirement to adjudicate residuals using original
full source context. It does not authorize changing frozen screen units or
metrics, pooling caller haplotypes, or crediting unresolved residuals as misses.
This is an inference from the primary paper, not a new observed result here.

The new PLOS paper reports the same Q100 VCF filename but compressed SHA-256
`abdd0d95470fe02cf6cf4872484f1bce1ea9b0a80ba13f47e51033eb2d16e8f9`.
Our frozen compressed hash is
`edb582ceec508f6d745acd0a8c522ee4f235ff5bf4754ba6bdc4c3abee122b5c`.
The BED hash matches our pin. Do not claim identical VCF bytes from filenames
or infer corruption from this discrepancy. No redownload or input replacement
was made; the cause is unresolved. [Paper data-availability statement](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014824).

## Research-tool execution and checked sources

Main used the Exa Search and Life Sciences Literature Entrez skills for this
triage. Four Exa searches requested 25 result slots across representation,
named prior art and uncertainty/ensemble angles. Slots are not 25 independent
or fully read sources. Primary pages were fetched selectively; the table only
uses claims supported by those responses. PubMed independently resolved
ASVBM/SVUPP/vcfdist and confirmed September 2026 PLOS/SVPG publication records.
Generic search hits and source-level assertions were not accepted as outcomes.

The search encoded publication years 2025–2026, with current date October 7,
2026; it was not an exhaustive last-twelve-month review. A December 2026 issue
date in PubMed with July electronic publication and unrelated clinical/LLM
hits were filtered by relevance, not treated as new SV methods. Exa's January
1 ASVBM date is not accepted as exact publication date; PubMed links its DOI
`10.1016/j.csbj.2025.06.045` and June 2025 electronic history.

Checked but not evidence-bearing: the first Entrez call failed because
`requests` was missing. `python -m pip` was unavailable in the project venv.
Main used the installed `uv` alternative to add requests and dependencies to
that existing venv, then reran the queries successfully. No raw PubMed JSON/XML
was saved, and no failed lookup is cited as evidence. Firecrawl CLI was not
used or assumed installed. No plugin was installed just to increase tool count.

Verified literature-runtime versions after installation: requests 2.34.2,
urllib3 2.8.0, idna 3.20, certifi 2026.7.22 and charset-normalizer 3.5.1.
These are retrieval dependencies, not a changed biological experiment stack.

PubMed esearch returned five named-query IDs. PMID 23074049 is an unrelated
pediatric-ultrasound article and was excluded. The broad recency query returned
ten IDs, including PMID 42777077 (PLOS), 42768106 (SVPG), 42260234 (Sniffles2
protocol) and 42719292 (ContextSV); the latter two were metadata-only leads,
not efficacy evidence used here. Query responses preserved their source and
canonical-URL fields in tool output; this note does not invent unsupported
identifier mappings.

Next high-impact review: challenge whether the remaining fixed diagnostic is
still worth its bounded cost. No new method or expensive campaign is selected
by this source triage.
