# Provisional search territory from GENCODE v46

The [protocol](../../docs/research/2026-11-22-cmrg-search-territory-protocol.md)
was registered at `a173624`. The GENCODE file matches its publisher MD5,
and the roster and chromosome-length index match their recorded hashes.

Of 395 names, 382 have one exact autosomal gene feature, 12 have none, and
one has more than one. The receipt lists every symbol and match, including
the unresolved names. The 382 placed genes yield 368 merged intervals
covering **23,732,357 bases** after adding 2 kb to both sides. The BEDs are
provisional until the missing and multiple names have been reviewed.
No read, truth VCF, or allele coordinate contributed to this search space.

Reproduce with
`python3 analysis/prepare_cmrg_gene_territory.py --roster results/cmrg_gene_roster_20261122_run01/genes.tsv --cache CACHE --out NEW_OUTPUT`.
