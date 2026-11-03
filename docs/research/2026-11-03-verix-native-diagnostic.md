# Native Verix junction-pairing diagnostic

## Question and scope

Does the pinned native Verix benchmark distinguish two grouped synthetic
events with identical breakend positions and local orientations but different
reciprocal mate pairings? This is an interface diagnostic, not a caller
benchmark, biological result or novelty claim. The 2026 Verix paper and its
README explicitly describe breakpoint-set evaluation; they are essential
prior art, not a strawman.

The local source checkout is `PopicLab/verix` commit
`7cb8524a941ce0d81dd04b0de51e009199386614`, reporting v0.0.2. Its installed
Python modules were compared byte-for-byte with this checkout before the run.
The standalone environment uses CPython 3.12.14 on the local x86-64 machine.
The initial package install retried network downloads before succeeding; no
cluster allocation or genomic reads are used.

## Synthetic construction and controls

An all-A, 40,000-base `chr1` contains two cuts between 1000/1001 and
30000/30001. Breakends a/b/c/d are at those four positions, with local
directions R/L/R/L. Each callset contains four VCF 4.3 BND records. The ALT
and MATEID fields encode reciprocal mates; each record has `EVENT=event1`,
`SVTYPE=BND`, PASS, and the same phased genotype `0|1`.

| Synthetic event | Reciprocal novel-adjacency pairs | Structural interpretation |
|---|---|---|
| Truth | a–c, b–d | Inverted intervening segment on a linear molecule |
| Rewired | a–d, b–c | Deleted linear derivative plus a retained circular intervening segment |

The circle is an explicit synthetic construction, including its retention;
this does not claim that a circle exists in a real sample or that a particular
caller emits these records. Both hypothetical events have the same four local
breakends and copy the segment once across their modeled molecules. The VCF
represents one grouped event, not a complete long-read phasing proof. The
[VCF specification](https://samtools.github.io/hts-specs/VCFv4.3.pdf) describes
reciprocal BND notation and inversion examples.

Self-versus-self must be complete in both configurations. Three separate
controls alter one position, one local orientation, or all genotypes; each
should fail to receive a complete match under the strict settings. The
orientation control is a parser-sensitivity perturbation, not a second
independently validated full chromosome model. If any control fails, do not
interpret the rewired case as a verified native behavioral result.

All commands explicitly group BND records by the common `EVENT` field using
the tool's multi-record format. The default case keeps the native matching and
merge thresholds. The stricter case sets `--breakend_mode`, type/genotype/
insertion enforcement, zero positional tolerance and zero breakend merging.
The query is evaluated against the truth in both configurations. A complete
rewired match would document behavior on this synthetic grouped input only;
it would not establish an error in a real callset or a publication opportunity.
The public HPRC source remains unqualified for such a comparison.

## Actual run and independent review

The [run packet](../../results/verix_junction_diagnostic_20261103_run01/)
retains the generated VCFs, synthetic reference, native stdout/stderr, VCF
and JSON results, commands, exit codes and SHA256s. The generator and runner
are [versioned](../../analysis/run_verix_junction_diagnostic.py).

## Separate linear-derivative extension, specified after run01

Run01 was inspected before this extension was designed. Its rewired input
requires retention of a circular segment, so a second, separately recorded
fixture checks whether that assumption matters. It does not replace run01.

Use three cuts at 1000/1001, 15000/15001 and 30000/30001, with six ends
a/b/c/d/e/f in reference order and directions R/L/R/L/R/L. Let B be the
intervening segment b–c and C the segment d–e. The two inputs use the
lexicographically first two pairings among those with one connected linear
derivative, all segments retained once and no unchanged reference-partner
junction: truth `ac,be,df` gives prefix–reverse-complement(B)–
reverse-complement(C)–suffix; query `ad,be,cf` gives prefix–C–B–suffix.
Both encode the same local positions, directions, event group and genotype,
but differ in two adjacency pairs. Their synthetic reference uses a fixed,
deterministic pseudo-random sequence with A bases at every listed breakend; derived paths
are retained as sequences. This is an intentionally constructed pair, not a
claim about an observed rearrangement, and it is not a validation of phase.

Run the same seven native commands and three perturbed controls in a new
run02 directory. Self matches must be complete; the strict positional,
orientation and genotype perturbations must not be complete. Observe, rather
than prescribe, the rewired result. The version, scoring, unknowns and
interpretation boundaries are the same as for run01. No acceptance follows
without the independent reviewer inspecting the actual new packet.

## Actual results and independent review

Both runs finish with seven native commands returning exit code 0. Each
comparison parses one query and one target event. Native output reports:

| Input comparison | Default thresholds, explicit EVENT grouping | Strict oriented breakends, zero thresholds |
|---|---|---|
| run01 self | complete, 2 merged positions | complete, 4 ends |
| run01 rewired | complete, 2 merged positions | complete, 4 ends |
| run02 self | complete, 3 merged positions | complete, 6 ends |
| run02 rewired | complete, 3 merged positions | complete, 6 ends |
| Strict position control, both runs | not run | partial |
| Strict orientation control, both runs | not run | partial |
| Strict genotype control, both runs | not run | spurious |

These are the tool's `BEST_MATCH_CLASS` labels, not whole-allele accuracy.
The default case explicitly groups records by `EVENT` and otherwise uses the
native defaults, including a 2-bp merge threshold in the pinned CLI. The
strict case preserves all local ends and requires matching local orientation,
type and genotype at zero distance; it still reports a complete match for the
rewired grouped events. The control reports omit some aggregate metric fields;
missing fields are not filled with zero.

A separate [fixture traversal](../../analysis/verify_verix_linear_fixture.py)
parses the six run02 reciprocal BND records, verifies their REF bases and
mate positions, traverses the fixed reference blocks, and reproduces both
saved 40,000-base derivative sequences. The two sequences differ. Its output
is [retained](../../results/verix_junction_diagnostic_20261103/linear-fixture-check.json).
The input genotype is phased `0|1`; the reported grouped records print `0/1`.
This observation does not establish a phase error, as the example has no
independent phase anchors and Verix is being used for its described
breakpoint-set comparison.

The result illustrates the known distinction between matching a set of local
breakends and checking the connections between them. It does not show that
Verix claims to score full paths, that a caller produced either rearrangement,
or that this is a new method or meaningful biological finding. Real sample
truth, explicit caller claims, relevant baselines and a publication-level
contribution remain open. The [independent reviewer](2026-11-03-verix-independent-review.md)
accepts this narrow observation after examining the original files, input
graphs, controls and recorded results. It did not replay the native commands.
All 113 receipt-listed file checks pass; both new packet directories, including
the first circular construction, remain intact.

## Header correction and external validation, specified after run01/02

The independent reviewer found that VCF 4.3 reserves `MATEID` with
`Number=.`; run01/02 declare `Number=1`. Every synthetic record lists one
reciprocal mate and Verix accepted both packets, but that does not make the
header conform to the reserved-field declaration. The two received packets
will remain byte-identical. Create separate copies with only that header
declaration changed, validate the originals and corrected files with an
independent VCF validator, and repeat the same seven Verix cases for each
fixture family with the same settings. This is a provenance/format correction,
not a new optimization or a biological experiment. Record any validator
warnings, failures or changes in match classes without selecting outcomes.

The official EBI vcf-validator v0.10.2 macOS x86-64 asset passed its published
SHA256 check but failed at startup because the local Boost dynamic libraries
are missing. Its failure is retained as an environment finding. The official
Linux x86-64 asset is the alternative; its hash must be checked against the
publisher before use. Validator scope and its own results must be reported,
not assumed to prove all biological or VCF semantics.

## Actual header-only repeats and validator result

[Run03](../../results/verix_junction_diagnostic_20261103_run03/) and
[run04](../../results/verix_junction_diagnostic_20261103_run04/) preserve
run01 and run02, respectively, with only `MATEID`'s header cardinality changed
in each of the ten VCFs. The other fixture bytes are identical. Both sets
repeat the original seven native cases; all 14 commands return 0 and all
14 report JSON files are byte-identical to their original counterparts.
The repeats used eight local workers, with BLAS/OpenMP threads capped at one
per worker. Native match-list order can vary and is not treated as a result.

The EBI Linux validator v0.10.2 binary and cluster copy match the publisher's
SHA256 `7326fc83425f5367f9974aaa223f2b48b1854bf9ecd5e9e5eae3899b3107fc87`.
Slurm job `1614653` completed 0:0 on hydra-n2, with four CPUs, one second
elapsed, 1.349 measured CPU-seconds and 11,572 KiB maximum step RSS. It used
temporary node storage, not the unrelated MCF7 workspace. All 20 original
and corrected VCFs returned 0 with one warning each: no `reference` metadata
entry. **The validator also accepted the original `Number=1` declarations**;
its success does not establish that this reserved-field condition was tested.
No FASTA was supplied to this validator. The separate fixture traversal checks
REF bases and graph paths, but does not attest full VCF conformance.

The [review addendum](2026-11-03-verix-independent-review.md#addendum-header-only-repeats-and-external-validation)
independently checks the ten header-only byte differences, all 228 receipt
entries, repeated outputs and validator records. The reviewer did not replay
the runs or independently hash the remote binary. The original inputs,
results, control caveats and execution history remain visible.
