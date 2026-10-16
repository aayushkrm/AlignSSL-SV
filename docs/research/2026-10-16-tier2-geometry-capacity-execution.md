# Tier2 geometry screen: incomplete01 and prospective02

16 October 2026, Asia/Tomsk. The research objective remains novel, rigorous
work with meaningful results. This capacity repair is not that result.

## Actual01: closed incomplete before native study classification

Job1604877 FAILED2:0 on14October. The native synthetic controls passed, but
the collector stopped at its128MiB derived-BAM guard. The wrapper correctly
did not classify the study BAM. No flag count, biological null, filter error
or allele-support loss was observed.

| Observed field | Value |
|---|---:|
| Completed source windows |44 of59|
| Fetched records |16,469|
| Distinct physical source records |16,448|
| Raw derived BAM |134,770,508B|
| Name-sorted BAM |136,523,769B|
| Group metadata |5,334,340B|
| Manifest |59,460B|
| Complete outer leaf |277,457,883B|
| Collector wall time |58.008s|
| Allocated CPU × elapsed |1 ×59 =59CPU-s|
| Measured CPU |55.094s|
| MaxRSS |207084K|

The first unfinished window isW0045 onchr17. Later zero-valued window/event
counts are unvisited, not evidence of no reads. The prefix can have group EOF
after sorting while source fetch remains incomplete. Retain that distinction.
The source BAM/BAI stats are unchanged; historical whole hashes are not fresh
rereads. Buffered output overshot the nominal guard;01 is not called compliant.

Full unmodified01 is present in scratch and permanent HOME under
`experiments/tier2_geometry_screen_20261014_01`. Fresh16October recursive byte
comparison finds no differences. Fresh permanent-copy SHA256s:

| Artifact | SHA256 |
|---|---|
| `collection/manifest.json` |`da1c26e15bd253b97bb08952437baa226aa15e3f4229187899e98da5e6538d4a`|
| `collection/raw_subset.bam` |`74faedba554c520c52644324a6fe4a87ff2e8672a0c456fe53420cd7190a50c6`|
| `collection/namesorted.bam` |`c9bd0d21391a57f28c1cd74808f997f248c3d7dcf7c2f7608348751202231da2`|
| `collection/groups.jsonl` |`13cd70292b2ab5d3b58a072c8b49ccf2e83277bb15986c37a19dac72b5abd9b0`|

Small metadata is retained locally at
`runs/tier2-geometry-screen-20261016.3Z6EcG/run01-metadata`.
No partial-BAM classification is used to select02. Both interruptions leave
the failed run intact. Older tracking snapshots saying UNBOOKED are superseded
here, not retroactively treated as actual results.

## Prospective technical exception for02

The [previous independent review](2026-10-14-pivot-scout-review.md#prospective-run02-storage-correction-after-run01-cap-stop)
accepts a separately recorded storage correction. Keep the original protocol's
no-inflation rule and01 history; this is an explicit exception after a
technical cap stop, before any native study outcome was available.

Change only nominal per-BAM capacity128→512MiB and the leaf allowance1→2GiB.
Defaults remain128/1024MiB;02 must explicitly request512/2048MiB. Mixed pairs
and selection-mode overrides are rejected. Tests compare the same records,
group metadata and event/window counts under both settings. No tags are lost.
The source, all53 rows/59 windows/3,692,176bp,50,000-record cap,300s soft clock,
native defaults, eligibility rules and interpretation are unchanged.

Cost heuristic: scaling the observed prefix by59/44 suggests roughly78s of
collection and181MB per BAM, plus native work. This is not a density/throughput
guarantee.512MiB gives storage headroom without reserving or spending that space;
the2GiB RAM request stays unchanged. OneCPU/2GiB/15min remains sufficient for
the bounded attempt; no deadline increase is approved. Count both attempts,
both BAMs, metadata and sort temporaries. Guards are sampled, not disk quotas.

The new exclusive scratch leaf will be
`experiments/tier2_geometry_screen_20261016_02`. Direct `srun` on
hydra-n1/amd_256M avoids the known batch/HOME-write path failure. Repeat the
small native ABI gate before study collection. Native classification requires
complete fetch/group EOF, unchanged source stats and all53 event rows. A
64MiB storage reserve is checked before native work; final leaf ceiling2GiB.
Another failure stays incomplete, not zero flags or permission for retries.

The executable, helper and plan stay pinned. Original01 snapshots and code
remain in their old leaf. This does not rewrite a past experiment or authorize
a new caller/model campaign. A flag, if any, is only an adjudication candidate.
Preserve complete02 through login into permanent HOME and hash-check it before
22October; the fresh workspace listing reports6days21hours/one extension.
Filesystem free space is ample, but `df` does not attest a per-user quota.

The old reviewer handles now return `not_found`. Finished reviews remain
evidence. A replacement Sol6.1/high-requested reviewer checks the narrow code
and command amendment; configuration is not independently backend-attested.
The full research goal remains active and unmet. No02 job is booked here.
