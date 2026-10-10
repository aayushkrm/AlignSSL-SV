# Matched reference expansion — routine S0

Prepare the five verified GENCODE50 compressed products for later tools.
This is not donor annotation, coding-path scoring or S2–S4 release. Main
works here while full-source S1b1604284 runs; independent Luna/max-requested
workers prepare native aligner builds and the study's exact calling recipe.

Source is the verified non-expiring home reference leaf
`/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/hg002_gencode_s0_20261010_01`.
Require its complete STAGED_CHECKSUM_VERIFIED manifest, exact five names,
and matching compressed sizes/SHA256s. Decode each whole gzip through EOF/
CRC, hash the expanded bytes, and publish exclusively only after CRC passes.
Do not replace inputs/outputs, retry, crop annotations, or change reference.
Keep partials/failure manifests. A completed filename alone is insufficient.

One useful serial CPU/4GiB/15min on n1/amd_256M, script deadline14min. The
gzip stream uses at most1MiB chunks, with no in-memory genome. No GPU or
idle node. This books at most15CPUmin within released S0's4h; prior setup,
failed attempts, mock controls and reference transfer remain charged.
No new upstream body transfer; only already retained compressed files.

S0's32GiB summed peak is not a new free allowance. Reserve8GiB for retained
compressed copies, software and small artifacts; this is planning headroom,
not an observed exact total. Main's finite du inventory sees both compressed
copies, both wheelhouses/logs, home LiftOn/intake venvs and bundles; separate
scratch venv and future small aligner builds must also fit this reserve.
The expanded-payload cap is12GiB minus16MiB, **including a reserved second
custody copy**. Thus8GiB plus twice that cap leaves32MiB for metadata below
32GiB. Require32GiB physical free space before decode. If a genuine reference
exceeds the account, stop INCOMPLETE; do not trim it to obtain success.

New writable output:
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/hg002_reference_expand_20261010_01`.
Immutable bundle: project home `bundles/hg002_reference_expand_20261010_01`.
Run `python -B -m scripts.expand_hg002_gencode --reference` with the exact
home source above and `--output` with that scratch leaf. Compute home remains
read-only. Later preserve complete new outputs through writable login I/O
and verify custody hashes. Scratch expiresOctober22.

Source SHA256fb5dbd198d00f804630eec4ae4d0d25ede33daeffbdd3ef69deb6ec357d0b499;
test SHA2562860086d86fd7e4b35c01225b51db264fdf2f8cbd5e3d33266eb2222c82d1c07.
Seven local synthetic controls pass,0skips,0.17s: full five-object decode,
exclusive output, source drift/missing file, truncated gzip CRC, low space,
payload cap and deferred cancellation. Actual Linux qualification/decode
remain pending in this preparation snapshot. No study BAM or RNA read here.

## Actual decode

Immutable source/test hashes match in1604285, all7 Linux controls pass,
zero skips,0.09s. Actual decode1604286 completes0:0,1CPU/4GiB,
34allocatedCPU seconds/31.615 measuredCPU seconds/19784K MaxRSS.
Its32.866s process wall is distinct from scheduler allocation. All five
compressed source SHA256s and whole-gzip EOF/CRCs pass. Expanded payload
12,807,281,629B, under cap12,868,124,672B by60,843,043B. The annotations
are large: GFF3 is4,767,708,901B and GTF4,688,772,094B. Do not estimate
future indexing cost from the compressed sizes or restrict isoforms to fit.
The [unchanged expansion manifest](../../results/hg002_reference_expand_20261010/manifest.json)
records all expanded hashes/sizes. This is format/custody preparation only.

The finite named S0 inventory totals3,603,477,828 apparent bytes before
expansion, including both compressed copies/wheelhouses, both LiftOn venvs,
the intake venv, Sniffles venv and bundles. This is scoped, not an exhaustive
project or pip-cache census. The8GiB planning reserve retains other small
artifacts/build headroom. Two expanded payload copies plus that reserve are
34,204,497,850B, leaving155,240,518B below32GiB; observed physical use is
not claimed by this reservation arithmetic. No reference body was redownloaded.

New expanded files/manifests copied once to matching non-expiring home leaf.
Separate read-only compute custody1604287 rehashes all five home payloads:
all match the expansion manifest. Home manifest SHA256 is
81d058277595b952fe4a69df9a25d69d131c24f7c10b5e9a44dcb82bbaa55c05.
No sole needed copy remains on expiring scratch. Live S1b continues independently.
Custody job completes0:0,15allocatedCPU seconds/12.518measuredCPU seconds;
its memory report is24K MaxRSS. This small read-only hash command does not
qualify native annotation. Combined local selected suite153tests+9subtests
passes, zero skips,2.01s; infrastructure controls, not biological outcomes.
