# HG008 primary-source check: a lead, not a result

2026-10-09. Main checked the load-bearing claims in the completed
[investment decision](2026-10-09-post-provenance-scientific-decision.md).
The independent scientific review is separate and pending. No data package,
caller run, training, booking or genomic-file inspection occurred here.

## Source and read scope

Firecrawl's paper metadata tool resolved DOI `10.64898/2026.05.01.722316` to
*A complete human pancreatic cancer genome*, PMID42146349 and PMC13174521.
The paper-index body query returned no passages. Main then used the connected
scrape tool, not a CLI: the exact [version-1 primary page](https://www.biorxiv.org/content/10.64898/2026.05.01.722316v1.full)
returned HTTP200 on October 9, with 283,185 extracted characters. Main read
selected results, availability, polishing, somatic-SV calling and curation
passages, including the complete selected SV calling/curation sections.
This is not a full paper, supplement, issue, source-code or genomic-data audit.

## What the primary text establishes

- The authors report 16 truncal tandem-repeat insertions/deletions missed by
  all four tested short-/long-read callsets made before the benchmark was
  available. This verifies the reported motivation, not current caller failure.
- Repeat loci with somatic SVs also have inherited insertions/deletions.
  Four have evidence of mosaicism in normal tissue. Main has not established
  which of those loci belong to the proposed fixed 16-event list.
- The truth process uses tumor/normal assembly comparisons and candidates
  from mapping-based callers, followed by read inspection and curation by
  at least two people. Passage-41 HiFi support is required for truncal
  inclusion. These are valuable evidence checks, not proof of an orthogonal
  assay or comparator-independent truth for each proposed event.
- The methods identify Supplementary Table S9 and public curation issues
  as case-level sources. Main has not opened them or established the exact
  16 IDs, independently supported negative controls or usable regional inputs.

These findings are from the [version-1 results and methods](https://www.biorxiv.org/content/10.64898/2026.05.01.722316v1.full).
They are published observations, not project measurements.

## Version bridge and scientific limits

The primary polishing text explains a transition from initial tumor v3.1
to final v3.2 after potential assembly errors were corrected. Availability
lists normal v6.3 and tumor v3.2; the SV phasing description still names
tumor v3.1. This is not, by itself, a contradictory or corrupt release.
The exact event/coordinate bridge to the benchmark must still be established.
Do not silently substitute the final assembly or assume every locus changed.

Donor-specific assembly comparison already recovers these changes in the
published study. Reproducing them with that approach is not new science.
The proposed prerequisite only has value if it enables a fair challenge
against current native callers and ordinary donor-specific controls, using
the observations those controls need. A cropped packet that removes needed
phasing, coverage or alignment context cannot establish a method advantage.

The earlier [repeat-native audit](2026-10-08-repeat-native-controls.md)
also identifies TRGT, SCIA and MosaicTR as potentially relevant controls.
That audit's source-read limits still apply. Calling the target an SV must
not exclude an applicable targeted repeat genotyper. Their relevance and
required observations need scrutiny before freezing a later falsifier.

All 16 published misses are development-exposed. Their recovery cannot be
an untouched confirmation result. Zero additional errors on 32 selected
controls would also not establish zero population risk. New methods,
independent final validation, complete uncertainty analysis and publication claims
remain unapproved. The proposed 90-minute material prerequisite is UNBOOKED
and awaits independent scope/account scrutiny; no preparation campaign follows
from this source check alone.
