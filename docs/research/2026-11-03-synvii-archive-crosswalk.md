# Actual synVII archive crosswalk

## Result and investment

The saved CNP0002230 metadata are internally reconcilable. They establish
archive membership and identify the reads associated with named strains.
They do not establish an eligible matched-dosage, different-structure fitness
contrast. No raw-read download or experiment campaign follows this result.
Park retrospective fitness inference unless a specific additional source
can supply the missing structure, dosage and measurement records. Missing
fields in this packet are UNKNOWN; they are not evidence that such records
do not exist elsewhere or that the biological hypothesis is false.

This executes the next action in the
[16 October source census](2026-10-16-synvii-source-census.md). The
[new packet](../../results/synvii_archive_inventory_20261103/README.md)
contains unchanged source bytes and a reproducible derived JSON crosswalk.

## Acquisition versus analysis dates

On 16 October the official [CNSA project page](https://db.cngb.org/data_resources/project/CNP0002230/)
was accessible by its direct record even though search had returned no result.
It listed 231 samples, 292 experiments, 319 runs, two sequence records and
539.83 GB. Three small files were retrieved by anonymous official FTP, not
through registration or an account. Together they contain 231,138 bytes.
The TSV metadata and file manifest were not yet documented in the earlier
Git checkpoint. On 3 November they were copied unchanged into this packet
and reconciled offline. This is not a fresh November archive snapshot.

| Source | Bytes | SHA256 |
|---|---:|---|
| experiment TSV |97,538|`2776b5da61f87c29051ac6544cbeabf015973179170f3b6814f68e248184adee`|
| sample TSV |59,424|`27cdbed6e9f2dadc484351a0ae4f159e2af3ab9655a0adf046eed738cbff0d18`|
| download manifest |74,176|`0f971b2705855d9bbea1669beb7728ed16d646256f631ebb9f3cae9c94d63364`|
| published Table S3 |18,157|`b7fcd9867096dcd52f6e551c28287c9f2c8d9c0a46236c1a53fc6524803ed3c5`|

No raw FASTQ or reference-sequence body was downloaded. The two reference
record pages were inspected on 16 October: N_001484978.1 and N_001484979.1,
lengths 1,028,998 and 1,028,952 bp. Those are reference records, not 219
resolved clone sequences. Their dates and lengths alone do not establish
design-versus-physical identity. Exact source URLs remain in the packet.

## Reconciliation and unresolved identity

The implementation checks unique sample/run keys, consistent experiment
membership, exact sample names across the TSVs, accession formats, paired
file names/checksum declarations and equality of all expected versus listed
read-file URLs. It rejects missing or extra links. All original sample/run
fields remain in the derived output. It never silently normalizes aliases.

| Observed record type | Count |
|---|---:|
| Archive samples |231|
| Unique experiments / runs |292 /319|
| Read-file links / separate reference links |638 /2|
| WGS / Hi-C / RNA-Seq run rows |230 /12 /77|
| Table S3 named strains |127|
| Sample-name joins with exact alias agreement |67|
| Sample-name joins with unspecified source alias |1|
| Sample-name joins with alias disagreement |3|
| Archive samples without a named Table S3 strain row |160|
| Named Table S3 strains without an archive sample-name join |56|

All 67 Table S3 SCRaMbLE strain rows join with exact aliases. This is an
identity crosswalk, not proof of full structures, assays or independent
origins. The 160 archive-only names remain present; they are not exclusions.
BY4741 has `/` as its source alias and is marked unspecified. The three
control-name joins with differing text remain explicit:

| Strain ID | Archive isolate | Published alias |
|---|---|---|
| YSy105 | `synVII` | `synVII W (257W-258C)-WT  159C loxP1-WT` |
| YSy142 | `N+S1` | `N+synVII` |
| YSy140 | `N+1` | `N+chrVII` |

These may reflect shorthand, but this audit does not certify their equivalence.
The strategy counts above are run rows. They cover 230 distinct WGS samples
(one row each), three Hi-C samples and six RNA-Seq samples. BY4741 is the only
sample without a WGS row. The RNA-Seq sample names are BY4741, YSy105, YSy140,
YSy142, YSy150 and YSy151; only the last two are SCRaMbLE source entries.
Seventy-seven RNA-Seq runs therefore do not establish 77 independent strains
or phenotype measurements. This coverage follows the actual run memberships.
Archive titles label 195 samples circular and 32 linear, plus four controls.
The 32 linear archive samples include source categories beyond the paper's
24 main linear derivatives. Do not replace the paper's selected 219-clone
denominator with 227 by adding archive labels.

## Scientific limits and reviewer correction

Sample `genotype` entries are marker descriptions. This packet has no
resolved ordered adjacency/path matrix, per-interval absolute copy-number
matrix, or quantitative phenotype/replicate field. The presence of WGS or
RNA-Seq does not fill those gaps by itself. Recovering structures from reads
would be new analysis, requiring a scientific reason to invest first.

The [independent logic review](2026-11-03-synvii-investment-review.md)
supersedes the old triage's ambiguous requirement to hold the same
“breakpoint set” fixed. Original cut-site positions differ from newly joined
oriented adjacencies. Holding every adjacency and multiplicity fixed can
remove the structural exposure itself. Topology is part of the proposed
effect if it differs. A meaningful-effect threshold must reflect biological
relevance as well as assay precision. An imprecise null is inconclusive.
Selection for improved growth also restricts any retrospective estimand to
recovered derivatives. Exact dosage matching alone does not establish novelty.

## Verification and execution state

Twelve focused controls pass on 3 November, including actual
packet counts, duplicate identities, wrong project/name, malformed checksum,
manifest mismatch, an unnormalized alias difference and output preservation.
The final parser, historical progress-accounting and README checks pass
together: 25 tests in 5.30 s. Read-only code review finds no confirmed join
defect; its suggested `TEXT_MISMATCH` clarification is applied and retested.
The old project venv executable is unavailable; bundled Python runs the
stdlib CLI, and an isolated `uv --with pytest` environment runs tests.
The spreadsheet skill informs read-only source preservation and explicit
missing records; no workbook was edited or re-exported.

The previous Sol6.1/high-requested reviewer completed the logic challenge.
After the revised objective was read, an independent Terra/max-requested
reviewer independently compared every saved sample/run/source join and
reproduced the JSON. It accepts metadata reconciliation and the park decision.
Its [packet review](2026-11-03-synvii-packet-review.md) also records three
exact-alias rows with additional workbook genotype text and the YSy196
Figure S5/karyotype-reference mismatch. Neither proves an identity conflict;
aliases alone cannot validate ploidy. Requests are recorded, not
backend-attested configurations.
Main cannot independently attest or switch its own serving model.

Fresh cluster inspection on 3 November finds no own queued/running job.
The permanent HOME geometry-run02 directory exists. The old AlignSSL scratch
workspace is no longer listed after its recorded October expiry. No new
full-source integrity claim is made. A different MCF7 workspace is unrelated
and was not changed. Use all useful CPU/GPU/RAM resources for justified
workloads and scale independent experiments in parallel; no idle reservation
is warranted for this small metadata diagnostic. The publication goal remains
active and unmet.
