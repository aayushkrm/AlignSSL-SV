# Caller preparation stopped at the first real input

October 8, 2026. Experiment `released-caller-preparation-20261008-throughput01`
ran once after [exact independent approval](2026-10-08-caller-preparation-review.md).
One CPU-only Slurm job **1604204** failed with exit **2:0** after 12 seconds.
No later caller ran. No matching or scoring ran. This is an incomplete
engineering stage, not a biological null or a test of the research hypothesis.

| Step | Observed result |
|---|---|
| Frozen bundle | All 11 entries, manifest and bundle pins matched before launch |
| Source transfer | All six sources copied once; sizes matched; original sources retained |
| Exact-stack controls | **48 passed, zero skips**, pytest 2.29 seconds |
| First caller, cuteSV | Source hash matched; **51,561 records / 51,561 children** |
| `norm` preservation gate | Failed: `norm source ALT identity/projected whole-field multiset differs` |
| Subsequent callers | Not launched; first-failure stop kept |
| Scientific outcome | H_R untested; no validated denominator, score or publication result |

## What the failure establishes

The failure report names `CallerPreparationGuardError` at phase `norm`.
The source and derived ALT-identity fingerprints agree, as do their counts.
The projected whole-field multiset check does not agree. Matching identities
are therefore insufficient to establish preservation of all other fields.
The cause of the field difference is **not diagnosed**. Do not infer a
rounding, END, RNAMES or source-corruption cause from this report.

The first source is 29,410,475 bytes. Its verified SHA-256 is
`9603595adebb54e656513c3ffba416e0d2173763030abef20f804e1c877209c1`.
Source posthash and final derived hashes were not reached. The other five
source hashes were not checked by their preparers because those never ran.
Sorting, indexing and native whole-row checks were not reached.

Partial files remain on scratch: annotated and split files are each
31,780,495 bytes; the derived file is 34,283,269 bytes. These are size
observations only: **no post-failure content reads or hashes**. Do not treat
them as validated outputs or transfer them to Git.

## Resource record and finite disposition

Full reservation **23,691,058,798 bytes** was booked before staging. Retain
the cumulative **39,899,763,595 bytes**, with no refund. The 64-GiB ceiling
is unchanged. The future 24-GiB screen margin is unbooked and not permission
to execute a screen. These are named accounting envelopes, not measurements
of physical, cached or opaque I/O.

The raw cuteSV report's `prior_global_charge_bytes`17,312,214,196 and
`reserved_charge_bytes`3,334,622,724 describe the frozen sequential caller
account. They do not replace the full six-caller reservation booked before
launch or permit a refund for the five unlaunched callers.

The normally waited outer tree used **9.92 user +0.86 system =10.78 CPU
seconds**, **12.56 seconds wall**, and max RSS **99,636 KiB =102,027,264
bytes**. Charge this once: 532.662707 +10.78 =**543.442707 named CPU
seconds**. Timer precision is 0.01 seconds; ledger digits do not increase
that precision. Slurm TotalCPU 10.813 and inner timers are descriptive, not
additional charges. This is not total historical project CPU. A normal
error exit does not test timeout or kill-path containment.

Submission and control slots are consumed. The first caller slot was claimed;
the remaining five were not used. The **whole preparation stage is closed
incomplete**, so unused slots do not authorize selective continuation, a
replay, a cap increase or another submission. Preserve all six callers in any
later scientific comparison. A new bounded source-field diagnosis, if useful,
requires a distinct reviewed scope and budget. Do not remove a preservation
check merely to let the pipeline pass.

## Small evidence archive

Thirteen selected regular, nonsymlink files total **7,233 bytes**. Stat checks
preceded content reads, hashing and transfer. Each file fits its per-file cap;
the total is below the 8-MiB collection cap. Main inspected complete nonempty
contents: only pinned paths, checksums, counts, sanitized failure text,
runtime/timing metadata and state are present. All stderr files are empty.
No genomic records, read names, source VCFs or credentials were selected.

Raw artifacts are in
[`caller_preparation01/raw/`](../../results/data_audits/svpg_2026/2026-10-08/caller_preparation01/raw/).
SCP session37394 completed with exit zero. All 13 local SHA-256 hashes match
the cluster hashes saved in `raw/remote.sha256`. Cluster `launched/state.txt`
is archived as `raw/state.txt`; the failure report is archived at the raw
folder root. The remaining basenames are unchanged. Main read the complete
failure report and three timers locally after hash verification. Independent
result scrutiny is pending, not inferred from the earlier launch approval.

The exact launch approval remains an engineering approval only. The broad
research goal is active and unachieved; no publication lead is established.
