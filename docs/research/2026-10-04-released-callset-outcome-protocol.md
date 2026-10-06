# Released HG002 call sets: development screen, protocol v1 draft

Status: **DRAFT, not scoring approval**. Freeze and obtain independent review
before biological records are parsed. No training or new caller is proposed.

## Question and scope

Do the six preselected released full-HiFi HG002 call sets leave eligible
current-v5.0q truth records uncovered even under lenient event compatibility?
Does a deterministic subset of those residuals survive local haplotype matching?
This is a falsifier for further investigation, not a new method or a replication
of the SVPG paper. Exact common raw reads/depth, historical reference bases,
SVPG version and graph membership remain unresolved. Do not call the result a
controlled same-input comparison, generator ceiling or independent confirmation.

## Fixed inputs and provenance

Use all six members from the pre-outcome `header_protocol.json`: cuteSV,
DeBreak, Sawfish, Sniffles, SVIM and SVPG. The verified source ZIP SHA-256 is
`fff2f1d2978234a1357c6a16ce5ed9fabf17925955247ae2f9ee2ee8564eb7ca`.
Do not replace callers after inspecting outcomes or omit DeBreak for its size.

Cluster root: `/scratch/igorno-alignssl_restart_20260922/`.

| Input | Relative path | Existing SHA-256 pin |
|---|---|---|
| Paired current SV truth | `giab-hg002-v5-grch37/HG002_GRCh37_v5.0q_stvar.vcf.gz` | `edb582ceec508f6d745acd0a8c522ee4f235ff5bf4754ba6bdc4c3abee122b5c` |
| Its confidence BED | `giab-hg002-v5-grch37/HG002_GRCh37_v5.0q_stvar.benchmark.bed` | `fbdec183e5b0ba83efdb5880ae038db98cd12cd9715e28debb9ed96541c10f40` |
| Truth tabix index | `giab-hg002-v5-grch37/HG002_GRCh37_v5.0q_stvar.vcf.gz.tbi` | `f1b274c5e1fe2e0c15e583039c6114e3acc281f4e39ccbc4bb42c7968f1983f6` |
| Earlier Tier1 territory | `recovery-pilot-v1/HG002_SVs_Tier1_v0.6.bed` | `a9bf43a242e74d403cf78f158dbf5b657b5aa5b4961fbba7218bbfe54072d82c` |
| Reference | `recovery-pilot-v1/hs37d5.fa.gz` | `e9157e19a95e01dfc47080b5b6aa559c861de90b9934c2ea7c49cd5ec49e0285` |
| Reference FAI | `recovery-pilot-v1/hs37d5.fa.gz.fai` | `1eab7540d4b62ef0b43b50581d027be37c1ee57da9e9cb75957e750641c8630c` |
| Reference GZI | `recovery-pilot-v1/hs37d5.fa.gz.gzi` | `4542808776e9376b2593cf461987d567f4b08d05babb6373a716591297cc9805` |

Recheck these bytes before use. NIST's
[current README](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/NIST_HG002_v5.0q_variant-benchmarksets_README.md)
states that v5.0q is a draft, derives from Q100 assembly V1.1 and needs paired
VCF/BED use. Small variants in the same VCF support local harmonization. The
July 17 corrected `ALT="*"` exclusion supersedes the older erroneous `ALT="."`
example. Never silently treat star alleles as absent variants or use a small-
variant BED for SV evaluation. No older benchmark release is substituted.

## Territory, units and fixed screening rules

Use autosomes 1–22. Merge overlapping/adjacent BED intervals before Boolean
operations. Define **Q100-added territory** as current confidence BED minus
Tier1 v0.6 BED. Define the ordinary comparator as their intersection. These
are benchmark-territory definitions, not evidence of intrinsic genomic difficulty.

Assign each original truth record `sha256(source_sha256|ordinal)`, where ordinal
is its one-based position in the complete original VCF stream. Preserve an
ordinal-to-record map outside Git and duplicate/decomposed-record multiplicity
in screening denominators. Truth units are biallelic sequence-resolved pure
INS/DEL records with diploid GT `0/1`, `1/0` or `1/1` (phased forms allowed),
no missing allele and net length >=50 bp. Define purity by trimming the maximal
common suffix, then maximal common prefix: exactly one remaining allele string
must be empty. Preserve phased GTs. Exclude and count multiallelic, symbolic/star, ambiguous-base, complex
replacement, missing/partial GT, reference-only and out-of-scope records;
these are limitations of this screen, not evidence that excluded biology is
easy or absent. A truth unit's full anchored reference span plus 2,000 bp on
each side must fit inside one interval of its assigned territory. Count
boundary/mixed-territory units separately. Do not estimate full-genome recall.
The units are records, not independent biological events. Before selecting the
20 checks, merge overlapping buffered residual spans into event clusters.

Stage all source caller records unchanged except deleting INFO/RNAMES values;
keep allele sequences, other INFO, all FORMAT, FILTER, QUAL, sample order and
GT. Retain the immutable original archive. Sorting may change order but not
records. Any unsupported field/record or line-budget failure stops the stage;
do not drop it silently. Save source/member hashes, counts and transformations.

Use installed **Truvari 5.4.0**, pysam 0.24.0 and edlib 1.3.9.post1 on the
cluster, with versions and installed source identities recorded before use.
This is not the paper's Truvari 5.3 execution. Fixed event screen:

```text
truvari bench -b eligible_truth.vcf.gz -c CALLER.vcf.gz -o NEW_DIR
  -f hs37d5.fa.gz -s 50 -S 30 --sizemax -1
  -r 1000 -p 0 -P 0.5 -O 0 --pick multi --dup-to-ins
  --bnddist -1 --no-decompose
```

Do not interpret this deliberately lenient, one-to-many compatibility screen
as accurate SV recall or precision. A compatible call can cover more than one
truth record. No genotype-agreement requirement is imposed by this screen.
Run each caller separately; never merge different callers into a synthetic
haplotype. A truth record is covered by the released union if any caller has
a compatible record. For the as-released presence arm retain all FILTER/GT
states and report missing/reference GTs separately: that arm describes listed
allele presence, not predicted donor genotype. A secondary native-VCF-filter
arm adds `--passonly --no-ref a`; record excluded FILTER and GT populations.
PASS and `.` handling must be checked against pinned installed source, not
assumed from the terse help string. This arm does not invent extra QUAL/GQ
thresholds or assert that all downstream publisher filtering is known.

Do not use precision/F1 from unrestricted comparison territory. Report the
full eligible denominator, screening residual count/fraction and per-caller
compatibility counts for each territory and arm. The as-released residual is
an optimistic screen, not a calibrated error rate. Publish exclusions and
missingness counts. No tuning, significance claims or multiplicity search.
For the hard-minus-ordinary screening difference, use a fixed 1-Mb reference
block bootstrap (2,000 draws, seed 20261004); show a 95% percentile interval
and block/record counts. Assign each record to
`(chrom, floor((POS-1)/1,000,000))`. Jointly resample the union of eligible-record
blocks, retaining both territories' counts in each sampled block. Do not
resample territories separately. With a zero observed territory denominator,
report the difference and interval as undefined. Report zero-denominator
draws without retries; fewer than 1,900 valid draws makes the interval
inconclusive. This interval describes this donor and screen only.

## At most 20 local haplotype checks

Choose from as-released union residual event clusters by ascending SHA-256
of `20261004|chrom|start|end`, with stable numeric-contig/position tie-breaking.
Take the first 20, or all if fewer. Do not pick by caller scores, visual appeal,
variant length, gene or favorable apparent mechanism. Save the complete
cluster list and selected hashes before refinement.

For each selected cluster and caller, first create a **separate regional bench
directory** with the complete original v5.0q VCF as its saved base path, not
`eligible_truth.vcf.gz`, and the full staged caller VCF as its comparison path.
Use the same fixed parameters and that cluster's frozen context BED. Preserve
mapping to selected original truth identities. Internal screening filters do
not remove small variants from these original input files. Existing Truvari `refine --align poa --threads 1
--use-original-vcfs --coords R --buffer 0 --subset` supplies the fixed local
harmonization, with regions passed explicitly. It inherits `-p 0`: the endpoint
is **geometry compatibility after POA harmonization**, not exact haplotype
sequence equivalence. Retain output/logs and identify which selected targets
remain uncovered; an unassignable regional summary makes the cluster unresolved.

Before construction, validate both complete context inputs: exact REF against
the pinned reference, every overlapping record wholly inside the context,
resolved biallelic alleles, complete diploid GT and no conflicting overlaps.
Collapse byte-identical allele/GT/phase duplicates only in a separate
reconstruction view, retaining their original identity list. Different GT/phase
annotations or other overlaps remain unresolved. Within each input, at most
one heterozygous record may be unphased; with several heterozygous records,
require all phased and a common explicit nonmissing phase-set identifier.
Never infer phase sets from GT order or generic sample labels. Boundary-crossing
variants, missing phase, unresolved symbolic/large alleles, REF mismatches and
compound conflicts remain **unresolved**, not a stable biological miss.
If the installed builder omits a relevant record by FILTER, size or
representation, classify that caller/cluster unresolved unless an inclusion
route was frozen and synthetically verified before outcomes. A builder omission
must not become an apparent miss.
Do not pool caller haplotypes or replace unknown genotypes with reference.

Classify the selected checks as representation-compatible, still unmatched
under this harmonization, or unresolved/failed. Only this selected subset has
been checked. It cannot establish a whole-set stable-miss rate, remove all
truth errors, or demonstrate read recoverability. The draft benchmark still
needs independent allele/read adjudication before accepting an actual miss.

## Resource amendment and decision gate

Requested, not yet approved: selected source-body decoding <=2 GiB, **total**
decoded input traffic <=6 GiB including truth, repeat passes and failed reads;
combined local/cluster work <=2 CPU-hours, <=4 GiB RAM. This explicitly replaces
the prior 256-MiB selection cap and proposed 2-GiB all-pass cap. The fixed six
members alone require 1,037,019,267 bytes; compact source staging and the two
screen arms require repeat reads. Use one CPU-only SLURM job, no GPU or other
users' jobs, <=90 minutes; charge local staging separately within the total
two CPU-hours. SLURM enforcement must cover descendants: installed `refine`
creates a two-worker counting pool even with `--threads 1`. Record allocation
and aggregate accounting. Local single-process staging requires an external
RSS supervisor and a 30-minute CPU limit; monitored memory is not a hard macOS
RAM guarantee. Limit VCF lines to 32 MiB and inventory metadata to 4 MiB.
Charge discarded RNAMES bytes. Freeze sample-column mappings and installed
source/dependency hashes before the screen. Generic sample labels map released
columns, not verified raw donors. Preserve >=10 GiB free local space. No new reference, assembly,
graph, raw reads or large archive acquisition is needed for this stage.

Hash failures, unsupported inputs, missing POA dependencies or exhausted
budgets stop this execution and are feasibility failures—not biological nulls.
Do not extend budget or change matching rules after seeing favorable outcomes.
Retain logs and partial results marked incomplete. Raw caller/truth/ref files
remain outside Git; commit only protocols, small summaries, selected-record
identifiers and checksums, not read names or large alleles.

If no as-released residual exists, stop this particular recovery lead under
this scope; it does not prove there are no true caller errors. If the selected
checks are all compatible or unresolved, do not invest in a generator. If at
least five distinct selected clusters remain unmatched after geometry/POA
harmonization with no unresolved
representation issue, consider a separately reviewed, bounded raw-read/truth
adjudication—not a positive scientific claim or training campaign. Fewer than
five is inconclusive for the planned mechanism screen. Independent unrelated
donors and a distinct mechanism are required before a publication contribution.
