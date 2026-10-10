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
