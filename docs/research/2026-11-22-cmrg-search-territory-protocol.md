# CMRG deletion pilot search territory

Prepare gene intervals before using the read library or allele coordinates.
The [scientific decision](2026-11-22-scientific-direction-decision.md) uses
the 395 candidate genes reported by Wagner et al., including names without
CMRG benchmark truth. Use the exact [reproduced roster](../../results/cmrg_gene_roster_20261122_run01/genes.tsv)
and the [GENCODE v46 comprehensive annotation for reference chromosomes](https://www.gencodegenes.org/human/release_46.html).
This step joins public annotations only.

Match case-sensitive gene symbols to autosomal `gene` features. Keep every
input name and every candidate Ensembl gene ID. Assign a coordinate only if
there is exactly one distinct gene ID and interval. Report no-match and
multi-match names separately. Do not use historical aliases or rename a
gene as part of this pass. Use the pinned reference index for chromosome
length bounds. Convert the GTF start to zero based before adding 2,000 bp
to both sides of the half-open gene interval, then clip to the chromosome
bounds. Keep the individual gene intervals and their union separately.
Measure the number of names placed, number of merged intervals and union
size. Freeze the output hashes before any proposer sees reads.

This first exact-name report is provisional if it contains unresolved
symbols. Before the actual caller or read comparison, resolve any such
symbol against authoritative gene histories, verify the final FASTA
compatibility, and record any explicitly unplaced names. This roster,
rather than benchmark VCF records or confident-region masks, defines the
generator's search space. The scorer separately applies the truth masks,
the sequence and context rules, and the flank requirements.
