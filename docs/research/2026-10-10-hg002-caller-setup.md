# HG002 native DNA caller setup — routine S0, UNBOOKED

Prepared 2026-10-11 after interruption. Requested Luna/max is not backend/effort evidence. Main owns review, frozen upload, execution and custody. Only this note and [setup_hg002_dna_callers.sh](../../scripts/setup_hg002_dna_callers.sh) are owned here. No source-read restart, worker job, genome/reference body read, download of an archive/executable, install, Git operation, or S2 release occurred.

## Actual state and primary metadata

Recovery checked the actual repository working directory and both paths: both were absent. No earlier file edits or live tool cell needed recovery. Firecrawl is exposed through its plugin, not a CLI. Its two author release-page fetches succeeded, but GitHub's asset panels showed loading errors and omitted names/sizes/digests. This was a page-content failure, not a plugin authentication failure. Official GitHub JSON/text provided the missing fields. The tag release API fields below were checked again on recovery; no asset body was fetched.

| Tool | Official tag / documentation commit | Direct release asset, API identity and exact bytes | Author-release API digest |
|---|---|---|---|
| pbmm2 | [v26.2.0](https://github.com/PacificBiosciences/pbmm2/releases/tag/v26.2.0), published 2026-06-30T19:36:50Z; commit `c0ebc3301a6978c453bc87ecc482eb0de40b9367` | [`pbmm2`](https://github.com/PacificBiosciences/pbmm2/releases/download/v26.2.0/pbmm2), release347060712 / asset462459777; **5,962,520 B** | `sha256:f8a583d27a6232706c8ffe31dab3e52815455032517e9c1399940d4a3ea612bc` |
| pbsv | [v2.11.0](https://github.com/PacificBiosciences/pbsv/releases/tag/v2.11.0), published 2025-02-26T16:13:25Z; commit `a99dfd9b8dfe91f9c2ad2024f2ba02ea157923e5` | [`pbsv`](https://github.com/PacificBiosciences/pbsv/releases/download/v2.11.0/pbsv), release202591571 / asset232792914; **9,756,600 B** | **null / UNKNOWN**, not an invented hash |

Evidence: author [pbmm2 tag API](https://api.github.com/repos/PacificBiosciences/pbmm2/releases/tags/v26.2.0) and [pbsv tag API](https://api.github.com/repos/PacificBiosciences/pbsv/releases/tags/v2.11.0). Each API lists one uploaded `application/octet-stream` asset. GitHub's two automatic source archives are not selected. These are direct binaries, not archives; no extraction or compilation is needed. The API does not encode ELF architecture or establish node compatibility. Actual Linux x86-64 ELF format, SSE4.1, dynamic dependencies, version/help remain main's executable controls.

Exact selected payload total: **15,719,120 B**. First-execution observed asset SHA256s are **UNKNOWN here**. The script records the author-release API SHA and observed SHA in separate columns; pbsv's author column stays `NULL` even after a successful transfer. The GitHub digest field is not a separately author-signed checksum. TLS + byte count + first observed SHA does not manufacture an author checksum, signature, reproducible-source build or published-call identity.

## Licenses and source boundary

Both checked tag LICENSE files contain BSD-3-Clause-Clear-style terms: copyright/conditions/disclaimer must accompany binary redistribution, endorsement is restricted, and no patent license is granted. The script embeds and retains each complete text (different copyright years), so custody does not leave the binaries without their notices. No additional binary-bundled license can be inspected before downloading it; this packet records the author's repository license evidence, not a legal or dependency-license audit.

| Primary text | GitHub text-blob SHA (not a binary SHA256) |
|---|---|
| [pbmm2 v26.2.0 LICENSE](https://github.com/PacificBiosciences/pbmm2/blob/v26.2.0/LICENSE) | `2bcaa371a4e7ef8083189468f18da18eeb502d0f` |
| [pbsv v2.11.0 LICENSE](https://github.com/PacificBiosciences/pbsv/blob/v2.11.0/LICENSE) | `736c7ba1f074d9882dc6e19403ce82cdfe16a79b` |
| [pbmm2 v26.2.0 README](https://github.com/PacificBiosciences/pbmm2/blob/v26.2.0/README.md) | `a1b484e21dfc5722bbb3063914454e4c7a666069` |
| [pbsv v2.11.0 README](https://github.com/PacificBiosciences/pbsv/blob/v2.11.0/README.md) | `93dec00c8ac80d457d0acda55a47ea22cff0f044` |

README headings lag their tags (pbmm2 says26.1.99, pbsv says2.10.0). pbmm2's changelog says public source updates stopped while binary releases continue. A tag's documentation commit is not proof of the binary's build-source identity; the manifest calls this field `documentation_tag_commit`. No source-build fallback for these exact modern versions is asserted. If author assets cannot be fetched, use only verified retained **same assets**, or stop INCOMPLETE. No package/version substitution, source archive acquisition or dependency install is automatic.

## Bounded script contract

```text
accepted remaining S0 ledgers + absent scratch leaf + exact Slurm allocation
  → author HTTPS asset once OR explicitly verified retained asset
  → exact length / available author SHA / distinct observed SHA
  → local private bin paths + license + ELF/ldd + version/all helps
  → closed logs + final status/exits + all-file SHA manifest
  → main's verified non-expiring home copy; no caller launch
```

Default exclusive scratch leaf:
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/hg002_dna_callers_s0_20261010_01`.
An explicit `--output` may name another absent two-digit attempt leaf under that exact resolved parent. Existing directories, files, dangling symlinks and aliased parents are refused. No failed leaf or shared environment is overwritten. Binaries stay under this leaf's `bin/`; no PATH or compiler/shared-environment edit.

SBATCH headers request **one node/task/CPU, 2GiB, five minutes, no GPU** in `amd_256M`. Script checks Slurm's actual `scontrol show job --oneliner` record for those exact limits, and rejects GPU TRES. This is a prerequisite, not a submission. Unexpected scheduler formatting fails closed; main must retain/inspect the record, not fake environment fields. It also requires Linux x86_64 and SSE4.1. CPU/node checks cannot make an unknown binary compatible.

A shared270s start/timeout budget limits new probes and online transfers. Copying, hashing and finalization do not have separate timeout wrappers; Slurm's300s hard allocation bounds the whole job. Each online asset has one curl process, TLS verification, HTTPS-only redirects (at most3), `--retry 0`, 20s connect and at most120s total, shortened by the remaining shared budget. Exact `--max-filesize` is that asset's API byte count; exact retained length is checked again. No auto-retry, failover or redownload after a mismatch. Preserve every partial and curl metrics/exit/stderr on failure.

Online mode requires **curl ≥8.4.0**. The author's [8.4.0 max-filesize documentation](https://github.com/curl/curl/blob/curl-8_4_0/docs/cmdline-opts/max-filesize.d) states earlier versions do not enforce this limit when size is unknown before transfer. This is not permission to upgrade curl. An older/missing curl requires main to prepare a separately verified retained cache through a new bounded action, then freeze offline mode. Native setup does not silently fetch extra dependencies. Software-body reservation is128MiB, not an assertion of measured wire traffic; exact successful selected payload is15,719,120B. Curl's reported bytes/redirect/time fields are retained; TLS/proxy/HTTP overhead is not a measured physical-network account.

Online arguments (placeholders are unresolved main ledgers, not runnable numbers):

```sh
bash /ABSOLUTE/FROZEN/setup_hg002_dna_callers.sh \
  --remaining-s0-cpu-seconds REMAINING_ALLOCATED_SECONDS \
  --remaining-s0-body-bytes CONSERVATIVE_REMAINING_BYTES \
  --external-s0-reserved-bytes ALL_OTHER_S0_RETAINED_AND_RESERVED_BYTES
```

Offline reuse adds `--asset-cache /ABSOLUTE/VERIFIED/assets --pbsv-observed-sha256 PRIOR_RECORDED_SHA256`. It reads only the explicit `pbmm2`/`pbsv` files, rejects symlinks/aliased cache paths, checks exact lengths and hashes before and after copying. pbmm2 still must match its author SHA. pbsv must match main's independently recorded prior observed SHA, not a hash computed and trusted in the same lookup. Offline mode has0 new software-body reservation; historical download/failure charges remain. No mixed automatic online/offline fallback is present.

Main now reports actual cluster curl7.76.1, local curl8.7.1 and about60GiB local free space; this worker did not query them. No old-curl body transfer was launched. The selected handoff is main's strictly capped local two-asset acquisition, retained TLS/transfer provenance and first observed pbsv SHA, followed by SCP and independent hash verification of the non-expiring home cache. The local step must use the same one-attempt/20s-connect/120s-total/per-asset size caps; no local Linux binary execution. If one asset succeeds and the other fails, preserve the verified success and failure evidence; do not rerun both downloads. Offline setup neither downloads nor installs a replacement. Main must retain transfer/copy accounting and prior evidence with the cache; a cache pathname alone is not provenance.

Selected offline argument contract (inside main's exact Slurm allocation; unresolved tokens are not runnable values):

```sh
bash /ABSOLUTE/FROZEN/setup_hg002_dna_callers.sh \
  --remaining-s0-cpu-seconds REMAINING_ALLOCATED_SECONDS \
  --remaining-s0-body-bytes CONSERVATIVE_REMAINING_BYTES \
  --external-s0-reserved-bytes 34204497850 \
  --asset-cache /ABSOLUTE/VERIFIED/HOME_CACHE/assets \
  --pbsv-observed-sha256 PRIOR_RECORDED_SHA256
```

All runtime probes use the absolute new binary paths. The packet keeps `file`, `readelf -h/-d`, `ldd`, `--version`, root `--help`, **pbmm2 align --help**, **pbsv discover --help**, and **pbsv call --help**, each with command, combined output and exact exit. Static-ELF ldd's recognized non-dynamic report is retained; missing dynamic libraries fail. Version pins must match, help must be nonempty usage/options with exit0. Different legitimate help exit behavior remains INCOMPLETE pending main's inspection, not automatic acceptance. Each probe is bounded to8s plus2s kill grace and a64KiB output-file guard; an overflow fails, not truncates. No reference/read input or biological test is supplied to any command.

Native failures are accumulated while remaining version/help probes are captured within the deadline. Format/asset/allocation failures stop before native controls. Final packet includes copied setup source and SHA256, documentation/source pins, resolved tool paths, asset/source URLs and SHA provenance, full notices, all logs/exits, disk samples, `status.txt`, `exit-status.txt`, and `artifact-sha256sums.txt`. Final synchronous setup log is closed before hashing; success/failure regular files are covered, except the hash list itself. Failed hash publication leaves INCOMPLETE/partial hashes. SIGKILL/node failure can bypass finalization; main must preserve and rehash the complete available packet, never infer success from an earlier log line.

## S0 account and custody

This is inside the existing **4 allocated CPU h / 4GiB reference+software body / 32GiB summed S0 disk** release, not a new account. Need at least300 remaining allocated CPU seconds; all earlier failures/setup/control jobs stay charged. The [earlier runtime](2026-10-10-hg002-runtime-setup.md) reports software bodies not exactly metered; use a defensible conservative remaining-byte ledger, not an invented precise remainder. The [native aligner history](2026-10-10-hg002-native-aligner-setup.md) and [reference expansion](2026-10-10-hg002-reference-expansion.md) remain prior costs. Historical October8 six-caller transport accounts are not spare software/DNA budgets.

Reserve64MiB for this scratch packet plus64MiB for its future home copy, including both retained assets and executable copies/logs/licenses; this is a guard, not predicted actual disk. The required external byte input covers **everything else**, including both12,807,281,629B expanded reference copies, compressed copies, retained environments/wheels/software/bundles and the8GiB other-material reservation where used. Avoid assuming those copies disappeared. Conservatively keeping the expansion note's34,204,497,850B external reservation and adding128MiB gives34,338,715,578B, **21,022,790B below32GiB**. This is reservation arithmetic, not current physical-use measurement. Main must resolve overlap with existing reservations and new concurrent work before launch; no double allowance or free reset.

Main confirms the retained15,719,120B software cache is already inside the prior8GiB other-material reservation. Keep external reservation **34,204,497,850B unchanged**, and add this new leaf+home128MiB separately. This gives34,338,715,578B as above. Cache custody copies must fit that existing reservation; do not add an uncounted copy or treat local free space as the S0 disk ledger. Offline software-body charge is0 for this job; main's preceding acquisition remains charged.

Script checks128MiB physical free scratch, samples its64MiB leaf cap after stages, and refuses an external+future-copy account above32GiB. These are boundary checks, not a filesystem quota or continuous peak measurement. Main must check home free capacity through writable login-side I/O and account concurrent S0 work; total concurrent RAM/disk still fit256GiB/512GiB. Main reports S1b complete (about5.359million reads/80.344Gb) and QA1604300 in progress; these are attributed status reports, not this worker's measurements. Source job1604284 audit/custody and QA remain main-owned and are neither queried nor restarted here; this script adds no S1 genomic body charge.

After actual completion/failure, main preserves the complete leaf and outer Slurm logs in non-expiring home using writable login I/O, then verifies hashes there before October22 scratch expiry. Compute home remains read-only. Keep binaries/assets out of Git. Capture actual allocation, process/Slurm CPU, elapsed, MaxRSS and storage scope; five minutes is a ceiling, not measured runtime. No deletion or scratch-only sole custody is proposed.

Before submission, main must set outer Slurm stdout/stderr to fresh files under an already existing writable parent, not the yet-absent exclusive leaf or read-only home. Retain those outer logs separately with job/allocation evidence and the leaf. A failed preflight before leaf creation can have only outer logs; preserve that failure too. This script never books or submits a job.

## Offline controls and handoff

Final script SHA256: `8662219ea36258fedadf60b0150a3ba0d7cd34fa080bf65a772d3bfd393261e5`. Bash syntax passed. **45 offline controls passed** against this script on the final rerun:34 in0.338s and11 in0.456s. Times are local harness wall times, not native setup measurements.

| Offline control group | Passed | Actual checks |
|---|---:|---|
| Budget accounts | 7 | Online boundary, offline zero-body account; insufficient CPU/body, disk overflow, missing/malformed account refusal |
| Curl version gate | 6 | Accept8.4/8.10/9; refuse7.76/8.3/unknown |
| Allocation record | 7 | Exact allocation; CPU/node/task/time/memory/GPU refusal |
| Exclusive leaf | 5 | Fresh path; existing leaf, dangling symlink, aliased parent and wrong name refusal |
| Asset verification | 5 | Exact length/SHA, distinct NULL-author observed SHA; bad length/hash/symlink refusal |
| Licenses and shared timeout budget | 4 | Both full text-blob SHA1 envelopes match API; shortened and expired budget |
| Mock online transfer | 4 | One attempt, exclusive publication/executable bit; TLS/size/time/retry flags; NULL-author distinction; failed transfer retains partial/exit without retry |
| Verified cache | 2 | Explicit prior pbsv observed SHA, no network/fallback; mismatch refused before copy |
| Probes, disk and finalization | 5 | Mock exit0/1 commands/output/exits; leaf cap; failure packet closed-log hashes; hash-publication failure stays INCOMPLETE |

The drivers sourced helpers only, using disposable synthetic text and shell mocks. No author binary, native caller, network, install or cluster execution was involved. Local macOS adapters supplied SHA256/timeout/du/GNU-style xargs behavior; they do not attest Linux ABI, real transfers, Slurm formatting or real help behavior. Initial harness faults were corrected; a recovery rerun from `/` failed to locate the relative source, then the explicit repository-directory rerun passed all45. No persistent test driver or third owned file was added. Main must independently review/freeze the script and note, verify completed upload and its exact SHA, and supply actual remaining CPU/body ledgers before execution. There is no S2 permission in CLI setup success.

Needed native observations remain **UNKNOWN**: actual embedded dependency versions, discover HiFi/CCS interface, support/strand threshold units/defaults, filters and size limits. The script records their help evidence; it does not select a calling policy or infer it from README prose. Keep the [caller preflight](2026-10-10-hg002-dna-caller-preflight.md) separation between CLI readiness, source/read readiness, same-exact-reference remapping, calling-only cohort indexing and later local phase/allele/copy proof.

Primary coverage: two known author release pages via Firecrawl; tag-release API JSON for both tools (rechecked on recovery); tag LICENSE files read fully; selected versioned README availability/changelog/workflow/compatibility sections; one exact official curl text source. Firecrawl skill and developer reference, full goal attachment, caller preflight, stage decision, prior runtime/native-aligner/reference budget notes and historical software/preparation constraints were read. No broad source search or asset/archive/genomic download was performed. Configuration remains requested, not backend-attested.

## Main's actual acquisition and CLI qualification

2026-10-11. The preparation above is preserved as worker scope, not current
execution status. Main independently checked the two official tag APIs through
Firecrawl and reviewed the entire final script. Its SHA matches8662219e above;
bash syntax passes. The actual cluster curl is7.76.1. Main's new
[small-software cache script](../../scripts/cache_hg002_caller_assets.sh) uses
local curl8.7.1, verified TLS, one attempt per exact asset,120s/20s limits and
stream-enforced exact size caps. It completes at09:26:07UTC with exit0.
Both final HTTP statuses are200, TLS verification0, redirects1. Reported
payloads5,962,520B and9,756,600B total15,719,120B; no genomic bytes or local
Linux execution. Retain the128MiB software-body reservation, not an invented
physical-network total. Prior software bodies remain unmetered. A conservative
prospective ledger with1GiB held for those,1,152,186,383B reference bodies,
259,784B native-aligner sources and128MiB for this acquisition leaves
1,934,561,577B, not2GiB. Use at most1.9billion bytes for any next new-body action.

pbmm2's observed SHA matches the release API value. pbsv's first observed SHA
is `01d83ec77ce40a5416b2a591f98090c51870b25d66650eccc7d7c493e1da5ae6`.
Its author/API digest remainsNULL. Complete transfer metrics, exit records,
source table and license notices accompany the15.7MB cache under HOME
`experiments/hg002_caller_assets_cache_20261011_01` (15,723,313 apparent bytes).
SCP completes before separate remote length/SHA checks; both match.

Immutable HOME bundle `bundles/hg002_dna_callers_s0_20261011_01` contains
the two scripts. Setup source SHA is checked after completed upload, before
execution. Job1604301 runs the frozen offline packet on hydra-n1/amd_256M,
1CPU/2GiB/5min, no GPU. Conservative remaining CPU input10,000s holds4,400s
of the original14,400s account aside; it is not an exact actual-cost claim.
Body input2,147,483,648B and external reservation34,204,497,850B are supplied
explicitly. The2GiB input is preserved as executed, not certified as the next
available-body ledger; the tighter prospective hold above supersedes it.
Offline mode consumes0 new body bytes, so this accounting correction requires
no rerun or altered raw budget receipt. No budget reset, body transfer or caller run occurs
inside this job. S1 QA1604300 runs independently; total allocated RAM6GiB.

1604301 COMPLETED0:0,1 allocated CPU second,0.543 measured CPU seconds,
stepMaxRSS2988K. StatusCLI_CONTROLS_COMPLETE. Versions pbmm2 26.2.0 and
pbsv2.11.0 match; all root/subcommand help probes exit0. pbmm2 reports
pbbam/pbcopper26.2.0,boost1.90,htslib1.23,minimap2 2.26,zlib1.3.1; these
are runtime self-reports, not independent dependency build attestations.

Native help resolves important formerly UNKNOWN interface fields:

- pbsv discover `--hifi`/`--ccs` sets gap-compressed identity97%; general
  default70%, MAPQ5, reference span100, signature length7. Native default
  downsampling is100 alignments per10kb window; no cohort policy is chosen here.
- pbsv call `--hifi`/`--ccs` sets `-S 0 -P 10`. Other native support defaults
  areA3/O3/B2 and genotype minimum1. S is reads per strand, P is percent.
  Native minimum SV length20, maximum insertion15K; retain all emitted filters
  and types, then apply the frozen downstream DEL/INS≥50bp cohort separately.
- pbmm2 supports explicit CCS/HiFi preset, RG/sample, unmapped retention,
  sorted BAI/CSI output, gap-compressed identity70%, minimum mapped length50,
  and explicit alignment/sort thread and per-sort-thread memory controls.

These are captured help declarations, not demonstrations of real-data
filtering, sensitivity, phase, reference compatibility or callset identity.
Repeat-BED compatibility, exact S2 command/resources and independent release
remain pending. CLI success cannot clear those gates.

The complete scratch packet is copied once to matching non-expiring HOME
leaf `experiments/hg002_dna_callers_s0_20261010_01`. Every original packet
hash in artifact-sha256sums.txt passes there. Apparent scratch/HOME sizes
31,490,324B/31,490,468B fit the64MiB reservations. The144B HOME difference
is copied outer Slurm stdout/stderr, added after original manifest creation;
those two late files are not covered by that original list. Separate byte
comparisons of both outer logs against HOME pass; the original hash list also
byte-matches scratch. Its SHA is195683792c5f93c4b1432c0685e3506a110b16d88c5fffd1500c9d08ae4499e7.
The [small unchanged CLI receipts](../../results/hg002_caller_setup_20261011/README.md)
retain these separate hashes and actual help/version evidence. All original
runtime logs/failures stay intact. No raw binaries/assets enter Git, no shared
PATH/environment change, no scientific positive result or S2–S4/RNA release.
