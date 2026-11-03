# synVII archive packet: independent review — 2026-11-03

**Decision: accept the metadata reconciliation; park retrospective fitness inference.** The packet does not establish an eligible exact-dosage, different-structure contrast. It also does not show that such a contrast is absent. Reopen this branch only if a specific source record can supply the missing fields. This review does not authorize a read download or an experiment campaign.

| Question | Finding |
|---|---|
| Do the saved records reconcile? | Yes, at the metadata and exact-text level. |
| Is a matched structural and phenotype contrast established? | No. Ordered paths, absolute segment dosage, ploidy and usable clone-level phenotype measurements remain **UNKNOWN** for this purpose. |
| Is a useful contrast ruled out globally? | No. The packet is not a complete census of all possible source records. |
| Next step | Park. If the underlying source data for Figure S10A/C or another specifically identified clone-keyed record becomes available, check it against the finite gate below. |

## Independent checks

I read the updated objective, the [inventory code](../../analysis/synvii_archive_inventory.py), all four packet inputs, the derived JSON, the [crosswalk note](2026-11-03-synvii-archive-crosswalk.md), and the [packet README](../../results/synvii_archive_inventory_20261103/README.md). I independently parsed the TSVs and workbook with Python and `openpyxl`, and compared every saved sample, run, matched workbook row, alias status and unmatched workbook row with the inputs. I compared the multiset of manifest experiment paths with the paths reconstructed from the metadata, including project, sample, experiment, run and filename. These comparisons passed. I also checked the relevant local supplement legends and Figure S10.

| Item | Independent result |
|---|---:|
| Unique samples / experiments / runs | 231 / 292 / 319 |
| Unique declared read-file paths / separate sequence links | 638 / 2 |
| Named Table S3 strains / sample-name joins | 127 / 71 |
| Alias status among archive samples: exact / unspecified / text mismatch / no workbook row | 67 / 1 / 3 / 160 |
| Named Table S3 strains with no archive sample-name join | 56 |

All 319 run rows declare two filenames and two syntactically valid MD5 values. All 638 paths match the saved manifest, with no duplicates. The MD5s are **declarations**; no read body was downloaded or hashed. The checks do not establish file availability, read quality, assay completeness or biological identity. The two sequence URLs were retained, but their bodies were not checked here.

Coverage is by sample, not by independent replicate:

| Strategy | Run rows | Unique experiments | Unique samples |
|---|---:|---:|---:|
| WGS | 230 | 230 | 230 |
| Hi-C | 12 | 12 | 3 |
| RNA-Seq | 77 | 50 | 6 |

BY4741 is the only sample without a WGS row in this packet; it has Hi-C and RNA-Seq rows. The 27 experiments with two run rows are RNA-Seq experiments. Multiple runs, experiment labels and the word “rep” do not by themselves establish independent biological replicates.

The archive titles label 195 samples circular and 32 linear, plus four controls. The workbook matches 35 circular and all 32 linear labels; the remaining 160 archive-only names are circular-labelled samples. These are archive labels, not proof that all 227 belong to the paper's 219 selected derivatives. The 32 linear labels and the reported 24 main linear derivatives need a membership crosswalk before their denominators are equated.

## Identity and source-reference cautions

The join uses exact strain-name text, followed by an exact comparison of workbook alias with archive isolate. The 67 `EXACT` results support text agreement; they do not validate the underlying strains or all genotype fields. The three `TEXT_MISMATCH` records remain unresolved, not proven conflicts:

| Strain / archive accession | Archive isolate | Table S3 alias |
|---|---|---|
| YSy105 / CNS0761754 | `synVII` | `synVII W (257W-258C)-WT  159C loxP1-WT` |
| YSy142 / CNS0761755 | `N+S1` | `N+synVII` |
| YSy140 / CNS0761756 | `N+1` | `N+chrVII` |

BY4741 / CNS0638055 has `/` as the workbook alias, so its alias is unspecified. Do not silently equate or exclude these records based on the label comparison.

Three other rows need care despite exact name and alias agreement: YSy196 / CNS0618035, YSy197 / CNS0618036 and YSy198 / CNS0618037. Their archive mating-type field says `MATa/a`; their Table S3 genotype cells each contain a second genotype line that the archive genotype field does not contain. This is a difference in source descriptions, not proof of a sample swap or of a particular genome-wide ploidy. Preserve both descriptions and resolve ploidy independently before matching dosage.

Table S3 cell E106 associates YSy196 with “Figure S5” and karyotype analysis. In the retained published supplement, Figure S5 describes a spotting assay; Figure S6 describes karyotype analysis. The note and figure label do not align in these copies. Do not infer an automatic relabeling or use that note alone as strain-level karyotype evidence.

## What the source figures do and do not establish

The [retained supplement](https://pmc-oa-opendata.s3.amazonaws.com/PMC10667312.1/mmc1.pdf) has Figure S10A schematics for 24 linear strains and a color scale for relative recovery. Figure S10C shows synVII segment-copy states for 18 named strains. Figure S11 reports seven biological replicates for a set of reconstructed deletion strains. These are real source observations; they do not supply, in this packet, a verified clone-keyed table of complete ordered paths, absolute genome-wide dosage, ploidy and same-assay replicate measurements for an eligible contrast. The Figure S10 legend's `n ≥ 200` must not be relabeled as 200 independent strain origins. Do not turn image colors or bar heights into exact raw measurements.

The packet lacks the required structured fields; that is a statement about the inspected files, not a claim that paths, dosage, phenotypes or source data are absent elsewhere. Marker text, a displayed synVII copy state, total retained length, or a chromosome cartoon does not alone establish exact genome-wide dosage or phase. Selection for growth also limits retrospective inference to the recovered cohort. A single clone per path cannot separate architecture from other clone differences.

## Conditional source gate

If a concrete source-data record for Figure S10A/C or an equivalent named record is identified, make one bounded, read-only check for the following together:

1. Stable strain IDs and a documented mapping to the archive, including the unresolved aliases and source-reference issue where relevant.
2. Resolved oriented segment paths and copy multiplicities, with uncertainty, circular-equivalence handling where relevant, absolute interval dosage, ploidy and other genome-wide copy changes.
3. Quantitative measurements for the same assay and condition, their units, batches and independent biological units, plus the relevant selection and ascertainment information.
4. At least one distinct-structure comparison with exact resolved dosage and a specific scientific contribution beyond the already-supported general proposition that architecture can affect fitness.

If a required field is missing or unresolved, record it as **UNKNOWN** and keep the branch parked. If a complete, sufficiently resolved source cohort contains no eligible pair, stop this dataset branch; do not infer that no such pair exists elsewhere. Even if a candidate passes the source gate, a new decision on novelty, confounding, uncertainty and the smallest justified validation is required before further investment. Distinguish original cut sites from the new oriented adjacencies: conditioning on all adjacencies can remove the structural difference being studied.

## Reproducibility and scope

The four packet inputs were byte-identical to the previously retained local copies. Independent SHA256 checks matched the values in the JSON:

| Input | SHA256 |
|---|---|
| `metadata_CNP0002230_experiment.tsv` | `2776b5da61f87c29051ac6544cbeabf015973179170f3b6814f68e248184adee` |
| `metadata_CNP0002230_sample_Microbial_sample.tsv` | `27cdbed6e9f2dadc484351a0ae4f159e2af3ab9655a0adf046eed738cbff0d18` |
| `cnsa-data-download-links.txt` | `0f971b2705855d9bbea1669beb7728ed16d646256f631ebb9f3cae9c94d63364` |
| `source-table-s3.xlsx` | `b7fcd9867096dcd52f6e551c28287c9f2c8d9c0a46236c1a53fc6524803ed3c5` |

The inspected `inventory.json` SHA256 was `91dbd295536e8568fb3366103fded0a663009ac00c1b361c45afbcf5431b4c4a`; the code SHA256 was `7863c79a614a31cc85555a66f44d85a74fdf517ac7e06ed31fa86192fff8a23d`. Running the current inventory function in memory reproduced the saved JSON exactly. After the alias-label change, the 12 focused tests passed offline in 0.38 s. The retained supplement SHA256 was `c1365d3c8ee40ea81cd2fdbed5388adc02f95a3ae87fa7297c1e424c54ca228e`.

Byte equality binds these local copies; it does not independently verify their original online acquisition. I used no network, cluster, Git operation or raw-data download in this review. Terra/max was requested for this reviewer; the serving model and effort were not independently attested.
