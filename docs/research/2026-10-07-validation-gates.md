# Essential validation after complete truth preparation

Date: October 7, 2026. This checkpoint is software/control work, not a
biological outcome. Prior goal turn made verified progress at `df95a54`:
complete eligibility preparation, backup, preparation-only review and push.
Main reread the full goal and clean worktree before this continuation.
DeepSV remains excluded; no learned method or training campaign is selected.

## Historical finite decision — superseded by STOP

The completed Sol6.1/max-requested direction review retained ONE fixed screen
by October 8 as a final rejection test, not as a publication direction.
Main accepted it conditionally. The later real metadata failure **closes that
screen**; the stop review below is authoritative. The broader publication
goal stays active. The following were historical contingency rules, not a
current launch plan. Zero as-released
union residuals stop recovery investment. Nonzero residuals supply only a
hypothesis list, not validated misses, biological gain or novelty. Known
representation, filtering and benchmark effects cannot establish a distinct
mechanism. Essential controls, exact execution review, 64-GiB aggregate ceiling,
two aggregate CPU-hours and original wall/RAM limits remain required. No extra
amendment, reduced caller panel, I/O-supervisor phase or deadline extension.

## Metadata gate: bounded native interpretation, no repair

`analysis/check_released_truth_metadata.py` reuses the existing linear allele
classifier. It requires exact signed SVLEN, SVTYPE and native Truvari size/type
agreement for every prepared row. Missing/partial/ref-only GT and unsupported
alleles fail the whole gate. It checks full-row pairing/cardinality, unique
64-hex truth IDs, exact sample HG002 and the frozen stack. No row is repaired,
discarded or normalized. REF and scoring are outside this scope.

Independent code review found a protocol hash/reopen race and mutable parser
inputs. Main fixed them before real execution. Parse the same bounded protocol
bytes that were hashed. Read the eligible plaintext once, cap at 16 MiB,
hash the payload, and feed both standard parsers separate opens of a Linux
anonymous memfd sealed against WRITE/GROW/SHRINK before parsing. Original input
is rehashed and its stat snapshot checked afterward. This is an immutable
bounded input buffer, not a new source parser or generic I/O supervisor.

The reviewer accepts a prospective **65-MiB** named-read reservation: two
original-input passes, two ≤16-MiB parser passes, plus small metadata and
overflow probes. It is conservative accounting, not measured opaque C I/O.
The exact real-data reservation was subsequently approved and charged in full;
its failed execution is recorded below. No refund is made.

## REF utility: one complete sequential reference pass

Historical unapproved proposal only. After the metadata failure, no real REF
driver, scan or new I/O work will follow for this closed dataset route.

`analysis/check_released_truth_reference.py` reads standard gzip/BGZF FASTA
to EOF and checks every original anchored REF against the pinned reference.
It does not normalize variants or perform random faidx/BGZF requests. It
retains one contig and bounded queries. Limits are hard and typed: decoded
FASTA ≤4 GiB, contig ≤256 MiB, query count ≤30,000 and aggregate REF bytes
≤16 MiB. Every FAI contig/length must appear exactly once; duplicate/unknown/
missing contigs, bad sequence grammar, bounds, REF mismatches and CRC errors
fail. The future driver must reject duplicate FAI rows before constructing
the dictionary and pin/recheck all scientific inputs through completion.

The result counter is delivered decoded bytes, with a separate 64-KiB
read-ahead allowance needed for failure accounting. The current function is
an unapproved utility, not an executable real-data protocol.

Main's earlier six-GiB reference proposal included two compressed hashes but
did not explicitly count the encoded gzip input consumed during decoding.
For conservative all-named-read accounting, propose **seven GiB**, still
inside the unchanged 64-GiB aggregate ceiling: three ≤892,326,179-byte
encoded passes, ≤4-GiB delivered decoding plus overflow/read-ahead, three
≤16-MiB eligible-truth passes, and small FAI/code/protocol reads. This fixes
a prospective accounting omission before execution; no six-GiB real pass
was approved or started. Do not claim file cache, returned sequence lengths
or `time` filesystem counters establish exact decoded traffic.

## Synthetic validation state

Local focused tests: **35 passed, two skipped** in 0.31 seconds. The skips
are the exact cluster-stack native endpoint controls. Tests include positive
and conflicting metadata, phased GT, byte caps and protocol race; REF line
crossing/overlap, all-contig completion, bad dictionaries/bounds, limit overrides,
query caps and corrupt trailing gzip-member CRC. No real sequence was read.

An earlier full suite ran during development: **694 passed, 33 skipped** in
153.40 seconds. It predates the latest bound/race fixes and resumed worker
tests; it is not final validation of the current worktree.

The original `_01` cluster staging contains earlier unexecuted candidate
source files; preserve them. Pytest 8.4.2 and its dependencies were installed
only into `_01/test_deps`, not into the scientific conda environment. Current
files were copied to fresh `_02` and all five SHA-256 pins matched before
starting synthetic-only pytest under CPU 60s, wall 120s/five-second kill grace
and four-GiB address space, with plugin autoload/BLAS threading disabled.
No real truth/BED/caller/reference source is opened by these tests.

| Historical `_02` synthetic source (failed below) | SHA-256 |
|---|---|
| Metadata checker | `7b355cadba7d8d6961e76ad99051dbddcc1840f6fc22e9a51e53c95cf059f774` |
| Reference utility | `72155ac81968fb83db370613da54d3aa18efca11abf77780e9a49039af7cf0a4` |
| Truth-unit helper | `4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93` |
| Metadata tests | `8704eaf959c68c0d1b1c50c914f0efd4918106ca5eddf6ffd0c3600dffb64166` |
| Reference tests | `232c4f36f69ce8bc742ad029fb727e2b797f76bfa1e8265bc217f2a6efbce3a9` |

The `_02` command exited **1**: 35 passed, two native endpoint failures.
Both stop before parser opening because the pinned Python build does not expose
`os.memfd_create`. CPU 0.61s, wall 1.28s, RSS 45,694,976 bytes. Preserve its
raw JUnit, stdout/log and sources; no real scientific input was opened.
This is an API-binding compatibility failure, not a biological null or an
observed metadata contradiction.

Read-only host inspection finds Linux 5.14.0-362.24.1.el9_3.x86_64 and glibc
2.34. The standard libc `memfd_create` symbol exists; Python's memfd and fcntl
sealing names are absent. Host UAPI headers verify flags CLOEXEC=1 and
ALLOW_SEALING=2, ADD/GET seals=1024+9/10 and sealing bits=1/2/4/8.
Cluster `rg` is unavailable, so `grep` retrieved these exact definitions.

Main uses the same standard Linux API through a typed libc call, checking
errno and the returned seal mask. No architecture-specific syscall number,
scientific Python upgrade, unbounded disk/parser fallback or changed scientific
rule. A new synthetic test checks kernel write denial, unchanged bytes and
independent positions of two opens. The API is documented by the primary
[Linux man-pages](https://man7.org/linux/man-pages/man2/memfd_create.2.html).
This documentation supports the API, not proof of cluster endpoint success.

Fresh `_03` keeps the revised code separate from `_02`. Its synthetic run
must use a project-specific fresh pytest base directory, the same limits and
isolated test dependencies. Revised local controls: **35 passed, three skipped**
in 0.18 seconds (Linux seal control and two pinned native endpoints).
Metadata source SHA-256:
`8b4acc8fa8b9a86d71c9847dd3a175e6816f24a1e2827f231ddf6cf244a05fa0`;
metadata tests:
`65ffd119d382eaba1c3101d4736d3c89d66c707b67b5300b6c6aefffda3e4f67`.
Reference source/tests/helper remain at the `_02` pins above.
Execution start is not success. Real metadata/REF/caller/sorting/scoring/
refinement remain unapproved.

### Actual revised pinned-control outcome

Fresh `_03` exited zero: **38 passed** in 1.36 seconds. CPU 1.08s, wall
2.08s, RSS 98,230,272 bytes. Kernel write denial and independent opens passed,
as did both real pinned-Truvari endpoints: valid metadata accepted and signed
SVLEN contradiction rejected without report/source mutation. The last helper
pin was also checked remotely. Failed `_02` and unexecuted `_01` stay preserved.
This proves these synthetic controls on this stack, not real REF/metadata.

Before copying the failed source and six small raw logs/reports off scratch,
main recorded a separate one-MiB conservative archival reservation. Full
retained charge is **8,520,545,565 bytes**; no real genomic input is parsed
by this preservation step. SCP completed successfully. Local stat confirms
all eleven expected files and **64,891 bytes** total: six small raw reports/logs
and five failed-source/helper/test files. File sizes match the recorded sources;
no new independent content-rehash claim is made. These backups are outside Git
at `data/derived/svpg_2026/2026-10-07-validation-controls/` in the workspace.

Next requested real scope is **metadata only**, before committing a whole
reference pass. `truth_metadata_protocol_v1.json` pins the complete eligible
VCF and unchanged classifier, exact native stack, 11,490 records, HG002, CPU
60s/wall 120s plus five-second kill grace and four-GiB address space. Its
65-MiB reservation would give **8,588,703,005 bytes** retained on success or
failure. No REF, BED, caller, sorting, scoring or refinement is included.
The artifact's true approval flag is an executable request configuration,
NOT independent approval; its pending exact-pin status remains. Do not run
it before the reviewer approves its exact hash and launch recipe. No automatic
retry, silent repair, selective record drop or partial-denominator use.

### Exact approval and actual metadata failure

Dirac (Sol6.1/high requested) approved ONE metadata-only pass under protocol
SHA-256 `008c6a5d7516359cd8c6c5f25dfea8dc29b4a01dbf1a113dc5cccdcc09fdb12b`,
checker `8b4acc8fa8b9a86d71c9847dd3a175e6816f24a1e2827f231ddf6cf244a05fa0`
and helper `4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93`.
Main verified all three remote pins and fresh report/stdout/log paths before
launching once with the exact proposed CPU/wall/address-space/thread limits.
The protocol's pending-status field is preserved as frozen request history;
the separate reviewer response, not that flag, supplies execution approval.

The real command exited **2**: `SVLEN contradicts canonical signed allele length`.
CPU 0.66s, wall 1.27s, peak RSS **99,201,024 bytes**. No success inventory was
created. No failing identity or checked-record count was emitted; do not infer
either or call this an exhaustive metadata audit. Failure occurs before the
final source rehash/snapshot check, which therefore is not claimed.

The full retained charge is **8,588,703,005 bytes**. The zero-byte stdout and
1,581-byte raw log remain untouched on scratch. The exact raw log and controller
summary are preserved in `results/data_audits/svpg_2026/2026-10-07/` as
`truth_metadata_command_run_v1.log` and `truth_metadata_failed_v1.json`.
Retrieval of the 1,581-byte log and its small size/hash metadata uses the
existing ≤one-MiB small-metadata component of the approved 65-MiB reservation
(four ≤16-MiB truth/parser passes plus one MiB). No additional genomic-source
read, new reservation, refund or measured opaque C-traffic claim is made.
No repair, record drop, automatic retry, REF check, caller preparation, sorting,
matching or scoring follows this failure. There is **no validated denominator**.
It is not a caller coverage result, biological null or proof of source corruption.
Whether this reflects source metadata semantics or an overstrict frozen
canonical rule is unresolved. The reviewer is checking the stop response;
any read-only diagnosis is a separate scope, not permission to retry this gate.

### Independent stop review and main decision

Dirac confirms that the failure closes the **fixed released-callset screen**
under its recorded any-further-failure stop rule. Main accepts this decision.
No REF pass, real caller preparation, repair, selective dropping, rerun or
scoring should follow. The failed contract is not proof of malformed truth.
For the offending row, eligibility and SVTYPE checks passed; native size/type
checks were not reached. Missing metadata, parsed type, sign convention and
magnitude mismatch remain possible explanations. No one cause is asserted.

The reviewer says record-level diagnosis is **not essential to STOP**. Main
does not request or run another genomic-source read merely to name the row.
Its optional proposed 16-MiB closeout read is unapproved and uncharged. It
would not reopen this route. Keep the complete prepared inputs, original
sources, failure logs and all reservations for reproducibility.

The wider publication objective remains active. The next step is a fresh
comparison of testable research questions and label feasibility, not more
pipeline work to rescue this screen. DeepSV remains excluded as a foundation;
SSL, the current task, dataset and architecture remain optional.

The final evidence-only reviewer rechecked exit/resources/accounting and
claim boundaries. The raw log was explicitly force-added because `*.log`
is ignored; it is tracked at checkpoint `e81765ea2ec8828209ea9fabe10b58fef03c1716`,
whose pushed remote hash matched. The reviewer’s pre-staging untracked-log
finding is resolved, not dismissed. Its request to mark the opening decision
and older “current” captions historical is addressed here and in the trackers.

Post-run `squeue -u igorno` is empty. Scratch expires October 22 at 23:02:50
(cluster-local), with 15 days/10 hours remaining and one extension available.
No unrelated job was affected or project job cancelled.

## Agent availability

Main's fresh account tool reports ordinary use permitted, 17% five-hour and
3% weekly consumption. This is not Luna-specific availability. The same
Luna/max worker was resumed once on its original caller-preparation task and
disjoint two-file scope; no model substitution or reset credit. Main owns only
the two truth-validation modules/tests. Requested reviewer remains Sol6.1/high.
Requested overrides were passed explicitly; backend execution is not independently
attested. The decision agent was closed after its completed review.
The caller worker later completed the two-file synthetic implementation; main
reviewed it and resumed the SAME worker for one explicit redundant-END
preservation control. It is not approved for real caller preparation. BGZF
decoded-traffic and sort-spill bounds remain unresolved, in addition to the
failed truth gate. A separate Luna/max-requested literature sidecar compares
other questions without reading real genomic inputs or launching compute.

### Caller implementation handoff: synthetic only

The SAME Luna/max-requested worker completed
`analysis/prepare_released_callers.py` and `tests/test_prepare_released_callers.py`.
Main read and integrated both files. Parent/source/ALT identities, dot-mode GT
projection, all-field/multiplicity checks, original-ID retention, sort/index
boundary preservation and caller-only native views have synthetic controls.
Main found that `.stop` alone cannot detect loss of redundant explicit END.
The bounded follow-up fingerprints END presence/value from standard-parser
serialization separately from `.stop`; controls reject unchanged-stop removal
and malformed/duplicate serialized END tokens. No custom source parser.

Worker reports **35 passed, one skipped** locally. The skipped exact native
endpoint is not claimed passed. Local standard writing removes redundant
nonsymbolic END; the new test correctly fails closed, not repairs or ignores it.
Raw lexical normalization by the standard parser is not checked. Source pin:
`c994fd930f631adb8538a063774648894f2dc5f0ee87ffd77beca5757f2d7804`;
test pin `d9ee4ba61f48837d287df9fff6532a288ba4029c8f6f949789e89e12a46b48e9`.

Decoded BGZF traffic, sort-spill peaks and external hard storage enforcement
remain unresolved. No real caller protocol was approved or run. After the
truth failure this work is archived infrastructure, not the next action for
this stopped screen. The worker was closed after its handoff.

## Final software verification at this checkpoint

Main's combined focused run passes **70 tests, four skipped** in 0.71s.
Full local suite passes **737 tests, 35 skipped** in 120.58s. Manuscript
consistency passes: tables/quoted p-values reconcile with historical results.
These are code/control checks, not validation of real REF, caller results,
the failed truth denominator or publication readiness. Skip scopes remain
explicit; no local skipped native endpoint is counted as passed.

The fresh question comparison uses Exa Search and Life Sciences Literature
Entrez, including the [mosaic-identifiability triage](2026-10-07-mosaic-identifiability-triage.md).
No new question is accepted merely because it avoids the closed dataset route.
