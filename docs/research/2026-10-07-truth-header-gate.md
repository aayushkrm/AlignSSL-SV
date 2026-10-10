# Current truth header: bounded independent gate

Date: October 7, 2026. The previous goal turn made verified progress:
all six frozen released files passed local standard parsing/count/hash checks,
642 tests passed with 29 skipped, and checkpoint `af9351e` was pushed.
The scientific objective is active and unachieved. Main read the full current
goal and clean worktree before this continuation.

## Separately approved scope

Dirac (Sol6.1/high requested) approved **one** header-only execution using:

| Artifact | SHA-256 |
|---|---|
| `analysis/inspect_truth_header.py` | `ff35909f4e1400dba52dc7d33f276deb803d00677d03def47f38f8cd2826a905` |
| `truth_header_protocol.json` | `099661e65ded46f807e676e7e9381547d0e50dc8963cae964a08db275551a145` |
| `truth_header_reservation.json` | `2ca1ce8191bf70e2c0a0a7a730167e436d125350affa1c5d61d997e335005b03` |

The existing compressed source is 42,978,214 bytes with pinned SHA
`edb582ceec508f6d745acd0a8c522ee4f235ff5bf4754ba6bdc4c3abee122b5c`.
Code rehashes exactly that size through one descriptor and checks descriptor/
path stability, then reads at most 65,536 compressed prefix bytes. Standard
zlib decodes the first gzip-member prefix **once**, with a one-MiB output
limit. All decoded read-ahead counts against the reservation, even though only
header lines through `#CHROM` are interpreted and saved. No continuation or
flush is allowed if the header is absent. First-member EOF/CRC and whole-file
CRC are distinct; whole gzip CRC is not claimed by a header gate.

Nine synthetic tests passed in 0.09 seconds, including actual growth during
prefix read, whole-source SHA/size mismatch, bad first-member CRC, truncated
header, concatenated gzip members and decoded read-ahead overflow. They do
not establish real source compatibility. Reviewer supplied approval after
checking the exact pins; tests are reported by main, not independently rerun.

Reserve **1,048,576 decoded bytes** beyond retained aggregate
5,219,838,743 bytes. New full conservative charge is **5,220,887,319 bytes**;
no refund on failure or unused read-ahead. Source acquisition charges are
unchanged. Linux process CPU limit is 30 seconds and address-space limit 256
MiB; the outer command is `timeout -k 5s 60s`. Use a fresh project directory,
verify remote script/protocol pins, and preserve reports/logs. If killed or
the report is absent/truncated, record a controller failure separately; do
not repeat the read automatically.

This approval does not include truth body parsing, BED inspection, eligibility
denominators, sorting, decomposition, matching, refinement or scoring. It is
to fix the exact sample and contig/GT/phase header contract for the already
specified preparation. No large campaign is selected.

## Actual execution result

The remote script and protocol SHA pins matched before execution. The single
approved command exited zero. The source compressed SHA/size and snapshots
passed. Exact sample label is **HG002**. The header declares 24 contigs
(1–22, X, Y) with GRCh37 lengths and GT/AD FORMAT fields. Its 22 autosomal
names/lengths agree with the released caller declarations; this is dictionary
compatibility, not reference-base identity. No PS field is declared in this
header; this does not prove absence of undeclared populated phase fields in
unread rows, and does not authorize inferring long-range phase.

Raw header bytes: **4,094**; SHA-256:
`42b183108a8bf35933f14a56befabfb3e9e904430bd16eeb008760b27d38295f`.
All decoded first-member bytes including uninterpreted read-ahead: **65,280**.
First-member EOF/CRC passed; whole-file gzip CRC was not checked or claimed.
Keep the full one-MiB reservation and **5,220,887,319-byte** aggregate charge.
No truth body record was parsed or saved; no BED/denominator/score was read.

The process used 0.039955 CPU seconds, 0.050079 wall seconds and 18,059,264-byte
peak RSS. The raw small report is copied byte-for-byte into the dated audit
directory; the original remains in the fresh project scratch directory. No
previous report was overwritten. All data interpretation gates remain separate.

The header also declares HET1/HET2/GAP1/GAP2 truth FILTER states. Whether any
occur in eligible records is unobserved. Apply native filtering to caller
views only, preserving the identical truth-ID multiset across both arms.
Eligible truth REF and native size/type must be checked against pinned inputs
before scoring; matched contig lengths alone do not establish that contract.

## Current cluster state

Fresh `squeue -h -u igorno` is empty. `ws_list` reports 15 days 20 hours left,
expiry October 22 at 23:02:50 cluster-local, and one extension available.
No job was launched or cancelled. SSH uses the configured connection;
private-key contents were not read. Only project-owned files are in scope.

Parallel Luna/max-requested workers address the existing truth boundary
classifier and a synthetic end-to-end shared-denominator fixture. Their
changes do not authorize data reads. Model runtime configuration is not
independently attested. The next goal remains the reviewed fixed diagnostic,
not another broad source acquisition or a return to DeepSV/SSL.
