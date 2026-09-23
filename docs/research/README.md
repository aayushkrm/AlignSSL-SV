# AlignSSL-SV research restart index

This directory holds prospective work started on 2026-09-22. It complements,
but does not rewrite, the historical results and withdrawals in `PROGRESS.md`.
The files separate verified code findings, experimental plans, external
literature, and independent criticism so that hypotheses cannot silently become
results.

| Document | Role | Current status |
|---|---|---|
| [`RESTART_STATE.md`](RESTART_STATE.md) | Operational state, cluster recovery, and next gates | Living checkpoint |
| [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md) | Prospective experiment design and acceptance criteria | Preliminary; freeze before training |
| [`2026-09-22-depth-diagnostic.md`](2026-09-22-depth-diagnostic.md) | Analytic and real-read evidence for the binned-depth defect and required factorial test | Encoding verified; performance unknown |
| [`2026-09-23-row-semantics.md`](2026-09-23-row-semantics.md) | Read-thinning and mask-aware pooling defect, correction, and ablation | Opt-in correction tested; performance unknown |
| [`2026-09-22-independent-audit.md`](2026-09-22-independent-audit.md) | Independent scientific/code review and resolution ledger | Two engineering findings addressed; one open |
| [`2026-09-22-literature-directions.md`](2026-09-22-literature-directions.md) | Nearby work and falsifiable research directions | Core primary-source ledger complete; BASILISC methods unresolved |
| [`2026-09-23-data-decision.md`](2026-09-23-data-decision.md) | Verified holdings, current GIAB benchmark, and staged new-data plan | 63 public CRAM index matches; callable-region gate pending |
| [`2026-09-23-hgsvc3-genotype-audit.md`](2026-09-23-hgsvc3-genotype-audit.md) | Reproducible per-donor deletion genotype inventory | 64,428 DEL loci ≥50 bp; no confident-negative inference |
| [`2026-09-23-hgsvc3-callability-audit.md`](2026-09-23-hgsvc3-callability-audit.md) | Primary-source search for donor-wide callable regions and negative-label gate | No mask in inspected v1.0 inventories; working archives unresolved |
| [`2026-09-23-hgsvc3-reference-audit.md`](2026-09-23-hgsvc3-reference-audit.md) | HGSVC truth versus IGSR/NYGC CRAM reference metadata comparison | 18 primary-contig M5 mismatches; bulk transfer on hold |
| [`2026-09-23-reference-reconciliation.md`](2026-09-23-reference-reconciliation.md) | Publisher-verified HGSVC no-ALT FASTA versus HGSVC VCF and IGSR dictionary; complete map | 194/194 HGSVC matches; 13,923,221 unequal bases in 152 intervals; bridge unresolved |
| [`2026-09-23-scientific-review-5762726.md`](2026-09-23-scientific-review-5762726.md) | Independent cohort/protocol review of the acquisition milestone | Transfer, callability, fairness, and untouched-test gates remain open |
| [`2026-09-23-scientific-review-reference-map.md`](2026-09-23-scientific-review-reference-map.md) | Sol/high audit of the complete map and its scientific limits | Integrity passed; shared-`N` sequence means difference BED is not a callability mask |
| [`2026-09-23-alternative-cohorts.md`](2026-09-23-alternative-cohorts.md) | Primary-source readiness comparison for GIAB, HGSVC3, HGSVC2, and HPRC | No independent cohort is end-to-end verified |

## Evidence rules

1. Prior test data are development evidence, not fresh confirmation data.
2. A code repair, cleaner representation, or successful job is not a positive
   scientific result.
3. Every learned arm must be compared at matched labels and compute with scratch,
   classical alignment features, and simple depth controls.
4. Threshold-free metrics and per-example predictions are retained; thresholds
   and calibration are selected only from training-side data.
5. Null and failed runs stay in the record. Publication language changes only
   after an independent review of a frozen analysis.
