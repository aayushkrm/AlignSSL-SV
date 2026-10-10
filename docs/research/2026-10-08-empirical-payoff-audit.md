# Scientific-payoff audit: fixed HG002 Q100-added screen

Date: October 8, 2026. Status: strategy audit only; no genomic source was
opened or parsed, and no result was scored.

Main's later metadata check: the bioRxiv API reports v1 posted October 1,
2026. September 23 in the DOI is not the posting date. Main's separate
[source/prospective-protocol note](2026-10-08-metadata-census-protocol.md)
records this check and the relevant primary methods read.

## Decision

**One bounded diagnosis of the metadata stop is worth considering; the fixed
screen is not yet worth reopening or scoring.** The prepared 11,490 truth rows
remain provisional. The signed-`SVLEN` check failed before a validated
denominator, caller coverage, or biological outcome existed. The failed row
was not identified. The cause may be a source inconsistency or an overstrict
contract; current evidence does not decide which.

A single read-only diagnosis could identify whether the first failure reflects
a metadata-semantics mismatch or an apparent content inconsistency. It would
have decision value only. It would not validate the other rows or denominator,
repair or exclude a row, establish caller recall, or support a publication
claim. Any further source read needs a separate explicit scope and independent
review. If the issue needs row dropping, outcome-dependent rules, or another
unbounded pass, keep the route closed. Do not change callers, territory,
matching, residual selection, or thresholds after scores; none exist yet.

Even if metadata passes, this is only a one-donor released-callset falsifier.
The six files do not prove identical reads or caller versions; only three
headers declare the same BAM path. Q100-added territory means new benchmark
coverage, not intrinsic genomic difficulty. A zero residual would reject this
specific archived-callset recovery lead. A nonzero residual would be a
hypothesis list, not a caller failure or research result. Same-read provenance,
read-level support, and unrelated-donor replication are absent.

## Closest prior work

| Primary work | Overlap with this screen | What it leaves open |
|---|---|---|
| [GIAB HG002 v5.0q assembly benchmark](https://www.biorxiv.org/content/10.64898/2026.09.23.752440v1.full) | Uses phased Q100 assembly, expands confidence territory into repeats and complex loci, and checks discrepancies against multi-technology calls and reads. It cites prior analysis that many caller FPs/FNs lie in newly added territory. | Its purpose is benchmark construction and curation, not a same-input six-caller union experiment. Generic “new territory has misses” is already known. |
| [Maden et al., 2026](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014824) | Compares three benchmark frameworks, five callers, and two samples; shows framework-dependent classifications. | Another framework comparison or caller ranking is not a distinct contribution. The Q100 VCF filename in that paper has a different reported compressed hash from this project's pin; identical bytes are not established. |
| [SVkhor, 2026 preprint](https://doi.org/10.64898/2026.07.30.26359319) | Its abstract describes caller-aware normalization and within-/cross-technology integration on HG002. | Generic union, merging, or normalization is already occupied; only abstract-level scope was checked here. |
| [Svirlpool, 2025 preprint](https://www.biorxiv.org/content/10.1101/2025.11.03.686231v1.full) | Builds local read consensus around SV candidates and compares with Sniffles; reports ONT benchmark and trio Mendelian results. | It is ONT-specific. Candidate regions start from alignment signals, so it does not establish a general HiFi mechanism for alleles with no candidate signal. No transfer to these six callsets is shown. |
| [Qin and Li, low-complexity SV study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12758381/); [vcfdist](https://doi.org/10.1186/s13059-024-03394-5); [ASVBM](https://pmc.ncbi.nlm.nih.gov/articles/PMC12271604/) | Existing project review records low-complexity misses, alignment instability, and joint local/sequence-aware comparison. | Generic repeat enrichment, realignment, or representation harmonization is not new. Repeat purity after controlling for repeat and variant length remains only a hypothesis. |

The v5.0q article's methods describe assembly-based truth, external callset
comparisons, and read review of benchmark discrepancies. That is a stronger
truth-control process than this released-callset screen can provide. It does
not turn this screen into an independent benchmark or algorithm comparison.

## One conditional mechanistic target

The only residual target worth carrying forward from this comparison is:

> In sequence-resolved INS/DEL alleles, does tandem-repeat purity predict
> missing native HiFi caller evidence after matching repeat length, allele
> length, depth, mappability, and caller?

Mechanism: homogeneous repeats may reduce uniquely anchored read evidence and
fragment or suppress alignment-derived candidate signals. A decisive test must
use native candidate/read evidence, not just final VCF overlap or Truvari.
Use interrupted repeats as matched controls; verify truth sequence and phase
against the assembly-based benchmark; blind adjudication; then replicate in
unrelated donors. The outcome must show repeat purity adds predictive value
after the listed controls and that the truth allele has independent read
support while native candidate evidence fails. Mere enrichment among misses
does not pass. This could matter for hard-to-detect alleles, but no current
residual, causal mechanism, or independent replication supports it. It is not
a selected project. If the screen produces no valid residuals, this target
does not survive by assumption.

## Protocol and controls

- The exact signed-length check is strict, but it is defensible for the frozen
  pure, biallelic, sequence-resolved INS/DEL unit. One failure does not prove
  that rule is overstrict. Diagnose the cause before deciding; do not infer a
  biological null or call the truth corrupt.
- The release-set estimand is useful for a rejection screen, but not for
  causal caller claims because input reads and versions are incompletely
  established. Keep the label “released-callset coverage.”
- The 20-cluster hashed selection is reproducible but can miss rare mechanisms.
  The “at least five” escalation threshold is not a power or consequence
  threshold. It must not turn one strong event into a null. Revisit it only in
  a prospective, independently reviewed protocol before any outcome is seen.
- The October 8 deadline and resource caps are operational controls, not
  scientific evidence. No automatic extension or screen restart follows from
  this audit. The separate Sol6.1/max strategic review must authorize the
  single metadata diagnosis; this note does not authorize it. Any scoring
  protocol still needs independent review.

## Search and source scope

Three targeted Firecrawl paper searches were run with five result slots each
and an indexed date filter of 2025-04-08 through 2026-10-08. This is a bounded
comparison, not an exhaustive review. Two Firecrawl full-text reads returned
no passages. Exa then fetched the Q100 and Svirlpool primary preprint pages;
the retrieved text covered the relevant methods and claims but was partial.
Maden and Qin/Li details above reuse the earlier [novelty review](2026-10-07-novelty-recheck.md)
and [repeat-mechanism review](2026-10-04-modern-callset-falsifier.md); neither
was reread here. Search slots are not papers read. No other benchmark or caller
result was treated as evidence for this project. No code or genomic data was
touched, and no experiment was run.
