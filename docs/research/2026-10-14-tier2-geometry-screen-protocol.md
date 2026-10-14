# Existing HiFi input: Tier 2 geometry viability screen

14 October 2026. Prospective diagnostic, not yet executed. The selected S10
simple-inversion method lead remains stopped. This uses every HG002 Tier 2
source row, not a substituted favorable case. No new caller or paper selected.

## Question and decision value

Does native Breakinator flag any usable observed read group selected near
the printed Tier 2 endpoints in the existing GRCh38-mapped HiFi input?
Its published HiFi result used personal-reference alignment and cannot answer
this question. A direct screen avoids the invalid cross-reference report join.
It can reject this available-data assay before allele reconstruction or calling.

This is an assay-viability screen. A nonzero count is not evidence of incorrect
artifact labels, true inversion support, lost alleles, genotype error or a
publication contribution. Proximity to a truth row does not authenticate a read.
Zero has only the selected-window/observed-group scope stated below.

## Frozen selection before new alignment-body access

Use the already retained, complete Tier 2 VCF from INV-Benchmark commit
`ee77a2f336bf055e5234d7565389aafda56b85cd`:
`HG002_T2Tv1.1_asm_ref_2aligners.merged.vcf_Tier2.vcf.gz`.
Compressed size 6,215 B; SHA256
`3a4f950dbac34fda87a4994069e11b7530f5310cc19291a8d70838fe00c7ac89`.
Main verifies the retained bytes and whole gzip decode: 53 rows on 14 chromosomes.
These source rows are not independent donors or necessarily independent events.
Dot IDs and repeated coordinates remain; identify each row by its source order.

Use **all 53 printed POS and END pairs**. Convert each printed point to
zero-based `point = value - 1`; fetch `[point-25000, point+25000)`, clamped to
the declared chromosome bounds. Merge overlapping windows before indexed access.
Retain every row-to-window association. This is a coordinate-based selection,
not adjudication of the truth writer's one-base convention or actual junctions.
Do not shift toward ORIGINAL_LOCUS, confidence offsets or a flagged read.
Large repeat uncertainty can put an actual junction outside these windows;
that remains outside this finite screen, not an absent allele.

Source whole BAM/BAI, unchanged and already in permanent HOME:

```text
/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/hg002_dna_s1a_20261010_01/HG002_WGS.haplotagged.bam[.bai]
```

Accepted sizes are 48,727,325,910 B and 21,582,928 B. The historical hashes are
in the earlier input-custody record; do not relabel them as fresh rereads.
The header names hg38.analysisSet.fa/pbmm2 1.10.0. Check every selected truth
contig length against the BAM header and require its existing index. This is
a declared GRCh38 reference plane, not exact whole-FASTA base attestation.
No new reference, index, genomic download, alignment, assembly or RNA work.

## Observed groups and native input

Retain all fetched records, without MAPQ, flag, phase or agreement filtering.
Deduplicate repeat retrievals of exactly the same source alignment. Write a
derived, name-sorted BAM with original sequence, quality, coordinates, CIGAR,
flags and tags. Preserve the original source and the complete derived input.
The native tool applies its own default MAPQ/length rules afterward.

For the eligibility census, require usable stored payload, consistent full
forward-query sequence across observed segments, a single observed primary,
and consistency between declared SA segments and fetched nonsecondary records.
Missing, conflicting, hard-clipped or otherwise required-but-unobserved segments
make the group **UNKNOWN**. Do not synthesize alignments from SA text.

Call an eligible unit an **SA-consistent observed group**. This does not prove
source-molecule completeness, unique placement, recovery of every alternative,
all secondary alignments or unmapped evidence. Raw UNKNOWN groups remain
preserved; exclude them from a zero-flags interpretation. Native classifications
and all event/window censuses must retain these distinctions.

Use author native Breakinator **v1.1.1**, with default classification settings:
MAPQ10, segment length200, fold distance200, symmetry margin0.1 and chimera
distance1,000,000. One I/O thread and `--rcoord` change resources/reporting only;
do not use `--no-sym`, tune thresholds, or compare a parameter sweep.

The official Linux-musl asset is 3,547,379 B, published 10 November 2025,
SHA256 `00747b208e25887eac9e61db57496085d2a593cb6899e1b2940ca9ab1c9c2310`.
The actual executable/version and source pin must be recorded before execution.
Synthetic native ABI controls pass through the same BAM/report route first:
contiguous reference, central foldback, noncentral foldback and cross-chromosome
join. These are interface/geometry controls, not independently verified artifacts.

## Endpoints and stop rules

Report all source rows/windows, EOF/cap status, fetched/deduplicated records,
unique group labels, eligible and UNKNOWN groups/reasons, and native outcomes.
Separate foldbacks, chimeras and nonartifact breakpoints. Retain the native
flagged location and its association with source windows: a selected read may
be flagged at a different position, not the truth event.

- Zero flags in a nonempty, adequately observed eligible set can close this
  **HiFi assay** as a low-yield investment. It does not exonerate filtering in
  UNKNOWN/elsewhere-mapped/unmapped reads, other technologies or true alleles.
- Any flag identifies only a candidate for later molecule/event adjudication.
  No automatic follow-up campaign, invented event threshold or positive claim.
- Empty/poorly observed input, incomplete fetch, cap, changed source, parser or
  native failure closes the attempt incomplete/uninformative, not a zero screen.

No recall, precision, prevalence, confidence interval or biological replication
claim follows. HG002 and these selected loci are development evidence; held-out
confirmation would need a separately justified future study.

## Finite execution envelope

One CPU, 2 GiB RAM, 15-minute allocation; no GPU or idle whole node. Use writable
physical scratch and direct `srun`, not the known failing batch/HOME-write route.
At most 50,000 fetched records across the entire merged collection, not per
window. Per derived BAM cap128MiB, metadata32MiB, retained-leaf allowance1GiB;
stage checks are not a filesystem quota. BGZF/native buffers can overshoot a
sampled size boundary; preserve and report any failed partials honestly.
Extractor soft300s plus explicit outer timeouts/scheduler bounds native calls.
Code, exact global caps, output locations and timings are pinned at launch.

Preserve controls, every failure and all outputs in permanent HOME through
writable login I/O, with hash checks before 22 October scratch expiry. Raw BAMs
and genomic sequences stay outside Git. No overwrite, automatic replay or cap
inflation after an outcome. Review before expensive work or major positives.

The [independent pivot review](2026-10-14-pivot-scout-review.md) accepts the
scientific scope of one real-input screen, not code/runtime or an actual result.
The full publication goal remains active and unmet. DeepSV is historical only.
