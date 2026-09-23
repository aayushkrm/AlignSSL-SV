# GIAB v5.x multi-donor SV pilot feasibility

**Checked:** 2026-09-24
**Question:** Does any GIAB v5.x structural-variant benchmark donor other than HG002 have a matched public short-read WGS alignment, sequence-resolved SV truth, and paired benchmark BED on the same reference, suitable for a cheap candidate-recall pilot?

## Recommendation

**No-go for an independent GIAB v5.x SV candidate-recall pilot using HG005 or HG007.** NIST's current whole-genome assembly-based SV release is HG002 v5.0q. GIAB HG005 and HG007 do have public Illumina WGS alignments and v4.2.1 VCF/BED pairs on GRCh37 and GRCh38, but the v4.2.1 README defines those calls and regions as a *small-variant* benchmark. I found no HG005 or HG007 v5.x SV truth VCF/BED pair.

There is a possible **I/O-only** pilot using a small indexed region of either WGS alignment, but no SV recall result can be measured from these donors against GIAB truth. The BAMs are also exceptionally large as whole files, and exact reference-sequence identity has not been verified from their BAM headers.

## Verified evidence

### What GIAB currently releases

NIST's [GIAB product page](https://www.nist.gov/programs-projects/genome-bottle), updated 2026-05-12, identifies the new assembly-based small-variant and SV benchmark as **HG002 v5.0q**. The same page describes **v4.2.1 for all seven GIAB samples on GRCh37 and GRCh38 as small-variant benchmarks**. The [live GIAB release index](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/) separates the [Chinese trio](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/) from the [Ashkenazi trio](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/).

The sample release directories are decisive for the two candidates: [HG005 / NA24631](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/HG005_NA24631_son/) lists NISTv3.3, NISTv3.3.2, NISTv4.2.1, and `latest`; [HG007 / NA24695](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/HG007_NA24695_mother/) lists NISTv3.3.2, NISTv4.2.1, and `latest`. Neither directory lists a v5.x release.

The [HG005 v4.2.1 README](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/HG005_NA24631_son/NISTv4.2.1/README_v4.2.1.txt) says the release contains high-confidence SNV, small-indel, and homozygous-reference calls; it says the VCF and BED are intended to be used together for **small-variant** benchmarking. It lists HG005 and HG007 among the seven samples and states that these calls are available on both GRCh37 and GRCh38. The HG007 release has the same README and benchmark scope. Thus the existence of a generic `benchmark.vcf.gz` plus `benchmark.bed` at v4.2.1 does not make these SV truth sets.

### HG005 and HG007 data that do exist

GIAB's [official alignment index repository](https://github.com/genome-in-a-bottle/giab_data_indexes/tree/master/ChineseTrio) indexes Illumina WGS BAMs for both donors, aligned to GRCh37 (`hs37d5`) and GRCh38. Below are the GRCh38 alignments and the v4.2.1 GRCh38 small-variant pairs. MD5 values are copied from the first-party GIAB alignment indexes and per-sample `md5.in` manifests.

**HG005 / NA24631 (Chinese-trio son).** The [GIAB alignment index entry](https://raw.githubusercontent.com/genome-in-a-bottle/giab_data_indexes/master/ChineseTrio/alignment.index.ChineseTrio_Illumina300X100X_wgs_novoalign_GRCh37_GRCh38_NHGRI_04062016.HG005) lists both builds. Its [GRCh38 BAM](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/data/ChineseTrio/HG005_NA24631_son/HG005_NA24631_son_HiSeq_300x/NHGRI_Illumina300X_Chinesetrio_novoalign_bams/HG005.GRCh38_full_plus_hs38d1_analysis_set_minus_alts.300x.bam) has MD5 `50080d14ba49462cfc6348e1fb41b5b3`; its [BAI](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/data/ChineseTrio/HG005_NA24631_son/HG005_NA24631_son_HiSeq_300x/NHGRI_Illumina300X_Chinesetrio_novoalign_bams/HG005.GRCh38_full_plus_hs38d1_analysis_set_minus_alts.300x.bam.bai) has MD5 `2d38162ba61e909d08e4ed438096174e`. A metadata-only HTTP HEAD returned 200, byte-range support, and a BAM `Content-Length` of 668,998,775,517 bytes.

The paired v4.2.1 files are [`HG005_GRCh38_1_22_v4.2.1_benchmark.vcf.gz`](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/HG005_NA24631_son/NISTv4.2.1/GRCh38/HG005_GRCh38_1_22_v4.2.1_benchmark.vcf.gz) (MD5 `35fe853b7e8d979daa91033ed6863e98`) and [`HG005_GRCh38_1_22_v4.2.1_benchmark.bed`](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/HG005_NA24631_son/NISTv4.2.1/GRCh38/HG005_GRCh38_1_22_v4.2.1_benchmark.bed) (MD5 `f06ec2339592168a75ad4236b87cb2a3`). The source manifest is [HG005 `md5.in`](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/HG005_NA24631_son/NISTv4.2.1/md5.in). On GRCh37, the matching v4.2.1 VCF/BED MD5s are `5902ae1c99f4376c8fdced7f641c4ba0` and `85533ad71474146e2a4e95f10e559b68`.

**HG007 / NA24695 (Chinese-trio mother).** The [GIAB alignment index entry](https://raw.githubusercontent.com/genome-in-a-bottle/giab_data_indexes/master/ChineseTrio/alignment.index.ChineseTrio_Illumina300X100X_wgs_novoalign_GRCh37_GRCh38_NHGRI_04062016.HG007) lists both builds. Its [GRCh38 BAM](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/data/ChineseTrio/HG007_NA24695-hu38168_mother/NA24695_Mother_HiSeq100x/NHGRI_Illumina100X_Chinesetrio_novoalign_bams/HG007.GRCh38_full_plus_hs38d1_analysis_set_minus_alts.100x.bam) has MD5 `3b8442105a4a45f71c3c1bda8af238dd`; its [BAI](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/data/ChineseTrio/HG007_NA24695-hu38168_mother/NA24695_Mother_HiSeq100x/NHGRI_Illumina100X_Chinesetrio_novoalign_bams/HG007.GRCh38_full_plus_hs38d1_analysis_set_minus_alts.100x.bam.bai) has MD5 `0c218cecd8cde9ad272de6d77bbd110f`. Metadata-only HTTP HEAD returned 200, byte-range support, and a BAM `Content-Length` of 244,218,496,410 bytes.

The paired v4.2.1 files are [`HG007_GRCh38_1_22_v4.2.1_benchmark.vcf.gz`](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/HG007_NA24695_mother/NISTv4.2.1/GRCh38/HG007_GRCh38_1_22_v4.2.1_benchmark.vcf.gz) (MD5 `336f8cf6806521618779b6c5f4eadeb7`) and [`HG007_GRCh38_1_22_v4.2.1_benchmark.bed`](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/HG007_NA24695_mother/NISTv4.2.1/GRCh38/HG007_GRCh38_1_22_v4.2.1_benchmark.bed) (MD5 `6239fad8618396f9f6a269070fede44b`). The source manifest is [HG007 `md5.in`](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/ChineseTrio/HG007_NA24695_mother/NISTv4.2.1/md5.in). On GRCh37, the matching v4.2.1 VCF/BED MD5s are `77fdf6c8a1c7ed7405fbf8bc4877d3d4` and `c716000305a3f834b2ba374cf9e6cd37`.

The two BAM sizes above are from HEAD response headers, not downloads. The available BAI files and byte-range response make a bounded interval read plausible, but no remote regional fetch or tool-level range query was tested.

### The v5.x SV control

The only current v5.x SV resource found is [HG002 v5.0q](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/). Its [first-party README](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/NIST_HG002_v5.0q_variant-benchmarksets_README.md) identifies the release as a **draft**, assembly-based benchmark built from the T2T-HG002 Q100 V1.1 assembly, and says its VCF and BED are intended to be paired for SV evaluation. The README was updated 2026-07-17. For reference, the GRCh38 SV BED MD5 is `55fc11c80ff376c0a8da99d0c69004f3` and the GRCh38 SV VCF MD5 is `34dbeeac5eb3fc09e94c5cb8cfe9e24f`, per the [checksum.md5 manifest](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/checksum.md5). Equivalent GRCh37 files are listed in the same directory and manifest.

NIST cautions that v5.0q is under active development, that some regions may admit alternative assembly-to-reference alignments, and that complex SVs are included. It recommends comparison tools that handle complex variants and manual review of a subset of apparent false positives/negatives. These caveats do not provide a corresponding v5.x truth set for HG005 or HG007.

## Independence, overlap, and limitations

- **HG005 and HG007 are not independent of each other.** The NIST release tree labels them son and mother; HG006 is the father. Keep all three grouped if defining independent train/validation/test donors.
- **GIAB HG005 is not HGSVC/IGSR HG00512.** NIST's [FAQ](https://www.nist.gov/programs-projects/faqs-genome-bottle) explicitly says GIAB HG005 / NA24631 and IGSR-HGSVC HG00512 are different people from different Chinese trios. The project's existing [HG00512 reference audit](2026-09-23-hgsvc3-reference-audit.md) therefore does not establish a GIAB HG005 alignment. The matching GIAB WGS paths are the ones indexed above.
- **Same build is not yet verified identical sequence.** GIAB labels the alignments GRCh37/GRCh38 and the v4.2.1 truth by the same build names. The BAM paths specify `hs37d5` or `GRCh38_full_plus_hs38d1_analysis_set_minus_alts`, while the v4.2.1 files are named `GRCh37_1_22` / `GRCh38_1_22`. I did not read BAM headers or compare sequence dictionaries/M5 values, so exact reference identity remains unverified.
- **Whole-file download is not cheap.** The listed GRCh38 BAMs are about 669 GB (HG005) and 244 GB (HG007), decimal. A small interval may avoid most transfer, but the cost and feasibility of that path have not been measured.
- **No SV recall labels.** The v4.2.1 VCF/BED pairs support small-variant benchmarking, not a sequence-resolved SV recall score. Candidate overlap or false-negative counts were not computed because no candidate callset was in scope.

## Go/no-go

**No-go** for claiming or measuring independent GIAB v5.x SV candidate recall on HG005 or HG007: the required SV truth/BED pair is absent, and the two donors are first-degree relatives. A small indexed alignment read can be used only as a technical I/O smoke test, with exact BAM/reference identity checked before interpretation. For an SV feasibility result, use a donor with an independently documented SV truth VCF and paired benchmark BED on the same sequence reference; none among non-HG002 GIAB v5.x donors was verified here.

## Research bounds

Sources were limited to NIST/GIAB release pages, their READMEs and MD5 manifests, and the GIAB-maintained alignment index. I read small metadata and manifests and issued HEAD requests for the two GRCh38 BAMs/BAIs. I did not download BAM, VCF, BED, or reference-sequence data, inspect BAM headers, fetch genomic intervals, or run cluster jobs.
