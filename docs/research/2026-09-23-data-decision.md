# Data decision: keep the engineering fixture, acquire new scientific cohorts

**Date:** 2026-09-23
**Status:** development benchmark and HGSVC3 callset staged and checked;
63 HGSVC3 donors have matching public 30× CRAM index entries, but bulk transfer
is on hold after reference-M5 and callable-region checks failed their gates.

## Decision

New raw short-read alignments are required. The historical multi-sample source
workspaces expired, and their surviving derived tensors encode the old
representation. The recovered 3 Mb HG002 BAM can validate tensorization and
candidate-generation software, but cannot support a model comparison. HG002
and the earlier panel have also been examined repeatedly in this project, so
they are development data for the restart.

The age of a BAM alone does not make it useless. What matters is whether its
reference, coverage, integrity, truth set, candidate generation, and donor
separation can answer the experiment. The public HG002/hs37d5 pilot passes the
engineering checks; it fails the sample-size and untouched-donor requirements
for a publication-level positive claim.

## Verified current holdings

| Item | Evidence | Permitted role |
|---|---|---|
| HG002 hs37d5 three-region pilot | `/scratch/igorno-alignssl_restart_20260922/recovery-pilot-v1/HG002.pilot.bam`, 1,293,795 reads, chr1/10/20 10–11 Mb; integrity and depth oracle documented in `RESTART_STATE.md` | Deterministic engineering fixture and caller smoke test |
| GIAB HG002 Tier1 SV v0.6 | Original source and file digests in the pilot `manifest.json`; 14 `SVTYPE=DEL` records ≥50 bp in those windows | Historical/development comparison only |
| GIAB HG002 SV v5.0q GRCh37 | NIST [release directory](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/) and [usage README](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/NIST_HG002_v5.0q_variant-benchmarksets_README.md); staged at `/scratch/igorno-alignssl_restart_20260922/giab-hg002-v5-grch37` | Current HG002 development truth, paired with its SV benchmark BED |
| Manta 1.6.0 | Official [release](https://github.com/Illumina/manta/releases/tag/v1.6.0); cluster Singularity image `/home/igorno/alignssl_restart_20260922/tools/manta-1.6.0--py27h9948957_6.sif`, SHA-256 `283022f0b46085579be8f13c356e7b513763cbb3d4f01fd3be392260d0ab330f`; `configManta.py --version` prints `1.6.0` | Frozen upstream candidate generator for the development pilot |
| HGSVC3 v1.0 GRCh38 SV callset | Official [release README](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/README_Variant_Calls_1.0.md) and [manifest](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/MANIFEST_Variant_Calls_1.0); sequence-resolved SV VCF, tabix index, README, and manifest staged at `/scratch/igorno-alignssl_restart_20260922/hgsvc3-v1-grch38-sv` | Independent cohort feasibility only until alignments and callable masks are verified |

The v5.0q VCF, index, and SV benchmark BED match NIST's published MD5 values;
the VCF passes gzip integrity. The staged files and SHA-256 digests are recorded
in `SHA256SUMS`. NIST's downloaded README has MD5
`5edb3da273b4923e3d6d04cc9e709b16`, whereas its `checksum.md5` lists
`f172a34de4bf9155450c58e7f223adac`. This discrepancy is isolated to the
README in our check; `README_CHECKSUM_NOTE.txt` preserves it. Do not describe
the entire release as checksum clean.

The v5.0q GRCh37 VCF names the sample `HG002` and uses primary contigs `1`–`22`,
`X`, and `Y`. Within the three pilot intervals, it has 11 `SVTYPE=DEL` records
with reference-span length ≥50 bp (1 on chr1, 7 on chr10, 3 on chr20). The
benchmark BED intersects 2,997,535 of the 3,000,000 pilot bases. These are
descriptive counts, not performance observations or a power calculation.

The HGSVC3 staged sequence-resolved VCF and index match the release manifest's
MD5 entries and pass gzip integrity. The VCF has 65 named samples, primary
contigs named `chr1` and so on, and only a `GT` FORMAT field. Its VCF SHA-256
is `cbdf253d1796b5cbcbaf17db072ebaa64a44204a263389522d64bc36292faac2`.
The official README says `.` marks an uncallable haplotype, but this is
variant-record callability, not a genome-wide confident-negative mask.

An exact sample-ID join of the 65 HGSVC3 VCF columns to the official IGSR
[2,504-sample](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/1000G_2504_high_coverage.sequence.index)
and [698-related-sample](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/1000G_698_related_high_coverage.sequence.index)
30× sequence indexes found 63 Illumina CRAM entries. The unmatched names are
`NA21487` and `NA24385` (HG002). The 698 index contains an unnamed empty field
after `POPULATION` in its data rows; `scripts/audit_hgsvc3_cohort.py` accounts
for this and rejects other row-width mismatches. The source-index SHA-256
digests are `0ac5fdda0b60b6575b1867827f53e39d723f915b325b10bf023b2dc3d71c08f2`
(2,504) and `d76df08d0dc227ca7b6977e74c3e835f70598b300ed20e391299f6c5cb1b4dcc`
(698). The IGSR [pedigree index](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000G_2504_high_coverage/working/1kGP.3202_samples.pedigree_info.txt)
identifies three parent-child trios within the truth roster: HG00512/13/14,
HG00731/32/33, and NA19238/39/40. Relatedness beyond those stated links
remains to be assessed before donor splits.

The indexed `HG00512` CRAM and CRAI respond to HTTP HEAD with byte ranges;
their reported sizes are 15,737,734,304 and 1,401,728 bytes respectively.
Reading the remote CRAM header with `samtools view -H` confirms `chr1` through
at least `chr4` primary contig names, with `chr1` length 248,956,422 and M5
`6aef897c3d6ff0c78aff06ac189178dd`. This is a metadata access check, not
a file-integrity or complete reference-compatibility verification. One 15.7 GB
donor already makes full-cohort transfer a sizeable decision.

Subsequent primary-source audits found no donor-wide callable BED in the
inspected HGSVC3 v1.0 release inventories and an exact M5 mismatch between the
HGSVC VCF header and the official IGSR CRAM reference dictionary on 18 of 25
canonical contigs, despite equal lengths. The chr1 mismatch was independently
reproduced from the staged VCF header and official dictionary. See the
[callability](2026-09-23-hgsvc3-callability-audit.md) and
[reference](2026-09-23-hgsvc3-reference-audit.md) audits. The reason for the
digest differences and availability of PAV callable output in uninspected
working archives remain unknown. Do not bulk-download the 30× cohort on the
assumption that GRCh38 naming alone proves compatibility.

NIST calls v5.0q a **draft**, assembly-derived benchmark and recommends using
the VCF and BED together. Its [README](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/NIST_HG002_v5.0q_variant-benchmarksets_README.md)
warns that complex variants and different representations need careful
comparison and recommends `truvari bench --refine` (or comparable tools) plus
manual curation of a subset of putative errors. Candidate-level labels must
therefore be versioned and checked against a call-set comparison, not assigned
by simple interval overlap alone.

## Staged acquisition plan

1. **Metadata first.** Inspect the [HGSVC3 v1.0 assembly-derived GRCh38
   callset](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/README_Variant_Calls_1.0.md),
   its sample manifest, per-sample no-call/callable regions, and exact overlap
   with public high-coverage Illumina alignments. The sample-ID overlap and
   one remote header are checked above. The HGSVC3 release describes calls
   from 65 phased genomes and marks uncallable haplotypes with `.`; this does
   not by itself guarantee a confident negative region for every donor.
2. **Development data.** Retrieve a label-blind, prespecified larger HG002
   region or whole alignment as needed, and generate a frozen Manta candidate
   pool. Use v5.0q paired VCF/BED for HG002 development, with v0.6 as a
   sensitivity analysis. Retain all emitted candidates and original caller
   scores. The small pilot is only a software smoke test.
3. **Independent donors.** Select genetically independent HGSVC donors with
   matching short-read data, verified reference compatibility, and defensible
   per-donor callable regions. Assign donors to training/development and an
   untouched confirmation set before comparing methods. Do not use a
   population-genotyped short-read SV callset as if it were assembly-derived
   truth. If HGSVC3 lacks a usable negative/confident mask, obtain or derive one
   from the assembly alignment with a documented validation gate, or select a
   different orthogonal benchmark.
4. **Reference gate before alignment transfer.** Obtain the exact HGSVC
   `hg38.no_alt.fa.gz` or authoritative dictionary, reconcile its M5s with the
   IGSR reference, and locate or validate donor-specific callable regions.
   Only then stage one donor's indexed alignment from the official source,
   verify published checksums or a complete read traversal, reference sequence
   MD5s, contig names, coverage, and Manta output. Determine compressed size
   and transfer speed before scaling. The past parallel range downloader
   produced corrupt full-size BAMs, so byte count and `quickcheck` alone are
   insufficient.
5. **Compute gate.** Run caller-score, depth-only, logistic regression, random
   forest, and gradient-boosted-tree baselines on the frozen candidate manifest
   before spending substantial GPU time. Only a fair scratch versus SSL
   comparison can establish value from pretraining.

The bounded Manta fixture job `1598015` failed before startup on `hydra-n12`
with scheduler signal 53. A single replacement job, `1598016`, is queued on
`hydra-n1` in the `galaxy` partition; it has produced no candidate VCF yet.
The fixture run is deliberately too small for a scientific score.

The exact confirmation donors and full-data transfer size remain open until
per-donor callable masks, pedigree separation, and complete reference
compatibility have been checked. The 63 CRAM index records establish a route
to new data, not a ready-to-train cohort.
