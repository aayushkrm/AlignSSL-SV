# Independent functional ecDNA formal review

Date: 2026-10-08. Verdict: accept the restricted mathematics; STOP the current method/publication framing.
The full attached goal and the completed centromere crosswalk, CE source audit, native-example follow-up, saved functional decision, and territory/error-twin reviews were read.
The functional decision is a saved proposal, not a completed reviewer response or approval. This review supplies independent reasoning, not native replication.
Requested reviewer configuration: GPT-6.1 Sol/high. Actual backend model/effort is not independently attested; no additional agent was launched.
Main's Oct 8 05:18 UTC quota figures (primary 2%, week 33%) are reported context, not measurements made by this reviewer.

## Exact model accepted for this control

Use a finite directed graph and a fixed nonnegative circulation f; retain only edges with f_e > 0 as its positive support.
Every permitted species C is a finite directed closed walk, with unrestricted repetition and real abundance w_C >= 0.
Let m(C) be its edge-traversal vector. Require sum_C w_C m(C) = f exactly.
Fix nonnegative coefficients a so n_A(C) = a^T m(C); for a node marker, count visits through outgoing traversals.
B is a fixed edge or node marker; I_B(C) indicates at least one traversal/visit. Only supported B occurrences count.
Set T_A = a^T f > 0 and q = sum_C w_C n_A(C) I_B(C) / T_A.
There are no path, size, sampling, nuisance, purity, or noncircular-copy constraints in this control.
The result applies only when all such directed walks are legal species; a biological signed/alternating graph needs its own legality check.

## Sharp lower endpoint: accepted, with a precise residual condition

Let H be the graph after deleting B edges, or B nodes and all incident edges, as appropriate.
Define M = max {a^T x : x is a circulation on H, 0 <= x <= f}.
Then q_min = 1 - M/T_A, and the minimum is attained.

Proof: in any compatible mixture, the B-free species contribute a feasible x, so their A-copy total is at most M.
The feasible flow polytope is compact, so choose an optimizer x*. Both x* and r = f - x* are nonnegative circulations.
If r had a B-free directed cycle D with a^T m(D) > 0, a positive multiple of D could be added to x*, contradicting optimality.
Decompose x* and r into finitely many directed cycles. Every B-free residual cycle therefore has zero A count.
All residual A copies lie on B-containing cycles, giving q = (T_A - M)/T_A exactly.
Correction: the residual may still contain B-free cycles with zero A count. It need not be acyclic or contain B on every cycle.
This is an ordinary maximum-cost circulation with the specified marker weights, not evidence of a new optimization method.

## Sharp upper endpoint: accepted, and attained by finite walks

Let U be the positive-support strongly connected components (SCCs) containing a supported B occurrence.
Let T_U be the A-copy flow within their union. Then q_max = T_U/T_A, and the maximum is attained.
Every closed walk lies within one SCC; a walk outside U cannot contain B. This proves the upper bound.
Positive circulation has no positive-flow edge between distinct SCCs, so components can be treated separately.

For one component in U, write f = sum_i w_i m(C_i) there, using finitely many positive-weight directed cycles.
The graph that joins two cycles when they share a vertex is connected: the cycles cover the connected support of the SCC.
Choose 0 < t < min_i w_i. For each i, independently choose integer k_i from floor(w_i/t), ceil(w_i/t), with E[k_i] = w_i/t.
Every k_i >= 1. For each possible k-vector, the union of k_i copies of every C_i is balanced and connected, hence has a directed Euler tour W_k.
Each W_k visits B. Assign abundance t Pr(k) to W_k. Then sum_k t Pr(k) m(W_k) = sum_i w_i m(C_i) = f.
There are at most 2^m choices for m cycles, each with finite multiplicities and finite walk length; irrational real weights cause no problem.
Combine these mixtures with any cycle decomposition outside U. Every A copy within U has a B-containing carrier.
Thus this is an exact finite witness, not merely an asymptotic supremum. It may require long walks and very small positive abundances.
Directed splicing preserves orientation. Rotation changes only the start position; combine weights for duplicate species.
Do not add reversed traversals unless the representation makes them legal. Physical reversal equivalence must preserve marker counts and observations.
An artificial multiplicity cap, universal physical length cap, or extra molecule constraints can invalidate this construction.

## Analytical controls, not CE S4 or biological data

Use edges S->A, A->S, S->B, B->S, each with unit flow. Each symbol denotes a unit-length segment visit.
CA = (S,A), CB = (S,B), CAB = (S,A,S,B), with cyclic closure understood. Both explanations give S=2, A=1, B=1.

| Permitted observations/species | Feasible explanation | Sharp q bounds |
|---|---|---|
| Edge flows only; unrestricted finite walks | CA+CB or CAB, each listed species at unit abundance | [0,1] |
| Universal L <= 3 | Only rotations of CA and CB | [0,0] |
| Universal L <= 3 plus bridge A,S,B on a carrier | No permitted circle can carry the bridge | Empty feasible set |
| Universal L <= 4 alone | CA^2 and CB^2 each at abundance 1/2; or CAB at abundance 1 | [0,1] |
| Every species has L = 4 | CA^2/CB^2 each at abundance 1/2; or CAB at abundance 1 | [0,1] |
| L <= 4; declared bridge-copy abundance in [1/4,3/4] | CAB abundance beta; CA/CB each at abundance 1-beta | [1/4,3/4] |

For L <= 4, every legal walk is a rotation of CA, CB, CA^2, CB^2, or CAB: each excursion from S has two visits and chooses A or B.
Mixing the two endpoint explanations attains each intervening q. With a strictly positive bridge-carrier requirement at L <= 4, q has infimum 0 and maximum 1, but no attained minimum 0.
Indeed, abundance alpha of CAB and 1-alpha of each CA/CB preserves f and gives q=alpha for 0 < alpha <= 1.
One C^k at abundance w versus C at abundance kw has the same edges and q: n_A(C^k)=k n_A(C), I_B(C^k)=I_B(C).
That equivalence requires both representations to be allowed; a cap can exclude one. L here is declared toy length, not an inferred physical observation.
A universal physical cap needs independent justification. The largest observed read/fragment does not supply it.
These are model-conditional identified bounds, not confidence intervals; empty feasibility means inconsistency, not q=0.

Narrow follow-up: checked only the added quantitative-bridge and exact-length-4 rows in [main's analytical control](2026-10-08-functional-ecdna-analytical-control.md); both are correct.
Write beta = w_CAB. Flow requires w_CA + 2w_CA^2 + beta = 1 and w_CB + 2w_CB^2 + beta = 1.
Only CAB contains the directed A,S,B bridge, once per circle traversal, and it has one A visit. Hence bridge-copy abundance = beta = q since T_A = 1.
Restricting that abstract abundance to [1/4,3/4] gives exactly that interval, with every value attained by the table's mixture; it is not an observed read count.
With every species of length exactly 4, w_CA = w_CB = 0; w_CA^2 = w_CB^2 = (1-beta)/2 and w_CAB = beta attain every q in [0,1].
This hand check changes no STOP decision or configuration/attestation statement; no other claim in main's note was reviewed in this follow-up.

## Evidence corrections and decision

Accept centromere STOP only for this paper as the activity-to-segregation anchor: no contrast in the two balanced lines and no linked derivative-fate outcome is established.
GM03417 is mosaic; dosage snapshots are not tracked loss events. Missing outcomes are UNRESOLVED, not a biological null or field-wide absence.
Accept the CE note as a reported pinned-source audit of retained representations. Omitted order/sign/suffix can be redundant under topology or upstream semantics.
Native CoRAL numeric-suffix meaning has not been independently checked here. Token loss alone proves neither lost independent information nor an identifiable recovery error.
Neither CE nor a solver was executed; HiGHS compatibility/equivalence and native S3/S4 input provenance remain unresolved.
The closed-walk formulas expose an exact baseline for the stripped model. They do not handle the original proposal's paths, physical constraints, nuisance bounds, or biological circle status.
Finite bounded-walk enumeration with linear programming is also a standard baseline when T_A is fixed; a variable denominator requires the usual fractional formulation.
Novelty cannot be inferred from missing inputs, unread sources, or an absence of a found method. No beyond-prior-art contribution or empirical gain is established.
STOP this method framing under the saved gate: the controls and standard reductions do not supply the required defensible constrained theorem/algorithm target.
Retain this result as an analytical falsifier and baseline. The broader research goal remains unachieved; no new campaign or direction is selected.

Scope: local note reading and hand proofs only. Underlying papers/source were not independently re-inspected; their factual claims retain the notes' inspection limits.
Only this review file was written. No source search, download, raw data, install, experimental/code execution, cluster action, job, or Git operation occurred.
This is review of the single paper-only analytical gate. Expensive-experiment approval was neither requested nor granted.
