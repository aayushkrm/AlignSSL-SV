# Independent finite review: Tier2 run02 capacity amendment

16 October 2026, Asia/Tomsk. Requested Sol6.1/high is not independently
backend-attested. Read the full attached goal and the prior pivot review,
including its acceptance of the prospective storage correction. This review
owns only this note. Scope: the current collector/test diff and run02 script
against run01. No literature search, cluster access, job action or Git write.

Decision: APPROVE the inspected change for one bounded run02 attempt. No
blocking defect found. This approves the capacity implementation, not a study
result or a further campaign. The old S10 study STOP remains in force.

The collector diff adds positive integer storage parameters and records their
values in the manifest. Existing defaults remain 128 MiB per BAM and 1 GiB
for the collection stage. The CLI accepts only the original 128/1024 pair or
the explicit 512/2048 pair; it rejects a mixed pair and selection-mode
overrides. The changed checks use these parameters. Source access, selection,
record identity, grouping, event association and native thresholds do not
change. The 50,000-record cap, 300-second soft limit, 64 KiB BGZF allowance,
32 MiB metadata cap and sort memory setting remain unchanged.

Run02 uses a separate leaf and passes both storage flags. Shell failure stops
execution before native study classification. The collection gate requires
COMPLETE, complete fetch, complete grouping, stable source stats and 53 event
rows. In the inspected collector, complete fetch requires EOF in every planned
window; complete grouping requires group-stream EOF. Plan validation and window
construction are unchanged. Thus the gate does not authorize classification of
the failed prefix. The supplied frozen selection remains 53 rows, 59 windows
and 3,692,176 bp; I did not regenerate or independently attest its retained bytes.

The script checks the whole leaf against 2 GiB minus 64 MiB before native work
and against 2 GiB after report parsing. It keeps the 32 MiB native-report check.
These are sampled storage checks, not hard quotas, and cannot guarantee peak
temporary use or completion. The native command, controls, default settings
and pinned executable SHA256 beginning 0499 are unchanged from run01. The
native-helper file is unchanged in the diff. The capacity amendment does not
increase RAM or time: the accepted envelope remains one CPU, 2 GiB RAM and
15 minutes. Scheduler booking itself was not inspected here.

Independent local verification: all 10 tests in
`tests/test_tier2_geometry_screen.py` passed with the specified project Python,
bytecode disabled and pytest's cache provider disabled. The added equivalence
test preserves sorted SAM records, group bytes, window and event censuses, and
record/time bounds under both capacities. The CLI rejection test passed.
`bash -n` on run02 and `git diff --check` on the collector/tests also passed.
Tests used temporary synthetic data; only this tracked review note was written.

Run01 evidence is supplied by main, not independently re-audited here: job
1604877 failed with exit 2 before any study classification; 44/59 windows
reached EOF, with 16,469 fetched and 16,448 unique records. Reported bytes:
raw BAM 134,770,508; sorted BAM 136,523,769; groups 5,334,340; manifest 59,460.
Reported charges are 59 allocated CPU-seconds, 55.094 measured CPU-seconds and
207,084 K MaxRSS. Main reports fresh full HOME/SCRATCH byte comparison and four
validated hashes. Those custody checks remain main's evidence. Preserve the
failed attempt, unchanged source/prefix and both attempts' charges separately.

The roughly 80-second/180-MB-per-BAM linear estimate is a planning estimate,
not a guarantee. A 512 MiB BAM guard and 2 GiB leaf allowance address retained
disk capacity; they do not establish RAM demand. No study classifications were
available to tune against. Any run02 failure remains incomplete and releases
no automatic retry. Native flags alone establish neither false artifact labels,
true inversion support nor caller failure. The actual complete packet still
requires independent result review; this reviewer role remains available for it.
