# CNP0002230 offline archive crosswalk

This packet preserves public metadata retrieved on 16 October 2026 and
reconciled offline on 3 November. It contains no genomic read bodies. These
counts describe archive membership, not independent biological replicates.

| Frozen input | Source |
|---|---|
| `metadata_CNP0002230_experiment.tsv` | `ftp://ftp.cngb.org/pub/CNSA/data7/public_info/CNP0002230/metadata_CNP0002230_experiment.tsv` |
| `metadata_CNP0002230_sample_Microbial_sample.tsv` | `ftp://ftp.cngb.org/pub/CNSA/data7/public_info/CNP0002230/metadata_CNP0002230_sample_Microbial_sample.tsv` |
| `cnsa-data-download-links.txt` | `ftp://ftp.cngb.org/pub/CNSA/data7/public_info/CNP0002230/data_download_links_CNP0002230_ftp.txt` |
| `source-table-s3.xlsx` | [Published Table S3, PMC version 1](https://pmc-oa-opendata.s3.amazonaws.com/PMC10667312.1/mmc2.xlsx) |

Archive attribution: [CNSA project CNP0002230](https://db.cngb.org/data_resources/project/CNP0002230/),
Shen et al., [Cell Genomics 2023](https://doi.org/10.1016/j.xgen.2023.100364).
The project page displayed CC BY 4.0 at retrieval; PMC supplied CC BY metadata.
The XLSX is byte-identical to the earlier source-census copy. Source files
are unchanged. `inventory.json` records byte lengths and SHA256s, original
sample/run fields, source worksheet row numbers, unmatched records and exact
alias comparisons. Raw-file MD5s are declarations, not newly verified hashes.
Trailing tabs in the original TSVs encode empty final fields and are retained;
they are excluded from authored-file whitespace checks.

Run from the repository root, using Python 3 with the standard library:

```sh
python3 -B -m analysis.synvii_archive_inventory \
  --input-dir results/synvii_archive_inventory_20261103 \
  --output /tmp/synvii-inventory-new.json
```

Output must not already exist. Compare the new JSON with `inventory.json`.
No network access occurs. The parser is specific to this archive and Table S3,
not a general XLSX reader. Focused controls: `tests/test_synvii_archive_inventory.py`.

All 638 read-file URLs reconcile with 319 run rows, 292 experiments and
231 samples. Two separate reference-sequence links are retained. This does
not show complete assay coverage, resolve any clone's chromosome path, or
provide a quantitative fitness matrix. See the
[analysis note](../../docs/research/2026-11-03-synvii-archive-crosswalk.md)
and [independent packet review](../../docs/research/2026-11-03-synvii-packet-review.md).
