# CloneSeq author-listed WGS specimen-key audit

The [prospective amendment](../../docs/research/2026-11-22-cloneseq-content-protocol.md)
was pushed as `1c72bb4` before this targeted check. It fixes the author roster,
the exact S2/S7/S8 match rules, and the restriction to four key columns.
`audit.json` records aggregate and deidentified patient-level statuses;
`receipt.json` pins its inputs and scripts. The public workbook remains
outside Git. To reproduce, use Python with `openpyxl` 3.1.5, an absent output
directory, and `python3 analysis/check_cloneseq_wgs_keys.py` from the root.
The original executable path was not recorded, so this is a reproduction
command rather than an independently verified transcript of the invocation.

All 12 author-listed specimens match both count-sheet keys, across six
patients. This is a key-availability result, not a validation of clone
estimates, marker independence, WGS access or assay budgets.
