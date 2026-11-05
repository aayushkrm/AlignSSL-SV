# ENA RNA sample titles

`ena_titles.tsv` is a small ENA `PRJEB76585` read-run metadata report, not a
read dataset. The [receipt](receipt.json) records the exact API request,
retrieval time and SHA256. It adds `sample_title` to the earlier
[run manifest](../paired_dna_rna_metadata_20261104_run01/); the crosswalk
checks shared run/sample fields between the two responses before joining.

```sh
python analysis/fetch_ena_paired_titles.py --output /tmp/ena-titles-new
```

A title that matches a DNA manifest name is a metadata match, not proof that
the sequenced aliquot, cell-line passage, allele, or reference matches.
