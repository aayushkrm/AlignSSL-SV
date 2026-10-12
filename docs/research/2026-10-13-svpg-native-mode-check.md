# SVPG native-mode check: the graph-present HG008 deletion

Date: 2026-10-13. Scope: source and saved archive metadata only. No archive was fetched again, no VCF body was read, and no caller, install, job, or genomic-data acquisition was run.

## Finding

SVPG's native BAM-guided `call` mode is a valid *candidate control* for a deletion already represented in the pangenome. The source starts from BAM CIGAR deletion signals, then realigns supporting reads to the graph. If graph-derived refinement does not match, the parser can retain a deletion at the original BAM coordinates. This makes graph presence alone an insufficient reason to predict that guided mode will discard the event. It does **not** establish that SVPG recovers this HG008 event: the paper did not test guided mode on HG008.

The reported HG008 run used pangenome-based `graph-call` on GAF alignments. The paper reports that four of five missed INDELs were already represented in the graph. It highlights a 419-bp deletion at chr7:19196736, says it was represented in the graph, and attributes its omission to that representation. The paper calls it previously reported as cancer-specific. This is a published case claim, not verification here of genotype, copy state, or tumor purity. [Nature Methods paper](https://www.nature.com/articles/s41592-026-03219-2)

```text
same HiFi tumor and matched-control read sets
             |
       +-----+------+
       |            |
 linear BAM      graph GAF
       |            |
 svpg call      svpg graph-call
 CIGAR DELs     graph gaps/splits
 graph refine   novel-signal route
       |            |
 test whether guided mode retains the graph-present deletion
```

## Inputs and mode boundary

The paper says the HG008 cancer-cell-line and matched-control HiFi data were aligned with minigraph to the GRCh38-90c.r518 pangenome. SVPG called each GAF independently; a custom subtraction then labeled tumor calls cancer-specific when no same event was found in normal within 1,000 bp. This was not a joint tumor-normal SVPG call. The paper suggests these graph-present events may be somatic changes overlapping common germline SVs. The highlighted deletion was missed in the graph-based mode. [Paper methods and results](https://www.nature.com/articles/s41592-026-03219-2)

The native guided command requires a coordinate-sorted, indexed linear-reference BAM, the matching reference FASTA, and the pangenome GFA. The GAF used in the paper is **not** a `--bam` input. To test the guided route on the same read sets, both tumor and matched control need suitable BAMs against the graph's linear reference, plus the exact GRCh38-90c.r518 GFA and matching FASTA. The saved callset archive has none of these alignments.

```bash
# Template only: replace paths and K_T/K_N with qualified, frozen values.
svpg call --working_dir tumor.guided --bam TUMOR.sorted.bam \
  --ref GRCh38.fa --gfa GRCh38-90c.r518.gfa --read hifi --min_support K_T
svpg call --working_dir normal.guided --bam NORMAL.sorted.bam \
  --ref GRCh38.fa --gfa GRCh38-90c.r518.gfa --read hifi --min_support K_N
```

These are two per-sample calls, not a paired caller. Freeze `K_T`, `K_N`, map-quality, size, and contig settings before comparing modes. Do not take the README's graph-mode example thresholds as the paper's exact HG008 settings. The current README lists `call --bam ... --ref ... --gfa ... --read ...`; it lists `graph-call --gaf ...` as the separate graph mode. [SVPG README](https://github.com/coopsor/SVPG/blob/master/README.md)

## Is a somatic wrapper already present?

The repository includes a VCF subtraction helper, `scripts/vcf_specfic.py` (spelled `specfic`). The README example spells the path `vcf_specific.py`, so the documented command does not match the tagged script filename. The helper compares chromosome, a broad SV-type label, and POS within 1,000 bp. It does not compare sequence, end/length, genotype, phase, or copy state. It is a post-call subtraction script, not joint tumor-normal inference. It can combine per-sample VCFs, but it is not adequate evidence by itself that the exact somatic allele was recovered. [Tagged helper source](https://github.com/coopsor/SVPG/blob/v1.4.1/scripts/vcf_specfic.py)

## What the source supports, and what remains open

- In v1.4.1, `SVCollect.py` creates DEL signatures from BAM CIGAR indels. `main.py` sends DEL and INS signatures through graph realignment. `SVPan.py` refines them from graph alignments and can fall back to the original BAM deletion coordinates if no suitable graph signature is found. [SVCollect.py](https://github.com/coopsor/SVPG/blob/v1.4.1/src/svpg/SVCollect.py), [SVPan.py](https://github.com/coopsor/SVPG/blob/v1.4.1/src/svpg/SVPan.py), [v1.4.1 main.py](https://github.com/coopsor/SVPG/blob/v1.4.1/src/svpg/main.py)
- Therefore, the cheapest *additional* native control is two `svpg call` runs, one per existing tumor/normal BAM, followed by exact allele-aware comparison. This control is eligible only if those BAMs and the matching graph/reference are already available. They are absent from the saved callset archive metadata; acquisition is outside this scope. Runtime and storage for the two HG008 calls, plus any needed BAM preparation, are unknown. The README's roughly four-minute HiFi example is for HG002 graph realignment and does not budget this paired HG008 control.
- Keep the strong comparisons. The saved archive inventory lists SVPG, Severus, Nanomonsv, and miniSV HG008 VCFs, filtered and unfiltered. Their presence is not proof that any one recovered this allele. Main's callset review should qualify each VCF before drawing that conclusion; a new comparison must retain paired Severus/Nanomonsv and the graph-based miniSV baseline.
- Do not generalize the deletion route to inversions. The README lists INV among SV types, but both the tagged and current `main.py` paths lack a dedicated inversion output list in the final VCF-writing call. Treat native SVPG INV support as unresolved until that interface mismatch is resolved. [Current master main.py](https://github.com/coopsor/SVPG/blob/master/src/svpg/main.py), [v1.4.1 README](https://github.com/coopsor/SVPG/blob/v1.4.1/README.md)

## Release and archive qualification

The paper's Methods name SVPG v1.4.1 in its caller-benchmarking section; the supplementary caller-command table labels SVPG v1.3. The version and command record is therefore inconsistent, and the materials checked do not pin the executable for these archived HG008 VCFs. Pin the official [v1.4.1 tag](https://github.com/coopsor/SVPG/releases/tag/v1.4.1) for a new control, but do not attribute the archived HG008 VCF to that exact executable without its header or run provenance. The current master README and inspected `main.py` retain separate `call` and `graph-call` interfaces, with no relevant change in the inspected mode path; this check did not audit every current source file.

The reused [archive inventory](../../results/data_audits/svpg_2026/2026-10-04/callsets_inventory.json) lists `SV_callsets/somatic_SV/hg008/svpg.vcf` and `svpg.filter.vcf`, plus the Severus, Nanomonsv, and miniSV VCFs. The saved [header audit](../../results/data_audits/svpg_2026/2026-10-04/full_hifi_headers.json) contains headers for six HG002 callsets only. It parsed zero biological records, extracted no archive members, and scored no outputs. The inventory exposes no HG008 BAM, GAF, or CRAM. Thus it confirms output-file availability and archive identity, not the HG008 VCF's exact software version, graph/reference identity, sample genotype, or call-level recovery.

**Disposition:** retain BAM-guided SVPG as a cheap, strong, source-supported deletion control *if the matching BAMs and graph already exist*. From the archived outputs alone it is not runnable or costed. A guided-mode recovery would close this case's unmet-caller premise; a miss would remain case-specific until read-level support and the strong paired/graph baselines identify a mechanism. No publication claim follows from this source check alone.

## Primary and exact source files checked

- [Nature Methods article, DOI 10.1038/s41592-026-03219-2](https://doi.org/10.1038/s41592-026-03219-2); [Supplementary Information](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41592-026-03219-2/MediaObjects/41592_2026_3219_MOESM1_ESM.pdf).
- SVPG [v1.4.1 README](https://github.com/coopsor/SVPG/blob/v1.4.1/README.md), [v1.4.1 `main.py`](https://github.com/coopsor/SVPG/blob/v1.4.1/src/svpg/main.py), [`SVCollect.py`](https://github.com/coopsor/SVPG/blob/v1.4.1/src/svpg/SVCollect.py), [`SVPan.py`](https://github.com/coopsor/SVPG/blob/v1.4.1/src/svpg/SVPan.py), [`SVCluster.py`](https://github.com/coopsor/SVPG/blob/v1.4.1/src/svpg/SVCluster.py), and [`scripts/vcf_specfic.py`](https://github.com/coopsor/SVPG/blob/v1.4.1/scripts/vcf_specfic.py). Current-upstream comparison was limited to the [master README](https://github.com/coopsor/SVPG/blob/master/README.md) and [`main.py`](https://github.com/coopsor/SVPG/blob/master/src/svpg/main.py).
- Saved archive acquisition/header scope: [execution ledger](../../results/data_audits/svpg_2026/2026-10-04/EXECUTION.md), [member inventory](../../results/data_audits/svpg_2026/2026-10-04/callsets_inventory.json), and [header audit](../../results/data_audits/svpg_2026/2026-10-04/full_hifi_headers.json).
