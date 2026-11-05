# Public paired-DNA/RNA metadata sources

The [feasibility note](../../docs/research/2026-11-04-paired-dna-rna-feasibility.md)
describes the two source collections and the limits of sample-name joins.
This packet contains only public, small source manifests and a reuse policy;
no sequencing files or expression matrices were downloaded. The
[receipt](receipt.json) records source URLs, retrieval time, HTTP metadata,
sizes and SHA256s. The MD5 values inside the Vienna manifests describe
listed remote files; their underlying data files have not been downloaded or
verified.

Regenerate the metadata packet with a new output directory:

```sh
python analysis/fetch_paired_metadata.py --output /tmp/paired-metadata-new
```

The ENA sample aliases in this first report are study-specific. The separate
[ENA title packet](../paired_dna_rna_ena_titles_20261104_run01/) supplies
the sample-title field needed for a cautious exact-name crosswalk.
