# New territories after the A/B/C stop decisions

Date: October 7, 2026. Main reread the full objective and verified clean HEAD
`12aa6c9418b394c0c77750bbc2b5eee188b3638e`. The preceding turn made progress:
reviewed mathematical corrections, exact output and current tracking were
committed and pushed. The publication objective is still unachieved. DeepSV
is excluded. No stopped callset, copy-state or minority-allele route is reopened.

**Completed decision supersedes the provisional gate below.** Sol6.1/max
rejects these three current method leads; independent scrutiny is complete.
Main accepts. The native estimator control verifies hidden rejected-length
sensitivity, not decisions or performance. The named-C check found a case-label
inconsistency: no three region-C structures established. Unresolved-C/>400-kb
wording below is the article's statement, not verified locus-specific evidence.
Also, acquisition cannot create absent **joint** distinguishing evidence;
phased overlapping molecules can resolve a structure without one long read.
See the [decision](2026-10-07-next-direction-decision.md),
[review/control ledger](2026-10-07-acquisition-direction-review.md) and
[stopped case check](2026-10-07-region-c-consequence-gate.md).

## What this changes

Search three different territories before building another method. The table
records hypotheses, not discovered gaps or experiment approval. Current tools
already do much of the generic work. The most useful next question is whether
**SV-structure-directed molecule acquisition** adds anything beyond existing
dynamic sampling and assembly. This remains a candidate for scrutiny, not a
selected publication lead.

| Territory | Strong existing evidence | Specific question worth challenging | Early rejection / smallest discriminating check |
|---|---|---|---|
| Inserted-sequence and transduction mechanism | The 1,019-genome study already uses SVAN for mobile-element architecture and transduction/source analysis. A separate curated SVA study already studies source elements, genic transductions and compound propagation. [Nature study](https://www.nature.com/articles/s41586-025-09290-7), [SVA study](https://doi.org/10.1186/s13100-025-00373-w). | Can a specific missed compound insertion change a functional conclusion, rather than just add an insertion annotation? Independent source/sequence validation would be needed. | Do not select a generic insertion/source annotator. First establish a consequential residual error against these native analyses; none is established here. No new data or annotator. |
| Junction reconstruction and rearrangement mechanism | SAVANA already uses breakpoint evidence, haplotype information and artifact filtering in somatic SV analysis; Severus is another strong breakpoint-graph comparator surfaced in search. [SAVANA](https://doi.org/10.1038/s41592-025-02708-0), [Severus](https://pmc.ncbi.nlm.nih.gov/articles/PMC12483193/). | Do residual junction-sequence errors change a defensible repair-mechanism inference after native assembly/phasing controls? | No causal mechanism truth or distinct residual failure is established. Do not infer repair mechanism from an alternative alignment alone. Severus is discovery-level evidence here; full methods/code have not been audited in this pass. |
| Acquiring useful molecules instead of more local depth | BOSS-RUNS already optimizes dynamic information gain; current BOSS also implements reference-free assembly. Clinical adaptive sampling already confirms complex SVs. [BOSS paper](https://doi.org/10.1038/s41587-022-01580-z), [pinned BOSS source](https://github.com/goldman-gp-ebi/BOSS-RUNS/tree/a5b6af8520669dd3d182bbf95021a7242a2ede4e), [clinical study](https://doi.org/10.1038/s41431-026-02039-4). | When local sequence/depth is sufficient but long-range linkage is missing, can a prefix-only acquisition policy obtain the distinguishing molecules at fixed cost without knowing the answer? | Generic information-gain or assembly-aware sampling is not new. Compare native BOSS/AEONS, static targets, contig-end targeting and accept-all first. Stop if an ordinary policy solves the case, or the library contains no distinguishable molecule. No replay or campaign approved here. |

## Load-bearing evidence and limits

BOSS-RUNS combines position-wise genotype benefit with read-length and
orientation information, then optimizes benefit per sequencing time. Its 2023
discussion states limits for complex variants; the main model and relevant
implementation sections were read. This is an older method statement, not
evidence of a remaining 2026 gap. [Primary paper](https://www.nature.com/articles/s41587-022-01580-z).

The 2026 clinical study confirms all ten target rearrangements, but region C
has three possible structures despite identifying every breakpoint. The
authors state that linkage across a >400-kb block is needed. Region O has
breakpoints in long segmental duplications that remain ambiguous. These are
reported observations, not our replication. More depth cannot be assumed to
add a linkage type absent from the library. [Clinical results/discussion](https://pmc.ncbi.nlm.nih.gov/articles/PMC13171962/).

This supports an important decision question, not novelty: **continue the
same acquisition, change the library/assay, or stop because the needed
information is unavailable?** A proposed method must predict and test a
useful acquisition choice; merely restating a length barrier is not a paper.
Do not use the unresolved region as positive truth for one of its three
structures, or as an oracle target during replay.

## Current BOSS source audit: generic assembly pivot disconfirmed

Live GitHub API, not the search cache, resolves main to
`a5b6af8520669dd3d182bbf95021a7242a2ede4e`, committed July 24, 2026. Its README
includes version 0.4.0/barcoding; Exa's cached README stopped at 0.3.1.
The recursive tree was complete (`truncated=false`). No install or execution.

| Read source at that commit | Verified scope / implication |
|---|---|
| [README](https://github.com/goldman-gp-ebi/BOSS-RUNS/blob/a5b6af8520669dd3d182bbf95021a7242a2ede4e/README.md) | First 170 lines of live README, plus cached complete README. No reference selects BOSS-AEONS; current simulation configuration exists. |
| [AEONS core](https://github.com/goldman-gp-ebi/BOSS-RUNS/blob/a5b6af8520669dd3d182bbf95021a7242a2ede4e/boss/aeons/core.py) | Entire 11,323-byte core read: ongoing overlap/unitig assembly, coverage updates and strategy regeneration. Blob `41ad2de68f4a2a1eecfd92423497c3b0db744ddb`. |
| [AEONS scoring](https://github.com/goldman-gp-ebi/BOSS-RUNS/blob/a5b6af8520669dd3d182bbf95021a7242a2ede4e/boss/aeons/sequences.py#L982) | Function index and lines 325–408, 982–1136, 1520–1606 read, not the entire 59,788-byte file. Coverage-based scores and uncapped/low-coverage contig-end interest feed length-dependent benefits and thresholds. Blob `5bbad375aa112be1c0508a1c82a09d5afd861572`. |
| [AEONS simulation](https://github.com/goldman-gp-ebi/BOSS-RUNS/blob/a5b6af8520669dd3d182bbf95021a7242a2ede4e/boss/aeons/simulation.py) | Entire 6,726-byte file read. Prefix mapping drives decisions; unmapped reads are accepted; rejected reads are truncated; a cache models pseudo-time. Blob `eeeb014c886cfd1765cade2243cc2794c490fc66`. Not actual instrument behavior. |

Therefore, adding contig ends, reference-free assembly or dynamic depth targets
alone would overlap native code. A narrow residual question concerns
structural alternatives and informative linkage, not whether assembly exists.
Uninspected mapper, sampler, cache, repeat-filter and live readfish code may
already change that assessment. No absence claim about the complete codebase.

## Label/access gate: no genomic transfer

The human clinical dataset is **controlled access**, not a ready public replay:
EGA `EGAD50000001821`, DAC `EGAC50000000748`, 12 listed samples/files totalling
169.8 GB. Its access page requires approved users/projects and ethics approval.
No application, agreement, login, patient data or file transfer was attempted.
[Official EGA record](https://ega-archive.org/datasets/EGAD50000001821).

BOSS's paper points to ENA `PRJEB51967`. A bounded 64-KiB metadata request
returned 373 bytes and two runs: `ERR9630949` and `ERR9630950`. Their submitted
tar.gz sizes are **100,593,111,985** and **98,490,195,827 bytes**; FASTQ fields
are empty in this report. Total **199,083,307,812 bytes**. Archive member
contents, raw signals, timing and replay suitability have not been inspected.
These microbial data do not establish human-SV structure truth. No archive
download or prefix/member inspection occurred.
[Official ENA study](https://www.ebi.ac.uk/ena/browser/view/PRJEB51967).

Existing project data are not a ready acquisition benchmark: the three-Mb
HG002 fixture and historical donors are development evidence; reference,
callability and independent truth limits are recorded in the existing
[data assessment](2026-09-23-data-decision.md). Neither old data age nor a
new paper's title determines suitability. Do not redownload the stopped
released-callset inputs for this different question.

## Source and execution audit

- Date calculation: October 7, 2026 minus 18 calendar months is April 7, 2025.
  Discovery window Apr 7, 2025–Oct 7, 2026; older strong priors retained.
- Exa: seven searches, **55 requested result slots**, not 55 papers read or
  deduplicated sources. Initial three large highlight responses were truncated
  in output; unshown content is not counted as reviewed. Four later searches
  were reduced to 1,700–2,100 characters per result before display.
- Seven primary page fetches: three at 10,000 characters, cached BOSS README
  at 14,000, clinical article at 26,000 and two at 11,000. These are five paper
  entities plus one repository, not seven complete method audits. Prefixes
  stop before full methods for the population/SVA/SAVANA papers. BOSS methods,
  limitations and data statement were additionally read through the web tool.
- Life Sciences Literature Entrez: two searches requested ten IDs each; compact
  summaries requested for both ten-ID lists. Output omitted the final record
  in each list, so only 18 individual titles were inspected. The first broad
  query had poor specificity and was replaced with explicit Title/Abstract
  fields. Metadata titles alone establish neither efficacy nor data readiness.
- PMC skill resolved the clinical paper to `PMC13171962.1`, PMID 41731181,
  DOI 10.1038/s41431-026-02039-4, CC BY/open access, queried nonretracted record.
  Metadata is a checked source, not biological evidence. Its XML was fetched
  twice into RAM, **117,000 bytes each**, ≤1 MiB and MD5
  `d1debc195319db1415a6cff359880659` verified before parsing each time. Read
  adaptive-sampling methods, structural characterization, full Discussion,
  data/code statements. Supplements, figure pixels and underlying patient
  sequences remain unread. No raw XML saved.
  [Checked metadata](https://pmc-oa-opendata.s3.amazonaws.com/metadata/PMC13171962.1.json).
- General web openings failed for two publisher URLs; Exa and versioned PMC
  XML supplied the relevant clinical content. No failed lookup is evidence.
  No Firecrawl CLI was assumed or installed; Exa/LifeSci served distinct needs.
- Three explicitly requested Luna/max workers failed at the usage limit before
  writing output. Their close attempts returned missing handles, not live
  work. Main completed this bounded review directly; no substitute model or
  repeated worker dispatch. Requested configurations are not attested execution.
- Read-only cluster check: `squeue -u igorno` empty; scratch expiry October 22,
  23:02:50 cluster-local, 15 days 1 hour left, one extension. No job cancellation,
  scientific input read or change to historical **8,588,703,005-byte** charge.

## Completed gate; no implementation campaign

The maintained reviewer challenged novelty, timing and access. The high-impact
decision rejects acquisition: no meaningful residual native benefit or ready
causal test is established. The later paper-only consequence gate also stopped
at source identity, not a biological null. No controller, claimed clinical
savings, 199-GB transfer or patient access follows. Next compare genuinely
distinct scientific questions; do not rescue these leads with more wrappers.
