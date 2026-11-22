# CMRG and v5.0q shared scope

The [fixed protocol](../../docs/research/2026-11-22-cmrg-shared-scope-protocol.md)
was registered before reading the allele rows. The first run showed that
the literal PASS rule excluded all 250 CMRG rows. The corrected rule accepts
the dot used by both benchmark VCFs and preserves [run 01](../cmrg_shared_scope_20261122_run01/).
The corrected run verified and reused all four cached inputs. Both CMRG
files are byte-identical across the NCBI and GIAB S3 paths. The two v5.0q
files match their published MD5. Scoring used 13.052 CPU seconds.

| Eligible CMRG rows | Inside both BEDs and exactly matched | Inside both BEDs with no exact match | Outside at least one BED |
| --- | ---: | ---: | ---: |
| Simple deletion over 50 bp | 84 | 4 | 4 |
| Simple insertion over 50 bp | 114 | 9 | 1 |

Of 250 source CMRG rows, 34 fall at or below the 50 bp cutoff. The eligible
rows make 211 distinct shared-mask edit keys, including 198 exact matches.
The shared autosomal masks cover 11,855,002 of the 11,961,541 CMRG bases
(99.1%). Within this intersection, v5.0q also has 88 eligible deletion
and 126 eligible insertion rows. All 214 use the dot FILTER value.

These counts use exact sequence and position after simple shared-base
trimming and a full raw REF-span mask check. An unmatched row can reflect
an equivalent repeat shift or a more complex representation. The count
of 84 exact deletions is a development denominator before the stricter
proposed repeat, flank, and locus-group requirements. Both releases use
the same donor. No BAM, caller output or model was read in this comparison.

From the repository root, rerun with the retained source files and first
receipt:

```sh
python3 analysis/check_cmrg_shared_scope.py \
  --cache ../runs/cmrg-shared-scope-20261122-run01 \
  --reuse-receipt results/cmrg_shared_scope_20261122_run01/audit.json \
  --out NEW_AUDIT.json
```
