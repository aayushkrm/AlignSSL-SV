# ONT-500 Sniffles object listing

This packet contains the complete S3 response for the public hg38 Sniffles
2.6.2 prefix and a summary matching exact RNA/metadata names. All 13 exact
ONT-500 targets have one listed VCF and its matching CSI. The listing reports
1,000 objects and no further page. No VCF or index body was downloaded; ETags
are opaque and do not verify data integrity. The
[feasibility note](../../docs/research/2026-11-04-paired-dna-rna-feasibility.md)
describes the prior preview and the scope of the source-only check.

```sh
python analysis/audit_ont500_s3_listing.py \
  --cluster-helper /path/to/cluster.sh \
  --crosswalk results/paired_dna_rna_ont500_crosswalk_20261104_run01/crosswalk.json \
  --output /tmp/ont500-sniffles-listing-new
```
