# Shred-seq opportunity: bounded source assessment

As of 2026-10-12. Scope: Shred-seq only. Weller2025 and scCHyMErA2026 are assessed elsewhere.

## Decision

- **Conditional yes** only for a prospective use: can the published features rank outcomes for deletions in not-yet-screened genomic regions, to prioritize follow-up experiments?
- **No** for independent per-deletion fitness. The files link real breakpoints to pre/post-selection detection, but do not separate survival from editing, capture, and sorting.
- Do not frame this as a new essentiality map. The authors already report feature associations and an elastic-net model.

The paper's main claim is descriptive association. A spatially held-out prediction test would add a new use claim; it is not needed to validate the paper's stated claim and is not a generic leakage criticism.

The bioRxiv page says **posted June 2, 2026**. The DOI stem is May 29; a January 1 metadata date is not the posting date. [Paper and posting record](https://www.biorxiv.org/content/10.64898/2026.05.29.728882v1)

## What the public records measure

```text
Cas3 creates deletions
        ↓
Day 3–4 pre-selection sample → breakpoint capture and UMI count
        ↓ culture for ~2–4 weeks; late samples can be GFP− / ploidy sorted
Day 15–18 post-selection sample (one pilot also has day 27)
        ↓
Outcome = observed after selection, not calibrated cell fitness
```

- The study reports 36,257 deletion events across 9,604 Cas3 launchpads. The processed outcome file has 34,515 sample-specific rows and 52 columns. Rows contain barcode, chromosome, start, end, stage, experiment, replicate, ploidy, and `n_umi`. These are real junction-defined deletion coordinates, not guide-pair predictions. [Processed outcomes](https://github.com/pinglaylab/deletion_scanning/blob/main/prc_data/deletions/annotated_deletions.tsv.gz) · [calling code](https://github.com/pinglaylab/deletion_scanning/blob/main/scripts/deletion_filtering_pipeline.R)
- Example: barcode `AAAACGAGATAG`, chr19:13,020,201–13,021,527, L10K pre-selection, replicate 1, haploid; `n_umi=3`. `n_umi` is captured molecule count, not a cell count or fitness value.
- After exact matching on cell line, replicate, ploidy, barcode, and both breakpoints, 428 of 33,667 deletion strata have both pre- and post-selection observations. Thus, most loci are not paired longitudinal breakpoint outcomes.
- All four outcome experiment series use HAP1. Each condition has two replicate populations. Thousands of deletion rows do not create thousands of independent biological units.
- Discovery calls span 100 bp–500 kb. The selection-analysis code filters to deletions over 1 kb and below 500 kb. There are 12,049 noncoding outcome rows. [Paper](https://www.biorxiv.org/content/10.64898/2026.05.29.728882v1.full-text) · [supplement, Table S1](https://www.biorxiv.org/content/biorxiv/early/2026/06/02/2026.05.29.728882/DC5/embed/media-5.xlsx?download=true)

## Outcomes, controls, and confounds

- The model outcome is binary post-selection detection. The paper also fits feature-wise logistic models and a 38-feature elastic-net binomial model (`α=0.5`; 10-fold CV selects `λ.1se`). The paper reports associations; it does not claim prediction for new genomic regions or estimate continuous fitness for each deletion. [Paper methods and results](https://www.biorxiv.org/content/10.64898/2026.05.29.728882v1.full-text)
- There is no event-level “neutral” or “non-deleterious” ground-truth label. “Noncoding” means no protein-coding overlap; it does **not** mean neutral. CRISPR/DepMap dispensability fields are external gene scores joined to overlapping deletions, not measured deletion fitness. [Feature annotation code](https://github.com/pinglaylab/deletion_scanning/blob/main/scripts/feature_annotation.R)
- The direct contrast is early pre-selection versus later cultured/sorted samples. No-crRNA controls validate assay/GFP behavior; they are not a matched neutral-deletion fitness arm in the outcome table. In-silico flipped deletions are repair-context comparisons, not survival controls.
- Cas3/DSB generation, continued Cas3 activity, event-specific editing efficiency, barcode capture, cell recovery, and late GFP/ploidy sorting can all change post-selection detection. The paper itself notes Cas3 persistence and sorting as possible sources of bias. Pre-observation helps control event generation only for the 428 matched strata; it does not remove capture or survivor-sampling bias.

## Three questions, ranked

| Question | Source support | Call |
|---|---|---|
| Can noncoding chromatin/constraint features rank post-selection detection in not-yet-screened genomic regions, beyond length, experiment, and ploidy? | 12,049 noncoding rows; four HAP1 series; existing annotations and published baseline. Potential use: prioritize regions for follow-up before screening them. This is a new prediction claim, not the paper's descriptive claim. | **Best cheap test, if that use matters.** |
| Which exact deletions persist from pre- to post-selection, and does length/context predict persistence? | 428 exact breakpoint+barcode strata are observed at both stages. This is direct, but sparse and still based on capture/detection. | **Small descriptive analysis only.** Do not call persistence independent fitness. |
| Does junction repair class or resection predict survival after controlling for deletion geometry? | `breakends.tsv` has 7,112 repair records; 166 unique exact keys match outcome records. The repair export collapses replicate/timepoint labels. | **Reject as a powered outcome question.** The matched, stage-specific units are too few and not cleanly replicated. [Repair table](https://github.com/pinglaylab/deletion_scanning/blob/main/prc_data/breakends.tsv) · [processing code](https://github.com/pinglaylab/deletion_scanning/blob/main/scripts/breakend_processing.R) |

## Smallest useful falsifier

Rebuild the published binary outcome from the 34,515-row table. Compare the published feature model with a simple baseline using deletion length, experiment, and ploidy. First inspect launchpad coordinates and interval overlap. Hold out spatial blocks with a guard band; keep overlapping deletions and nearby launchpads in one block. A barcode-only split is not enough. Spatial independence has **not** been checked, so do not call the current rows independent genomic loci. Report held-out log loss and calibration for the 12,049 noncoding rows. Use label permutation as the negative control. If spatially held-out value is absent, stop. If it is present, it supports prioritization for follow-up, not fitness independent of editing or capture.

## Execution / source audit

- The processed outcome table and repair table were read in the prior turn into in-memory Node arrays. No local source copy was written. No local cache path exists. No raw FASTQ/BAM/CRAM or sequencing deposit was downloaded. GitHub links below use `main`; no commit SHA was captured.
- Outcome source: [raw `annotated_deletions.tsv.gz`](https://raw.githubusercontent.com/pinglaylab/deletion_scanning/main/prc_data/deletions/annotated_deletions.tsv.gz). The prior fetch reported 3,514,807 bytes. A separate GitHub metadata read reported 3,630,906 bytes; this mismatch is unresolved. The compressed buffer and its SHA-256 were not retained. The decoded table in memory had 34,515 rows plus header, zero blank rows, and final `deletion_id=34515`; parsing reached decoded EOF. The archive's gzip integrity is not independently verified. Canonical LF-joined decoded text is 12,952,503 bytes, SHA-256 `c8311dd838f4095fe6b986abe2703646cf6c8dda772a1b791178f450cd6727a3` (not a hash of the gzip file).
- Exact pre/post count logic: these are counts computed from the in-memory table, not paper-reported metrics. Group rows by `cell_line, replicate, ploidy, barcode, chr, start, end, strand`; record the set of `selection` values per key. This gives 33,667 strata: 17,315 pre-only, 15,924 post-only, 428 both. Required key/stage fields had no blank values. Same-stage repeats collapse to presence; `n_umi` is not summed, and `day` is not part of this matching key.
- Repair source: [raw `breakends.tsv`](https://raw.githubusercontent.com/pinglaylab/deletion_scanning/main/prc_data/breakends.tsv). The complete in-memory UTF-8 text is 836,430 bytes, 7,112 records plus header, ends with a newline; SHA-256 `ca1ff90d2f2808cf39a59086d60d58e857db401345b0dd97e44507712b11c2da`. No join-key fields were blank. Exact join used `(barcode, chr_2, start, end, strand)` against `(barcode, chr, start, end, strand)`: 175 rows, 166 unique keys. There are 78 repeated first-strand keys in the full repair table; repeated rows were not treated as independent. Using `strand_2` instead gives 101 rows, 100 unique keys. The orientation mapping needs validation; do not treat these joins as independent survival observations.
- Code read: relevant portions of [`deletion_filtering_pipeline.R`](https://github.com/pinglaylab/deletion_scanning/blob/main/scripts/deletion_filtering_pipeline.R), [`feature_annotation.R`](https://github.com/pinglaylab/deletion_scanning/blob/main/scripts/feature_annotation.R), and [`breakend_processing.R`](https://github.com/pinglaylab/deletion_scanning/blob/main/scripts/breakend_processing.R). Their byte counts/hashes were not retained. **The model's CV implementation code was not read.** The `α`, fold, and `λ.1se` details above come from paper Methods. The supplementary workbook was used for Table S1 metadata; no local path, byte count, or hash was retained.

## Scope status

This does not meet the broader research goal. HG002 remains at the scientific stop before S2. No SSL, DeepSV, or diagnosis requirement is introduced. Requested model: Luna/max; this is not an independent attestation.
