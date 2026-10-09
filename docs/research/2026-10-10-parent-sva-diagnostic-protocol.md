# One-parent SVA native diagnostic

Status: selected by the completed Sol6.1/max-requested decision; implementation
in progress. Not yet launched. This is one cheap diagnostic, not a campaign.
The independent reviewer is checking the decision and the much larger future
HG002 paired proposal in parallel. No major scientific positive is accepted.

## Frozen inputs and question

Read [the completed selection](2026-10-09-public-paired-falsifier-decision.md)
and [original source limits](2026-10-10-platinum-sva-source-check.md).
Use public NA12878 CHM13 HiFi material only; child NA12887 is controlled.
Query buffer BED `chr3 71539909 71643317`; reporting/core BED
`chr3 71579909 71603317`. These half-open query intervals do not establish
the workbook's coordinate convention. Keep complete records, tags and names.

Question: does either current native Sniffles policy emit a non-reference
insertion compatible with the reported parental neighborhood? A parental
sequence is not independent exact truth for the controlled child's allele.
No forced genotype, trained model, parameter grid, new sample or whole BAM.

## Independent descriptive read census

Before outcomes, freeze these CIGAR-based compatibility rules:

- Query reads overlapping the 1-kb flanks of position0 71589909.
- Exclude unmapped, secondary, supplementary, QC-failed and duplicate records;
  require MAPQ at least20. Multiple primary records with the same read name
  are ambiguous, not arbitrarily reduced to the favorable record.
- Each flank must contain at least500 M/= /X aligned bases within its1-kb
  reference window; deletions and skips are not aligned flank bases.
- Compatible insertion: breakpoint within500bp of the frozen position,
  inserted length2726–4088bp (published3407±20%). Keep the sequence and hash.
- Reference-compatible CIGAR: adequate flanks and no INS/DEL/skip at least50bp
  overlapping the ±500bp neighborhood. This is not a truth-negative label.
- Other structural CIGAR, inadequate flanks, multiple compatible insertions
  and duplicate primary names remain separate unresolved categories.
- Preserve external-SA declarations. The first census does not adjudicate
  split-only insertion reconstruction, paralog placement or missing outside
  supplementary records. Such limitations cannot become a biological null.

Report every examined record and exclusion count. The raw descriptive fraction
is compatible INS/(compatible INS+reference-compatible), with unresolved
records separately counted. No population estimate, independence assertion,
confidence interval or comparison of this fraction to scaled native VAF.
The census is sequence-supported compatibility, not exact-child-allele truth.

## Native pair and useful resources

Run Sniffles2.8.1 native germline and `--mosaic` on the same regional BAM/core
BED, with `--output-rnames`. Retain each policy's support, merging and other
QC defaults. No `--no-qc`, support-auto, invented shared merge or tuning.
For this single small interval, use one worker per call and run both calls
concurrently with the census: three useful CPUs, rather than eight largely
idle workers. Thread count is a resource choice, not a scientific policy
change. Capture complete stdout/stderr, exit status, VCF and native support,
GT/FILTER, VAF, ALT and record names. A missing output is not a successful
empty callset. A present candidate is not necessarily a non-reference GT.
Freeze acceptance separately: FILTER PASS is native filter acceptance, not
truth. A germline record needs a non-reference GT for germline-call success.
Reference-only or filtered germline records remain visible diagnostic records,
not accepted non-reference calls. Mosaic visibility follows the intended
native mosaic representation with PASS and credible insertion evidence; do
not add an invented diploid-heterozygous requirement. Always report its actual
GT unchanged, including any0/0, rather than relabelling it heterozygous.

Use a new scoped cluster run directory. Selected new genomic HTTP-body bound:
4GiB including BAI, retries and overfetch; no whole BAM/reference download.
Preserve partial artifacts and a body-byte request ledger on failure. A local
range proxy records the actual body bytes read; physical TLS/TCP overhead is
not being claimed. Maximum selected CPU account:1800seconds. A three-CPU,
10-minute Slurm allocation enforces that scheduling envelope; request4GiB
RAM within the16GiB planning ceiling. Record actual CPU, wall and retained
bytes rather than treating ceilings as usage. No GPU is useful here.

The source-prefix65,536B and publication workbook249,138B are already recorded
separately. Runtime software is not genomic transfer: an isolated CPython3.12.1
venv installed Sniffles2.8.1 and dependencies; imports/CLI qualification and
the exact freeze will be saved before launch. No shared environment changed.

Actual qualification completed: `sniffles --version` reports2.8.1, `pip check`
reports no broken requirements, and native extension imports succeed. Freeze:
edlib1.3.9.post1, numpy2.5.3, psutil7.2.2, pysam0.24.1, pyspoa0.3.2,
sniffles2.8.1. This qualifies that runtime, not a successful genomic assay.

## Outcomes and stop rules

Native compatible non-reference success retires a new-method premise for
this known case. Germline absence plus mosaic success is expected policy
behavior, not novelty. Both absent with credible parental evidence permits
one bounded context/representation inspection, not automatic training or a
caller grid. Missing compatible reads or unresolved mapping/sequence gives
INCONCLUSIVE about the published event. Preserve the paper's result.
No outcome establishes prevalence, full-trio sensitivity, clinical risk,
whole-genome equivalence or publication readiness.

## Implementation qualification before acquisition

The Luna/max-requested acquisition handoff was requested immediately after
the task remained on the critical path; the same worker concluded without
restart. Its six earlier tests passed, but its last CPU-metadata edit was
unverified. Main read all548 original source lines and172 test lines, then
fixed a concrete pre-acquisition HTS compatibility fault: initial GETs and
open-ended logical range streams must work. They are not whole-file staging.
Upstream BAM bodies still require206 and pinned identity; every response
body read is globally capped and logged, including overfetch. Explicit bounded
ranges remain limited to64MiB, and streaming chunks are65,536B.
Main added a loopback-only, mocked-upstream initial-open/seek control. No
external network or real genomic input was used in these tests. The helper
is larger than the requested approximate250-line target; it is not represented
as that smaller implementation. This correction changes transport, not the
frozen census, native policies or scientific endpoints.

The helper conservatively includes the already charged65,536B prefix within
its4GiB body cap. Report new body bytes separately to avoid double-counting
the historical prefix. Runtime package material remains a separate software
acquisition; installation byte totals were not measured as genomic reads.

The next unknown-residual question is the frozen HG002 DNA-first coding-path
pilot. Its large cost requires independent scrutiny before any expensive
campaign. The current diagnostic does not automatically release that budget.
