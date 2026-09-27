# Conditional next falsifier after the PAV and caller-source audits

**Date:** 2026-09-27. **Status:** research-direction triage, not a frozen
experiment protocol or method claim.

An Astra/medium internal decision review was *requested* to compare
candidate-recall ceilings, multi-truth/matcher evaluation, and targeted
breakpoint/genotype refinement. The runtime did not independently attest its
actual model or reasoning effort. Its recommendation was to test the
candidate-union recall question first, with truth/matcher sensitivity built
into that falsifier, and to defer refinement until a robust residual error is
shown. This is consistent with the earlier
[primary-source comparison](2026-09-23-research-pivots.md), but is a
feasibility judgment, not evidence of novelty or positive results.

## Data feasibility now

The NIST HG002 v5.0q GRCh37 SV VCF and paired BED are staged, but the 3-Mb
local read fixture has only 11 qualifying deletions and Manta produced no
candidate VCF. The [new source inventory](2026-09-27-hg002-precomputed-callsets.md)
finds six small historical Parliament2 caller outputs on hs37d5 and two HitSV
short-read output VCFs on GRCh38. Candidate VCF bodies, exact reference
sequences, and per-file run provenance were not checked in that inventory.
Parliament2's Manta header identifies `GenerateSVCandidates 1.4.0` and a
local `ref.fa` path with GRCh37 contig lengths; this supports the documented
historical caller version but does not prove FASTA sequence identity. The
Parliament2 Delly deletion VCF does not declare a reference sequence in its
header. No local or cluster scratch candidate VCF from the restart exists.

These resources permit a **small descriptive released-callset audit** after
header/reference checks. They do not yet provide a controlled contemporary
caller-candidate union: the Parliament2 tools are historical and their files
may be filtered outputs, while the checked HitSV repository supplies only one
caller per coverage level. Released-callset union recall must not be renamed
an internal candidate-generation ceiling. The 3.33-GB Zenodo `sv.gz` package
in the source inventory might contain newer multi-caller outputs, but its
members and per-caller provenance have not been inspected; it is not yet an
approved transfer.

## Highest-information next gate

Before fitting a model or transferring whole-genome reads, identify at least
two complementary, same-donor/same-reads/same-reference caller outputs with
frozen versions and preferably unfiltered emitted candidates. Verify VCF
headers, source reference sequence or dictionary, sample identity, depth,
candidate filtering status, and file checksums. If only the historical or
heterogeneous *final* VCFs are available, use them only for a bounded
representation/matcher smoke test and report that the candidate-generation
investment gate remains untested.

If a compatible panel is established, the proposed no-training falsifier is
truth-in-caller-union recall for autosomal DEL ≥50 bp within the paired v5.0q
benchmark BED, with a prespecified difficult-region mask, non-difficult
comparator, caller-level and union outputs, and two fixed matching approaches.
Compare v0.6 only on reconciled common territory, not as independent donor
replication. Report denominators, exclusions, matcher disagreements, and
locus/block-level uncertainty; an HG002-only result remains development
evidence. Do not infer confident negatives from a missing call or use the
HGSVC3 PAV inventory as a callability mask.

The Astra review proposed numerical stopping gates (at least 200 eligible
difficult-stratum DELs over 50 blocks; a 5% missing-fraction threshold;
adjudication of a fixed 30-locus sample; at least 50 stable misses before a
read-evidence pilot) and a 16-CPU-hour/32-GB/no-GPU planning cap. These are
**unfrozen proposals**, not literature-derived cutoffs or permissions to run.
First check denominator feasibility without outcome-driven selection, then
freeze the protocol and obtain independent Sol/high scientific review before
any substantial campaign. If no compatible panel exists, record that
feasibility failure and reconsider a bounded caller-generation plan or a
different direction; do not relaunch the same failed Manta job unchanged.

A publication-worthy claim would need a reproducible missing-allele mechanism
on unrelated donors, orthogonal allele validation, and a method or evaluation
advance beyond current caller unions, catalogs, and matcher-sensitive
leaderboards. A single HG002 audit, even if positive, is not that claim.

**2026-09-28 gate update:** The nine pinned Parliament2 VCF bytes passed a
Git-blob/SHA-256 header audit, but none carries sequence M5 provenance and
several have no contig/reference declaration. An independent reviewer found
the candidate-generation estimand untestable with these released outputs and
the proposed thresholds unjustified. The no-go and review gates are in
[`2026-09-28-parliament2-header-gate.md`](2026-09-28-parliament2-header-gate.md).
