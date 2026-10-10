# Native controls for repeat-instability inference

Date: 8 October 2026. Scope: sequence interruptions, allele-specific methylation, and somatic instability methods only.

Requested worker configuration: GPT-6 Luna / maximum effort. No worker was dispatched. This records the requested configuration; it does not attest to the active backend.

Main integration: no proposed joint-state test is approved. A changed call
replicated on the same assay does not by itself establish correctness, a
causal methylation effect, or contribution beyond native methods. Independent
adjudication of a fixed consequential claim is still required. See
[source/outcome audit](2026-10-08-repeat-outcome-source-audit.md) and
[main disposition](2026-10-08-three-direction-disposition.md).

## Decision

STOP a standalone repeat-length distribution or noise-inference method claim. Keep one joint-state hypothesis only as a bounded kill test, not as a selected research lead.

**Hypothesis to test:** Within one expanded repeat allele, the phased interruption pattern and allele-specific CpG methylation jointly change the inferred expansion tail after baseline repeat size is fixed. This could change which haplotype is called stable or actively expanding. It is not established by the sources below.

**Strongest reason to reject it now:** Recent native methods already measure distribution shifts and haplotype-specific instability. The remaining idea is to join those outputs to sequence and methylation state. No independent evidence here shows that this join changes a biological conclusion. A better classifier, more accurate total length, or a length–methylation correlation is not enough.

## Closest native controls

| Control | What the source establishes | Consequence for this proposal |
|---|---|---|
| **SCIA / Smith et al., v3** ([full text](https://www.biorxiv.org/content/10.64898/2026.03.12.707943v3.full.pdf), [version history](https://www.biorxiv.org/content/10.64898/2026.03.12.707943v3.article-info)) | Direct distribution control. It normalizes repeat-size histograms, aligns them to the day-0 mode, and uses delta plots to measure instability frequency, expansion/contraction bias, and average change size. It also compares these measures with an instability index and uses statistical tests between conditions. | **Nearest control** for any new distribution or noise summary. Generic inference from repeat-length distributions is already covered. The paper does not establish the proposed interruption-by-methylation effect. |
| **MosaicTR / Kim (2026 preprint)** ([full text](https://www.biorxiv.org/content/10.64898/2026.03.16.712141v1.full-text)) | Reads haplotype-tagged long reads, sizes repeats from CIGAR operations, applies motif-unit weights, and reports a per-haplotype Haplotype Instability Index. Pairwise modes compare tissues or time points. Its sizing method does not realign read sequence. The reviewed methods do not include interruption sequence or methylation as HII inputs. | Strong control for haplotype-specific somatic instability. It identifies a narrow residual: the reported instability score does not explain its length distribution by changing repeat sequence or methylation state. This is a limitation of the reported score, not proof that no other tool can make the join. |
| **TRGT / Dolzhenko et al.** ([paper](https://www.nature.com/articles/s41587-023-02057-3)) | The paper abstract reports per-allele consensus sequence and methylation summaries from PacBio HiFi reads, supporting reads for each allele, and detection of mosaicism in known expansions. | Close sequence/methylation control. The full methods were not available in this audit, so I make no claim about a missing TRGT feature. |

The 2026 Nanopore genotyping assessment also warns that length concordance does not predict sensitivity to confirmed pathogenic expansions. It supports sequence-level evaluation, not a new joint-state contribution ([Genome Biology](https://link.springer.com/article/10.1186/s13059-026-04210-y); abstract-level screen only).

## Finite falsifier

Use one preselected repeat locus, one sequencing platform, and one phased allele observed in paired passages or tissues, plus one untouched independent replicate. Reproduce SCIA distribution metrics and MosaicTR haplotype instability as the baselines. Add interruption state and allele-specific methylation to the same-haplotype model.

Pass only if the joint state changes a predeclared conclusion about expansion direction or stable-versus-expanding status, and that change repeats in the independent sample. Reject if the conclusion stays the same or fails to replicate. Better length accuracy, classifier score, or methylation correlation alone fails this test.

Independent outcome-label feasibility: **unknown**. This audit did not inspect cohort availability or outcome labels. Unknown does not mean that no suitable data exist. The main thread owns the clinical, functional, and longitudinal label audit.

## Search and retrieval record

- Date window: 8 April 2025–8 October 2026. Older native controls were retained where they remain close controls.
- Exa: three targeted searches, 10 result slots requested each (30 requested). The first result display was clipped; searches two and three were compacted across 20 result entries. Search-result cards were not treated as full method reads.
- Load-bearing full-text methods reads: **2 of 3 slots** — SCIA v3 and MosaicTR. TRGT and the 2026 Nanopore assessment were abstract-level screens only. Search-only controls included TRGT-denovo, LongTR, Vamos, Straglr, ATaRVa, TRsv, HMMSTR, MASTR-seq, and Owl; these are not used to claim that a feature is absent.
- Firecrawl paper-reader calls returned an invalid-argument error for the Nanopore assessment and no indexed passages for MosaicTR/TRGT. Direct page retrieval then supplied MosaicTR full text and the SCIA v3 PDF. TRGT full text remained paywalled; its abstract is the limit of the evidence used here.
- The bioRxiv metadata API returned an HTTP error. The publisher's article-history page confirms v3 is the most recent version; both that page and the v3 PDF give 2 October 2026. The date was read from the publisher page, not inferred from the DOI.
- No raw genomic data, scientific tools, installs, jobs, Git operations, credentials, or other file edits were used. No experiment campaign or novelty claim is approved.
