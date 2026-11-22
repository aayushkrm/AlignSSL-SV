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
corrected patient-status counts did not change. An [independent review](2026-11-22-cloneseq-content-independent-review.md)
reproduced the narrow findings and identified the missing-key reporting and
same-time diagnostic limitations described below.

## Observed availability

- **23 of 24** author-listed patients have at least one identical SV/SNV
  `(sample, timepoint, days)` tuple in the two public count sheets. The
  remaining patient has no usable exact pair under the stated sheet/key rule;
  that is not evidence of absent tumor or absent sequencing elsewhere.
- Those matches comprise 149 distinct patient/sample/time/day tuples; these
  are repeated measurements, not 149 independent patients. All six patients
  named in the authors' 12-sample cfDNA-WGS configuration have at least one
  exact SV/SNV specimen-time match. This initial check did not itself link
  the specific WGS specimens to those measurements.
- The audit read 72,607 SV and 147,984 SNV count-sheet rows. All had finite,
  nonnegative integer `total_counts` and `alt_counts` with `alt <= total`
  and a positive total under the coded validity rule. This checks data shape,
  not assay accuracy, independent molecules or equivalent effort.
- Five SV metadata keys are duplicated; 342 SV count-sheet rows meet a
  non-unique metadata key. Another 156 SNV count-sheet rows have at least one
  missing component of the author-code composite join key. These are row
  counts, not counts of false variants or independent events; a duplicate or
  missing key may have a legitimate source explanation. Uncertain joins stay
  unresolved. Run 02 omitted 16 incomplete S10 metadata rows from its key
  index without a missing-key counter; its zero duplicate SNV metadata keys
  refers only to complete keys. The reviewer found four SV duplicate groups
  with the same nonmissing clone label and one with different labels; all
  remain ambiguous under the prospective rule.
- Fourteen patients meet this audit's strict **metadata-linkage-only** rule
  for all their observed count rows; nine remain unresolved and one has no
  count rows of one type. Even a unique clone label does not prove marker
  exclusivity, agreement of the two arms on a clone, copy-number correctness,
  or a valid reference. The run's same-time counter can miss an unmatched
  sample when a different sample matches within the same time group; the
  independent reviewer found no such mixed group in the current workbook.

The eight-category patient table keeps separate data availability, marker
linkage, count units, cost, error controls, calibration, reference and reuse.
The current output marks cost, independent controls, calibration, separate
molecular reference and complete reproducibility as unresolved for all
patients. This is a conservative statement about evidence checked here, not
proof those resources do not exist. The source paper already describes
off-target controls and limited WGS validation; their per-sample accessibility
and suitability for a new comparison require direct verification.

## Targeted WGS sample-key follow-up

The amendment to the protocol was pushed as `1c72bb4` before the targeted
read. The [key-only audit](../../results/cloneseq_wgs_key_audit_20261122_run01/)
found that all 12 author-listed WGS sample identifiers have a unique S2
sample match and an identical patient, sample, timepoint and day key in both
count sheets. They represent **six patients**, with two listed samples each.
The audit read the first four identifier/time fields only; it did not read
read counts, clinical outcomes or WGS signals. A key match does not establish
marker distinguishability, independent clone truth or equivalent assay cost.

A separate [anonymous Synapse check](../../results/cloneseq_synapse_metadata_20261122_run01/)
found that project and archive metadata are visible, but both the file-handle
and documented download-reference requests returned HTTP 403. No archive was
downloaded. Authenticated access has not been tested, and the response does
not establish the applicable legal terms or the contents' suitability.

The [literature update](2026-11-22-cloneseq-literature-update.md) identifies a
2026 cfClone preprint that reuses these WGS-reference patients and reports
that only three of six had clone sets distinguishable with both marker
classes. This is the preprint's finding, not a new result from this audit.
The [third reporting run](../../results/cloneseq_content_audit_20261122_run03/)
records all 16 incomplete S10 metadata rows and finds no mixed same-time
sample groups. It reproduces all 24 patient statuses and 149 shared keys.
The 156 incomplete S8 join rows remain unresolved. Twelve focused tests
passed across the three audit scripts. Both previous runs are preserved.
The [investment reassessment](2026-11-22-investment-reassessment.md) parks
the comparative campaign pending an independent cohort, reference and
measurable assay budget.
