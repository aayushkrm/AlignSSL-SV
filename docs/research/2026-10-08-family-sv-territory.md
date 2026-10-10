# Family/trio de novo SV territory

Date: 8 October 2026. Scope A only: family/trio de novo SV ascertainment, parental origin, and recurrence. DeepSV stays excluded. No study or novelty claim is approved.

Main integration: the proposed zero-of-300 bound below assumes perfect ALT
detection and independent callable gametic targets. A passing 1% control alone
does not establish either assumption. Measured sperm fraction is a conditional
transmission proxy, not a clinical recurrence estimate. The
[main disposition](2026-10-08-three-direction-disposition.md) supplies the
sensitivity-qualified law; no assay or clinical recommendation follows.

## Decision

**Reject this as a current research lead.** One specific hypothesis is testable only if a matching paternal sperm sample exists:

> The 350-bp Alu insertion in *TRHR* in REACH000479 was present in at least 1% of the father's sperm. The trio call says “de novo,” but that sperm fraction would imply recurrence risk near 1%, assuming sperm fraction reflects conception risk.

The 1% threshold is a pre-set materiality level for this falsifier, not an estimate from the SV cohort.

This matters for recurrence counseling. A paternal haplotype identifies the chromosome carrying the insertion. It does not show when the insertion arose or how many sperm carry it.

```text
Child ALT; sampled parents REF  ->  de novo call under a read-support rule
Child phase = paternal H1       ->  variant lies on the paternal chromosome
Paternal sperm assay            ->  tests for a multi-sperm mosaic and its rate
```

## Nearest controls

The review window is **8 April 2025–8 October 2026**. The closest recent study is [Mortazavi et al., *Cell Genomics* (2026)](https://www.cell.com/cell-genomics/fulltext/S2666-979X(26)00048-0), DOI [10.1016/j.xgen.2026.101186](https://doi.org/10.1016/j.xgen.2026.101186). It studied 267 people in 63 ASD families. Publisher metadata gives 9 March 2026 online and 13 May 2026 citation dates; Exa also gave 13 May. Both dates are in-window.

- LR candidates required ≥3 phased proband ALT reads, zero ALT reads in both parents, and ≥1 phased parental REF read on each haplotype. SR-only candidates needed trio-genotype support and the original `PASS_STRICT` flag.
- The paper reports 65 candidates and 15 confirmed dnSVs (3 LR-only, 6 SR-only, 6 both) across 11 cases and 3 controls. SR breakpoint/depth evidence checked LR calls. The 350-bp *TRHR* Alu call lay on paternal H1.
- This is a strong trio-call control, but it tests sampled tissue, not sperm. Sparse parental REF reads do not exclude low-frequency germline mosaicism.

Two older controls close the obvious novelty paths:

- [Bowers et al., *AJHG* (2021)](https://www.cell.com/ajhg/fulltext/S0002-9297%2821%2900054-9) analyzed 9,599 genomes from 2,384 SFARI and 33 CEPH families. It inferred SV parent of origin by extended-read and SNV allele-balance phasing and reported paternal bias. This is a large phasing control, not a sperm mosaic assay.
- [Pauper et al., *European Journal of Human Genetics* (online 2020; issue 2021)](https://www.nature.com/articles/s41431-020-00770-0) studied five long-read trios. Review and breakpoint PCR left eight candidates: four SVs confirmed, two inconclusive, two likely false. None of the confirmed SVs was de novo; they had been missed in a parent. Missing-parent calls are a known failure mode.
- [A PLOS Genetics study](https://doi.org/10.1371/journal.pgen.1011651), dated 31 March 2025 (eight days before this window), used deep parental blood/sperm sequencing in five trios and found mosaics among phased small-variant DNMs, including sperm-only cases. This is assay precedent only, not SV evidence.

## Finite falsifier and label feasibility

For REACH000479, test the exact *TRHR* junction in two independent aliquots of stored paternal sperm, using a blinded, junction-specific unique-molecule assay. Validate error and sensitivity at 1% variant fraction; confirm any positive with a second assay.

If zero ALT molecules appear among ≥300 independent sperm molecules and the 1% sensitivity control passes, the one-sided 95% upper bound is below 1%. That rejects this hypothesis. It does not rule out a lower fraction or an event present only in the transmitted sperm.

**Independent outcome label:** the exact junction in paternal sperm, confirmed by a second assay, would label a detectable parental mosaic. Blood alone cannot rule out sperm-only mosaicism. The paper does not report stored sperm for this family, so availability is **unknown**, not absent. The label is feasible in principle but unverified here.

## Why stop

Trio reads cannot distinguish a one-sperm event from a mosaic below detection. The independent label may not exist for REACH000479. A positive result would inform one family, not establish a general SV rule. The 2026 study already has stringent parental support and orthogonal validation; older controls cover parent phasing and missed-parent calls. No broader contribution is supported here.

## Search and execution record

 - Exa: three distinct targeted queries, ten slots each (30 requested). Tool output was clipped; the full result-card count is unknown and 30 is not a read count. Three method-bearing sources supplied usable excerpts: Mortazavi 2026, Bowers 2021, Pauper 2020/2021. PLOS was checked only for assay precedent.
 - Firecrawl: the Cell page returned an ad/navigation shell. Exa's publisher-indexed passages supplied methods and date details. The Nature page returned metadata; Exa supplied its method excerpt. No further searches were run.
 - The 18-month window is 8 April 2025–8 October 2026. Older studies are close controls, not recent evidence.
 - Requested worker: **GPT-6 Luna / maximum effort**. This records the request only; backend model/effort is not attested. No worker or subagent was dispatched.
 - Only this note was written. No raw genomic data, scientific tool execution, imports, installs, jobs, credentials, Git operations, or other file edits.

The broad publication goal remains active and unachieved. This screen selects
no lead and authorizes no experiment campaign.
