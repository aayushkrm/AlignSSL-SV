# HGSVC3 deletion genotype inventory (feasibility only)

**Date:** 2026-09-23. **Input:** [official HGSVC3 v1.0 GRCh38 SV release](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/README_Variant_Calls_1.0.md), specifically `variants_GRCh38_sv_insdel_alt_HGSVC2024v1.0.vcf.gz` staged at `/scratch/igorno-alignssl_restart_20260922/hgsvc3-v1-grch38-sv`. Its SHA-256 is `cbdf253d1796b5cbcbaf17db072ebaa64a44204a263389522d64bc36292faac2`, consistent with the previously checked release manifest MD5. The exact parser is [`scripts/audit_hgsvc3_genotypes.py`](../../scripts/audit_hgsvc3_genotypes.py); generated per-donor counts are in the same scratch directory as `genotype_summary.json`.

The VCF has 176,231 SV records and 65 sample columns. Of these, 64,428 have `SVTYPE=DEL` and absolute `SVLEN` at least 50 bp. For these records, the per-donor summary is:

| GT category | Minimum | Median | Maximum |
|---|---:|---:|---:|
| At least one non-reference allele, with neither allele missing | 9,003 | 9,978 | 12,165 |
| Both alleles missing | 425 | 1,052 | 2,651 |
| One allele missing | 721 | 3,002 | 5,959 |

Example `HG00512`: 9,512 carrier, 50,756 homozygous-reference, 3,015 partially missing, and 1,145 fully missing deletion genotypes. These four counts total 64,428. The script reads `GT` only and rejects unexpected field widths, non-diploid genotypes, and a changed FORMAT schema; two synthetic tests cover category assignment and malformed rows.

These are *record-level* counts, not a precision estimate, confident-region measure, or candidate-label set. A `0|0` genotype at a site already present in the joint VCF cannot label a caller candidate elsewhere as false, and `.|.`/`0|.` show that the release cannot be treated as universally callable. The next scientific gate is a donor-specific callable/confident-region definition aligned to the same assembly/reference, plus representation-aware truth matching and family-safe donor splits. No training or bulk CRAM transfer should treat the numbers above as proof that gate passed.
