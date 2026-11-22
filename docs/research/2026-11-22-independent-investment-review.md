# Independent scientific investment review — 22 November 2026

## Decision

**Allow one bounded content-feasibility check after the main agent's schema check, under a separate prospective scope. Do not treat it as an experiment, an accuracy result, or permission for a larger campaign.** Its best immediate value is to show whether a specific comparison is identifiable or to stop an unevaluable data path cheaply. Its chance of producing novel science by itself is low.

The strongest remaining CloneSeq question is conditional: **at a stated assay budget and a specified decision time, does adding SV junctions improve clone inference beyond a strong multi-marker SNV analysis?** This is not established by a join, by SV–SNV agreement, or by the mere existence of cfDNA WGS. The [Williams et al. study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12629990/) already reports clone tracking, SV/SNV frequency comparisons and a WGS validation. A useful new result would need an incremental, decision-relevant comparison that the paper did not already answer, credible uncertainty, and evidence beyond this selected cohort. The present public-data route may be too small or lack the necessary units; that remains unknown.

```text
Main agent's separate first-row schema check
                      │
                      ▼
      Freeze a separate content-check protocol
                      │
       ┌──────────────┴─────────────────────┐
       ▼                                    ▼
Exact joins, units, budget and         Missing, ambiguous, inaccessible,
reference can support an endpoint     or only a repeated published result
       │                                    │
       ▼                                    ▼
Design a limited exploratory          Record the precise limitation;
comparison and assess precision        consider the paired-DNA/RNA fallback
       │
       ▼
Independent scrutiny before scale or major claims
```

This is a recommendation, not a report of a new check. The [schema protocol](2026-11-06-cloneseq-schema-protocol.md) permits only first-row inspection under its stated rules. It explicitly says that a data-row check needs a separate prospective scope. I did not inspect the workbook, its first row, any patient data, or the other agent's running work.

## Paper denominators and observation units

The numbers below are **published counts**, not counts independently reproduced from the supplementary tables. They answer different questions and must not be added. The cited paper is [Williams et al., Nature 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12629990/).

| Published set | Unit and correct interpretation | What it does not establish |
|---|---|---|
| 24 | Patients in the tissue/scWGS cohort, with baseline plasma collection reported. A defensible frame for auditing the full published cohort. | Twenty-four patients with paired, evaluable SV/SNV clone estimates, an independent reference, or recurrence labels. |
| 22 of 24 | Patients in whom the authors inferred high-confidence clone-specific SVs in scWGS. | Twenty-two evaluable patients for every clone, time point or comparison. The two others must not vanish from full-cohort availability reporting. |
| 21 | Preoperative **plasma samples** with sufficient SNVs for the authors' tumor-DNA detection comparison. | Twenty-one independent reference patients or twenty-one valid clone-accuracy comparisons. |
| 18 | Patients with radiographically confirmed recurrence and postbaseline and postrecurrence plasma samples, selected for longitudinal analysis. | An unselected surveillance cohort with both recurrence and non-recurrence outcomes. |
| 12 from 6 | WGS **plasma samples**, baseline and recurrence for six patients. The paper reports 11/12 agreement of the WGS-correlated dominant clone with the CloneSeq-SV dominant clone. | Twelve independent patients, a relapse-seeding truth set, or a proven gain over an optimized SNV arm. For this exact WGS subset the patient-level upper bound is six, before exclusions. |
| 3 with later tissue | Three patients had a second scWGS tissue time point; the paper describes postrecurrence tissue for two and interval debulking for the third. | Three independent postrecurrence-tissue seeding labels. |

Time points, clones, markers, reads, duplex molecules and patients are different units. A patient can have many samples and multiple clone contrasts; a marker can be shared by clones, amplified, lost, not targeted, or fail measurement. A patient-level claim requires patient-level uncertainty and must account for repeated samples. The source notes correctly distinguish the 24, 18 and six; the [investment decision](2026-11-06-scientific-investment-decision.md) also correctly says that a single joined case is only case feasibility.

For scale only: if six independent, exchangeable patients were each scored once on a prespecified binary error endpoint, observing zero errors would still give an exact one-sided 95% upper error bound of about 39%. This is a hypothetical calculation, **not a result** from these data. The selected WGS subset need not be representative, so even that calculation would not settle generalization.

## Clone labels, recurrence labels, and references

The paper's tissue-derived clone definitions and baseline mutation assignments are useful shared inputs. They are not error-free ground truth. The authors infer a copy-number tree, define clades, assign markers using sparse single-cell support and copy number, and sometimes merge sister clones when marker resolution is inadequate. A clone name alone does not show that an SV or SNV is private to that clone, that it is measurable in plasma, or that two competing clones are distinguishable. Amplified markers can increase sensitivity while also changing how VAF relates to cell fraction. Track the exact clone/marker mapping and its uncertainty. [Williams methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC12629990/).

Keep these endpoints separate:

| Object | What it can support | Key limitation |
|---|---|---|
| Clinical recurrence date | Timing of a radiographically defined progression event. | A date or recurrence annotation is not a molecular identity for the seeding lineage. |
| Targeted SV or SNV frequency | An assay-derived measurement of markers assigned to a tissue clone. | It is not independent truth for the accuracy of the same assay. A comparison of two frequencies can show agreement, not which is correct. |
| cfDNA-WGS clone similarity | A separate molecular signal for a limited dominant-clone comparison, if sample linkage and distinguishability are established. | It uses the same biological specimen and library preparation and shares tissue clone/copy-number definitions. It is not fully independent of the clone model or necessarily able to distinguish similar profiles. |
| Recurrence tissue and phylogeny | Potential evidence for the relation between sampled recurrent disease and a baseline lineage. | Spatial sampling, new or multiple lineages, evolution and missing tissue can leave the actual seeding lineage uncertain. |

**The WGS distinction matters.** The authors identify the best-matching clone by correlating cfDNA-WGS read-depth and allele-frequency profiles with tissue clone profiles. This is an orthogonal measurement conditional on the shared clone definitions. Separately, their plotted WGS copy-number predictions use the CloneSeq-SV clone fractions; those predictions cannot be recycled as independent ground truth for those fractions. The reported 11/12 agreement is useful internal validation, not direct evidence that adding SVs beats SNVs or that a relapse seeder was correctly identified. The paper also reports that clone B in patient 139 had no identified SV and was followed using SNVs. A published trajectory or a field named “SV frequency” must not be assumed to be SV-only without tracing provenance.

The [paired review](2026-11-06-paired-scientific-review.md) and the investment decision correctly require a separate reference for **accuracy** and richer recurrence tissue for a **relapse-seeding** claim. Those are claim-specific requirements. They are not prerequisites for a descriptive audit of marker assignment, assay background, missingness or measurement units. A future molecular endpoint can be useful without asserting a clinical outcome.

## Fair comparison and leakage

The paper's SV clone estimates use raw uncorrected reads; its SNV estimates use duplex consensus reads. Both choices can be scientifically reasonable. A raw read, a read family, a duplex consensus and an input DNA molecule are not interchangeable. Coverage, target count, plasma input, assay design, library construction, sequencing and computational cost are different budget axes. Preserve the native error correction in each arm and identify precisely which cost is fixed. An SV-only arm can be a secondary analysis; the primary added-information contrast is **SNV-only versus SNV plus SV**, with a strong multi-marker SNV baseline. [Williams methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC12629990/).

A feature ablation on an already purchased joint capture panel can estimate a conditional information difference **given that joint assay**, if the measurements and an appropriate reference are available. It does not by itself estimate what a separately designed SNV-only assay would achieve for the same money or input. A true assay-allocation claim needs a defensible counterfactual: common plasma material and time point, assay design and target selection, unique-molecule or family information where needed, total sequencing and relevant laboratory costs, and an optimized SNV comparator under the same specified resource constraint. Do not assume normalized clone frequencies, average coverage, or equal numbers of targets can be downsampled into that counterfactual. If only a narrower budget is observable, name it and limit the claim.

The [ECLIPSE/TRACERx study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7614605/) already tracks many mutation markers and estimates subclonal composition. It is an important comparator for a compatible NSCLC claim; it is not automatically runnable on the ovarian workbook or equivalent to the paper's SNV analysis. Conversely, a single-gene baseline such as TP53 would be too weak to establish added clone information against modern multi-marker methods.

Selection needs explicit handling:

- The paper excludes clone-frequency estimates below a tumor-fraction threshold of `10^-4` based on truncal SVs. Applying that rule to both arms can select on one arm's information and hide cases where SNVs work differently. The paper's displayed SV/SNV scatter has its own stricter selection: purity above 0.5% and at least five SVs and SNVs per clone. These are paper-specific descriptive subsets, not a general target population. Report them as such; do not carry them into an incremental comparison without an estimand and bias analysis.
- Freeze the target population, decision time, clone definitions, calibration, marker-selection rule, abstention and eligibility criteria before inspecting comparative outcomes. Use information available at the intended decision time. Keep failed assays, clones with no informative marker, low-shedding samples and unmeasured targets visible; distinguish absent, zero, uncallable and unknown. Do not select only concordant clones, high-purity samples, or patients with positive outcomes.
- Published trajectories use calibration, normalization, smoothing and, in some gaps, an assumption of zero tumor DNA. Do not use future-aware interpolation, postrecurrence samples or outcomes to construct an earlier prediction or select its features. A later reference can evaluate that prediction if it is obtained independently of the prediction under a prespecified evaluation design. A retrospective recurrence-conditioned analysis is possible if labeled as such; it cannot by itself estimate surveillance specificity across all patients.
- All this public cohort and the paper's figures are already development evidence. Masking outcomes during a new feasibility check reduces new choices based on results, but does not make the published patients unseen. Patient-disjoint splits reduce within-project fitting leakage; they do not undo author-level selection or supply external replication. A clinical claim needs appropriate follow-up, censoring and non-recurrence controls as well as an independent molecular reference for any clone-accuracy endpoint.

## What the next cheap content check should do

After the current schema result is available, write a separate protocol that names the source versions, fields, masks, units, intended endpoint, output and resource limit **before any patient-row inspection**. This review does not authorize itself to read those rows, and the schema result does not establish any of the following facts. A sensible target is availability for the narrow, conditional joint-assay comparison described above, not an attempt to prove superiority.

1. **Freeze the frame and missingness rules.** Attempt to reconcile the 24 published patients from public IDs, and retain the original frame and all unresolved IDs. Do not silently relabel the 18, 22, 21 or six as the full cohort. If the public roster cannot be reconciled, record that failure and the actual recoverable frame; it blocks a claim about complete 24-patient coverage, not every narrower descriptive question. Keep outcomes masked during structural checks where possible, and label all eventual analysis as exploratory reuse.
2. **Build a linked availability manifest at the correct grains.** Use separate linked records for patient; specimen and collection time; clone and competing clone; marker and clone assignment; assay/library and target; and independent reference/control. Record exact source, key, definition, status and exclusions. For every potential patient/time/clone contrast, check whether both assay arms, their denominators and the same linked reference exist. A 24-by-8 patient summary can be an index, but it must link to the finer records: one “present” cell cannot prove that all eight items refer to the same specimen or clone. Summarize distinct patients, paired specimens, contrasts and controls separately.
3. **Validate meaning without scoring performance.** Check whether count fields actually represent alternate and reference/total counts, raw reads, simplex, duplex or unique molecules; whether zeros differ from absent or failed targets; whether marker assignment, baseline-only calibration, copy number, and collection order are documented; and whether off-target controls have exposure denominators and separable fitting/evaluation roles. Check time-specific unprocessed measurements versus derived or interpolated values. Do not calculate clone accuracy, compare arms, tune thresholds, rank patients, or infer biological absence.
4. **Trace reference and resource provenance.** For WGS, verify patient/time linkage, the actual read-depth/allele-frequency evidence, use of shared clone definitions, distinguishing contrasts, and whether an SV-derived prediction enters the purported reference. For a recurrence claim, separately identify actual recurrence tissue and its independent phylogeny and sampling limits. Determine which input, molecule, sequencing and assay-cost measures can be matched, and what reuse permissions apply. Do not presume workbook summaries contain WGS profiles, complete SNV inputs, or cost accounting.
5. **Report the feasible estimand and its limits.** Give the complete eligibility flow and counts at each unit; identify all unavailable, ambiguous and controlled-only information; show the maximum number of independent patients for the specific reference actually found. Present **supported**, **unsupported**, and **unresolved** separately. A positively documented absence differs from a missing row or unresolved label. Do not present any hypothetical count as an observation.

For an accuracy comparison, success means that at least one explicitly specified, paired patient/specimen/clone contrast has usable measurements, a reference independent of the tested predictions conditional on shared baseline information, and a budget claim that the available fields actually support. One case proves only that such a join can exist. Before any comparative outcome analysis, the next design must assess eligible patient count, cluster-level precision, a useful effect size and error target, selection, and the additional evidence needed. No fixed minimum patient count in this memo is a power calculation.

If the reference or cost information is absent, a narrower descriptive measurement or background audit may still be identifiable. If the only possible endpoint is the already-published result, or if an essential field cannot be joined or interpreted, park **this public-data comparison** with the missing item and a realistic route/cost to resolve it. If the time limit expires with ambiguity, call it inconclusive; a small targeted resolution may be worth considering if it changes the decision. None of these outcomes proves that SVs lack biological or clinical value.

## Gates that are operational, not scientific laws

| Proposed gate | Review and safe interpretation |
|---|---|
| 24 patients and 192 status cells | The investment note does **not** require all 24 to be complete. Its full roster is a useful audit frame, but obtaining every ID and filling a fixed patient-level matrix is not a universal prerequisite for a narrow question. Exact specimen/clone joins and honest denominators matter more than the grid shape. |
| Four analyst hours, two CPU-hours, 4 GiB RAM and 100 MiB | Reasonable proposed spending limits, not evidence of biological or scientific feasibility. If exhausted, report an investment stop or a named unresolved question. Do not claim the data lack value. |
| One fully linked case | Sufficient for a concrete existence/engineering check only. It cannot support a population effect, a reliable error rate, or publication readiness. Conversely, more complete cases alone cannot rescue circular truth or an unmatchable budget. |
| A seeding-lineage label | Necessary for a claim about seeding accuracy, with uncertainty and sampling limits; not mandatory for an assay-background audit or a narrower plasma clone-measurement comparison. The clinical recurrence date alone is not that label. |
| Paired review's `chr1:1,000,001–2,000,000`, first ten insertions, 100-bp exon window, two alleles in two genes, two carriers and two non-carriers, and 32-MiB cap | These are explicitly small search and spending rules in the [paired review](2026-11-06-paired-scientific-review.md), not demonstrated minimums for all useful SV/RNA science. A negative or empty fixed window rejects only that bounded route under those rules. Two carriers do not establish power, and exceeding the transfer cap does not establish absence. |
| Investment decision's chromosome-22 pilot and 56 names | A reproducible candidate frame, not a representative genome-wide search or 56 verified independent, callable DNA/RNA pairs. A negative chromosome-22 screen does not falsify all SV/transcript mechanisms. Do not select a new region after looking for favorable RNA outcomes. |

## Safe fallback and scientific return

If the CloneSeq route is unsupported or remains unresolved within a sensible resource limit, use the investment decision's **separately specified chromosome-22, 56-name DNA/RNA content pilot** as a fallback, not as an automatic claim of discovery. Before RNA outcome inspection, fix the stated sequence-resolved insertion/deletion and gene-body rule, source versions, coordinates, and all exclusions. Count callable carriers and non-carriers, genotype missingness, transcript/annotation links, and actual RNA observability at the relevant allele and donor level. Retain all candidates, including failures; do not choose by QTL significance. The nine Vienna VCF names overlap the 56 according to the reviewed source notes; they are not nine more independent donors or automatic truth for the other 47.

The more specific insertion-linked splice-junction idea in the paired review needs reads that can establish the inserted sequence and junction on an informative molecule, plus mapping, phase and non-carrier controls. A transcript count and BED coordinate alone cannot establish this. If reads, allele identity, or adequate carriers cannot be obtained, report non-evaluability rather than no biological effect. A generic SV–expression association has little novelty by itself: [Ebert et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC8026704/) already analyzed SV expression and splicing QTLs in 427 donors, and the [Lu et al. preprint](https://pmc.ncbi.nlm.nih.gov/articles/PMC13345107/) studies pangenome-based expression mapping with 430 samples and includes a 201-sample long-read RNA cohort. Linked small variants, donor identity, reference/mapping bias, relatedness and transcript-catalogue leakage remain material controls. A measurable, independently confirmed allele-linked mechanism beyond those baselines could be meaningful; the header overlap alone does not establish one.

## Scope, provenance and attestation

I read the two requested untracked notes, the tracked schema protocol as it stood before concurrent updates, the related supplement inventory, and selected project context. I checked the cited CloneSeq paper and selected primary comparator sources through public full-text/search excerpts. The publisher DOI route returned an access challenge; the PMC full text supplied the paper passages. The literature review was targeted, not exhaustive, and cannot prove novelty or the absence of closer work. The contents and permissions of the workbook and controlled data remain unverified by this review.

No workbook rows or workbook schema were inspected; no experiment, model fitting, cluster job, workbook check, commit or push was performed. This file is the only file written for this review. The requested **GPT-6.1 Terra/max** reviewer model and effort are configuration requests; the exact model and effort used here are **not independently attested**.
