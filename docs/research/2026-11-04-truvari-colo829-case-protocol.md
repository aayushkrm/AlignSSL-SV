# Truvari on COLO829 BND case aliases

## Protocol, written before native execution

The two-record synthetic Truvari test gives self matches and case-only cross
mismatches. Test whether the same behavior occurs for **all 66 BND records in
the one previously examined public COLO829 caller VCF**. This is a matched-file
software diagnostic; the inputs derive from the same callset and do not form
independent biological truth. The case and source were already inspected.

Verify the pinned original compressed source hash. Generate the existing
case-only ALT mate-contig mapping using the uniquely matching header IDs.
For both versions, retain all and only `SVTYPE=BND` records, all FILTER
values, and the first eight original VCF fields. Drop FORMAT and sample columns
from both copies so no missing or invented genotype is compared; this site-only
projection is identical in both inputs. Preserve INFO, including the original
`ANN` fields, so the case-adjusted VCF may have inconsistent annotations and
is not a production-normalized callset. Keep an explicit input manifest and
independently byte-check that the two projected copies differ only in ALT
mate-contig case. Inputs and any source-specific full VCFs remain outside Git.

BGZF-compress and index both site-only inputs. Run native Truvari 5.4.0 in
four ordered comparisons: both self-controls and both cross comparisons.
Keep BND distance 1, reference distance 1, zero size thresholds and sequence
similarity 0, with no PASS-only filter, in all four. No reference, benchmark
truth, or sample genotype is used. Preserve all native outputs, errors and
file hashes. Based on the already inspected exact chromosome comparison,
predict self matches and zero cross matches if all 66 records are accepted;
any filtering, failure or different outcome must be reported in full.

This can show a representation-sensitive comparison on this one processed
public VCF. It cannot estimate tool sensitivity, false-call rates, clinical
impact or prevalence in other datasets. Independent review remains pending.

## Result — independent review pending

All four native commands exited 0 and counted all 66 projected BND records
on each side. The two self-controls each reported `TP-base=66`, `TP-comp=66`,
`FP=0`, and `FN=0`. Both cross comparisons reported `TP-base=0`, `TP-comp=0`,
`FP=66`, and `FN=66`. In the cross reports, native `f1` is `null`, not zero.
The 66 records represent 33 reciprocal pairs in the earlier case-normalized
Verix audit; they are not 66 independent biological events.

The site-only input check compared 336 lines: 270 were identical and 66
differed only in the case of one uniquely matched ALT mate-contig token.
The 195 contig declarations, INFO fields and original FILTER values were
retained; all sample fields were removed from both inputs. Each native params
file records `skip_gt=true` and no sample. **Do not interpret genotype summary
fields:** even the self-control summaries report `TP-comp_FP-gt=66` and
`gt_concordance=0.0` with a `None`/`None` matrix. No genotype was supplied.

The 58 native packet files and six workspace input files pass their recorded
SHA256 checks. The [small packet](../../results/truvari_colo829_case_20261104_run01/README.md)
retains the complete commands, logs, reports, processed output VCFs and input
manifest; source-specific input copies remain outside Git. Logs have no
warning/error lines. The native category names are results of comparing two
representations of the same exploratory source; they are not false-variant
counts or measured clinical sensitivity.

Together with the [Verix check](2026-11-03-colo829-contig-alias-diagnostic.md)
and [synthetic SnpEff runs](2026-11-04-snpeff-annotation-replay.md), this
shows a plausible reproducible interoperation risk in two named tool versions.
It does not establish that the historical source intermediate was produced by
the tested binary, that case-insensitive names are universally equivalent,
or how often independent datasets and downstream workflows are affected.
Independent scientific review and broader prior-art/impact checks are required.
