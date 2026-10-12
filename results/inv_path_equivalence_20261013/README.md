# Conditional pure-inversion equivalence result

13 October 2026, Asia/Tomsk. **No exact match in any of36 frozen comparisons.**
This rejects one reference-based pure-INV normalization explanation for the
nine retained declarations. It does not prove distinct actual biological
alleles, a caller defect or a new publication contribution.

The [protocol](../../docs/research/2026-10-13-inversion-path-equivalence-protocol.md)
was committed at8c55560,2026-10-13T02:20:22+07:00, before the regional API
reference acquisition at19:20:27UTC. It fixed all nine records and four pairs
of coordinate conventions before comparison. No shifts, distance threshold,
trimming, realignment, favorable-mode selection or new case follows the result.

| Mode pair | Comparisons | Exact equalities | Unequal positions, min–max |
|---|---:|---:|---:|
| TruthA / callA |9|0|9355–16301|
| TruthA / callB |9|0|9276–16088|
| TruthB / callA |9|0|9332–16238|
| TruthB / callB |9|0|9286–16168|

A inverts [POS,END); B inverts [POS−1,END−1), zero-based half-open. All use
the same29,000-base hg38 chr2 context. Unequal positions are a deterministic
string diagnostic, not edit distance, a biological effect size or an acceptance
cutoff. Nine records/four modes are not independent biological replicates.
All modeled truth and call alternates also differ from reference. GT0/0 remains
visible and is never counted as carrier recovery.

## Evidence and execution

[comparison.json](comparison.json), SHA256
a62fd24187934e5efbeec5f0e6dc3b689452e362a0c4e94785df236a9b70836c,
contains all36 results, full raw selected rows, genotype/filter fields and
alternate-string hashes. Reference [receipt](reference_receipt.json) preserves
the earlier acquisition snapshot, including its then-PENDING result field.
No receipt is overwritten to turn preparation into a result.

Canonical hg38 reference: UCSC chr2 [240675000,240704000),29,000unambiguous
bases. Regional JSON transfer29,159B, cap128KiB, no whole genome. Raw JSON
SHA256d28acc720fd15ca939a1e9f5d885ed3da0970ff4edbfdf93bea081ed71036656;
upper-DNA SHA256ecb39b7eb34964b213989ea986ffd8f67475c9ccff9910f0ac22d065621e4edb.
Original caller FASTA identity and actual coordinate conventions remain unknown.
An existing cluster reference was found but its adjacent index was absent;
the small API alternative avoided a whole-reference scan/index or native job.

Main executed the diagnostic once after all20offline controls passed and a
complete code/test read. Timed local process:0.16s wall,0.13s user,0.01s system,
16,879,616B maximum RSS. The [independent reviewer](../../docs/research/2026-10-13-inversion-equivalence-result-review.md)
recomputes all36 values/hashes/flags without importing the comparator and
ACCEPTS this conditional negative. Its review also accepts the separate header
correction. Requested Sol6.1/high; backend/effort not independently attested.
The [max-effort decision](../../docs/research/2026-10-13-inversion-residual-investment-decision.md)
had recommended this finite check, not a new campaign or method.

## Limits and next useful step

These are pure flips of a canonical reference. Actual haplotypes can carry
substitutions/compound structure, and symbolic INV can encode partial junction
evidence. Inequality under these two modes is not exhaustive molecular-allele
inequality, independent phase/CN validation, genotype accuracy or all-types
caller absence. A new input track cannot reproduce the original20-result panel
merely because it is named HG002. No meaningful performance claim is accepted.

The preserved whole study BAM/BAI opens and is coordinate-sorted, with chr2
length242193529, CCS/Revio sampleHG002_WGS and195references. Existing native
Python3.12.1/pysam0.24.1 works. The [bounded trace protocol](../../docs/research/2026-10-13-inversion-mapped-input-trace-protocol.md)
uses this separate existing track, not a new DNA download or old annotation
campaign. Source-base identity, locus evidence and phase are not proved by
header/index opening. No case alignment bodies have been inspected yet.

Software regression:157tests+62subtests pass5.55s, including20path controls
and21source-fetch controls. No software control is a biological validation.

```sh
/Users/akm/aayushkrm-AlignSSL/.venv/bin/python -B analysis/compare_inv_declared_paths.py --manifest results/inv_fixed_case_20261013/sources_with_commands.json --reference-json /Users/akm/aayushkrm-AlignSSL/runs/inv-supplement-check-20261013.nq0gdp/hg38-chr2-240675000-240704000.json --output NEW_OUTPUT_PATH.json
```

Use a new output path for any audit replay; the saved result must remain intact.
No native caller, training, GPU or costly cluster campaign. Full goal unmet.
