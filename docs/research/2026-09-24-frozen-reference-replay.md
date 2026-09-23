# Frozen-FASTA replay of the HGSVC/IGSR reference-difference map

**Date:** 2026-09-24. **Status:** complete technical provenance check; no
cohort-selection or model-performance claim.

The first complete 18-contig base-difference map was computed against a live
IGSR FASTA URL. That job did not preserve a digest of the exact remote FASTA
bytes it read. The later full IGSR snapshot has SHA-256
`3b103f4742abfd54938fb0333e19ad067635c8eb86f1dbf0ce44b165c4292b50`
and matched all 3,366 entries in its official sequence dictionary. The HGSVC
no-ALT FASTA has SHA-256
`90f1dcdb28a81ac26f6eaa1afc285e7ec459c195c2134fb25af0e82be2f11729`
and matched all 194 shared HGSVC VCF contig M5s. Both snapshots and indexes
were hash-checked again after preservation in cluster home storage.

[`cluster/audit_frozen_reference_differences.sbatch`](../../cluster/audit_frozen_reference_differences.sbatch)
replayed [`compare_reference_contig.py`](../../scripts/compare_reference_contig.py)
on the two frozen scratch copies under job `1598267`. It checked IGSR
`SHA256SUMS` and the HGSVC SHA-256 before reading sequence. The job completed
with exit code `0:0` in 1m29s. Its
[log](../../results/reference_reconciliation/2026-09-24/frozen_compare_1598267.out),
36 BED/JSON files, source note, and file manifest are in
[`results/reference_reconciliation/2026-09-24`](../../results/reference_reconciliation/2026-09-24).
No raw FASTA was committed.

The local file manifest validates all 18 new BEDs and 18 JSON files.
[`scripts/verify_frozen_reference_replay.py`](../../scripts/verify_frozen_reference_replay.py)
also verifies the original map bundle, the replay source hashes and paths, and
the replay manifest. For every contig it confirms **byte-identical BEDs** and
equality of length, difference count, interval count, difference-type counts,
first recorded positions, and BED digest. The resulting
[`VERIFICATION.json`](../../results/reference_reconciliation/2026-09-24/frozen-comparison-1598267/VERIFICATION.json)
records exact agreement on all 18 contigs: **13,923,221 unequal bases in 152
intervals over 2,371,021,378 compared bases**. The
[`BUNDLE_SHA256SUMS`](../../results/reference_reconciliation/2026-09-24/BUNDLE_SHA256SUMS)
file covers the log, source note, file manifest, and verification JSON.

From the repository root, the reduction can be repeated without FASTA access:

```bash
../.venv/bin/python scripts/verify_frozen_reference_replay.py \
  --historical results/reference_reconciliation/2026-09-23 \
  --frozen results/reference_reconciliation/2026-09-24/frozen-comparison-1598267 \
  --out results/reference_reconciliation/2026-09-24/frozen-comparison-1598267/VERIFICATION.json
```

This establishes that the *saved sequence-difference map* is exactly
reproduced from the hashed frozen FASTAs. It does not prove which bytes the
historical URL served at that earlier moment; that is no longer needed to
interpret the reproduced map. The [joint non-ACGT audit](2026-09-23-reference-ambiguity.md)
therefore has stronger input provenance for its zero-difference-outside-union
observation. Reference agreement where both bases are A/C/G/T remains a
sequence-content result only. It does **not** validate read alignment around
masked sequence, IGSR-only decoys/HLA, HGSVC3 donor callability, confident
negatives, truth matching, or independent confirmation. Bulk CRAM transfer
and candidate-label training remain gated.
