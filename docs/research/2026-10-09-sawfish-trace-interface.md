# Sawfish native trace interface: bounded source check

Date: 2026-10-09  
Source pin: [`PacificBiosciences/sawfish` `8fdf4cf1b16e366ae8291d4547a1da06affc5c4a`](https://github.com/PacificBiosciences/sawfish/tree/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a).

**Later main correction:** the original no-interval-selector finding below is
withdrawn. It omitted shared CLI arguments. Hidden global `--target-region`
exists and bounds BAM scanning, but still loads the reference and changes
some split-read inclusion. See the
[source-path correction](2026-10-09-sawfish-seed-and-target-source.md).
The original limited audit is preserved; do not use its negative finding.

## Finding

Sawfish has an interface for a small synthetic fixture. The source does not show a command that limits discovery to an interval in an existing whole-genome BAM. A one-contig FASTA and a mapped, indexed BAM for that contig could bound the input. This is interface-level feasibility only. Synthetic-input compatibility and runtime were not tested.

The discover CLI requires `--ref` and `--bam`. Its settings define no region or interval selector. `--expected-cn` and `--cnv-excluded-regions` are not candidate-region selectors; the latter explicitly does not affect SV breakpoint analysis. A hidden `--target-cluster-index` option keeps one cluster for refinement debugging. The CLI does not describe it as a way to limit region discovery or whole-genome scanning. [Discover CLI, lines 15–81](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/discover.rs#L15-L81), [cluster debug option, lines 158–193](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/discover.rs#L158-L193)

Sawfish documents `--disable-cnv` for targeted or non-WGS data. It disables CNV calling and read-depth GC-bias estimation. The option is a boolean flag, off when omitted, and conflicts with `--fast-cnv-mode`. Do not use fast mode for a small SV control: it skips smaller assembly regions and can remove all insertions and most deletions below about 1 kb. [Discover CLI, lines 65–81](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/discover.rs#L65-L81), [guide, lines 693–705](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md#L693-L705)

Joint-call defines a separate hidden `--disable-cnv` flag. It is also off by default; its comment says it disables additional CNV segmentation and output for all samples. [Joint-call CLI, lines 108–115](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/joint_call.rs#L108-L115)

## What each stage exposes

```text
mapped reads + reference
        │
        ▼
discover: candidate regions ── assembly.regions.bed
        │
        ├─ simplified candidate SVs ── candidate.sv.bcf
        └─ assembled SV haplotypes ─── contig.alignment.bam
        │
        ▼
joint-call: merge, read support, genotype, score, filter
        └─ genotyped.sv.vcf.gz
```

`assembly.regions.bed` describes regions targeted for assembly. `candidate.sv.bcf` stores simplified candidate SVs for joint genotyping with the aligned candidate contigs. The discover-stage `contig.alignment.bam` shows assembled SV haplotypes. The guide says it has contigs for single-breakpoint SVs; CNVs have none, and multi-breakpoint events have contigs for each breakpoint. [Discover and joint-call stages, lines 82–97](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md#L82-L97), [output definitions, lines 635–677](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md#L635-L677)

The final VCF is a later stage. The guide lists `MinQUAL` (QUAL below 10), `MaxScoringDepth`, `InvBreakpoint`, and `ConflictingBreakpointGT` filters. With CNV disabled, the maximum scoring depth is 1000. Therefore, final filtering can differ from candidate selection and assembly. [Final VCF, lines 408–410](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md#L408-L410), [filters, lines 428–449](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md#L428-L449), [joint-call QUAL option, lines 48–50](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/joint_call.rs#L48-L50)

These files are useful stage markers. They are not a full rejected-signal trace. The guide says discover outputs are not fully documented or intended for end users. It does not promise a record of every signal rejected before region selection, an assembly failure reason, or a causal explanation for an absent final call. [Guide, lines 635–653](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md#L635-L653)

## Input limits and command shape

The guide specifies mapped HiFi BAM or CRAM. It says pbmm2 is tested; supported-style alignments have supplementary records without hard clipping and exact split-read CIGARs in `SA`. The reference is required, and every BAM chromosome name must occur in the FASTA. The CLI validates the alignment through an indexed reader and rejects unmapped input. [Guide, lines 258–276](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md#L258-L276); [discover CLI, lines 268–294](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/discover.rs#L268-L294)

The default minimum indel size is 35 bp for co-linear insertion/deletion output. A smaller synthetic allele could fail this size rule even if the fixture reaches discovery. [Discover CLI, lines 127–132](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/discover.rs#L127-L132)

If a prepared one-contig fixture meets that input contract, the source-supported command shape is:

```sh
sawfish discover --ref <fixture.fa> --bam <indexed-fixture.bam> --disable-cnv --output-dir <new-discover-dir>
sawfish joint-call --sample <new-discover-dir> --disable-cnv --output-dir <new-joint-call-dir>
```

This runs over the whole fixture; it does not select a region within a larger BAM. The guide documents `joint-call --sample` as consuming the discover directory and reusing its BAM and reference paths. The CLI requires a completed discover directory for joint-call. [Guide, lines 99–135](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md#L99-L135), [joint-call sample input, lines 19–30](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/joint_call.rs#L19-L30), [completed discover check, lines 201–219](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/joint_call.rs#L201-L219)

## Evidence boundary

- **Positive:** the pinned source exposes candidate-region, candidate-SV, assembled-contig, and final-filtered-call stages. `--disable-cnv` supports targeted/non-WGS discovery.
- **Negative:** there is no discover interval selector in the CLI settings. A run on the existing full BAM is not made small by naming a BED interval.
- **Unknown:** whether a synthetic one-contig BAM will pass all caller assumptions, how small it can be, its runtime, and whether it will reproduce the biological mechanism. Source inspection cannot verify these points.

This read covered only the pinned user guide and discover/joint-call CLI definitions. It did not inspect caller internals, run an executable, or access genomic reads. It does not authorize a run. The generic released-callset route remains STOP; H_R remains UNTESTED. This note does not select a new direction. See the [native-control source check](2026-10-09-native-control-source-check.md) and [post-diagnosis value decision](2026-10-09-post-diagnosis-value-decision.md).

## Main integration: reporting threshold is not the seed threshold

Main independently fetched the cited pinned CLI sections. The discover source
also defines hidden `--min-indel-size-noise-margin`, default10. Its comment
explicitly says assembly may trigger below the reporting size because nearby
small indels can merge and because a complex non-SV haplotype improves
genotyping. Therefore, neither the50bp scientific SV definition nor the35bp
reporting default can be assumed to be the native candidate-seed cutoff.
The effective rule still needs discovery-internal inspection and executable
verification; do not infer its arithmetic or all rejected signals from this
CLI comment alone.
[Pinned source, lines158–170](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/discover.rs#L158-L170).

The cited initial unmapped-input check tests whether the BAM header has a
chromosome dictionary. It does not by itself prove that every record is mapped
or meets other alignment requirements. A synthetic fixture would need explicit
record-level checks. Main did not run one. The source main commit and the
latest release asset are also not assumed to be the same version.
