# COLO829 BND contig-name interoperability diagnostic

## Exploratory observation and question

After inspecting the published COLO829 VCF, a whole-file census found that all
66 BND ALT mate-contig strings use uppercase `CHR...`, whereas the local
CHROM values and the 195 declared contig IDs use `chr...`. No BND mate token
exactly matches a header contig ID. Case-folding gives a unique header match
for the inspected records; case-sensitive identifiers are not automatically
interchangeable. This is an input representation issue to investigate, not
proof that the biological breakends are wrong.

The [previous anchor census](2026-11-03-colo829-bnd-anchor-census.md)
deliberately case-folds and removes a `chr` prefix when pairing. Its 66
reciprocal-record count therefore describes that explicit normalization; it
does not mean the original VCF uses exact mate-contig names. The source was
inspected before this diagnostic was designed, so the case and hypotheses
are exploratory.

## Fixed native comparison

Create one copy of the public caller VCF with only each BND ALT mate-contig
token changed to its unique case-insensitive header spelling. Abort if any
token lacks a unique header match. Keep all original records, INFO, FILTER,
genotype fields, local coordinates and alleles otherwise byte-identical.
Retain the original, transformed bytes, source hash and an explicit per-token
change manifest. This mapping is an operational alias assumption based on
the supplied header; it is not a general rule for every reference genome.
The source `ANN` values are deliberately untouched and may repeat the original
uppercase ALT allele. The transformed file is an isolated parser diagnostic,
not a generally corrected or annotation-consistent release VCF.

Use the pinned Verix v0.0.2 CLI in BND-only mode on four comparisons:
original/self, alias-normalized/self, original/query versus normalized/target,
and the reverse. All use zero position and merge thresholds with no manual
EVENT grouping. Record both group counts and raw native reports. Source-code
inspection predicts that the parser's exact mate-coordinate lookup can group
different numbers of BND events when the names differ. Observe all outcomes,
including failures, without using self-comparison F1 as evidence of accuracy.

This tests whether the **tested tool's grouping depends on this case-only
input representation**. It does not validate the alias biologically, prove
a caller error, infer a phased derivative path, or measure performance on an
independent truth set. Other software may handle aliases differently. No
training, tuning or held-out test data are involved.

## Attempt 01 and seekable-input correction

The first run completed original-versus-original but the other three native
commands failed: the case-normalized copy was written as ordinary gzip, and
HTSlib's reader reported `seek not implemented in files compressed by method
1`. This is an input-format failure, not a biological or benchmark result.
The [complete failed attempt](../../results/colo829_verix_alias_diagnostic_20261103_run01/)
and its receipt are retained.

The separate second attempt uses plain, seekable VCFs for both original and
case-normalized input. It checks their decompressed SHA256s against attempt 01
and regenerates the same case-only transformation before running the same
four commands and native flags. Both inputs now have the same storage format.
No locus, record, source filter, genotype, matching setting or outcome metric
is changed. The normalized INFO/ANN caveat above still applies. The raw source
and both original attempt files are preserved.

## Attempt 02 results — independent review pending

All four native commands exited 0. All 168 source records were retained;
the diagnostic parsed 66 BND records across all FILTER values.

| Query → target | Query groups | Target groups | Native class |
|---|---:|---:|---|
| Original → original | 66 | 66 | 100% complete |
| Normalized → normalized | 33 | 33 | 100% complete |
| Original → normalized | 66 | 33 | 100% partial |
| Normalized → original | 33 | 66 | 100% aggregate |

The cross-comparison reports do not contain precision, recall or F1. Do not
substitute zero for missing fields. A self-match is only a control and does
not measure biological accuracy. Each command emitted the same three HTSlib
header warnings about the declared `AD` and `DP` fields; the commands did not
fail. Full reports, stdout, stderr and the receipt are in
[attempt 02](../../results/colo829_verix_alias_diagnostic_20261104_run02/).

A separate [byte-level comparison](../../results/colo829_verix_alias_diagnostic_20261104_audit/byte-diff.json)
examined all 438 lines: 372 were identical, and the other 66 differed only in
the case of a BND ALT mate-contig token with one unique header spelling.
The separate [native-group audit](../../results/colo829_verix_alias_diagnostic_20261104_audit/native-groups.json)
found 66 singleton groups in the original and 33 pairs after this case-only
change. Every normalized pair has reciprocal source `MATEID` values. The
pinned parser groups using exact mate coordinates, not those `MATEID` values.
The code and commands needed to repeat these checks are in the
[audit packet](../../results/colo829_verix_alias_diagnostic_20261104_audit/README.md).

The public file's header reports SnpEff 5.1d. In an independent **synthetic**
replay, that version's parser and serializer uppercased the entire BND ALT,
including the mate-contig name, while preserving local CHROM case. See the
[SnpEff replay](2026-11-04-snpeff-case-reproduction.md). This is a plausible
source of the pattern; the original intermediate file and deployed binary
were not recovered, so causation in the 2024 workflow is not proven.

This observation is restricted to one public file and the pinned Verix
version. It is not evidence of a wrong biological call, a phased path, a
clinical error, or a publication result. The independent reviewer could not
finish because the subagent runtime returned a usage-limit error; no expensive
campaign or major positive claim is released on these provisional findings.
