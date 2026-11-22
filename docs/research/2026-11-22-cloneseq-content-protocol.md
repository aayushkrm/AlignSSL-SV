# CloneSeq-SV public tables: prospective content-feasibility check

## Question and evidence standard

Can the public tables support a later, fair patient-level test of whether SV
junctions add clone information to a strong SNV analysis? This check examines
keys, count validity, missingness and the availability of controls. It does
not estimate clone accuracy, compare SV and SNV performance, tune thresholds,
or use recurrence outcomes. Every published patient and result is development
evidence for this project, not an untouched final test. A successful join is
not a biological or publication result.

The [independent review](2026-11-22-independent-investment-review.md)
supports this bounded check and distinguishes the original paper's 24 tissue
patients, 18 longitudinal patients and 12 cfDNA-WGS specimens from six
patients. Those groups answer different questions; specimen counts must not
be presented as independent-patient counts.

## Fixed inputs and frame

1. The retained public workbook `SupplementaryTables.xlsx`, SHA256
   `7fd3bf312acb0ba617d28878bd9b4a54122164fb842e933d6a13c5efdc53ee33`,
   and the 14 first-row headers in the [schema packet](../../results/cloneseq_schema_20261122_run01/).
2. The original [figure-code repository](https://github.com/shahcompbio/spectrum_cfdna_figures)
   at commit `076281373393e6922652371262f5975af9a41a30`. Its `config.yaml`
   has SHA256 `f5a25b5b0109a102b670e0a549679da08e49c33bd6fdb1d65292005e366ac954`.
   Its named `patients` list defines the 24-patient audit frame; the named
   timeline and WGS lists remain separate nested sets. Preserve extra,
   missing or conflicting identifiers as unresolved rather than guessing an
   alias or silently changing the denominator.
3. The [paper](https://doi.org/10.1038/s41586-025-09580-0), legends and
   pinned author code establish what the fields could mean. A shared
   tissue-derived clone model, SV-based calibration or WGS similarity is not
   automatically an independent relapse-seeding truth.

Use a read-only parser and verify all input hashes before examining rows.
Inspect all rows of the public S1–S10 sheets for identifiers, marker metadata,
count validity and presence/absence of the named fields. Keep all missing and
duplicate keys. Do not inspect S11–S14 clinical/outcome data rows, use
frequency values to select cases, or calculate allele fractions, clone
accuracy, detection rates, outcomes or associations. The author-defined
`patients_timeline` and `patient_wgs` lists are metadata, not new truth.

## Prespecified join and reporting rules

- Match patient names exactly to the author list. Do not normalize or infer
  aliases without an explicitly sourced crosswalk. Report every unmatched
  patient label and a count of rows with missing patient identifiers.
- For SV markers, check exact `(patient, target_idx)` keys between S7 and S9.
  For SNVs, check the author-code key `(target_idx, clonality, Hugo_Symbol)`
  between S8 and S10, including missing keys, duplicates and conflicting
  clone labels. A match to a non-unique key is ambiguous, not confirmed.
- Test whether SV and SNV counts share an exact `(patient, sample,
  timepoint, days)` using S7 `sample_id` and S8 `sample`; do not silently
  equate different strings. Report same-timepoint but nonidentical sample
  names separately. Counts have usable numeric fields only when total and
  alternate counts are finite nonnegative integers and alternate does not
  exceed total. Record zero totals, missing and invalid counts separately;
  no zero is imputed for an absent or failed target. Record sequencing types
  separately and do not call raw reads unique molecules.
- For all 24 patients, publish a status table covering: (1) sample/time keys,
  (2) marker-to-clone information, (3) count fields and units, (4) material
  and sequencing budget, (5) error controls, (6) timing/calibration,
  (7) a separate molecular reference, and (8) reuse/reproducibility. Use
  PRESENT only for the explicitly documented subcondition; ABSENT means no
  supporting row in the named public sheet, not biological absence;
  UNRESOLVED covers ambiguous keys, provenance, units or unavailable sources.
  Attach concise evidence and limitations to each status. Retain the complete
  24-by-8 table, including patients with no matching rows.
- Keep row/target keys and all clinical observations out of Git. Save only
  aggregate diagnostics and the deidentified patient-level availability
  statuses, source/script hashes, exact command, software versions and
  exceptions. The original public workbook stays unmodified outside Git.

## Interpretation and resources

Expected outcomes are: a precisely defined, potentially estimable comparison;
a documented missing/ambiguous essential field; or an inconclusive check.
The 12 WGS sample identifiers in author configuration name a candidate
reference subset but do not prove accessible WGS profiles or independent
labels. Clinical recurrence dates are not lineage truth. If the public path
cannot support a meaningful comparison, document the reason and consider the
separately specified 56-name chromosome-22 DNA/RNA content pilot; do not
present non-evaluability as a biological null. Any comparative result or
larger campaign needs a new protocol and independent scrutiny.

Use the retained 19 MB workbook and local CPU. Bound this check to four
analyst hours, two CPU-hours, 4 GiB RAM and at most 100 MiB new source
metadata, as proposed in the investment draft; these are local spending
limits, not limits on the user's overall research goal. This protocol is
pushed before the first data-row inspection.
