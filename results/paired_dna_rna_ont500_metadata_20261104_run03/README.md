# ONT-500 metadata, cluster-curl route

This independent transfer of the two public metadata files is byte-identical
to the [local curl retry](../paired_dna_rna_ont500_metadata_20261104_run02/).
`receipt.json` records the commands and hashes; no sequencing data were
transferred. See the [feasibility note](../../docs/research/2026-11-04-paired-dna-rna-feasibility.md)
for sample identity and reuse limits.

```sh
python -m analysis.fetch_ont500_via_cluster \
  --cluster-helper /path/to/cluster.sh --output /tmp/ont500-cluster-metadata-new
```
