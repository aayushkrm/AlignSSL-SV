# Functional ecDNA property: formal gate decision
Date: 8 October 2026. One bounded, paper-only analytic gate.
Read the FULL goal-objective.md and the full 100-line 7 October interrupted saved draft; it had no completed handoff.
Requested decision agent: GPT-6.1 Sol/max; requested main: Sol/high. Exact runtime model/effort is not attested.
Read the completed [Descartes review](2026-10-08-functional-formal-review.md) and [main hand control](2026-10-08-functional-ecdna-analytical-control.md) in full; both accept the restricted mathematics and STOP.

## Decision
STOP the current method framing after this bounded check; do not select a new method lead.
The interrupted 7 October draft proposed this gate; the completed control now supports STOP of this framing.
Both sharp endpoints below are attained by finite mixtures. The reduction uses ordinary circulation and cycle splicing.
This is a useful falsifier, with no claim of a new theorem, established novelty or biological benefit.
The prior note records close CoRAL/AR overlap; this check does not supply the missing advance or re-audit those papers.
Independent physical constraints can change the bounds, but neither arbitrary caps nor ordinary LP establish a method contribution.
CE v1 S3/v2 S4 remain closed at the unresolved exact-input gate. This toy supplies no CE case, A32 label or empirical null.
The publication objective remains unmet. No major scientific selection or experiment campaign is approved by this note.

## Restricted model
G is a finite directed state graph; every nonempty directed closed walk is legal, including repeated traversals.
f >= 0 is a finite, conserved edge flow. Set a_e,b_e >= 0; n_A(C)=a·n(C), and B(C) means b·n(C)>0.
Species abundances w_C are nonnegative real numbers, with sum_C w_C n(C)=f. There is no fixed total circle abundance.
T_A=a·f>0 is fixed; q=sum_C w_C n_A(C) 1[B(C)]/T_A. This counts A copies, not circles or cells.
No paths, size constraints, nuisance structures or missing sequence enter this result. f is exact, not a copy interval.
A separately supplied T_A unequal to a·f makes this restricted model inconsistent; zero T_A does not define q.

## Sharp flow-only bounds
Let E_0={e:b_e=0}. Extend flows on E_0 by zero on all other edges.
M=max{a·x : x is a circulation on E_0, 0<=x<=f}; this compact feasible set contains x=0.
q_min = 1-M/T_A.
Let K_B be the union of SCCs of the positive-flow support that contain a positive-flow B-marked edge.
q_max = (sum_{e in K_B} a_e f_e)/T_A. Edges outside those SCCs cannot contribute A copies on a B carrier.

### Lower endpoint proof
Any compatible mixture's B-free species induce a circulation x_0 on E_0 with x_0<=f.
Its B-free A mass is a·x_0<=M, so q>=1-M/T_A.
Choose an optimizer x*. The residual r=f-x* is a nonnegative circulation.
If r supports a B-free cycle Z with a·n(Z)>0, add a small positive multiple of Z to x*; this contradicts maximality.
Decompose x* and r into finitely many simple cycles. Every A-positive residual cycle must contain B.
All remaining B-free residual cycles have zero A mass; hence the combined mixture attains q_min exactly.

### Upper endpoint proof
Every positive edge of a circulation lies on a directed cycle. Thus support SCCs have no positive edges between them.
A closed walk stays in one support SCC, which proves the upper bound and gives q=0 for A copies in B-free SCCs.
In each B-positive SCC, take a finite simple-cycle decomposition f_K=sum_i w_i n(C_i), with w_i>0.
The cycles cover the component. Their intersection graph, with intersections at identical oriented states, is connected.
Choose 0<t<min_i w_i. Independently choose k_i as floor(w_i/t) or ceil(w_i/t), with E[k_i]=w_i/t.
Every k_i>=1. Along a spanning tree of the intersection graph, splice k_i traversals of each cycle into one closed walk W(k).
Then n(W(k))=sum_i k_i n(C_i); every such walk contains B because it includes every cycle.
Give W(k) abundance t Pr(k). There are at most 2^m choices, and their edge flow is t sum_i E[k_i] n(C_i)=f_K.
This attains the upper endpoint with finite walks and real abundances, even when f or the cycle weights are irrational.
For rational f, a common integer scaling gives one Euler tour per component with reciprocal-scale abundance instead.
No uniform repeat cap is claimed. Convex combinations of the two endpoint witnesses attain every q between them.
Zero-flow edges are excluded from the support; a B label reachable only through zero flow cannot raise q_max.

## Encoding and marker checks
For edge-additive B, delete edges with b_e>0; do not delete all their endpoint vertices or shared sequence states.
For a vertex marker counted on each visit, split that vertex with a marked traversal edge, or delete the marked vertex itself.
A walk must close in the same oriented state. Sharing a genomic label with opposite orientation does not permit splicing.
Rotation preserves counts. Quotient reversal only as a whole-walk reverse complement with consistent physical-copy counts.
If observations specify only sums over strand-paired edges, their oriented allocations remain variables; the fixed-f formula cannot be applied unchanged.
Non-additive intact-gene or motif definitions are outside this proof unless a valid state expansion makes their counts additive.

## Complete toy controls
All segment lengths are one. Each label below denotes one legal oriented state; each directed junction has flow one.
Graph: A <-> S <-> B. Segment-copy flow is S=2, A=1, B=1; T_A=1.
C_A=(S,A), C_B=(S,B), C_AB=(S,A,S,B), written cyclically; the terminal closure adds no extra S copy.
Both w(C_A)=w(C_B)=1 and w(C_AB)=1 give exactly those segment and junction flows.

| Permitted observation/restriction | Compatible witness or consequence | q |
|---|---|---|
| Replace k copies of C by one C^k, when both are permitted | Traversal counts scale by k; B presence is unchanged | unchanged |
| Exact flows only | C_A+C_B versus C_AB | 0 versus 1 |
| Every circle has length <=3 | Only C_A and C_B are legal | 0 |
| Every circle has length exactly 4 | Half-abundance C_A^2+C_B^2 versus unit-abundance C_AB | 0 versus 1 |

Local two-token flanks S-A, A-S, S-B and B-S agree; no whole-molecule observation follows.
The size conditions are hypothetical universal population restrictions, not inferences from sampled fragment sizes.
Under the length <=3 restriction, a hard molecule-compatible A-S-B path requires an absent carrier: F is empty, not q=1.

## Quantitative bridge under a universal length cap of four
The entire legal species set, modulo rotation, is C_A,C_B,C_A^2,C_B^2,C_AB; every circuit concatenates at most two branch loops.
Use respective nonnegative abundances u,v,r,s,z. Exact flows give u+2r+z=1 and v+2s+z=1.
The S and junction equations add no restriction; q=z. For every z in [0,1], u=v=1-z,r=s=0 is feasible.
A cyclic A-S-B occurrence appears once in C_AB and zero times in the other four species; its population occurrence flow H=z.
If independently justified quantitative bounds h_L<=H<=h_U are imposed, sharp bounds are [max(0,h_L),min(1,h_U)].
F is empty if the lower endpoint exceeds the upper endpoint. This is an ordinary LP with a fixed denominator.
For exact length four, set u=v=0 and r=s=(1-z)/2; the same full [0,1] interval and bridge bounds remain possible.
Hard bridge presence alone gives z>0: inf q=0 is unattained, sup q=1 is attained. Taking z=epsilon>0 proves the limit.
Read counts do not supply h_L,h_U without a valid sampling/abundance model. No such bounds or sampling truth are asserted here.
The flow-only formulas do not certify endpoints after paths or size restrictions change the feasible mixture set.

## Gate disposition and handoff
The relaxed case has a complete elementary reduction; the bounded toy has a complete enumeration and ordinary LP.
Neither result establishes the specific nontrivial, non-enumerative advance required by the saved 7 October draft gate.
A solver preserving validated physical constraints, original oriented paths and nuisance bounds is an unsolved broader target here, not a selected lead.
Decision agrees with the completed Descartes review and main hand control; no mathematical disagreement was identified. Close this gate with STOP.
The interval [0,1], periodic invariance and infeasible bridge are retained; no favorable result or positive fraction is forced.
Only this note was written. No new papers, installs, scientific code execution, raw-data work, jobs or Git operations.
