# scCHyMErA-Seq: exact-exon-deletion evidence

Checked 2026-10-12. Scope: the paper, supplement legends, and public repository manifests. No raw RNA/DNA, Git checkout, or model was acquired.

## Finding

**No exact DNA exon-deletion allele linked to each cell’s expression is evidenced in the public materials I could inspect.** The reported linkage is guide capture to poly-A RNA and cell state. That is a useful guide-assignment baseline, but it does not establish which DNA alleles each cell carries.

```text
intended guide pair → captured guide call → RNA / cell-state outcome
                              ╳
             no reported per-cell DNA junction or allele/copy call
```

The paper profiles 224 alternative exons in 161 genes. Each exon has three guide pairs. Supplementary Data 2 lists target genes/exons, guide sequences, *predicted* cut sites, on/off-target scores, and library oligos. It is a design table; I found no observed junction sequence, per-cell DNA amplicon call, biallelic state, or copy-number state. HAP1 cells were diploidized before the screen, so guide identity cannot be treated as a haploid genotype.

## Smallest usable public outcome table

| Layer | Public item | What it supports | Boundary |
|---|---|---|---|
| Intended edit | Supplementary Data 2 | Target exon, guide pair, predicted cut sites and design scores | Intended cuts, not observed deletion alleles |
| Guide assignment | Zenodo `feature_reference.csv` (332.5 KB) + `paired_hgRNA_calls_per_cell.csv.gz` (3.3 MB) | Per-cell guide/feature calls | Guide capture only |
| Strongest per-cell guide check | Zenodo `protospacer_calls_per_cell.csv.gz` (10.3 MB) | Per-cell protospacer calls | Still no DNA genotype |
| Expression outcome | GEO GSE293013; Supplementary Data 4 | Article deposits screening data; Data 4 gives exon-level pseudobulk DESeq2 results vs intergenic controls | GEO file inventory was blocked here, so a processed per-cell expression matrix and barcode overlap remain unverified |
| Cell state | Supplementary Data 6 | Cell-cycle fractions by perturbation | The analysis treats the three hgRNAs as replicates; not allele-level or biological-replicate genotype data |

For a small, verifiable target-level benchmark, join Data 2 to Data 4 and Data 6. For a per-cell *guide-assigned* benchmark, add the two Zenodo tables above and a processed expression matrix only if GSE293013 metadata confirms one with matching cell barcodes. The Zenodo manifest also lists Mixscape observation tables, but no DNA-variant table. The article says supporting data are available from the authors on request. Its own detection baseline is guide capture: custom amplification raises Cas12a capture to about 90% and dual-guide detection across all profiled cells from 47% to 72%. These are guide-detection rates, not deletion-genotype accuracy.

## What is and is not validated

- **Observed edit vs intended guides:** exon skipping is checked by RT-PCR for selected targets. Other checks include CD46 flow cytometry and expression validation. These support editing/function for selected conditions; they do not sequence each genomic deletion junction or connect it to a single-cell barcode.
- **NRF1 exon 7:** a strong independent functional case. The screen reports 373 differentially expressed genes. Separate experiments use NRF1 full-length/ΔE7 rescue, three base-editor constructs that induce exon-7 skipping, RNA-seq, qRT-PCR, ChIP-seq and ChIP-qPCR. These validate NRF1’s transcriptional role and exon skipping, not the exact CHyMErA DNA allele in each screen cell. GEO lists NRF1 RNA-seq accessions GSE292986/GSE292988 and ChIP-seq GSE292984.
- **Splicing and NMD:** targeted RT-PCR/RNA-seq readouts exist for selected examples. The paper discusses SMG5 exon 5 as a possible NMD-related mechanism, but I found no direct NMD assay or systematic NMD readout.
- **Replicates and selection:** the screen uses three guide pairs per exon and eight 10x GEM replicates. The methods do not establish that these are independent biological screen replicates. HAP1 cells undergo puromycin selection for about 40 hours; scRNA-seq follows at T1. The cell-cycle outcome is therefore measured after selection. This design does not resolve selection effects by observed allele.
- **Off-targets:** guides were selected for high prior on-target activity, minimal *predicted* off-target activity, and deletions under 2 kb. Supplementary Data 2 reports design scores. I found no empirical genome-wide off-target or per-cell allele validation for this screen.

## Open questions with distinct value

1. For a captured guide pair, what fraction of cells has the intended junction, an alternative repair, no edit, or a mixed/biallelic edit? Does that fraction vary by target and guide pair?
2. Does the *observed allele and dosage* predict exon inclusion, transcript abundance/NMD, and downstream expression better than guide identity? NRF1 exon 7 is a useful positive control, but its independent assays do not answer this for the screen cells.
3. Do allele-conditioned effects persist across biological replicates and before/after selection, or do guide activity, cell-cycle state, and selection explain the signal? The current screen reports guide-level perturbations and selected validations.

The useful opportunity is a genotype-to-cell-readout benchmark. A generic structural-variant effect predictor is already covered by the cited Swap-seq work; this dataset adds no exact-allele labels for that task.

## Decision and cheap falsifier

**Bounded no-go for an exact-allele benchmark from the inspected release manifests.** One cheap check could reverse it: inspect only the GSE293013 processed-file metadata for a barcode-linked genomic amplicon/variant table. Reopen this opportunity only if that table exists. Otherwise, use scCHyMErA-Seq as a guide-assigned expression/cell-state baseline, not as validated exact-deletion ground truth. GEO pages were inaccessible during this check; their file inventory is unverified, not evidence that no such file exists.

## Sources

- [Nature Communications article and supplementary links](https://www.nature.com/articles/s41467-026-68774-w) · [supplementary data legends (PDF)](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68774-w/MediaObjects/41467_2026_68774_MOESM2_ESM.pdf)
- [Zenodo scCHyMErA-Seq 0.1.1 manifest](https://zenodo.org/records/18186607) · [Mendeley source data](https://doi.org/10.17632/rxfzrptr2d.1)
- [GSE293013 screen](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE293013) · NRF1 [RNA-seq GSE292986](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE292986), [RNA-seq GSE292988](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE292988), [ChIP-seq GSE292984](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE292984)
