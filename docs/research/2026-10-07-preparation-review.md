# Independent review: first diagnostic preparation

**Historical review, superseded by the October 7 stop decision.** Later truth
preparation completed, but the real metadata gate failed; no validated
denominator or screen followed. The next-step list below is not a current
launch plan. See [validation and stop review](2026-10-07-validation-gates.md).

Date: October 7, 2026. Reviewer: Dirac, Sol6.1/high requested; actual runtime
configuration not independently attested. Read-only review, no new source
body, truth/BED read or cluster job. Main accepts the findings below.

The reviewer verified the standard-01 reports: all six files passed local
compatibility/count/hash checks without repair or filtering. Main's full
validation completed 642 passed, 29 skipped. Checkpoint `b1f1b32` is pushed;
remote SHA matches. These are source/software results, not biological gains.

## Minimum next steps, not an open-ended setup phase

1. Inspect the current truth **header only** under a separate pinned gate.
   Reverify compressed source SHA and file stability, stop at `#CHROM`, record
   exact sample/contig/GT/phase declarations and raw header SHA. Reserve at most
   one MiB decoded traffic including read-ahead. No body-record parsing,
   BED read, eligibility denominator or scoring. Reviewer considers this
   scope acceptable; exact code/protocol/reservation approval is still required.
2. Freeze the existing truth/reference and caller-preparation recipe. No
   matching is included in this next approval scope.
3. Review the exact screen command and identity/count assertions, then run the
   fixed six-caller diagnostic. POA/phase reconstruction/refinement stay closed
   and need not delay the first event-compatibility screen.

## Concrete preparation corrections

| Control | Required correction/check |
|---|---|
| Truth boundary eligibility | The existing truth parser rejects POS=0 before classification. Count legal telomeric sentinels as ineligible boundary records, not malformed data or repaired coordinates. This does not enlarge the buffered-autosomal truth population. |
| Reference/type/size | Freeze exact sample and contig mapping against pinned FASTA/BEDs. Verify eligible truth REF and Truvari size/type interpretation. Source+original-ordinal identities, linear trimming and joint bootstrap are already explicit. |
| Caller views | Assign parent ordinals before filtering/decomposition; preserve ALT index, duplicate multiplicity and source GT. Freeze dot-mode splitting without reference imputation. Use standard sorting; assert coordinate order and identity multiplicity without an unproven general ordinal tie-order claim. |
| Shared truth denominator | Global `--passonly --no-ref a` can touch the base/truth side too. Apply native-arm restrictions to caller views only, or prove every eligible truth ID survives. Assert the identical truth-ID multiset for all six callers and both arms. No caller-specific denominator. |
| Exact environment | Freeze cluster Truvari 5.4.0 / pysam 0.24.0 / bundled 1.23.1 identities; local 0.24.1/1.24 source compatibility is not sufficient proof. Run a small end-to-end SV fixture for decomposition, duplicate truth IDs, lenient multi-match and both arms. |
| Budget | Replace the draft's stale resource section before outcomes. Reserve every preparation and repeated read starting from retained aggregate charge **5,219,838,743 bytes**; preserve all previous charges. |

These are pre-outcome corrections, not changes selected to improve a result.
No eligibility denominator, union coverage, missing-event list or biological
score has been inspected. Any later change to scientific rules must be explicit
before outcomes and independently reviewed. The first diagnostic remains
development evidence on released HG002 files, not independent confirmation,
state-of-the-art superiority or a candidate-generation ceiling.

The decision deadline remains the next working day: reach the reviewed fixed
diagnostic, or reject this dataset route if further bespoke infrastructure is
required. Do not resume the closed caller stager or broad source-wrapper work.
No expensive campaign or publication contribution is approved.
