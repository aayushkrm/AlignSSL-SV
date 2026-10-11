# Balanced and complex rearrangement: opportunity screen

Date: 12 October 2026. Scope: balanced and complex rearrangement detection,
exact structural genotype, and the resulting diagnosis decision.

## Decision

No new study lead passed all three gates: a consequential question, a strong
comparison against current methods, and public independent case-level truth.
Keep the earlier closures as bounded results, not proof that the whole field is
closed. The October 7 inversion and centromere reviews and the October 9
transcript scout remain relevant limits ([inversion/centromere decision](2026-10-07-inversion-centromere-decision.md),
[centromere screen](2026-10-07-centromeric-territory.md),
[transcript scout](2026-10-09-structural-transcript-falsifier-scout.md)).

The closest low-cost falsifier was a paper-only check of the new complex-
inversion benchmark for independent truth and a real diagnosis endpoint. The
benchmark has public truth files, but it has no patient phenotype or diagnosis
outcome. Assembly callers also use the haplotype contigs used to build its
truth. This does not show that its results are wrong. It does block a new
clinical claim from this dataset alone.

Do not start an HG002 preparation, caller, or other native job from this note.
The accepted DNA read set and retained infrastructure stay as recorded in the
research index. Main review must precede any compute.

## Three concrete questions

| Disposition and question | Why a positive result could matter | Closest strong prior art | Public truth and data access | Cheap non-tuning falsifier and interpretation | Strongest reason to reject |
|---|---|---|---|---|---|
| **Reject.** Can short-read WGS recover a balanced reciprocal translocation that changes a rare-disease diagnosis? | A correctly identified gene-disrupting translocation can provide a molecular diagnosis and clarify inheritance. | A medRxiv preprint posted 5 October 2026 analyzed 16,131 people in five cohorts. It reports 46 balanced translocations and five new diagnoses. It reports Sanger confirmation for six Birth Defects Biorepository events. The preprint is not peer reviewed. [Jammihal et al.](https://doi.org/10.64898/2026.09.30.26363717) | The methods identify public 1000 Genomes data. The diagnostic cohorts use CHOP, GREGoR, and UDN data stores. This version gives no public case-level read or callset accession for the five new diagnoses. The authors say sensitivity is not measured at scale and functional validation is incomplete. | Metadata-only check: find a new diagnosis with public reads plus orthogonal truth from a separate assay. I found no such open case in the inspected version. If one appears, it could support a new fixed-case audit. If none appears, this candidate is not testable on public independent truth; that is not a biological null. | The preprint already makes this detection and diagnosis claim. Repeating its BND filters or its five case interpretations would not be a distinct contribution. |
| **Reject.** Does the exact phase and derivative structure of a multiway translocation change the gene genotype or diagnosis beyond paired breakends? | Phase can show which derivative carries a disrupted gene, whether events are linked, and how a rearrangement segregates. This could change a diagnosis. | The 2026 preprint states that its workflow cannot phase events and may miss or split rearrangements involving three or more chromosomes. Recent graph and complex-SV methods include [SVPG](https://doi.org/10.1038/s41592-026-03219-2), [Severus](https://doi.org/10.1038/s41587-025-02618-8), and [SVision-pro](https://doi.org/10.1038/s41587-024-02190-7). A 2026 case report combines karyotype, ONT, and X-inactivation analysis. [Qiao et al.](https://doi.org/10.3389/fgene.2026.1811784) | The case report provides its contributions in the article and supplement, with further data available by request. The UDN and GREGoR cases are not public case-level inputs. I found no open case with sequence reads, independently confirmed derivative structure, and a clinical adjudication that can be held out. | One source-only gate: require one open case with karyotype or FISH, sequence-resolved derivatives, and a diagnosis set before analysis. If found, ask whether a fixed current workflow changes the diagnosis. If not found, stop; case-report repetition is not a positive result. | The scientific gap is plausible, but the public independent truth needed to test it is not established. A few already published patient examples would repeat known methods. |
| **Reject as a paper lead.** Do current callers misassign exact genotypes for complex, repeat-rich inversions in disease-relevant cases? | A wrong haplotype or zygosity could change inheritance or gene-disruption interpretation. It matters only if it changes a real diagnosis decision. | An August 2026 peer-reviewed benchmark tested nine callers, including Severus, Sniffles2, SVision-pro, PAV, and SVIM-asm, on five reference samples. For Tier 2 complex inversions, it reports about 50–68% recall for Severus/Sniffles2 with VACmap, about 30–50% for PAV, and zero for SVIM-asm. [Cheng and Sedlazeck](https://doi.org/10.1186/s13059-026-04223-7). [SVPG](https://doi.org/10.1038/s41592-026-03219-2) is a recent pangenome-graph comparator. | Benchmark truth uses Strand-seq plus phased assemblies. Truth VCFs are public at [Zenodo](https://zenodo.org/records/17624133), with analysis code at [INV-Benchmark](https://github.com/jamesc99/INV-Benchmark/). The five samples are reference genomes, not clinical cases. PAV and SVIM-asm use the same haplotype contigs used to build the truth. Exact independent truth for a disease-linked non-HG002 case is unknown from the inspected sources. | The paper-only gate is complete: the public release supports caller benchmarking, but not diagnosis testing. A future positive would require a non-HG002 case with an independently confirmed exact genotype and a clinical outcome. A null would be no such case, or no change in exact genotype or diagnosis. No reads or callsets were opened. | The paper already tests detection and genotyping across the caller panel. The sample set has no phenotype or clinical decision. Re-running callers would repeat the benchmark, and shared assemblies weaken an independent comparison for its assembly callers. |

## Prior-art boundary

Severus and SVision-pro directly address complex rearrangements. SAVANA is a
somatic tumor-normal caller, so it is not a direct constitutional-carrier
baseline. The recent inversion benchmark already includes Severus, SVision-pro,
PAV, and SVIM-asm. SVPG adds a pangenome graph approach. These papers report
variant calls and benchmark performance; they do not validate a new clinical
decision rule for balanced carriers. [SAVANA](https://doi.org/10.1038/s41592-025-02708-0),
[Severus](https://doi.org/10.1038/s41587-025-02618-8),
[SVision-pro](https://doi.org/10.1038/s41587-024-02190-7),
[SVPG](https://doi.org/10.1038/s41592-026-03219-2).

Therefore, no new decoder, provenance framework, general caller leaderboard,
or clinical-utility claim is selected. The remaining multiway-phasing question
stays open only as a data-feasibility question. Public case truth is currently
unknown, not absent from the field.

## Search and source record

- Fresh-paper window: 12 October 2025 through 12 October 2026, inclusive.
  Older strong controls were allowed.
- Exa: five distinct queries, eight results requested per query; 40 result
  cards returned and screened by title, date, and source text. Query angles:
  current complex-SV methods; clinical cases; diagnostic consequence; public
  independent truth; and the named tool prior art. Three fetch batches read
  eight publisher, author, or data pages. Four primary papers were read for
  methods and data access: the inversion benchmark, the balanced-translocation
  preprint, SVPG, and the 2026 case report. Result cards are not papers read.
- Life Sciences Literature: two PubMed searches returned 10 and 5 IDs; two
  summaries checked metadata. Three PMC DOI lookups returned two open-access
  records and one empty result. One medRxiv metadata request confirmed the
  preprint title, version, and 5 October 2026 posting date. No raw response was
  saved. PubMed results were not used to infer absence.
- Scite: one targeted search was blocked because the connected account needs a
  paid plan or active trial. No billing change was made. Exa, Life Sciences
  Literature, and primary publisher pages supplied the alternative evidence.
  The direct web open for the medRxiv PDF also failed; Exa supplied the paper
  text. No Firecrawl call was used.
- Limits: this was a bounded screen, not an exhaustive novelty search. It does
  not prove field-wide absence. The exact clinical truth for the controlled
  cohort cases and the external support for each non-HG002 inversion are
  unresolved.
- The requested Luna/max configuration is recorded as requested, not attested.
  No independent reviewer was run and no reviewer approval is claimed.
- No genomic reads, CRAMs, BAMs, VCFs, assemblies, or reference objects were
  downloaded or opened. No software was installed. No job or experiment ran.
  No Git action occurred. Only this note was written.
