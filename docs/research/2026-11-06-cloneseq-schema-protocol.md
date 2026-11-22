# CloneSeq-SV public table schema: prospective check

## Purpose

The [verified workbook metadata and legends](2026-11-06-cloneseq-supplement-inventory.md)
describe SV/SNV read counts, clone-frequency estimates, marker metadata,
assay errors and clinical annotations. Before proposing a scientific
comparison, check what the released tables call their fields. This is a schema
check, not an evaluation of clone tracking, accuracy, recurrence or utility.

## Scope

Use the existing local workbook only after its SHA256 matches the saved
receipt. Read the first worksheet row of each of its 14 named sheets, using
a read-only parser. Record string-valued column labels and blank columns only
when the first row is clearly a header. If the row contains a non-string value
or looks like an individual observation rather than field names, stop for that
sheet and record only that its header was unresolved; do not expose the row.
Do not read or analyze subsequent worksheet rows. Record the workbook and
script hashes, parser version, each sheet's header or unresolved status, and
all failures. No genomic data, extra patient files, computed biological
statistics or clinical outcome comparisons are authorized in this step.

Field labels alone cannot establish patient-level joins, eligibility,
assay-budget comparability, a clean control or independent truth. A data-row
feasibility check or comparison requires a separate prospective scope and must
identify exploratory and final evaluation sets explicitly.

## Result — 2026-11-22 UTC

The first row of each of the 14 sheets was readable as a field-label row.
The [schema packet](../../results/cloneseq_schema_20261122_run01/) records the
fields, workbook/script SHA256s and parser version. SV counts identify a
patient, specimen, timepoint and target, while SNV counts use a field named
`sample`; both include total, alternate and background-count fields. SV marker
metadata include a patient field, whereas the SNV marker metadata do not.
The author code uses a composite SNV join on target, clonality and gene symbol;
its uniqueness and correctness in this workbook remain to be checked. Other
fields name coverage, DNA yield, clone-frequency estimates and assay errors.
Names alone do not establish units, exact matches, independent molecule
counts, zero-versus-missing semantics or fair cost. No data rows were read.
