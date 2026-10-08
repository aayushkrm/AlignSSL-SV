# Native-tool readiness: metadata only

October 9 local / October 8 UTC. No native experiment or installation ran.

## Observed cluster state

At `2026-10-09T00:47:19+07:00`, the account queue was empty. The login
PATH query found only Singularity among the ten requested tools. Named
bioinfo/truvari paths found an executable bioinfo samtools. Its version and
runtime dependencies were not tested; an older missing-library failure
remains in the history.

At `00:48:24+07:00`, a separate metadata query enumerated these six conda
environments: bioinfo, celllines, deepsv2, deepsv2_new, nt_embeddings and
truvari_env. None had an executable named sawfish, minimap2, pbmm2, sniffles,
spoa or lamassemble in its immediate `bin/` directory. This does not search
other paths, modules, containers or other users' installations. The immediate
project tools directory listed only the retained Manta image. Do not call
the newer tools absent from the entire cluster.

Local free space was 15,026,164 KiB (about14.3GiB), above the10GiB safety
guard. Large genomic work remains cluster-only. No key contents, read files,
reference files or truth/caller VCFs were opened by these metadata queries.

## Official release candidates, not installed tools

Three current `releases/latest` API queries returned the following assets.
These are observations of mutable latest endpoints; freeze the exact version
and verify actual downloaded bytes before use. An API digest is not a hash
we have measured from the binary.

| Author release | Candidate Linux payload | Declared bytes |
|---|---|---:|
| [Sawfish v2.2.1](https://github.com/PacificBiosciences/sawfish/releases/tag/v2.2.1) | `sawfish-v2.2.1-x86_64-unknown-linux-gnu.tar.gz` | 3,616,061 |
| [pbmm2 v26.2.0](https://github.com/PacificBiosciences/pbmm2/releases/tag/v26.2.0) | `pbmm2` | 5,962,520 |
| [minimap2 v2.31](https://github.com/lh3/minimap2/releases/tag/v2.31) | `minimap2-2.31_x64-linux.tar.bz2` | 2,252,266 |

API-declared SHA256:

```text
Sawfish 869d866d1399bd9803b3c60cc0e260ed1f60aa38a6f40d46f3093cd4bf5631f4
pbmm2   f8a583d27a6232706c8ffe31dab3e52815455032517e9c1399940d4a3ea612bc
minimap2 300bc287f05eb890c6211fa7db043ce98320a401621fadd1cfdbeabd1a6e4ab5
```

The combined declared compressed/raw payload is11,830,847bytes, excluding
checksums, extraction, runtime files and repeated verification passes. No
payload was downloaded, unpacked, staged, executed or charged as an invented
installation. GNU/libc compatibility, executable versions and region/fixture
semantics remain unverified. Latest source and release code are not assumed
identical. The guide's pbmm2 input requirements must be checked before using
minimap2 as an interchangeable supported input.

Later tag resolution: the official annotated Sawfish v2.2.1 tag object
`4412d4d94d413ae81c74d29f062bb12ef5233e00` resolves to commit
`8fdf4cf1b16e366ae8291d4547a1da06affc5c4a`, the exact inspected guide/CLI
source pin. This establishes the tag-to-source mapping, not downloaded binary
integrity, build provenance, installed behavior or fixture compatibility.
[Author tag reference](https://github.com/PacificBiosciences/sawfish/tree/v2.2.1).

## Next boundary

Source-interface and nearest-prior-art sidecars run in parallel. Their result
must identify a decisive native contrast before an installation or synthetic
test is selected. No production contract change, real-data pass or all-six
preparation restart is implied. The old screen remains stopped and its full
charges retained.
