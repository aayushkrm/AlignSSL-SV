# Candidate one-off SVUPP archive inventory

Status: **UNBOOKED, UNSTAGED, UNEXECUTED; exact review pending**.
This is data-readiness work for a conditional research question, not a
publication result or permission for generic GQ-ranked benchmarking.

## Fixed question and input

Does the author assessment archive expose reproducible score/truth inputs
that could support a useful new empirical question beyond the published
GQ-ranked coverage comparison? A manifest alone cannot answer calibration,
truth validity, clinical benefit or independence. It can rule out a proposed
cheap development test whose inputs are not present.

Inspect exactly `SVUPP_paper.zip` from author record 17569072:
47,443,427 bytes, MD5 `5469337ca9249691b2b376ceb9b67e1d`.
Measure stored SHA256; authenticate complete stored size and MD5 before ZIP
use. Do not download its container, other ZIPs or any BAM/CRAM/FASTA. The
paper's older record lacks this assessment archive.
[Official versioned record](https://zenodo.org/records/17569072).

## Finite read scope

One acquisition to a fresh cluster root, one timed inventory, one output.
Download digest and complete stored digest must agree. Read the complete
central directory and list every member, including compressed/uncompressed
sizes, type, compression and CRC. Cap 4,096 members and 256 KiB aggregate
filename bytes; reject unsafe, duplicate, encrypted, multidisk, special/link,
absolute or parent-traversal entries. Never extract or decompress member
bodies. ZIP member CRC/payload integrity is **not** verified by listing.
Do not describe a listed VCF/RData name as a usable score or truth vector.

Require a stable regular single-link asset, unchanged full stored hash and
metadata snapshots before/after inspection. Manifest is exclusive and at
most 1 MiB. No outcomes are read, no caller is run, no split is chosen using
labels, and no genotype or calibration score is computed. A changed input,
failed integrity/type/count/cap check or acquisition failure closes this
attempt incomplete with no selective continuation or replay.

## Proposed complete resource allowance

One **512 MiB** named byte allowance covers acquisition, whole stored hash
passes, complete inventory/source checks, finite synthetic controls, bounded
logs and raw metadata source hash/transfer/local verification. No local
genomic asset transfer. Only manifest, claims, logs, timer and ledger are
collected, with a 2 MiB aggregate archival cap. This is an allowance, not a
measurement or proof of all physical I/O.

Prior retained bytes 40,772,178,827 plus 536,870,912 would become
**41,309,049,739**, below 68,719,476,736. Book before root creation only after
the exact code, pins, wrappers, account and claim/submission are reviewed.
Retain the full charge even on failure. Proposed named CPU 180 seconds;
prior measured 561.292707 would give 741.292707 with the allowance, below
7,200. Add only the actual outer waited-tree CPU once after completion.
Preserve all earlier charges and the closed native attempts.

Use one CPU, 2 GiB address space, 120-second outer wall timeout with five-
second kill grace, 60/90-second per-process CPU limits, one fresh submission
claim before Slurm and one timed payload claim. Archive output/file caps,
required synthetic control count and exact launcher are not yet frozen.
This document is not a ready submission bundle or booking record.

## Decision boundary

No new paper direction is selected here. If the archive has no plausible
score/truth resource, reject this acquisition path and stop. If members look
plausible, a separate small content/analysis protocol must define authoritative
truth, score semantics, complete eligible denominators, matched baselines,
leakage-safe development units and a real publication payoff before reading
outcomes. The whole public study is development evidence for this project,
never an untouched confirmation set. A technical replicate is not an
independent biological family. Do not make another leaderboard or change
the stopped released-callset screen into a confidence paper by renaming it.

Scratch expiry remains October 22, 2026 at 23:02:50+07, one extension. Retain
small metadata/code/claims outside scratch before that date. The versioned
author checksum supports later reacquisition; it is not a substitute for
saving scientific raw results if an actual analysis is later approved.
