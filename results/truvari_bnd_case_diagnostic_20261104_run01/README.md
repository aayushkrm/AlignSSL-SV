# Synthetic Truvari BND case diagnostic

The [protocol and result note](../../docs/research/2026-11-04-truvari-bnd-case-diagnostic.md)
describes this one invented adjacency and its limits. `header_case.vcf` and
`upper_case.vcf` differ only in the two ALT mate-contig tokens. Their BGZF
copies and indices are derived from those artificial inputs. The four native
Truvari result directories, complete stdout/stderr logs, parameter files,
comparison summaries and receipt are preserved. All 63 file hashes listed
in the original receipt were verified after the run.

Recreate in a new output directory with Python 3.12, `truvari==5.4.0`, and
the dependency versions recorded in [receipt.json](receipt.json):

```sh
python analysis/run_truvari_bnd_case_diagnostic.py \
  --output /tmp/truvari-bnd-case-new
```

The runner uses four parallel native comparisons, one thread per BLAS/OpenMP
environment, and creates BGZF indices using pysam. It records hashes of the
installed Truvari match code. The separately coded
[byte-difference audit](../truvari_bnd_case_diagnostic_20261104_audit/byte-diff.json)
checks the two plain input files without using the fixture generator.
