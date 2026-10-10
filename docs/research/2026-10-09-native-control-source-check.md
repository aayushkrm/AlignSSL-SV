# Native recovery controls: corrected prior art and documented traces

October 9 local / October 8 UTC. This is a source-only feasibility check.
It does not select a publication lead or approve an experiment.

## Findings

Svirlpool v3 adds annotated tandem-repeat intervals as candidate seeds,
then merges and extends candidate regions. It does not depend exclusively
on a strong indel signal to seed a known repeat locus. Local consensus
assembly, read-derived noise and sequence-aware joint calling are already
part of that method. A proposed repeat-rescue method must test against this
control rather than assume these features are absent.
[Primary methods, section 2.1.2](https://www.biorxiv.org/content/10.1101/2025.11.03.686231v3.full).

The publisher history identifies v3 as the most recent version, posted
June 29, 2026. Exa's January 1 indexed date is not accepted as its posting
date. The bioRxiv metadata request succeeded and returned three records;
its compact preview omitted version/date fields, so it does not independently
establish that date. The history page is the date evidence.
[Publisher history](https://www.biorxiv.org/content/10.1101/2025.11.03.686231v3.article-info).

Sawfish's guide documents discovery-stage `assembly.regions.bed`,
`candidate.sv.bcf` and `discover.settings.json`, and assembled-haplotype
`contig.alignment.bam` at both stages. These offer an upstream interface
for separating region selection, assembly and final calls. They are not
a record of every rejected signal or proof of causal candidate absence.
The guide warns that discovery internals are not fully documented or
intended for end users.
[Pinned official guide](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/docs/user_guide.md).

Svirlpool's pinned README requires indexed minimap2 BAM/CRAM with sequences
and qualities, an indexed reference, assembly error matrices and repeat
annotations. Its documented scope is ONT. This does not verify compatibility
with existing HiFi reads or installation on our cluster.
[Pinned official README](https://github.com/bihealth/svirlpool/blob/a60166dcc45702b7e874a8d96e2a1a4fd014e3ad/README.md).

## Consequence for this project

The earlier v1-based payoff framing must not be used to claim that all local
consensus callers miss loci lacking a strong alignment signal. Keep that
historical review; this newer source check qualifies it. Neither documented
traces nor a public container make a native experiment ready. Still needed:
verified executable versions, compatible inputs, candidate-stage semantics,
a decisive contrast beyond these controls, and a prospectively reviewed
finite experiment. No local installation or native run was tested here.

## Search and checked sources

- Exa skill: two named-tool searches, five requested result slots each.
  Ten requested slots are discovery results, not ten papers read. Aggregator
  and Context7 mirror hits were not used as primary evidence.
- Read the author repository README, v3 candidate-method passage and article
  history; read Sawfish input and discovery/debug-output guide sections.
  Initial guide extraction omitted the output section; a larger extraction
  supplied it. No claim of a complete paper, supplement or code audit.
- `git ls-remote` observed the two main commits shown in the pinned links.
  Direct capped HTTPS reads at those exact commits confirmed the cited
  Sawfish output section and Svirlpool input table. No repository was cloned.
- Life Sciences Literature bioRxiv skill issued one DOI details request
  using its provided REST script. HTTP200, three records, no raw saved.
  Checked DOI: `10.1101/2025.11.03.686231`. This is successful metadata
  resolution, not a separate methods or date reading.
- No genomic data, cluster access, installation, experiment, source policy
  change, reservation or historical-result edit occurred in this check.
