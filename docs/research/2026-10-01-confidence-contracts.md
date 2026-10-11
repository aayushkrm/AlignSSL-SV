# Confidence contracts: source-level diagnostic, not biological performance

Initial inspection: October 1 local / September 30 UTC. The producer follow-up
was completed October 1 UTC; its append-only report remains in the diagnostic
directory named for the initial inspection. This follows the fresh direction
comparison, not a return to SSL or DeepSV. No expensive experiment, new cohort,
genotype truth comparison or publication-ready result is approved here.

## Why this diagnostic

The preceding header audit cannot establish populated fields or shared
confidence semantics. In particular, a genotype-likelihood gap is not the
posterior probability that a genotype is incorrect. SVUPP already studies
GQ-ranked selection across depths/platforms, so a generic confidence benchmark
does not establish novelty. A small source-contract falsifier is cheaper than
starting a calibration or training campaign.

## Verified SVUPP fork contract

The documented cuteSV fork tag `v0.0.2` resolves to commit
`eb3d79de3b87ad823552f1156627c79de61d587c` in `Zilong-Li/cuteSV`.
The [genotyping function](https://github.com/Zilong-Li/cuteSV/blob/eb3d79de3b87ad823552f1156627c79de61d587c/src/cuteSV/cuteSV_genotype.py#L43)
marginalizes both heterozygous phase assignments with equal weight. For each
read, however, its probability lookup uses truthiness: an exact zero falls
back to 0.5, while an exact one is retained. The
[input parser](https://github.com/Zilong-Li/cuteSV/blob/eb3d79de3b87ad823552f1156627c79de61d587c/src/cuteSV/cuteSV_forcecalling.py#L680)
accepts endpoints without clipping; a text row `read_name 1 2` produces exactly
zero. The force-calling entry point routes this dictionary through
`force_calling_chrom` and `assign_gt_fc` to `cal_PGL`.

With six reference-supporting reads assigned probability one and one
alternate-supporting read assigned probability zero, the independently
implemented likelihood formula gives:

| Lookup contract | Original haplotype labels | All labels swapped |
|---|---|---|
| Zero treated as missing | GT `0/1`, GQ 14 | GT `0/0`, GQ 3 |
| Zero retained as probability | GT `0/1`, GQ 17 | GT `0/1`, GQ 17 |

Haplotype labels are arbitrary; swapping them should preserve a marginalized,
unphased diploid genotype distribution. The first row violates that symmetry
in the modeled contract. This is an **operational counterexample**, not a
measured genotype error or an allegation about the paper's conclusions.
The second row is a counterfactual missing-value interpretation, not a deployed
caller repair or improved biological result.

The diagnostic also retains interior-probability (0.99/0.01), missing-value and
unphased-0.5 controls: all preserve label symmetry. Eleven tests cover the
counterexample, those controls, a 36-pair endpoint/interior/missing grid for
the counterfactual interpretation, and invalid inputs. Independent review
requested stricter absolute tolerances and analytic anchors; the retained suite
now has thirteen tests, including a separately calculated endpoint posterior
and missing-equals-0.5 equivalence. The error probability
is 0.01 and the genotype prior is uniform, matching this pinned function.
Output PL tail flooring at `9e-9`, integer rounding and GQ cap 100 are modeled;
the report separately retains the pre-floor posterior. A naive PL-to-posterior
conversion could therefore manufacture a discrepancy at high confidence.

Reproduce (choose a new output path; existing reports are never overwritten):

```sh
../.venv/bin/python analysis/probe_phasing_label_symmetry.py \
  --verify-sources --out /tmp/phasing-contract-new.json
../.venv/bin/python -m pytest tests/test_phasing_label_symmetry.py -q
```

The initial bounded source verification reads three files, checks their Git blob IDs,
and records SHA-256 identities. It never imports or executes downloaded code.
The raw synthetic report and checksum are in
`results/diagnostics/phasing_label_symmetry/2026-09-30/`.
Actual executable revision, upstream endpoint frequency and biological
consequences in the published assessment remain unverified. The source wrapper
was additionally pinned at current SVUPP commit
`ca953fd54e3df76abfa07a5c8160398d301c7445`: its
[QUILT2 module](https://github.com/Zilong-Li/SVUPP/blob/ca953fd54e3df76abfa07a5c8160398d301c7445/modules/quilt2/phasing/main.nf#L35)
(blob `a972a45f62ec788102f477df0662552a36c3ae3f`) copies
`final_read_labels_prob` to text without clipping. Its
[README](https://github.com/Zilong-Li/SVUPP/blob/ca953fd54e3df76abfa07a5c8160398d301c7445/README.org#L183)
(blob `ecd8213732fb3dfd741e6dfa2a695f7e119feb8a`) accepts externally prepared
labels but calls direct WhatsHap support future work. It does not establish a
native hard-phasing mode or real endpoint frequency. This current commit is
not proof of the archived assessment run's revision.

### QUILT2 producer bridge (synthetic arithmetic only)

The exact QUILT tag `2.0.3` resolves to commit
`30a14b0326979be69c6310e736d4853e9119b30d`. Its
[read confidence function](https://github.com/rwdavies/QUILT/blob/30a14b0326979be69c6310e736d4853e9119b30d/QUILT/R/functions.R#L1615)
computes `p1/(p1+p2)`, replaces NaN with 0.5, and folds values below 0.5.
That output route explicitly sets `rescale_eMatRead_t=FALSE`; the
[emission routine](https://github.com/rwdavies/QUILT/blob/30a14b0326979be69c6310e736d4853e9119b30d/QUILT/src/copied-from-stitch.cpp#L165)
only applies its likelihood-ratio cap when that flag is true. The final
confidence is copied into `final_read_labels_prob`, then
[saved to RData](https://github.com/rwdavies/QUILT/blob/30a14b0326979be69c6310e736d4853e9119b30d/QUILT/R/quilt.R#L1041).

Six illustrative BQ30 SNP emissions favoring one hard haplotype over the
opposite have likelihoods `0.999^6` and `(0.001/3)^6`. Both are nonzero, but
binary64 division `favored/(favored+other)` rounds to exactly one. A haplotype-2
parser then computes zero. This is a constructed source-formula input, not
an observed QUILT read, an executed QUILT/R pipeline or proof of a particular
historical run. It rules out assuming the output likelihood-ratio cap forbids
endpoints; it does not measure their frequency or genotype effect.

The append-only `producer_bridge.json` records this additional synthetic
fixture and verifies six source blobs (the original three plus three QUILT
files), capped at 150 KB each. The original `probe.json` is preserved unchanged.
Fourteen targeted tests pass. A worker hit its usage limit before completing
this bridge; the main agent performed the bounded check instead. The reviewer
then independently checked pinned sources, reran fourteen tests and accepted
**conditional source-supported endpoint reachability**, not real occurrence.
It requested testing the opposite raw ratio and the producer's folding branch;
both are now retained in the test and append-only `producer_fold.json`.
The six SNP emissions per constructed read are distinct from the downstream
six-reference/one-alternate SV-read fixture. Exact hard haplotype alleles and
the non-rescaled diploid branch are assumptions, not observed biological inputs.

The reviewer also caught a version boundary: the current wrapper names a QUILT
**2.0.4 container**, while the initial producer audit used source tag 2.0.3.
Tag `2.0.4` resolves to commit `05056767c64d1f1405c7cbccd4eaec41a45bc9cb`.
Main-agent source retrieval subsequently verified that **the entire two
load-bearing files** `QUILT/R/functions.R` and
`QUILT/src/copied-from-stitch.cpp` have identical Git blob IDs/content in both
tags. The final report verifies those two additional pinned source identities,
eight total. This closes a difference in these source functions, not container
binary identity, historical assessment provenance or real endpoint frequency.

## Other caller field lineage: bounded independent source review

A Luna/max-requested worker inspected two release paths, without opening VCF
bodies or truth rows. These are source-level expectations, not proof that
every published record was produced by that exact executable.

- Sniffles2 `v2.3.3`, commit `97fb29bad3a1a8b7973fb532badd19ca1e290711`:
  `--genotype-vcf` uses the first eight input columns as a catalog and
  recomputes sample GT/GQ/DR/DV. Its GQ is the best-versus-runner-up
  likelihood gap, capped at 60, not posterior error. Its output FORMAT is
  `GT:GQ:DR:DV`; retained input headers can still declare PL and a Sawfish
  source line. An unused PL declaration is not evidence of a populated PL
  field. See [genotyping](https://github.com/fritzsedlazeck/Sniffles/blob/97fb29bad3a1a8b7973fb532badd19ca1e290711/src/sniffles/postprocessing.py#L338)
  and [output/header rewrite](https://github.com/fritzsedlazeck/Sniffles/blob/97fb29bad3a1a8b7973fb532badd19ca1e290711/src/sniffles/vcf.py#L321).
- kanpig `v1.0.2`, commit `aca6d12e60af812b42d562c0c0152027ab48fd1d`:
  incoming sample fields are cleared and rebuilt. GQ is a coverage-model
  best-versus-second score gap capped at 100; path scores are separate KS
  values. GT can derive from the path while the coverage model disagrees,
  which is separately flagged. It emits no PL field/definition while retaining
  non-FORMAT source metadata. See [metrics](https://github.com/ACEnglish/kanpig/blob/aca6d12e60af812b42d562c0c0152027ab48fd1d/src/kplib/metrics.rs#L130),
  [annotation](https://github.com/ACEnglish/kanpig/blob/aca6d12e60af812b42d562c0c0152027ab48fd1d/src/kplib/annotator.rs#L203),
  and [writer](https://github.com/ACEnglish/kanpig/blob/aca6d12e60af812b42d562c0c0152027ab48fd1d/src/kplib/vcfwriter.rs#L29).

An unmatched Sniffles catalog site with positive coverage can emit `0/0`, GQ 0;
zero coverage emits `./.`, and unscheduled/unset-coverage cases may have no
result. Kanpig distinguishes no-path positive-coverage reference calls from
zero-coverage no-calls. These source distinctions reinforce the existing rule:
omitted rows and missing GTs never automatically become supported reference GTs.
They do not establish per-donor truth confidence or callability.

## Scientific disposition and next gate

The Sol6.1/high-requested reviewer independently read the diagnostic, reran
the original eleven tests, and compared the saved report with a fresh in-memory
calculation. It found no blocking mathematical error and accepted the narrow
synthetic scope, not a full caller reproduction. It explicitly required
producer endpoint/serialization rules and assessment executable provenance
before any published-result relevance claim. The two test-strengthening
requests above were implemented; thirteen tests passed before the producer
bridge's additional test. The full suite after adding the producer test passed
432 tests with 29 skips; the latest fourteen-test target and the 30-test related
diagnostic target also pass after the folding assertions. Manuscript
consistency and saved-report checksum checks passed. No historical results
were altered.

No caller confidence fields are pooled as a shared error-probability scale.
The existing seven-person pedigree is development material, not unrelated
transfer evidence. Source coherence/interop alone is not a scientific mechanism.
The current narrow lead requires checking whether a documented upstream phase
generator actually produces endpoints on the routed execution path. Source
arithmetic now admits endpoints in the reviewed QUILT2 source functions shared
by tags 2.0.3/2.0.4, but frequency is unmeasured.
If the real producer/run excludes them, or the assessment used a different
executable, the published-result relevance claim stops there; preserve the
counterexample as an input-contract finding.

Only a source-verified, consequential residual mechanism could motivate a
frozen biological counterfactual on independently sourced high-confidence GTs,
with identical reads/catalogs/eligibility and ordinary calibration controls.
That protocol needs independent review and an explicit new compute/data budget
before any outcome access. No performance table, plot, GT truth comparison,
new genomic download or GPU training was used for this diagnostic.

Requested roles: main Sol6.1/high; independent reviewer Sol6.1/high;
source/literature workers Luna/max. Requests are recorded, but runtime identity
is not independently attested. No separate user-owned chat was created.
