# Sniffles2 regional-input and mode check

Date: 2026-10-10  
Scope: source-level viability only. No BAM/header/read access, read download, tool install, caller run, job, or tracking-file edit.

## Finding

Sniffles2 v2.8.1 supports this input shape at the code level: it opens a coordinate-sorted, indexed BAM with `require_index=True`, then builds its read table from the requested region list. A full set of whole-genome `@SQ` records does not itself supply coverage observations. Use the documented `--regions target.bed` in both calls, with the same region BED and the same regional BAM/index. The read-table builder then receives the target region list.

The local BAM still needs the exact contig name used by the BED. Source review does not validate the actual BAM/index or prove that the target alignments are present.

The call-task code sets `coverage_average_total` by calling `postprocessing.coverage(candidates, lead_provider)`, then passes it to support and post-annotation QC. The call site passes candidate/read-provider data; it does not pass `@SQ` lengths as a coverage input. At first pass, `postprocessing.py` was outside the four-file limit, so the helper formula and numeric aggregate were unverified. The addendum below records the authorized fifth-file review and its remaining limit: the `LeadProvider` coverage-array shape was not inspected.

## What changes between modes

The control suggestions in this first-pass table are superseded for the primary comparison by the addendum at the end. Use each mode's native defaults there.

| Behavior | Germline default | `--mosaic` default | Paired-run control |
|---|---|---|---|
| Minimum supporting reads | `--minsupport` parser default is `3` | Same configured value; mosaic has a separate mosaic-read filter | `3` is already the native default; do not select `auto` for the primary regional-input comparison |
| Auto support | Only if `--minsupport auto` is selected; multiplier default is `0.1` | No separate multiplier is assigned in the inspected config code | Not the native default; see addendum for the regional-coverage limitation |
| Candidate merging | `--cluster-merge-len` is `0.22` | Config changes the default `0.22` to `0.27` | Retain both native defaults in the primary comparison. A shared `0.23` is optional only for a later clustering-mechanism sensitivity; passing `0.22` does not hold the mosaic value |
| Coverage-based support QC | `qc_sv_support` runs for QC-passing calls | That call is skipped | This is an intentional mode difference. Equal `--minsupport` does not make the final filters identical |
| Mosaic AF gate | None | Default VAF range is `0.05` to `0.218` | Pin those two values explicitly in the mosaic invocation; keep the gate as part of the mosaic treatment |
| Genotype z-score filter | Can set `GT` when the z-score is below the configured minimum | The genotyper disables that z-score filter in mosaic mode | Record FILTER and genotype fields separately; mode outputs are not a one-threshold toggle |

For insertions, the genotyper rescales support before it computes VAF. It records the original support as `SUPPORT_UNSCALED`; VAF is then `support / coverage`, where coverage is the mean of available nonzero read-spanning coverage values (the insertion genotyper uses center coverage). Do not treat the emitted VAF as an unadjusted count of alternate reads divided by all reads.

So default outputs can differ for reasons beyond AF. The fixed `--minsupport 3` avoids a coverage-adaptive minimum. A shared `--cluster-merge-len 0.23` avoids the mode-specific default rewrite. The mosaic AF gate, germline support QC, mosaic z-score behavior, and other mode-specific filters remain part of the caller comparison.

## Runtime and reference

The v2.8.1 README states Python `3.10.15`, `pysam >=0.21.0`, `edlib >=1.3.9`, `psutil >=5.9.4`, `numpy >=2.2.0`, and `pyspoa >=0.2.1`. It describes BAM/CRAM input as long-read alignments and requires coordinate sorting and an index. These are upstream requirements; no local runtime was checked.

A whole CHM13 FASTA is not required for BAM calling or insertion calls. `--reference` is optional in the CLI; the README says it is needed to output deletion sequences. If supplied, the task code also opens it for unresolved-reference-region handling. For BAM input, omit it in both runs unless that reference-based annotation is required. (CRAM input has a separate reference-decoding path.)

## Initial paired follow-up (superseded for the primary comparison)

After a v2.8.1 runtime and the regional BAM/index are already available, run the same input and BED in each arm. Use the same one-locus BED selected by the main analysis.

```sh
sniffles --input NA12878.CHM13.regional.bam --regions target.bed \
  --vcf germline.vcf --threads 1 --minsupport 3 --minsvlen '~50' \
  --mapq 20 --qc-coverage 1 --cluster-merge-len 0.23

sniffles --input NA12878.CHM13.regional.bam --regions target.bed \
  --vcf mosaic.vcf --threads 1 --mosaic --minsupport 3 --minsvlen '~50' \
  --mapq 20 --qc-coverage 1 --cluster-merge-len 0.23 \
  --mosaic-af-min 0.05 --mosaic-af-max 0.218
```

These commands are a follow-up template, not a run performed in this task. Check the caller version, indexed-input open, candidate record, `SUPPORT_UNSCALED`, VAF, genotype, and FILTER in both outputs. The two modes still apply different QC logic by design.

## Source log

One release record was checked: [GitHub latest-release API](https://api.github.com/repos/fritzsedlazeck/Sniffles/releases/latest) reports v2.8.1, published 2026-09-10. The tag ref resolves to commit **`684c7cb2f2f1d0a6dfe794617c661b1b7018c8c3`**. Firecrawl retrieval succeeded for the version-pinned raw files below. A GitHub Contents API directory listing was used only to confirm source paths.

| Pinned file | Sections used |
|---|---|
| [README.md](https://github.com/fritzsedlazeck/Sniffles/blob/684c7cb2f2f1d0a6dfe794617c661b1b7018c8c3/README.md) | L24–50 (runtime, input, reference); L61–75 (mosaic mode and input notes) |
| [config.py](https://github.com/fritzsedlazeck/Sniffles/blob/684c7cb2f2f1d0a6dfe794617c661b1b7018c8c3/src/sniffles/config.py) | L176–186 (indexed input and regions); L219–244 (support and filters); L252–263 (merge threshold); L354–363 (mosaic AF); L521–547 (support defaults); L598–610 (mosaic override) |
| [parallel.py](https://github.com/fritzsedlazeck/Sniffles/blob/684c7cb2f2f1d0a6dfe794617c661b1b7018c8c3/src/sniffles/parallel.py) | L91–103 (indexed open and region-scoped read table); L127–148 (aggregate coverage and QC calls); L266–273 (optional reference handling) |
| [genotyping.py](https://github.com/fritzsedlazeck/Sniffles/blob/684c7cb2f2f1d0a6dfe794617c661b1b7018c8c3/src/sniffles/genotyping.py) | L91–191 (coverage, AF, genotype and z-score filter); L194–212 (insertion support rescaling) |

## Addendum: aggregate coverage and native defaults

This follow-up adds exactly one pinned source file, the fifth source file in total. It supersedes the earlier common-override command as the primary comparison. Preserve each mode's native policy defaults in the primary pair. Do not set `--cluster-merge-len 0.23` there. The earlier suggested `--minsupport 3` equals Sniffles' actual parser default, but the primary commands below leave it implicit.

### Exact aggregate and support behavior

`coverage()` annotates each call from `lead_provider.coverage` at start, center, end, upstream, and downstream bins. For an insertion, it samples the breakpoint neighborhood. It returns `lead_provider.coverage.mean()`; its docstring calls this the average coverage across the contig. `parallel.py` passes that result to support QC and post-annotation QC.

`qc_sv_support()` selects one of two branches:

- With the native `minsupport` value `3`, `qc_support_const()` checks `svcall.support >= config.minsupport`. The aggregate coverage is not used in this branch.
- Only when `--minsupport auto` is selected does `qc_support_auto()` use aggregate coverage. It calculates regional coverage from nonzero upstream/downstream bins, falling back to nonzero start/center/end bins and then to global coverage if no local value is available. It blends 75% regional and 25% global coverage, then uses `round(1.5 + 0.1 * blended_coverage)` as the minimum support. Support is rescaled before this check.

Therefore the native default germline support floor is fixed at three reads. A possible region-induced bias in the contig-wide mean cannot alter that floor. Do not switch to `auto` for this primary regional-BAM comparison. The code reviewed here does not establish whether `lead_provider.coverage` spans the full contig or only processed regions; if it spans the full contig and has zeroes outside the selected interval, the mean would be diluted. The exact array construction is in another module and was not inspected under this follow-up's one-file limit. No numeric genome-wide mean is claimed.

The mosaic path applies different native policy. In `qc_sv_post_annotate()`, calls with VAF at or below `mosaic_af_max` are classified as mosaic. Germline mode filters such calls with `MOSAIC_VAF` (except the special DUP path). Mosaic mode applies its min/max VAF gate and a mosaic-specific read-support rule; that rule can lower its support minimum by one for precise calls that meet the stated dispersion checks. For a call classified as non-mosaic while `--mosaic` is on, the code may invoke `qc_sv_support()` before the default mosaic policy excludes it as `NOT_MOSAIC_VAF`. These are intended mode differences. For a call in the mosaic AF range, global auto coverage is not the support threshold.

For this primary test, use the native defaults and the same target BED, BAM/index, and reference choice in both arms:

```sh
sniffles --input NA12878.CHM13.regional.bam --regions target.bed --vcf germline.vcf
sniffles --input NA12878.CHM13.regional.bam --regions target.bed --vcf mosaic.vcf --mosaic
```

The config does change the default merge fraction from `0.22` in germline mode to `0.27` in mosaic mode. Keep that difference in the native-policy result. If a later mechanism check needs to isolate clustering, one shared `--cluster-merge-len 0.23` can be used as a single optional sensitivity comparison; it is not needed to mitigate the aggregate-coverage concern. Do not expand this into a parameter grid.

### Input metadata supplied by main

Main reports the BAM header has chr3 length `201105948`, all `@RG` `SM` values are `NA12878`, and the `@PG` provenance names `pbmm2` with `human_chm13v2.0_maskedY_rCRS.fasta`. Main parsed only the text header from a finite 65,536-byte prefix; no alignment record was parsed. The retained prefix can contain bytes after the header. It is not evidence for or against reads or coverage at the target locus. I did not inspect the BAM or acquire reads. (Main clarified the distinction after the completed handoff.)

### Follow-up source log

The new source is [postprocessing.py](https://github.com/fritzsedlazeck/Sniffles/blob/684c7cb2f2f1d0a6dfe794617c661b1b7018c8c3/src/sniffles/postprocessing.py), pinned to the same commit. Sections used: L74–136 (`coverage()`); L139–165 (`qc_sv_support()`); L180–203 (`qc_support_auto()` and `qc_support_const()`); L450–606 (`qc_sv_post_annotate()`, including mosaic VAF and support filters). No other release metadata or source files were checked.
