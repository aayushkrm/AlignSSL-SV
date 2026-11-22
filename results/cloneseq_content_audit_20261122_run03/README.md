# CloneSeq content audit — run 03

This run applies the reporting corrections preregistered in commit `3d04c13`. It uses the frozen workbook, author configuration, 24-patient frame and schema.

- S9 metadata rows: 3718; incomplete rows: 0; missing components: `{"patient": 0, "target_idx": 0}`.
- S10 metadata rows: 6956; incomplete rows: 16; missing components: `{"Hugo_Symbol": 13, "clonality": 3, "target_idx": 0}`.
- Duplicate complete metadata key groups: S9 5; S10 0. Incomplete keys are not matches.
- Exact patient/sample/time/day matches: 23 patients and 149 keys. Unmatched keys: SV 3; SNV 0; mixed same-time groups 0.
- Common run02 aggregate metrics and patient statuses unchanged: true.
- Missing and invalid count flags are independent. Primary count categories are retained. No zero is imputed.

The audit reports metadata and key availability. It does not establish biological truth. It reads S1-S10 only. It does not inspect S11-S14 clinical rows, calculate allele fractions, compare arms or outcomes, or access WGS signals. `audit.json` contains aggregate diagnostics and the fixed patient frame; it contains no specimen or target keys. `receipt.json` records the invocation, runtime, source/input/output hashes and any exception.
