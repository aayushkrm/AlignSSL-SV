# Post-native research opportunities

Date: 2026-10-09. Literature and repository-note review only. No genomic reads
or callsets were opened or downloaded. No cluster or Git action was taken.
This note does not approve an experiment or change a stop, charge, or budget.

## Current boundary

The latest status supplied with this request says Native02's canonical control
failed the exact PASS heterozygous endpoint after both native commands; the
remaining arms did not run. This is a synthetic assay-suitability failure. It
is not a biological null or a novelty result. The checked opening of
`PROGRESS.md` still said runtime review was pending, so this run status is
user-supplied and was not independently audited here. None of the research
questions below relies on it.

## Recommendation

The strongest conditional lead is **calibration of SV genotype confidence in
difficult sequence contexts**. Ask whether a reported genotype score predicts
the chance that the exact diploid genotype is correct, at the same accepted
call rate in simple and difficult regions. This has a direct use in clinical
interpretation and inheritance analysis. It is not another discovery recall
screen.

The lead is not ready for a study. The project’s HGSVC3 audit reports a 65-sample
SV VCF staged on cluster, but it counted record-level GTs; it did not establish
independent truth, donor-specific callability, or score availability. The
Platinum Pedigree provides public family truth and multi-platform data, but
SVUPP already used its benchmark truth. A held-out family or other independent
truth source is needed before this can support a general claim. See the
[HGSVC3 audit](2026-09-23-hgsvc3-genotype-audit.md) and the official
[Platinum data index](https://github.com/Platinum-Pedigree-Consortium/Platinum-Pedigree-Datasets).

| Rank | Candidate | Potential | Main limit today |
|---|---|---|---|
| 1 | Germline SV genotype-confidence calibration | High if confidence supports safe abstention across families and platforms | No independent, held-out score/truth pair is verified in this project |
| 2 | Truth evaluability for complex SV representations | High if representation alone changes important genotype or benchmark conclusions | Generic harmonization is mature; complex-event truth inputs are unverified |
| 3 | Low-VAF somatic SV confidence calibration | High clinical relevance in principle | MIMS already benchmarks 12 pipelines and models read-support limits; only one physical mixture is represented |

## Candidate 1 — calibrate germline SV genotype confidence

**Estimand.** Among callable truth loci where the same SV allele is present in
the query and truth, estimate the observed exact diploid-genotype error rate
for each reported GQ/GL-derived probability. Report calibration slope and
Brier score, plus error versus accepted-call coverage. Stratify by technology
and predeclared sequence context, including tandem repeats and segmental
duplications. Keep missed alleles and unresolved representations outside this
conditional genotype estimand; report them separately.

**Why it matters.** A caller can find the right allele and still assign the
wrong dosage. Downstream interpretation often treats a confident genotype as
usable. A score that stays calibrated across difficult regions could support
safer acceptance or abstention. This is a hypothesis about score reliability,
not a claim that current scores fail.

**Closest prior art.** [SVUPP (2025)](https://doi.org/10.1093/bioinformatics/btaf587)
uses read phasing in genotype likelihoods. Its abstract reports lower genotype
discordance than cuteSV2, Sniffles2, and kanpig on ONT and HiFi, and lower
Mendelian error in six ONT trios. That makes an accuracy-only genotyper
improvement a weak claim. The inspected abstract and methods emphasize
discordance and Mendelian error; whether its full supplements evaluate
probability calibration remains unchecked. [The Platinum Pedigree (2025)](https://doi.org/10.1038/s41592-025-02750-y)
adds a four-generation, multi-platform resource with 24,315 SVs and public
open-consent data. The hypothesis that difficult-context scores are
miscalibrated remains unverified, and this resource is not independent of
SVUPP's evaluation.

**Input readiness.** Metadata and public files exist. Local readiness is
unverified. The prior HGSVC3 audit is useful for inventory only; it does not
provide a truth mask or a validated error denominator. The Platinum files are
publicly indexed, but no exact score-bearing VCF, matching truth version, or
held-out cohort was checked or downloaded.

**Cheap falsifier.** If two family/platform slices are available, fit a score
map on one and test it on the held-out family/platform. Use exact
allele-matched truth genotypes; compare with a depth-only baseline at the same
genotype coverage, and keep related alleles and loci in one split. Stop if
score fields or independent callable truth are unavailable, or if the held-out
score does not improve error risk at a predeclared coverage. One family can
test within-family signal only; it cannot pass the transfer gate.

## Candidate 2 — measure the evaluable fraction of complex SV truth

**Estimand.** In a predeclared set of high-confidence, multi-allelic or complex
SV loci, estimate (1) the fraction of apparent callset disagreements whose
phased alternate haplotypes are identical and differ only in record
representation, and (2) the fraction that remains unresolvable from available
truth. Compare record-level classifications with full local haplotype
sequence. Do not count an unresolvable locus as a false call.

**Why it matters.** A benchmark can report caller error when two records encode
the same allele, or claim certainty where the truth cannot distinguish two
alleles. A result matters if it changes which genotypes or method conclusions
can be trusted, not merely a genome-wide F1 score.

**Closest prior art.** [vcfdist (2024)](https://doi.org/10.1186/s13059-024-03394-5)
already compares phased SNP, indel, and SV calls together and resolves some
cross-size representations. [The tandem-repeat benchmark](https://doi.org/10.1038/s41587-024-02225-z)
uses 86 haplotype-resolved assemblies and provides repeat-aware truth and
allele harmonization. [A September 2026 comparison of three SV benchmarking
frameworks](https://doi.org/10.1371/journal.pcbi.1014824) reports that framework
and parameter choices alter classifications and metrics for HG002 and
NA12878. Its experiments are limited to insertions and deletions; the authors
do not claim those results quantify complex, repetitive, or low-mappability
events. These sources leave a possible complex-event gap, but they also make a
generic “new harmonizer” claim untenable.

**Input readiness.** Platinum Pedigree and HGSVC3 provide public variant
resources; the Platinum repository also lists assemblies. This project has a
prior report of a staged HGSVC3 VCF, not verified phased truth for complex
events. Exact complete haplotypes, common reference, masks, and enough
independent complex loci are not confirmed.

**Cheap falsifier.** Use every eligible complex locus in one predeclared public
truth slice, if complete phased haplotypes are available. Reconstruct caller
and truth haplotypes and classify each disagreement. Stop if current evaluators
are already invariant on these loci, if apparent differences disappear under
sequence comparison, or if the remaining effect is only a small metric shift
with no change in genotype or method interpretation. Set the minimum useful
effect before reading outcomes.

## Candidate 3 — calibrate confidence for low-VAF mosaic SV calls

**Estimand.** For caller-emitted mosaic SV calls, measure whether a frozen
per-call score predicts truth status after conditioning on expected VAF, depth,
technology, and sequencing center. Test held-out centers and allele families.
Compare the score with a VAF-plus-depth baseline using calibration and
risk-versus-coverage, not another caller leaderboard.

**Why it matters.** False low-VAF SV calls can create a false mosaic diagnosis.
However, another sensitivity curve or minimum-read-support rule would add
little.

**Closest prior art.** The 2025 [SMaHT MIMS preprint](https://doi.org/10.1101/2025.09.18.677206)
uses a six-donor physical mixture, assembly-derived alleles, multi-center
sequencing, and 12 caller pipelines. It also models read-support probability
from VAF and depth. The authors’ [benchmark repository](https://github.com/BCM-HGSC/SMaHT_MIMS)
is at v2.0 and documents easy and hard allele sets. The paper and repository
already occupy generic low-VAF benchmarking, support-threshold curves, and
allele-matching comparisons. Per-call probability calibration is a narrower
hypothesis; its novelty is not established. One mixture with center replicates
does not establish transfer across independent biological mixtures.

**Input readiness.** The benchmark and code are public. The project’s earlier
triage records that hashes, reference compatibility, exact score fields, and
read access were not checked. No data were acquired here.

**Cheap falsifier.** First verify that the released caller VCFs contain usable
per-call scores and exact matching truth. If they do, hold out a center and
allele family; stop if score adds no predictive value over VAF and depth at
fixed coverage. Even a pass on MIMS alone would require an independent mixture
before a general mosaicism claim.

## Reject these weak claims

- **More generic released-callset filtering or a broader F1 screen:** the
  October 9 investment decision already stopped that route. Do not reopen it.
- **A generic SV harmonizer or another repeat representation benchmark:**
  vcfdist, the tandem-repeat benchmark, and the 2026 framework study already
  cover substantial parts of that claim. Candidate 2 survives only if it
  demonstrates material truth or genotype misclassification in complex
  events.
- **Generic CIGAR-fragment merging, repeat-purity enrichment, or local
  consensus rescue:** [TRsv (2025)](https://doi.org/10.1186/s13059-025-03718-z)
  reports repeat-associated fragmented alignments across long-read aligners
  and merges same-read repeat events. The project’s
  [fragmentation prior-art review](2026-10-09-native-fragmentation-prior-art.md)
  further limits the remaining contrast. Do not build a paper on the generic
  mechanism.
- **Another MIMS caller ranking or VAF/depth detection curve:** those are
  direct prior art. Candidate 3 is worth a small look only if score calibration
  is distinct and can be tested on independent mixtures.
- **Accuracy-only SV genotype improvement:** SVUPP already occupies that
  direction. A calibration or abstention result must add measurable value.

Do not use DeepSV as a foundation. SSL is not required. No candidate is a
selected campaign, and this note changes no earlier stop or resource limit.

## Search record and limits

Seven primary papers were checked: Maden et al. 2026; Dunn et al. 2024;
English et al. 2025 print issue (online 2024); SVUPP 2025; Kronenberg et al.
2025; the SMaHT MIMS 2025 preprint; and TRsv 2025. I read abstracts and the
relevant methods, results, and data-availability passages. I did not review all
supplements or establish an exhaustive novelty claim. No direction is called
novel because a search returned no result.

Ten Exa search calls were issued across four themes and requested 70 result
slots; those slots are not 70 papers read. The first combined response was
too large and truncated, so I used compact searches and fetched primary
publisher, PMC, bioRxiv, and author-repository pages. NCBI Entrez
returned three broad searches; a PMC metadata lookup for SVUPP confirmed its
PMCID, DOI, open-access status, and non-retracted status. Two exact-title
Entrez requests were rate-limited (HTTP 429), and three returned no records.
The first Entrez commands failed because `python` was unavailable; retrying
with `python3` succeeded. The successful calls emitted a LibreSSL compatibility
warning.

Two targeted Scite calls returned `INVALID_ARGUMENT`; I used Exa and the
primary publisher/PMC sources instead. Firecrawl was not called. The requested
Luna/max backend is unattested; no subagent output is presented as independent
review. No data files were downloaded, and no cluster or Git operation was
performed.
