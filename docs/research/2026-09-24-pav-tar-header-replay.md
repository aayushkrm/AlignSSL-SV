# Reproducible header-only inventory of two HGSVC3 PAV working TARs

**Date:** 2026-09-24. **Scope:** only the two named archives in the official
[`20240307_PAV_VCF` working directory](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/working/20240307_PAV_VCF/).
This checks archive member names, not donor callability or SV truth quality.

The earlier [availability note](2026-09-23-pav-callable-availability.md)
reported a complete metadata-only TAR-header walk without retaining its
scanner or member log. The [new scanner](../../scripts/scan_remote_tar_headers.py)
repeated that walk against the official archives. For each archive it checked
the HEAD length against the [official manifest](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/working/20240307_PAV_VCF/MANIFEST_20231211_Freeze1_20240307),
required a strong stable ETag, requested one 512-byte header block at each TAR
member offset, and required exact HTTP 206, `Content-Range`, response length,
and TAR header checksum. It advanced past each payload by the header-declared
size without requesting the payload, then required two zero-block TAR end
markers. It fails closed on PAX/GNU extended-name metadata because resolving
those names would require reading member payload. Neither archive contained
such metadata records.

| Archive | Manifest length | Members | VCF / TBI / directory | BED names | `callable` names | Range requests |
|---|---:|---:|---:|---:|---:|---:|
| `20240307_PAV_VCF_hg38_mm2.tar` | 12,630,108,160 | 391 | 195 / 195 / 1 | 0 | 0 | 393 |
| `20240307_PAV_VCF_hs1_mm2.tar` | 12,857,282,560 | 391 | 195 / 195 / 1 | 0 | 0 | 393 |

Each run requested 201,216 TAR-header bytes (393 × 512), or 402,432 for the
two archives, excluding HTTP protocol overhead and HEAD responses. No VCF or
other member payload was transferred. The versioned
[audit bundle](../../results/pav_callable_archive_audit/2026-09-24) has one
`members.jsonl` row per member, plus `summary.json` and a matching SHA-256
manifest per archive. The member-list counts and zero BED/`callable` flags
were independently recomputed from both JSONL files with `jq`; both local
SHA-256 manifests passed. A small copy of the publisher's textual
[`MANIFEST`](../../results/pav_callable_archive_audit/2026-09-24/OFFICIAL_MANIFEST.txt)
records the source lengths and full-archive MD5 values.

From the repository root, repeat the inventory into *new* output directories:

```bash
../.venv/bin/python scripts/scan_remote_tar_headers.py --archive hg38 \
  --out-dir results/pav_callable_archive_audit/recheck-hg38
../.venv/bin/python scripts/scan_remote_tar_headers.py --archive hs1 \
  --out-dir results/pav_callable_archive_audit/recheck-hs1
```

The whole 12–13 GB TARs were **not** downloaded, so their publisher MD5s were
not recomputed. Matching length, stable ETag, valid TAR checksums, and complete
header walks support the member inventory but are not cryptographic proof of
whole-archive identity. The negative finding is limited to these two TARs:
neither contains a BED-named or `callable`-named member. It does not exclude
callability data in other HGSVC3 sources, prove that PAV could not generate
such output, or define confident negatives. An actual donor/haplotype mask
still requires provenance, unsmoothed alignment coverage, QC exclusions,
reference-coordinate validation, and independent truth checks before use.
