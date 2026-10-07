# Competing research opportunities

Date: 7 October 2026. This is a bounded literature sidecar. It does not select a method, approve an experiment campaign, or claim novelty from search absence.

The last-12-month window is **7 October 2025 through 7 October 2026**, inclusive. I calculated the start as the current date minus 12 calendar months.

| Topic | Closest primary prior art in the window | Useful unanswered question, if it survives review | One cheap falsifier | Independent label/data feasibility | Strongest reason to reject |
|---|---|---|---|---|---|
| **A. Multiallelic CNV and tandem-duplication genotyping in paralogous regions** | **ctyper** (17 Oct 2025) already assigns allele-specific copy numbers from NGS reads and pangenome haplotypes. It reports tests on 3,351 CNV genes and 273 challenging medically relevant genes, with at least 99.1% copy-number correctness in the CNV-gene set. Its paper also notes that similar paralogs can be merged in graph representations. [Primary paper](https://www.nature.com/articles/s41588-025-02346-4). **ContextSV** combines long-read alignments with coverage-derived copy number and SNV allele fractions for large CNVs, then assigns a learned confidence score; it reports experimental validation of selected large SVs. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13554283/). | At high-identity tandemly duplicated loci, **when do the reads contain enough paralog-specific evidence to identify each copy state?** Can a sample- and locus-specific identifiability measure tell apart supported genotypes from states that remain ambiguous on an unseen haplotype or assay, and support abstention in the latter case? This is a narrower question than building another CNV caller. The ctyper paper makes it plausible; it does not establish that a transferable identifiability test is missing or useful. | Select a small set of assembly-resolved multiallelic loci. Hold one carrier haplotype out of the reference panel. At two existing read depths, check whether a simple count/rank measure of paralog-specific read evidence separates correct genotypes from errors. **Stop** if it does not flag ambiguous states or predict held-out-haplotype errors, even at high depth. No new caller or large training run is needed for this screen. | Partly feasible. Haplotype-resolved HPRC/long-read assemblies, long-read samples, and family consistency can provide independent labels at selected loci. The 2026 Nanopore repeat study used more than 100 genomes and compared assemblies, Mendelian consistency, and molecularly confirmed expansions, showing that several evidence types exist. [Primary study](https://link.springer.com/article/10.1186/s13059-026-04210-y). However, labels for multiallelic, high-identity paralogs are likely sparse. Keep each test donor out of the pangenome panel and prefer a different assay for truth. | **Direct overlap is strong.** ctyper already addresses allele-specific CNV genotyping across paralogs; ContextSV adds long-read evidence and confidence scores. A new score or benchmark around those tools may be incremental. Independent labels at the hardest loci may also be too sparse for a transfer claim. |
| **B. Selective prediction under incomplete truth and assay/read-depth transfer** | **ContextSV/ContextScore** already assigns SV confidence from genomic context and combines alignment, coverage, and SNV-allele-frequency evidence. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13554283/). **Dual-SVF** (July 2026) uses sequence, alignment, and context features for long-read SV filtering, with confidence-gated fusion and tests across platforms and species. The inspected paper text reports filtering performance, but no selective-risk bound. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13502093/). The 2026 Nanopore repeat study found accuracy changes with pore chemistry and allele length; assembly concordance and Mendelian consistency did not predict sensitivity to confirmed pathogenic expansions. This is adjacent evidence that one proxy score may not measure every error mode. [Primary study](https://link.springer.com/article/10.1186/s13059-026-04210-y). | For SV genotypes, **can a system bound the error among calls it keeps at a useful call rate after assay or depth transfer, when benchmark labels are missing more often in difficult regions?** The claim must say which labeled population and missingness assumptions it covers. It must not treat unlabeled variants as negatives. This is about a usable risk guarantee, not another caller ranking or aggregate sensitivity comparison. No direct study of this exact question was confirmed in this bounded search; that is not evidence of novelty. | On a small public cross-depth set with existing native call scores, freeze a threshold on one high-depth assay. Hide labels in a context-dependent way that resembles truth gaps, then measure error among retained calls on a held-out depth or assay. **Stop** if the claimed upper risk bound is exceeded inside the labeled support. A pass would not validate regions with no independent labels. | Narrow testing is feasible with public GIAB/HPRC samples, multiple read depths or assays, and selected orthogonally validated SVs. ContextSV reports experimental validation of selected calls; the repeat study uses assemblies, pedigrees, and confirmed expansions. These sources can support a small falsifier. They do not supply labels for every difficult or unreported call, so broad guarantees need new orthogonal adjudication. | **The guarantee may be unidentifiable.** Truth gaps are not random, and the assay shift can occur in the same hard regions where truth is absent. Without explicit missingness assumptions or representative independent labels, a valid bound may cover only the already-callable subset or force the system to abstain on nearly everything. |

## Triage against the third candidate

The main task's update describes a third, mosaic-identifiability candidate: minority-allele identifiability against a near-identical common background. This comparison uses only that summary; I did not open or edit its research note.

| Candidate | Target | Disconfirming prior art or key risk | Current sidecar read |
|---|---|---|---|
| **A. Paralogous multiallelic CNV** | Germline copy-state identifiability across duplicated loci. | ctyper already infers allele-specific copy number from pangenome and read evidence; ContextSV adds long-read CN evidence and confidence scoring. | Clear use case, but weakest novelty case unless a specific unseen-haplotype identifiability gap remains after direct comparison with ctyper. |
| **B. Selective risk under missing truth and assay shift** | Error bound among retained calls, with abstention when labels or assay support are weak. | ContextScore and Dual-SVF already score/filter calls. The main risk is that nonrandom missing truth makes a useful guarantee impossible. | Most distinct estimand in this sidecar, but feasibility depends on representative independent labels and a non-vacuous bound. |
| **C. Mosaic minority-allele identifiability** | Detect a minority allele against a near-identical common background. | Per the main-task summary, MIMS already uses beta-binomial coverage; generic coverage curves, easy hard-matching benchmarks, and personal-assembly filtering are not novelty by themselves. Independent labels and the remaining novelty are unproven. | Potentially more focused than A, but this sidecar did not independently audit its prior art or labels. Keep conditional until those checks resolve. |

Relative triage only: **A is currently easiest to disconfirm** because of ctyper. **C may be the strongest focused biological question** if the label source and a gap beyond MIMS survive independent review. **B remains a distinct fallback question** only if a useful risk bound is identifiable under realistic label gaps. This is not approval to run any falsifier or campaign.

## Main integration and evidence limits

Main read this full handoff and fetched the four linked primary pages to
check the load-bearing claims. The ctyper report supports the allele-specific
copy-number method, its reported gene-set accuracy and k-mer representation.
Its parent page states an Author Correction on February 16, 2026; the correction
itself was not read here. Reported performance is not independent replication.
The tandem-repeat paper's publisher marks it an early, unedited version with
possible errors. Its concordance-versus-expansion-sensitivity finding supports
the limited proxy-metric caution, not a general error bound for CNVs.

The fetched ContextSV and Dual-SVF PMC excerpts contain abstracts/reference
lists, not a complete methods audit. They support the stated integrated
evidence/confidence and multimodal-filtering claims. **No claim that these
papers lack selective-risk guarantees is established by an excerpt.** Full
methods/code comparison remains required; absence of a search hit is not
novelty evidence. Main's fetch added no new primary source beyond the four
already identified, and did not download genomic inputs.

The Sol6.1/max-requested decision agent is comparing A/B/C before selection
of a finite next falsifier. No new method, data acquisition, risk guarantee or
experiment campaign is accepted by the relative ranking above. The independent
Sol6.1/high reviewer remains available for concrete protocol/result scrutiny.

## Search and source audit

| Check | Record |
|---|---|
| Date window | 7 Oct 2025–7 Oct 2026, inclusive; start date is current date minus 12 calendar months. |
| Exa search | 3 searches × 5 requested result slots = **15 requested slots**. **Four primary pages fetched and read** (6,500-character extraction cap each); slots are discovery results, not full-text readings. |
| PubMed Entrez | Two focused searches returned 4 and 10 IDs. Metadata summaries for all **14** were reviewed; these are not counted as full-text readings. No raw JSON/XML was saved. Requests succeeded with a non-fatal Python/urllib3 LibreSSL warning. |
| Primary pages read | ctyper; ContextSV; Nanopore tandem-repeat genotyping assessment; Dual-SVF. These are original studies. Claims are from their reported methods and cohorts, not independent replication. |
| Date discrepancy | PubMed lists ContextSV electronic publication on 9 Sep 2026; its PMC page shows 27 Jun 2026. Both are in-window. The retrieved PMC page dates Dual-SVF to 1 Jul 2026. |
| Retrieval failures / alternatives | No external retrieval failed. The repo path needed the nested `repo/` directory; after correction, both requested project notes were read. Exa and Entrez worked, so no Firecrawl fallback or CLI was used. No paid terms were accepted. |
| Configuration requested, not attested | Project record requests a GPT-6 Luna/max literature worker. This run has no independent backend/model-effort attestation; the request is recorded, not represented as verified execution. |
| Project boundary | Main reports the fixed released-callset screen closed by the independent reviewer and main after `SVLEN contradicts canonical signed allele length`. No diagnosis or processing follows; there is no score or validated denominator. This sidecar did not repair, retry, score, or inspect genomic data. Main reports **737 passed, 35 skipped** for the current full suite; this sidecar did not run or verify it. No tests, Git operations, cluster work, or other project-file edits were made. |
