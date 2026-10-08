# Fixed all-six preparation guards

Status: prospective candidate bundle, NOT execution approval or a booked charge.
Main requested Sol6.1/high; worker requested Luna/max; independent reviewer
requested Sol6.1/high. These requests are not backend attestations.

Use one new ID: `released-caller-preparation-20261008-throughput01`.
All six callers remain fixed in this order: cuteSV, DeBreak, Sawfish, Sniffles,
SVIM, SVPG. This stage prepares their complete files, not scores or truth.
Native and original-REF checks completed previously. They did not validate
the biological denominator. This development route remains a kill-test,
not a publication lead.

## Inputs and allowed transformation

The six recorded files were statted locally on October 8: every size agrees
with the recorded metadata. This is not a new hash or body validation.
No matching caller filename was found within the inspected first three levels
of project scratch; this does not establish absence everywhere on the cluster.
Transfer each exact existing local source once to fresh cluster `inputs/`.
The preparer checks its pinned SHA-256/size before parsing and after preparation.
Do not extract another archive, download another data set, or substitute a source.
The cuteSV input is the previously audited RNAMES-stripped derivative; its
pin differs from the archived member. The other five use their recorded pins.
Keep existing source files and the historical archive.

Only INFO/RNAMES values may be removed from new working copies. Keep its header
declaration. Charge the entire source, including discarded read names.
Retain all other INFO, FORMAT, genotype/phase, QUAL, FILTER, alleles and rows.
Standard multiallelic splitting uses frozen ALT-ordinal identities and existing
whole-field checks. Other ALT genotypes become missing, not reference.
No REF normalization, header repair, truth filter or score is allowed.

## Chosen guards, not observed output sizes

| Guard (same for every caller) | Value |
|---|---:|
| Maximum derived children | 1,000,000 |
| Each annotated/split/derived/sorted/native plaintext file | 128 MiB |
| Each released/native BGZF file | 64 MiB |
| Each tabix index | 4 MiB |
| Remaining sort temporary files | 128 MiB |
| Opaque I/O allowance | 256 MiB |
| Stored output cap including temporary files and 1-MiB report allowance | 948,961,280 bytes |

These are pre-outcome finite guards, not estimated sizes or asserted populations.
The first failure stops the whole preparation. Keep partials and unused slots.
No larger cap, retry, caller omission or selective record drop follows from failure.
Checks occur at phase boundaries. A Linux 128-MiB per-file limit supplements
them, but is not a total filesystem quota or proof of bounded spill peak.
Four-GiB address space and Slurm memory limits are distinct from observed RSS.

## Named byte account

Prior retained charge: 16,208,704,797 bytes. Ceiling remains
68,719,476,736 bytes (64 GiB). No historical reservation is refunded.

One transfer-read allowance: 1,036,400,535 bytes. Metadata/control/staging,
code pins, small logs/reports/copies allowance: 67,108,864 bytes (64 MiB).
The metadata allowance is not permission for extra scientific input reads.

For each caller, reserve three capped source passes including their one-byte
growth/EOF probes, plus 18 weighted plaintext-cap passes, eight weighted BGZF
passes, six weighted index passes and 256 MiB opaque allowance:

```text
caller reservation = 3*(source_bytes+1) + 3,246,391,296
sum of six preparations = 22,587,549,399
transfer + metadata + preparations = 23,691,058,798
retained total after booking = 39,899,763,595
remaining under 64 GiB = 28,819,713,141
```

The protocol's sequential priors include the complete transfer/metadata account
first and then each earlier caller reservation, even if a later caller never
launches. Book the whole bundle once, before fresh staging. Do not book yet.

Reserve a prospective 24-GiB ceiling (25,769,803,776 bytes) for the later
twelve-process, two-arm screen. This is an UNBOOKED margin, not scoring
approval or proof that its as-yet-unreviewed commands fit. It leaves
3,049,909,365 bytes after both prospective ceilings. If the exact screen
cannot fit, stop this route; do not raise 64 GiB or silently change the screen.

Named passes are file-size accounting, not measured physical I/O.
BGZF expansion, parser read-ahead, library/runtime loads, caches and sort
traffic are not directly measured. The opaque allowance is a reservation,
not evidence that these physical bytes were observed or hard-enforced.

## Slots, time and review

One exclusive submission claim; one control process; at most six fixed caller
processes, in the stated order; no replay after an interrupted acknowledgement.
Controls: 60 CPU seconds, 120 wall seconds plus five-second kill grace.
Each caller: 300 CPU seconds, 600 wall seconds plus five-second kill grace.
Wrapper own CPU: 120 seconds; hard limit 300 permits bounded child limits.
Outer process-group KILL at 3,900 seconds; CPU-only Slurm job, one CPU,
4,096 MiB memory and 70-minute scheduler limit. No GPU or unrelated job change.
Reserve 2,400 named CPU seconds including ancillary margin; prior measured
named CPU is 532.662707 seconds. Measure the process tree once; do not add
child or Slurm times twice. This is not total historical project CPU.
Keep a prospective 3,900 named-CPU-second margin for a later reviewed screen:
532.662707 + 2,400 + 3,900 = 6,832.662707, below the unchanged 7,200 ceiling.

Exact code, tests, six protocol hashes, launcher, source-transfer scope,
fresh root and commands require independent review before booking/staging.
Successful local stub tests do not replace exact-stack controls.
The control run must have zero skips/deselections; any failed control prevents
all real caller processes. Review actual completion before preparing any screen.

Collection limits apply to success AND failure, including outer/Slurm outputs.
Before any whole-content read/hash/transfer/readback, stat only the manifest's
explicit small-file allowlist and require regular non-symlink files. Each
preparation JSON must be <=1 MiB; each stdout/stderr/timer/Slurm log <=64 KiB;
durable state <=4 KiB. Total selected content must be <=8 MiB. At most six
content-sized collection/inspection/hash/copy/readback passes fit48MiB, leaving
16MiB of the64MiB metadata reservation for staged code/control/pin/metadata work.
These are named allowances, not measured physical traffic.
Do not read/hash/fetch/truncate oversized or unknown artifacts. Keep them on
the cluster and record size/type/path plus OMITTED_OVERSIZED or UNVERIFIED.
This does not refund their reservation or supply a complete scientific result.
Raw diagnostics are not automatically Git-safe: keep them remote unless fully
inspected within these limits and found free of read names, complete variant
rows or credentials. No source/working VCF/index transfer is in this allowlist.
Archive safe small reports/timers/logs only; no variants or read names in Git.

Cluster metadata at 19:14:55 +07: no account jobs. Scratch expiry:
October 22, 23:02:50 +07, one extension remains. The scope above is new
prospective work; expired or failed historical bundles stay unchanged.
