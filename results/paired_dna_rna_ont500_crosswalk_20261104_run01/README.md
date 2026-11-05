# Exact RNA-to-ONT-500 metadata crosswalk

`crosswalk.json` records the exact string joins between 60 RNA sample titles,
the earlier 1,019-sample Vienna manifest, and the separate ONT-500 metadata.
It yields 11 Vienna matches, 13 ONT-500 matches, no exact overlap between those
sets, and 36 RNA titles with neither exact match. The ONT-500 table contains
`GM` names and no `NA` names; no alias conversion has been performed.

```sh
python analysis/crosswalk_ont500_metadata.py \
  --vienna-crosswalk results/paired_dna_rna_crosswalk_20261104_run01/crosswalk.json \
  --ont500 results/paired_dna_rna_ont500_metadata_20261104_run02 \
  --output /tmp/ont500-crosswalk-new
```

These counts are metadata matches, not proof of sample identity, SV truth,
usable RNA coverage, or independent test examples. See the
[feasibility note](../../docs/research/2026-11-04-paired-dna-rna-feasibility.md).
