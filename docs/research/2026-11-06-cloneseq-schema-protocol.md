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
