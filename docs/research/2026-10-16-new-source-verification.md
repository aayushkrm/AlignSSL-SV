# New-source checks and scientific decision boundary

16 October2026. Main verifies selected primary sources after the broader
scout. This is not a new study result or a selected publication direction.

## What is verified

- The15October COLO829 paper uses a donor-specific assembly and two melanoma
  passages. It already demonstrates a reference-coverage benefit and resolves
  three centromeric junctions. Its limitations include incomplete assembly and
  uncertain generalization. Repeating the reference comparison is not a new
  contribution. [Primary paper](https://doi.org/10.1016/j.cell.2026.09.033).
- The current portal table marks COLO829 sequences, germline variants and
  somatic variants open. Its full text requires portal login for open-file
  download, including self-registered users. A general protected-tissue
  paragraph must not be applied to this cell line. Exact files and our access
  remain unverified. [First-party access policy](https://data.smaht.org/docs/access/data-availability-and-access).
- HitSV describes germline reconstruction/genotyping across technologies,
  populations and species. Those results do not establish performance on
  low-frequency somatic mixtures. Nor do they prove that every useful
  cross-platform question is resolved. [Primary paper](https://doi.org/10.1038/s41587-026-03332-9).

Main reads the COLO829 results, limitations and resource sections, then checks
the author repository via read-only GitHub requests. Observed source commit:
`1e8454e21a30a7e4b0d9eb78edb44a8aee4ee576`. Its public tree includes small code
and CDR interval tables, not only large sequencing inputs. Examples:

| Public artifact | Declared bytes | Inspection scope |
|---|---:|---|
| `Revision/scan_Centromeric_unitsize_indels_SV.py` |41,354|Path/size and purpose from revision README; code not read or executed|
| `Revision/colo829_centromere_genetic_analysis.py` |157,147|Path/size and purpose from revision README; code not read or executed|
| `Centromere/bulk_cdr_bl_r9_highconf.bed` |5,461|Path/size only; not an SV truth table|
| `Centromere/COLO829-BL_UL-ONT-R9.single_mol_cdr.bed` |6,566,594|Path/size only; not downloaded|

[Pinned author repository](https://github.com/StergachisLab/T2T-COLO829BLT-Manuscript/tree/1e8454e21a30a7e4b0d9eb78edb44a8aee4ee576).
The README also links public DiMeLo material. This does not attest which
files contain sequence, compatible references, junction evidence or the
correct passage. The paper links a UCSC session and Zenodo22774707; availability
statements are not a completed event/truth/caller crosswalk.

## Corrections to the scout, not new evidence of a method gap

The [independent challenge](2026-10-16-new-evidence-scout-review.md) is sound:
large raw files, completed broad benchmarks and lack of an isogenic phenotype
contrast do not rule out every cheap sequence-inference diagnostic. Scout
no-download limits are not limits on the user's broader project. Full cluster
resources can be used when a worthwhile workload can benefit from them.

The updated scout proposes checking three centromeric junctions against
benchmark truth and scoring. Treat this as a possible source/case crosswalk,
not a ready scientific result. Main does not adopt its arbitrary two-of-three
advance threshold. Keep all three and record why each comparison is evaluable
or UNKNOWN. One material discrepancy may merit investigation; three expected
omissions outside declared benchmark territory may add no new information.

Before interpreting any such comparison, establish sample/clone/passage,
reference, callable mask and exact allele/path identity. Coordinate proximity,
liftover or a generic BND pair alone cannot establish the same junction.
Missing sequence in GRCh38 can explain unscored breakends and is already a
paper result, not automatically a benchmark defect. The more informative
question is whether new evidence changes an old allele-level conclusion in
shared evaluable sequence, beyond added coverage or representation, and
whether the paper already resolved that case. No such case is verified here.

Likewise, the rare-specific-allele versus abundant-near-identical-background
question is not newly discovered today. The full
[October7 triage](2026-10-07-mosaic-identifiability-triage.md) already records
MIMS hard/easy truth, joint germline/somatic matching and complex-region
limits. Main rereads that note and the full
[October9 investment comparison](2026-10-09-post-native-value-decision.md).
New file availability could change experiment feasibility, but does not by
itself supply scientific novelty or justify repeating broad caller rankings.

## Retrieval and current action

Exa initially times out on HitSV. Parallel Search retrieves its primary
methods/results as the alternative. Exa retrieves a147,910-character COLO829
article representation; main reads the relevant sections, not every reference
or supplementary figure. Parallel retrieves the SMaHT policy table; bounded
`curl` of the same public page confirms the login requirement. Its separate
Zenodo19636324 lookup times out. That record is HapMap mixtures, not a verified
COLO829 release; a timeout is not missing data. No raw biological file,
reference or benchmark callset is downloaded, and no new account is created.

Current action is source verification of a potentially useful finite residual,
in parallel with the controlled non-human evidence scout. No new experiment,
bulk acquisition, caller run or training campaign is selected by this note.
The completed HiFi geometry assay and its scoped investment STOP remain intact.
The publication goal is active and unmet.
