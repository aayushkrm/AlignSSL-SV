# Fresh direction assessment and bounded ensemble-contract diagnostic

**Date:** 2026-09-30. **Status:** competing hypotheses and synthetic operational
evidence, not a selected method, biological improvement, or publication-ready
result. The renewed user objective explicitly permits leaving the prior SSL,
candidate-filtering, benchmark, and dataset choices. DeepSV remains historical
context only. Existing negatives and corrected artifacts are preserved.

## First-party source discovered

The [Guo et al. article](https://link.springer.com/article/10.1186/s13059-026-04219-3)
already studies short-read caller ensembles and graph-versus-linear alignment.
Its [supplementary dataset](https://zenodo.org/records/20410726) has eight
per-sample/alignment ZIPs, a graph BAM, and ensemble summary files. The ZIPs
are approximately 409–445 MB each; the graph BAM is 47,589,383,607 bytes.
Initial inspection was metadata-only. Subsequently **one** development ZIP,
`linear-NA12878.zip` (434,544,359 bytes), was downloaded outside Git and verified
against published MD5 `cef8268e5dc77d9881b35f90875151c0`. The graph BAM and the
other seven callset ZIPs were not downloaded. This is not a final-test dataset.

The dataset describes VCFs before and after benchmark processing. These are
not automatically internal candidate streams: the
[pinned Manta rule](https://github.com/yuliu-guo/SV-Benchmarking-Germline/blob/64b8aafc1b83a93c6718b577d8408c9b691dd60d/workflow/rules/callers/manta.smk)
copies `diploidSV.vcf.gz`, not `candidateSV.vcf.gz`. This distinction excludes
an internal candidate-generation ceiling claim from that Manta output alone.

The [source-code release](https://zenodo.org/records/21346400) resolves to
Git tree/commit `64b8aafc1b83a93c6718b577d8408c9b691dd60d` (`v1.0.0`). Its
configuration names four Platinum Pedigree samples and a local `hg38.fa`;
the local reference path is not sequence-identity evidence. The example
configuration names `NA12878_hq_v1.2.svs.bed` for its configured samples.
Actual per-run BED/reference use needs logs or manifests; the example alone
does not prove what every published run used. These related samples cannot
be counted as independent donor replication. NA12878 is already development
evidence in this repository.

### Completed outcome-blind source availability audit

Strict HTTP range inventories failed closed on both the API and public
download routes: HEAD supplied a Last-Modified value, but the 206 response
omitted that validator. The first 22-byte terminal probe was rejected before
its body was consumed. No failed range inventory was accepted as evidence.
The complete-download, published-checksum-verified alternative succeeded;
`unzip -t` also reported no compressed-data errors for all members.

`scripts/audit_verified_local_zip.py` records **103 members** and the headers
of all **14 pre-final caller VCFs**, with bounded header decompression and zero
biological records parsed. No released truth-derived performance summary was
opened or scored. The raw header audit and its checksum are under
`results/data_audits/guo_2026_linear_na12878/2026-09-30/`. Header declarations
alone are not evidence of populated or calibrated confidence values.

The headers declare `GT` in all 14 files and `GQ` in nine; one of those, SvABA,
declares GQ unsupported and always zero. No header declares `GP`. Sample names
include `2188`, `2188.v4.2.4.grc38`, `NA12878.bam` and `NA12878`; exact mappings
need run provenance, not automatic normalization. Reference declarations
such as `hg38.fa` and DRAGEN's `10` do not establish sequence identity. Released
discovery calls are not automatically forced genotypes over an independent
fixed catalog. Do not pool QUAL with GQ or infer missing calls as `0/0`.

The small SVUPP pipeline archive from record 17227287 is 118,468 bytes, matches
MD5 `72a522927785cdbe9a528d2202738f3a`, passes ZIP integrity testing, and has
95 members. Its inventory provides code/schema evidence, not genotype tables.
The newer [v0.0.2 record](https://zenodo.org/records/17569072) additionally lists
`SVUPP_paper.zip` (47,443,427 bytes; MD5
`5469337ca9249691b2b376ceb9b67e1d`). The older pipeline inventory must not be
used to claim assessment tables are unavailable.
Before inspection, the high-impact decision agent approved a bounded follow-up
of that **same release's** assessment archive: one CPU-hour, 4 GB memory, no GPU,
no follow-on acquisition; verify checksums and inspect metadata/schema only,
without scripts, GT comparisons or performance-table/plot inspection. This
scope is frozen in the independent decision note.

That follow-up **completed**: whole size/MD5 and ZIP integrity passed, SHA-256 is
`b15665743d28151bf2e9f656ae32dc8de9a3d6a5582c8033dbf251fec71daa2c`, and the
archive contains 26 members. Header-only inspection found a Platinum catalog
VCF and four genotyper VCFs (Sniffles2, kanpig, SVUPP and cuteSV2), all declaring
GQ, with the same seven pedigree sample IDs in **different column orders**.
Match samples by exact ID and validated allele identity, never column/row
position. Four headers declare PL; none declares GP. No GT body was parsed or
compared, and no performance table/plot was opened. Raw metadata and checksums:
`results/data_audits/svupp_2025/2026-09-30/assessment_header_audit.json`.

The README and inspected force-calling workflow explicitly use a supplied SV
catalog: Sniffles `--genotype-vcf`, cuteSV `-Ivcf`, and kanpig `gt --input`.
The workflow references a local no-ALT GRCh38 FASTA and a TR-excluded Platinum
catalog. These configured paths are not reference-sequence digests or actual
run manifests. The truth, Sniffles and kanpig headers carry a sawfish source
line; SVUPP carries a cuteSV source string different from its documented fork
tag. Do not infer actual caller versions or invalidate results from inherited
header metadata alone. Before scoring, establish **field lineage**: which
GT/GQ/PL values were recomputed, retained or replaced, and link each artifact to
the catalog, run/sample, executable/fork, modality and depth. Source reading
does not prove actual execution. No bundled script was executed.

The independent reviewer checked both saved report checksums and accepted only
the corrected availability/semantics checkpoint. This is a materially better
availability lead for conditional genotyping than discovery-only callsets,
but still one pedigree. It does not close unrelated-donor transfer, establish
a residual uncertainty mechanism, or prove novelty beyond SVUPP. Acquisition
expansion stops here; genotype scoring needs a further protocol review.

## Cheap diagnostic completed: what object does an ensemble score?

The [pinned exhaustive script](https://github.com/yuliu-guo/SV-Benchmarking-Germline/blob/64b8aafc1b83a93c6718b577d8408c9b691dd60d/workflow/scripts/exhaustive-search-ensemble.py)
uses truth-side `tp-base` representatives and separately clustered false
positives. Its four-field keys omit `END`; FP clustering uses adjacent start
positions; its consensus TP and FP counts use different support requirements.
This is a source-level observation about a retrospective object, not a claim
that all article results use that object or that an article conclusion fails.

`analysis/probe_ensemble_semantics.py` reproduces only those reviewed operations
on synthetic records. It verifies the fetched source's Git blob
`427f8db84aa1d110a2797ad975de131337fbbe7f` and SHA-256
`24756065868eee1cfc2fff58cd9c8b53f731387474062b3abf7c57723373344d`;
downloaded code is **never executed**. The raw diagnostic and checksum are in
`results/diagnostics/ensemble_semantics/2026-09-30/`.

The four counterexamples establish only operational distinctions:

- Two symbolic deletions with different `END` values share a four-field key.
- A 50-bp single-linkage start rule merges a three-record, mixed-type toy chain
  spanning 90 bp without testing allele equivalence.
- The retrospective output changes when the truth partition changes, even
  though the emitted input predictions are fixed.
- A one-vote FP is counted under an any-support rule but is absent from a
  two-vote consensus callset. The toy precisions are 0.5 and 1.0 respectively;
  these are **not real-data precision estimates** or evidence of optimism.

Six contract tests passed. No real VCF body, truth labels, released performance
CSV, or final-test outcome was scored. An oracle summary can legitimately
describe retrospective complementarity when labeled as such. The separate
[iterative merge script](https://github.com/yuliu-guo/SV-Benchmarking-Germline/blob/64b8aafc1b83a93c6718b577d8408c9b691dd60d/workflow/scripts/iterative-merge-ensemble.py)
does merge actual VCFs with SVDB and benchmark them, selecting additions by
truth-set metric. Do not extend the exhaustive-script distinction to every
method in the article. Deployment evidence would require freezing selection
and evaluating on genuinely separate data.

## Competing directions: decision still open

| Direction | Contribution that would be required | Immediate falsifier or gate |
|---|---|---|
| Another learned/SSL candidate filter | Useful held-out-donor/platform gain over modern trees, caller scores, and matched scratch controls | Existing repaired results do not justify scaling; modern-filter and transfer evidence must precede training |
| Discovery beyond contemporary caller pools | Orthogonally validated missing alleles and an actionable discovery mechanism, not another union | Obtain genuine emitted candidate-stage inputs; released Manta diploid calls do not satisfy this gate |
| Allele/representation-aware deployable ensemble evaluation | A consequential real-data gap between prospective label-blind outputs and retrospective oracle summaries, beyond existing matching/benchmark work | Freeze one label-blind merge and matcher, compare on development evidence with all exclusions; synthetic contracts alone are insufficient |
| Calibrated genotyping/abstention for complex alleles | Better uncertainty and useful genotype decisions under measurable donor/platform shift | Establish allele-resolved genotype truth and comparable native/modern genotyper baselines; preserve unrelated final donors |
| Targeted complex/repeat breakpoint or allele refinement | A robust residual mechanism not already solved by native callers or compatible local assembly | Small predeclared locus diagnostic with orthogonal allele validation; do not train on representation-only errors |

Independent literature, data-feasibility, and repository-evidence assessments
are being integrated before a high-impact direction decision. No large compute
campaign is authorized by these observations. A novelty claim, biological
effect size, precision improvement, or caller ranking remains unproven.

## Independent challenges to the new direction

The independent repository audit rechecked the corrected tables and history,
not just the old proposal. The uniform-benchmark pretraining advantage is a
fixed-threshold result: validation-selected F1 and AUPRC do not establish better
ranking. A real-candidate 1% pretraining/scratch contrast survives its declared
six-budget correction, but both arms remain below the hand-crafted control.
The corrected cross-population family has no Holm-significant result. These
facts reject scaling the existing SSL thesis without a different demonstrated
failure mechanism. They do not prove that representation learning is useless
for all structural-variant tasks. The separate table 23 quantile-matched
HG002/Tier1 arm must not be confused with the Manta-candidate arm in table 24.

The literature worker proposed confidence transfer/useful abstention as the
strongest *hypothesis to falsify*, not a validated novelty claim. Closest work
substantially raises the bar:

- [SVUPP](https://pmc.ncbi.nlm.nih.gov/articles/PMC12771361/) incorporates read
  phasing into genotype likelihoods and compares modern long-read genotypers.
  Full-text methods already compare error at GQ thresholds and equal numbers
  of GQ-ranked accepted calls across depths and platforms. Its principal
  accuracy scope excludes nearby SVs after reporting poor quality-ranked
  performance there. Seven truth-supported donors are pedigree relatives;
  six other trios supply a Mendelian-error proxy, not full genotype truth.
  Merely adding risk–coverage plots, another genotype model, or likelihoods is
  therefore not a new contribution. Same-donor platform comparisons alone
  would reproduce part of this work.
- [SVLearn](https://www.nature.com/articles/s41467-025-57756-z) already combines
  dual-reference features and supervised genotyping. Its released
  [datasets](https://zenodo.org/records/13309024) may enable a cheap input audit;
  released training data are not an untouched donor/platform test.
- [TRsv](https://doi.org/10.1186/s13059-025-03718-z),
  [FocalSV](https://doi.org/10.1101/gr.280282.124), and
  [Svirlpool](https://doi.org/10.1101/2025.11.03.686231) constrain repeat and
  local-assembly novelty. The last is a preprint, not peer-reviewed validation.
- The September 23, 2026
  [benchmark-framework study](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014824),
  [Aardvark](https://doi.org/10.1186/s13059-026-04165-0), and
  [ASVBM](https://doi.org/10.1016/j.csbj.2025.06.045) make a generic new matcher or
  metric-sensitivity thesis insufficient. A prospective decision consequence
  and residual error mechanism would have to be demonstrated.

The data worker independently verified that NA12878 is the mother of
NA12879, NA12881, and NA12882 in the
[Platinum pedigree](https://github.com/Platinum-Pedigree-Consortium/Platinum-Pedigree-Datasets#sample-meta-data).
The Zenodo caller package supplies benchmark outputs, not a new independent
truth source. Platinum v1.2's NA12878 truth/BED is a qualified development
resource, but using already inspected benchmark outcomes to choose a method
precludes calling that same donor untouched confirmation. HG005's small-variant
confidence regions do not establish SV negative territory.

A second bounded data-worker check found only **partial** SVLearn feasibility.
The [operational README](https://github.com/yangqimeng99/svlearn) describes hard
calls from precomputed features and a pretrained model, not a documented
per-locus GP/PL/GQ table. The paper uses 14 training donors and HG002 validation;
those training rows are not held-out predictions, and HG002 is not independent
confirmation. Its cohort-derived known-SV GT labels are not genome-wide
callable negative territory. The dataset manifest lists a 79,565,930-byte
validation archive and 342,612,215-byte training archive; the smallest listed
human model is 557,320,148 bytes. None was downloaded or executed. This does
not prove that probabilities cannot be obtained from the model; it leaves
out-of-training predictions, confidence interpretation and trusted catalog GT
eligibility unverified. A model download or raw BAM expansion is not the next
stage on this evidence.

The independent Sol/high-requested reviewer accepted only a narrow prospective
estimand: genotype reliability conditional on a predefined, independently
genotyped known-SV catalog. Eligibility must be fixed using truth confidence
and callability, independently of evaluated predictions. Trusted reference
genotypes may be included at those loci; a genome-wide absence label is not
required for this conditional task. Report accepted-GT coverage, error among
accepted GTs, and correct-GT yield over eligible donor/locus pairs. Missing
records and missing GTs remain no-calls, never inferred `0/0`. This is neither
candidate recall nor end-to-end discovery precision. Catalog provenance,
score semantics, unrelated donors and nonconfounded platforms remain gates.

Before a confidence experiment, distinguish site-level `QUAL` from genotype
`GQ`, likelihoods (`PL`/`GL`), and posterior probabilities (`GP`). A field name
alone does not guarantee a calibrated probability. A useful contribution would
need persistent, consequential reliability failures beyond simple calibration
on disjoint development labels, with the calibration-label budget counted and
an independently protected confirmation set. Stop or redirect if ordinary
calibration suffices, scores transfer already, or missing candidates—not GT
uncertainty—dominate the actionable failure.
SVUPP's existing quality-ranked evaluation makes *generic* abstention an
insufficient thesis. A transferable calibration or residual allele-neighborhood
mechanism must change a prospective decision beyond those existing comparisons;
no such mechanism has yet been demonstrated here.

The [independent high-impact decision and rigor review](2026-09-30-independent-direction-review.md)
prioritizes the **outcome-blind availability stage** for conditional genotype
confidence transfer, not a method or campaign. A no-fit donor-transfer
falsifier is conditional on interpretable confidence, trusted catalog GTs,
unrelated out-of-training predictions and a frozen protocol. If those inputs
are unavailable, stop this acquisition path; if ordinary calibration or
existing allele-equivalence safeguards explain a surviving failure, reject the
learned-uncertainty thesis. No architecture training is selected.

## Tool and operational evidence

Life Sciences Literature's bundled PubMed and PMC skills were read with their
source-presentation rules and called successfully. PMC resolved versioned
full-text URLs for `PMC13072666`; a targeted PubMed search for the Guo title
returned no hit, which is **not** evidence that the publisher article is absent.
The project Python 3.11 environment lacked `requests`; the system Python with
that dependency supplied the successful requests. Earlier restricted-network
failures were retried through the then-required approval mechanism.
For SVUPP, the PubMed lookup resolved PMID 41134129 and the PMC skill resolved
`PMC12771361`, its current CC BY metadata, and versioned full-text URLs. The
compact PubMed/Exa date disagreed with the PMC citation; use the latter's
2025-10-24 date, not the former's 2022 placeholder. An unsupported Entrez
cross-database request was rejected and replaced by the dedicated PMC skill.

Exa found the article/dataset lead; first-party Zenodo APIs and pinned GitHub
code supplied the load-bearing package/stage evidence. Scite returned its
monthly MCP limit (reset 2026-10-01 UTC); repeat calls were avoided. Firecrawl's
connected PDF scrape returned HTTP 404 for the tested publisher PDF URL; no
full-methods conclusion is inferred from that failure. Other plugins remain
available for suitable questions; usage is not a quota to call every tool.

The goal requests GPT-6.1 Sol/high orchestration, Luna/max independent workers,
Sol/max high-impact decisions, and Sol/high independent review. Dispatch
requests follow those roles; actual model/effort is not independently attested
by the exposed worker metadata. Internal agents were used, not new user-owned
chats. Agent handles missing after interruption were replaced only after an
authoritative `not_found` result; a timeout was not treated as completion.

A read-only cluster check on 2026-09-30 showed no jobs for `igorno`.
`/scratch/igorno-alignssl_restart_20260922` expires 2026-10-22 23:02:50
cluster-local, with one extension available. No job was cancelled or launched.

The existing-reviewer automation view rendered an app card but did not return
machine-readable configuration, and the expected local automation directory
was absent. No duplicate schedule or blind scheduler rewrite was created.
Current milestone reviews explicitly requested Sol6.1/high; the existing
schedule's model configuration remains unverified, not claimed updated.

## Reproduction and final integration

The three downloaded source archives are outside Git at
`/Users/akm/aayushkrm-AlignSSL/data/source_archives/`; their public URLs, byte
sizes, MD5s and computed SHA-256s are in the saved audit JSONs. No archive code
or container was executed. Rerun the verified-local-ZIP helper with those
manifest fields and exact `vcf_headers[].member` names, choosing a **new**
output path. The strict remote helper is retained with fail-closed tests; do
not reinterpret its rejected Range responses as accepted source evidence.

From the repository root, the successful combined declaration audit was:

```sh
../.venv/bin/python scripts/audit_vcf_confidence_fields.py \
  --header-audit-json results/data_audits/guo_2026_linear_na12878/2026-09-30/archive_header_audit.json \
  --header-audit-json results/data_audits/svupp_2025/2026-09-30/assessment_header_audit.json \
  --out results/data_audits/confidence_fields_2026-09-30.json
```

It contains 19 compact header-semantic reports, normalized-header and contig
hashes, exact sample IDs, declared fields and explicit interpretation limits;
**zero records** were read or scored. Its optional record-prefix mode is not a
genotype evaluator and was not used on these data. GP numeric shape and
Number=G cardinality are not posterior calibration; source prefixes are not
whole-file identity checks. The synthetic operational report is reproducible
with `analysis/probe_ensemble_semantics.py` and a new output directory.

Final integration: **418 tests passed, 29 skipped** in 127.83 s. The final
field-auditor targeted suite separately passed ten tests after the worker
finished. Manuscript/result consistency and diff whitespace checks passed,
as did all four archive-audit checksum sidecars and the synthetic-probe
sidecar. This closes code/input verification only, not a publication outcome.
