# AlignSSL-SV

This repository supports research on structural-variant (SV) calling and
genotyping. The goal is to identify and test an important, rigorous research
question. Compare directions. Use small falsification checks before expensive
experiments. Self-supervised learning (SSL) is optional. DeepSV is historical
context only. It is not the foundation for new work.

## Verified and planned

Latest review (2026-11-05 UTC): a case-only change to BND mate-contig names in
one public COLO829 file changes native comparator output. The independent
[review](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-11-06-independent-interop-review.md)
found the SnpEff producer behavior was reported years ago and recommends
stopping this as a publication lead. The altered file also has stale `ANN`
allele strings. Keep the work as a bounded regression case; it does not
establish a biological error or a publication result.

Current feasibility work compares published DNA sample lists with 60 public
direct-RNA sample names. The union of three DNA sources covers 58 names; 24
are in two long-read DNA metadata sets, and 56 occur in the header of an older
short-read genotype VCF. A public transcript-count file's header contains all
60 RNA names. These are name matches, not verified SV genotypes or RNA effects.
Close prior work already covers SVs and expression, splicing and phased
isoforms, so novelty remains unproven. See the [source check](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-11-04-paired-dna-rna-feasibility.md).

Recent clinical papers already use insertion sequence with SpliceAI; a generic
mobile-element splice prediction method is not a new contribution. See the
[prior-art check](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-11-04-mei-prior-art-check.md).

Latest source diagnostic (2026-11-03): the saved CNP0002230 metadata reconcile
231 samples, 292 experiments, 319 runs and 638 read-file links. No raw reads
were downloaded. This establishes archive membership, not a resolved
chromosome-path, dosage or quantitative fitness dataset. No usable matched
contrast or publication direction is established. Retrospective fitness
inference is parked pending specific missing evidence.
See [the archive crosswalk](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-11-03-synvii-archive-crosswalk.md).

Completed diagnostic (2026-10-16): the all-53-row Tier2 geometry screen completed.
It retained 15,460 observed read-name groups, including 4,170 UNKNOWN groups.
Native output contains 21 Chimeric breakpoint labels and no Foldback labels;
17 Chimeric labels occur in SA-consistent observed groups. Independent review
accepts the accounting. These labels do not establish artifacts, true inversion
support or a filter error. No follow-up campaign is released.
See [the complete screen](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/results/tier2_geometry_screen_20261014/README.md)
and [the result review](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-16-tier2-result-review.md).

Current decision (2026-10-14): stop the selected simple-inversion case as a
new-method lead. The complete regional input census has 52 alignment records
from 47 read-name labels and passed independent review. It contains useful
linked alignment patterns, but the proposed next positive would demonstrate
existing allele-genotyping, read-linkage or local-assembly capabilities.
No distinct contribution is established, so no further case compute is
allocated. This does not show biological absence or native caller success.
See [the actual census](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/results/inv_mapped_trace_20261014/README.md)
and [the investment decision](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-14-inversion-post-trace-investment.md).

Earlier decision (2026-10-12): stop the HG002 annotation-exclusion pilot before
genome-wide calling. Its best possible positive could reflect ordinary
annotation incompleteness. An important external claim or diagnostic decision
tested by that endpoint has not been established. This is a scientific
investment stop, not a biological null.

The complete HG002 DNA read input passed extraction and custody review:
5,359,077 original read identities and 80,344,827,828 bases. Full input data
were preserved in permanent cluster storage, outside Git. Their full integrity
has not been rechecked since the October scratch expiry.
No new calling, assembly or RNA campaign is released.
New research questions are being compared; no publication result
is claimed. See [the decision](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-11-hg002-calling-release-decision.md)
and [the input result](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-11-hg002-source-readset-result.md).

Earlier checkpoints:

Completed engineering diagnostics (2026-10-08): 20 native controls passed; all
11,490 unchanged rows are metadata-compatible. 41 REF controls passed; all
11,490 anchored REF spans agree. Source and row-order pins remained stable.

Earlier input check (2026-10-09): 44 cluster controls passed. The bounded
SVUPP provenance/header check and its complete raw evidence passed independent
review. The archive route is closed: the required ONT-to-HiFi caller views
were not sufficiently established. No genotype outcome was scored. This is
an input-readiness stop, not a biological null result. Competing research
directions are under review.

These checks do not validate the truth denominator, ALT alleles, phase,
callability, or scoring. Caller preparation follows a fixed reviewed process.
Check the current progress record for its status. No novel method, publication
lead, or performance claim is established. Keep null and failed results in the
record. A passing engineering check is not a biological result.

## Use this repository

- [Research index](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/README.md) lists research notes and reviews.
- [Restart state](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/RESTART_STATE.md) records current checks and open gates.
- [PROGRESS](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/PROGRESS.md) is the authoritative progress log.
- Technical records: [native controls](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-08-native-throughput-result.md),
  [REF controls](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-08-reference-throughput-result.md), [metadata census](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-08-metadata-census-result.md), and
  [caller preparation review](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-08-caller-preparation-review.md).
- Earlier input decision: [provenance result](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-09-svupp-provenance-header-result01.md) and
  [independent review](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-09-svupp-provenance-header-review.md).
- [results/](results/) contains earlier SSL benchmarks and technical audit
  outputs. Use the research notes to interpret them.
- [Archived README](docs/archive/README-legacy-ssl.md) preserves the former
  results page.

The progress and research-note links above point to the research branch
research/genotype-confidence-contracts-20261001 because default main may not
contain those records. Historical results and the archived README use
repository-relative paths.
