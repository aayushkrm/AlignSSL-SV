# DNA/RNA metadata crosswalk

The [feasibility note](../../docs/research/2026-11-04-paired-dna-rna-feasibility.md)
explains the source selection, prior art and limitations. `crosswalk.json`
retains every RNA title and run, exact DNA-manifest matches and non-matches,
published DNA file paths/modes, the source code commit, and all input hashes.
It reconciles the two ENA reports by run ID and compares sample titles with
the author repository's explicitly listed 60 IDs.

To reproduce, use the adjacent metadata and ENA-title packets and a clean
checkout of [the RNA authors' repository](https://github.com/aline2593/DRS-LCLs-qtl-analysis)
at commit `70f64b309fd3325ec518857270b78d5f4e2a80f9`:

```sh
python analysis/crosswalk_paired_metadata.py \
  --metadata results/paired_dna_rna_metadata_20261104_run01 \
  --titles results/paired_dna_rna_ena_titles_20261104_run01 \
  --author-source /path/to/DRS-LCLs-qtl-analysis \
  --output /tmp/paired-crosswalk-new
```

The result is 11 exact shared labels, not 11 independently validated alleles
or a study powered to test a biological hypothesis. The remaining 49 RNA
titles are retained as non-matches to these Vienna manifests, not classified
as missing from every possible DNA resource.
