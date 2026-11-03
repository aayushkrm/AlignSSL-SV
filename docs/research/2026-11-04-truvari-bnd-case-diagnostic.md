# Truvari BND mate-contig case diagnostic

## Protocol, written before native execution

The synthetic SnpEff annotation replay changes `chrA`/`chrB` to uppercase
inside BND ALT fields. The public COLO829 file has a similar case difference.
Check a second SV comparison tool before assuming the Verix outcome is
general. This is an exploratory metamorphic test, not a performance study.

Create a fresh two-record artificial VCF from the same two reciprocal BNDs,
with one invented heterozygous sample. Create a second copy in which only
the two ALT mate-contig tokens differ in case, consistent with the tested
SnpEff output. Preserve reference coordinates, MATEID, FILTER, genotype,
headers, and all other fields. Retain both plain inputs, their BGZF/indexed
copies, exact package versions, commands, logs and outputs.

Run native Truvari 5.4.0 on the four ordered comparisons: each input against
itself, and each input against the other. Use the same BND distance, zero
minimum sizes, and other explicit flags in all four commands. Before the run,
inspection of this installed version's `bnd_match` shows an exact string
comparison of the remote chromosome, so it predicts self matches and cross
mismatches. The observed output, warnings and any failures will be preserved.

The two records describe one invented adjacency. Self-comparison scores and
case-change mismatches cannot establish real-caller sensitivity, false
negatives, or a benchmark result. A remote name with different case is not
automatically a valid alias; this experiment asks how a particular consumer
reacts, not whether its exact-string behavior is wrong. Independent review
is pending.

## Result

All four Truvari commands exited 0. The native summaries report:

| Baseline → comparison | `TP-base` | `TP-comp` | `FP` | `FN` | `f1` |
|---|---:|---:|---:|---:|---:|
| Header case → header case | 2 | 2 | 0 | 0 | 1.0 |
| Upper case → upper case | 2 | 2 | 0 | 0 | 1.0 |
| Header case → upper case | 0 | 0 | 2 | 2 | null |
| Upper case → header case | 0 | 0 | 2 | 2 | null |

These are **two BND records for one synthetic adjacency**, not two independent
SVs. The cross-comparison F1 is explicitly `null` in the native output; do
not replace it with zero. These software-generated category names describe
the fixture comparison, not biological truth. The stderr logs contain native
INFO output and no warning or error lines. The four commands used the same
explicit thresholds and filters; both inputs contain PASS, heterozygous records.

The separate [byte comparison](../../results/truvari_bnd_case_diagnostic_20261104_audit/byte-diff.json)
confirms that seven of nine lines are identical and the remaining two differ
only in the case of a uniquely matched ALT mate-contig token. This simplified
fixture does not include SnpEff's changed `ANN` annotations. Full native
outputs and 63 verified file hashes are in the
[replay packet](../../results/truvari_bnd_case_diagnostic_20261104_run01/README.md).

This confirms an effect in the two tested comparators, with different native
contracts: Truvari compares remote chromosome strings in BND records, whereas
the Verix result concerns record grouping. The strings in the transformed
fixture do not match declared contig IDs exactly. We do not label either
consumer's case-sensitive handling a bug. Real-world prevalence, independent
biological accuracy and clinical impact remain unknown, and independent
scientific review is still pending.
