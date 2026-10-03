# Updated goal and close-prior-art challenge

Date: October 4, 2026 local / October 3 UTC. Status: research triage;
no new biological result, selected method or experiment campaign.

## Governing objective

The main agent read the full updated objective after the user reported an
update. Its SHA-256 is
`624de4ace478d0476cc8d899197c61db22a32c55543edb61f79ac7e9bd4145a0`.
The objective remains active. Publication-worthy science is the priority,
not preserving AlignSSL, SSL, a particular architecture or a prior data plan.
DeepSV is excluded as the scientific foundation. Keep historical failures
and negative results; do not erase them when changing direction.

The operating sequence is understand, research, compare competing directions,
reject weak ideas, implement, experiment, analyze, review, document and push.
Prefer a small experiment that can disprove an idea before large compute.
Do not choose data, metrics or thresholds to force a favorable result.

Requested model roles are Sol6.1/high for the orchestrator, Luna/max for
workers, Sol6.1/max only for high-impact decisions, and a separate Sol6.1/high
reviewer. Returned agent metadata does not independently attest actual model
execution. Internal subagents are used; no new user-owned chat was created.

Use connected research tools by task. Life Sciences Literature is included.
Firecrawl is a plugin, not an assumed CLI or mandatory exclusive search route.
Find an alternative when a tool fails. Keep progress and research notes current
and push meaningful checkpoints without credentials or raw genomic data.

## New close prior art

This is a targeted check, not an exhaustive systematic review. The search
window is October 4, 2025 through October 4, 2026. Read published methods as
well as metadata; a search hit does not validate a novelty claim.

| Study | Verified scope relevant to the decision | Implication for our proposal |
|---|---|---|
| COSIGT, published September 8, 2026 | Masked cosine genotyping; native distinct-haplogroup margin filtering; leave-all-out and ancestry-mismatched tests; comparison with Locityper 1.2.0 | A generic confidence filter or demonstration of missing-panel harm is insufficient |
| SVPG, published September 21, 2026 | Long-read graph discovery, refinement and graph augmentation; current callers and difficult-region benchmarks | Generic graph-guided recovery or augmentation is insufficient |
| minisv, current PMC citation September 29, 2026 | Joint support-read alignment to a linear reference, pangenome and personal normal assembly | Generic personal-assembly filtering or its known population-panel false negatives is insufficient |

[COSIGT](https://link.springer.com/article/10.1186/s13059-026-04242-4)
already benchmarks 265 SV loci and 326 challenging genes. Its SV leave-all-out
design uses 62 HGSVC short-read samples against 38 HPRC assemblies. The native
margin threshold of 0.002 is indicative and explicitly architecture-dependent,
not a calibrated universal error probability. Its best-achievable sequence-QV
comparison is not, by itself, event-level structural correctness. Published
outputs and reproduction scripts are linked in the
[paper repository](https://github.com/davidebolo1993/cosigt_paper).

[SVPG](https://www.nature.com/articles/s41592-026-03219-2)
already reports somatic benchmark false negatives represented in its germline
pangenome. Its paired-sample workflow subtracts normal calls using a 1,000-bp
breakpoint rule. Population-panel presence alone does not establish a variant's
somatic status in a particular donor. This logical distinction is not a new
biological finding or proof that a published benchmark is wrong. Released
VCFs and scripts are linked at
[Zenodo 18456502](https://zenodo.org/records/18456502); their bytes, reference
identity and suitability for our experiment have not been checked here.

The [minisv article](https://pmc.ncbi.nlm.nih.gov/articles/PMC13621377/)
explicitly discusses true somatic SVs lost by population-pangenome filtering
and mosaic alleles incorporated into a self-assembly. It proposes
haplotype-aware retention. Rediscovering either limitation is not enough.
The earlier September 4 online-date lead was not independently confirmed in
this check; retain the verified PMC citation date rather than pool versions.

## Competing directions, not a selected thesis

| Direction | Evidence needed to survive | Present obstacle or rejection risk |
|---|---|---|
| Candidate/call-set recovery in difficult regions | Modern compatible caller outputs; confidence-qualified structural truth; fixed matching rules and full denominators | Released final calls are not internal candidate ceilings; generic unions are prior art |
| Conditional genotype-confidence transfer | Caller-specific score meaning, native safeguards, independent donor/catalog GTs and matched decision coverage | Existing source archives are pedigree development material, not unrelated confirmation |
| Structural panel inadequacy or event-level QV blind spots | Independent structural-event labels, panel-equivalence rules and all native controls | The verified Locityper summary archive does not supply these labels; COSIGT is a closer control |
| Paired-normal graph/somatic inference | Independent tumor-normal truth, local normal callability and comparison with current native/personal-assembly methods | Both SVPG and minisv already expose relevant limitations; no distinct residual mechanism established |

The main agent sent the updated objective to the active workers. Aristotle
(`01a102f6-dca0-7a81-9638-19825a8e31e2`, Sol6.1/max requested) is making the
bounded high-impact direction recommendation. Helmholtz
(`01a102f6-dd04-7c90-b4c9-4763707d83a4`, Luna/max requested) completed the
source-only Locityper alignment-to-structural-label feasibility check without
acquisition or outcome scoring, then was closed. Anscombe
(`01a102db-1c85-72a2-b1c0-fc76d4a46c2e`, Sol6.1/high requested) completed a
separate direction review and is checking this written handoff. No outcome
protocol has been approved. A concrete protocol must be written and challenged
before scoring.

### Independent review and source-feasibility outcome

The independent reviewer recommends stopping **open-panel confidence as the
active publication lead under the present budget**, while continuing the wider
goal. Main accepts this limited stop: do not build a detector from the existing
QV archive or acquire the larger database solely to preserve this direction.
Keep the source route as an option only if a distinct scientific need and
independent structural labels are established.

The reviewer favors an event-level QV diagnostic only if confidence-qualified
event truth and combined native outputs already exist. QV dilution alone is
not a contribution. Modern call-set recall with adjudicated, recoverable
residual misses is the competing route. Both need a frozen practical effect
threshold, uncertainty and adequate denominators; insufficient precision is
inconclusive, not a biological null. Truth construction, alignment, graph
building and confirmation costs must be counted, even with precomputed outputs.

Helmholtz recommends deferring the Locityper database as structural truth.
Main checked the pinned
[PAF writer](https://github.com/tprodanov/locityper/blob/146cfd42e9179bafd63d1f41db7fc449940989de/src/command/align.rs):
it writes full-span, `+`-strand records and MAPQ 255, including zero-alignment
records for skipped pairs. Those fields do not supply mapping confidence.
The writer also records requested alignment parameters in a leading comment;
the archived parameter values have not been inspected. The worker's proposed
simple-indel screen requires sequence-checked CIGARs, unambiguous flanks,
duplicate-sequence donor membership and complete callable comparisons. Missing
or ambiguous comparisons remain unknown. It cannot establish inversion or
copy-number truth. These are feasibility limits, not measured error rates.

Do not pool Locityper v0.17.3 archive scores with the newer comparator outputs
without a new version-specific protocol. No new scientific thesis or biological
improvement has been accepted by these reviews.

## Source accounting and failures

The literature worker Cicero clarified that its original research pass used
three Exa queries with ten requested results each: 30 requested slots, not
30 papers read. Its exact original queries and returned-hit counts are not
preserved in the available handoff. Its statement that it made no new searches
referred only to the final provenance follow-up. It returned three leads and
reported primary-method checks; the main agent separately checked the
load-bearing methods above. Cicero completed and was closed.

The main discovery pass requested three named-paper Exa queries with five
results each: 15 requested slots, not 15 validated papers. Life Sciences
Literature Entrez returned PubMed records 42768106 and 42711702; a separate
summary verified the SVPG and COSIGT publication dates. These metadata checks
support identity and date, not methods or performance claims.

AACR article/PDF and several DOI/web openings failed. The PMC web page returned
a browser check. Life Sciences Literature resolved the current PMC metadata,
license, DOI and text/XML locations for PMC13621377. The S3 text request timed
out. First-party Europe PMC full-text XML supplied the methods and discussion
instead. No provider restriction was bypassed, and no full paper was committed.
Only canonical links are retained; cookie/session redirect parameters are not.

## Operational checkpoint and limits

A fresh read-only `squeue -h -u igorno` returned no project-account jobs.
`ws_list` showed the restart workspace expires October 22, 2026 at 23:02:50
cluster-local, with one extension available and about 18 days 21 hours left.
No cancellation, job submission or large genomic-data acquisition occurred.
The existing Locityper archive remains inventory/schema evidence only;
no outcome rows were parsed or scored in this follow-up. Its larger database
was not acquired. Existing biological outcomes and confirmation data remain
unchanged.

Next: integrate the direction and independent-review findings, choose a
scientifically meaningful bounded falsifier if one survives, or reject the
current lead and move to a different question. Do not replace the unresolved
truth gate with another generic reader or call a feasibility check a result.
