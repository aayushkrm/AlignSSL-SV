# Sawfish source path: target selection and indel evidence

October9 local / October8 UTC. Source-only check at commit
`8fdf4cf1b16e366ae8291d4547a1da06affc5c4a`, independently resolved as the
annotated v2.2.1 tag target. No executable, genomic data or experiment used.

## Correction: a shared target option exists

The earlier interface note inspected discovery-specific arguments only.
Its statement that discovery has no interval selector is **withdrawn**.
The shared CLI defines hidden, global `--target-region` values. The option
is for debugging, and users must provide nonoverlapping regions. Top-level
settings flatten the shared arguments into the CLI.
[Shared option](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/shared.rs),
[top-level wiring](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/mod.rs).

Discovery constructs target regions and passes them to the BAM scanner.
The scanner selects target chromosomes and creates workers for selected
intervals; each worker uses indexed region fetch. However, discovery still
loads the reference FASTA before scanning. This is not a bound on total
reference, alignment-block, assembly or downstream I/O. Region syntax and
joint-call target semantics were not audited here.
[Discovery wiring, lines100–113 and171–178](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/discover.rs#L100),
[scanner implementation](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/bam_scanner.rs).

## Exact source predicate, not a guessed reporting cutoff

`get_min_evidence_indel_size()` computes
`max(min_indel_size, min_indel_size_noise_margin) - min_indel_size_noise_margin`.
The inspected CLI defaults are35 and10, so that source-level evidence size
is25bp, not35bp or the scientific50bp SV definition. This is now based on the
function body, not merely its explanatory comment. The installed binary and
its resolved defaults remain untested.
[Exact function, lines200–204](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/discover.rs#L200).

For CIGAR evidence, consecutive insertion/deletion operations accumulate.
Another operation flushes that candidate. The candidate must intersect the
worker region and have insertion OR deletion size at least the evidence
threshold. Scanner alignment/identity filters and MAPQ checks occur before
this evidence is accepted. Split-read and soft-clip paths also exist; failure
of this one CIGAR predicate cannot prove that the locus has no native seed.
Clustering, assembly and output rules remain separate.
[Indel predicate and CIGAR parser, lines191–315](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cluster_breakpoints/break_builder.rs#L191).

Targeted split-read inclusion differs from ordinary scanning. Its source
comment explicitly warns of broken cases under some target arrangements,
and the targeted branch returns on supplementary records. Do not infer
ordinary full-run failure from a debug-targeted absence without a matched
full-fixture control. A small complete fixture may still be the safer finite
control, but runtime/input compatibility is untested.
[Targeted split-read branch, lines413–429](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cluster_breakpoints/break_builder.rs#L413).

## Consequence and read scope

The interface is more capable than the initial bounded audit reported, but
debug targeting is not a validated substitute for default whole-input
behavior. The corrected seed predicate narrows any future fragmentation
test. It does not establish a project failure, a new mechanism, rescue,
scientific significance or publication lead. Generic repeat-fragment merging
and annotated-repeat seeding remain prior art. The old released-callset route
is still STOP; no data pass, installation, new reservation or campaign selected.

Main read full shared/top-level CLI, discovery and scanner sources, plus
relevant indel/split-read builder and discover-settings sections. Public Git
tree metadata located the files. HTTPS responses were capped at1MiB each;
no raw source files or example genomic rows were saved. The complete assembly,
clustering, region parser, helper libraries and joint-call implementation
were not audited. This correction changes the next feasibility decision;
it does not constitute a native execution result.
