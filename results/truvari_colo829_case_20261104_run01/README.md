# COLO829 site-only Truvari case diagnostic

The [protocol and result](../../docs/research/2026-11-04-truvari-colo829-case-protocol.md)
explain the exploratory comparison and all claim limits. This packet contains
only small processed callsets and native reports; no genomic reads or full
source input VCF are committed. The 66 compared BND records come from one
public COLO829 file, not independent truth.

`input-manifest.json` pins the compressed public input, records the case-only
mapping and byte-level comparison, and hashes the six projected inputs retained
outside Git. All output reports, parameters, compressed native result VCFs,
logs and the [receipt](receipt.json) are preserved. The sample-free inputs
make the native genotype summary fields meaningless, even in self-controls.
See the note for the `skip_gt` and `None`/`None` evidence.

To reproduce, obtain the [exact original source](https://ont-open-data.s3.amazonaws.com/colo829_2024.03/wf_somatic_variation/sup/COLO829.wf-somatic-sv.vcf.gz),
use Python 3.12 with `truvari==5.4.0` and the dependencies listed in the
receipt, and run from the repository root with new output and workspace paths:

```sh
python -m analysis.run_truvari_colo829_case \
  --source-gzip /path/to/caller.vcf.gz \
  --workspace /tmp/colo829-truvari-inputs-new \
  --output /tmp/colo829-truvari-result-new
```

The runner refuses a different source SHA256, missing or non-unique aliases,
an unexpected BND count, and non-case changes between the two projected
inputs. It retains every BND FILTER value and uses four parallel native runs.
