# Independent comparator case review

13 October 2026, Asia/Tomsk. Replacement maintained reviewer after the supplied
authoritative previous-Franklin `not_found` report. Requested GPT-6.1 Sol/high;
backend and effort are not independently attested. This role continues.
Only this note is owned. No costly campaign is released.

## Decision

**Reject novelty of the generic claim that graph-encoded somatic alleles can be missed.
SVPG already reports it. HOLD a new recovery contribution and the INV mechanism.**
One fixed-case comparator falsifier is worth retaining, subject to existing
evidence qualification below. It is not a new experiment result or a paper lead.
Native guided-mode recovery is plausible, not demonstrated. Neither a rescue nor
a residual failure has been observed in this review. Missing access is not failure.
HG002 annotation stays STOP; the full publication goal remains active and unmet.

I fully read the goal objective and both completed October 12 decision/review notes:
[investment decision](2026-10-12-functional-deletion-investment-decision.md) and
[screen rigor review](2026-10-12-deletion-screen-rigor-review.md).
The October 13 native-mode and investment sidecars were absent at initial inventory.
No completion, agreement, or reviewer acceptance is inferred; no repeated polling ran.
Main retains archive metadata and actual case checks. Their results are not mine.

## Load-bearing primary evidence

The [SVPG publication](https://www.nature.com/articles/s41592-026-03219-2), posted
21 September 2026, has distinct inputs: BAM signatures for graph-guided refinement,
and GAF alignments for novel signals. Results report four graph-represented alleles
among five missed HG008 INDELs. Figure 4d names a 419-bp deletion at
chr7:19196736. This is author-reported GIAB cancer-specific truth, not new validation.
Methods describe independent tumor/normal calls followed by position-only subtraction
within 1,000 bp. This is separate from the absence of a novel graph signal.

Guided-mode Methods retain deletion signals from missing reference nodes and refine
them against the original BAM signal. Thus graph representation does not establish
that both native modes miss the allele. Guided mode can still lose weak linear
signatures; its germline genotype model does not establish somatic sensitivity.
These are mechanism hypotheses inferred from Methods, not code or runtime findings.

The [miniSV v1 preprint](https://www.biorxiv.org/content/10.1101/2025.10.28.685154v1.full)
describes joint linear, graph and optional normal-assembly evidence, plus filtering
other callers. Its intersection rule can discard a linear signal absent in graph
alignment. Do not assume miniSV rescues this graph-represented allele. A qualified
paired linear caller is therefore essential even when miniSV is included.

## Strong controls and truth scope

| Required comparison or fact | Why it changes the decision |
|---|---|
| Both applicable native SVPG modes, paired linear calling, and miniSV's documented paired configuration | A GAF-only miss is not an unmet recovery capability. Native somatic callers such as Severus/nanomonsv are stronger controls than an unqualified VCF subtraction. |
| Same tumor/normal DNA, callable context, reference bases and evidence budget | Compare equal permitted information. Let each caller use its supported alignment. Record any extra graph, normal assembly or learned prior; give the intervention the same budget. |
| Graph panel identity, construction date and evaluated-sample membership | A graph allele can be valid population prior information. Inclusion of evaluated tumor/normal or truth-building material creates dependence that must be disclosed; truth cannot seed the proposed discovery method. |
| Pretraining provenance for any learned comparator/intervention | Record evaluated sample/locus exposure where known. Unknown exposure remains unknown; no model download is needed for this gate. |
| Exact alternate sequence/path, both flanks and coordinate convention | Node/bubble overlap and a 419-bp size do not prove the same allele. Accept sequence-equivalent placements in repeats; preserve distinctions between different nearby alleles. |
| Actual matched-normal DNA support and genotype | A missing normal VCF call does not prove absence. Check coverage and allele/reference support; distinguish recurrent somatic formation from inherited allele, mosaicism or genotype error. |
| Tumor/normal purity, local total and allele-specific CN, and truth scope | Read fraction is not a diploid genotype. CN change/LOH can change an existing allele's fraction. Unknown quantities block a strong somatic-origin claim, not all detection analysis. |

The five misses are selected by the authors' failure inspection. Four of five is
not prevalence among somatic SVs, graph alleles, patients, or genomic regions.
The named case can diagnose a mechanism; it cannot estimate recall or generalization.
A positive intervention must also control false somatic calls, not merely emit more.

## One retained cheap falsifier: the named chr7 deletion

Question: **Does the exact published allele remain missed after the existing
native guided mode and strong paired controls use the same permitted evidence?**
Freeze chr7:19196736/419-bp DEL before viewing new comparator outcomes. First use
main's qualified existing calls and case packet. Record build, sequence, versions,
mode, support thresholds, normal identity and graph panel. Do not select a different
case if this one closes the claim. Other four cases remain untested.

Trace existing output through candidate formation, pre-subtraction calls, paired
filtering and allele matching. Test graph representation by sequence/path identity.
Test any subtraction loss against the actual normal allele, not coordinate distance.
An allele-aware subtraction correction alone is routine unless it yields a distinct,
reproducible useful result beyond current paired callers at comparable precision.

```text
fixed allele + qualified paired evidence + equal permitted information
                              |
                existing/native comparator recovers?
                   yes -> close this case's unmet-method claim
                    no -> input distinguishes exact allele?
                             no/unknown -> HOLD or information limit
                             yes -> trace one residual loss mechanism
```

No new run is released here. A later native check needs a supported entry point
costed by main; retain the prior proposed cap of one case/one CPU-hour, no large
graph/read/model acquisition. If existing evidence cannot qualify the case cheaply,
HOLD without more setup. Native incompatibility is untested, not failed.
An equal-information residual miss retains a hypothesis only. Further investment
needs an actionable cause, useful precision/recall behavior and independent cases.
A simple mode union may be useful, but is not novel merely because it adds calls.

## Complex INV alternative and bounded audit

The [August 1 published INV benchmark](https://doi.org/10.1186/s13059-026-04223-7)
abstract confirms Strand-seq plus phased assemblies, difficult complex events,
and an alignment effect. Low recall does not identify loss of linkage/orientation.
The supplied seven-caller preprint Figure 5 already detects complex components;
component detection must be compared with recovery of the complete allele.
Do not transfer that figure or its panel to the supplied nine-caller publication.
The publisher scrape exposed abstract/metadata but no Results/Figure 5 body;
Firecrawl's DOI passage request returned 404. Published body claims remain unchecked.
Keep INV conditional on a fixed supported residual beyond equivalent representations
and strong callers. Strand-seq orientation and assembly-derived junction/CN/linkage
truth have different scopes. Missing phenotype blocks a clinical claim, not a
molecular calling contribution. Do not rerun the existing generic benchmark.

Audit: Firecrawl skill and full paper-research reference read; selected complete
SVPG Results/Figure 4/Methods passages and miniSV v1 Methods read independently.
No exhaustive supplement, code, archive or case-file audit is claimed. No genomic
or model downloads, installs, jobs, Git actions or historical edits occurred.
The old completed reviews remain intact. Expensive work and major positive claims
still require maintained independent review of actual qualified evidence.

## Addendum: independent actual-packet review, October 13

**ACCEPT the bounded archived-record comparison. STOP this named case as a new
generic 419-bp deletion-detection lead. Exact allele recovery and somatic origin
remain HOLD; those limits do not justify running guided mode merely to repeat
already reported comparator detection. No new contribution is established.**

This supersedes the earlier statement that no actual comparator result was read,
within the narrow scope below. It does not establish current native performance.
I read [sources.json](../../results/svpg_named_case_20261013/sources.json) and the
complete [native-mode note](2026-10-13-svpg-native-mode-check.md). At the review
snapshot, the proposed `index.json` was absent. I did not infer its contents.
The actual members were under `/Users/akm/aayushkrm-AlignSSL/runs/`
`svpg-named-case-20261013.wDDbXj/`, outside the repository's runs directory.

I independently checked all 11 members: each <250,000 bytes, exact listed size,
SHA-256 and decoded CRC32. All pass. EOF record counts of the ten VCFs agree
with the packet. Only the frozen chr7:19195736–19198155 neighborhood was selected;
no callset scoring, F1 calculation, case substitution or new native run occurred.
Range receipt lengths sum to 236,857 bytes, matching the manifest's transfer total.
This verifies cached decoded bodies against the packet, not remote transport afresh.
Reviewed sources.json SHA-256:
`a564e1591c51a49ebb25ab966792003e05d8f4470c0eb85282d36b1ffa8ea95b`.

| Source; full / filtered record counts | Independently observed fixed-case content | Accepted limit |
|---|---|---|
| Truth; 149 / 119 | SV_62 PASS, POS19196736, REF420 bases, ALT A, DEL419, GT0/1. Full END19197155; filtered END absent. | Sequence is supplied for truth. Missing filtered END does not erase the explicit allele. CN is missing. |
| Severus; 224 / 176 | PASS DEL, POS19196736, END19197155, length419, GT0/1, HP1, VAF0.44, DR27/DV21 in both. | Exact reported geometry and GT match. Positive SVLEN is caller representation; compare deletion magnitude. REF N/ALT<DEL> supplies no deleted sequence. |
| SVPG; 189 / 163 | INS130 at19196745; DEL191 at19196966, END19197157; both GT1/1 in both files. | These records do not explicitly report the 419-bp deletion. Proximity or combining sizes is not exact allele recovery. |
| miniSV; 186 / 168 | DEL195 at19196966, END19197160, GT1/1, with SEQ, in both files. | A different-sized candidate; not an explicit 419-bp deletion. SEQ alone does not identify it with SV_62. |
| nanomonsv; 1049 / 634 | No record with POS in the fixed window; independent interval/mate check also finds none. | Absence is qualified for these archived records and this window, not all native outputs or input evidence. |

My first interval-overlap check disagreed with miniSV's packet selection because
an INV at361341–35958957 spans the window. The packet uses POS selection; that
additional spanning INV has neither a deletion tag nor the named endpoints.
The explicit selection distinction resolves the check; no evidence was discarded
to manufacture a recovery result. No complex-allele inference follows from it.

## Line-item claim limits and investment consequence

| Claim boundary | Reviewer disposition |
|---|---|
| Whole archive and transport | sources.json records whole_archive_checksum_verified=false. October 4 ledger records a verified whole cache and six HG002 header-only checks, not earlier HG008 scoring. Main's reported fresh whole MD5/SHA and remote/member cross-check remain main evidence until a completed receipt is reviewed. I did not reread or download the whole archive. |
| Archive versus current native caller | Severus_v1.5 header date2025-10-22; SVPG date2025-11-24 without source/version. miniSV lacks version; nanomonsv names0.7.2. No current pinned execution, equal raw inputs or exact commands are independently certified. |
| Reference and exact allele | chr7/7 aliases and endpoint agreement do not verify reference bases. Severus's symbolic allele cannot prove sequence identity with truth; HP1 is a caller label, not independent phase validation. |
| Somatic and quantitative genotype | Publisher paired workflow and benchmark labels support source context. These VCFs do not independently prove matched-normal absence, purity, local CN or recurrent somatic origin. DR/DV and VAF are reported support, not independent biological validation. |
| Filtering and mechanism | `.filter` is a filename, not proof of subtraction, normal filtering or candidate stage. Presence in both versions establishes survival in those files only. SVPG/miniSV misses do not by themselves locate graph, alignment, clustering or paired-filter loss. |
| Graph/learned information and ascertainment | Graph allele identity, panel/sample membership and any pretraining exposure remain unresolved. One author-selected case and four-of-five misses supply no prevalence, generalization or equal-information superiority estimate. |

The source falsifier resolves the prior HOLD for **reported comparator detection**:
a strong caller in the published panel already emits the named deletion geometry
and GT. This rejects using this case as evidence that the reported 419-bp deletion
is generically unmet. It is a reproduction/control finding, not a new method result.
It does not resolve the stronger exact-sequence/native-mode question. Unknown
normal/CN/reference facts preserve that narrower uncertainty without creating novelty.

The completed mode note supplies interface information only: `svpg call` requires
sorted/indexed linear BAM, matching FASTA and GFA, separately for tumor and normal;
`graph-call` takes GAF. Tagged guided DEL fallback is source-supported, not executed
on this case. The note also reports v1.4.1 versus supplementary-v1.3 provenance
inconsistency and unresolved INV output support. I did not re-audit its source code.
There is no need to acquire BAM/GFA or run this control solely to decide investment
in generic detection of this already reported case. A separate useful question
would need its own evidence and comparative benefit before any release.

Complex INV remains conditional under the earlier limits. This DEL packet does not
prove an INV mechanism, validate its benchmark body, or establish SVPG INV support.
Only this addendum was written; original117 lines are retained byte-for-byte.
No historical edits, installs, downloads, jobs, Git actions or major positive result.

Path clarification, 13 October 2026: main supplied the correct archive index at
[svpg_archive_index_20261013/index.json](../../results/svpg_archive_index_20261013/index.json);
the earlier proposed case-directory index path was wrong. Main reports the completed
cache receipt at [cache_verification.json](../../results/svpg_named_case_20261013/cache_verification.json)
and added [case README](../../results/svpg_named_case_20261013/README.md), with sources.json unchanged.
These are supplied locations, not a further reviewer audit. Prior review is untouched.
