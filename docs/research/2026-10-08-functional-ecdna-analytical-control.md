# Functional ecDNA query: completed analytical falsifier

2026-10-08. Main's hand derivation, checked against the
[independent review](2026-10-08-functional-formal-review.md).
This is a mathematical control, not a native CE input, simulated dataset,
biological result, or selected publication direction. No code was executed.

## Restricted observation model

Fix a finite directed graph and a nonnegative circulation `f` on its edges.
Each allowed species is a finite directed closed walk, with unrestricted
repetition. A finite mixture has real weights `w_C >= 0` and exactly reproduces
`f = sum_C w_C m(C)`, where `m(C)` counts edge traversals.
Fix nonnegative marker weights `a`; `n_A(C) = a^T m(C)` and `T_A = a^T f > 0`.
The B marker is a specified edge or node; `I_B(C)` means the walk visits it.
Define `q = sum_C w_C n_A(C) I_B(C) / T_A`.
For a node marker, count A visits on outgoing traversals. Count supported B
occurrences only. These definitions do not automatically represent intact genes.

There are no read paths, size limits, sampling laws, copy intervals, impurity,
missing graph edges, noncircular structures or per-cell assignments in this model.
All directed closed walks must be legal species. An oriented biological graph
needs a separate legality argument; reversal is not silently made legal.
The endpoints are identified bounds conditional on this model, not confidence
intervals, expression effects, fractions of cells, or proof that ecDNA exists.

## Exact unrestricted endpoints

Delete B edges, or B nodes and their incident edges, to form `H`.
Let `M = max a^T x` over circulations on H with `0 <= x <= f`.
The sharp, attained lower endpoint is `q_min = 1 - M/T_A`.

Every mixture's B-free flow is a feasible x, proving this lower bound.
Choose a maximizer x*: its feasible polytope is compact. The residual `f-x*`
is a nonnegative circulation. It cannot contain a B-free cycle with positive
A weight: adding part of that cycle to x* would improve the objective.
Cycle-decompose x* and the residual. B-free residual cycles may remain, but
they have zero A weight. Thus this decomposition attains the claimed endpoint.
This is an ordinary maximum-cost circulation, not a new algorithm.

Let U be the positive-support strongly connected components containing B.
The sharp, attained upper endpoint is `q_max = (A flow within U)/T_A`.
Each closed walk is in one component, and positive circulation has no positive
flow between distinct components. This gives the upper bound.
For a component in U, decompose its flow as `sum_i w_i m(C_i)` with `w_i > 0`.
The cycle-intersection graph is connected because these cycles cover that
component. Choose `0 < t < min_i w_i`. Independently round each `w_i/t` to
its floor or ceiling with the correct expectation, giving integers `k_i >= 1`.
For each finite rounding outcome, the connected balanced union of k_i copies
has a directed Euler tour W. It visits B. Give W abundance `t Pr(outcome)`.
The resulting finite mixture recovers the flow exactly, even for irrational
real weights, and puts every A copy in that component on a B-containing walk.
There are at most `2^m` outcomes for m cycles. This existence proof is not a
claim of efficient enumeration. Long walks and small abundances can be essential.
Extra molecule, length or multiplicity restrictions can invalidate the proof.

## Full hand-checkable control family

Toy vertices S, A, B each have unit visit length. Edges S->A, A->S, S->B,
B->S each have flow one. Hence segment visits are S=2, A=1, B=1.
CA=(S,A), CB=(S,B), CAB=(S,A,S,B), with cyclic closure understood.
CA and CB at abundance one give q=0; CAB at abundance one gives q=1.
For `0 <= beta <= 1`, CAB abundance beta and each of CA/CB abundance
`1-beta` give the same observations and q=beta. Local two-token flanking
paths also agree. No whole-molecule observation is implied by those paths.

| Added assumption or observation | Sharp bounds / outcome |
|---|---|
| None | [0,1], both attained |
| Universal toy length <=3 | [0,0]; only CA and CB are legal |
| Length <=3 and a positive A,S,B bridge-carrier requirement | Empty feasible set, not certainty at zero |
| Universal toy length <=4 | [0,1]; both attained |
| Every species has toy length exactly 4 | [0,1]; CA^2/CB^2 each at abundance 1/2 give zero, CAB gives one |
| Length <=4 and strictly positive bridge abundance | Infimum 0 is unattained; maximum 1 is attained |
| Length <=4 and declared bridge-copy abundance in [1/4,3/4] | [1/4,3/4], both attained |

For length <=4 the complete universe, modulo rotation, is CA, CB, CA^2,
CB^2, CAB. Each excursion from S is two visits and chooses A or B.
Only CAB contains the A,S,B bridge, once; total A flow is one. Thus its
abundance equals q, proving the final row. This is an abstract quantitative
constraint, NOT a read count converted to abundance without a sampling law.
All length assumptions are stipulated physical restrictions in this toy.
Neither a longest observed read nor a decoder's repeat cap supplies them.
Replacing C^k at abundance w by C at abundance kw preserves edge flow AND q
when both species are permitted. Circle count changes; this query does not.

## Stop and remaining scientific limits

Main accepts the review's STOP of the current method framing. The exact
unrestricted reductions and complete small bounded universe expose standard
baselines. They do not solve the original paths/nuisance/physical-constraint
proposal or establish a distinct nontrivial theorem, algorithm or empirical gain.
Do not turn these controls into a method claim, software wrapper, training
campaign, fabricated CE S4 reproduction or biological impossibility result.
The broader research goal is active and unachieved. No new lead is selected.
