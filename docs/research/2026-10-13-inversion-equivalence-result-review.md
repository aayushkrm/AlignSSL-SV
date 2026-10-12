# Independent review of the inversion equivalence result

13 October 2026, Asia/Tomsk. Maintained reviewer; requested Sol6.1/high continues.
Model/effort are not independently attested. Only this new note is owned.
Main retains integration, reference/input availability checks and subsequent work.

## Decision

**ACCEPT the finite conditional negative result. Reject exact pure-INV equality
for these nine declarations on canonical hg38 under the four frozen mode pairs.
HOLD full molecular-allele equivalence, caller-failure and mechanism claims.**
The result removes one representation explanation under explicit assumptions.
It does not show that a current caller missed all structures or that a new method
can recover this selected simple inversion. No costly campaign or native job is
released. A small trace needs qualified existing mapped inputs; their absence
can HOLD that trace without stopping the full research goal.

I fully read the [frozen protocol](2026-10-13-inversion-path-equivalence-protocol.md),
the 662-line [comparator](../../analysis/compare_inv_declared_paths.py), its full
[test file](../../tests/test_inv_declared_paths.py), retained reference receipt,
and load-bearing saved-result fields. The supplied freeze commit is 8c55560,
before API sequence acquisition; no Git check was performed by this reviewer.

## Actual inputs and independent recomputation

The case remains chr2:240685775–240688980, 3,205 bp. I used only retained local
canonical DNA and the corrected manifest. I did not import or run the comparator.
My independent construction reverses the declared segment then complements
each base, leaving identical flanks in the full 29,000-base context.
All 36 saved interval pairs, alternate SHA256s, equality flags, reference-equality
flags, eligibility flags and positional-difference counts reproduce exactly.
All nine raw caller rows also agree with the corrected packet's selected records.

| Frozen mode pair | Comparisons | Exact / eligible equalities | Positional differences, min–max |
|---|---:|---:|---:|
| Truth A / call A | 9 | 0 / 0 | 9355–16301 |
| Truth A / call B | 9 | 0 / 0 | 9276–16088 |
| Truth B / call A | 9 | 0 / 0 | 9332–16238 |
| Truth B / call B | 9 | 0 / 0 | 9286–16168 |

A=[POS,END); B=[POS−1,END−1). No favorable mode is selected or collapsed.
All constructed truth/call alternates differ from reference. Differences count
unequal positions in equal-length strings; they are not edit distances, acceptance
thresholds, recall/F1, effect sizes or independent biological observations.

The retained UCSC JSON is 29,159 bytes for hg38 chr2 [240675000,240704000), with
29,000 A/C/G/T bases after case normalization. Its exact bytes and upper-DNA
hashes match the acquisition receipt and saved result. Soft masking is letter
case, not an independently validated repeat annotation. No network check ran.

| Bound artifact | Independently verified SHA256 |
|---|---|
| Raw canonical-reference JSON | `d28acc720fd15ca939a1e9f5d885ed3da0970ff4edbfdf93bea081ed71036656` |
| Uppercase reference DNA | `ecb39b7eb34964b213989ea986ffd8f67475c9ccff9910f0ac22d065621e4edb` |
| Corrected source manifest | `cf2afb766f55035dc03c8cb095599eda35ba4d85c4713044b41ea64356312ca7` |
| [comparison.json](../../results/inv_path_equivalence_20261013/comparison.json) | `a62fd24187934e5efbeec5f0e6dc3b689452e362a0c4e94785df236a9b70836c` |

## Algorithm and corrected metadata

The code implements full-context reverse-complement substitution and direct
string equality. It checks reference metadata, 29-kb length, unambiguous bases,
in-range endpoints, the fixed source panel and duplicate merged/Tier1 truth.
It retains each declaration's GT/FILTER and four comparisons, with no threshold,
realignment, trimming or deduplication. It refuses to overwrite output.
Its source-summary checks are not independent authentication of raw bodies,
original FASTA, executed commands or biological truth. Earlier body checks and
this result's hash-bound inputs supply the finite provenance used here.

The test file covers a known expanded/central inversion equality, a changed-flank
negative, a palindromic no-change case, both modes, invalid inputs and retained
GT0/0/FILTER. I reviewed it; I did not rerun its temporary-file tests. Kepler's
20-control pass and main's 20 tests plus broader 137 tests/62 subtests are supplied
execution evidence, not independent runs by this reviewer or biological validation.
Main reports one original diagnostic process: wall 0.16s/user 0.13s/sys 0.01s,
RSS 16,879,616 bytes. I did not independently reproduce that resource measurement.

I compared [sources_with_commands.json](../../results/inv_fixed_case_20261013/sources_with_commands.json)
against preserved sources.json, SHA256
`8f49e113eb3dd0e0071694d340a4b0701fed8ea42475d5993c16894e35bfe52e`.
Only header lists/counts and correction metadata changed; all 25 body identities,
counts and selected rows are unchanged. All restored aliases match retained raw
headers: eight CommandLine, one cmdline, four bcftools_viewCommand and four
bcftools_viewVersion. No new network bytes are recorded. Accept this metadata
correction without rewriting the original receipt or prior review.
Paths/command strings improve provenance but do not certify executed inputs,
reference bases or complete all-types output. The acquisition reference receipt
still labels diagnostic_result PENDING; the separately hash-verified comparison
is the actual result, not a reason to overwrite that earlier receipt.

## Meaning and next finite step

Original caller FASTA identity and actual coordinate semantics remain UNKNOWN.
Testing A/B does not exhaust all representations or prove either is correct.
Main's supplied static truth-writer report adds 1 to both boundaries, prefers a
Minimap2 union with VACmap fallback and can infer GT0/1 when the other haplotype
has NOSIGNAL. It is not the attested executed writer or independent haplotype proof.
Do not substitute ORIGINAL_LOCUS or tune shifts to reverse the negative result.

Symbolic INV can report partial junction evidence. A pure-INV patch omits actual
haplotype substitutions, complex components and alternate mapping placements.
Therefore these inequalities do not establish distinct actual alleles, full-allele
non-recovery, true CN/phase, or original all-types caller absence. INV-only export
and the 2025 source versus 2026 nine-caller publication limits still apply.
The earlier nine selected INV declarations remain present, including GT0/0;
neither their presence nor this negative comparison proves carrier recovery.

```text
36 conditional inequalities -> pure-INV equality explanation rejected
                            -> qualified mapped input available?
                               no: HOLD input trace
                               yes: inspect molecules and loss stage
```

A next trace is worthwhile only with named, usable input evidence: test ordered
junction/orientation support, alternative mappings and candidate/filter/export
retention against applicable strong callers. Existing accepted S1 DNA alone does
not certify mapped/indexed availability. No full-assembly proof or clinical
phenotype is required before this cheap inspection. Input evidence must separate
the expected structure from alternatives before an algorithmic loss is claimed.

This HG002 simple case remains development evidence. A mechanism beyond current
SVision-pro/Severus capabilities, precision controls and independently held-out
loci/samples would be needed before a larger study. No architecture or publication
claim follows from exact inequality. HG002 annotation/HG008 stops remain intact;
the full goal is active and unmet.

Audit: read-only local recomputation; no public-source refetch, raw-data download,
whole-reference scan/index, model, native job, Git or other-file edit. Only this
new note was written; the earlier full review remains untouched. Reviewer continues.
