# Full-reference ambiguity audit: HGSVC no-ALT versus IGSR GRCh38

**Date:** 2026-09-23. **Scope:** reference-sequence provenance and ambiguity,
not donor callability, truth confidence, or SV performance.

The earlier [complete base-difference map](2026-09-23-reference-reconciliation.md)
found 13,923,221 unequal bases on 18 of 194 shared contigs. Its independent
[review](2026-09-23-scientific-review-reference-map.md) found that shared `N`
sequence can lie *between* difference intervals. The mismatch BED therefore
cannot serve as a reference-ambiguity mask. This audit generated the missing
per-reference non-ACGT BEDs from complete FASTAs, checking every sequence M5.

## Inputs and reproducibility

| Input | SHA-256 | Verification |
|---|---|---|
| HGSVC no-ALT `hg38.no_alt.fa.gz` | `90f1dcdb28a81ac26f6eaa1afc285e7ec459c195c2134fb25af0e82be2f11729` | Publisher MD5 manifest, gzip test, 194/194 HGSVC VCF sequence M5s |
| IGSR `GRCh38_full_analysis_set_plus_decoy_hla.fa` | `3b103f4742abfd54938fb0333e19ad067635c8eb86f1dbf0ce44b165c4292b50` | Official IGSR `.dict` SHA-256 `91f7a9993b70c9c85b3a51a20b888d866cd55938ce1ccd3a325a38954d2fbdeb`; 3366/3366 sequence M5s |

The IGSR FASTA is 3,263,683,042 bytes. SLURM job `1598077` staged and hashed
it; dependent job `1598079` scanned both FASTAs with
[`scripts/scan_reference_ambiguity.py`](../../scripts/scan_reference_ambiguity.py)
using [`cluster/scan_reference_ambiguity.sbatch`](../../cluster/scan_reference_ambiguity.sbatch).
The four raw BED/JSON outputs, both job logs, and IGSR source manifests are mirrored
in [`results/reference_ambiguity/2026-09-23`](../../results/reference_ambiguity/2026-09-23);
the HGSVC source manifest is in the adjacent reference-reconciliation bundle.
Their local SHA-256 digests match the cluster manifest, recorded as
[`MASK_SHA256SUMS`](../../results/reference_ambiguity/2026-09-23/MASK_SHA256SUMS); the BED hashes also
match their JSON companions. The IGSR and HGSVC FASTAs and indexes are preserved
under `/home/igorno/alignssl_restart_20260922/references/` and verified against
their respective `SHA256SUMS`. The fresh
[`2026-09-24` login-node verification record](../../results/reference_ambiguity/2026-09-23/preserve_login_verification_2026-09-24.txt)
retains all six `OK` results. The FASTAs are intentionally not committed to Git.

A first attempt to preserve them in SLURM job `1598082` failed because the
compute node reported the home archive path as read-only. Its log is retained.
The successful low-priority copies were performed on the login node; the
repeatable command is [`cluster/preserve_reference_snapshots.sh`](../../cluster/preserve_reference_snapshots.sh).
Scratch remains time-limited to 2026-10-22 unless renewed.
An [independent review](2026-09-24-scientific-review-reference-ambiguity.md)
of this ambiguity analysis is complete, with model/effort attestation caveated
in that note. It accepts only the narrow saved-map sequence-content result;
do not promote this finding into a cohort-compatibility or efficacy claim.

## Observed reference territory

| Territory | Non-ACGT bases | BED intervals |
|---|---:|---:|
| Complete HGSVC no-ALT FASTA, 194 contigs | 151,122,963 | 1,094 |
| Complete IGSR FASTA, 3,366 contigs | 173,893,449 | 1,185 |
| Union on the 194 shared contigs | 165,046,090 | 1,037 |
| Intersection on the 194 shared contigs | 151,122,963 | — |

The shared contigs span 3,099,750,718 reference bases. HGSVC non-ACGT
territory is a subset of IGSR non-ACGT territory on those contigs; the extra
13,923,127 IGSR non-ACGT bases are precisely the HGSVC A/C/G/T versus IGSR `N`
class identified in the full difference map. The other 94 unequal bases are
ambiguous in both references. Consequently, **zero** of the 13,923,221
base differences lie outside the union non-ACGT BED. Equivalently, where both
references have A/C/G/T on these 194 shared contigs, their bases agree. This is
a sequence-content statement, not proof that alignments, SV calls, or coordinate
handling are interchangeable.

[`scripts/analyze_reference_ambiguity.py`](../../scripts/analyze_reference_ambiguity.py)
verifies source BED hashes and counts, the full difference-map bundle, and the
prior 194-contig M5 audit. It writes
[`reference_ambiguity_analysis.json`](../../results/reference_ambiguity/2026-09-23/reference_ambiguity_analysis.json)
and [`joint_reference_non_acgt.bed`](../../results/reference_ambiguity/2026-09-23/joint_reference_non_acgt.bed).
The joint BED SHA-256 is
`17315f48dea4597ddc59f088e281584fad0c66eafd9809f8a5348489b8f101d1`.
The [analysis manifest](../../results/reference_ambiguity/2026-09-23/ANALYSIS_SHA256SUMS)
also records the final JSON digest.
It represents reference ambiguity only; it is **not** a donor-callability or
safe-exclusion mask.

From the repository root, the local reduction can be reproduced with:

```bash
../.venv/bin/python scripts/analyze_reference_ambiguity.py \
  --hgsvc-bed results/reference_ambiguity/2026-09-23/hgsvc_non_acgt.bed \
  --hgsvc-json results/reference_ambiguity/2026-09-23/hgsvc_non_acgt.json \
  --igsr-bed results/reference_ambiguity/2026-09-23/igsr_non_acgt.bed \
  --igsr-json results/reference_ambiguity/2026-09-23/igsr_non_acgt.json \
  --m5-audit results/reference_reconciliation/2026-09-23/all_contig_m5.json \
  --differences results/reference_reconciliation/2026-09-23 \
  --out-bed results/reference_ambiguity/2026-09-23/joint_reference_non_acgt.bed \
  --out-json results/reference_ambiguity/2026-09-23/reference_ambiguity_analysis.json
```

## Decision and open gates

In the difference map, the M5 discrepancy is explained at the base level by
ambiguity/masking differences, not by A/C/G/T substitutions on the shared
contigs. A [frozen-input replay](2026-09-24-frozen-reference-replay.md) of all
18 distinct contigs (SLURM job `1598267`) reproduced every BED byte and
scientific summary field from hashed FASTAs, closing the saved map's earlier
live-URL input-provenance gap.
The current evidence removes one possible cause of incompatible truth and CRAM
references, but does not
establish that candidate generation, evidence extraction, truth matching, or
SV scoring near ambiguities are safe. The current analysis also says nothing
about IGSR-only decoy/HLA sequences, which can affect read alignment. Before
using HGSVC3/IGSR as a labelled cohort: inspect source read mappings and
candidate/truth overlap with a predeclared flank policy; obtain validated
per-donor callable/negative regions or avoid confident negatives; and freeze
pedigree-safe splits and an untouched confirmation set. Bulk CRAM download
remains on hold. No positive model result is claimed.
