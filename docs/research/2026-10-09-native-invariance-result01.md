# Native CIGAR diagnostic — attempt 01 setup failure

## Outcome

Experiment `native-cigar-invariance-20261009-01`, Slurm job `1604208`,
ended `FAILED 1:0` after five scheduler seconds. The cluster's 70 frozen
software controls passed, with zero skips, in 2.58 seconds. Fixture creation
then failed: `ValueError: output directory ancestors must not be links`.

No fixture was created. No release asset was acquired. No Sawfish version,
discover, or joint-call command ran. There is no candidate, allele, FILTER,
genotype, biological null, or publication result. The failure does not test
the research hypothesis or establish native compatibility.

## Evidence and cause

The actual traceback reaches `create_fixture` and `_new_output_directory`
before any native step. A read-only cluster check at 10:11:35+07 shows that
the managed workspace `/scratch/igorno-alignssl_restart_20260922` resolves to
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922`. The logical path
contains a normal managed filesystem alias. The fixture correctly rejects
symlink ancestors, but the launcher passed that logical path to the fixture.

All 12 staged bundle entries still matched after failure. The original
bundle SHA256 is
`5fb12fce0d6a5a43a170827af88405214af59c98f99718a14733dc1503c3cfad`.
The exact runner, wrappers, protocol snapshot and claims must remain
recoverable in Git before a replacement changes the common runner.

## Charges and closure

The selected raw archive is local at
`results/data_audits/native_invariance/2026-10-09/raw01/`: 14 payload files,
16,696 bytes, plus the 1,175-byte checksum file, **17,871 bytes total**.
All 14 local SHA256 checks pass. The staged pre-submission reservation is
preserved in `raw01/reservation.json`; the parent `reservation.json` is the
live post-failure journal. These are deliberately different records.
The first SCP command used unsupported remote brace expansion and transferred
no file. A second command listed the exact 15 paths and completed successfully;
this was an archival transport correction, not experiment replay.

The full 256 MiB reservation was booked at 03:03:09 UTC before root creation.
It remains charged: cumulative retained allowance **40,503,743,371 bytes**.
The single outer timer reports user 1.00 plus system 1.07 seconds, counted
once: **2.07 CPU seconds**, 4.52 wall seconds, maximum RSS 55,120 KiB.
Cumulative measured named CPU is **558.792707 seconds**. Inner test elapsed
and Slurm CPU are not charged again. Named allowances do not measure or
bound all physical filesystem or opaque tool I/O.

This attempt is closed incomplete. Its root, claims, logs and charges remain
intact. It will not be rerun or selectively continued. Scratch expires
2026-10-22 at 23:02:50+07, with one extension available.

## Prospective replacement, not an outcome amendment

A fresh, separately reviewed attempt may resolve the trusted workspace to
the exact observed physical path before fixture creation. It must reject an
unapproved destination or linked experiment leaf. Keep the fixture's link
guard; keep all molecules, CIGARs, caller settings, endpoints and stop rules.
Add path-alias regression controls. Use a new experiment ID, claims,
reservation and root. No native setup retry is authorized by the old claim.

The selected four-arm test remains a cheap software diagnostic, not a novel
method or publication lead. Its value decision and stop rules are unchanged.
