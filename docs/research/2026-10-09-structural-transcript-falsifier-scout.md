# Structural-transcript falsifier scout

Date: 9 October 2026. Bounded literature and access check; one owned note.

## Decision

**No new one-locus falsifier is supported by the verified public material in this pass.** The closest biologically specific case is already reported, and the case-level sequence data are controlled. Its open paired DNA/RNA records are different reference cell lines used for assay benchmarking; they cannot validate the UDN318336 allele. This is a data and prior-result limitation for this candidate, not a biological null, a two-donor rule, or a general stop on structural-variant research.

The only concrete one-case candidate found is UDN318336's X;13 translocation. A direct comparison would fix the ordinary baseline first—reference-based breakend consequence plus measured copy number—then ask whether that baseline identifies the phased, full-length *PDK3–MAB21L1* fusion and its non-NMD coding path in the same skin-fibroblast sample. The falsifying outcome would be a baseline that misses or misstates that transcript path. This is a specific test, but it is not a new recommendation: the paper already reports the fusion from those data, and the raw case data require controlled access.

This pass does not require prior proof that the ordinary baseline fails. One adequately supported donor would be enough to falsify a prediction; no campaign-level power or donor replication is required. The obstacle here is that the exact case is both already published and not publicly accessible.

## Closest exact case, and why it does not qualify

The primary case is UDN318336: a chromosome X;13 balanced translocation studied in skin fibroblasts. The paper reports haplotype-resolved long-read DNA and full-length RNA from that same material. It reports that the translocation affects *NBEA*, *PDK3*, *MAB21L1* and *RB1*, including a full-length *PDK3–MAB21L1* fusion transcript. The reported fusion joins *PDK3* exon 11 to *MAB21L1* exon 2 and adds 66 amino acids to PDK3. Those observations already answer the generic question that long-read RNA can reveal a transcript consequence beyond a gene-level breakpoint label. Repeating this published case would not be a new result. [Vollger et al., Nature Genetics (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12077378/).

The paper's data statement says the UDN case data require a dbGaP data-access request. The public BioProject contains four other samples used for assay benchmarking, not UDN318336. Thus the exact case is not an open empirical falsifier in this scope. The paper also derives the structural and transcript interpretation from the same case material; it is not an independent held-out validation of a new consequence claim. The study's reference-based variant annotation could be a comparator, but no annotation failure should be inferred without running that comparison on new or independently available evidence.

### Public records checked (metadata only)

The paper identifies the four public lines as GM12878/HG001, HG002/GM24385, HG02630 and GM20129. The [NCBI BioProject](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1124997) and [ENA run listing](https://www.ebi.ac.uk/ena/browser/view/PRJNA1124997) expose matched genomic and long-read transcriptome runs:

| Line | BioSample | RNA run | Genomic run |
|---|---|---|---|
| GM12878 / HG001 | [SAMN41878944](https://www.ebi.ac.uk/ena/browser/view/SAMN41878944) | [SRR29438432](https://www.ebi.ac.uk/ena/browser/view/SRR29438432) | [SRR29438436](https://www.ebi.ac.uk/ena/browser/view/SRR29438436) |
| HG002 / GM24385 | [SAMN41878946](https://www.ebi.ac.uk/ena/browser/view/SAMN41878946) | [SRR29438430](https://www.ebi.ac.uk/ena/browser/view/SRR29438430) | [SRR29438434](https://www.ebi.ac.uk/ena/browser/view/SRR29438434) |
| GM20129 | [SAMN41878945](https://www.ebi.ac.uk/ena/browser/view/SAMN41878945) | [SRR29438431](https://www.ebi.ac.uk/ena/browser/view/SRR29438431) | [SRR29438435](https://www.ebi.ac.uk/ena/browser/view/SRR29438435) |
| HG02630 | [SAMN41878947](https://www.ebi.ac.uk/ena/browser/view/SAMN41878947) | [SRR29438429](https://www.ebi.ac.uk/ena/browser/view/SRR29438429) | [SRR29438433](https://www.ebi.ac.uk/ena/browser/view/SRR29438433) |

ENA labels the RNA runs “Long-read transcriptome” and the genomic runs “Open Chromatin”; the paper describes the latter as Fiber-seq genomic reads and the RNA as MAS-Seq. The run metadata list about 1.6–4.3 GB per RNA file and 31–47 GB per genomic file. These verified ENA pointers are large raw inputs; I did not check whether smaller processed files are available elsewhere in the BioProject. No sequence files were downloaded. The paper's benchmark table uses hg38/GRCh38 terminology; I did not establish a separate case-specific build for UDN318336 from a public case record. The paper's data statement spells GM24385 as “GM23485”; ENA maps HG002 to GM24385. NCBI reports 18 SRA experiments for the BioProject, while the ENA read-run report returned eight rows (one RNA and one genomic run per listed line). I did not reconcile that archive-count difference, so the table reports only the eight ENA rows actually returned.

The accessible lines therefore provide a real paired-data control, but not a distinct consequential allele with a measured transcript effect. Selecting a gene from those lines and then scanning it for a favorable SV would turn this into an exploratory benchmark, which is outside the requested falsifier.

## Recent lead not promoted

The three Exa searches also surfaced a 2026 recurrent-astrocytoma preprint that reports matched tumor/blood HiFi DNA and Kinnex RNA. Its indexed record suggests that it already analyzes SV-linked RNA structure, allele-specific transcript usage and predicted ORF consequences. I did not treat that record as primary evidence: I did not verify a canonical primary-paper body, exact per-sample accessions, reference build, or public file listings within this bounded pass. It is a close-prior-art warning, not a recommended dataset or a claim that its data are unavailable. [Exa discovery record](https://exa.ai/library/publication/1b9wf2qvb69).

## Search and evidence audit

- Exa discovery used three distinct searches, each requesting 10 results and prioritizing 2025-01-01 through 2026-10-09. The first displayed output was clipped. I reissued the same three queries only to recover counts; those responses returned 10/10 each. This was six API calls across three distinct searches: 60 requested result slots under the Exa `sources_reviewed` accounting. Title-level overlap was visible. The search was not exhaustive, and I did not inspect every returned paper.
- Life Sciences Literature's PMC script resolved the exact Nature Genetics DOI to PMCID PMC12077378. A broader title-string lookup returned 10 of 32 fuzzy matches and did not identify the paper; I did not use those matches as evidence.
- Firecrawl retrieved the complete PMC article markdown (149,079 characters). I inspected the abstract, case/results passages, methods/build references, and data-availability statement; I did not review every figure or supplement. The NCBI BioProject page and ENA run metadata were read as listings only.
- The Exa indexed copy of the astrocytoma preprint returned 132,111 characters, but this was not treated as a primary-body read. Scite full-text access was reported by the main task as denied with `INVALID_ARGUMENT`; no purchase, billing change, or retry was made. Firecrawl and NCBI provided the usable alternatives for the source checked here.
- No new experiment, data request, raw-data download, job, Git operation, or change to another file occurred. The requested GPT-6 Luna/max configuration is recorded as a request; backend execution is not attested.

**Handoff:** keep the generic transcript-consequence direction open, but do not nominate UDN318336 as new work or treat the four benchmark lines as a substitute. This pass found no verified public case that supports a novel, direct one-locus falsifier. It does not reinstate the closed HG008 proposal or its limits.
