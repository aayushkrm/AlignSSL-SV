# Conditional inversion path equivalence diagnostic

13 October 2026, Asia/Tomsk. Frozen before reading new reference sequence.
This finite diagnostic challenges a representation explanation for the fixed
case. It does not select a new method or change a benchmark metric.

## Inputs and explicit hypotheses

The first S10 case stays fixed. The completed source packet has one nearby
Severus INV declaration and eight larger spanning declarations from Severus/
Sniffles2. The truth has repeat-flank tags. Do not label the larger records
as either equivalent recovery or different biological alleles without evidence.

Question: under a stated standard hg38 reference and pure inversion model,
do any of these nine declarations reconstruct exactly the truth-declared
alternate sequence? Test all nine; keep their GT/FILTER, including0/0, visible.
An equal0/0 declaration is not a carrier/detection success. These records are
not nine independent biological events, and the fixed case is development data.

Use the standard UCSC hg38 chr2 interval [240675000,240704000),29,000 bases,
which contains all selected endpoints with padding. The official API specifies
zero-relative start and one-relative end (a half-open interval). Retrieve only
this region, with a128KiB HTTP body cap; no whole genome. It is an independent
canonical reference source, not proof of the exact original caller FASTA.
Existing cluster reference paths are also being inventoried; do not launch a
whole-genome streaming job merely to obtain this small reference region.

## Coordinate and sequence contract

The pinned truth writer adds1 to both zero-based boundary coordinates when
writing POS and END. Its precise executed version and the caller conventions
are not fully attested. Preserve this uncertainty instead of silently shifting.
Evaluate four predeclared pairs, with no best-case collapse or relabeling:

| Mode | Zero-based half-open inverted interval | Scope |
|---|---|---|
| A | [POS, END) | Anchored-boundary VCF interpretation |
| B | [POS−1, END−1) | Undo both writer boundary offsets |

Test truthA/callA, truthA/callB, truthB/callA, truthB/callB separately. Both
modes preserve END−POS. A matching mode is a conditional result, not license
to select a favorable coordinate convention; qualify the actual writer before
accepting a real equivalence claim. Keep the frozen printed truth, not the
ORIGINAL_LOCUS or a tuned breakpoint, as the target of this diagnostic.

For each pure INV, replace the corresponding reference interval by its
reverse complement inside the same complete29kb context. Only A/C/G/T are
eligible; letter case is mask annotation, not a different nucleotide. Refuse
ambiguous/missing sequence or endpoints outside the reference. Compare complete
strings exactly. No edit-distance threshold, identity cutoff, trimming, realignment
or call-size relaxation is chosen after seeing the result. Also flag any alternate
that equals reference; it supplies no distinguishable pure-inversion sequence.

## Claims and consequence

Exact equality can falsify the proposed difference of pure-INV declarations
under the tested reference/conventions. It cannot validate actual haplotype
sequence, phase, dosage, carrier genotype, copy state or caller input identity.
Severus/Sniffles symbolic INV output may be a partial-junction representation;
the pure INV reconstruction is an explicit model, not an observed full allele.

If every eligible comparison differs, reject this exact pure-inversion
normalization explanation only. Do not infer that callers missed all original
structures or that a new architecture will rescue them. Next work must inspect
qualified molecules/alignment/candidate evidence, not count screenshots.
Save hashes, all comparisons and negative outcomes; never replace source receipts.
No native caller, training, genome acquisition or expensive cluster campaign.
Independent review precedes any major positive conclusion or later costly work.
