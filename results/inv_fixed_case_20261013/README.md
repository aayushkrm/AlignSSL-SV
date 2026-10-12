# Fixed HG002 inversion source panel

13 October 2026, Asia/Tomsk. **Reject the zero-record premise; keep allele
equivalence and caller-mechanism claims separate.** This is a selected published
case diagnostic, not a new inversion discovery or accuracy benchmark.

The first published TableS10 HG002 row was frozen before caller bodies at
commit8e8c76e: chr2:240685775–240688980,3,205bp. No replacement case is selected.
Twenty long-read VCFs, two additional short-read controls and three truth VCFs
come from author commit ee77a2f336bf055e5234d7565389aafda56b85cd. Source2025
release and the2026 nine-caller paper are not automatically the same execution.

| Complete source check | Actual result |
|---|---|
| Whole saved bodies |25files;6,087,705bytes; every size/Git blob SHA1/SHA256 passes |
| Pinned-tree metadata |168,192bytes;603entries; not truncated |
| Merged / Tier1 / Tier2 truth records |125 /72 /53; all three gzip EOF/CRC checks pass |
| Target in truth | Same raw row in merged and Tier1; absent Tier2; symbolic INV, PRECISE, GT0/1, maternal source label |
| Caller selections | One nearby Severus ONT/Minimap2 INV16,229bp, GT0/0; eight larger spanning INV declarations from Severus/Sniffles2, some GT0/1 |
| Literal target geometry | No caller record declares the target's exact POS/END/3,205bp geometry |

All25 files declare chr2 length242193529. This is consistent with hg38, not
exact reference-base attestation. The truth's two repeat-flank annotations are
source assertions, not independently verified inverted repeats or exact allele
sequence. The one nearby call starts at240685789, equal to ORIGINAL_LOCUS start,
but ends at240702018 and has GT0/0. It is not carrier detection of the truth.
Spanning records must not be discarded as blank output or counted as recovery
solely because they overlap. No F1, recall, prevalence or genotype error is inferred.
INV-only exports do not establish absence from original all-types outputs.

## Retained sources and correction

Original bodies remain outside Git:
`/Users/akm/aayushkrm-AlignSSL/runs/inv-fixed-case-20261013.EBNrEy/`.
[sources.json](sources.json) is the immutable first acquisition receipt, SHA256
8f49e113eb3dd0e0071694d340a4b0701fed8ea42475d5993c16894e35bfe52e.
[sources_with_commands.json](sources_with_commands.json), SHA256
cf2afb766f55035dc03c8cb095599eda35ba4d85c4713044b41ea64356312ca7,
is a local-only correction. It adds8CommandLine,1cmdline,4bcftools_viewCommand
and4bcftools_viewVersion headers. All biology fields/rows/hashes/selection remain
unchanged; new network bytes0. The [attempt record](first-attempts.txt) retains
the omission and a local verifier NUL-construction error as a transcription.

Commands reveal SVIM QUAL>=10 filtering and different ONT input path labels
across aligners. Paths alone do not prove different data, equal input or filtering
of every caller. No commands from the source headers were executed.

The [maintained review](../../docs/research/2026-10-13-inversion-fixed-case-review.md)
independently verifies all25 bodies and the selected records. Its accepted
scope does not validate biological truth or current native callers.
The [separate pure-INV check](../inv_path_equivalence_20261013/README.md)
finds no exact sequence equality under its explicit reference/mode assumptions.

## Reproduction and next scope

Fetcher: analysis/fetch_inv_fixed_case_sources.py. Public source acquisition occurred
once. The corrected receipt can be regenerated to a distinct path without any
network operation using --from-manifest, --manifest and --first-attempts.
Never overwrite the original receipt or retained bodies. New fetches require
a fresh source directory and a new output path; do not repeat this acquisition.
Twenty-one offline fetcher controls pass. Combined software scope is recorded
with the path result; these controls are not a biological result.

One existing mapped/indexed HG002 input is available on the cluster for a
separate bounded trace. It is not the benchmark's attested read set. No mapped
case records, native caller or expensive experiment have been run by this panel.
The old annotation/HG008 generic-detection studies remain stopped; goal unmet.
