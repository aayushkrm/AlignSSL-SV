# Research orchestration handoff — 22 November 2026

## Recommendation and scope

**Run one small, blind-to-variant-coordinate HG002 development diagnostic for
hard-region candidate discovery.** Its immediate question is whether a
sequence-resolved deletion or insertion can be proposed from the same
short-read data when a strong set of existing inputs does not already provide
that allele. Report the extra candidate-review burden and uncertain matches.
The test is exploratory, and no novel method or positive result has yet been
established.

This is a recommendation to the ongoing decision and review processes, not
their outcome. The proposed first run is more informative than another archive
inventory because a real, indexed 30× HG002 Illumina BAM is now available.
It is also narrower than a generic SV-caller leaderboard: adding an existing
caller, finding a truth-set disagreement, or seeing a one-donor recall gain
would not by itself be a publishable advance.

```text
Same HG002 reads + whole-reference FASTA + fixed chr21 search space
                         |
        +----------------+----------------+
        |                                 |
  Published caller inputs          Blind proposal arm
  pre- and post-filter             SvABA first: control only
        |                                 |
        +-------------+-------------------+
                      v
     One-to-one allele-aware match, after proposals are frozen
                      |
   paired benchmark BEDs + two HG002 truth sources + unknowns
                      |
      extra supported alleles / extra candidates reviewed
          |                             |
    credible opportunity        no opportunity / not evaluable
          |                             |
    compare against full        stop or resolve named missing input;
    caller + catalog union      do not manufacture a negative result
```

**This note records no caller run, truth/callset scoring, model training, or
cluster submission.** The Sol/max decision agent and separate Terra/max
reviewer are doing their own work; their pending conclusions are not assumed
here. DeepSV is not a scientific foundation for this proposal.

## What has and has not run

| Item | Evidence now | What it does not establish |
|---|---|---|
| CloneSeq | [Content audit](2026-11-22-cloneseq-content-result.md): 23/24 listed patients have a shared SV/SNV specimen-time key; 149 keys are repeated measurements. The 12 WGS specimen IDs link across six patients. The corrected third run and earlier versions are preserved. | Clone accuracy, equal assay cost, independent clone truth, or an adequately powered comparison. The [investment reassessment](2026-11-22-investment-reassessment.md) parks that campaign; this is not a biological null. |
| Three COLO829 junctions | [Source screen](2026-11-22-colo829-centromeric-source-screen.md): two exact junctions lack shared GRCh38/CHM13 sequence; the third has unresolved paired-allele identity and earlier partial evidence. | A shared-domain caller error. That finite three-case route is closed, not all hard-region work. |
| Low-frequency SV mixture | [Mosaic scout](2026-11-22-mosaic-sv-opportunity.md) found no independently verified, sample-matched SV positive set and negative mask for its proposed COLO829 mixture. | A valid false-positive rate or recall denominator for that mixture. |
| Hard-region sources | [Hard-region scout](2026-11-22-hard-regions-opportunity.md) specified a CMRG/v5.0q crosswalk and candidate-source gate. The [dicast archive check](../../results/dicast_archive_metadata_20261122_run01/) found no VCF-named entries in the 1.84 GB archive's inspected central directory; the timing script uses external BAM/VCF placeholders. A separate [shared-scope protocol](2026-11-22-cmrg-shared-scope-protocol.md) is registered. | At the last check, an `audit.json` had appeared in the other worker's result directory, but I had not inspected its contents or verified a terminal receipt or review. No matched caller comparison was reported. The archive check does not prove the authors' inputs do not exist elsewhere. |
| Old caller outputs | The [Parliament2 header gate](2026-09-28-parliament2-header-gate.md) checked nine files from six historical caller families. The [Zenodo package gate](2026-09-28-zenodo-sv-package-gate.md) checked a package prefix. | A same-read, same-reference, current unfiltered candidate panel. Neither result should be relabeled as such. |
| Retained cluster HG002 BAM | Its [readiness receipt](../../results/hg002_read_extract_20261010/readiness.json) records PacBio CCS/REVIO reads, not Illumina. The recent size/time check was metadata-only. | A short-read input or new file-integrity proof. Its reference/phase compatibility also remains a separate question. |
| Public 30× short reads | The new [input audit](../../results/hg002_illumina_header_20261122_run01/README.md) verifies one HG002 Illumina read group, the BAM header, a pinned BAI and a fixed indexed fetch: 299 alignment records in a 1 kb chr22 access-control interval. No alleles were inspected there. | Exact alignment-FASTA identity, experimental validation of every call, whole-file integrity, or identity with the dicast accuracy-run BAM. |

At an earlier inspection, local and remote research branch heads both pointed
to `9564085`. Concurrent project work later advanced the local head through
`d1be3a8`, which registers the shared-scope protocol. Recheck the live branch
and the other worker's result before acting. The current publication objective
remains unmet.

## Why this question is still conditional

[Alavi et al., dicast](https://doi.org/10.1186/s13059-026-04280-y) scores
candidates from Delly, Manta, Lumpy, GRIDSS and CNVnator, with a population
catalog also used in its HG002 evaluation. Its reported CMRG difference
between ordinary discovery and predefined-region scoring motivates a source
of missed candidates; it does **not** demonstrate a blind discovery gain.
Do not substitute Manta alone for the full dicast-like baseline in a gain
claim.

[Guo et al.](https://doi.org/10.1186/s13059-026-04219-3) already compared
14 short-read callers, including SvABA, and ensemble strategies using four
related Platinum Pedigree people. Thus SvABA is an **existing positive
control / feasibility probe**, not our new method, and adding another known
caller to an ensemble is not enough for novelty. The
[2026 short-read standards preprint](https://doi.org/10.64898/2026.10.13.758836)
also shows that representation and ensemble merging matter. A method claim
must beat appropriately run assembly callers and a sample-excluded catalog,
at a stated review burden, on independent evidence.

There is a concrete catalog-leakage risk. The [Ebert et al. supplement](https://eichlerlab.gs.washington.edu/eichler/pdfs/Ebert_Science_2021-Supp.pdf)
says HG002 data were included in the study's final dataset. This does not by
itself prove that every Ebert-derived catalog contains each HG002 allele.
Inspect the **exact** catalog and its discovery provenance. Removing HG002's
genotype column from a merged VCF does not remove alleles discovered from
HG002. Keep a clearly labeled inclusive-catalog sensitivity arm if useful;
do not call it an independent sample-excluded baseline without proof.

## Available input and fallback paths

1. **Preferred pilot input:** the [version-pinned Google Health NovaSeq BAM](https://storage.googleapis.com/brain-genomics-public/research/sequencing/grch38/bam/novaseq/wgs_pcr_free/30x/HG002.novaseq.pcr-free.30x.dedup.grch38.bam?generation=1607665356367383)
   is 43,667,905,004 bytes; its [pinned BAI](https://storage.googleapis.com/brain-genomics-public/research/sequencing/grch38/bam/novaseq/wgs_pcr_free/30x/HG002.novaseq.pcr-free.30x.dedup.grch38.bam.bai?generation=1607665356361183)
   is 9,390,960 bytes, with publisher MD5
   `d3bd1bf2c785da0226d37bb14a802553`. The audit matched all 3,366 ordered
   contig names and lengths to Broad and 1000 Genomes FASTA indexes; the BAM
   has no `M5` fields. A dictionary match is **not** sequence identity. Seek
   the original pipeline/reference provenance; until resolved, label this a
   conditional feasibility run and do not assert a reference-perfect score.
2. **Exact-reference fallback:** [NovaSeq R1](https://storage.googleapis.com/brain-genomics-public/research/sequencing/fastq/novaseq/wgs_pcr_free/30x/HG002.novaseq.pcr-free.30x.R1.fastq.gz?generation=1607665347333933)
   and [R2](https://storage.googleapis.com/brain-genomics-public/research/sequencing/fastq/novaseq/wgs_pcr_free/30x/HG002.novaseq.pcr-free.30x.R2.fastq.gz?generation=1607665347352230)
   returned HTTP 200 at 25,664,092,287 and 26,634,286,830 bytes. Align both
   once to one version-pinned, checksummed full GRCh38 FASTA; give every arm
   the same resulting BAM. Their naming and release support a source link,
   but verify read-set equivalence before claiming they reproduce the existing
   BAM. The [Broad FASTA](https://storage.googleapis.com/gcp-public-data--broad-references/hg38/v0/Homo_sapiens_assembly38.fasta?generation=1575676516681666)
   is an available candidate, 3,249,912,778 bytes; dictionary agreement is
   not proof it was used for the public BAM.
3. **Independent hosting/technology fallback:** NIST's [300× Illumina GRCh38 BAM](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/data/AshkenazimTrio/HG002_NA24385_son/NIST_HiSeq_HG002_Homogeneity-10953946/NHGRI_Illumina300X_AJtrio_novoalign_bams/HG002.GRCh38.300x.bam)
   and [BAI](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/data/AshkenazimTrio/HG002_NA24385_son/NIST_HiSeq_HG002_Homogeneity-10953946/NHGRI_Illumina300X_AJtrio_novoalign_bams/HG002.GRCh38.300x.bam.bai)
   returned 200; a 1,024-byte request returned 206. Their sizes are
   601,190,937,104 and 11,735,344 bytes. [GIAB's index](https://raw.githubusercontent.com/genome-in-a-bottle/giab_data_indexes/master/AshkenazimTrio/alignment.index.AJtrio_Illumina300X_wgs_novoalign_GRCh37_GRCh38_NHGRI_07282015.HG002)
   supplies whole-object MD5s. Indexed extraction and deterministic
   template-level downsampling may reduce transfer, but retain required
   mates, supplemental alignments and all relevant reference contigs; measure
   actual depth and data transferred. A partial range cannot verify a whole
   BAM MD5. It is a different library/alignment: do not mix its calls into the
   NovaSeq same-read comparison. The [HPRC 30× FASTQ pair](https://github.com/human-pangenomics/HG002_Data_Freeze_v1.0#hg002-data-freeze-v10-recommended-downsampled-data-mix)
   is another independent source route: its two public objects list
   42,868,243,557 and 45,882,070,975 bytes. Multipart ETags are not MD5s.
4. **Tool/source fallback:** the [dicast repository's pinned caller-fixture recipe](https://github.com/burgshrimps/dicast/blob/e88576e4d5dd791a956b7c1d46933078b050a82f/tests/data/callers/README.md)
   gives concrete caller invocations on a GIAB chr21 BAM slice. It is useful
   for software-interface checks, not a ready-made benchmark panel: some
   files are trimmed, the region was selected partly around demo loci, mates
   on other contigs were dropped and the reference was chr21-only. Its
   documented `samtools view -s 42.3` retains 30% of its input; if that input
   really is 300×, nominal depth would be about 90×, not 30×. The actual
   depth is unverified. Do not infer recall or absence from these fixtures.

On this check the laptop had about 14 GiB free. The cluster filesystem
reported 60 TiB free, but that is **not** the user's quota; `quota -s` did
not establish a limit. `sinfo` listed the `amd_256M` nodes with 128 CPUs and
257,204 MiB per node, plus larger-memory CPU nodes. These are node capacities,
not a promise of a particular allocation. The login node had Singularity on
`PATH`; samtools, bcftools and bedtools were not found on that `PATH`, which
does not exclude modules or other environments. Check quota, workspace expiry,
containers and network on the allocated compute node. Do not use the
unrelated Alice job or unproven workspaces. No GPU is needed for the initial
caller comparison.

## Runnable first work: fixed real-data diagnostic

### 1. Freeze the search space and prepare the inputs

Use the whole **chr21** as the discovery region, with the full reference and
full same-sample BAM available to each caller. Its GRCh38 length is
46,709,983 bases. Do not pass truth VCFs, truth coordinates, CMRG genes or
benchmark BEDs to a proposal caller. Chr21 was chosen here after checking
only benchmark BED metadata, not variant outcomes: the CMRG SV BED has 26
chr21 intervals totaling 384,173 bases. This is exploratory selection, not
a blinded preregistration or a representative chromosome sample. Another
worker's ongoing crosswalk may inspect these publicly known HG002 alleles
before any future run. The proposal *software* must still receive no truth
coordinates, but the pilot is exploratory for the project. The chr22 1 kb
access check is not the evaluation set.

Stage and record the BAM and BAI object generations, checksums and header;
pin software builds/container digests and the full FASTA plus its `.fai` and
BWA index. Confirm sequence identity or use the realignment fallback above.
If remote indexed access is unstable, stage the whole 43.7 GB BAM rather
than silently cropping reads. `samtools quickcheck` checks header/EOF, not
the entire BAM or sample identity. Preserve the 3,366-contig dictionary,
read groups, unmapped reads and mates; do not use a chromosome-only FASTA.

The following commands are a **handoff template, not commands executed by
this note**. Run only in an allocated compute environment after staging the
inputs. Set `WORK`, `BAM` and `REF` to absolute, verified paths and ensure
`configManta.py`, `bgzip`, `tabix` and `svaba` are from the recorded builds.
The storage and binaries must be checked first; these commands do not submit
a job. Manta 1.6.0 and SvABA 1.2.0 are concrete initial versions; validate
their native help and container behavior before freezing the run.

```bash
set -euo pipefail
WORK=/absolute/path/to/new-hg002-diagnostic
BAM=/absolute/path/to/verified/HG002.novaseq.30x.bam
REF=/absolute/path/to/verified/Homo_sapiens_assembly38.fasta
mkdir -p "$WORK/regions" "$WORK/svaba"
test -s "$BAM"
test -s "$BAM.bai"
test -s "$REF"
test -s "$REF.fai"
printf 'chr21\t0\t46709983\n' | bgzip -c > "$WORK/regions/chr21.bed.gz"
tabix -p bed "$WORK/regions/chr21.bed.gz"
configManta.py --bam "$BAM" --referenceFasta "$REF" \
  --callRegions "$WORK/regions/chr21.bed.gz" --runDir "$WORK/manta"
"$WORK/manta/runWorkflow.py" -m local -j 8
svaba run -t "$BAM" -G "$REF" -k chr21 -a "$WORK/svaba/chr21" \
  -p 8 -L 6 -I
```

The [SvABA 1.2.0 documentation](https://github.com/walaj/svaba/blob/v1.2.0/README.md)
describes its germline `-L 6 -I` recipe and `-k` region. `-I` changes
interchromosomal mate lookup; restrict this small diagnostic to simple DEL/INS
events and record that limitation. Save Manta's `candidateSV.vcf.gz` and
`diploidSV.vcf.gz`, plus SvABA's complete unfiltered and PASS VCFs and
`bps.txt.gz`. The Manta candidate file is pre-genotype output, not proof that
every internal proposal survived to disk. Save logs, versions, checksums,
wall/CPU time, peak RAM and transfer volume. Start with an 8-CPU allocation;
set memory/time only after a measured installation and input preflight rather
than claiming an unmeasured runtime. Continue to use full allocations
efficiently; scale only when measurements justify it.

### 2. Blindly generate the baseline and independent control

The first Manta/SvABA pair validates the interface and may expose a tangible
development example. **It is not the strong-baseline result.** On the same
read file, reference, whole-chr21 discovery space and a frozen set of versions,
add Dysgu and the other feasible dicast source callers: Delly, Lumpy, GRIDSS
and CNVnator. Preserve each caller's native emitted records, filter semantics,
unfiltered and PASS views where they exist, and a deterministic mapping from
normalization back to native IDs. GRIDSS breakends and symbolic insertions
need special handling; unresolved sequence/representation is `unknown`, not
an automatically absent allele. If a caller or normalizer cannot run, report
the missing baseline explicitly and do not make a full-union claim.

Before truth matching, freeze each caller output and the sample-excluded
population catalog/force-calling input, its source history, reference,
deduplication rule and versions. If no demonstrably sample-excluded catalog
can be built, the catalog-adjusted endpoint is **not evaluable**; continue a
clearly labeled caller-only feasibility check. If an inclusive catalog is
available, run it as a leakage-sensitive control, not as independent prior
information. Preserve the cost of candidate generation and catalog genotyping.

Only if the full caller-plus-catalog union leaves supported alleles absent
should a new prototype be considered. A concrete candidate is an
**ambiguity-aware read-rescue assembler**: across chr21, take QC-passing,
nonduplicate read templates with clipped, discordant, unmapped-mate or
multi-mapping evidence; retrieve mates from the full BAM; cluster breakpoint
evidence without any truth/caller VCF input; assemble local sequence and align
each contig against the *whole* reference including decoys/alternate contigs.
Require support from distinct read templates, retain all plausible loci and
abstain when sequence is not locus-identifying. Freeze clustering, assembly,
quality thresholds and resource limits without using scored truth outcomes.
This is an implementation hypothesis, not established novelty: GRIDSS,
SvABA and other assemblers must remain explicit comparators. If it merely
reproduces their candidates, stop the method path.

For a reproducible first prototype, assign each primary or supplementary
alignment to a template by read-group and QNAME; filter duplicate and QC-fail
templates, but retain MAPQ-zero evidence and unresolved mates. Form chr21
seed clusters from clipped/discordant anchors within 250 bp with at least
three distinct templates. Retrieve their mates and supplementary records
from the full alignment, and locally assemble the full template sequences
with a pinned assembler. Align each contig to the same full reference and
report all plausible placements before emitting a DEL/INS candidate. If
there are equally supported loci or no sequence-resolved alternate, emit an
explicit ambiguity/no-call record. The 250 bp and three-template values are
development defaults, not optimized or validated operating points. Save a
table containing cluster ID, template count, evidence categories, candidate
allele, alternate placements and abstention reason; keep read names out of
Git. Check on synthetic multi-mapping and duplicated-template controls that
one read pair cannot count twice and ambiguous loci cannot become certain.
The public BAM may not retain every secondary alignment: missing alternatives
must stay unknown, or be recovered by separately remapping the same FASTQs.

### 3. Score with explicit denominators and unknowns

Use the [GRCh38 CMRG SV VCF](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/CMRG_v1.00/GRCh38/StructuralVariant/HG002_GRCh38_CMRG_SV_v1.00.vcf.gz)
with its [CMRG BED](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/CMRG_v1.00/GRCh38/StructuralVariant/HG002_GRCh38_CMRG_SV_v1.00.bed),
and the [v5.0q SV VCF](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/HG002_GRCh38_v5.0q_stvar.vcf.gz)
with its [v5.0q SV BED](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/HG002_GRCh38_v5.0q_stvar.benchmark.bed).
All four URLs returned HTTP 200 in this check. Download and verify the
published checksums where supplied; record full hashes and the complete
VCF/BED versions. CMRG and v5.0q describe the **same HG002 individual** and
may share supporting data. Agreement is a conservative evidence tier, not
independent-donor validation. NIST describes v5.0q as a draft and recommends
review of putative FPs/FNs; see its [README](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/NIST_HG002_v5.0q_variant-benchmarksets_README.md).

The separate shared-scope protocol uses variants **over** 50 bp, raw REF-span
coverage and exact minimally trimmed matches. This proposal uses a different,
stricter flank rule and sequence-aware matching; reconcile and report both
denominators instead of silently substituting one for the other. Freeze the
following before the proposal is scored, while acknowledging any truth
already examined during the ongoing development crosswalk:

- **Frame:** sequence-resolved simple DEL and INS of at least 50 bp on
  chr21. For deletions require the entire reference span plus 50 bp flanks
  within both benchmark BEDs; for insertions require both 50 bp flanks.
  Record partial overlaps, complex/multiallelic events, symbolic/unresolved
  alleles and missing sequence separately. Group nearby components of a
  complex event as one locus for uncertainty; never treat each record as an
  independent example.
- **Truth reconciliation:** perform one-to-one, sequence-aware matching
  between CMRG and v5.0q, using a pinned Truvari version and NIST's `bench`
  plus `refine` guidance, with 2,000 bp candidate distance, 0.7 sequence and
  size similarity and explicit matching/contig rules. Preserve raw matches,
  complex conflicts, source-only events and events outside either BED.
  Remove `ALT=*` only in the documented bench-specific view; retain the
  untouched truth and the context needed for `refine`. Review disagreements;
  neither coordinate proximity nor the number of truth sources proves an
  allele. A secondary matcher or different thresholds are sensitivities, not
  an opportunity to choose a favorable answer.
- **Primary denominator:** the number of distinct, cross-supported,
  sequence-resolved, eligible CMRG/v5.0q alleles or complex-locus groups.
  Report CMRG-only, v5.0q-only and unresolved groups separately, including
  all exclusions. Detection is allele-candidate recall, not genotype
  accuracy. Preserve genotype as a separate field.
- **Baseline and increment:** for each eligible group, record each caller's
  emitted/PASS status, compatible catalog status, and the proposal's match.
  A positive increment requires a supported allele matched to a blind
  proposal and **not** to any complete baseline candidate or eligible catalog
  candidate. If any baseline has missing calls or an ambiguous match at that
  group, label the increment unresolved. Record candidates that match only a
  filtered caller separately from those absent from all emitted records.
- **Burden:** report total distinct candidate hypotheses by arm across the
  whole discovery region, including outside the truth mask, and the number
  needing review per extra supported eligible allele. Inside the paired
  callable territory, report unmatched, unknown and representation-conflict
  counts separately; an unmatched call is not automatically a proven false
  call in a draft benchmark. Do not hide candidate burden by scoring only
  easy truth loci. A later fixed-budget comparison requires a single frozen,
  defensible ranking rule and the same review budget for both arms.
- **Audit:** produce a complete per-locus evidence ledger, not a hand-picked
  success list, with read/contig evidence, native IDs, truth provenance,
  reference version, ambiguity flags and adjudication decisions. Any
  orthogonal long-read/assembly evidence must have its own provenance and
  reference reconciliation; the retained CCS BAM is not independent merely
  because it is a different technology. Do not train or tune on these scored
  cases and then present the same cases as validation.

## Decisions after the pilot

- **Proceed to a reviewed method design** only if there is a real,
  sequence-compatible blind candidate beyond the complete caller-plus-catalog
  baseline, its locus is adequately evidenced, and the extra review burden
  could plausibly be useful. This is a feasibility signal, not a publication
  result. Seek independent reviewer scrutiny before larger compute or
  accepting a positive result.
- **Stop this proposal** if a complete comparison shows no such candidate,
  if candidates require truth coordinates, if the full baseline already
  emits them, or if evidence supports multiple loci with no useful way to
  abstain. A very small or ineligible chr21 denominator is **inconclusive**;
  predefine a broader fixed territory before inspecting its outcomes, or
  move to a different question. One missing catalog or failed installation
  is a missing input, not a biological failure.
- **For publication:** require a locked design, strong native and ensemble
  baselines including dicast where its input contract is met, measured burden,
  an appropriate independent truth strategy and at least one untouched,
  unrelated evaluation donor. [Platinum Pedigree](https://github.com/Platinum-Pedigree-Consortium/Platinum-Pedigree-Datasets)
  offers a possible HG002-independent follow-up, subject to exact read/truth
  and callable-mask checks. Its relatives are clustered, not independent
  population replicates; Guo et al. already studied four of them. New
  research needs a contribution beyond their benchmarking. Use a meaningful
  effect and donor/locus uncertainty, not a significance test that treats
  reads or related events as independent people.

## Provenance of this handoff

I read the goal, `PROGRESS.md`, current 22 November notes and selected prior
source-gate records. I checked the cited primary publications, the NIST
benchmark README, public-source metadata and reference index. I used Parallel
web search and direct HTTP as alternatives when a separate web reader could
not open the publisher/PMC pages. I inspected CMRG BED interval metadata only,
not truth variant outcomes. I also checked read-only cluster filesystem and
`PATH` metadata. No new repo code, result packet, job, commit or push was
made by this handoff.

**Requested orchestration model:** GPT-6.1 Terra, maximum effort. The
effective serving model and reasoning effort were not independently verifiable
from the runtime available to this task; do not treat the requested role as an
attestation.
