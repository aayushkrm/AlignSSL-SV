# HG002 native aligner setup

Prepared for S0 on 2026-10-10. This is a source-build packet only. It does not install software, read the BAM, run LiftOn, or qualify an annotation result. Main owns code review, immutable-bundle preparation, launch, and qualification.

## Pinned releases

LiftOn 1.0.14 needs the external `minimap2` and `miniprot` commands. Its installation guide sets minimum versions of minimap2 2.17 and miniprot 0.10. It requires miniprot 0.14 or later for any target sequence at least 2^31 bases long. Both selected versions exceed these limits. The guide uses `minimap2 --version` and `miniprot --version` as CLI checks. [LiftOn 1.0.14 installation guide](https://ccb.jhu.edu/lifton/content/installation.html)

On 2026-10-10, the authors' [`minimap2`](https://api.github.com/repos/lh3/minimap2/releases/latest) and [`miniprot`](https://api.github.com/repos/lh3/miniprot/releases/latest) `releases/latest` APIs returned these non-prerelease tags:

| Tool | Release and author commit | Source asset | GitHub API asset SHA256 |
|---|---|---|---|
| minimap2 | [v2.31](https://github.com/lh3/minimap2/releases/tag/v2.31), published 2026-05-19; [`3c28777e7e2dcc90f825de1b9f17a89cca7d4452`](https://api.github.com/repos/lh3/minimap2/commits/v2.31) | `minimap2-2.31.tar.bz2`, 187,931 B | `c1351de6319c123369c2f4f37ba0ccf18c7ace47e2b1c0a35e30056b4a3bd9c9` |
| miniprot | [v0.18](https://github.com/lh3/miniprot/releases/tag/v0.18), published 2025-07-11; [`671db243f964a68bd724af11cd9964d840f29c43`](https://api.github.com/repos/lh3/miniprot/commits/v0.18) | `miniprot-0.18.tar.bz2`, 71,853 B | `307428a8da5854fa4c2f078ff0ca07756143b28e1598b8247c727ca2b87b15b1` |

The source asset URLs in the script use these versioned release paths. The script enforces each API-reported byte count and SHA256 before extraction. Total source payload: 259,784 B (about 0.25 MiB). This is software under S0, not genomic body under S1. HTTP overhead is not included. No source archive was downloaded for this packet.

The [minimap2 README at its pinned commit](https://github.com/lh3/minimap2/blob/3c28777e7e2dcc90f825de1b9f17a89cca7d4452/README.md) and [miniprot README at its pinned commit](https://github.com/lh3/miniprot/blob/671db243f964a68bd724af11cd9964d840f29c43/README.md) document source compilation with GNU `make`. They list a C compiler and zlib development files. The release tag-to-commit mapping is recorded above.

## Build and artifacts

[`setup_hg002_native_aligners.sh`](../../scripts/setup_hg002_native_aligners.sh) writes only to this new scratch leaf:

```text
/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/hg002_native_aligners_s0_20261010_01
```

It refuses an existing leaf. It requires one Slurm task with 4 CPUs, one node, and no GPU. It downloads each pinned source asset once over HTTPS, with a 20-second connect limit, a 120-second transfer limit, and a strict maximum body size. It checks the exact length and digest, then keeps the archive. It extracts into the output tree. Each build runs in sequence with `make -j4`. `TMPDIR` points inside the scratch output. The script does not write to compute-node home, change a shared environment, change `PATH`, install dependencies, retry downloads, or remove failed files.

Main should freeze the reviewed script and launch it with one node, 4 CPUs, 4 GiB RAM, no GPU, and a 15-minute wall limit. The maximum allocation is 1 CPU hour and counts inside the released S0 ceiling of 4 CPU hours. Do not reserve a whole node. This packet does not book that allocation.

On success, the output contains:

- Both retained release source archives and extracted source trees.
- One local binary for each tool under `bin/`; no shared install or PATH edit.
- Each tool's version output and `-h` output.
- Build logs, archive member lists, a source manifest, exit status, and `artifact-sha256sums.txt`.

The script checks the version strings and help output, then verifies the artifact hash list. Help/version success qualifies only these CLI controls. It does not qualify minimap2/miniprot alignment behavior or release P1.

Keep every success or failure output. Scratch expires on 2026-10-22. After execution, main must copy the complete output to non-expiring home through writable login-side I/O and verify hashes. Do not use compute-node home for that copy.

```mermaid
flowchart LR
    A[Author release asset] --> B[Exact size and SHA256 check]
    B --> C[Source build in new scratch leaf]
    C --> D[Version and help records]
    D --> E[Artifact SHA256 manifest]
    E --> F[Login-side custody copy]
```

## Boundary

Offline Bash control for archive-name resolution. It starts with a global `tool=uname`, as the script does after its command preflight. The corrected local assignment prints the two intended paths and does not access the network:

```bash
bash -uc '
out=/offline/output
tool=uname
fetch_source() {
  local tool=$1 version=$2 commit=$3 bytes=$4 digest=$5 url=$6
  local archive="$out/source_archives/$tool.tar.bz2"
  printf "%s\n" "$archive"
}
fetch_source minimap2 2.31 pin 187931 sha https://example.invalid/minimap2
fetch_source miniprot 0.18 pin 71853 sha https://example.invalid/miniprot
'
```

Expected output:

```text
/offline/output/source_archives/minimap2.tar.bz2
/offline/output/source_archives/miniprot.tar.bz2
```

`bash -n scripts/setup_hg002_native_aligners.sh` and this offline control pass. No source archive, binary, reference, or genome was downloaded or built. No cluster job was submitted, and no project test suite was run. Main continues to own live BAM job 1604284 and the later LiftOn qualification gate. This setup packet is routine software preparation; native gene mapping and P1 remain unreleased.
