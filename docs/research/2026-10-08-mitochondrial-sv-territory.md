# Mitochondrial SV territory — 2026-10-08

## Decision

Main's subsequent disposition **closes this origin-inference framing**, not
merely its availability gate. Distinct cell-lineage labels do not label
distinct deletion origins: linked variants can arise after one ancestral
deletion. The diagram/hypothesis below is retained as the worker proposal,
not accepted inference. Do not pursue its suggested MitoTracer inventory.
[Exact counterexample and claim limits](2026-10-08-three-direction-disposition.md).

Reject this as an active research lead for now. A specific test is possible in principle, but no public processed artifact was verified to join deletion molecules to independent cell-lineage labels. This is an evidence gap, not a biological null and not proof that such data do not exist.

No raw data were downloaded. No bioinformatics pipeline or computational analysis was run. This note is the only file change. DeepSV remains excluded; SSL remains suspended. The stopped ecDNA, error-twin, copy-state, annotation/acquisition, and released-callset work stays stopped.

## Candidate hypothesis considered

In one donor, the same large-deletion junction on different private, linked mtDNA variants may mark independent deletion origins. The same junction and rare linked variants in independently barcoded related cells may mark expansion of one deletion-bearing lineage. Linked variants should predict lineage better than the deletion junction alone.

```text
deletion junction + linked variants ──> predict independent barcode labels
                                      ├─ one lineage: expansion
                                      └─ separate lineages: repeated origin
```

This distinction matters: a hotspot can reflect repeated mutation, expansion of one clone, or both. The test must use lineage labels that do not come from the mtDNA calls.

## Closest controls

| Control | Evidence and limit |
|---|---|
| **Kowald & Kirkwood (2026)**, [accumulation-time model](https://www.nature.com/articles/s41514-026-00431-4) | Direct control for mutation versus expansion. It fits mutation probability and selective advantage from cross-sectional single-cell RNA data. Validation uses synthetic ground truth. The fraction of advantageous mutants is partly unidentifiable near its upper bound. The authors name deletion-breakpoint information as a possible future constraint. A general “add breakpoints to separate mutation from expansion” claim is not new. |
| **NanoDel (2026)**, [journal paper](https://academic.oup.com/bioinformatics/article/42/10/btag684/8800054) and [2025 preprint methods](https://www.biorxiv.org/content/10.1101/2025.09.19.677263v1) | Closest long-read deletion control. It combines one-amplicon long-range PCR, ONT reads, and splice-aware alignment. It tests artificial data and samples with prior clinical deletion diagnoses; it reports recurrent sequence-motif regions. It does not provide independent cell-lineage labels. The current journal page exposed its abstract; method details below come from the earlier preprint version. |
| **MitoDelta (2025)**, [paper](https://link.springer.com/article/10.1186/s12864-025-11931-0) | Calls deletions from single-cell RNA data, but pools reads by cell type. It tests simulated data, engineered cell lines, and Parkinson disease data. It masks NUMT regions in comparisons. It does not test cell lineage or deletion origin. |
| **Himito (2026)**, [paper](https://www.nature.com/articles/s41467-026-77418-y) | Close NUMT and haplotype control: long-read graph analysis filters NUMT reads and assembles mtDNA haplotypes. Its abstract does not establish deletion-origin labels. |
| **MitoTracer (2025)**, [paper](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1013090) | Close independent-label control. The paper reports public figure data and experimental lineage labels for 65 populations from 15 clones. The search record does not establish that these tables contain large-deletion junctions or variants linked to deletion-bearing molecules. |

Older close control: [“Clonal expansion dictates the efficacy of mitochondrial lineage tracing”](https://link.springer.com/article/10.1186/s13059-025-03540-7), published 2025-03-26, just before the 18-month window. Its abstract warns that many cell-subpopulation mtDNA variants may be pre-existing heteroplasmies; lineage use depends on strong clonal expansion. It is not a deletion-specific test.

The known [2025 MitoSAlt/Mitopore comparison](https://www.mdpi.com/2673-6284/14/1/9) is also outside the window. It remains a caller control, not evidence for a new origin-versus-expansion method.

## Outcome-label feasibility

**Status: unknown for the joint deletion-plus-lineage outcome.** MitoTracer shows that independent experimental lineage labels and public processed tables exist for mtDNA lineage work. NanoDel has prior clinical labels for deletion presence; MitoDelta has engineered deletion controls; the 2026 accumulation model uses synthetic labels. None of the inspected records confirms one small artifact with all of these together: per-cell deletion junction, variants linked to the deletion molecule, independent lineage barcode or clone label, and orthogonal deletion confirmation.

Long reads can link sequence features. A read from an amplicon is not automatically an independent original mtDNA molecule. Any future test must document NUMT exclusion and PCR/duplicate control. Do not infer clone origin from read counts or from mtDNA markers alone.

## Finite falsifier if a compatible artifact is found

Use only an existing small processed table. First require all four fields above, plus donor and cell/clone IDs. If the fields are missing, stop this direction; do not substitute simulated truth or labels derived from the same mtDNA calls.

On held-out, independently labeled clones, compare a fixed baseline (junction, donor, tissue, coverage) with the same model plus linked private variants. Include mtDNA-SNV-only and shuffled-linkage controls. Use held-out log-loss as the sole primary metric. Define gain as baseline log-loss minus augmented-model log-loss. Reject if the 95% bootstrap lower bound for gain is at or below zero. Fix the split and model before viewing outcomes.

This is a proposed kill test only. It was not run, and no campaign is approved.

## Search and read record

- Recent window: 2025-04-08 through 2026-10-08. Older close controls are marked above.
- Three targeted Exa searches requested 10 results each: 30 result slots. They returned 30 entries with repeats. Three primary works received methods/validation reads: NanoDel, MitoDelta, and the Kowald–Kirkwood model. MitoTracer, Himito, and the 2025 lineage paper were screened from search abstracts only.
- Retrieval limits: Firecrawl paper reads gave `INVALID_ARGUMENT` for NanoDel and no passages for MitoDelta or the model. Scite full-text calls gave `INVALID_ARGUMENT` for all three. Firecrawl page extraction supplied relevant methods for MitoDelta and the model, but not NanoDel. The OUP page exposed NanoDel's abstract; its XML fetch timed out. Exa's fetch of the NanoDel bioRxiv v1 page supplied the methods fallback. Current journal-version methods were not independently retrieved.
- Requested worker configuration: **GPT-6 Luna / maximum effort**, as requested by the user. This records the requested configuration only; it is not backend attestation. No worker or new chat was started.
- No raw genomic data, software, cluster jobs, Git operations, credentials, or external writes were used.

## Recommendation

Do not select this direction yet. First verify whether the public MitoTracer processed artifact contains deletion junctions and linked variants. Even if it does, the main risk is that mtDNA variants mark pre-existing heteroplasmy rather than a newly arisen cell clone. The broad method overlaps with published deletion callers, NUMT controls, and mutation-selection models. A specific linked-variant result with independent lineage labels could be useful; no such result is established here.
