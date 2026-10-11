# HG002 repeat-annotation preflight — UNBOOKED

2026-10-11. Independent S2 sidecar. Requested Luna/max; backend identity and effort are not attested. Main owns software setup, policy, booking and release. This note selects no annotation policy and does not release S2.

## Result

**Compatibility of the published pbsv BED with the exact selected FASTA is UNKNOWN.** The retained target is the full GENCODE 50 `GRCh38.primary_assembly.genome.fa` (3,151,417,447 B; SHA256 `e49b92b3e4f321bf254c042f25b726d9931c4d74c7523e8b6bb530e63b0cfd4b`). The names `GRCh38`/`hg38`, a matching contig dictionary, or matching lengths do not prove matching bases.

The official [pbsv v2.11.0 README](https://github.com/PacificBiosciences/pbsv/blob/v2.11.0/README.md#2-discover-signatures-of-structural-variation) calls `--tandem-repeats` highly recommended because it increases sensitivity and recall. It is optional. Its recommended [BED path](https://github.com/PacificBiosciences/pbsv/blob/master/annotations/human_GRCh38_no_alt_analysis_set.trf.bed) is on mutable `master`, not pinned by the README to a blob hash.

The [pbsv annotations directory](https://github.com/PacificBiosciences/pbsv/tree/master/annotations) associates the no-alt label with an NCBI `GCA_000001405.15` FASTA and documents `findTandemRepeats --merge <REF>.fa <REF>.trf.bed`. GitHub path-history metadata dates the published BED's addition to 2018-11-28 ([commit](https://github.com/PacificBiosciences/pbsv/commit/e13435fbf61424fa0947c1ac2aa90e9a54eac760)); it dates addition of the current helper to source control to 2022-04-22 ([commit](https://github.com/PacificBiosciences/pbsv/commit/bcec7d382f3ea40158ed9cca3c5fef9686a76641)). The current command therefore does not establish how the original BED was generated. The inspected sources give no exact source-FASTA checksum, historical tool/version and parameters, or base-level comparison to this GENCODE file.

The [PacBio reference README](https://github.com/PacificBiosciences/reference_genomes/blob/main/reference_genomes/human_GRCh38_no_alt_analysis_set/README.md) describes its GRCh38 no-alt reference as a modified `GCA_000001405.15` analysis set: it excludes ALT and decoy sequences; masks chrY PAR and specified duplicated centromeric arrays to N; replaces mitochondrial sequence with rCRS; adds chrEBV; and converts non-ACGTN codes to N. The [GENCODE 50 release page](https://www.gencodegenes.org/human/release_50.html) identifies release 50 as GRCh38.p14 / `GCA_000001405.29` and defines its primary assembly FASTA as chromosomes and scaffolds. These are different reference definitions. This evidence does not tell us which shared contig bases differ, or whether any specific BED interval transfers unchanged. **Do not infer identity from the assembly names.**

## Bounded alternatives for main and reviewer

| Path | What the evidence supports | Conditions and limit |
|---|---|---|
| Use the published BED | It is the file pbsv recommends for its `GRCh38` workflow. | First pin the exact BED blob and hash. Obtain authoritative sequence digests for the FASTA used to make it, then prove base identity for every BED contig against the exact retained GENCODE FASTA. Include contig set and masking differences. Names and lengths alone fail this check. No such proof was found here. |
| Generate a BED on the exact FASTA | The PacBio annotations page documents `findTandemRepeats --merge <REF>.fa <REF>.trf.bed`; the exact reference hash can be enforced as input. | Pin the helper's source revision/hash, runtime and dependencies, parameters/defaults, license, command log and output hash. This makes a new annotation on the selected bases; it does not recreate the historical BED by provenance. The upstream [TRF help](https://tandem.bu.edu/trf/help) gives command parameters but does not pin a release. If main selects standard TRF instead of the documented PacBio helper, freeze its exact release/build, flags and BED-conversion rules; treat that as a distinct method. |
| Omit the repeat BED explicitly | pbsv documents this input as a recommendation, not a required input. | Main/reviewer must record that `--tandem-repeats` was omitted and accept the sensitivity/recall limitation. The effect on this HG002 run and the ≥50 bp CDS-overlap cohort is UNKNOWN. Omission cannot support a claim that repeat-associated events are absent. Retain the complete native VCF and all filters/unresolved accounting. |

Generation or use of a published BED must fit the existing S2 account: at most 96 allocated CPU hours, 64 GiB RAM and 384 GiB peak disk, within the shared 256 GiB RAM / 512 GiB total-disk cap. Count the full FASTA read, output BED, temporary files, software and retained copies. Runtime, peak memory and output size are UNKNOWN; no allowance is added and no run is proposed here.

## Gate and next factual action

The [stage decision](2026-10-10-hg002-dna-stage-investment.md), [caller preflight](2026-10-10-hg002-dna-caller-preflight.md), [reference expansion](2026-10-10-hg002-reference-expansion.md) and [source-readset result](2026-10-11-hg002-source-readset-result.md) keep S2 conditional. At the source-readset note's snapshot, terminal custody QA and verified non-expiring home result custody were still pending. This sidecar changes neither that gate nor the S2 budget.

Before freezing the `pbsv discover` recipe, main's next factual check is to pin the published BED blob and seek source-reference per-contig sequence digests that can be compared with the retained GENCODE 50 FASTA. If that evidence is unavailable or fails, the reviewer can assess the exact-reference generation route against its S2 account, or an explicit sensitivity-limited omission. Main chooses; this note does not.

## Scope checked

Local: the governing objective attachment and the four named S2/source/reference notes linked above. No FASTA, BED, BAM or FASTQ body was read locally. Remote primary sources: versioned pbsv README; pbsv annotations page; PacBio reference-genomes overview and no-alt reference README; GENCODE release 50 page; TRF help page; and GitHub commit-history metadata for the BED and helper paths. Searches were targeted through Firecrawl and Exa; the search set was finite, not a full source-code, binary or historical-reference audit. No reference or BED asset was fetched or saved, no base comparison or native run was performed, and no software was installed.

One Exa result preview unexpectedly included BED coordinate text and a partial helper-source excerpt. No BED or source file was fetched or saved; I did not use coordinate values or source-code details from that preview. The provenance conclusions above use repository documentation and commit metadata only.
