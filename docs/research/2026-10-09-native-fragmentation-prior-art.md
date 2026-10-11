# Native alignment fragmentation: bounded prior-art sidecar

Date: October 9, 2026. Source-only check. This note addresses one prospective
mechanism. It does not rank a new topic or approve an experiment.

## Finding

The strongest known mechanism is unstable long-read alignment inside tandem
and low-complexity repeats. One true repeat expansion can appear as several
separate insertions on the same read. Different reads can also place the
sequence inconsistently. These are already observed mechanisms. Generic
repeat-associated fragmentation, alignment instability, and local consensus
or realignment rescue are not new claims.

The specific proposed contrast remains narrower: does repeat interruption or
purity change pre-assembly fragmentation or candidate-region loss when true
allele length, read depth, and flanking anchors are held fixed? The sources
checked here do not report that matched causal contrast. This is a boundary on
the inspected sources, not evidence that the contrast is novel.

## Closest overlap and controls

| Work | What it already demonstrates or controls | Limit for this contrast |
|---|---|---|
| [TRsv (2025)](https://link.springer.com/article/10.1186/s13059-025-03718-z) | Its Fig. 1 shows single NA12878 HiFi reads with multiple repeat-unit insertions in the same tandem-repeat region. It reports fragmented insertions across minimap2, NGM-LR, and Winnowmap2. Its examples include two 169-bp pieces in a repeat with about 156 AAGG copies. The paper reports 14–28% fragmented insertions in its repeat-region analysis and merges same-read repeat insertions/deletions for repeat calling. | This is the closest direct demonstration of read-level fragmentation. It does not compare pure and interrupted alleles matched on true allele length, depth, and anchors. Some reported multi-event counts include multiallelic loci, and the shown fragments are not evidence specifically about sub-50-bp pieces. Publisher date checked: August 20, 2025. Inspected scope: article background, Results section “Problems in detecting TR variations,” and Fig. 1 caption; not a full methods audit. |
| [Qin and Li, “Challenges in structural variant calling in low-complexity regions”](https://pmc.ncbi.nlm.nih.gov/articles/PMC12758381/) | The earlier project review records a primary-paper example of inconsistent minimap2 alignments in a long LCR. Haplotype-aware multiple-sequence realignment recovered the two truth insertion lengths in that example. This already occupies generic LCR error and consensus-rescue claims. | It is an observational LCR study, not a purity/interruption intervention with length, depth, and anchors fixed. Prior project scope: primary Methods and Results were reviewed for the October 4 note; this sidecar did not repeat that full read. The linked preprint identifier [arXiv:2509.23057](https://arxiv.org/abs/2509.23057) dates to September 2025; current journal-version metadata was not refreshed here. |
| [SVDSS (2022)](https://www.nature.com/articles/s41592-022-01674-1) | SVDSS combines sample-specific strings, read mappings, partial-order consensus, and local realignment. The author-manuscript methods describe SFS extraction with Ping-Pong/FMD indexing, plus read smoothing and placement that use mapped-read CIGARs. | The methods excerpt does not describe an SMEM-only route. SVDSS is a relevant alternate discovery and consensus control, but not an alignment-independent control: preprocessing and placement use alignments. It does not isolate repeat purity. Publisher date checked: December 22, 2022. Inspected scope: publisher abstract/date and author-manuscript methods excerpt; not the full article. |
| [Sawfish guide, pinned revision](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md) | The existing source check records discovery outputs such as `assembly.regions.bed`, `candidate.sv.bcf`, and `discover.settings.json`, plus assembled-contig alignments. These give useful region-selection and assembly-stage controls. | The documented files do not record every rejected signal. Missing output alone cannot prove that candidate evidence was absent. The source check read selected guide sections at the pinned commit; it did not audit all discovery internals. |
| [Svirlpool v3 methods](https://www.biorxiv.org/content/10.1101/2025.11.03.686231v3.full) and [version history](https://www.biorxiv.org/content/10.1101/2025.11.03.686231v3.article-info) | V3 seeds candidate regions from annotated tandem-repeat intervals, then merges and extends regions. Local consensus and sequence-aware joint calling are also present. This is a control for repeat-informed candidate seeding. | The existing source check records v3 as the latest listed version, posted June 29, 2026. The README documents ONT inputs; HiFi compatibility is unverified. The prior check read the candidate-method passage, README, and version history, not the complete paper or code. |

## Contrast and rejection result

The useful contrast is not released-VCF F1. It is the stage before local
assembly: for truth-resolved INS/DEL alleles of at least 50 bp, compare matched
pure and interrupted repeats at fixed true allele length, depth, and flanking
anchor properties. Count per-read split operations, including pieces below
50 bp, and record whether each true allele's region reaches local assembly.
The design must keep the truth allele sequence fixed within a matched contrast
and identify alignment fragmentation separately from candidate-region
selection and assembly behavior.

One result would reject investment in this mechanism: after matching the
stated controls, pure and interrupted repeats have equivalent pre-assembly
fragment counts and candidate-region retention, with uncertainty narrow
enough to exclude the predeclared minimum worthwhile effect. A difference
that first appears after assembly would also fail this specific
pre-assembly-alignment hypothesis.

## What remains unverified

- The checked literature does not establish that purity adds an effect after
  true allele length, depth, and anchors are controlled.
- TRsv establishes repeat-associated fragmentation, but not the proposed
  purity effect or a specific excess of subthreshold fragments.
- Sawfish outputs expose useful stages, but do not prove complete logging of
  rejected candidates. Equivalent stage evidence for the other controls is
  not established here.
- Svirlpool's documented ONT scope does not establish compatibility with the
  project's HiFi data or environment.
- No project reads, alignments, executables, or candidate traces were opened.
  No installation or experiment was performed. No protocol or campaign is
  approved by this note.

## Search and source scope

Three targeted Exa searches returned five requested result slots each. The 15
slots were discovery results, not 15 papers read. Two primary methods sources
carry the fresh mechanistic assessment: TRsv's publisher text and the SVDSS
author-manuscript methods excerpt. The SVDSS publisher page supplied its date
and abstract. Qin/Li, Sawfish, and Svirlpool details above reuse the inspected
scope recorded in the [October 4 mechanism review](2026-10-04-modern-callset-falsifier.md)
and [October 9 native-control source check](2026-10-09-native-control-source-check.md).
The [October 8 payoff audit](2026-10-08-empirical-payoff-audit.md) already
warns against claiming generic repeat effects or consensus rescue as new.
The requested Luna/max execution is not backend-attested; no conclusion here
depends on model identity.

No conclusion here rests on absence from search results.

## Main integration and contrast correction

Main fetched TRsv's primary publisher text and read the fragmentation result,
Figure1 caption, development description and evaluation passage. These support
the existing same-read fragmentation and motif-aware merging control; reported
accuracy is not independent replication by this project. Images, supplements
and complete Methods were not inspected in that check.

Two design qualifications are required before any proposed test. Changing
repeat interruption changes sequence. A purity intervention cannot hold the
complete allele sequence fixed. Instead, declare the exact sequence in each
arm and distinguish a changed surrounding repeat context with a fixed inserted
segment from a changed allele itself. Match length, anchors and other stated
covariates; do not call the two arms biologically identical.

Also, sub50bp pieces do not prove native seed loss. Main's
[Sawfish interface addendum](2026-10-09-sawfish-trace-interface.md) records an
explicit native allowance for triggering assembly below its reporting size.
Any test must inspect the actual seed rule and compare the strong native
controls before inferring a pre-assembly bottleneck. No such test is selected
by this literature sidecar or addendum.
