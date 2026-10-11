# Locityper: usable control schema, unresolved structural truth

Executed October 4 local / October 3 UTC. This is a data-availability result,
not a genotype-performance result or a selected publication thesis.

## Decision

The two inspected tables declare all required native controls together.
However, this benchmark archive alone has not passed the structural-truth
gate. Do not read outcome rows, fit a detector or download the larger database
under this stage's approval. Resume the broader opportunity search. Do not
replace structural absence with generic sequence divergence to get a result.

| Requirement | Evidence | Status |
|---|---|---|
| Exact acquisition identity | 14,709,179 bytes; publisher MD5 matches; local SHA-256 recorded | Pass |
| Safe archive inventory | 19 members: 3 directories and 16 files; complete outer gzip/TAR stream checked | Pass for outer archive, not all nested streams |
| Joint native controls | Both inspected headers declare `quality`, `unexpl_reads`, `weight_dist`, `warnings`, `total_reads` | Schema pass only |
| Prediction and evaluation-unit declarations | Both have `sample`, `locus`, `genotype`, `query_type` | Declared; populated values, unique keys and joins not checked |
| Remaining-panel sequence comparison | LOO header adds `avail_edit`, `avail_size`, `avail_div`, `avail_qv` | Declared sequence distances, not verified structural labels |
| Confidence-qualified structural panel-absence truth | No such field in these two headers; inspected source aggregates sequence differences | Unresolved; no outcome experiment approved |
| Separate donor / locus-family holdouts | No row access or independently verified family/panel-exclusion manifest in this stage | Unresolved |

This does not prove that Locityper's other data lack useful truth, or that an
open-panel research question is impossible. It limits what these inspected
schemas and sources establish. No native-control failure or biological null
result has been measured.

Independent review accepted this narrow conclusion and verified report
checksums. The two `hap` rows share their `query_type` and original prediction
fields; the declared keys do not identify separate haplotype units. A later
protocol must not infer independence or a haplotype join from those columns.

## Source-verified format repair

The [October 1 plan](2026-10-01-open-panel-preflight.md) froze an inventory-first
inspection. The reader initially failed closed because the first line was not
a recognized CSV header. It wrote no header report and printed no rejected
content. This was a format failure, not missing scientific data.

At official commit `146cfd42e9179bafd63d1f41db7fc449940989de`:

- [`extra/eval_accuracy.py`](https://github.com/tprodanov/locityper/blob/146cfd42e9179bafd63d1f41db7fc449940989de/extra/eval_accuracy.py),
  blob `13db51350b74db2826073af6cb79daf8cd7b71e0`, writes one `# ` command
  comment before its tab-separated header.
- [`extra/into_csv.py`](https://github.com/tprodanov/locityper/blob/146cfd42e9179bafd63d1f41db7fc449940989de/extra/into_csv.py),
  blob `96fb123d38fad396aef2862ddb39d2eac3c3f118`, defines the eight native
  columns carried into that evaluation.
- [`extra/gt_dist.py`](https://github.com/tprodanov/locityper/blob/146cfd42e9179bafd63d1f41db7fc449940989de/extra/gt_dist.py),
  blob `c12cbdd51e8cdca49efe82fe2729d522c25d4b91`, records pairwise distance
  as alignment size minus matched bases, with alignment size as denominator.
  `find_closest` excludes named true/excluded haplotypes, then finds the
  smallest sequence divergence among remaining candidates. These emitted
  distance summaries do not separate a ≥50-bp structural event from ordinary
  nucleotide differences. Identical representatives can remain after LOO.

The same distance source contains optional upstream CIGAR parsing. The
missing-structural-label statement applies to the inspected QV output fields,
not to all upstream alignment information or possible reconstruction routes.

Source code was read, never executed. The source format does not establish
the historical archive-producing executable's exact identity.

An append-only protocol v2 enabled exactly one leading `# ` line. Its content
was neither printed nor retained; only length and SHA-256 were recorded.
Comment plus header share a 64-KiB limit. The table paths, required columns and
allowed vocabulary did not change. A second comment or a headerless data row
still fails. The independent reviewer approved this amendment before retry.

## Raw evidence and limits

Artifacts are under
[`results/data_audits/locityper_2025/2026-10-04/`](../../results/data_audits/locityper_2025/2026-10-04/):
inventory, original/v2 frozen protocols, two header reports and an execution
ledger. The 14.7-MB archive remains outside Git.

| Run | Aggregate decompressed bytes / conservative charge | Outcome rows parsed |
|---|---:|---:|
| Inventory | 14,837,760 | 0 |
| First header attempt, failed | ≤14,903,297 charged | 0 |
| Full-panel header retry | 18,209,039 | 0 |
| LOO header retry | 19,759,106 | 0 |
| Total stage charge | **67,709,202 / 262,144,000 budget** | **0** |

The failed-attempt counter was not returned. Its conservative charge includes
the entire verified outer TAR plus the maximum first-line request; source
inspection confirms failure occurred before nested-stream drain. Repeated
outer traversal is charged. The two retained header metadata blocks total 375
bytes. All three successful scans validated the complete outer stream; only
the two selected nested gzip streams were validated internally. Body bytes
passed through integrity checks but were not decoded as records, retained or
scored. No bundled scripts or archive members were extracted.

Scanner CPU totaled 1.87 seconds. Each scan had a 120-second CPU limit.
Maximum measured RSS was 17,223,680 bytes, below the 4-GB budget. macOS rejected
the requested `RLIMIT_AS` before scanner startup, so a hard address-space cap
was not enforced. Bounded stream allocations and measured RSS supplied the
alternative; do not report a nonexistent hard memory cap.

The independent reviewer used requested Sol6.1/high; the initial code worker
used requested Luna/max. Actual execution configuration remains unattested.
Reviewer stages covered the initial recognized-schema contract, the
source-verified comment amendment before retry, and the final narrow evidence
interpretation. No reviewer accessed genotype outcomes or changed results.
The initial 29 safety tests passed independently. The format amendment adds
seven cases: all 36 pass. The first full suite, before those seven cases,
passed 461 tests with 29 skipped. The final full suite passed **468 tests with
29 skipped** in 247.68 seconds.
Manuscript/result consistency and `git diff --check` passed. The cluster queue
was empty; no job was submitted or cancelled. Scratch expires October 22 at
23:02:50 cluster-local, with one extension available.

## What could justify a later experiment

Before any outcome analysis, require a separate reviewed protocol with a
defined evaluation unit, donor/family holdouts, population/join checks,
independent structural absence labels and their confidence scope. Compare
combined native controls and ordinary calibration, not GQ alone. Reject a
new-detector thesis if those controls suffice. This stage grants no such
analysis permission and claims no publication-worthy improvement.
