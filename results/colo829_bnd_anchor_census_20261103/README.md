# COLO829 BND anchor census

This exploratory census reads **all** BND records in two published COLO829
callsets. The [result](census.json) retains every BND record, exact ALT text,
source FILTER, reciprocal-pair status and missing/unsupported states. An ALT
anchor differing from REF can encode a real base replacement; it is not, by
itself, an error or evidence that a variant is absent.

| Input | Public source | SHA256 |
|---|---|---|
| `caller.vcf.gz` | [ONT COLO829 caller VCF](https://ont-open-data.s3.amazonaws.com/colo829_2024.03/wf_somatic_variation/sup/COLO829.wf-somatic-sv.vcf.gz) | `ae2d7b02fea3dda159e602c6124ef1911324efb692682ad9977eac697d6e5042` |
| `truth.vcf` | [2022 truth-set archive, hg38-lifted VCF](https://zenodo.org/records/4716169/files/truthset_somaticSVs_COLO829_hg38lifted.vcf?download=1) | `a8f38454367cf8837a7dba1d29c9bc338a8e62cadfee6d2489931f8105f0dcdc` |

The original full files are retained outside Git in the local project run
directory `runs/colo829-der3-20261103/`. They are small processed callsets,
not raw reads. Their source links and byte-level pins make a fresh retrieval
checkable. The project also retains the tutorial contig, alignment and BED
there; those are described separately in the
[source scout](../../docs/research/2026-11-03-complex-path-real-evidence.md).

## Reproduce

Download the two unchanged files under the names in the table. Then run from
the repository root with Python 3. The new output path must not exist:

```sh
python -m analysis.colo829_bnd_anchor_census \
  --input-dir /path/to/sources --output /tmp/colo829-census.json
```

The parser checks the two SHA256s before and after reading. It recognizes
single-base A/C/G/T REF alleles and the four standard reciprocal BND forms.
Other forms remain `UNKNOWN`. A reciprocal pair requires mutually compatible
coordinates and orientations, honors MATEID where provided, and is accepted
only when unique in both directions. The truth VCF does not supply MATEID, so
its pair associations are coordinate-and-orientation inferences. `chr` prefix
and letter case are normalized for those joins only; the original text is
retained. No caller phase or biological truth is inferred from a pair.

The [analysis note](../../docs/research/2026-11-03-colo829-bnd-anchor-census.md)
records record-level denominators, FILTER subsets and interpretation limits.
The [focused controls](../../tests/test_colo829_bnd_anchor_census.py) exercise
the four orientations, real substitutions, missing/ambiguous mates, unsupported
ALT forms and the full-file denominator.
