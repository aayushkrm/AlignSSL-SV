# Field difference localizes to END serialization before norm

October9 cluster-local / October8 UTC. Exactly approved diagnosis
`caller-projection-diagnosis-20261009-01`, CPU-only Slurm **1604205**,
completed once, **0:0**,15s scheduler elapsed. Durable state COMPLETE.
One18-control and one diagnosis slot consumed; no replay or caller scoring.

| Comparison | Complete rows | Rows with projected difference | Observed category |
|---|---:|---:|---|
| Source to annotated | 51,561 | **48,286** | `serialized_END` only |
| Annotated to split | 51,561 | **0** | None |
| Source to split | 51,561 | **48,286** | `serialized_END` only |

Complete standard serialized row-string mismatches have the same three
counts. All rows joined by exact integer source ordinal and singleton integer
ALT1, sampleNULL, exactly one ALT and complete row count. No prefix/subset.
Annotated and split sizes are both31,780,495 and SHA256 both
`21b661d22bc9cab4c4a9f837d25ffc5f77f8a688434159aca930c185777412c2`.
The original29,410,475-byte source matches its prior SHA256
`9603595adebb54e656513c3ffba416e0d2173763030abef20f804e1c877209c1`.
All current input hashes and filesystem snapshots remain stable across the
diagnosis. Partial hashes are new observations, not retrospective proof of
launch-time bytes or kernel sealing.

Exact-stack18 controls passed, zero skips, pytest0.45s. Runtime is pinned
Python3.10.20/pysam0.24.0/Truvari5.4.0/HTSlib andbcftools1.23.1.
Neither the data process nor this review reran norm, preparation, a writer,
sorting, indexing, filtering or scoring. No VCF/sequence/read-name output.

## What this changes

For these current artifacts, the discrepancy is already present in the
annotated file, before norm's output. Annotated-to-split agrees both by
projection and whole-file size/hash. The old error's `norm` phase label
identifies where the preservation condition was tested, not necessarily the
operation that first caused the difference.

The only reported category is the serialized explicit-END token list; `stop`,
coordinates, original ID, REF/ALT, QUAL, filters, other INFO, FORMAT/GT and phase
show no differences under the frozen projection. This does not validate those
fields biologically. The report contains no END tokens or field deltas: it
does **not** distinguish token removal, value or spelling changes. Do not
invent an insertion/deletion subgroup, affected coordinate, or raw-source
lexical equality. No original-failure output hash existed to authenticate
that earlier instant.

The local and exact-stack synthetic Float fragility witness remains true,
but **the real-input diagnosis does not support Float drift as this observed
discrepancy**. Keep that negative hypothesis result. Official formatter source
supports a possible Float mechanism in general, not this field attribution.
The [synthetic END control](2026-10-09-end-serialization-controls.md) passed
locally: ordinary annotation omitted redundant END on two literal variants
while preserving stop and other projected fields. A changed symbolic END
negative control changed stop. Local pysam0.24.1/HTSlib1.24 differs from the
pinned cluster stack; this does not establish the detailed real mechanism.
Production/guard remain
unchanged; the earlier all-six preparation remains CLOSED INCOMPLETE.

This is an engineering diagnosis. H_R remains untested; no truth denominator,
caller performance, biological null, accepted method or publication claim.
Any source-preservation policy change or preparation restart needs a distinct
high-impact value decision and exact independent review, not a forced pass.

## Measured cost and evidence collection

Normal waited outer tree: **12.84 user +0.44 system =13.28 CPU seconds**,
**14.19 wall**, maxRSS **42,416KiB =43,433,984 bytes**, zero exit/signals.
Charge once:543.442707+13.28 =**556.722707 namedCPU seconds**. Timer precision
is0.01s; ledger digits do not add precision. Controls0.54CPU/1.13wall,
diagnosis12.69CPU/13.02wall and SlurmTotalCPU13.316 are descriptive, not
added again. Outer tree is not total project CPU or a kill-path validation.

Retain full320MiB charge, cumulative **40,235,307,915 bytes**, no refund.
64GiB/7200namedCPU ceilings unchanged. Named/cached/opaque physical traffic
is not measured. The future24GiB screen margin remains unbooked/unapproved.

Stat before whole content/hash/copy found13 regular nonlinks totaling
**5,085 bytes**: report1474; control/caller streams, timers, outer and Slurm
logs and55-byte state. All individual/256KiBaggregate caps pass; four stderr
files are empty. Main read all nonempty raw contents fully within caps and
found metadata/counts/checksums/sanitized status only. No genomic data,
credentials, private read names or arbitrary field/value content was selected.
Files are archived in
[`projection_diagnosis01/raw/`](../../results/data_audits/svpg_2026/2026-10-09/projection_diagnosis01/raw/).
SCP9404 completed exit zero; all13 local hashes match the cluster checksum
record in `raw/remote.sha256`. State is flattened from `launched/state.txt` to
`raw/state.txt`; other basenames remain. The new checksum record1095bytes
gives combined local archive**6,180 bytes**. The maintained independent
[reviewer](2026-10-09-projection-diagnosis-review.md) verified all13 hashes,
the complete safe-content archive, counts and accounting. Technical completion
and limited field localization are accepted; cause, guard changes, another
data pass and preparation restart are not approved by that review.
