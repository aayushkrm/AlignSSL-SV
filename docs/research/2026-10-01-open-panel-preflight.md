# Competing directions and a bounded complex-locus availability gate

Date: October 1, 2026. This is an availability decision, not a selected
publication thesis, outcome analysis or positive biological result.

## Objective and decision

The updated objective explicitly permits abandoning SSL and the old benchmark,
and excludes DeepSV as the foundation of new work. It also names Exa,
Firecrawl, Parallel Search, TinyFish, Scite, Hugging Face, Context7, GitHub and
Life Sciences Literature. Use them by evidence need, with alternatives when a
route fails; there is no scientific value in a plugin usage quota.

| Direction | Importance if supported | Present falsification/data constraint | Current decision |
|---|---|---|---|
| Candidate-generation recall in difficult SV regions | Recover genuine misses rather than merely filter existing candidates | Modern, versioned candidate populations and donor-callability/reference compatibility are unresolved in the inspected holdings | Keep open; no further identical Manta submission or bulk cohort transfer |
| Read phasing / block-aware genotype uncertainty | Protect genotype decisions from arbitrary phase labels or inconsistent phase blocks | The endpoint counterexample is synthetic. No read-probability, informative-SNP or QUILT RData payload was found in the acquired SVUPP archives. Regeneration inputs are not staged. Absence of block marginalization in four reviewed descriptions is not a novelty proof | Preserve software evidence; reject the endpoint bug as the biological lead under the current budget |
| Diagnosing an absent structural haplotype in a complex-locus panel | Avoid confidently choosing among wrong available alleles; potentially identify when additional sequence evidence is needed | Locityper already studies panel representativeness and exposes multiple native controls. Structural absence, rather than ordinary nucleotide divergence, needs independent labels | One small availability check only; no new detector, training or outcome analysis approved |

The high-impact decision agent (Sagan, requested `gpt-6.1-sol/max`) and
independent reviewer (Averroes, requested `gpt-6.1-sol/high`) separately approved
the narrow stage below. Exact execution model/effort metadata is not attested.
The coding worker was requested as `gpt-6-luna/max`. These are internal
subagents, not new user-owned chats.

## Primary-source challenge to novelty

[Locityper, Nature Genetics](https://www.nature.com/articles/s41588-025-02362-4)
explicitly identifies the limitation of choosing from existing panel
haplotypes, evaluates leave-one-out panel representativeness, and provides
native confidence/adequacy controls. A generic GQ calibration result, or
rediscovery that a missing allele harms a closed-panel caller, is not a
sufficient contribution. The published method is not a strawman GQ-only
baseline: `quality`, `unexpl_reads`, `weight_dist` and `warnings` all need
consideration, with `total_reads` for the count denominator.

The published article is DOI `10.1038/s41588-025-02362-4`, PMID `41107551`,
PMCID `PMC12597825`. Life Sciences Literature verified publication metadata
and open-access status; the canonical PMC article supplied full methods after
a text-file retrieval failed. PMID `39990346` is the earlier preprint of the
same study, not independent support. Exa supplied recent primary-paper leads;
GitHub supplied pinned source/version evidence. Discovery snippets and article
metadata alone were not treated as method evidence.

Pinned official source for the released benchmark's declared **v0.17.3**:

- Annotated tag object `9baffe0f31d4eff43c8607dcb318bbdd8411f8e6` resolves
  to commit `146cfd42e9179bafd63d1f41db7fc449940989de`.
- `src/solvers/scheme.rs`, blob `ef0d67ed0bfb483eaaa5ae4908354fcb17e127e3`:
  lines 412–415 normalize among considered genotypes before calculating
  `quality`; lines 529–537 check the normalized best-genotype probability.
  Lines 611–624 count reads whose best likelihood at the selected genotype
  falls below their best available-panel likelihood plus a penalty. This is
  not an independent likelihood for an unknown missing allele.
- `src/model/locs.rs`, blob `4e7896bde97c875f778a1d4702aedf25e170468f`:
  the load contract at lines 744–746 retains alignments conditional on an
  acceptable edit distance and inner-region overlap at some panel contig.
  Prediction summaries alone cannot reconstruct all upstream read evidence.

Sources: [v0.17.3 solver](https://github.com/tprodanov/locityper/blob/146cfd42e9179bafd63d1f41db7fc449940989de/src/solvers/scheme.rs),
[v0.17.3 alignment model](https://github.com/tprodanov/locityper/blob/146cfd42e9179bafd63d1f41db7fc449940989de/src/model/locs.rs).
The paper says v0.18.0; current main and stale available-data documentation
must not silently substitute for the released benchmark's version. Relevant
solver content also has the same blob at v0.18.0, but whole run/container
identity is not established by that equality.

## Frozen inventory/schema stage

First-party [Zenodo record 15879519](https://zenodo.org/records/15879519),
version DOI `10.5281/zenodo.15879519`, July 14, 2025, is the resolved version
of the paper's concept record. Its README declares v0.17.3 HPRC full-panel
and leave-one-out benchmarking. Each sample/locus has two haplotype
evaluation rows and one genotype row: these are not three independent units.
`qv` is assembly-comparison accuracy, not native `quality` confidence.
`avail_*` describes similarity to remaining panel haplotypes/genotypes; LOO
alone does not imply that the true sequence is absent, because another donor
can have an identical representative.

Approved acquisition is exactly `locityper-benchmarking.tar.gz`:

- Expected compressed size: **14,709,179 bytes**.
- Publisher MD5: **`10e629a4793e3ef6fe7bb6796417a77b`**.
- Endpoint: `https://zenodo.org/api/records/15879519/files/locityper-benchmarking.tar.gz/content`.
- Storage outside Git: `data/source_archives/locityper-15879519-benchmarking.tar.gz`
  beneath the parent project workspace.
- Budget: one CPU-hour, 4 GB memory, at most 1,000 TAR members and 250 MiB
  aggregate decompressed bytes (including metadata and inspected nested gzip
  output); at most 64 KiB retained headers. No archive extraction, bundled
  script execution, outcome parsing, model fitting or recursively opened
  archives. Only requested regular CSV/TSV headers and one nested CSV gzip
  layer are permitted. Complete integrity claims require draining the checked
  streams within the bounds.

Execution order is inventory first, then freeze an explicit member allowlist
before any table-header inspection. Reports must distinguish acquisition
identity, outer gzip/TAR integrity, inspected nested-stream integrity and
schema compatibility. Partial or budget-limited inspection is not a general
integrity PASS. Streaming body bytes for integrity does not permit parsing,
retaining or printing their records.

No database TAR, 1KGP genotype CSV, background archive, raw reads, reference or
additional cohort is approved by this decision. Headers cannot establish
populated fields, unique keys, successful joins or valid truth.

## Subsequent gate, not automatic permission

Require version-linked prediction identifiers; documented sample/locus,
panel-mode and platform/evaluation-unit keys; all native channels and their
denominator; individual prediction representation; and independent,
confidence-qualified assembly truth capable of labeling **structural** panel
absence. Donor/panel-exclusion and locus-family identities must support
separate holdouts. Merely finding disconnected field names or aggregate QV
tables is insufficient.

If any required evidence is missing, stop this dataset path and redirect the
scientific search; do not acquire larger archives to rescue it automatically.
If compatible declarations exist, freeze a separate protocol and obtain a
new independent review before reading outcomes. The first proposed falsifier
is whether frozen, version-compatible **combined native controls** already
detect consequential structural panel inadequacy while retaining useful
represented-allele calls. Compare ordinary fit/calibration controls before
proposing a detector. If they suffice, reject that detector thesis. A failure
must be linked to independently established panel absence and recoverable
read evidence before implementation. No outcome test is approved here.

## Execution checkpoint

The single approved archive was downloaded with a 14,709,179-byte transfer
limit on October 1 UTC. Whole-file identities, bounded integrity, member
inventory and header findings will be recorded below after scanner review.
No outcome rows have been parsed or scored by this research stage.

Independent whole-file checks before traversal matched the expected size and
MD5 above. SHA-256 is
`fd0e8ab023d8173c1cacf7627f07f7cacc62bcea5a2ab5f171d096bcc090312f`;
this is an additional local identity, not independent publisher
authentication. The release README's downloaded bytes also matched publisher
MD5 `12027cd715e3423cdf0b08b0ab164fc9`. No source script was executed.
A fresh read-only cluster check showed no queued/running account jobs;
scratch expiry remains October 22 at 23:02:50 cluster-local, with one
extension available. No cancellation or cluster submission was made.

The independent reviewer additionally checked the stage document and pinned
GitHub provenance: no scope-blocking finding, but no scanner/run approval was
implied. The reviewer requested the explicit inventory-first allowlist and
separate integrity/schema statuses above. The v0.18.0 alignment-model blob
differs from v0.17.3 despite solver equality; version compatibility remains
bounded to the inspected source components, not a historical executable.
