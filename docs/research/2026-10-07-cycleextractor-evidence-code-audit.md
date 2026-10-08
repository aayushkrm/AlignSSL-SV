# CycleExtractor: PathConstraint source audit

2026-10-07. Full goal read. Requested worker: GPT-6 Luna/max; exact model and effort are not independently attested. Scope: pinned native code and solver metadata. Main retains the exact S3 case history, papers, and input provenance.

## Verified source

Official commit: `1b29b338fc2bab437ce56b48b1829bf28f73601a`. Downloaded CE.py is **182,143 bytes**. Git object digest `SHA1("blob " + decimal_length + NUL + bytes)` equals **`e95d8e67c5031eda9451e62eb57ade96179e823f`**, matching both the requested blob and the official recursive tree entry. All CE links below use this immutable commit. The source was inspected, never imported or executed.

## What reaches each stage

There are two parsers. [Create_graph][cg] retains raw tokens/support but derives endpoint-keyed incidence dictionaries for the MILP. [parse_graph_file][pg] separately retains the constraint string, support, and a one-based index for traversal/output. The main caller reparses the original graph after each solve; it does not pass MILP `P_val` to the traversal selector ([cycle caller][caller], [path caller][pcaller]).

| Input field | MILP: Create_graph → model builders | Traversal: match_e_constraints → candidate rank |
|---|---|---|
| Edge order | Derived `p[(i,j,k)]=1` records membership, with sorted endpoints; no ordinal or adjacency constraint. | Preserves order of the **sequence-edge (`e`) projection** only. Tests a contiguous signed segment slice, including one circular wrap. All `c`/`d` tokens are dropped. |
| Multiplicity | Numeric `:n` suffix is discarded. Repeated edge tokens collapse into the same incidence key. | Numeric `:n` is discarded by the regex. Explicit repeated `e` tokens remain repeated in the projected list. A constraint longer than the candidate segment list is rejected; multiple laps are not tested. |
| Sign | Path-token `+/-` is discarded in incidence construction. Graph endpoint strand labels remain in the topology. | Sequence-edge signs survive, modulo whole-walk reversal plus sign flip. Breakpoint-token signs do not enter the match. |
| Support | Parsed/stored integer; every `P[k]` has the same objective coefficient. Support does not weight the reward. | Support is ignored; ranking uses the count of matched constraint indices. It survives as output metadata. |

Sources: [Create_graph, L628–748][cg]; [build_cycle_model, L876–978][cm]; [build_path_model, L2386–2525][pm]; [matcher helpers, L1670–1728][match]; [select_best_closed_walk, L1731–1788][rank]; [select_best_s_t_walk, L2815–2880][prank]; [write_all_cycles_and_paths, L3044–3103][out]. These are semantic readings, not results from test inputs.

Parser boundary: `Create_graph` requires exactly three tab-separated fields and integer support; `parse_graph_file` accepts whitespace separation and uses `int(float(support))`, falling back to `None`. Thus malformed/nonstandard records can be handled differently. This audit assumes the documented tab-delimited syntax; no malformed-input experiment was run ([parsers][cg], [second parser][pg], [README format][format]).

## MILP satisfaction versus traversal satisfaction

Both builders impose only `X_edge >= P[k] * p_edge` for path constraints. Their objective is length-weighted sequence flow plus `gamma * total_sequence_capacity_length / N_constraints * sum(P)`. A selected `P` requires mapped edge-selection flags; it does **not** certify an ordered, signed, multiplicity-correct subwalk. The optional directed connectivity/order variables establish connectivity; they do not encode PathConstraint token order ([cycle builder][cm], [path builder][pm]).

There is separate native multiplicity logic: discordant read counts determine bounds `K` (maximum inference setting 5); binary choices enforce discordant flow `m*F`. Sequence/concordant flows are continuous. Traversal creates edge copies using `round(flow/F)` for every edge type. This graph/flow multiplicity survives, although PathConstraint `:n` does not ([EdgeMultiplicityModel][mult], [cycle builder][cm], [create_closed_walks][walk], [create_s_t_walks][pwalk]).

Traversal uses random edge choices from those copies. Shared-node closed walks are spliced when edge alternation permits; walks that cannot merge remain separate. The cycle selector ranks validity first, then unweighted projected matches, then completeness/closure and fewer unmerged walks. The main requests 100 candidates. Missing matches do not impose a hard rejection or feed an ordered-path cut back to the MILP ([merge helpers][merge], [cycle selector][rank], [cycle caller][caller]). The path selector uses the same matcher, which still permits circular wrap; it is not a full linear breakpoint-path validator ([path selector][prank], [matcher][match]).

The main updates edge capacities and keeps the same path-incidence inputs for later solves. It reports matcher indices independently of MILP `P_val`; it does not consume support or assign each supporting molecule exclusively to a reconstructed circle ([update_the_graph][update], [cycle loop tail][tail], [output writer][out]).

## Which observations can distinguish two circles from one merged circle?

- Different graph junctions/endpoints, edge capacities, and read-count-derived multiplicity bounds can change feasible flows and objective values. Residual capacities can permit later extractions. Disconnected or unmergeable components can remain separate. These mechanisms do not guarantee correct circle count ([graph builder][cg], [MILP][cm], [traversal/merge][merge], [capacity update][update]).
- A different ordered/signed **sequence-edge projection** can change traversal match counts when candidates expose different projected subpaths. The MILP can reward co-inclusion of a constraint's mapped edge set, even without its order. Both mechanisms use positive, soft evidence; neither provides a joint molecule-to-circle mixture assignment ([MILP][cm], [matcher][match], [selector][rank]).
- Distinctions confined to PathConstraint breakpoint order/sign or numeric `:n`, with the same mapped edge set and signed sequence projection, do not reach those respective scores. Different numeric supports alone do not change either score. Actual graph topology still restricts possible traversals; this statement concerns the PathConstraint representation, not arbitrary topologies.
- If both explanations satisfy the same retained capacities/multiplicity bounds and projected matches, this audited representation supplies no additional molecule-boundary or circle-count observation to choose between them. Equality **after CE's projection** does not prove equality of the original observations. A merged optimum alone establishes no identifiable recovery error when both circle multisets also fit all supplied original observations.

Scientific guardrail reused from the [independent territory review](2026-10-07-territory-independent-review.md): separate recovery of generating cycles from LWCNR optimization; preserve multiplicity modulo equivalent representations; challenge with CoRAL and Decoil using equal underlying evidence. This sidecar does not recover S3 inputs, execute a comparator, establish biological truth, measure an algorithm failure, or claim novelty.

## HiGHS dependency and license path

The pinned CLI defaults to Gurobi and offers `--solver highs`. Optional imports allow either backend to be absent; selecting an absent backend raises a parser error. HiGHS wrappers call the **same builders** with `HighsModel`/`HighsGRB`; the facade maps bounds, integrality, coefficients and constraints to `highspy.Highs()`, calls `run()`, and checks `kOptimal` ([imports][imports], [facade][facade], [backend selection][backend], [cycle wrapper][cwrap], [path wrapper][pwrap]). This source path requires no Gurobi API/license checkout. Runtime compatibility and solver equivalence were not tested.

CE's [pinned README requirements][requirements] state Python ≥3.10, NumPy, NetworkX, and optional `highspy` via the documented package-install command. The complete pinned tree contains three files and no requirements lock, package manifest, or LICENSE file; the highspy version and CE's own license grant are therefore not established by that tree.

Current [PyPI metadata](https://pypi.org/pypi/highspy/json) observed highspy **1.15.1**, Python ≥3.9, NumPy, and conditional typing_extensions below Python 3.10. Official tag v1.15.1 resolves to `04024d701f79feb8e2f18bc3df0dffc04ef05088`. Its [pyproject.toml][hmeta] names MIT and packages both `LICENSE.txt` and `THIRD_PARTY_NOTICES.md`; the [MIT license][hlicense] requires retained notices. The [third-party notices][hnotices] identify additional component licenses, including BSD-3, Apache-2.0 and zlib. This licenses HiGHS components, not CE by implication. No package, wheel, solver, or license key was installed or inspected locally.

## Audit scope and calls

Read complete relevant parsers, both model builders/wrappers, multiplicity class, traversal constructors, merge/validation/conversion/matcher/selection functions, capacity update, graph-connection helpers, output writer, and relevant top-level caller blocks. Read the solver facade and relevant README/configuration sections; read the HiGHS license and third-party notices in full. Unrelated CE metrics/export functions and paper landscape were not audited. Full goal and existing reviewer guidance were read locally.

12 public HTTPS requests, each with a 30-second timeout: CE raw source (1), CE tree (1), pinned README (2), PyPI metadata (2), HiGHS tag commit/tree (2), HiGHS license (1), pyproject (2), third-party notices (1). Repeated small source views resolved display truncation; no network/quota error occurred. CE/README and HiGHS license/pyproject Git blobs were verified; the notices digest was computed without a separate tree-entry comparison. No research plugin was needed for this immutable source audit. Only the assigned repository note was written; a 182,143-byte verified temporary source copy was retained. No CE/solver execution, raw-read or genomic acquisition, install, job, or Git command occurred.

[cg]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L487-L766
[pg]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L248-L300
[cm]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L829-L1180
[pm]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L2339-L2683
[match]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L1670-L1728
[rank]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L1731-L1788
[prank]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L2815-L2880
[out]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L3044-L3103
[caller]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L3362-L3433
[pcaller]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L3665-L3730
[format]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/README.md#L42-L98
[mult]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L302-L462
[walk]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L1288-L1478
[pwalk]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L2692-L2812
[merge]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L1198-L1501
[update]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L2114-L2138
[tail]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L3529-L3627
[imports]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L1-L24
[facade]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L29-L245
[backend]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L3170-L3220
[cwrap]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L1183-L1187
[pwrap]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/CE.py#L2684-L2688
[requirements]: https://github.com/AmpliconSuite/CycleExtractor/blob/1b29b338fc2bab437ce56b48b1829bf28f73601a/README.md#L8-L22
[hmeta]: https://github.com/ERGO-Code/HiGHS/blob/04024d701f79feb8e2f18bc3df0dffc04ef05088/pyproject.toml#L9-L22
[hlicense]: https://github.com/ERGO-Code/HiGHS/blob/04024d701f79feb8e2f18bc3df0dffc04ef05088/LICENSE.txt#L1-L21
[hnotices]: https://github.com/ERGO-Code/HiGHS/blob/04024d701f79feb8e2f18bc3df0dffc04ef05088/THIRD_PARTY_NOTICES.md#L1-L78
