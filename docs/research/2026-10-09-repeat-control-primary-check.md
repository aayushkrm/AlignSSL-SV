# Repeat controls: primary methods and current native interface

2026-10-09. Main source check for the proposed HG008 material prerequisite.
It changes the required baseline assessment, not the experiment's readiness.
No installation, caller execution, case table, genomic file, acquisition or
cluster job occurred. The separate independent scientific review is pending.

## Primary paper: stronger than the earlier abstract-only check

Life Sciences Literature's provided PMC metadata script resolved
DOI10.1038/s41587-023-02057-3 to PMC11921810, version1, PMID38168995.
Returned fields: author manuscript; `is_pmc_openaccess=false`;
`is_retracted=false`; license code `TDM`. Raw metadata was not saved.
These are metadata fields, not a scientific correctness assessment.
[Validated primary record](https://pmc.ncbi.nlm.nih.gov/articles/PMC11921810/).

Firecrawl's indexed paper-body query returned no passages. The live PMC
page then returned HTTP200. Main read the complete selected TRGT genotyping,
simple/complex repeat annotation and flanking-SNP genotyping sections, plus
selected results and code availability; not the complete paper or supplements.

The paper describes sequence-level repeat alleles, supporting reads and
flanking-SNP assignment to local haplotypes for difficult/mosaic repeats.
It uses aligned HiFi reads and repeat definitions. The paper's clustering
rule retains clusters with at least 10% of spanning reads and uses the two
largest for diploid calls or the largest for haploid calls. This is an old
method description, not an attestation of current runtime behavior.
[Primary methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11921810/).

Thus a sequence- and haplotype-aware targeted repeat control is relevant
to assessing inherited-repeat changes. Merely comparing general SV callers
could miss a strong ordinary explanation. Applicability to the fixed HG008
events, their copy states and normal mosaicism remains unverified.

## Current official interface: do not substitute old defaults

One Firecrawl developer search returned three results, followed by a live
official README fetch. The README states version5.1.0. A read-only GitHub
API call identified HEAD `b21c6217eeaef9a080205932fe29f730dc00e31f`
(June10,2026). Main read all three following documents at that commit:

| Official source | Consequence for a fair later control |
|---|---|
| [CLI](https://github.com/PacificBiosciences/trgt/blob/b21c6217eeaef9a080205932fe29f730dc00e31f/docs/cli.md) | WGS defaults to the size genotyper; the targeted preset defaults to clustering and also changes flanks, quality, alignment scoring and depth. Freeze a justified preset before outcomes. A karyotype file is supported; cancer copy-state capability was not established here. |
| [Repeat definitions](https://github.com/PacificBiosciences/trgt/blob/b21c6217eeaef9a080205932fe29f730dc00e31f/docs/repeat_files.md) | IDs, motifs and structure fields are required; the structure field is currently unused. Catalog definitions cannot be derived from evaluation-only tumor alleles. |
| [Remote inputs](https://github.com/PacificBiosciences/trgt/blob/b21c6217eeaef9a080205932fe29f730dc00e31f/docs/remote_files.md) | Native remote references, reads and catalogs are documented as experimental. This is not evidence of access, bounded transfer, complete context or successful runtime. Do not build a new transport framework merely to duplicate it. |

No current genotyping source code, binary, release asset or tumor analysis
was audited. The original paper's clustering rules must not be represented as
the default algorithm of the current 5.1.0 tool. Published descriptions,
current documentation and executed behavior are different evidence levels.

## Disposition

Independent review must assess the relevance and input contract of a
dedicated repeat baseline before any later falsifier is frozen. The
[October8 audit](2026-10-08-repeat-native-controls.md) also names SCIA and
MosaicTR; its own scope limits remain intact. This check neither rejects
the proposed scientific question merely for related prior art nor selects
a new method. The material prerequisite remains UNBOOKED. The full research
goal is unmet.
