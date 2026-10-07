# Validation, local headroom and an inverted smoke-test gate

October 7, 2026. Software findings only. No historical scientific results,
model, metric, threshold or seed changed. DeepSV remains excluded; checking
legacy infrastructure does not select SSL again.

**Latest storage follow-up:** user reported cleaning local space. Measured
15,237,808,128 available bytes (~14.2 GiB), above unchanged 10,770,972,672-byte
guard. Both previously failing headroom checks now pass (1.16s), without
guard changes. Their original failures remain below/in Git. The corrected
actual smoke failure remains unresolved; no post-correction full rerun or
all-green claim. User's cluster preference remains for large compute/data.
[Recovery record](../../results/software_checks/2026-10-07/storage_recovery.json).

## Full suite is not green

Initial full run: **739 passed, two failed, 35 skipped, 397.03 seconds**.
The two failures are existing positive job-supervision tests:

- `test_run_svpg_stage_bounded.py::test_success_records_cpu_memory_and_preserves_logs`
- `test_transport_svpg_standard.py::test_actual_guard_launches_child_with_real_cpu_limits`

An isolated rerun failed both again in 1.13 seconds. Both runtime reports
give `local free-space headroom exhausted`, not a new estimator-control
failure. The first synthetic child exited zero but the supervisor still
correctly recorded incomplete; the second received SIGTERM. Both runtime
report objects are retained in the
[failure record](../../results/software_checks/2026-10-07/headroom_failures.json).
Report objects are transcribed unchanged from the original runtime reports;
the enclosing inventory is a summary, not a raw stdout/byte-identical file.

`df` reports 1,945,112 available 1,024-byte blocks (about 1.85 GiB), below the
10-GiB-plus-32-MiB runtime guard. The project tree is 6.2 GiB, including
5.1 GiB of data; the retained pytest tree is only 16 MiB. No sufficient
project-owned disposable cache was identified. Deleting useful project data
would not safely solve the shortage. No cleanup or guard reduction performed.

Pause large local transfers/staging. Main requested a storage preference;
the user chose **continue on the cluster for now**. Use the cluster for compute
and larger files, checking its storage before each transfer/campaign. Small
local code/tracking updates and paper research remain possible.
This local prerequisite does not block the broad research goal or authorize
deleting unrelated user files. No new cluster job/cancellation follows.

## Boolean gate correction

`test_e2e.main()` returns a Boolean; only its CLI converts that to a POSIX exit
code. Its pytest wrapper used `main() == 0`: **False passed; True failed**.
Main changes only the wrapper to `main() is True`, with four offline regression
cases for True/False/0/1. No underlying pipeline settings or success criterion
changed. The full run above executed and passed the old wrapper: it accepted
an actual False return. Its captured stdout was not printed by pytest on pass;
do not claim a raw initial-run loss/accuracy log. Prior result files are separate and
remain untouched, but earlier overall suite counts are not proof that this
smoke check enforced the intended learning condition.

After correction, the estimator controls, wrapper-convention regressions and
existing headline/field-audit tests pass together: **25 passed, 6.76 seconds**.
Manuscript tables/p-values reconcile with saved results; whitespace check passes.
These do not override the full-suite failures. A separate actual legacy smoke
check uses declared one-thread OMP/OpenBLAS/MKL limits, without changing its
model, thresholds or seed. It **fails** in 278.08 seconds: actual return False,
printed accuracy 0.667 below the unchanged 0.7 criterion. Pretraining loss
drops, but that alone does not satisfy the test. Keep the failure; no tuning,
threshold relaxation or changes to historical benchmark result files.
[Check metadata](../../results/software_checks/2026-10-07/legacy_smoke_check.json)
and [captured stdout](../../results/software_checks/2026-10-07/legacy_smoke_stdout.txt).
This is a tiny synthetic software fixture, not a newly selected research
benchmark or confirmation of a biological effect. The entire suite was not
rerun after the Boolean correction, so do not manufacture aggregate counts
by combining separate runs. Before space recovery, known failures included
the corrected legacy smoke and two environmental headroom checks. The latter
are now cleared by the separately recorded two-test run; the smoke is not.

No full-suite green claim, biological gain, expensive campaign or publication
lead is accepted. Historical stopped-route byte charge remains unchanged.

Independent reviewer Dirac accepted the Boolean repair/convention controls,
did not rerun tests, and required distinguishing report objects from retained
raw stdout/stderr. That wording is corrected above. Main's later actual
corrected smoke failure is recorded separately; not independently replicated.

Cluster follow-up: account queue empty; shared scratch `df` lists
51,599,217,664 available 1-KiB blocks. This is not the user's quota or reserved
experiment space. Workspace expires October 22 at 23:02:50 cluster-local,
15 days 0 hours remaining, one extension. No job launched/cancelled or genomic
transfer. Check destination storage and exact inputs before any later job.
Final focused controls/document tests: 25 passed in 8.05s; manuscript and
whitespace checks pass. Do not combine these with historical full-run counts.
