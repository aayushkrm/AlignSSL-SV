# Functional ecDNA property: bounded direction decision
Date: 7 October 2026. Full goal, centromere outcome crosswalk and CE code audit read.
Requested: GPT-6.1 Sol/max. Runtime model/effort is not independently attested.
Existing-gate review is running; the new property has no reviewer approval.

Main checkpoint, October 8: this file was saved before the prior decision
agent ended with a usage-limit error. No completed handoff was received then.
The proposal below is preserved as an interrupted draft, not approval to launch.
The [completed independent formal review](2026-10-08-functional-formal-review.md)
and [hand calculation](2026-10-08-functional-ecdna-analytical-control.md) now
accept only the restricted mathematics and STOP the current method framing.

## Decision
Allow ONE <=60-minute paper-only formal/native-baseline falsifier.
Do not select a method lead, build a wrapper, or approve an experiment campaign.
The estimand differs from circle count and could matter for oncogene inheritance.
Its novelty and empirical benefit are unestablished; generic optimization is insufficient.
Main retains the original CE v1 S3/v2 S4 input gate; do not duplicate it.
Centromere outcome crosswalk meets STOP for that anchor: no linked segregation outcome.
GM03417 is mosaic, not a clean unbalanced-only comparator. Missing outcome is not a null.

## Affirmative native overlap
[CoRAL 2024](https://genome.cshlp.org/content/34/9/1344) already uses weighted cycles, ordered subwalk evidence and parsimony.
Its Discussion explicitly allows glued smaller circles and limits discordant-edge reuse.
Its formulation bounds multiplicity; these are model restrictions, not physical boundaries.
[AR 2020](https://www.nature.com/articles/s41467-020-18099-z) already combines breakpoint graphs with optical maps,
returns alternative explanations and tests equally abundant heterogeneous mixtures.
Its gap-length and copy constraints are strong native controls for the proposed inputs.
An optical-map contig can be a partial scaffold, not an observed whole circle.
The [AACR 2026 abstract](https://aacrjournals.org/cancerres/article/86/7_Supplement/66/776226/Abstract-66-Gene-co-amplification-and-structural)
reports CDK4/MDM2 on the same ecDNA molecule in 93% of their co-amplification cases.
This motivates a consequential property; abstract inspection does not establish
its complete methods, validation, error or incompatibility with this proposal.
Neither known ambiguity nor future-work prose establishes a new research gap.

## Exact model and truth query
Fix A and B marker definitions before analysis; intact gene copies are not arbitrary overlaps.
O = signed breakpoint graph G; edge-copy intervals [l_e,u_e]; original signed paths P;
and independent physical size/linkage observations S from the same modeled population.
Keep sequence and junction order, orientation and repeated traversal in P.
Mapping ambiguity, chimeric/error paths and copy-estimation error need declared bounded sets.
A read count is not a circle count or direct abundance constraint without a sampling model.
Declare purity and linear/integrated contributions as bounded nuisance variables.
A cyclic graph alone does not establish ecDNA or distinguish an integrated tandem array.
Assume graph completeness only for this formal test; unobserved sequence cannot be ignored
in a later biological claim without an independently justified bound on its contribution.
C ranges over physical closed walks, allowing repeated edges, modulo rotation/reversal.
w_C >= 0 denotes population-average abundance, not a per-cell assignment.
Let n_A(C) count A copies, and I_B(C) indicate at least one B marker on that circle.
T_A = sum_C w_C*n_A(C) + A copies assigned to noncircular amplified structures.
Require T_A > 0. Normal/background copy treatment and the target population must be fixed.
q_AB = sum_C w_C*n_A(C)*I_B(C) / T_A.
This is an A-copy-weighted fraction, not fraction of cells, circles, or expression.
Co-residence does not establish enhancer action, physical contact or therapeutic dependence.
F(O) contains ALL jointly compatible mixtures and nuisance settings, not just native outputs.
The target is [inf_F q_AB, sup_F q_AB]; empty F means inconsistent model/data, not certainty.
Observed paths need molecule-compatible assignments; presence alone permits tiny abundance.
No quantitative lower fraction follows from one bridge without sampling/abundance constraints.
Strict positive-support constraints can give unattained endpoints; report infima and suprema.
These are model-conditional identified bounds, not automatically confidence intervals.

## Multiplicity and finite search are load-bearing
A validated whole-circle length upper bound can make the walk universe finite because
segments have positive length. The largest sequenced fragment is NOT that upper bound.
Sampled size observations constrain represented molecules, not every unobserved species;
a universal cap requires additional justification. Pooled sizes require joint assignment.
Otherwise declare a multiplicity cap as a prior and widen it in the formal sensitivity check.
Never silently inherit CE/CoRAL defaults or prohibit repeated walks to obtain narrow bounds.
One circle C repeated k times versus k copies of C preserves aggregate edges AND q_AB.
Thus periodic-circle ambiguity does not automatically invalidate this property.
Joining two different circles through shared sequence can change q_AB despite identical edges.

## One decisive formal gate; no execution in this turn
Use a explicitly analytical small graph, NOT fabricated CE S3/S4 inputs or biological truth.
Check three controls by hand, with full permitted observations fixed before scoring.
(1) Replace k copies of C by one C^k: q_AB must stay invariant although circle count changes.
(2) Shared S: circles (S,A)+(S,B) versus (S,A,S,B), each at unit abundance.
Both give S=2,A=1,B=1 and identical branch-junction capacities; q_AB is 0 versus 1.
With only local flanking paths and no separating physical constraint, the bounds are [0,1].
This elementary witness is a guardrail, not a novel theorem or publication result.
(3) Add an explicit independent size/path constraint; enumerate every legal repeated walk
in the small declared universe and derive the sharp endpoints and feasibility by hand.
Do not manufacture a universal size cap from truncated reads; test incompatible inputs too.
The baseline is complete bounded-walk enumeration plus ordinary linear-fractional optimization
for closed linear constraints. This reduction alone is standard, not a contribution.
Native CoRAL/AR/Decoil solutions provide feasible witnesses after compatibility checks;
their selected alternatives need not exhaust F and cannot alone certify outer bounds.
No native rerun or software change is approved here; baseline comparison is formal only.

## Required advance and kill criterion
Retain only a specific nontrivial identifiability characterization or certified exact algorithm
that avoids exhaustive walk enumeration on a declared, defensible repeated-walk class.
It must preserve original paths, nuisance bounds and physical constraints, with endpoint
witnesses/certificates or explicit unattained limits. No such theorem is claimed here.
STOP if the result is merely the controls above, generic fractional optimization,
a decoder repair, native alternative scoring, or bounds informative only under arbitrary caps.
STOP if no concrete beyond-prior-art theorem/algorithm target emerges within this one gate.
A pass supports further mathematical scrutiny only. Synthetic truth can falsify soundness;
it cannot establish empirical biological benefit or replace absent same-cell A32 labels.
No independently validated physical co-residence test is established by these inspected records.

## Source and execution scope
Firecrawl skill and paper reference read in full; three named primary pages retrieved.
Read relevant CoRAL/AR paragraphs and the AACR abstract, not supplements or complete workflows.
Audit-note source claims remain reported inspections, not replication by this decision.
Only this note was written. No source discovery, raw data, installs, experiments, jobs or Git.
