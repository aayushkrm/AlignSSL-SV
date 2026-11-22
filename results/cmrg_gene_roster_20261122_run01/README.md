# NIST CMRG candidate gene roster

The [CMRG paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9117392/) defines 395
challenging autosomal genes at or below 90% coverage in the earlier v4.2.1
benchmark on either GRCh37 or GRCh38. The author
[analysis](https://github.com/usnistgov/cmrg-benchmarkset-manuscript/blob/f56326c60641b5fef9e09e27fb02b78457091944/analysis/09_supplemental_table.Rmd)
and the source table pinned in the receipt supply that rule and its inputs.
Select the `gene` region and `v4` benchmark, keep autosomal coordinates with
usable coverage, then take the union of gene symbols at coverage at or below
0.9. The output has 395 symbols. Of these, 362 meet the rule on GRCh37 and
354 on GRCh38. A flag describes coverage in the author's source, not whether
the gene exists on that reference.

This gives an external list for the discovery territory. It does not apply
new coordinates, add flanks, choose variant loci or establish current
callability. The CMRG study reports a benchmark for a subset of 273 genes.
The pilot should retain the broader roster as its search domain and treat
regions without suitable truth as unscored rather than as absent variants.
