# Structural-variant breakpoint uncertainty: opportunity screen

Date: 2026-10-12  
Scope: breakpoint location, junction sequence, and clinical consequence. This is not genotype-GQ calibration or record harmonization.

## Decision

**No-go as an active study today.** There is a consequential candidate question, but the checked sources do not establish a public, independent case set that can answer it. Do not book work or describe this as a selected campaign. The main project's STOP/PIVOT before S2 remains in force; accepted HG002 input and caller infrastructure are reusable, not evidence or motivation for this question.

## Candidate question

When a caller reports an imprecise breakpoint, do independently supported, sequence-distinct breakpoint or junction alternatives change the gene, transcript, fusion, or diagnostic conclusion? Does the current workflow expose that unresolved state, or does it annotate one representative coordinate? Measure the caller's reported span against orthogonally resolved sequence as an empirical range check. Do not assign a probability to positions inside the span, or a nominal coverage level, unless that caller's primary documentation explicitly claims one.

This is narrower than the prior repo proposal to “report uncertainty when reads cannot distinguish alternatives.” That proposal already identified high novelty risk and required sequence-aware truth; see [the earlier breakpoint-refinement screen](2026-09-23-research-pivots.md). This note does not claim that the refined question is novel.

## Evidence and decision

| Check | Primary evidence | Readout |
|---|---|---|
| Is the clinical consequence real? | A 2026 balanced-translocation preprint resolved breakpoints to single-base positions, reported five new or refined diagnoses, and Sanger-confirmed six events in one cohort. A separate BRCA1 family study found that the structural interpretation and pathogenicity assessment changed when a reference-specific region was resolved with long reads, optical mapping, RNA evidence, and Sanger confirmation. ([Jammihal et al., preprint, posted 2026-10-05](https://doi.org/10.64898/2026.09.30.26363717); [Schwartz et al., 2025-07-31](https://doi.org/10.1038/s41525-025-00517-0)) | Yes. A wrong or unresolved junction can change which gene or transcript is disrupted. The preprint shows current clinical workflows can resolve a defined class; it is not a peer-reviewed validation of interval uncertainty. |
| What do VCF intervals claim? | VCF v4.5 defines CIPOS as pairs of integer offsets around POS and CIEND as offsets around inferred END. IMPRECISE records without CIPOS have an unspecified interval. HOMSEQ is used with CIPOS when breakpoint homology exists. These definitions state no nominal probability or 95% coverage. ([official VCF v4.5 specification](https://samtools.github.io/hts-specs/VCFv4.5.pdf)) | Treat these as producer-defined coordinate spans. Do not call them calibrated confidence bounds or score them against an invented 95% target. The spec's word “confidence” does not supply a coverage level. |
| What does a caller say? | DRAGEN says local assembly can fail to explain the data, especially in repeats; it may then report approximate breakpoints as IMPRECISE. The manual does not state a probability or coverage level for that coordinate span. ([DRAGEN SV caller documentation](https://help.dragen.illumina.com/dragen-v4.5/product-guides/dragen-v4.5/dragen-dna-pipeline/sv-calling.md)) | There is a real unresolved-input state. A format label alone does not establish how often the true, sequence-resolved junction falls inside the reported span. |
| Closest benchmark control | A 2026 study compared Truvari, EvalSVcallers, and SVbenchmark across five callers. Matching rules use breakpoint distance, overlap, size, or alternate-sequence similarity; changing rules changed TP/FP/FN labels and summary scores. Its resampling intervals quantify benchmark-score variation, not breakpoint-location coverage. It does not test CIPOS/CIEND containment or clinical consequence. ([Maden et al., 2026-09-23](https://doi.org/10.1371/journal.pcbi.1014824)) | Generic SV matching or a new interval formatter would repeat existing work. A viable question must link a non-equivalent sequence alternative to a changed consequence and independent truth. |
| Repeat-anchor control | Analysis of 64 phased HGSVC haplotypes found ancestry- and homology-associated breakpoint placement differences; read-based callers increased disagreement relative to assembly callers. These are known representation and alignment effects, not by themselves uncertainty about distinct biological structures. ([Audano & Beck, 2024](https://doi.org/10.1101/gr.278203.123)) | Compare alternate haplotype sequence before calling a shifted coordinate an uncertain or different biological breakpoint. Exclude equivalent anchors from the primary outcome. |
| Residual space in the clinical preprint | The 2026 workflow clusters BNDs within 1,000 bp and uses a 50-bp position-span rule for event classification. It excludes some repeat-mediated and complex three-or-more-chromosome events and does not phase all alternatives. ([methods and limitations](https://doi.org/10.64898/2026.09.30.26363717)) | A possible residual is genuinely distinct structures whose consequences differ. The paper does not provide a calibrated interval target or a public, independently resolved case set for that residual. |
| Public material without new acquisition | The preprint identifies public 1000 Genomes DRAGEN v4.4.7 VCFs and CRAMs at s3://1000genomes-dragen-v4-4-7. The benchmark names NA12878 reads SRR17658585, HGSVC2 v1.0 freeze3.sv.alt.vcf.gz, and public code release v1.1.0 at [gamzemdn/sv-benchmarking](https://github.com/gamzemdn/sv-benchmarking). The 2024 HGSVC analysis used 64 phased assemblies. ([Jammihal et al.](https://doi.org/10.64898/2026.09.30.26363717); [Audano & Beck](https://doi.org/10.1101/gr.278203.123); [Maden et al.](https://doi.org/10.1371/journal.pcbi.1014824)) | These are candidate technical controls, not a qualified clinical cohort. The benchmark is restricted to DEL/INS. Same-sample caller-VCF/assembly crosswalk, original interval fields, and independent event truth were not verified. The inspected clinical preprint does not establish a public case-level sequence-plus-outcome package. No files were downloaded. |

## Cheapest falsifier and stop rules

The cheapest next check is a source-only crosswalk of the named public manifests and repositories. Confirm that at least one same-sample set has (1) the original caller VCF with its breakpoint span, (2) independent sequence-resolved junction truth, and (3) a gene/transcript consequence that can be recomputed. Keep coordinate shifts that preserve the alternate haplotype separate from sequence-distinct structures. No job or data acquisition is part of this note.

Stop if any of these holds:

- No same-sample crosswalk or no independent junction truth is available.
- All apparent errors are equivalent repeat/microhomology anchors, benchmark matching choices, or annotation/serialization defects.
- No sequence-distinct alternative changes a clinically relevant consequence, or a current caller plus its existing confirmation workflow already gives the same conclusion.
- There are too few independent events to estimate a prespecified useful consequence-change rate. Treat this as inconclusive, not as a biological null.

The strongest possible result would show, across independently adjudicated clinical events, that current outputs suppress sequence-distinct alternatives whose consequences differ, and that an explicit uncertainty-and-resolution workflow prevents or changes a real diagnostic decision. That would be a meaningful clinical-methods contribution. A malformed field, parser error, missing annotation, or repeat-anchor normalization issue alone is a software or representation bug, not the scientific result.

## Existing-project guardrails

- The current research index records STOP/PIVOT before S2 and says accepted whole-DNA input does not establish biological value. This sidecar leaves that decision unchanged.
- The earlier P3 screen already names uncertainty for read-indistinguishable alternatives and requires orthogonal sequence truth; it warns to stop on representation-only or unresolvable residuals. The October 7 territory review also rejected generic junction-mechanism claims without causal truth.
- The [October 1 confidence-contract note](2026-10-01-confidence-contracts.md) concerns genotype likelihood/GQ behavior. It is out of scope here and is not reopened.
- The [October 7 territory review](2026-10-07-fresh-territories-and-acquisition.md) rejected generic junction-mechanism claims without causal truth.
- No direction or publication claim is selected. Main retains selection and independent review.

## Search and evidence limits

- Exa: four distinct searches, ten requested result slots each (40 slots, not 40 unique papers). The exact discovery window was 2025-10-12 through 2026-10-12. The exposed Exa search schema has no date-filter parameters; candidate sources used here were date-checked, but the 40 slots were not all deduplicated or fully screened. Full relevant methods/claims were read for four primary papers: the 2026 preprint, the 2026 benchmark study, the 2024 breakpoint-placement study, and the 2025 BRCA1 case. The 2025 and 2024 papers are older load-bearing controls.
- Life Sciences Literature / NCBI Entrez: one date-limited PubMed search returned ten IDs; summaries were requested for those ten. PMC metadata was checked for the 2024 and 2026 benchmark papers. One adjacent 2026 hemophilia result had no PMC record in this lookup and its PubMed page was unavailable through Exa; it is not used as evidence.
- Scite: three targeted searches were attempted. All returned the paid-plan/trial requirement and zero records. No billing or account change was made; NCBI Entrez and primary pages were the fallback.
- Primary semantics: the official VCF v4.5 CIPOS/CIEND section was read directly. No 95% level is present in those definitions. The DRAGEN page and relevant paper methods/limitations were also read. Search results alone were not treated as proof of absence or novelty.
- No jobs were booked or submitted. No genomic data, binaries, packages, or credentials were downloaded or installed. No Git operation or historical-result edit was made. Only this document is in scope.
- The broad goal requested GPT-6.1 Sol at High effort; no tool in this task attested the requested model/effort, so this note makes no claim that it was met.
