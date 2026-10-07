# Finite preparation, control findings and execution decision

Date: October 7, 2026. Goal active, publication contribution not established.
The preceding goal turn made verified progress: checkpoint `5e17ff2` was
pushed with the approved truth-header result and pinned synthetic evidence.
Main read the full updated objective and clean worktree before this continuation.

## Close the known controls, not a new source-wrapper phase

Main extended the original synthetic fixture with two identical event rows
that differ only in their unique truth identity, plus a deliberately uncovered
truth target. On the pinned cluster, both arms retain four truth IDs, three
covered truth records and exactly one FN (`truth_uncovered`). One caller
record covers three truth records under the unchanged lenient matching rules.
The complete derived-row multiset survives standard sorting; retained native
rows remain exact. The paired-reader helper now fails on differing stream
lengths or whole rows instead of silently truncating `zip`.

The expanded cluster probe passed. Source SHA-256:
`888c758784fd05ebb2359839b0b6b208cf48a26ea660c24ff74e1ae6977980ff`.
CPU 31.24 seconds, wall 5.09 seconds, peak RSS 95,559,680 bytes. Earlier
fixtures, reports and the initial software failure remain untouched. These
small controls do not prove general tied-coordinate stability or preservation
of real caller inputs. Production invariants must be checked during preparation.

## A real control failure changes the reference-check recipe

Singer (Luna/max requested) supplied a separate synthetic REF and native
type/size probe. Main reviewed it and ran it on the actual pinned cluster.
Its first attempt failed: `norm -N -c e -f` did not reject a deliberate REF
mismatch. Do not use that combination as demonstrated REF validation.

Main made the unsafe combination an explicit negative control and tested the
alternative `norm -c e -f`, without `-N`. The mismatch now fails with a
reference-allele diagnostic. Matched insertion/deletion source bytes and GT/
INFO remain unchanged, but the validation output moves the insertion.
**Discard that output; never score its normalized representation.** The
original eligible-truth representation remains the required analysis input.

The same probe independently changes one INFO field at a time. Incorrect
SVLEN changes native Truvari size, and incorrect SVTYPE changes native type.
The canonical allele plus INFO/native consistency checks reject both. A
truth unit must pass those checks before scoring; no INFO repair is authorized.
The probe helper is synthetic-only, not a general production truth classifier.
Use the existing linear purity classifier for real eligible units.

The revised reference probe passed on Truvari 5.4.0, pysam 0.24.0, bundled
bcftools/HTSlib 1.23.1 and Python 3.10.20. Source SHA-256:
`8824f8d32de814f0e47464b57b502a28d2bcb23d3a2e103a594c08daaa8bde07`.
CPU 7.82 seconds, wall 1.26 seconds, peak RSS 89,776,128 bytes. Preserve the
first failure report/log/script and both successful probe reports outside
scratch-only storage. Small raw reports are committed in the dated audit.
No real reference sequence or truth record was read by these synthetic runs.

## Exact one-pass truth-preparation request

Dirac (Sol6.1/high requested) identified one concrete blocker: both BEDs must
match the truth header exactly before classifying the first body record.
Main added that check. Every autosomal interval needs an exact name with one
unique positive declared length and `0 <= start < end <= length`. Mismatched
names, duplicate/missing lengths or out-of-bounds intervals fail; no aliases
or clipping are permitted. Four new namespace/bounds tests cover both BEDs
and verify zero body records classified on failure.

Main also observed standard gzip read-ahead in a synthetic early-failure test.
Delivered bytes alone undercount decoding before failure. Add a fixed 64-KiB
read-ahead allowance to the full reservation. The pinned CPython 3.10.20 gzip
source uses an 8,192-byte buffered reader and bounded decompressor outputs;
the synthetic spy confirms actual decoded bytes exceed delivered bytes while
remaining covered. Successful complete gzip EOF delivers the whole decoded
stream; failures retain the full reservation, not a claimed measured total.

| Frozen artifact | SHA-256 |
|---|---|
| `analysis/prepare_released_truth.py` | `52e2932521cc1aa580cab5275adc8ab66460e3a16549b87e570112c565b86864` |
| `analysis/released_truth_units.py` | `4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93` |
| `truth_preparation_protocol_v2.json` | `56e94e3ecf4b0ebb161539dba82b6dbf5d0a67b4d4766afedc1a11aac8109138` |
| `truth_preparation_reservation.json` | `da4d88f6f9673672e99548a3c06d0d51c21aa3d3c7bee73e247853973df02d35` |

The earlier unexecuted protocol remains in the record. This request is one
sequential eligibility/preparation pass only: original decoded truth <=1 GiB,
line <=32 MiB, complete identity map <=64 MiB, each BED <=4 MiB, one exact
HG002 sample, single-process CPU <=600 seconds, wall <=600 seconds, Linux
address space <=4 GiB. Reserve 1,082,195,971 bytes beyond the retained
5,220,887,319 bytes: **6,303,083,290 bytes**, below this stage's existing
six-GiB sub-ceiling. Keep full charge after failure or unused capacity.
No reference body, caller body, sorting, matching or refinement is in scope.
Exact-pin independent approval is required before execution. No automatic
retry, metadata-cap raise or partial-denominator interpretation is permitted.

Dirac approved exactly this one pass under the four pins above. All remote
code/protocol hashes matched before execution. The approval excludes real
reference validation, caller-body processing, sorting, matching, scoring,
refinement and the proposed 64-GiB campaign. The command uses inherited Linux
CPU/address-space limits and an outer 600-second timeout with five-second
kill grace. The fresh prepared output is inside the named project directory.
Its outcome must be recorded separately; starting a command is not success.

Final local suite for these frozen code changes: **666 passed, 31 skipped**,
124.16 seconds. Both local pinned-stack integration skips were covered by the
actual cluster synthetic probes. Manuscript consistency passed.

### Actual preparation outcome: failed, attempt closed

The single approved command exited **2**, not a timeout or resource kill.
The complete identity map reached its 67,108,864-byte limit after 376,029
source records. The failure report records 67,108,700 bytes written and
21,305,391 truth bytes delivered; standard gzip read-ahead is separately
reserved. Both BEDs passed their hashes and exact header/bounds checks.
Total BED bytes read were 916,384. CPU was 11.67 seconds, wall 11.86 seconds,
peak RSS 44,625,920 bytes. There was no successful whole-stream EOF inventory.

Partial eligible counts are **not** completed denominators, coverage results
or biological nulls. Do not score the partial eligible file or extrapolate
from this source-order prefix. Preserve both partial files, logs, code,
protocol and raw failure report. The full cumulative **6,303,083,290-byte**
charge remains; no refund or automatic retry. The small raw failure report
is copied byte-for-byte to the dated audit directory.

The independent reviewer confirms a preparation-feasibility failure, not a
biological null. Map overflow occurs after the possible eligible VCF write
but before appending that record's map entry; the partial files therefore
need not correspond exactly. Whole gzip EOF/CRC and final source rehash were
not reached. Neither partial is a scoring input. The review initially noted
the local raw failure report was not yet available at inspection; it has now
been copied into the dated audit as recorded above.

This failed execution closes the approved v2 attempt and activates the
predeclared limit stop. The failure establishes a metadata-output feasibility
limit under this protocol, not scientific inferiority of the hypothesis or
unusable genomic data. A separate high-impact decision is required before
any proposal to amend metadata storage or resume this dataset route. No such
amendment or new biological execution is approved here. The publication goal
remains open; engineering persistence alone is not success.

### Separate high-impact metadata-storage exception decision

After inspecting the real failure report, Dalton recommends exactly one
explicit exception to the recorded stop policy. Main accepts the rationale
conditionally: this output-storage cap is not evidence against the scientific
question, and the observed cost was small. The standalone screen still has
weak novelty; its value is rejecting further investment, not validating a
publication direction. The failed prefix does not select new scientific rules.

The proposed fresh pass keeps every input, ordinal, identity, exclusion,
territory and metric fixed. Amend only the full uncompressed map allowance
from 64 MiB to **1 GiB**, and this preparer's stage ceiling from six to eight
GiB. Retain the full earlier 6,303,083,290-byte charge and reserve another
1,082,195,971 bytes: **7,385,279,261 bytes**. CPU/wall/AS remain 600 seconds,
600 seconds and four GiB. Reserve up to two GiB of new truth/map output storage
plus ten GiB free headroom. Map writes are storage; later rereads need their
own input reservation. No compression path or partial-prefix continuation.

The original v2 attempt remains closed. This exception needs explicit
independent acceptance of the stop-policy change and new code/protocol pins
before execution. It is **not** permission inferred from the prior approval.
One GiB is a final allowance, not a prediction of complete map size.
**Any further failure ends this dataset route**: no second metadata amendment,
compressed fallback, parser redesign, partial scoring or deadline extension.
If the pass completes, move directly toward the fixed October 8 screen under
separate REF/caller/scoring review. No training or publication claim follows.

### Preserve the failed artifacts off scratch

An authenticated `scp -p` copy completed with exit zero into
`/Users/akm/aayushkrm-AlignSSL/data/derived/svpg_2026/2026-10-07-truth-preparation-01/`.
It preserves the two partial files, failure report and run log outside Git;
the remote originals remain untouched. Payload is 67,717,159 bytes. File sizes
match the remote metadata; a separate large-file SHA comparison was not run
and byte identity is not claimed from sizes alone. The files remain unusable
for scoring regardless of transfer success.

For conservative all-read history, add a separate **128-MiB (134,217,728-byte)**
raw-copy reservation without refund. It includes copying these payloads,
not genomic parsing or a rerun. Current cumulative charge is therefore
**6,437,301,018 bytes**, still below the old six-GiB stage ceiling. The original
attempt's immutable reservation/report remain unchanged. If the proposed
exception is independently approved, its additional 1,082,195,971-byte pass
reservation would yield **7,519,496,989 bytes**, replacing the earlier
7,385,279,261-byte projection that preceded this archival copy. Later map
rehashes or rereads need their own reservation. The small ledger is committed.

## High-impact finite direction decision

### Final storage exception: exact-pin approval and preflight

On the next continuation, Dirac (GPT-6.1 Sol/high requested) approved ONE
fresh full eligibility-preparation pass. This is another real truth-body
pass, not merely a metadata read. Its only changed limits are the one-GiB
plain map, one-GiB eligible VCF and eight-GiB stage ceiling. Scientific
inputs, units, exclusions, territories and metrics remain fixed.

| Artifact | Approved SHA-256 |
|---|---|
| Preparer | `e047ec4d644da3b48f0dc80aa21f13c59452a2f79b5f82f8027c67b2dc0c8632` |
| Truth-unit helper | `4c1cf4fc3d98f4cc3e0f136c15d27095730aa1725b951ea607b4684f4ed93e93` |
| Protocol v3 | `4c80c9a589cbea1807fdd885b88eb735738bf8b8414c5e21ea6e47845ea9d5f9` |
| Exception reservation | `57ecc622e621c3e81f921e4bf846949db79eeaf76bb39388602f5970c9932d77` |

Remote code/helper/protocol hashes match. The fresh `_02/prepared` directory
does not exist. Immediately before launch, shared-filesystem available space
was 53,181,628,809,216 bytes, above the required 12 GiB. This does not prove
account quota. CPU/wall limits remain 600 seconds, with five-second kill
grace; Linux address space remains four GiB. Full cumulative charge is
**7,519,496,989 bytes**, retained on success or failure. The v2 failure stays
closed. Any further failure ends this dataset route: no retry, fallback,
cap increase or deadline extension. Approval excludes REF validation,
caller processing, sorting, matching, scoring, refinement and the wider
campaign. A completed preparation is not a publication finding.

Poincare's caller-preparation task stopped at the account usage limit. No
worker-owned code or tests were present in the worktree at reinspection.
The errored worker was closed; no replacement was dispatched to evade the
limit. Main can continue safe, in-scope work already independently approved.

### Actual final preparation outcome: complete, not a scientific score

The approved `_02` command exited zero. It consumed 167.84 user plus 0.37
system CPU seconds (168.21 total), 169.61 wall seconds, and 45,101,056-byte
peak RSS. The complete raw inventory is committed as
`results/data_audits/svpg_2026/2026-10-07/truth_preparation_inventory_v3.json`
(2,784 bytes, SHA-256
`f4ec03f52e7b5a1e7a35459e875ad3d277d49990ad06ab2e62315a085511f808`).
It records successful whole gzip EOF/CRC and source snapshot/hash verification.
All category counts reconcile to 5,497,286 original rows and map entries.
Actual decoded truth plus both BEDs is 300,157,874 bytes; the full reserved
7,519,496,989-byte cumulative charge remains without refund.

| Complete preparation classification | Records |
|---|---:|
| Eligible, current-minus-Tier1 | 1,430 |
| Eligible, current/Tier1 intersection | 10,060 |
| Boundary or mixed territory | 18,377 |
| Ineligible telomeric boundary | 0 |
| Ambiguous base | 25,903 |
| Below minimum length | 992,972 |
| Complex replacement | 3,839,311 |
| Missing or partial GT | 347,264 |
| Out-of-scope chromosome | 195,172 |
| Symbolic or star | 66,797 |
| **Total original rows** | **5,497,286** |

The eligible VCF is 11,853,747 bytes, stream-written SHA-256
`c908217f7ec8eba1efe93f51605675a8a8b9676d9c9ca443d1348ad0a00f68d2`.
The full map is 985,747,356 bytes, stream-written SHA-256
`20301f1c08560c2e767f9f0f4dce991fb3293f00935fa92668c6524505cdb955`.
Both are below one GiB and remain outside Git. These reported hashes were
computed during writing; no independent large-output rehash is claimed.
The source compressed hash was checked before and after the full input scan.

Dirac's independent result review passes **eligibility preparation only**.
The reviewer inspected the inventory, not the large VCF/map or runtime log.
REF and native INFO/type/size validation remain required before these counts
can be treated as a validated scoring denominator. No caller coverage,
accuracy, biological improvement, test-set confirmation or publication finding
has been measured. No real REF/caller/sorting/scoring/refinement is approved.
The last storage exception is used and closed; no additional cap change or
fallback is available for this dataset route.

Local validation for the final code: **667 passed, 31 skipped**, 128.04
seconds. Focused truth/header/unit checks: 81 passed in 0.73 seconds.
Manuscript consistency passed. Requested reviewer configuration was explicitly
Sol6.1/high; backend model execution is not independently attested.

To preserve the complete outputs off scratch, a separate raw-copy reservation
of 1,000,000,000 bytes was recorded before starting `scp -p` into the fresh
local `data/derived/svpg_2026/2026-10-07-truth-preparation-02/` directory.
This covers the VCF, map, inventory and run log only, not genomic parsing or
large-file rehashing. Local available space was 12,360,974,336 bytes, sufficient
for the reservation plus ten-GiB headroom; this is not quota proof. The full
charge becomes **8,519,496,989 bytes**, retained regardless of copy outcome.
Transfer completion and size checks must be recorded separately. Original
remote outputs and both failed v2 partials remain untouched.

The authenticated copy subsequently completed with exit zero. Local sizes
match the recorded remote VCF/map/inventory sizes; the log is 1,524 bytes.
Total payload is **997,605,411 bytes**, inside the raw-copy reservation. The
small copied inventory compares byte-for-byte with the committed inventory.
No VCF/map rehash was performed, so transfer success plus matching sizes is
not claimed as independent genomic byte verification. Local available space
after copying is 11,334,406,144 bytes, above ten-GiB headroom. Nothing was
deleted to make space. The retained charge remains 8,519,496,989 bytes.
The exception reservation's original pending-status field is frozen history;
the exact-pin approval and actual outcome above supersede that operational
status without rewriting its approved bytes.

Fresh post-run `squeue -u igorno` is empty. `ws_list` reports 15 days 11 hours
remaining, expiry October 22 at 23:02:50 cluster-local, one extension. No
project job was cancelled, and no unrelated jobs or private-key contents were
touched. All local/remote final code/protocol pins still match the approval.

Dalton (Sol6.1/max requested) recommends one final fixed development screen
by **October 8**, after essential controls and independent execution review.
Main accepts that conditional recommendation. The source gate is complete;
another broad acquisition or bespoke source-wrapper phase is not justified.
If standard preparation, essential controls or honest bounded accounting
cannot close by the deadline, stop this dataset route and reconsider the
research question. The cheap screen is a rejection test, not a new method.

Prospective aggregate ceiling is explicitly amended from 12 GiB to **64 GiB
(68,719,476,736 bytes)**, retaining every historical charge. Original caller
extraction remains under its four-GiB ceiling and 4,124,617,258-byte charge,
already included in the aggregate. Do not add that charge twice. New campaign
limits: two aggregate CPU-hours, 120 active wall minutes, at most one 90-minute
CPU-only job, and four-GiB RAM for the job and descendants. No GPU/training.
This ceiling is **not proof the campaign fits and not execution approval**.
The preparer's six-GiB sub-ceiling remains unchanged for its one pass.

Before the screen, explicitly reserve actual named derived inputs, size
growth from decomposition, sort/index/hash/result reads, all twelve benches,
reference fetches and read-ahead. `len(fetch())` is returned sequence length,
not BGZF decoded traffic. File size and cached reads do not establish total
I/O. Freeze a defensible finite recipe before outcomes; do not add an open-ended
I/O-monitoring infrastructure project to make this dataset route continue.
POA/refinement remains separate from the first screen.

All eleven original scientific limitations remain: released outputs are not
controlled same-input candidate ceilings; HG002 is development data; exact raw
reads/depth/reference/graph identity is absent; record multiplicity is not
independent biological evidence; geometry coverage is not accuracy; Q100-added
territory is not inherently difficult; truth REF/metadata require validation;
native caller filtering must not change the truth denominator; residuals need
representation/truth/read adjudication; independent donors are needed; and a
distinct useful mechanism is needed before publication or training.

Requested agent settings were passed explicitly. Backend model execution is
not independently attested. Both bounded workers were closed after completion;
the independent reviewer is reused for exact preparation gates. Fresh cluster
queue is empty, scratch expires October 22 at 23:02:50 cluster-local, and one
extension remains. No unrelated jobs or private-key contents were touched.
