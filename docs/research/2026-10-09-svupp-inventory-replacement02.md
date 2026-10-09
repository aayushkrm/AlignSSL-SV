# Separate SVUPP metadata inventory02

Status: **UNBOOKED, UNSTAGED, UNEXECUTED; exact review pending**.
This is a data-readiness check, not a selected method or publication result.

## Governing scope

Main reads the latest objective FULL:
`/Users/akm/.codex/attachments/2fa04b13-b328-4023-872e-0c4cc9dbfaee/goal-objective.md`,
SHA256 `74ba6450712e7f0e763cd81de896d3a71ca73f9c4a10fec3f1ecab59b3f1b0b8`.
Its resource clause names GPU, CPU, RAM and storage, used efficiently. The
user's explicit clarification is: “Use all useful resources efficiently;
scale parallel experiments fully.” Allocate one CPU and2GiB for this serial
single-asset inventory. No GPU operation or useful parallel experiment is
part of this job. No extra idle node allocation is justified.

The [completed investment decision](2026-10-09-svupp-permission-value-decision.md)
selected one narrow prospective02. It read the previous objective; the latest
revision changes resource wording, not the scientific question. The next
independent exact review must read the latest objective and this reconciliation.
Requested decision configuration was Sol6.1/max; actual backend is unattested.

Keep01 ACCEPT CLOSED INCOMPLETE, its source snapshot in5df488c, all13 tracked
raw files, full512MiB charge, and measured2.64CPU counted once. Never replay
its root or claims. This02 is the one explicit setup-only exception; failure
or wider necessary repair closes this candidate. No automatic03, substitute
archive, author-format repair, or alternate platform/caller is allowed.

## Exact narrow implementation

`analysis/inspect_pinned_research_zip.py` changes only directory access:
Linux requiresO_PATH; non-Linux keepsO_RDONLY. Missing LinuxO_PATH fails
closed. RetainNOFOLLOW, DIRECTORY, CLOEXEC, component-wise dir_fd traversal,
directory fstat, descriptor closing and reopened parent identity checks.
The archive leaf remainsO_RDONLY/NOFOLLOW. ZIP parsing, two stored hashes,
input/output caps, single-link regular-file and exclusive output guards
are unchanged. This corrects a directory read-versus-search incompatibility;
it grants no archive read access or general concurrent-writer guarantee.

`analysis/run_svupp_archive_inventory.py` changes only the literal experiment
ID to `svupp-inventory-20261009-02`. The physical root is exactly
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/svupp-inventory-20261009-02`.
No selectable production root or continuation of01 is introduced.

Fresh wrappers/reservation live in
`results/data_audits/svupp_inventory/2026-10-09/attempt02/`.
Do not edit the original01 wrapper/book/pins. New02 checks include live
unprivileged identity, each ancestor's mode/owner/effective read/search
access, successfulO_PATH traversal/fstat and dir_fd leaf access on the real
workspace, saved exclusively in `permission_preflight.json` before controls.
It does not read a member or change any production permissions/ACL/owner.

The Luna/max-requested sidecar adds bounded synthetic permission controls and
proves symlink rejection reaches the intended component. Requested config
is not backend attestation. The expanded count is33:28 existing cases plus
three Linux permission cases and two portable flag-selector controls.
The non-Linux selector uses fake descriptors rather than unreadable cluster
ancestors; it tests flag choice/closing, not real non-Linux compatibility.
The payload wrapper requires exactly33 passed and no skips before download.
Linux permission tests must pass as the actual unprivileged cluster user,
zero skips. A local macOS skip is not Linux validation. Temporary permission
fixtures restore their original modes; no production chmod is permitted.

Main reads the completed worker changes and runs inventory/launcher/permission
plus integer-ceiling controls locally:53passed,3Linux-only skips,0.87s.
This is56 collected cases, including23 ceiling cases not staged for02.
The actual inventory bundle runs33, not56. No non-root Linux run is claimed.
Both shell scripts and inline preflight Python parse successfully.

## Fixed input and limits

One acquisition only, same author record17569072 asset:
`https://zenodo.org/api/records/17569072/files/SVUPP_paper.zip/content`.
Exactly47,443,427bytes; MD5 `5469337ca9249691b2b376ceb9b67e1d`.
Download digest must agree with stored SHA256. Inventory all central-directory
members within4096members/256KiB directory and names/1MiB exclusive manifest.
Never decode/extract member bodies or run author code/callers/scoring.
Full stored hash passes read opaque compressed bytes; member CRC and payload
integrity are not established by metadata. Names alone do not establish
scoredGT, authoritative truth, reference/ALT identity, callability, technology,
depth, independence or current native baseline compatibility.

Retain oneCPU affinity,2GiB address-space limit,120s wall plus5s kill grace,
60/90 per-process CPU, initial64MiB file cap then1MiB reports, capped synthetic
tree32MiB/4096entries,2MiB complete small raw archive. Python3.10.20 and
pytest8.4.2 use the existing dependency path, with no installation.

| Account | Value |
|---|---:|
| Retained prior bytes |41,309,049,739|
| New02 allowance, UNBOOKED |536,870,912bytes /180 allowance seconds|
| If booked, retained total |41,845,920,651bytes|
| Prior measured named CPU |563.932707seconds|
| PriorCPU plus proposed allowance, not a measurement |743.932707seconds|
| Residual original complete-candidate envelope if booked |1,073,741,824bytes /240 allowance seconds|

Conservative named byte-pass ceiling remains373,017,001bytes: acquisition
47,443,427; stored hashes94,886,854; six32MiB synthetic passes201,326,592;
six2MiB metadata hash/transfer/verification passes12,582,912;16MiB staged
source/log/claim allowance16,777,216. The focused fixtures are within those
caps. This does not measure all physical/network/cache I/O. Retain the full
new512MiB charge even on failure. Measure outer waited-tree user+system once;
do not double count pytest wall time orSlurmCPU. Global64GiB/7200 ceilings
are unchanged. The residual allowance approves no content analysis job.

## Required order and outcomes

Freeze complete code, tests, zero-skip count, wrappers, reservation, bundle,
literal exclusive claim-before-sbatch submission. Then require maintained
independent Sol6.1/high-requested review of the exact diff and full account.
Only conditional acceptance may allow booking status/timestamp repin without
new code/command changes. Book before root creation or any staging; verify
final booked pins on cluster and submit the exact literal command once.
Unknown acknowledgement consumes the slot. Before creation check fresh root
absence and live jobs/expiry. Post-control source pins must match before
download. Any failure stops the attempt; preserve complete bounded raw logs.

Runtime success requires wrapper exit0 and exclusive
`COMPLETE_METADATA_INVENTORY` marker after stream/stored agreement, not just
an inventory file. Independently audit actual hashes/logs/account before
accepting readiness. Plausible names require a separately reviewed complete
content protocol within residual allowance. Missing inputs stop; no favorable
prefix, substitute source, outcome-driven threshold or selective continuation.

Scientific question remains the fixed SVUPP/kanpig ONT ultra-long→HiFi
confidence-value falsifier,1% published-label discordance and10-point
neighboring-SV coverage investment margin over strong frozen ordinary
controls. GenericGQ coverage is prior art. A large selection ceiling is only
room, not learnability, clinical accuracy, a new method or publication payoff.
The full publication goal is active and unmet.

## Read-only precreation snapshot

Main metadata13:33:35+07 on October9: unprivilegedigorno uid1638200118;
queue empty; fresh02 absent; `/beegfs`0711, `/beegfs/scratch`0755, owned
physical base0700. Workspace expiresOctober22 at23:02:50+07,1extension.
This is a snapshot, not future effective-operation/ACL or control validation.
No new root, budget booking, staging or acquisition occurred.

## Frozen unbooked candidate

The [eight-entry bundle](../../results/data_audits/svupp_inventory/2026-10-09/attempt02/bundle.sha256)
SHA256 is `9d62d97d6eaf3a072ff1fa7347bf8f1e631c25f77660440060a54f013c41820b`.
The [literal command](../../results/data_audits/svupp_inventory/2026-10-09/attempt02/submission_command.txt)
pins that hash in both exclusive claim and Slurm invocation. It is not yet
executable authority. Exact review is pending, all numeric charges UNBOOKED.
If review accepts status/timestamp-only booking, repin reservation, bundle
and both literal occurrences before staging; reverify the final values.
Any other code/test/wrapper/resource/command change needs exact review.
