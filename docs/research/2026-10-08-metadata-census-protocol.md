# One prospective metadata census

Date: October 8, 2026. Later status: the exact v2 census completed once;
[result](2026-10-08-metadata-census-result.md) and qualified independent review
are complete. Initial prospective specification/history below are preserved.
No genomic body was read to write that specification. Historical attempts
remain closed; no additional read or broader experiment is authorized here.

## Decision and purpose

Main accepts the [Sol6.1/max-requested strategic decision](2026-10-08-strategy-reset-decision.md):
one bounded technical census has decision value. The
[contract audit](2026-10-08-metadata-contract-audit.md) identifies a possible
standards/guard mismatch, not the real failed cause. The
[payoff audit](2026-10-08-empirical-payoff-audit.md) leaves the caller screen
closed and generic benchmarking unselected. A worker is implementing only
the census and synthetic tests. Requested models are not backend attestation.

Question: what metadata flags occur across the entire unchanged prepared
input, and which is the first strict-contract contradiction in source order?
The old pysam/Truvari execution is NOT replayed. A lexical contradiction is
not automatically the original failed identity or a standards violation.

## Frozen scope

One existing cluster input, already preserved outside Git:
`/scratch/igorno-alignssl_restart_20260922/svpg_truth_prepare_20261007_02/prepared/eligible_truth.vcf`.
Expected bytes: 11,853,747; expected provisional rows: 11,490; sample HG002.
SHA-256: `c908217f7ec8eba1efe93f51605675a8a8b9676d9c9ca443d1348ad0a00f68d2`.
This is the preparation's stream-written pin; byte identity will be checked
during this run, not inferred from matching size. The matching-size local
copy is not read. Main departs from the strategy note's local execution path
to use established Linux CPU/address-space controls and the user's cluster
preference. This changes the execution location, not the frozen payload or
scientific scope; the independent exact review must accept this recipe.

Read at most 16 MiB into immutable bytes, verify the pin, and parse that
payload with a narrow stdlib diagnostic and the unchanged linear classifier.
Read the source once more under the same cap, checking hash and stat snapshot.
No installed native genomic parser is used or assumed equivalent.

Keep every row in the census. Report overlapping eligibility, SVTYPE and
SVLEN flags, clean/flagged totals, kind totals, unique source-ID count and
ordered ID digest. Record the actual fileformat and field declarations.
For the first contradiction only, report ordinal, ID, coordinate, allele
lengths and limited metadata states. Do not output bases, genotype strings,
read names or whole genomic records. Missing, sign-only and magnitude
differences stay separate. Unknown schema semantics stay unresolved.

No source repair, normalization, decomposition, row drop, truth-map read,
original-source pass, reference/BED/caller read, matching, scoring or training.
Native acceptance and REF remain UNASSESSED. The truth denominator remains
NOT VALIDATED even if the technical census completes. Raw data stay outside
Git; a small no-sequence technical report may be committed after review.

## Limits and accounting

At most 60 active minutes for specification, controls, execution and report
review. Real run: 60 CPU seconds, 120 wall seconds, five-second kill grace,
4 GiB address space, one process, report at most 1 MiB. No new framework,
package installation, genomic transport or cluster campaign. Tiny code,
helper, protocol and no-sequence report transfers fit the metadata allowance.

Reserve 33 MiB (34,603,008 bytes): two at-most-16-MiB source passes and
at-most-one-MiB diagnostic code/protocol/report metadata. This is a conservative
reservation, not measured physical or runtime-library I/O. Full retained
charge: 8,588,703,005 + 34,603,008 = 8,623,306,013 bytes. No refund on failure.
The aggregate 64-GiB ceiling and two CPU-hour limit remain unchanged. Prior
measured CPU and run limits must be reconciled before execution.

Run only after independent acceptance of exact code/helper/protocol hashes
and launch recipe. The executable approval flag is not reviewer approval.
Hash/schema/count/parser/integrity/resource failures end this census as
incomplete; no prefix result, automatic retry or expanded scope. Integrity
failure stops use of this copy. Historical logs and reservations remain intact.

## What the next decision needs

A complete census can explain an engineering contract failure. It cannot
show a caller miss, validate truth, establish novelty or approve an experiment.
Any uniform prospective analysis rule and any empirical screen require their
own scientific decision and independent review before outcomes. No new
publication lead or expensive campaign is selected here.

## Original implementation/preflight — v1 withheld, not executed

Luna/max requested worker completed the diagnostic and synthetic tests;
main reviewed the complete implementation and controls. New controls: 14
passed. Combined new/helper/old metadata checks: **55 passed, 3 skipped in
0.65s**. Native-stack skips are not native validation of this census. Old
checker/helper bytes are unchanged. Script is 25,652 bytes; helper is 12,525.
This is a narrowly frozen script, not a reusable VCF validator or new pipeline.

| Artifact | SHA-256 |
|---|---|
| Diagnostic | `deae6f39416eabc5dd7b65131b24dc5d57a9a2341bc16153d013d743cd193649` |
| Unchanged helper | `4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93` |
| New tests | `9dd81bce88ba2871c436e6c0fecca68bfc2767a4b1ad0a8146412a5f2f56b894` |
| Protocol JSON | `e0a8cdf1605c3f37d9fde2302702180bfea704e1f9f941120ded705e633c9cb8` |
| Exact Linux launch | `8cde01488c0f2904ed385acd53c319321637d47520433222da8026e21383b4eb` |
| Prospective reservation | `d564748f4477ee2f1f87d829f5cfe08dd27c0c03cc1595058e9bdfa4e9674246` |

Linux preflight confirms Python 3.10.20, `/usr/bin/time`, `timeout`, a regular
11,853,747-byte prepared input and an absent fresh output root. No input hash
or body was read in preflight. Two small original failed synthetic-control
logs reconcile formerly unknown CPU to 0.15 and 0.14 seconds. All named prior
stage/preparation/control CPU sums to 421.532707 seconds; this census's
60-second maximum leaves 481.532707, below 7,200 seconds. The original
reservation retains its conservative placeholders; the separate preflight
record supplies observations. Historical SSL/general software suites are
not charged as this experiment's compute. No refund of source-read charges.

The launch enforces Linux CPU/AS limits and a bounded wall timeout, verifies
all code/protocol pins and fresh report/log paths, and writes no genomic
artifact. Named code/protocol bundle is under 64 KiB. At most eight bounded
bundle reads/transfers and four bounded no-sequence output-bundle reads/copies
of at most 128 KiB each fit the one-MiB metadata allowance. Before output
retrieval, check summed sizes; stop rather than fetch an oversized bundle.
This reservation does not describe physical/cache/runtime-library or Git I/O.

Execution still awaits [exact independent approval](2026-10-08-metadata-diagnosis-review.md).

### Focused correction and new prospective pins

The reviewer withheld v1: source growth could consume a cap-plus-one byte
before failure. Main removed that overflow probe from the acquisition,
posthash and metadata readers. Snapshot/hash checks still reject growth.
Two synthetic growth-at-cap regressions confirm each source path consumes
only the cap, not its overflow byte. Combined focused result: **57 passed,
3 skipped in 0.45s**. This changes no allele, population, flag rule or budget.

V1 code/protocol staging remains untouched on the cluster; no genomic command
was run there. V2 uses a fresh `_02` report root and adds an aggregate
128-KiB output-bundle guard before any retrieval. Same single 33-MiB allowance;
no second genomic pass reservation or refund. Original protocol/launcher pins
above remain withheld history. Corrected execution needs exact reapproval:

| Corrected artifact | SHA-256 |
|---|---|
| Diagnostic | `2fb977a24b4d027ee4508f2f45eb07d11866cc4dd8101ab340cf95983de1f523` |
| Tests | `7d86fba1eced8b284148476ed2383fc6f687ffeb2464dd480cb84d6cab0e0955` |
| Protocol v2 | `b1f619bccc1d6728048da6165a5c872d0f4d6e38c2b4b5fd43dd42134acdf0d4` |
| Launcher v2 | `655a802390c88426c60da15d3821878294d9f33d3cda3889e098b6af33a56113` |

The unchanged helper, expected input and retained-charge pins are identical.
No actual genomic read or scoring is approved merely by writing these files.

The independent reviewer subsequently approved ONE exact v2 execution under
the corrected four pins. Main independently checked matching remote hashes
and fresh report/log paths. Book the single full 33-MiB reservation before
launch: **8,623,306,013 bytes retained** on success or failure. No refund,
automatic retry, extra source pass, native/REF validation or scoring is approved.
V1 remains withheld and unexecuted. Actual result will be recorded separately.

## Current benchmark source check

The already committed October 7 original-source header report declares
VCFv4.2, SVLEN Number=1/Type=Integer and SVTYPE Number=1/Type=String.
Static preparation code inspection confirms raw header lines are retained.
The census must still observe and reconcile its prepared header. This closes
the source-version uncertainty from the README-only contract audit without
another real-source read. [VCF 4.2's SV INFO specification](https://github.com/samtools/hts-specs/blob/e821e4f02ae25c2175f9a366edca1322d6a2de72/VCFv4.2.tex)
describes positive insertion and negative deletion lengths. Therefore a
positive deletion value, if observed, cannot simply be called a compliant
4.5 encoding. Annotation semantics, usable literal alleles and biological
truth remain separate. Exa retrieved the relevant primary specification;
a separate Truvari annotation-documentation fetch failed and supplies no evidence.
Web's GitHub tree fetch also failed. Exa's alternative raw official
[Truvari 5.4.0 annotation source](https://raw.githubusercontent.com/ACEnglish/truvari/v5.4.0/truvari/annotations/svinfo.py)
was retrieved successfully: `add_svinfo` assigns `var_size()` to SVLEN.
That shows one unsigned annotation implementation, not which version produced
this benchmark's fields. No source repair or native execution follows.

Life Sciences Literature's bioRxiv API returned one version, v1, dated
**October 1, 2026**, for DOI `10.64898/2026.09.23.752440`. The DOI suffix is
not the posting date; Exa's January 1 metadata is not used. The API request
was compact and successful; raw JSON was not saved.

The [Q100 primary preprint](https://www.biorxiv.org/content/10.64898/2026.09.23.752440v1.full)
describes assembly-derived benchmarks with exclusions for alignment,
representation, mosaicism and known errors. External SV review samples
discrepancies by type and repeat context and uses reads aligned to both the
reference and phased assemblies. Uncertain curations remain uncertain in
sensitivity analyses. These methods already challenge a generic new-territory
miss claim. Our six archived outputs do not establish the same input reads,
and our pinned draft bytes are not proven identical to that paper's inputs.

Inspection scope: Exa returned a 70,325-character primary-text extraction;
main read the introduction, benchmark construction/exclusions and external
manual-curation/confidence methods. Tables, supplements, native curation
records and paper code were not independently audited. No project biological
result follows from a paper's validation. No broad new search was run here.
