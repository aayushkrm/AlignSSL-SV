# SVJedi-graph: bounded input and CLI assessment

14 October 2026. Source and README assessment only.

## Decision

**UNSELECTED; NOT THE NEXT LAUNCH.** The post-trace investment decision closes
this simple inversion as a new-method lead and sets further case compute and
setup to zero. This note records interface facts for a possible future,
distinct question. It does not reopen the case or qualify a run.

The current interface has no fatal small-reference mismatch for a local,
known-catalog placement diagnostic. It can build a graph from the contigs that
the user supplies. A one-contig FASTA can therefore represent a local region.
Such a graph cannot test genome-wide placement uniqueness.

## Source pin and dependencies

The author repository's newest listed tag is `v1.2.2`, at commit
`ad345a9b79304a20a1a77e860ea970cdc15f661e` (15 April 2026). The tag and commit
are the source pin for this assessment. The paper describes SVJedi-graph
v1.1.1, so its reported performance is not evidence that v1.2.2 is qualified
on this case. [Author repository and tag](https://github.com/SandraLouise/SVJedi-graph/tree/v1.2.2),
[pinned commit](https://github.com/SandraLouise/SVJedi-graph/commit/ad345a9b79304a20a1a77e860ea970cdc15f661e).

The v1.2.2 README lists Python 3.8.13 or later and `minigraph`. It does not
pin a minigraph release or provide a lock file in the inspected tree. The
paper used minigraph v0.19 with `-x lr`, without base-level alignment. That is
the paper's method setting, not a verified current runtime dependency.
[Pinned README](https://github.com/SandraLouise/SVJedi-graph/blob/ad345a9b79304a20a1a77e860ea970cdc15f661e/README.md),
[primary paper, Methods 2.1–2.3](https://pmc.ncbi.nlm.nih.gov/articles/PMC10311344/).

The documented CLI is:

```text
svjedi-graph.py -v <input.vcf> -r <reference.fa> -q <reads.fastq> \
  -p <output-prefix> -t <threads> -ms <minimum-support>
```

The README says `-ms` defaults to 3 alignments. A future descriptive run would
keep that value explicit. No dependency was installed and no command was run.

## Reference and coordinate contract

The paper describes a graph for the whole reference plus the input SV alleles.
The pinned graph constructor reads every FASTA record supplied, uses the first
whitespace-delimited token after `>` as its sequence name, and requires each
VCF `CHROM` to match a supplied name exactly. It builds reference paths for
the supplied contigs. It does not check that those contigs make up a whole
human genome. This small-reference conclusion follows from the pinned parser;
it is not a claim that the authors benchmarked a cropped reference.
[Pinned graph constructor](https://github.com/SandraLouise/SVJedi-graph/blob/ad345a9b79304a20a1a77e860ea970cdc15f661e/construct-graph.py).

The project trace protocol uses `chr2 [240675000,240704000)` as a 29,000-base
reference slice. A technically valid local input would use a FASTA header
`>chr2`, VCF `CHROM=chr2`, and coordinates translated to that slice. For the
declared target (`POS=240685775`, `END=240688980`), local VCF coordinates are
`POS=10775`, `END=13980`; their difference remains 3,205 bases. Copy the
predeclared overlapping inversion records from the frozen panel and apply the
same coordinate transform. Keep all their breakpoints inside the supplied
contig. Do not replace the target with the separate `ORIGINAL_LOCUS` annotation
(`240685789–240688966`); that is a different, unselected coordinate
hypothesis. [Post-trace decision](2026-10-14-inversion-post-trace-investment.md),
[mapped-input trace protocol](2026-10-13-inversion-mapped-input-trace-protocol.md).

A 100 kb single-contig slice would also fit the parser if its FASTA name,
coordinates, and VCF records agree. It would still omit the rest of the genome
and could omit competing repeat placements. The 29 kb slice is enough to
represent the frozen target coordinates. The exact decoy VCF was not rebuilt
or checked against the crop in this source-only pass.

## Reads, filters, counts, and outputs

The paper accepts long reads in FASTA or FASTQ. The same retained set means one
full sequence record for each of the 47 QNAME labels, not 52 regional BAM
alignment records. These reads were selected by a reference-coordinate fetch.
They are not a blind discovery input or the original benchmark's 20 caller
inputs. Their results would be conditional on that selection.

The published filter treats an alignment as informative when it covers a
graph breakpoint, with at least 100 bp on each side by default. It first
requires an alignment to cover at least two graph nodes. Inversions have two
breakpoint edges per allele. A single read can add support at both edges, so
edge counts are not counts of independent molecules. The tool estimates a
genotype from normalized allele support; it does not establish genome-wide
uniqueness. [Primary paper, Methods 2.2–2.4](https://pmc.ncbi.nlm.nih.gov/articles/PMC10311344/).

With output prefix `<prefix>`, the README documents these files:

| File | Contents |
|---|---|
| `<prefix>.gfa` | Constructed graph |
| `<prefix>.gaf` | Minigraph graph alignments |
| `<prefix>_informative_aln.json` | Read support by input SV and allele |
| `<prefix>_genotype.vcf` | Input SV set with predicted genotype |

These outputs could show how the supplied reads align and which declared
alleles receive edge support. They cannot show that omitted genomic locations
were considered when a cropped reference was used.

## Prospective input shape; no launch selected

If a future, distinct question reopens this baseline, the smallest source-
compatible packet is one 29 kb `chr2` FASTA slice, one VCF with the frozen
target and all predeclared overlapping INV decoys on that slice, and one
FASTQ with one full sequence per retained QNAME (47 records). Keep the
reference allele as the graph's reference path. Keep source truth fields and
the translated coordinates traceable to the frozen declarations.

The documented command shape would be:

```bash
svjedi-graph.py \
  -v inv_panel.local.vcf \
  -r chr2_240675000_240704000.fa \
  -q retained_47.fastq \
  -p svjedi_inv_v1.2.2 \
  -t 1 -ms 3
```

This is a prospective interface example only. No FASTA or VCF was created, no
read sequence was accessed, and no command, install, or job was performed.
The output would be a known-catalog placement/genotyping diagnostic on the
retained reads. It must not be described as blind discovery, global mapping
uniqueness, recovery on the published 20-input benchmark, or current tool
qualification. The simple case remains closed as a new-method lead; the
broader research pivot continues separately.
