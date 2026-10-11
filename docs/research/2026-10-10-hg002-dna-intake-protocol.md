# HG002 S1a: exact DNA acquisition

Prospective acquisition only. The [investment decision](2026-10-10-hg002-dna-stage-investment.md)
and [independent S0/S1 release](2026-10-10-public-paired-falsifier-review.md#hg002-concrete-s0s1-investment-review)
permit one exact DNA intake, not calling, reconstruction, P1 or RNA.
The actual launch below supersedes the preparation state; acquisition is
running, not complete or scientifically qualified.

## Exact execution

One CPU/8GiB RAM/4h in`amd_256M`, hydra-n1, direct srun with streamed stdout.
No whole node or GPU. Working bundle is read-only project home:
`/beegfs/datasets/home/igorno/alignssl_restart_20260922/bundles/hg002_dna_s1a_20261010_02`.
Writable exclusive output:
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/hg002_dna_s1a_20261010_01`.
Use the isolated CPython3.12.1 intake-check venv. Module command from bundle:

```sh
python -m scripts.acquire_hg002_dna \
  --output /beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/hg002_dna_s1a_20261010_01
```

| Frozen bundle file | SHA256 |
|---|---|
| scripts/acquire_hg002_dna.py | `57524ec840fdd08a9cd25505e230fbe1063ae0e4ade70f2f9dbba77f237aef35` |
| scripts/acquire_parent_sva_region.py, unchanged helper | `c0f47e522d4f88b2e068f035b78eb558e63e4abc94839b4a78e32f3c6f09034b` |
| tests/test_acquire_hg002_dna.py | `87ceab5c936b71b5b542b6b6d37221aa2bc82ce0eacabbcccdc925bd43777bec` |

Main FULL read initial221 acquisition/220 test lines and all subsequent
correction hunks; corrected source243/test267 lines. Local mocked controls:
32 pass, with no network,0.25s. The initial exact review correctly HOLDs a
returned-byte/cancellation gap: its8B were uncharged. Original01 bundle is
preserved unexecuted. Corrected02 handlers defer exceptions until returned
or partial-exception bytes are journaled and retained; both signals have
deterministic read-return/charge-boundary controls. Hashing checks cancellation
per4MiB. Socket timeout30s bounds inactivity, not absolute read duration;
Slurm is the hard allocation cap. Synthetic tests do not qualify the real BAM.
Independent reviewer clears the finite HOLD after five independent synthetic
checks. Deployed n1/amd_256M job1604247 verifies all three bundle hashes and
passes the complete32 Linux controls, zero skips,0.19s; actual module help also
works from the read-only bundle. This satisfies the conditional code-review
gate. Combined local selection86 tests plus9subtests passes, zero skips,0.96s.
No large transfer is claimed by these checks.

## Fixed inputs, budget and failure semantics

Only the[recipe's](2026-10-10-hg002-dna-input-recipe.md) original DNA BAM and BAI:
48,727,325,910B and21,582,928B; the immutable ETags and HTTPS URLs are compiled
into the launcher. HEAD and full206 GET verify exact object, content range,
length and identity encoding before any body read. No redirects,200 fallback,
second representation, automatic retry or RNA URL. SHA256 each whole object.

The52GiB cap is55,834,574,848B, including196,608B already acquired in all three
DNA/assembly header prefixes. Expected new body48,748,908,838B gives expected
cumulative48,749,105,446B, leaving7,085,469,402B. This is arithmetic, not actual
acquisition. Every at-most1MiB response-read is charged and journal-flushed
before writing; partial exception bytes are counted. Headers/TLS and software
are separately scoped, not claimed by the genomic body measure. The prior
argument may increase but never decrease. Failed-run charges never reset.

Require160GiB free before opening the objects. S1's peak disk limit includes
scratch and future custody/extracted-read copies; aggregate later-stage peaks
are not free separate allowances. This job books at most4allocatedCPUh of S1's
8h; measured task CPU is separate. At timeout/error, preserve the partial file,
initial/final manifests and journal. SIGALRM and SIGTERM request graceful
manifest closure; SIGKILL can leave only the initial manifest/flushed journal.
No biological null follows from incomplete intake, and no retry is automatic.

Atomic exclusive publication never replaces an existing complete object.
Fresh leaf only; helper hash drift, path alias escape, symlink output, existing
output, low space or source-pin drift stops. Do not write compute-node home.
No historical source/result or shared environment is changed.

## Readiness and custody after acquisition

ACQUIRED means hashed transfer, not full S1 readiness. Before S2: decode/validate
the complete BAM/index, reconcile original identities and full forward sequence,
qualities/unmapped records, conflicts/missing sequence and read/base counts.
Duplicates and supplementary placements are not new molecules; recover full
sequence without inventing hard-clipped bases. Compress the extracted read set.
Explain differences from archive counts instead of forcing equality.

Back up completed and failed raw material through writable login-side I/O to
the non-expiring project home, with hashes checked. Scratch expiresOctober22;
keep no sole needed copy there. Large genomic objects never enter Git. Track
small unmodified manifests, complete accounting and outcome here/PROGRESS.
S2–S4 and RNA remain unreleased even if this acquisition succeeds.

## Actual launch and first live snapshot

Job1604251 is RUNNING on hydra-n1/amd_256M with the exact one-CPU/8GiB/4h
allocation. Source files match research commit
`e0727cfb914918e88e9dd92541760a35d207ddf1`; the run uses immutable bundle02,
not a mutable Git checkout. Read-only path preflight1604249 passes the exact
CLI root/new-leaf check and reports55,156,068,581,376B free. Its1s elapsed
and0.132s measuredCPU, plus1604247's1s/0.545s, belong to S0 setup controls,
not scientific outcomes or new genomic-body charges.

At the06:02:40UTC monitoring call, the read journal reaches454,033,408B new
upstream body, cumulative454,230,016B including prior prefixes. A subsequent
stat in the same call observes497,025,024B in the growing partial BAM; these
are sequential live observations, not an atomic size/account comparison.
The full transfer and BAI have not completed. No final hash, integrity,
complete-read count, eligibility denominator or positive/negative is claimed.
Keep the live journal and partial raw on failure; no automatic replacement.

Later:1604251 completes0:0, full body journal reconciles and both whole
objects have verified home custody. See [actual intake result](2026-10-10-hg002-intake-result.md).
Acquisition does not attest full read/index/alignment/phase readiness.
