# 2026 sequencing benchmark: is `sv.gz` a cheap candidate panel?

**Checked:** 2026-09-28. **Scope:** first-party article, Zenodo metadata, and 4 MiB of HTTP-range metadata/prefix. No whole archive, VCF call body, or reads were downloaded or scored.

## What the paper actually releases

The [Genome Biology full text](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13072666/fullTextXML) says short-read SVs were called with Delly, LUMPY, Manta, WHAM, BreakSeq2, and CNVkit *integrated through MetaSV 0.5.4*. It describes further DupHold 0.2.1 filtering at DHFFC 0.7 for DEL/DUP; DRAGEN SV 4.3.13 and Dysgu 1.6.1 were also applied to short-read datasets. Its data-availability section points to ENA `PRJEB109257` for alignments and [Zenodo record 18868532](https://zenodo.org/records/18868532) for SV VCFs and benchmark outputs. These statements establish a modern processed-callset comparison source, not that the six individual MetaSV input caller candidate streams are released.

The installed Firecrawl paper-index plugin located the article metadata, but
its full-text retrieval returned no passages and a page scrape hit a cookie
policy. The first-party Europe PMC full-text XML above supplied the methods
and availability statements instead; no CLI-based Firecrawl access was used.

The [Zenodo API record](https://zenodo.org/api/records/18868532) lists five top-level files. The SV package is `sv.gz`, 3,329,540,940 bytes, MD5 `093a0f10661014fb820e0f776891a7a9`; it gives no per-caller member links, member sizes, or checksums. An HTTP `Range: bytes=0-4194303` request returned `206` with exactly 4,194,304 bytes. The prefix SHA-256 was `64a6ece8568d13d249a0f7fe6d60467da74ed6f649d7dc98509c98da3b42b50b`.

The prefix is **concatenated gzip members**, not a directly listed TAR/ZIP central directory. Parsing each complete gzip member with Python `zlib.decompressobj(31)` and its `FNAME` header gave:

| Start byte | Gzip member name | Compressed bytes in complete member | Uncompressed bytes |
|---:|---|---:|---:|
| 0 | `HG002.revio.pbsv.vcf.gz.tbi` | 338,598 | 349,545 |
| 338,598 | `HG002.R9.svim.vcf.gz.tbi` | 271,078 | 280,174 |
| 609,676 | `HG002.revio.dysgu.vcf.gz.tbi` | 254,117 | 263,595 |
| 863,793 | `HG002.sequel.dysgu.vcf.gz` | incomplete within the 4-MiB prefix | unknown |

The first decompressed member begins with another gzip/BGZF header, consistent with a compressed `.tbi` payload. This prefix does **not** inventory the whole 3.33-GB package or prove which short-read VCFs it contains. The fourth member is an HG002 Sequel (long-read) Dysgu file, not an inspected short-read candidate output. Selective byte-range retrieval of an arbitrary later member would require its offset, which the published top-level metadata do not provide. The archive's own MD5 was not verified because the full package was not transferred.

**Decision:** this source does not currently pass the no-large-transfer, candidate-stage input gate. Even if the whole package were fetched, the paper documents processed MetaSV and other SV callsets, not individually preserved raw emitted candidates from the six MetaSV component callers. A full transfer might be worthwhile for a *different*, prospectively defined realistic-callset/matcher question, but should not be undertaken merely to rescue the candidate-generation ceiling claim. Continue seeking a matched candidate-stage panel or review a bounded new caller-generation protocol. Do not pool this source with the historical Parliament2 or separate HitSV reads/builds.
