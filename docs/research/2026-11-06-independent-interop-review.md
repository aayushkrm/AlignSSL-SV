# Independent review: BND interoperability evidence

**Date:** 2026-11-06. **Scope:** commits `ee80196` and `b522150`, the EBI validator protocol, and `results/ebi_validator_case_20261104_run01`. This review examines saved inputs, commands, logs, reports, source code, and primary sources. It does not rerun the historical software or judge the biological truth of the calls.

## Decision

**No-go** for an expensive campaign, a major novelty or biological-impact claim, or a general case-folding repair. The SnpEff behavior and its potential downstream consequences were reported years ago. The current experiment uses one public callset, a manually altered copy, and small synthetic fixtures. It does not measure prevalence, clinical harm, or the accuracy of independent calls.

**Go**, at low cost, for a clearly labeled interoperability regression case and for source-only checks that could falsify a stronger opportunity. The saved results support a specific mechanism in the named versions and settings. They do not yet show an actual end-to-end production failure caused by this mechanism.

```text
Synthetic input ──> SnpEff 5.1d / 5.4c ──> changed BND ALT case
                                             │
Separate synthetic, manually changed fixture ──> Truvari: cross-matches lost

One COLO829 VCF ──> assumed case-alias mapping ──> Verix grouping changes
                            └──────────────────────> Truvari cross-matches lost

Separate EBI fixture ──> remote-name discrepancy gets no added warning
```

The arrows are limited to the recorded tests. The Truvari synthetic test does **not** consume SnpEff's actual annotation output: it recreates the ALT change, adds an invented genotype, and omits SnpEff's `ANN`. The historical COLO829 pre-annotation intermediate and deployed SnpEff binary were not recovered.

## Highest-priority findings

| Finding | Evidence and consequence |
|---|---|
| **The main producer behavior is prior art.** | [SnpEff issue 237](https://github.com/pcingola/SnpEff/issues/237), opened in 2019, shows BND mate names and `ANN` uppercased and already identifies possible downstream pairing and FASTA-lookup effects. [Issue 516](https://github.com/pcingola/SnpEff/issues/516), opened in 2024, gives another BND example with SnpEff 5.2a. Its 2026 closure comment says it was closed during backlog review; closure is not evidence of a fix. The specific Verix, Truvari and validator combinations may still be useful regression examples. A bounded search cannot establish their novelty exhaustively. |
| **A header-derived alias is a hypothesis, not sequence identity.** | The 66 COLO829 mate tokens each have one case-insensitive header match, but a reference can have distinct case-sensitive names. Do not apply case folding to other references without an explicit, unambiguous reference dictionary or alias map. |
| **The transformed COLO829 file is not a consistent release VCF.** | The independent recount found that all 66 changed records retain `ANN` entries whose allele is the original uppercase ALT; none has the new ALT as an `ANN` allele. The comparison isolates a parser behavior, but the result must not be used as an annotation-consistent corrected dataset. |
| **The comparators did not measure biological accuracy.** | Both sides of each cross-comparison derive from the same observed callset. A self-match checks execution and internal matching; it does not validate the variant, the reference mapping, or a caller's sensitivity. Record-level TP/FP/FN labels are comparator categories, not biological error counts. |
| **The validator observation is narrower than a conformance finding.** | In the saved warning-level runs, the two remote-name changes produced no additional warning. The local-CHROM and malformed-ALT controls were detected, but they do not prove that this validator promises remote-contig or mate-graph checks. No reference FASTA was supplied. |

## Raw controls and commands

### SnpEff and the two comparators

The [full SnpEff replay receipt](../../results/snpeff_annotation_replay_20261104_run01/receipt.json) records separate database builds and annotation commands for the two jars. Both builds and annotation commands exited 0. For the two artificial BND records, the saved output changes `A[chrB:20[` to `A[CHRB:20[` and `]chrA:10]C` to `]CHRA:10]C`; local CHROM remains mixed case. The ordinary SNV remains `A>G`. The synthetic gene has a start-codon annotation warning, and CDS/protein checks were disabled for the build. This is a serialization mechanism check, not evidence of correct biological annotation. The [earlier parser-only replay](../../results/snpeff_case_repro_20261104_run01/receipt.json) gives a consistent result in its two-record fixture.

The [synthetic Truvari receipt](../../results/truvari_bnd_case_diagnostic_20261104_run01/receipt.json) and [COLO829 Truvari receipt](../../results/truvari_colo829_case_20261104_run01/receipt.json) contain every actual `argv`, exit code, and summary. The common command shape below uses placeholders; the receipts contain the original absolute paths:

```text
python -m truvari bench --base BASE --comp COMP --output OUT \
  --bnddist 1 --refdist 1 --sizemin 0 --sizefilt 0 --pctseq 0
```

The synthetic commands add `--passonly`; the COLO829 commands do not. The saved `params.json` files also record `pctsize=0.7`, `sizemax=50000`, `pctovl=0`, `reference=null`, `no_single_bnd=true`, `decompose=true`, and `pick=single`. Thus `sizemin=0` and `sizefilt=0` do not mean every possible size-related setting was zero. Applicability of each default to BND matching is a separate code question. The locally installed `variant_record.py`, `matching.py`, and `bench.py` match the receipt hashes; the installed BND matching code compares remote chromosome strings exactly. See also [Truvari v5.4.0 source](https://github.com/ACEnglish/truvari/blob/v5.4.0/truvari/variant_record.py).

| Saved Truvari comparison | TP-base / TP-comp | FP / FN | Native precision / recall / F1 |
|---|---:|---:|---|
| Synthetic, each self-control | 2 / 2 | 0 / 0 | 1 / 1 / 1 |
| Synthetic, either cross direction | 0 / 0 | 2 / 2 | 0 / 0 / `null` |
| COLO829 site-only, each self-control | 66 / 66 | 0 / 0 | 1 / 1 / 1 |
| COLO829 site-only, either cross direction | 0 / 0 | 66 / 66 | 0 / 0 / `null` |

These are two records for one synthetic adjacency and 66 records in one source file. Under the explicit mapping, the 66 records form 33 reciprocal-MATEID pairs; pairs are not necessarily 33 independent biological events. In the cross runs, Truvari's `performance_metrics` sets F1 to `None` because precision plus recall is zero. Preserve that native `null`. A separately defined count-based F1 convention can yield zero when TP is zero and FP/FN are positive, but that is a derived convention, not the native output.

The synthetic self-controls include an invented `0/1` sample and report matching genotypes; that is only a fixture check. In the COLO829 projection, **all sample columns were removed**, and the saved params say `skip_gt=true`. Yet its self summaries contain `TP-comp_FP-gt=66`, `gt_concordance=0.0`, and a `None`/`None` matrix. Those numbers have no genotype interpretation. The cross summaries' empty genotype matrix and zero concordance likewise are not measurements of genotype disagreement.

For Verix, the [first receipt](../../results/colo829_verix_alias_diagnostic_20261103_run01/receipt.json) records exit codes `0,1,1,1`: three runs failed because the normalized input used non-seekable ordinary gzip. The [plain-input repeat](../../results/colo829_verix_alias_diagnostic_20261104_run02/receipt.json) records four zero exits. Its [raw reports](../../results/colo829_verix_alias_diagnostic_20261104_run02/) show 66 versus 66 groups in original self, 33 versus 33 in normalized self, 66 versus 33 with all query groups `partial`, and 33 versus 66 with all query groups `aggregate`. The cross reports omit precision, recall, and F1. Three AD/DP header warnings appear in the successful native stderr. The classes describe this representation-sensitive grouping, not missed biological calls.

### EBI validator

The [attempt 02 JSON](../../results/ebi_validator_case_20261104_run01/attempt02.stdout.json) contains the five actual command arrays, native exit codes, stdout, stderr, and complete summary-report text. Each uses the recorded binary with `-i INPUT -l warning -r summary -o TEMP`; no FASTA or assembly-checker command appears. The table transcribes the native reports:

| Input | Exit | Native result in addition to the common missing-reference warning |
|---|---:|---|
| `valid.vcf` | 0 | No additional warning |
| `uppercase_remote.vcf` | 0 | No additional warning |
| `undeclared_remote.vcf` | 0 | No additional warning |
| `undeclared_local.vcf` | 0 | Warning: local `chrZ` absent from contig metadata |
| `malformed_alt.vcf` | 1 | Error: invalid ALT `Z` |

The independent byte check confirmed that the four altered files are exactly the specified string transformations of `valid.vcf`. The uppercase fixture recreates the two observed SnpEff ALT changes; it is not the actual annotated output and has no `ANN`. The unknown-remote and uppercase fixtures also change the relationship between ALT mate names and the named mate records. Therefore they do not isolate a header-declaration check from a mate-consistency check. The local-name control tests a different field; the malformed allele tests syntax. Neither is a positive control for a remote-mate check. The validator's own `valid` text and exit 0 do not establish complete VCF or reference validity. The [EBI project](https://github.com/EBIvariation/vcf-validator) describes warnings separately from errors.

The [scheduler record](../../results/ebi_validator_case_20261104_run01/accounting.txt) and stderr support a cancelled, unallocated attempt `1614658` followed by completed job `1614659` with four CPUs. The packet does not preserve the full scheduler submission command or an independently signed execution record. It does preserve the validator command arrays and output. The runner checks the binary against the pinned digest before launching it, but the binary and cluster were not independently inspected during this review. The pinned `7326fc83425f5367f9974aaa223f2b48b1854bf9ecd5e9e5eae3899b3107fc87` agrees with the `vcf_validator_linux` asset digest in the [official v0.10.2 release metadata](https://api.github.com/repos/EBIvariation/vcf-validator/releases/tags/v0.10.2). This verifies agreement with the published asset metadata, not the bytes actually executed on the cluster.

## Representation and sequence limits

[VCF 4.3](https://samtools.github.io/hts-specs/VCFv4.3.pdf), sections 1.4.7, 1.6 and 5.4, distinguishes a breakend's local replacement sequence, the remote `chr:pos` identifier, and bracket orientation. Base letters in alleles are case-insensitive, but that does not establish a general rule that differently cased reference identifiers name the same sequence. Contig declarations are **recommended** for textual VCF and required for BCF; an undeclared remote identifier alone is not a demonstrated VCF 4.3 violation. In these fixtures the remote names also fail to match the declared mate records under exact identifiers. This is an interoperability and interpretation problem; it is not a basis to call every exact-string consumer wrong.

Do not require exact reciprocal positions as a universal validity rule. VCF 4.3 section 5.4.8 gives microhomology and `CIPOS` examples where the mate's ALT coordinate differs from the other record's chosen POS. The format also permits single breakends and multiple mates. A future checker needs explicit cases for those forms, orientation, reference identity, and uncertainty; it must not silently merge ambiguous names.

The independent source recount reproduced 66 caller BNDs: 51 local anchors equal REF and 15 differ; the separate lifted truth file has 13 equal and 13 different out of 26. These counts are records, not errors. A BND replacement sequence is allowed to differ from REF. The [nanomonsv synthetic packet](../../results/nanomonsv_bnd_source_repro_20261104_run01/) supports the narrower old-versus-fixed converter observation; the [upstream 2026 commit](https://github.com/friend1ws/nanomonsv/commit/04da795fa71adf495e50c857099ebf3a6ef6f64a) had already identified and changed that converter behavior. It does not prove the precise binary, input, or cause of the historical COLO829 allele. The truth file must not inherit that causal explanation. The retained [junction note](2026-11-03-colo829-junction-sequence-check.md) itself flags the J1, J2, and J3 sequence interpretations as unresolved; do not promote its original draft conclusions.

## Independent integrity and provenance checks

I recomputed SHA256 values for the entries named in eight relevant receipts: 209 of 209 listed packet-file entries matched, with no missing files. These comprise both Verix attempts, the nanomonsv replay, both SnpEff packets, both Truvari packets, and the EBI packet. The EBI preparer, EBI runner, and synthetic source also match their recorded digests. All six COLO829 Truvari workspace files and both local SnpEff jars match their recorded hashes. Hashes establish agreement with the saved manifests; because the manifests and outputs share provenance, they do not by themselves prove when, where, or by which binary the work ran.

I separately read the local source VCF and projected inputs in memory. The published caller gzip has SHA256 `ae2d7b02fea3dda159e602c6124ef1911324efb692682ad9977eac697d6e5042`; its decompressed bytes equal the plain original. Of 438 original/normalized lines, 66 differ, all only in a uniquely case-matched remote ALT token. The source has 195 contig declarations and 66 BND records; none of the 66 original remote names exactly matches a declared contig. All 66 have reciprocal `MATEID` and coordinates after the stated case-folding rule. This recount did not independently validate their biological orientation or allele sequence. The 336-line site-only projection retains the original first eight fields and order for all 66 BND records; its BGZF files decompress to their plain counterparts. The complete per-token manifest is [here](../../results/truvari_colo829_case_20261104_run01/input-manifest.json).

The [independent-callset inventory](2026-11-04-independent-callset-inventory.md) found 1,100 named members in a remote ZIP but inspected only four selected VCF headers. None of those headers declared SnpEff or `ANN`; the check did not inspect variant records, verify member CRCs or the full archive hash, or authenticate donor identity from filenames. It does not supply an independent annotated cohort or a prevalence denominator.

The protocol says it was written before execution. That is an author statement, not independently established by the retained evidence. The report filename contains a timestamp consistent with 2026-11-04 local time, while Git first records the protocol in `14296ed` on 2026-11-06; neither fact proves the protocol's prior existence or its exact contents at run time.

At review start, HEAD was `b522150` and the protocol and packet were untracked. During the review, the branch advanced to `14296edf59b31158d1661df43412cae3577312ab`, which tracks those files; the local origin-tracking ref also appeared at that commit. The reviewed protocol and packet matched the tracked version when checked. This reviewer made no commit, push, or change to the inputs. A moving local tracking ref is not independent proof of a remote push.

## Minimum gates before more work

1. **Check the practical question first.** Identify a real, version-pinned downstream workflow and the decision affected. Obtain the actual pre- and post-annotation files, reference dictionary, and commands for at least one independently sourced workflow. Demonstrate an observed failure or changed actionable result, not just a constructed mismatch. Compare with an explicit reference-aware alias map and ordinary existing validation/repair practice.
2. **Use a cheap adversarial fixture matrix.** Include distinct `chrA` and `CHRA` contigs, missing and ambiguous aliases, all four bracket forms, missing/multiple mates, orientation errors, valid `CIPOS` uncertainty, local versus remote unknown names, and malformed ALT. Check `ANN`, sample fields, and reference bases separately. A checker should fail closed or report ambiguity; do not blindly rewrite identifiers.
3. **Predefine what would justify scale.** Specify inclusion rules, the count of independent workflows and samples, event-level denominators, practical outcome, comparator baseline, and a meaningful effect threshold before selecting cases. Check access and costs without downloading a large archive. If no independent workflow or meaningful change is found, stop at a regression note.
4. **Require independent evidence for stronger claims.** A biological accuracy claim needs suitable truth, sequence/reference verification, and an evaluation independent of the exploratory source. A clinical claim needs evidence of an actual decision consequence. Neither follows from `FP`, `FN`, self-F1, or validator exit status here. The [Truvari paper](https://doi.org/10.1186/s13059-022-02840-6) already establishes SV comparison and representation as an important general problem; its version-3.1 analysis does not validate this version-5.4 BND experiment.

## Research and configuration record

I used Exa and Parallel Search for bounded source discovery, then checked the VCF specification, tool source, issue reports, release metadata, and the original Truvari paper. Exa searches requested 25 results across four targeted workstreams, including a follow-up; I checked selected results, not every returned page. The Life Sciences Literature NCBI Entrez workflow resolved the Truvari paper to [PMID 36575487](https://pubmed.ncbi.nlm.nih.gov/36575487/). Scite's available connector rejected access because the account lacked a paid plan or active trial. Firecrawl operations were not exposed among the available tools; no Firecrawl CLI was assumed. The search is not exhaustive.

Requested model names and effort levels in historical notes are configuration requests, not backend attestations. I could verify the local tool versions, hashes, command arguments, and native outputs described above; I could not independently verify this review's exact backend model slug or effort, nor those of earlier workers. No expensive job was started.
