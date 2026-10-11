# Current kanpig calibration: important control, not a new research lead

2026-10-09. **New verified source evidence strengthens the prior-art boundary.**
Do not select beta-binomial read-support fitting, GQ correction or ordinary
calibration as this project's contribution. This note changes no outcome,
experiment, caller, budget or selected endpoint. Exact archive launch remains
HOLD because the maintained reviewer returned an account usage-limit error.

## Primary source scope and pins

Exa used two distinct searches,5 requested slots each, then one paired fetch.
Ten requested slots are not ten papers read. Duplicate Nature/PMC/preprint
and repository results were consolidated. The primary author repository was
used over library mirrors. Its official main-commit API reports
`9d2b86e25b37d9a571c0c30ab60fb5df1e7e321c`,2026-01-30, release/v2.0.2 merge.
All source URLs below pin that commit; no tool was installed or executed.

| Source actually inspected | Scope | Bytes / SHA256 |
|---|---|---|
| [Calibration guide](https://github.com/ACEnglish/kanpig/blob/9d2b86e25b37d9a571c0c30ab60fb5df1e7e321c/gqcalibration/README.md) | FULL guide |5,195 / `a4ed075be703b1102bd39595c2956caaba36b7446e11d12613f0e0ead2fa4f06` |
| [Germline genotyper](https://github.com/ACEnglish/kanpig/blob/9d2b86e25b37d9a571c0c30ab60fb5df1e7e321c/src/kplib/germ_genotyper.rs) | FULL source file |13,887 / `b3bdae10ccd72428adf054c8a7acdb6b5de696bc4c860abcc54740f52b6f3a90` |
| [Parameter estimator](https://github.com/ACEnglish/kanpig/blob/9d2b86e25b37d9a571c0c30ab60fb5df1e7e321c/gqcalibration/estimate_params.py) | Whole body fetched/hashed; read ONLY lines100–293,680–721,756–841 and function/match index. Not a full code audit. |29,060 / `a5cdaf07efeff1fc93f53640e75f4d0cd4bf859272690eade7ed39e85c8afa93` |

Life Sciences Literature's mandated PMC metadata script resolves the published
DOI to PMC11971316, PMID40185777, April4,2025; current metadata says open access,
CC BY-NC-ND, not retracted. This is identifier/license evidence, not a new full
paper reading. The search also returns PMC11526963 for an earlier preprint;
do not conflate it with the published record. No article body, supplements or
genomic/archive member was acquired in this follow-up.

## Existing functionality

The guide already describes fitting a beta-binomial genotype model to a
truth/query VCF, exporting a configuration, recalibrating GQs, and producing
held-out plots. It explicitly says useful default GTs need not imply useful
GQs and discusses experiment/depth dependence. The generated table includes
original and new GTs, correctness, depth, allele support, FT and KS. Thus
ordinary support-distribution fitting and confidence plots are existing
functionality, not a novel project method. This is documentation, not an
independent performance replication.
[Author guide](https://github.com/ACEnglish/kanpig/blob/9d2b86e25b37d9a571c0c30ab60fb5df1e7e321c/gqcalibration/README.md).

The inspected Rust defaults use Beta mode with genotype mixture fractions,
means and precisions, then choose the highest scoring state. A supplied
configuration can change those scores and GTs; its calibration table then
maps the GQ by piecewise linear interpolation. Parameter fitting is therefore
not interchangeable with a monotone map on FIXED genotypes. It may change
what a fixed-output selection ceiling bounds.
[Pinned genotyper](https://github.com/ACEnglish/kanpig/blob/9d2b86e25b37d9a571c0c30ab60fb5df1e7e321c/src/kplib/germ_genotyper.rs).

## Score meaning: a ratio is not posterior error

For three normalized model probabilities ordered p1≥p2≥p3, the inspected
raw GQ is `-10 log10(p2/p1)`, capped at1000. It is NOT
`-10 log10(1-p1)`. This follows directly from the source's top-two normalized
log-probability difference. Conditional on this three-state model and ignoring
the cap, q20 means r=p2/p1=.01, so model error `(p2+p3)` can range from
`r/(1+r)` to `2r/(1+2r)`, approximately0.99% to1.96%. That is a mathematical
example, not observed error or an empirical1% guarantee. A calibrated table
changes the interpretation further.
[Score implementation](https://github.com/ACEnglish/kanpig/blob/9d2b86e25b37d9a571c0c30ab60fb5df1e7e321c/src/kplib/germ_genotyper.rs).

## Static cautions, not executed bug results

In the inspected estimator, `--leaveout` samples records within Ogt groups,
not locus/family/technology blocks. That cannot substitute for this project's
transfer split. There is also a documentation/code discrepancy: `--all` says
include incorrect GTs, but the corresponding `all_gts` branch filters to
`state` true. Calibration bins use `nGQ` with original `state`, although
re-genotyping also produces `nState`. These are source-level concerns, not
proof of observed harm, an author-benchmark reanalysis or defects in every
release. No calibration script, Rust binding or real genotype was run here.
Do not execute or silently repair the script as part of the inventory.
[Exact inspected sections](https://github.com/ACEnglish/kanpig/blob/9d2b86e25b37d9a571c0c30ab60fb5df1e7e321c/gqcalibration/estimate_params.py).

## Consequence for the selected development measurement

1. Establish the exact version and score semantics of the archive's outputs.
   Today's author code does not attest the version of released VCFs.
2. A finite ceiling on old fixed outputs can reject investment on those
   outputs. An apparent gap cannot establish improvement over a current
   genotyper or justify a paper about fixing an old GQ implementation.
3. Keep fixed-output selection separate from parameter refitting that changes
   GTs. Never use the former ceiling to claim a bound on a new genotyper.
4. Any later method proposal must confront native v2 fitting/calibration and
   support/neighbor controls, with source-only tuning and grouped tests.
   Generic probability recalibration or replacing binomial support with a
   beta-binomial model is particularly weak prior-art overlap.

This is a stricter interpretation boundary, not an endpoint change or a new
campaign. The selected1%/10-point value measurement, finite archive route,
close-on-insufficient-input rule and historical charges remain unchanged.
No future native rerun or larger data acquisition follows from this note.

The paired Exa fetch also exposed the first3000 characters of GATK-SV's
ScoreGenotypes guide: learned multi-feature genotype filtering and rescaled
GQ are not unique in SV workflows. That was a PREFIX reading only; no complete
pipeline or latest commit audit was done, and no long-read equivalence is
claimed. It is a further caution against broad novelty, not a selected control
or empirical result.
[Official guide](https://github.com/broadinstitute/gatk-sv/blob/master/website/docs/modules/score_genotypes.md).

Publication potential and meaningful method/biological improvement remain
unestablished. The next executable action is still the independently reviewed
metadata inventory, not calibration fitting or training.
