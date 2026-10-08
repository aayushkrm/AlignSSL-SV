# Read-only localization of the stopped caller field mismatch

Candidate dated October9 cluster-local (October8 UTC). The earlier all-six
preparation stage stays CLOSED INCOMPLETE; this is **not a replay**. Main read
the full goal and classified the prior turn as progress: README publication,
preserved failure evidence, and substantive tracking changes. Publication
significance remains unproved. Current status: the corrected exact bundle was
approved, booked and executed once as job1604205. Its slots are consumed.
The [result](2026-10-09-projection-diagnosis-result.md) and
[independent review](2026-10-09-projection-diagnosis-review.md) accept technical
completion only. Prospective and earlier HOLD text below retains the design
history; it does not offer another launch.

## Question and minimal observation

Which fixed field categories differ between the pinned original cuteSV source,
the retained annotated file and the retained split file? The
[local synthetic witness](2026-10-08-projection-serialization-controls.md)
shows that parsed float values can change in ordinary VCF serialization while
standard serialized row text stays identical. This is a hypothesis about this
failure, **not yet its demonstrated real-data cause**.

Read exactly three existing files. Original source SHA must match its prior
pin. Partial hashes were not recorded at failure; first-observed hashes now
cannot retrospectively authenticate their exact launch-time bytes. Check full
size/hash/snapshot before and after parsing; no transient-interference or
kernel-sealed acquisition claim. Join all51,561 biallelic source rows in order
to source ordinal/ALT1 in each partial; mismatch or truncation stops the whole
diagnosis. No subset or alternate source is allowed.

Compare the unchanged production `_semantic_child` projections, independently
of the source-identity fingerprints. Count mismatched rows and fixed field
categories for each of three pairs. Also compare complete standard serialized
row text after the original identity annotations and permitted RNAMES omission
in memory. No row, allele, genotype, coordinate, original ID, read name or
arbitrary tag/value is output. Unknown INFO/FORMAT names map to `OTHER`.
Current input hashes and counts are metadata, not biological scores.

No new norm, VCF writer, sort, index, filtering, matching, scoring, training,
new cohort, source transfer or genomic output. Derived output is not read.
Do not change the old preservation guard to force a pass. This localization
cannot establish the truth denominator or a caller performance result.

## Exact candidate and finite resource account

Bundle lives at
`results/data_audits/svpg_2026/2026-10-09/projection_diagnosis01/`.
Manifest binds production/diagnostic/test/script pins and all input paths.
Independent exact review is required before any booking, staging or data read.
At this note's creation all are **UNBOOKED / UNEXECUTED**.

Input bytes:29,410,475 +31,780,495 +31,780,495 =92,971,465.
Three named passes including legacy overflow probes:
3×(92,971,465+3) =278,914,404. Add32MiB opaque and16MiB metadata =329,246,052.
Reserve full **320MiB =335,544,320 bytes**, including6,298,268 margin.
Prior39,899,763,595 gives prospective40,235,307,915; full64GiB ceiling
unchanged. Future24GiB screen margin remains unbooked/unapproved; even with
it2,714,365,045 bytes remain. No refund after any outcome. Named envelopes
do not measure physical/cached/parser seek traffic.

One new experiment ID `caller-projection-diagnosis-20261009-01`, one exclusive
CPU-only submission, one18-control slot and one diagnosis slot. Controls must
pass18 with0skip on the actual pinned stack; local18pass0.16s is not that.
Controls30CPU/60wall+5; diagnosis120CPU/180wall+5; wrapperown30CPU/hard180;
outer process-groupKILL300wall; Slurm1CPU4096MiB/amd_256M/10minutes/noGPU.
4GiB address-space and128KiB per-file limit are not a total disk quota.
Reserve240 namedCPU:543.442707+240 =783.442707 under7200. Charge normal
waited outer tree once; lost accounting retains its reserve. Inner/Slurm are
descriptive. Process interruptions do not replenish claims or submissions.

All success/failure/abnormal outputs need regular-nonlink stat checks BEFORE
whole reads, hashes or copies: report64KiB, each stream/timer/Slurm16KiB,
state4KiB, selected aggregate256KiB. Six content-sized passes <=1.5MiB
within16MiB metadata. Oversized/unknown outputs stay remote without read/hash/
fetch/truncation; record omission metadata. Fully inspect allowed raw contents
before Git; no assertion that arbitrary parser stderr is safe.

## Decision boundaries

If source-to-annotated differs while annotated-to-split agrees, the mismatch
already exists before norm's output. If standard row strings agree while
parsed fields differ, localize representation precision without declaring the
numeric change scientifically harmless. If norm changes other fields, retain
that result and stop; no automatic normalization workaround. Any outcome
remains an engineering diagnosis of current artifacts, not novelty or a
publication method. Later representation changes or resumed preparation need
distinct value/protocol scrutiny; this bundle authorizes neither.

## Corrected frozen readiness and exact submission command

The first17-control candidate was held before booking/staging/execution.
Reviewer found that `_one` could accept a malformed CTRL_ALTIDX=(1,2) join.
Main now requires exactly one integer ALT index1 and integer ordinal equal to
the source row, and adds an explicit rejection case. Production helper stays
unchanged.18 local controls pass0skip0.16s; these are not cluster results.
Manifest corrects the scheduler field to **partition**amd_256M, not a node
constraint. No scientific or resource scope expands.

Final manifestSHA `37448767b9dfeea81d46991768c178430eae7524fa93f4d64aa164dc4a02e35b`;
bundleSHA `5f9a667b2c16c8123c66c17a6058d03921790a97a37f6ced11820ac061f46e83`.
These replace the unexecuted17-case candidate pins; its Git history remains.
Changed utility/test/inner pins are in the manifest; the outer/production/
serialization test pins are unchanged. Independent exact re-review was pending
at this candidate stage; the appended review records the later ACCEPT.

After exact approval and full booking, use this ONE command from the fresh
root. Create the exclusive submission claim BEFORE sbatch. Failed or unknown
acknowledgement consumes it; reconcile job/log state, never rerun this command.
The explicit checksum argument is outside the checksum-bound manifest to
avoid a circular hash. It must equal the final independently reviewed hash.

```bash
cd /scratch/igorno-alignssl_restart_20260922/caller-projection-diagnosis-20261009-01 &&
mkdir submission.claimed &&
sbatch --parsable --partition=amd_256M --cpus-per-task=1 --mem=4096M --time=00:10:00 --job-name=alignssl-proj-diagnosis --chdir=/scratch/igorno-alignssl_restart_20260922/caller-projection-diagnosis-20261009-01 --output=/scratch/igorno-alignssl_restart_20260922/caller-projection-diagnosis-20261009-01/slurm.%j.log --error=/scratch/igorno-alignssl_restart_20260922/caller-projection-diagnosis-20261009-01/slurm.%j.err --wrap='bash /scratch/igorno-alignssl_restart_20260922/caller-projection-diagnosis-20261009-01/run_outer.sh 5f9a667b2c16c8123c66c17a6058d03921790a97a37f6ced11820ac061f46e83'
```

Command-only review correction: the `&&` chain stops before sbatch if the
directory change or exclusive claim fails. No assumed caller-shell error mode.
All seven bundle pins, resources and scheduler arguments remain unchanged.
