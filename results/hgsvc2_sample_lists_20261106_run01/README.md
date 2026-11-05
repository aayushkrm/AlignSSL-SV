# HGSVC2 PanGenie sample-list crosswalk

The source, protocol and limits are in
`docs/research/2026-11-04-paired-dna-rna-feasibility.md`. Four bounded text
responses and every retrieval attempt are retained with SHA256 receipts.
The release manifest's sizes and MD5 values match the README and both sample
lists. The sample-list rows have the form `SAMPLE_ERR...`; the crosswalk
compares only the left sample token to the 60 exact RNA titles and retains
the full matching rows. It does not inspect any VCF or genotype.

Reproduce with `analysis/crosswalk_hgsvc2_sample_lists.py` after preserving or
moving the existing `crosswalk.json`: the script refuses to overwrite it.
