# Weller deletion-screen rigor: independent bounded review

2026-10-12, Asia/Tomsk. Maintained reviewer; requested GPT-6.1 Sol/high,
not independent backend/effort attestation. This is a new fitness-assay question.
HG002 stays stopped. Shred-seq/scCHyMErA scouts were not repeated. Swap-seq's
direct deletion-expression benchmark remains prior art, not an endpoint here.

**Decision: no costly study selected. Reject causal edit/dropout deconvolution
and biological false-negative calibration from Table S4 alone. One cheap
screen-level redundancy diagnostic is useful, with the restricted claim below.**

## Actual measurement and source checks

The screen tracks paired-guide abundance in HAP1, not RNA effects or confirmed
genotypes for every intended allele. Weller reports10,471 constructs around149
selected genes, two separately infected replicates, and D4-relative dropout.
The summary averages D11/D14/D21/D28. Essential coding deletions yield724/1003
hits; overlap-conditioned hits yield759/1115. The Discussion explicitly assumes
threefold tiling and independent pair efficiencies for its <3% expectation.
It also allows editing noise and true exon tolerance as explanations of misses.
Twenty-one viable deletions have PCR/Sanger support; seven of ten competition
tests depleted. Those validations retain their value within their tested scope.
[Primary Results, Discussion and Methods](https://www.biorxiv.org/content/10.1101/2025.11.03.686307v1.full).

Independently read only the1697-byte header of main's retained media-3.tsv:
13,221,638B file;136 fields/135 unique names. main_gene_essentiality occurs at
columns31/40 (zero-based30/39). Header SHA256:
`934248cf7625ee3f91ad601f8ab20a24ae4c940d197f8595d615f0dc87bd6d9a`.
No data rows were read or inventoried by this reviewer. The spreadsheet skill
kept column positions intact and prevented silent duplicate-name overwrite.

FULL-read the109-line inventory code and184-line result. Main's result reports
10,471 unique IDs, five missing L2FC values,1196 depleted/82 enriched known
outcomes, identical duplicate-column cells on all rows, and no known-row flag
disagreements. Its named positive-control/exonic subset is450 rows/336 depleted.
That subset is not the paper's1003-row essential-coding denominator. Neither
that difference nor150 literal gene_name values contradicts the published counts.
Missing outcomes are not zero; literal gene labels are not independent loci.

Static inspection plus eight reviewer-written in-memory controls pass: valid
duplicates/NA, conflicting aliases, nonfinite L2FC, duplicate ID, invalid flag,
ragged rows, missing required field, and strict threshold boundaries. This
qualifies those finite parser behaviors, not the complete author test suite,
every source row or source-origin checksum binding. No actual TSV reanalysis ran.

| Local evidence | Independently computed SHA256 |
|---|---|
| analysis/prime_deletion_table_inventory.py | `aff052e33a3fc2afa4ceb5307a5bf7f166d8ec4bbf7266cf72de6a0927c5001f` |
| results/prime_deletion_inventory_20261012/inventory.json | `795e6694618ef533d5bb75a6ac275d4af94b0aec43646a615e637785270963dc` |

The inventory records source SHA256
`6b622cef1e49c3eed46a1d5d039f145744ca0c1469f32f163b8cb94bdf3e2f0a`.
That whole-table hash is main evidence, not a new reviewer body-hash pass.
Data availability points to supplementary tables; the author code is
[PrimeDeletions](https://github.com/julianeweller/PrimeDeletions). Neither raw
sequencing nor model resources are needed to decide the present premise.

## Three questions and their limits

| Candidate | Legitimate endpoint and strong controls | Present disposition |
|---|---|---|
| Held-out-locus functional prediction | Predict measured guide dropout in new loci; compare CADD-SV, external gene essentiality plus coding/splice overlap, and design/count features | Eligible for a small assay-prediction check, not yet a publication question or allele-fitness benchmark |
| Editing-efficiency/dropout deconvolution | Separate the fraction correctly edited from the fitness of the resulting allele | Reject from this table alone: both are latent; trajectories and late BFP do not identify them |
| Tiling sensitivity/independence | Test whether multiple overlapping constructs add observable detection as an independence-based rule predicts | Accept one bounded redundancy diagnostic; reject calling its misses biological false negatives |

For prediction, random construct splits leak shared genes, guides and overlapping
regions. Hold out loci/connected overlap groups and prevent shared-guide leakage.
Use only verified external essentiality, not a gene summary derived from these
dropout labels. Compare within coding/noncoding strata so identifying essential
coding DNA cannot masquerade as learning noncoding fitness. CADD-SV is a useful
ranking control here, not an established calibrated HAP1 fitness predictor.
An improvement must transfer across held-out loci and exceed these simple controls
at a useful precision/coverage tradeoff. A leaderboard on one selected screen,
or a model that mainly reproduces gene essentiality, is insufficient motivation.

For deconvolution, repeated timepoints measure the same evolving mixtures.
Strong dropout can hide correctly edited cells that have disappeared. Flat
dropout can reflect failed editing or a tolerated allele. Guide-count trajectories
do not distinguish these alternatives without additional identifying evidence.
Methods put BFP integration after D21 in a surviving subset, with later selection
and sorting; the table's populated freq_BFP fields are not unbiased preselection
edit fractions. BFP labels also require their own sample crosswalk. A universal
sham requirement is unnecessary; the missing quantity is independent allele
formation/fitness evidence for the claimed separation, not another generic control.

## What the <3% argument does and does not establish

With three independent misses each of probability0.3, all three miss with
probability0.3^3=0.027. The calculation is correct under its premises. The paper
states independence as an assumption; it does not report measuring every
construct's editing failure. Essential-gene exons are not uniformly essential
alleles. A pooled hit fraction need not be the detection probability of each
truly consequential deletion, and three covering alleles need not share its effect.

Even conditionally independent failures can give a higher aggregate miss rate
when target-specific probabilities vary: E[q^3] is at least E[q]^3. As a logical
example, three perfectly shared failure events can each miss30% yet jointly
miss30%, not2.7%. These are analytic examples, not empirical Weller findings.
They identify missing premises; elementary dependence mathematics is not itself
a new methods contribution. The published68% overlap-conditioned hit rate does
not demonstrate independence, nor by itself demonstrate its violation.

Outcome dependence could arise from shared biological tolerance, guide quality,
counts or editing. Therefore correlated dropout alone cannot refute independent
editing efficiencies. It can challenge transporting marginal assay-hit rates into
a practical tiling detection rule. It cannot estimate the true <3% biological
false-negative rate. The selected21/10 validations do not supply a random,
independently known positive denominator for all regions either.

## One useful cheap discriminating check

Freeze coordinate-defined three-construct coverage groups before looking at hits.
Use one declared essential/exonic subgroup, explicitly separate from the unresolved
paper-denominator crosswalk. Resolve duplicate aliases and NA first. Reconstruct
each replicate's author-style average LFC and cutoff without pooling the replicates.
Compare the fraction of groups with no detected construct against a stratified
permutation reference that preserves marginal hits, design/count strata and each
construct's paired replicate trajectory. Separate groups with shared guide ends;
cluster uncertainty by locus, not by all possible overlapping pairs. This is one
table calculation, not a new model, assay framework or infrastructure campaign.

A persistent excess of group misses across both replicates would reject that
specific independence-based assay-detection approximation in the tested subgroup.
It would not identify editing dependence or biological false negatives. No excess
would support that narrow approximation, without proving biological sensitivity.
If the subgroup/coverage/metadata cannot be frozen, or the result disappears after
matching locus/design/count structure, close this candidate. Do not rescue it by
tuning cutoffs, substituting a different denominator or declaring exon misses truth.

Larger costs need a reproducible practical loss of detection from redundant designs
and an independent check or useful design correction beyond known assay caveats.
No clinical diagnosis endpoint is required. No expensive campaign is approved.

Audit: Firecrawl paper instructions and the spreadsheet skill's required references
were read. One known primary-page retrieval; selected complete load-bearing passages
read, not an exhaustive body/supplement/code audit. Main's initial NA parsing failures
remain history. Only this new owned note was written. No jobs, downloads of genomic
reads/models, installs, Git commands or historical edits occurred. No new biological
result, RNA benchmark, global null or publication-ready contribution is claimed.
