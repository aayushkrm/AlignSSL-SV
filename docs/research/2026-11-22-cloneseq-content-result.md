# CloneSeq public-table content feasibility — preliminary result

## Scope and provenance

The [prospective protocol](2026-11-22-cloneseq-content-protocol.md) was
pushed as `364d75a` before worksheet data rows were inspected. The fixed
24-patient frame comes from the authors' figure-code configuration at
`076281373393e6922652371262f5975af9a41a30`. The public workbook and author
configuration matched their frozen SHA256s. Only S1–S10 were read, for keys,
missingness, metadata joins and count validity. No S11–S14 clinical rows,
clone accuracy, allele fractions or clinical outcomes were analyzed.

The [first execution](../../results/cloneseq_content_audit_20261122_run01/)
did not require a nonmissing clone label when marking a unique metadata join
as clone-linked. Its exact source and output are preserved, but that status
must not be used. The [corrected run](../../results/cloneseq_content_audit_20261122_run02/)
adds this check; six focused tests pass. In this particular dataset the
corrected patient-status counts did not change. Independent review of the
actual code, joins and results is pending.

## Observed availability

- **23 of 24** author-listed patients have at least one identical SV/SNV
  `(sample, timepoint, days)` tuple in the two public count sheets. The
  remaining patient has no usable exact pair under the stated sheet/key rule;
  that is not evidence of absent tumor or absent sequencing elsewhere.
- Those matches comprise 149 distinct patient/sample/time/day tuples; these
  are repeated measurements, not 149 independent patients. All six patients
  named in the authors' 12-sample cfDNA-WGS configuration have at least one
  exact SV/SNV specimen-time match. This does **not** yet link the specific
  WGS specimens to those measurements or establish access to WGS profiles.
- The audit read 72,607 SV and 147,984 SNV count-sheet rows. All had finite,
  nonnegative integer `total_counts` and `alt_counts` with `alt <= total`
  and a positive total under the coded validity rule. This checks data shape,
  not assay accuracy, independent molecules or equivalent effort.
- Five SV metadata keys are duplicated; 342 SV count-sheet rows meet a
  non-unique metadata key. Another 156 SNV count-sheet rows have at least one
  missing component of the author-code composite join key. These are row
  counts, not counts of false variants or independent events; a duplicate or
  missing key may have a legitimate source explanation. Uncertain joins stay
  unresolved.
- Fourteen patients meet this audit's strict **metadata-linkage-only** rule
  for all their observed count rows; nine remain unresolved and one has no
  count rows of one type. Even a unique clone label does not prove marker
  exclusivity, copy-number correctness, or a valid reference.

The eight-category patient table keeps separate data availability, marker
linkage, count units, cost, error controls, calibration, reference and reuse.
The current output marks cost, independent controls, calibration, separate
molecular reference and complete reproducibility as unresolved for all
patients. This is a conservative statement about evidence checked here, not
proof those resources do not exist. The source paper already describes
off-target controls and limited WGS validation; their per-sample accessibility
and suitability for a new comparison require direct verification.

No publication-worthy improvement has been established. A further prospective
check of the authors' 12 named WGS sample identifiers against S2/S7/S8 is
specified in the protocol. It can test exact linkage, not the availability or
independence of actual WGS profiles. An independent review must assess the
current results and any material code correction.
