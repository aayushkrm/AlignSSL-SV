# Inversion recurrence and gene exchange: native-control screen

October 7, 2026. Starting repository HEAD `9a58e81fbdaff790f2ddb2385ba1a21a8b6d7ca7`.
This is a prior-art and source audit, not a selected method or measured biological result.

## Result

Do not select the broad proposal “add gene exchange to inversion-recurrence inference.”
Current public native code already simulates exchange across chromosome orientations,
checks a flux grid, and trains a recurrence classifier on flux-varied simulations.
This affirmative overlap defeats the broad novelty premise. No simulation was run here.

The motivating question was whether exchange can make an inherited inversion appear
to have multiple origins. A localized tract model might differ from population migration,
but that distinction alone is not a useful contribution. No consequential residual
failure, independent origin truth, or advantage over the current native control is established.
Do not launch a campaign or relabel a generic sensitivity study as a new method.

## Evidence and its limits

| Source | Verified observation | Limit |
|---|---|---|
| [Genome-wide inversion diversity preprint](https://pmc.ncbi.nlm.nih.gov/articles/PMC12485790/) | Read simulation methods separate single-origin orientations and allow migration between same-orientation demes in recurrent simulations. | September 2025 preprint, not assumed peer reviewed. Its historical null is not the full current code landscape. Discussion of conversion is not a measured conversion control. |
| [17q21.31 gene-flux preprint](https://doi.org/10.64898/2026.09.28.755014) | The read results describe 13 two-switch tracts of 17–150 kb across five heterozygous sperm donors and a reported rate of 0.0033 ± 0.0008 events/Mb/meiosis for tracts >10 kb. | September 30, 2026 preprint. Switches do not directly label inversion origins or uniquely establish conversion versus double crossovers. Read full-text prefix stops before Methods. |
| [Current upstream single-origin generator](https://github.com/hsiehphLab/inversionSimulation/blob/af0bece3f9470a34788e44ec985f2fd01684a2ca/scripts/singleINV_m1.py) | Complete source has two populations, a split, and no migration call; parsed `m_const` is unused. | Source inspection only; no execution. Code uses `N_a=6000`; do not silently substitute the article's reported parameterization. |
| [Current upstream recurrent generator](https://github.com/hsiehphLab/inversionSimulation/blob/af0bece3f9470a34788e44ec985f2fd01684a2ca/scripts/recurrentINV_m1.2pop.py) | Complete source sets migration between two direct and two inverted demes, with two independently drawn admixture fractions. | No cross-orientation migration in this inspected file; not a claim about every method. |
| [Current ferromic reference simulator](https://github.com/SauersML/ferromic/blob/0aa57692c4f49c676a790757aa25d930191c7b34/simulations/refsim/refsim.py) | Inspected `demography`, `_flux_pairs`, `demography_single` and growth-model sections implement symmetric opposite-orientation `m_flux`. | Migration is an exchange analogue, not an empirical conversion-rate fit. Selected sections, not the entire 33,157-byte file, were read. |
| [Native flux-grid verifier](https://github.com/SauersML/ferromic/blob/0aa57692c4f49c676a790757aa25d930191c7b34/simulations/refsim/verify_reported_flux.py) | Complete source expects 11,520 successful loci, two arms, and flux levels 0, 1e-8, 1e-7, 1e-6; it checks sampling and computes call-count trends. | Expected rows are not an independently verified completed grid or replicated effect. No rows were downloaded or checked here. |
| [Native recurrence training](https://github.com/SauersML/ferromic/blob/0aa57692c4f49c676a790757aa25d930191c7b34/recurrence/simulate.py) and [classifier](https://github.com/SauersML/ferromic/blob/0aa57692c4f49c676a790757aa25d930191c7b34/recurrence/classifier.py) | Complete source includes flux as a simulation axis and standardized logistic warm-start/partial-AUC refinement. | No independent rerun, calibrated real-origin labels or reported performance accepted here. |

The sperm-paper unit is events/Mb/meiosis. The code's migration unit is per
population lineage per generation. These are not interchangeable. A mapping needs
tract lengths, affected sequence, orientation frequency and a population model.
Do not insert 0.0033 directly into `m_flux` or treat this mismatch as a measured failure.

## Immutable source checks

Public upstream pin: `af0bece3f9470a34788e44ec985f2fd01684a2ca`.
Its recursive Git tree reported `truncated=false`. Read four complete files into
memory and verified byte counts and Git blob SHA-1 before displaying them:

- README: 840 bytes, `b1eb0476f77c5920f7d5d7fc132733f5f8b8c7e8`.
- Single generator: 2,334 bytes, `da2ca6992527070e732b0b8171919df67cafa77f`.
- Recurrent generator: 3,550 bytes, `50243edfcc26fcabf89c85a3ee5de0c0b59d7d89`.
- Minimum-state-change scorer: 1,260 bytes, `d9defabbcd13b0ea5b7d6590dc702fcca6fa74ba`.

ferromic pin: `0aa57692c4f49c676a790757aa25d930191c7b34`.
Likewise verified reference simulator 33,157 bytes / `26e9bba289321e20cf7d4bb9278be712e8d7c793`,
flux verifier 2,466 / `0058313394521b79e5632375e217cdb96371a963`,
training script 5,094 / `bf757f07636d22036b76e1abf70682d8edd04965`, and
classifier 4,048 / `651f77aedb210c9e6c4c9d363027c7a1d2a390ed`.
The first combined display truncated part of reference-simulator context; no
whole-file coverage claim. An Exa-cached recurrence README is not current-code proof.

## Search and execution ledger

Date window: October 7, 2026 minus 18 calendar months = April 7, 2025 through
October 7, 2026 inclusive; seminal 2022 work was a separate historical comparator.
Exa: two main searches, 10 and 5 requested result slots (15), three-page fetch at
12,500 characters/page and one full-text fetch at 24,000 characters. Slots and
partial fetches are not 15 fully read papers. Result-card previews were reviewed;
deduplicated preprint/journal versions are not independent studies.
Entrez returned four publication IDs; summaries were metadata, not full articles.
PMC resolved the preprint and its versioned XML: 116,191 bytes, verified MD5
`763e92679e36dc2102cb71019dad24a7`; relevant simulation paragraphs were read.
bioRxiv metadata confirmed the gene-flux date/version. No raw metadata saved.
One incorrect local Entrez script path returned no evidence. Scite rejected an
overlong intent field, then required a paid plan/trial; neither call yielded papers.
Exa and Life Sciences Literature supplied alternatives; no subscription change.
No genomic data, simulation, install, job launch/cancellation, training or test-set
use. Independent scrutiny and comparison with the other territories remain next.
