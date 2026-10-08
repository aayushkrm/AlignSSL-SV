# Metadata result: sign convention, not a biological null

Date: October 8, 2026. One exact independently approved v2 command completed
on the cluster. No caller outcome, validated truth denominator or scientific
improvement was measured. The old fixed screen remains closed.

## Complete observation

| Technical census | Rows |
|---|---:|
| Complete prepared rows / unique IDs | 11,490 / 11,490 |
| Canonical literal insertions | 6,960 |
| Canonical literal deletions | 4,530 |
| SVTYPE agrees with literal allele classification | 11,490 |
| Absolute SVLEN agrees with literal allele length | 11,490 |
| Signed SVLEN agrees with the old guard | 6,960 |
| Global sign-only flags, not cross-tabulated by type | 4,530 |
| Missing, noninteger, cardinality or magnitude flags | 0 |
| Eligibility flags | 0 |

Every row remains in the census. Flag counts overlap in general; these
observed sign-only flags are not a new exclusion mask or scoring denominator.
The equality between deletion count and global flag count does not establish
which types carry those flags. Negative insertion values offset by correctly
signed deletions could give the same marginal totals. Main's first update
overstated this as all deletions being positive; independent review corrected
it. No extra genomic pass is requested to support that stronger claim.
The observed header is VCFv4.2 with scalar integer SVLEN and scalar string
SVTYPE, matching the previously archived source declarations.

The first fresh literal contradiction is prepared ordinal 1, chromosome 1,
position 900011. REF/ALT lengths are 76 and 1; canonical DEL length 75;
SVLEN is +75 rather than -75. Identity:
`74c31c555a163fe0ee4134cc2fd8a9580f0b59be5285a0d016e7bca632a8723b`.
No bases, genotype string, read names or full row are reported. This is NOT
replayed through the old pysam/Truvari guard and is not asserted to be its
original failed identity. It is consistent with that failure message.

## Interpretation and boundary

The complete census explains the prepared file's incompatibility with the
strict signed-length contract: 4,530 rows disagree in sign but not magnitude;
the first reported example is a positive-length deletion. It does not show corrupted alleles or a
biological null. Conversely, it does not certify annotation compliance:
[VCF 4.2](https://github.com/samtools/hts-specs/blob/e821e4f02ae25c2175f9a366edca1322d6a2de72/VCFv4.2.tex)
defines deletion SVLEN as negative. The newer 4.5 example is not applicable
proof for this source.

The official [Truvari 5.4.0 annotation implementation](https://raw.githubusercontent.com/ACEnglish/truvari/v5.4.0/truvari/annotations/svinfo.py)
assigns `var_size()` to SVLEN. That is consistent with unsigned annotation,
but the actual producer/version was not established. Static source behavior
does not prove native acceptance of these records. Native type/size and REF
are still UNASSESSED; original-source mapping and biological truth are not
independently validated by these prepared-file counts. No source field was
repaired, normalized or dropped. No caller, original truth/map, BED or
reference body was read by this census.

## Raw evidence and cost

Input: 11,853,747 bytes; acquisition and posthash matched the preparation pin
`c908217f7ec8eba1efe93f51605675a8a8b9676d9c9ca443d1348ad0a00f68d2`.
Source snapshots are stable. Identity-order digest:
`13db07d2c659f578144067d45eea85684816cce6482230e190a1b01b8d627e37`.

Raw [report](../../results/data_audits/svpg_2026/2026-10-08/metadata_census.json):
3,791 bytes, SHA-256 `04f5c349862b84d1a1d7ac9dfaf83460f5045aa7acef9590a9a97c0184a81793`.
Raw time log: 1,115 bytes, SHA-256
`6ce4717ed635e4196ee6745889fc592dff59705164d66b8443fd9ae293b195d8`.
Stdout 3,111 bytes, stderr zero; full output bundle 8,017 bytes. Local copied
report/log hashes match remote values. Keep raw outputs byte-for-byte.

Exit zero; 0.94 user + 0.08 system = **1.02 CPU seconds**; wall **1.16s**;
peak RSS 55,368 KiB = 56,696,832 bytes. Linux caps remained 60 CPU seconds,
120 wall seconds/five-second grace, 4 GiB address space. Named prior-run CPU
plus this run is 422.552707 seconds, not total historical project CPU.
Retain the full **8,623,306,013-byte** read charge, no refund for unused cap.
Logical named-input reservation is not measured physical/cache/runtime I/O.

## Disposition

Close this census as technically complete. Independent result review accepts
completion with the marginal-versus-joint-count qualification above. Main
accepts that correction; no type-specific flag count is inferred.
The publication objective remains active and unmet. A future uniformly applied
absolute-length/native consistency contract may be defensible before any
caller outcomes, but needs a separate prospective rule and review. It must
preserve this raw convention, every row and the old failed gate. REF and
empirical scope still require explicit independent scrutiny. No automatic
restart, retry, threshold change, new acquisition or training follows.

The meaningful next research observation would be an independently supported,
recoverable native discovery failure—not this successful engineering census.
All raw historical attempts and their charges remain unchanged.

## Final software/tracking check

The concurrent manuscript check briefly failed while the existing gate tests
injected a deliberately wrong historical table row into live PROGRESS.
After test restoration the checker passed; source results were unchanged.
Main moved those injections to isolated temporary PROGRESS copies through
the checker's existing `--progress` argument. The checker, historical CSVs,
scientific thresholds and defect classes are unchanged. Eighteen headline/
field checks pass after this test-isolation fix; manuscript reconciliation
passes separately. This is test-harness behavior, not an experiment failure
or resolution of the preserved legacy smoke failure. No full-suite green claim.

Read-only post-run cluster check October 8 13:31:10 +07: account queue empty;
scratch expires October 22 23:02:50, 14 days 9 hours left, one extension.
No job launched/cancelled or unrelated user affected. Small raw reports are
already preserved off scratch; larger existing inputs remain unchanged.
