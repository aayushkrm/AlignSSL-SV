# Independent review of CloneSeq content results — 22 November 2026

## Decision

**Accept the narrow key-availability findings, with the corrections below. Do not accept the corrected run as a complete audit of every missing metadata key.** An independent, read-only pass reproduced the 24-patient frame, 23 patients with at least one exact shared count-sheet key, 149 shared keys, the reported join counts, and every per-patient status in run 02. It also reproduced the separate WGS-key follow-up: 12 author-listed IDs have unique S2 mappings and exact S7/S8 keys, across six patients.

These are checks of identifiers, count shape and metadata availability. They do not establish 149 independent patients, validated clone identities, accessible WGS profiles, independent truth, equal assay budgets, or added SV accuracy. **One reporting omission is real:** run 02 drops 16 incomplete S10 metadata rows from its key index without reporting their missing key fields. The affected S8 rows are nevertheless flagged unresolved, so this omission does not change the reproduced 23/24 result, the 149 shared-key count, or the reported 14/9/1 marker-status counts. It does mean the result is incomplete against the protocol's instruction to retain missing keys.

```text
24 author-listed patients
        │
        ├── 23: at least one exact S7/S8 patient–sample–time–day key
        │         └── 149 distinct shared keys; repeated measurements
        └──  1: S7 rows present, no S8 rows under the exact patient ID

12 author-listed WGS sample IDs
        └── unique S2 mapping + matching S7/S8 keys: 12, from 6 patients
            WGS profile access and clone truth: not established
```

## Check: protocol, inputs and author code

I read [protocol `364d75a`](2026-11-22-cloneseq-content-protocol.md), its WGS-key amendment in `1c72bb4`, the two audit scripts, the tests, both retained content runs, the WGS follow-up output, and the relevant pinned author code. I independently checked the workbook, author configuration, schema, and script hashes against their recorded receipts. The schema and its receipt match the copies committed in `364d75a`. The author-code checkout was clean at commit `076281373393e6922652371262f5975af9a41a30`, and its configuration hash matched the protocol.

The local remote-tracking branch contains both protocol commits. Their recorded commit times precede the corresponding timestamps in the outputs. These local records are consistent with prospective registration; they do not independently attest the time of the actual remote push or execution.

The author's [setup code](https://github.com/shahcompbio/spectrum_cfdna_figures/blob/076281373393e6922652371262f5975af9a41a30/src/setup.R#L26) uses `(patient, target_idx)` for S7/S9 and `(target_idx, clonality, Hugo_Symbol)` for S8/S10. The audit uses those exact keys. S10 has no patient column; the SNV join is global by the author's key. In the observed S8 rows, I found no complete SNV key used by more than one patient. That does not prove the annotation is biologically correct or guarantee this property in other data.

My independent pass used a separate in-memory implementation, Python 3.9.6, `openpyxl` 3.1.5 and PyYAML 6.0.3. It checked only permitted S1–S10 identifiers, metadata, counts and field presence. It did not use frequency values for selection or inspect S11–S14 outcome data. It did not calculate allele fractions, detection rates, clone accuracy or clinical outcomes. No actual row, target or specimen keys are reproduced in this review.

## Check: patients, specimen keys and statuses

The author configuration has 24 distinct patient IDs, 18 listed timeline patients and 12 distinct WGS sample IDs from six patients. The WGS list has two IDs per patient. In S1–S9, the independent pass found no missing patient IDs or patient IDs outside the 24-name frame; S10 has no patient field.

| Finding | Independent result | Scope of the finding |
|---|---:|---|
| Patients with an exact S7/S8 key | 23 of 24 | At least one exact patient, sample, timepoint and day tuple; no alias normalization. |
| Shared S7/S8 tuples | 149 | Distinct keys across patients and time points, not 149 independent patients or proven separate physical aliquots. |
| Shared tuples with numerically exposed rows in each arm | 149 | At least one valid positive-total count row in each arm at the key; not necessarily the same clone, processing type, input or cost. |
| SV-only tuples | 3 | No exact corresponding S8 tuple. The patient without S8 rows still has S7 rows. |
| Same-time groups with different sample-name sets | 0 | No actual same-time naming mismatch was found under this frame and exact rule. |

Run 02's `sample_time_keys = PRESENT` is an **existence** condition: one matching key is enough. `ABSENT` for the remaining patient means that at least one required count-sheet side has no row under that exact patient ID. It does not mean both sheets lack rows, that a clone is biologically absent, or that sequencing is unavailable elsewhere. The 23/24 and 149 claims are acceptable with those qualifications.

The run's `shared_timepoints_without_exact_sample` counter has a narrower meaning than “all nonidentical names at the same time.” It removes a whole time/day group when **any** exact sample name matches, so it would hide an extra nonmatching sample at that same time. I confirmed this with synthetic rows. The independent workbook pass found no same-time groups with different name sets, so this limitation does not change the reported zero for the current data. Future checks should separately count unmatched sample keys within each patient/time/day group.

For an additional availability check, 135 of the 149 shared tuples had at least one equal, nonempty, non-generic textual clone label on an unambiguous marker in each arm with a positive numeric count total. This is a syntactic label match only. It does not establish marker exclusivity, a validated clone contrast, or accuracy; the other 14 keys are not evidence of biological absence.

## Check: duplicate and missing marker joins

| Check | Independent result | Interpretation |
|---|---:|---|
| S9 complete SV metadata keys | 3,711 | Based on exact patient and target index. |
| Duplicate S9 key groups | 5 | All five must remain ambiguous, even where labels agree. |
| S7 rows touching those groups | 342 | Repeated count-sheet rows, not 342 independent variants or patients. |
| Duplicate groups by clone label | 4 with the same nonempty label; 1 with differing labels | Agreement on a label does not prove the other metadata fields are identical. |
| S7 rows touching those groups, by label agreement | 294 same-label; 48 differing-label | Both groups remain ambiguous under the protocol. |
| S10 complete SNV metadata keys | 6,940, with no duplicate complete keys | This excludes incomplete S10 keys. |
| S8 rows with incomplete SNV join keys | 156, across 6 patients | 126 lack `Hugo_Symbol`; 30 lack `clonality`. Do not infer the missing field. |
| S10 rows with incomplete SNV join keys | **16** | 13 lack `Hugo_Symbol`; 3 lack `clonality`. Run 02 does not report these rows as missing-key metadata. |

The 156 incomplete-key S8 rows use 16 distinct incomplete tuples. Those same incomplete tuples occur in S10. This is a **partial-key availability observation**, not a valid join: a missing component is still missing. All 16 S10 rows are omitted from the complete-key index at [the S10 branch](../../analysis/audit_cloneseq_content.py), and no output counter records them. The reported zero SNV duplicate keys therefore means zero duplicate **complete** keys, not that every S10 key is complete.

The 342 ambiguous SV rows affect three patients; the 156 missing-key SNV rows affect six other patients. The nine unresolved marker statuses and 14 present statuses are reproduced. One additional patient has an absent marker status because one count-sheet side has no rows. These are patient-level status counts; the 342 and 156 are row counts.

**Correction required:** report incomplete S10 metadata rows and missing fields explicitly, without writing target keys to Git. Preserve incomplete S9 keys similarly if encountered. Add tests for incomplete metadata keys and distinguish duplicate complete keys from incomplete keys. Keep the 156 count rows unresolved; do not repair them by treating equal missing values as a confirmed biological match.

## Check: missing clone labels, zero counts and status meaning

The retained [run 01 source](../../results/cloneseq_content_audit_20261122_run01/audit_source_v1.py) counted a unique metadata key as clone-linked without requiring a nonmissing `clone_id`. Run 02 corrects that rule and flags missing clone labels. Do not use run 01's marker statuses as authoritative.

In these actual rows, all 72,265 uniquely matched S7 rows and all 147,828 uniquely matched S8 rows have nonmissing metadata clone labels. Thus the correction is necessary for general validity but does not alter this workbook's reported 14 `PRESENT`, 9 `UNRESOLVED`, and 1 `ABSENT` patient counts. A unique label is still not proof of clone exclusivity, cross-arm clone compatibility, copy-number correctness or independent truth.

The corrected count rule treats a missing total or alternate as missing; rejects booleans, nonfinite, negative or noninteger values and alternate counts above total; and distinguishes a zero total from a valid positive total with zero alternate count. No zero is imputed for a missing row. Independent inspection reproduced:

- All 72,607 S7 and 147,984 S8 count rows have positive numeric totals and valid alternate counts under that rule. These are rows, not molecules or independent observations.
- Positive-total rows with zero alternate counts are validly exposed rows: 50,115 S7 rows and 73,394 S8 rows. A zero alternate count is not proof of biological absence.
- Background fields contain 36 S7 and 32 S8 rows with zero totals. These have no positive denominator and must not be interpreted as a measured zero error rate.

The code gives missingness precedence if one count is missing and the other is invalid; a synthetic `(missing, negative)` pair is recorded only as `missing`. No such count rows were observed here. If complete error accounting is needed later, retain separate missing and invalid flags and add a test for this combination.

The per-patient status table is conservative but must be read at its exact grain. `marker_to_clone_metadata = PRESENT` means the observed count rows meet the script's strict metadata-linkage rule for both arms; it does not require the two arms to name the same clone in the same sample. A synthetic example with different clone labels still receives `PRESENT`. `count_fields_and_units` remains `UNRESOLVED` for the 23 paired patients. Budget, independent controls, timing/calibration, separate molecular reference and full reuse are `UNRESOLVED` for all 24 by construction. These statuses neither prove those resources absent nor establish their availability.

## Check: 12-sample WGS-key follow-up

The separate [follow-up script](../../analysis/check_cloneseq_wgs_keys.py) reads only the four permitted identifier/time columns from S2, S7 and S8. It requires exactly one S2 row for an author-listed sample, checks that the patient encoded in its name agrees with S2, and tests the exact four-field key against both count-sheet key sets. Independent workbook inspection reproduces its [output](../../results/cloneseq_wgs_key_audit_20261122_run01/audit.json): **12 of 12 sample IDs, two for each of six patients**. The sets in S7/S8 intentionally collapse repeated marker rows; the result does not imply that each sheet has only one row per sample.

The follow-up establishes linkage of the **author-listed identifiers** to table keys. It does not open or locate WGS profiles, show that WGS can distinguish the relevant clones, establish independent relapse-seeding labels, or match a sequencing budget. The `separate_molecular_reference` status should remain unresolved.

The pinned author's [WGS comparison code](https://github.com/shahcompbio/spectrum_cfdna_figures/blob/076281373393e6922652371262f5975af9a41a30/scripts/EDF9_validateclonefrequencies.Rmd#L436) joins WGS similarity records to SV clone-frequency records and applies `na.omit()` before selecting maxima. This can restrict candidate clones to records with available joined information. I did not evaluate its effect on the published result. It is an additional reason not to treat a key match or the published comparison as an automatically independent reference for a new SV-versus-SNV accuracy claim.

The follow-up writes the author commit value from an imported constant; it does not itself check the checkout's `HEAD`. I independently verified the pinned clean checkout and configuration hash for this review, so this does not invalidate the present key result. Future runs should verify the checkout and helper before reading rows and retain an output receipt and exact command.

## Corrections and remaining decision

1. **Fix the S10 omission** and report the 16 incomplete metadata keys as aggregate missingness, with their field counts. Keep their 156 S8 rows unresolved. Preserve run 01 and run 02 as historical artifacts.
2. **Clarify statuses and units:** `PRESENT` is the stated existential or metadata-only condition; `ABSENT` means a required sheet side has no supporting rows. Report patient, specimen key, marker and row counts separately. Do not promote matching clone labels to a common-clone truth set.
3. **Improve the same-time diagnostic** to retain nonmatching sample names even when another sample in the group matches. The present dataset has no such mismatch, so no change to the 149/23 result is indicated.
4. **Strengthen provenance and tests:** verify the schema hash against its frozen receipt before row inspection. Run 02 records the schema hash only after its analysis; I verified the retained schema matches the frozen version afterward. Record exact invocations and exceptions, and test incomplete metadata keys, mixed same-time sample names, and simultaneous missing/invalid counts. The source and result hashes are recorded, but the inspected run receipts do not record the exact commands.
5. **Update the result interpretation** to include the 12-sample WGS-key follow-up while keeping WGS profiles, clone distinguishability, independent reference, controls and matched assay budget unresolved. The original result note predates that follow-up and correctly did not claim the specific 12-key linkage.

These corrections do not require discarding the narrow key findings. They do prevent calling run 02 a fully complete missing-key audit. The public tables' scientific usefulness for a fair added-SV comparison remains unresolved; no accuracy, clinical, or publication claim follows from this review. A subsequent protocol can decide whether a bounded check of actual reference and budget availability is worthwhile, or whether to use the previously proposed paired DNA/RNA fallback.

## Verification and attestation

I independently recomputed all eight recorded statuses for all 24 patients and the cited key, count and join aggregates. The six existing tests passed with `pytest` after pointing its Python 3.11 environment at the installed `openpyxl` package; pytest's cache and Python bytecode writes were disabled. Six additional in-memory synthetic cases exercised the WGS follow-up's matching and rejection rules. Synthetic cases also exposed the same-time counter limitation, the existential clone-status semantics and the missing-plus-invalid priority described above.

No S11–S14 outcome rows, WGS profiles or clinical outcomes were inspected. No biological experiment, campaign, commit or push was performed. This review is the only file written for this task. The exact backend model and reasoning effort are not independently attested.
