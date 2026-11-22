# CloneSeq public-table content feasibility

The [prospective protocol](../../docs/research/2026-11-22-cloneseq-content-protocol.md)
fixes the 24-patient author roster, input hashes, join rules and limits.
`audit.json` contains deidentified patient-level availability statuses and
aggregate diagnostics, with no target keys, clinical outcomes or performance
estimates. `receipt.json` pins the result, source script and inputs.

This corrected second run requires a nonmissing clone label for a unique
metadata match. The [first run](../cloneseq_content_audit_20261122_run01/)
and its exact source remain preserved. [Independent review](../../docs/research/2026-11-22-cloneseq-content-independent-review.md)
reproduced the narrow counts and identified 16 incomplete S10 metadata rows
missing from this run's aggregate reporting, plus a same-time counter
limitation. A third reporting run is specified; do not treat run 02 as a
complete inventory of missing metadata keys.
