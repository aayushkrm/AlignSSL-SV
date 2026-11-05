# ONT-500 metadata, local curl retry

`ont500_metadata.tsv` and `ont500_readme.txt` are the two small public
sources described in the [feasibility note](../../docs/research/2026-11-04-paired-dna-rna-feasibility.md).
The first Python retrieval attempt timed out. This curl retry and the separate
[cluster-curl retrieval](../paired_dna_rna_ont500_metadata_20261104_run03/)
returned identical SHA256s for both files. Commands, statuses and hashes are
in `receipt.json`. The 500-row table is metadata, not proof of an individually
usable SV callset.

```sh
python -m analysis.fetch_ont500_metadata_curl --output /tmp/ont500-metadata-new
```
