# Caller preparation: independent RNAMES code review

2026-10-08. ACCEPT the narrow RNAMES implementation at code-review level; HOLD the superseded exact execution candidate pending corrected final pins/controls and archival guards. No source transfer, booking, staging, submission or real preparation is approved.
Requested maintained reviewer configuration: GPT-6.1 Sol/high; actual backend model/effort is not independently attested.
Read FULL current caller utility, original tests, current worker RNAMES tests and historical October 4 outcome protocol. The full goal was read earlier. No original caller/truth/reference body, network, SSH, cluster, install or Git action occurred.

## Observed pins and synthetic verification

| Artifact | Independently observed SHA256 |
|---|---|
| Production utility | `11823ed5692497d837c67e8c81ae26fa7f801f1fb863459cf9f51d3781902969` |
| Original tests | `d9ee4ba61f48837d287df9fff6532a288ba4029c8f6f949789e89e12a46b48e9` |
| Current RNAMES tests | `06265a18a2ad7e147e3d5735e53d14a700cb0c4cf23ed5a26cb02b0ecc3ada4e` |

Ran ONLY these two synthetic test files with existing project `/Users/akm/aayushkrm-AlignSSL/.venv/bin/python`, plugins/cache writes disabled and bytecode writes disabled: 42 passed, 2 skipped in 0.49s. Rehashed the three files afterward; pins above matched.
The old 35-pass/1-skip result is preserved as earlier context, not overwritten by this distinct check. Current local successes use actual local pysam/bcftools plus an explicitly mocked native decision API; both exact pinned-runtime integration cases skipped. No actual cluster-native endpoint was validated.
The worker was editing its test file during review. The first read had contradictory RNAMES-presence assertions in omission mode; a subsequent full read showed the correction `has_rnames and not omitted`, which is the version tested/pinned above. This reviewer edited no worker code/test file and does not report that transient defect as outstanding.

## Accepted implementation

`omit_info_rnames` is optional and defaults to false. The public protocol path requires `type(value) is bool` before runtime/source parsing; integers 0/1, strings and null do not enable it. False/absent preserves the prior policy.
When true, `_annotate` freezes each expected child projection BEFORE deleting INFO/RNAMES from the working record. Only that INFO key is excluded; coordinate, stop/serialized END, REF/ALT, QUAL/FILTER, other INFO, FORMAT, sample labels/order, GT/phase and identity metadata remain in the expectation.
The downstream `_derive` projection uses `_semantic_child(child)` with NO exclusion. Restored RNAMES or changed non-RNAMES fields therefore change the expected-versus-observed projection; the opt-in does not create a general ignored-field escape hatch.
The copied source header retains the RNAMES declaration; deletion operates on record INFO values, not header metadata. Local tests check declaration number/type/description through annotated, split, derived, sorted, released and both native VCF views.
Source/ALT identities still derive from FULL original source SHA, row ordinal and ALT index, including duplicate source IDs or identical ALT strings. Source record/child counts and identity/projection fingerprints remain multiplicity-sensitive; sorting is order-independent, not row-dropping permission.
The released view retains the full prepared child population. The native view is an explicitly filtered/presence-selected subset with partition counts, not another all-row-preserving claim. RNAMES omission adds no FILTER/GT rule or caller-specific exception.
Report records `info_rnames_policy` and removed source-row count. Count means rows with RNAMES removed, not read names, bytes or children. Missing RNAMES requires no synthesized field; strict source/header failures still stop the whole preparation.
The CLI accepts only existing source/output/protocol/hash arguments and emits a small status/count or report-location summary, not source rows. It grants no scientific scope or authority on its own.

## Preservation and accounting limits

“Immutable source” means retained original bytes, no source-write operation, hash/snapshot checks before/after standard parsing and final rehash. It is NOT kernel-sealed source acquisition: the legacy parser reopens the filesystem path. Do not claim absence of transient interference or byte-for-byte parser lexical preservation.
The frozen projection is standard-parser semantic/serialized preservation, including explicit END handling, rather than raw-text equality. Source SHA still covers original text and all RNAMES bytes. Header-copy intent/local tests are not a production fingerprint of every downstream header declaration.
Multiset count/sum/XOR checks retain their disclosed collision limitation. Native reads share parser dependencies; stub decisions and fingerprint agreement are not independent truth, donor identity, phase validity or caller performance evidence.
The historical October 4 rule explicitly allowed RNAMES value omission and required charging discarded bytes. It remains a closed historical screen, not renewed execution authority. Smaller working copies do not discount original source acquisition/parse/rehash or refund any prior charge.
Existing source/protocol readers retain their declared cap-plus-one convention and corresponding source-pass reservation; this narrow change did not modify them. Do not describe this utility as the census/reference strict no-overflow reader. Legacy protocol JSON handling is not the newer exact-key/duplicate-key schema implementation.
Output/sort/native/storage checks remain phase-boundary guards, not enforced spill-peak/disk/physical-I/O measurements. CPU/wall/address-space/disk and all six callers' cumulative budget need exact prospective review; no approval of the draft budget is inferred from these tests.
HTSlib diagnostics and saved failure context are not guaranteed sequence/read-name-free by the CLI summary alone. Freeze safe small-log/report archival limits in the execution bundle; do not commit RNAMES or large genomic outputs.

## Control coverage and disposition

Current RNAMES controls check invalid booleans, >64-KiB synthetic RNAMES omission, absent-policy preservation, original source bytes/hash, header declarations, all seven working VCF views, stable child identities and rejection of non-RNAMES DP corruption. The exact native opt-in case is present but skipped locally.
No explicit negative RNAMES-reinsertion control or separate explicit-false case is in this current new test file; static implementation supports both rules. Freeze adequate final controls/pins before exact launch review, without editing the worker's scope here.
Keep all six fixed callers and the same 11,490 truth units in both later arms; DeepSV remains discarded. This stage prepares transport/native views only: no truth denominator, REF/scoring call, biological outcome, pipeline performance or publication claim is established.
Technical code ACCEPTED at the observed production pin, with the stated preservation/test limits. Only this new owned review note was edited; synthetic tests wrote temporary fixtures only. No real-data read, SSH/network/cluster job, installation or Git action occurred. Exact execution approval remains pending; historical failures and charges are unchanged, and requested Sol6.1/high remains unattested.

## Initial exact candidate: static review completed, HOLD preserved

Read FULL caller-preparation limits note and ALL ten files under `results/data_audits/svpg_2026/2026-10-08/caller_preparation01/`: six protocols, manifest, bundle checksum and both scripts. Flags/approval-reference strings are candidate configuration, not independent acceptance.
Independently verified historical candidate manifest SHA `807290d2086e7c408f278bcd8113bb13c5db9fed3e458a833a2e805e55e14788`; bundle checksum SHA `7936db5d1bb16c191376aff63b59c674ad2630cdb5b1714d1413121915c14fc0`; inner SHA `a5b45c33fc25979b8c8bc519ade2f38310f14ac73b4eff1294f90800a37aae8f`; outer SHA `8a16ae29a84f55054a10a87643ccff42d56201d3c6aafc9147cc2c1fcd4e0cca`.
All six initial JSON hashes match checksum/manifest: cuteSV `22993c13479d0091474bec1436632cba7dbcd4c148a0f02da74ab3526ef081c4`; DeBreak `d4244c542bfedba24f87bacb6a4b6769cbed69d24b7fa7df23b9fa9a2ab417d4`; Sawfish `11eb5a27b3e7bf5cd749bb45e15b02bb2f07a4942db1881e328c01318dfe19ed`; Sniffles `a0e19a4dde554f54e19c24822beb16d3fe3c93dfd1da6b59e46008985464bcdb`; SVIM `db5e1de3f7d93d3b9c3e66b38bc0dca9fe0dca073c1f81efd4e787e2b6d33d7c`; SVPG `d077971fea93cfbe4b311698a5dd7f7a3afcc7192c4dc4aae7b295dcdf899e93`.
Initial staged metadata/code/tests/scripts total 72,379 <131,072 bytes. Initial tests contain 44 collected cases: local observed 42 pass/2 skip is not the required 44/zero-skip exact-stack result; only two cases exercise actual pinned native end-to-end behavior.
The checksum-file argument binds outer execution without a circular script hash. Outer verifies every frozen pin and fresh output/claim paths; inner claims controls and then six callers sequentially. Current CLI argument names/protocol-hash extraction match the utility. Any failure stops all later callers; unknown submission/launch status must not replenish slots.
Outer group KILL at 3,900 seconds and inner foreground timeouts preserve the reviewed grouping pattern. Controls 60 CPU/120+5 wall; callers each 300 CPU/600+5 wall; wrapper soft-own 120 with inherited hard 300. Maximum sequential payload walls 125+6×605=3,755 leave 145 seconds inside the outer limit. This is static containment, not a kill-path test.
The inner explicitly unsets POSIXLY_CORRECT before Bash `ulimit -f 131072`: 1024-byte units give 134,217,728 bytes per regular output file. This supplements phase checks; it is not total disk quota, sort-spill peak control or a 64-MiB hard BGZF limit. Address-space and Slurm memory are distinct.

## Byte/CPU account: accepted arithmetic, still UNBOOKED

All six source sizes sum 1,036,400,535 bytes. Planned transfer scope is exactly one copy of each manifest-named local file to the NEW root's inputs, including full 935,962,599-byte DeBreak; no archive extraction, substitution or extra source hash preflight is part of the candidate.
cuteSV is explicitly the previously audited RNAMES-stripped derivative, not asserted byte-identical to its archived member. Other source pins/sample labels/counts are supplied metadata to be verified by the preparer, not independently re-read here. Generic sample labels are not donor identity evidence.
Per-caller fixed weighted allowance verifies as 18×128 MiB plaintext +8×64 MiB BGZF +6×4 MiB index +256 MiB opaque =3,246,391,296 bytes. Add 3×(source_bytes+1), retaining legacy overflow-probe reservations and every discarded RNAMES byte.
Verified reservations in fixed caller order: 3,334,622,724; 6,054,279,096; 3,323,539,344; 3,291,404,199; 3,266,438,184; 3,317,265,852 bytes. Sum 22,587,549,399; plus transfer 1,036,400,535 and metadata 67,108,864 =23,691,058,798.
Every sequential prior reconciles: first 16,208,704,797+1,036,400,535+67,108,864=17,312,214,196, then full earlier caller reservations. Full retained total would be 39,899,763,595. Unbooked later screen margin 25,769,803,776 leaves 3,049,909,365 below 68,719,476,736; it is not screen approval or proof of its future recipe.
Per-caller storage guard also reconciles: five 128-MiB plaintext +two 64-MiB BGZF +two 4-MiB indices +128-MiB remaining sort files +1-MiB report =948,961,280. Child cap 1,000,000 is a pre-outcome guard, not an observed count or permission to retain a prefix.
CPU payload/own envelope is 60+6×300+120=1,980 seconds; 2,400 reserves 420 ancillary seconds. Prior 532.662707 +2,400 +unbooked later 3,900 =6,832.662707, leaving 367.337293 under 7,200. Charge normal waited outer tree once, not inner/Slurm times twice; abnormal lost accounting retains the reserve and INCOMPLETE status.
Named passes, opaque allowance, remaining sort bytes and per-file guards do not establish physical-I/O or spill-peak enforcement. No refund, old-screen reopening, scoring rule change, caller omission or threshold increase is accepted by this arithmetic review.

## Focused failure-detail correction and narrow pending holds

During review, main withdrew the 44-test execution candidate before any authority/staging/booking. Its pins above are historical only. The interim sanitizer retaining exact built-in ValueError text was insufficient: external parsers/tools can raise that same type with row/read-name context.
Latest production read independently hashes to `f975699c57ec61ac4ab9062ad417623218b867213dbde127937b7b183e1c95d3`: `_need` now raises distinct `CallerPreparationGuardError(ValueError)` and saved report detail is retained ONLY for that exact internal type. All other exceptions, including external built-in ValueError, get category plus fixed sanitized text. ACCEPT this narrow static correction; guard conditions/messages and RNAMES semantics are unchanged.
The raised CallerPreparationError still carries original exception text/cause, and HTSlib can write raw stderr. The approved CLI shape prints only type/report location, but raw diagnostics/tracebacks are not automatically Git-safe. Keep them remote; archived failure reports/logs need the declared safe handling, not a claim that every process stream is sanitized.
HOLD 1: await refreshed utility/test/protocol/checksum/script/manifest pins and exact final control count. Main anticipates explicit-false, RNAMES-reinsertion and external RuntimeError/ValueError controls: 48 exact cases, local 46+2 skipped. At this inspection the worker test file still had the earlier `06265a…` pin; anticipated tests/results are not certified or rerun here.
HOLD 2: final bundle must specify size-check-before-transfer/readback for FAILURE outputs as well as success. Current success guards are 256-KiB controls and 1.25-MiB caller report/log/time bundles; failure branches exit before those aggregate checks, and individual raw logs can reach the 128-MiB file limit, exceeding the 64-MiB metadata allowance. Bound outer/Slurm collection too; no full oversized/raw-sensitive log fetch is implied.
These are narrow pin/control and archival conditions, not a new framework, campaign, strategy loop or request to expand input/resource scope. Frozen scientific caps/account/order remain technically acceptable; execution and all six source transfers remain NOT APPROVED until corrected exact readiness review.
Only this review note changed during static candidate review. No source/FASTA/caller body, SSH/network/cluster read, new synthetic test, installation, booking, staging, submission or Git action occurred; earlier local test history stands. Requested Sol6.1/high remains unattested and old failures/charges are preserved.
