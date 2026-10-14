# Fixed inversion: separate mapped-input census

Job **1604870 completed once** on 14 October 2026. It retained all 52 regional
alignment records, reached region EOF and did not hit a cap. The maintained
[independent review](../../docs/research/2026-10-14-inversion-input-extraction-review.md)
accepts the bounded census and its local consistency checks. It does not accept
an inversion-support, genotype or caller-failure claim.

## What was observed

- 52 alignment records from 47 QNAME labels: 47 primary and 5 supplementary.
- MAPQ 60: 49 records; MAPQ 12: 2; MAPQ 32: 1. No MAPQ filter was applied.
- All 52 retain stored sequence and quality. No hard clips or query/CIGAR
  length disagreements occur in this packet.
- Three QNAME labels have multiple fetched records. Their normalized sequence
  and quality hashes agree within each label. These are not technical replicates.
- The local `=` check compared 522,266 bases against the retained canonical
  context with zero conflicts. It witnesses 28,991 of 29,000 reference positions;
  nine positions remain unknown. This does not identify the whole mapper FASTA.

The [descriptive query-order report](observed-query-order-02.json) includes
**every** fetched record, not just the two patterns below. It contains no SEQ
or QUAL strings. Exact SA text is metadata, not an independently fetched record.
No biological support threshold or classifier was applied.

Two labels have these three fetched segments, ordered along the original query.
All coordinates below are zero-based, half-open. Prefix for both QNAMEs is
`m84039_230418_220405_s4/`; suffix is `/ccs`.

| QNAME suffix | Forward-query intervals | Strand order | Interior reference interval | MAPQ in query order |
|---|---|---|---|---|
| 78253641 | [0,23406), [23406,26583), [26583,28242) | + → − → + | [240685789,240688966) | 60, 60, 60 |
| 169218442 | [0,564), [564,3733), [3733,20304) | − → + → − | [240685789,240688966) | 12, 12, 60 |

Each pattern tiles the stored query without gaps or overlaps and puts the
interior on the opposite strand to its flanks. This is observed alignment
structure, not independently validated molecule structure or unique placement.
The third multi-record label, 43849379, has two cross-strand fetched segments
with different, larger geometry; it is retained, not discarded as inconvenient.
Label 210505410 also has a chr10 SA entry, but that segment was not fetched.

The interior span is 3,177 bp. Do not silently replace the frozen 3,205 bp truth
interval with these boundaries. The truth VCF separately retains its
`ORIGINAL_LOCUS` and confidence-interval fields. These observations do not tune
the earlier 36 conditional comparisons or establish the true alternate allele.

## Scope and preserved evidence

This is existing Vollger/Stergachis CCS/Revio HG002 data, mapped by pbmm2, not
the benchmark's attested 20 caller-input combinations. The prior caller exports
do not locate candidate/filter loss on this separate input. Basic split-read
linkage is already prior art. No new method, caller defect, improvement or
publication result is established.

Full JSONL, manifest, sequence, quality, fixture, code and logs stay outside Git:

```text
Permanent cluster HOME:
/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/inv_mapped_trace_20261014_02
Local retained copy:
/Users/akm/aayushkrm-AlignSSL/runs/inv-mapped-trace-20261014-02.SEsMRo/inv_mapped_trace_20261014_02
```

The complete scratch and HOME leaves compare byte-for-byte. Bundle and output
hashes pass in HOME. No sole copy depends on the 22 October scratch deadline.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `case/alignments.jsonl` | 4,527,955 | `ca77cd139dcb8344cf0697dc7468e97db35344c3d10dfdb42d28eedcbd43df18` |
| `case/manifest.json` | 462,702 | `80f29373616a355ce4c2b23dbba49ade7796ac28a094032c4598b65f508aae3a` |
| [Native fixture receipt](fixture-check-02.json) | 269 | `e905bbd688d4084e475998c4f4da4aff3a2469223a7502af4764d80eb854c2b9` |
| [Complete descriptive summary](observed-query-order-02.json) | 76,813 | `120ab4c4f73a3d20003524d8bf4f0dd28e076107c6ed902643eee4c5ec07c42a` |

The summary binds its generator SHA256
`09aca137feed01ffbafcf303f11f78a346b4715796a3a21888236f957e2c36df`.
An initial ad-hoc summary print had a Python bracket SyntaxError; its corrected
read-only version reports the same saved file. No summary or raw row was edited.

The full manifest records stable BAM/BAI stats, not fresh whole-file hashes.
The [execution record](../../docs/research/2026-10-14-inversion-input-extraction-execution.md)
preserves failed first launch 1604869, its correction, both resource accounts,
inspection errors and the exact code hashes. Resource use for the successful
allocation: one CPU, 1 GiB requested, 2 s elapsed, 0.907 s measured CPU,
17,424 K MaxRSS. No GPU, new DNA, index rebuild, caller or training campaign.

The offline summarizer passes 14 synthetic controls. Combined inversion source,
path, extraction and summary checks pass 69 tests in 3.37 s. These are software
checks, not 69 scientific replicates. The full research goal remains unmet.
