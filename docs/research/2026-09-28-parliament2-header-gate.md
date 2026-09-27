# Parliament2 HG002 caller-file provenance gate

**Checked:** 2026-09-27 to 2026-09-28. **Purpose:** decide whether small published files can support a controlled caller-candidate experiment. This is an input audit, not SV scoring or a performance result.

## Reproducible input check

The first-party Parliament2 result tree at commit `b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6` supplies nine VCF files representing six historical caller families. `results/caller_source_audit/2026-09-27/parliament2_manifest.json` pins their raw URLs, byte sizes, and Git blob SHA-1 IDs. `scripts/audit_published_vcf_headers.py` fetched 9,232,207 bytes, verified all nine sizes and blob IDs, and recorded SHA-256 digests and VCF header fields in `results/caller_source_audit/2026-09-27/parliament2_headers.json`. It saved no raw VCFs and scored no variants. This verifies the published blobs, not their original caller workflows.

| Caller family | Files | Reference/source and dictionary evidence in headers | Sample column |
|---|---:|---|---|
| BreakDancer | 1 | `Breakdancer` source; no reference or contig declarations | none |
| BreakSeq2 | 1 | `/home/dnanexus/ref.fa`; 86 contigs with lengths, no M5 | HG002-labelled filename |
| CNVnator | 1 | `1000GenomesPhase3_decoy-GRCh37`; no contig declarations | `cnvnator`, not an HG002 ID |
| Delly | 4 | No reference, source, or contig declarations | HG002-labelled filename |
| LUMPY | 1 | `LUMPY` source; no reference or contig declarations | HG002-labelled filename |
| Manta | 1 | `GenerateSVCandidates 1.4.0`, local `ref.fa` path; 86 contigs with lengths, no M5 | HG002-labelled filename |

All nine lack contig-sequence M5 evidence. Manta and BreakSeq2 provide build-compatible contig lengths, but neither the local `ref.fa` header path nor the shared “GRCh37” label proves exact sequence identity. These are six caller families, not nine independent callers. BreakDancer has no sample column; CNVnator's `cnvnator` column is a tool label. Filenames and publication context point to HG002, but those headers alone do not prove sample identity. Nor do they establish that the files are unfiltered emitted candidates or bind each file to the README's executable version, reads, depth, and filters.

**Decision:** no-go for a controlled contemporary multi-caller *candidate-generation ceiling* from these files. A separately labelled historical released-callset/matcher smoke test remains possible after a frozen protocol; it must not be presented as internal-candidate recall, independent donor validation, or current state of the art. No scoring or cluster campaign is approved by this audit. A valid candidate-generation test requires same-donor, same-reads, same-reference, documented candidate-stage inputs and prespecified truth/BED/matcher rules; unrelated-donor confirmation is separate.

## Independent scientific challenge

An independent Sol/high review was **requested** for the conditional direction triage and caller-source inventory. The runtime did not expose independently verifiable model-variant or reasoning-effort metadata, so this is not recorded as an attested Sol/high run. Its verdict was that no scientific recall experiment is ready to freeze. It identified five open gates:

1. Historical, incompletely documented *final* outputs cannot estimate internal candidate generation; HitSV is a separate build/coverage and single-caller source.
2. Pair each truth VCF with its build-matched benchmark BED. Prespecify full-event and breakpoint-flank eligibility, complex-event grouping, local one-to-one matching, and eligible/excluded denominators.
3. HG002 is development data. Parliament2 used earlier HG002 truth in its publication; v0.6 is not a second donor or clean confirmation. Keep unrelated confirmation donors untouched.
4. The direction memo's numeric thresholds and compute cap lack denominator, power, and runtime justification. Predeclare a primary endpoint/stratum, sensitivity analyses, adjudication frame, unresolved-case rule, and locus-level uncertainty; HG002 block bootstrap is not between-donor uncertainty.
5. Claims need compatible individual-caller baselines, filtered/unfiltered outputs where available, a union, ensemble/catalog comparison, false-positive/precision cost, and orthogonal allele/read support for misses. A historical HG002 miss list is methods-development evidence, not a publishable gain.

**Next gate:** find a compatible, documented multi-caller candidate-stage panel or construct one under a separately reviewed bounded protocol. If not feasible, record that failure and reconsider the direction; do not rename released-callset matching as candidate-generation research. HGSVC3 reference and donor-callability blockers remain independent.

## Artifact integrity

The manifest SHA-256 is `37af87511b430af196bbac54d6f2155a366a6c898558d19f3ba3657b8d6a12d1`; the header-report SHA-256 is `cf95118791622f9e71a99159174dcddc61b7cc96e2be209ac3b4ea6a26021886`. These cover the JSON files, not the original workflows or raw reads. All nine VCF-byte SHA-256 values are in the report. No raw VCFs, reads, private keys, or caller outputs were committed.
