# synVII: independent next-investment review — 2026-11-03

**Decision: finish one cheap offline metadata crosswalk. Do not start a read download, phenotype reanalysis, model campaign, or cluster job on this evidence.** No failed experiment is required before that diagnostic. The crosswalk can establish whether a useful contrast exists; it cannot establish research value by itself.

I read the [objective](/Users/akm/.codex/attachments/2fa04b13-b328-4023-872e-0c4cc9dbfaee/goal-objective.md), the complete [source census](2026-10-16-synvii-source-census.md), and the complete [matched-dosage triage](2026-10-16-matched-dosage-architecture-triage.md). This is an independent logic review of those records. I did not verify their external literature claims, inspect an actual CNP0002230 packet, or conduct a new literature search. Backend/model/effort configuration was requested, not independently attested.

## Scientific value needs a stronger target

The supplied triage already records prior evidence that chromosome architecture affects fitness at unchanged content. Repeating that result in a synVII disome is a system-specific extension, not yet a strong publication premise. Exact dosage matching improves interpretation; it does not create novelty. “A residual remains after adjustment” also lacks a biological explanation.

A useful next question must name a specific structural mechanism or a predictive rule, explain what the cited work leaves unresolved, and state a result that would discriminate between explanations. For example, a defined new adjacency could motivate a small validation if the actual strains and measurements support it. That is a possible target, not evidence that this collection contains one. Do not require a proven mechanism before the cheap audit; require a plausible, testable contribution before substantial investment.

## Correct the contrast definition

| Feature | What the audit must distinguish |
|---|---|
| **Cut-site positions** | Original segment boundaries used in rearrangement. Two structures can use the same cut sites but reconnect their ends differently. Matching positions can reduce one source of difference while retaining a contrast. |
| **Reconnected adjacencies** | Which oriented segment ends are joined. These encode the structure under study. Holding all resolved adjacencies, multiplicities, and topology fixed generally fixes the paths, apart from equivalent representations or unresolved copy assignment. Conditioning on them can remove the exposure itself. |
| **Dosage** | Match absolute copy number at every resolved interval, with ploidy and genome-wide copy-number changes accounted for. Equal retained length or total synVII dosage is insufficient. Unknown copy number is not a match. |
| **Path identity** | Compare canonical structures: a different drawing start or direction for the same circular molecule is not a new architecture. State any unresolved phasing across repeated copies or molecules. |

Replace the triage's ambiguous “same breakpoint set” with an explicit distinction between cut sites and new junctions. Treat adjacency, position, orientation, and topology as parts of the proposed structural effect when they differ. Do not demand an order effect independent of every feature that constitutes order. Choose the estimand first; do not regress away its mechanism. No model can separate features that always occur together in the available clones.

## What the present evidence permits

The census reports a strain inventory, not a full quantitative phenotype table. Aliases, accession membership, and chromosome cartoons do not supply clone-level fitness values, measurement uncertainty, or independent biological replication. A metadata join is necessary source work, not a research result. The paper's 219 selected derivatives and the workbook's named strains also need separate denominators; do not assume a complete one-to-one cohort join.

Selection for growth restricts the observed fitness range. If structure and other clone properties both affect recovery, selection can also induce an association between them. A within-selected-cohort difference is descriptive evidence for the recovered strains; it does not identify an architecture effect in all induced derivatives. A new endpoint does not undo the original selection. A complete screen denominator helps describe ascertainment but does not alone remove this bias.

One clone per path cannot separate path from other clone differences. Technical repeats estimate measurement precision, not independent architecture replication. Independent origins help; controlled reconstruction is stronger for causal attribution. Do not call a small or nonsignificant difference evidence of no effect unless its uncertainty excludes a predeclared meaningful effect. Assay repeatability informs feasibility; biological relevance must also inform that threshold.

## Decision conditional on the actual packet

| Actual crosswalk result | Next investment |
|---|---|
| Available resolved structures contain no exact-dosage, distinct-structure candidate | Stop this dataset branch. Do not acquire reads merely to preserve the direction. A separately justified reconstruction opportunity would be a new decision. |
| Structure or dosage fields are missing or unresolved | Eligibility is unknown, not disproved. Permit another cheap source check only if it targets a named record that could settle eligibility; otherwise park this retrospective branch. |
| Candidate structures, but no usable quantitative same-assay phenotype records | Record feasibility only. Stop retrospective fitness inference. Consider a small new assay only with accessible strains and a specific contribution worth testing. |
| Usable phenotypes, but one clone per path or inseparable structural/background differences | Report a descriptive candidate. No causal or general architecture claim. A bounded validation can be justified by the candidate's scientific value. |
| Resolved contrast, usable measurements, and adequate biological support | Run a small diagnostic with fixed eligibility, endpoint, meaningful-effect threshold, and uncertainty analysis. Advance only if the result supports a specific contribution beyond “architecture matters.” |

The diagnostic may be informative even if negative. An imprecise estimate is inconclusive, not a validated null. Metadata completeness, a successful join, and a nominal positive difference are each insufficient reasons to expand the project.

**Packet status:** pending. This review approves completion of the bounded metadata diagnostic only; it is not a sign-off on cohort eligibility, novelty, or an experiment campaign. Append an actual packet check when supplied, including what was inspected and which decision row applies.
