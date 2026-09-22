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
