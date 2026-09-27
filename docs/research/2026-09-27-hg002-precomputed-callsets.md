# HG002 precomputed short-read SV candidate callsets for a v5.0q ceiling pilot

**Checked:** 2026-09-27
**Scope:** First-party published/released HG002 caller outputs on GRCh37 or GRCh38 that could support a low-cost candidate-recall ceiling check against the NIST HG002 v5.0q SV truth. Metadata only: no candidate VCF or multi-gigabyte archive was downloaded; no caller or cluster job was run.

## Decision

**Scoped go for a small exploratory pilot, after checking VCF headers and reference dictionaries.** The Parliament2 publication repository contains six historical short-read caller outputs from HG002 at about 35× on hs37d5, with individual VCF sizes and Git object IDs available. A 2026 HitSV paper and its linked results repository identify 35× and 60× HG002 Illumina short-read VCFs on GRCh38; their Git LFS pointers expose payload sizes and SHA-256 values.

This is **not yet a verified exact-reference-matched panel**: the candidate VCF bodies and contig dictionaries have not been inspected. The Parliament2 documentation states caller versions, but there is no per-file execution manifest binding those versions to each VCF. The HitSV paper says its source code is version 2.0, but the released callset files are not tied to a specific executable commit in the metadata inspected here. Do not call either set a contemporary, independently validated test panel.

**No-go for a contemporary multi-caller panel under the current no-large-download bound.** A 2026 paper reports multi-technology SV VCFs in a single 3.33 GB Zenodo `sv.gz` archive. Its record supplies an archive checksum but not per-caller member paths or member checksums. I did not download or inspect that archive. This is a scoped operational limit, not a claim that no other compatible callsets exist.

## Truth files are separate from caller candidates

NIST's [HG002 v5.0q release directory](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/) has SV truth VCFs and their paired benchmark BEDs for both builds:

| Truth build | Truth VCF | Paired benchmark BED | MD5 from NIST `checksum.md5` |
|---|---|---|---|
| GRCh37 | [HG002_GRCh37_v5.0q_stvar.vcf.gz](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/HG002_GRCh37_v5.0q_stvar.vcf.gz) | [HG002_GRCh37_v5.0q_stvar.benchmark.bed](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/HG002_GRCh37_v5.0q_stvar.benchmark.bed) | VCF `66ae1ae0915903d91839226f5ace9d76`; BED `679b4223190432349be5ce8b28db3048` |
| GRCh38 | [HG002_GRCh38_v5.0q_stvar.vcf.gz](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/HG002_GRCh38_v5.0q_stvar.vcf.gz) | [HG002_GRCh38_v5.0q_stvar.benchmark.bed](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/HG002_GRCh38_v5.0q_stvar.benchmark.bed) | VCF `34dbeeac5eb3fc09e94c5cb8cfe9e24f`; BED `55fc11c80ff376c0a8da99d0c69004f3` |

These are truth and evaluation-region files, not caller output. Likewise, the older `HG002_SVs_Tier1_v0.6.vcf.gz` in NIST's integration release is a historical benchmark truth VCF. The caller candidates below are separate files in the Parliament2 results repository.

## Verified candidate sources

### Parliament2: six historical short-read callers, hs37d5 / GRCh37

The [Parliament2 paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7751401/) describes the HG002 benchmark as Illumina HiSeq X data, about 35×, mapped to hs37d5, and explicitly points to its [individual caller result files](https://github.com/slzarate/parliament2/tree/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs). Its documentation identifies the files as individual tool outputs and lists the caller versions below. The paper describes these as benchmark results/caller outputs, while the NIST v0.6 file is the truth set.

The GitHub tree was inspected at commit `b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6`. Sizes below are bytes. “Git blob SHA-1” is the repository object ID, not an independently computed SHA-256 of the downloaded file.

| Caller; version stated in repository README | Candidate VCF and metadata |
|---|---|
| BreakDancer 1.4.3 | [breakdancer.vcf](https://raw.githubusercontent.com/slzarate/parliament2/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs/HG002-NA24385-50x.70_percent.markdup.realigned.breakdancer.vcf) — 736,797 bytes; blob SHA-1 `42a6cee49cd96ed03a222694c66b372aa7264a9b` |
| BreakSeq2 2.2 | [breakseq.vcf](https://raw.githubusercontent.com/slzarate/parliament2/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs/HG002-NA24385-50x.70_percent.markdup.realigned.breakseq.vcf) — 256,452 bytes; blob SHA-1 `67996cd25993db00292b3a9fd0d242d1783de65c` |
| CNVnator 0.3.3 | [cnvnator.vcf](https://raw.githubusercontent.com/slzarate/parliament2/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs/HG002-NA24385-50x.70_percent.markdup.realigned.cnvnator.vcf) — 1,283,026 bytes; blob SHA-1 `597a44c5af988bc647dc4478221d6243c5d6b3ba` |
| Delly 0.7.2 | [deletion](https://raw.githubusercontent.com/slzarate/parliament2/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs/HG002-NA24385-50x.70_percent.markdup.realigned.delly.deletion.vcf) — 2,864,514 bytes; blob SHA-1 `84a419159c591686962c511fcdbe893221ccae86`; [duplication](https://raw.githubusercontent.com/slzarate/parliament2/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs/HG002-NA24385-50x.70_percent.markdup.realigned.delly.duplication.vcf) — 579,671 bytes; `fff5ca2f5839a9d20f2d19f258a0cceb55975f21`; [insertion](https://raw.githubusercontent.com/slzarate/parliament2/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs/HG002-NA24385-50x.70_percent.markdup.realigned.delly.insertion.vcf) — 1,581,178 bytes; `48245056f6378da25317c7e0060e8dbb44117c9a`; [inversion](https://raw.githubusercontent.com/slzarate/parliament2/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs/HG002-NA24385-50x.70_percent.markdup.realigned.delly.inversion.vcf) — 614,297 bytes; `7613f82a62f3618cd9d5f383f766e17e080e5e75` |
| LUMPY 0.2.13 | [lumpy.vcf](https://raw.githubusercontent.com/slzarate/parliament2/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs/HG002-NA24385-50x.70_percent.markdup.realigned.lumpy.vcf) — 503,986 bytes; blob SHA-1 `1a5a3602f88eeabf9de13c7c4ce803235196f042` |
| Manta 1.4.0 | [manta.diploidSV.vcf.gz](https://raw.githubusercontent.com/slzarate/parliament2/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs/HG002-NA24385-50x.70_percent.markdup.realigned.manta.diploidSV.vcf.gz) — 812,286 bytes; blob SHA-1 `0d3cbe9c5e625de07fd17cb240f0e75c2bb831af` |

The selected raw caller files total **9,232,207 bytes**. The repository also has `.svtyped.vcf` and `combined.genotyped.vcf` outputs; they are downstream genotyped/combined artifacts and should not be substituted silently for the individual raw caller VCFs in a discovery-recall ceiling.

**Compatibility and provenance caveat:** the paper reports hs37d5, which is GRCh37-based and therefore offers build-level coordinate compatibility with the NIST GRCh37 truth. Exact reference sequence identity, contig naming, and candidate VCF headers were not checked. The repository README lists tool versions, but no per-file run manifest was found in the inspected paper/repository metadata to prove those exact versions generated each committed VCF. The repository README also describes its code tree as a fork under construction. Treat this as a useful historical multi-caller panel, not a current state-of-the-art panel.

### HitSV: two newer short-read callsets, GRCh38

The [HitSV paper](https://assets-eu.researchsquare.com/files/rs-8913458/v1_covered_2bd3a889-d877-43ab-a121-b9c0cc14aeb0.pdf) states that the HG002 35× and 60× Illumina short-read datasets were aligned to GRCh38 with decoy sequences using BWA-MEM. It reports benchmarking HitSV alongside Manta, Delly, and Lumpy, but the linked [results repository](https://github.com/hitbc/HitSV_call_results/tree/25428c7a4eb7191ef54f69c38f4f51c558d73f19/HG002/HG002-SRS) exposes the two HitSV SRS VCFs below; this checked inventory does not provide the comparison callers' VCFs.

| HG002 short-read candidate VCF | Payload size | SHA-256 from Git LFS pointer | Access |
|---|---:|---|---|
| `HG002_SRS35X_asm5.vcf.gz` | 5,288,143 bytes | `9cff44816f1706d59df1def1f03a313c7287dc26ff27e5369586525f4d2c696c` | [GitHub file](https://github.com/hitbc/HitSV_call_results/blob/25428c7a4eb7191ef54f69c38f4f51c558d73f19/HG002/HG002-SRS/HG002_SRS35X_asm5.vcf.gz) |
| `HG002_SRS60X_asm5.vcf.gz` | 6,323,674 bytes | `3dac398e6a2edecc6db64ef4234f0e0325401d460326be21bb8ed2547ad5fc96` | [GitHub file](https://github.com/hitbc/HitSV_call_results/blob/25428c7a4eb7191ef54f69c38f4f51c558d73f19/HG002/HG002-SRS/HG002_SRS60X_asm5.vcf.gz) |

The binary payloads are in Git LFS; the small pointer records, not the VCF bodies, were inspected. The paper's code-availability section says source code “v2.0”; the code repository has later tags as well. The result metadata does not identify the exact executable tag/commit used for these two VCFs. The filename token `asm5` is a HitSV alignment preset, not the reference-build designation. The paper's GRCh38 statement is the build evidence. Exact sequence-dictionary match to the NIST GRCh38 truth remains unchecked.

The paper evaluates against its NIST-Q100 v1.1 benchmark, so these are an already-published benchmark input/output context. Reusing the callsets against v5.0q can be a pipeline/ceiling pilot, but should not be presented as an independent replication or novel comparison without checking truth-version overlap and caller provenance.

## Newer multi-caller package that exceeds this task's download bound

The 2026 [Genome Biology study](https://doi.org/10.1186/s13059-026-04048-4) describes short-read SV callsets from a MetaSV workflow (MetaSV 0.5.4 integrating Delly, Lumpy, Manta, WHAM, BreakSeq2, and CNVkit), plus DRAGEN SV 4.3.13 and Dysgu 1.6.1. It reports linear alignment to GRCh37 decoy (`hs37d5`) and benchmarking against T2T-Q100 v1.1. Its [Zenodo record](https://zenodo.org/records/18868532) says the SV VCF files are available, but the record groups them in `sv.gz` (**3,329,540,940 bytes**, MD5 `093a0f10661014fb820e0f776891a7a9`). This is not a per-caller manifest: the archive member names, individual VCF sizes/checksums, and exact run-to-caller mapping were not inspected. No archive or caller file was downloaded. Under the current bound, this source is **not an actionable cheap pilot input**; it remains a possible follow-up only if selective files can be obtained without retrieving the full archive.

## Pilot conditions and limits

If proceeding with the small sources above, first verify each VCF header against the chosen NIST v5.0q build: sample name, contig names/lengths, reference/build declarations, and whether decoy/alternate contigs occur. Keep the NIST truth VCF paired with its matching benchmark BED. Restrict recall to the truth variants inside that BED and report caller-level recall and candidate-union recall separately. Do not turn unmatched regions or absent calls into negative training labels; this is a candidate-availability ceiling only, not an estimate of classifier precision or evidence that a missing truth allele is callable from short reads.

The older Parliament2 calls and modern HitSV callsets differ in data provenance, reference handling, caller generation, and caller version certainty. Report them as separate evidence strata rather than pooling them as a single controlled caller benchmark. No recall numbers were computed in this research note.

## Sources and metadata checks performed

- NIST first-party [v5.0q release directory](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/) and [checksum manifest](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/checksum.md5).
- Parliament2 [publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC7751401/), [pinned result tree](https://github.com/slzarate/parliament2/tree/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/benchmarking_data/hg002_benchmarks/sv_caller_outputs), and [pinned README](https://github.com/slzarate/parliament2/blob/b6bd509e954cf5aeae508ce1d03bdd6690c3bdb6/README.md).
- HitSV [paper PDF](https://assets-eu.researchsquare.com/files/rs-8913458/v1_covered_2bd3a889-d877-43ab-a121-b9c0cc14aeb0.pdf), [caller source](https://github.com/hitbc/HitSV), and [pinned HG002 SRS results](https://github.com/hitbc/HitSV_call_results/tree/25428c7a4eb7191ef54f69c38f4f51c558d73f19/HG002/HG002-SRS). GitHub API file metadata and the two 132-byte LFS pointer records supplied the payload byte counts and SHA-256 values above.
- 2026 Genome Biology [paper](https://doi.org/10.1186/s13059-026-04048-4) and [Zenodo record metadata](https://zenodo.org/records/18868532).

Only web pages, repository trees, file metadata, manifests, and LFS pointers were read. No candidate VCF body, BAM/CRAM, reference FASTA, or multi-gigabyte archive was downloaded; no cluster resource was used.
