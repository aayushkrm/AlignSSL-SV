# Independent review of the reference-ambiguity milestone

**Date:** 2026-09-24. **Scope:** saved HGSVC/IGSR non-ACGT masks, their
reduction against the earlier reference-difference map, the PAV callable note,
and limits on cohort selection. This is an independent review of a technical
finding, not a method-efficacy or publication-readiness approval.

**Reviewer configuration:** The delegation requested `gpt-6-sol` at `high`
reasoning effort. The reviewer reported that its runtime did not independently
expose a verifiable variant/effort identifier, so the *actual* model/effort
cannot be certified from its self-report. Its substantive findings below remain
useful but do not satisfy a strict model-attestation requirement. The reviewer
did not rerun the full FASTA scans.

## Findings and disposition

1. **High: donor-negative gate remains closed.** The joint non-ACGT BED is
   reference sequence ambiguity, not per-donor callability. In tagged
   [PAV 2.4.0.1](https://github.com/EichlerLab/pav/blob/v2.4.0.1/rules/call.snakefile#L183-L215),
   the `_500` callable output combines trimmed alignment and large-variant
   intervals. Its [region merge](https://github.com/EichlerLab/pav/blob/v2.4.0.1/pavlib/util.py#L36-L100)
   can bridge an unaligned gap of up to 1,000 bp. Therefore membership in a
   smoothed PAV BED cannot prove every proposed negative base is aligned on
   both haplotypes. The [PAV note](2026-09-23-pav-callable-availability.md)
   now requires checking unsmoothed, trimmed reference-alignment intervals,
   QC exclusions, full candidate spans and flanks, and independent truth.
2. **Medium: prior comparison provenance not yet closed.** The saved
   [reduction](../../scripts/analyze_reference_ambiguity.py) verifies existing
   map files and intersects their BEDs with the new masks, but the original
   difference-map job read an IGSR URL without retaining a digest of the exact
   FASTA bytes consumed. The new frozen FASTA and its 3,366 sequence M5 checks
   narrow this. Frozen-source re-comparison job `1598267` is submitted; until
   it completes and agrees on all 18 contigs, the zero-outside-union finding
   remains a result of the *saved* map and masks.
3. **Medium: PAV TAR survey lacks raw reproducibility.** The reported
   two-archive header walk has counts and source links but no saved scanner or
   raw member log. The note now treats the absence claim as provisional and
   scoped to those two archives. No full TAR transfer or negative labels are
   justified by that report.
4. **Medium: durable-copy evidence was absent from the bundle.** The earlier
   committed log recorded only the failed compute-node copy. A fresh
   [login-node verification record](../../results/reference_ambiguity/2026-09-23/preserve_login_verification_2026-09-24.txt)
   now checksums the IGSR and HGSVC archived FASTAs and indexes. The final
   reduction JSON and BED now have a separate
   [SHA-256 manifest](../../results/reference_ambiguity/2026-09-23/ANALYSIS_SHA256SUMS).
5. **Low: stale instruction.** The data-decision note still instructed readers
   to map the 18 differences. It now records that the map exists and that the
   frozen-input replay, read-evidence bridge, and callable-negative gate are
   the remaining tasks.

The narrow defensible result is: on the 194 shared contigs in the saved
comparison, the two references agree at every position where both have
A/C/G/T. This says nothing conclusive about read alignment, IGSR-only
sequences, near-ambiguity truth matching, donor-negative labels, pedigree-safe
splits, or independent confirmation. **No cohort-selection or efficacy claim
is approved.**

## Post-review evidence update

After the review, job `1598267` completed. The
[frozen-reference replay](2026-09-24-frozen-reference-replay.md) verified both
FASTA source hashes and reproduced every BED byte and scientific summary field
of the prior 18-contig map. This resolves finding 2 for the *saved map*; it
does not change finding 1 or authorize a cohort. The successful archived-FASTA
checksum record and final-analysis manifest resolve the missing bundle
evidence in finding 4. The PAV TAR member-log/scanner and all donor-callability
and read-alignment gates remain open.
