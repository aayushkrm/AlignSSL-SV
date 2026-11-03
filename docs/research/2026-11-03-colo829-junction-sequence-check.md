# COLO829 der(3) junction sequence check

**2026-11-04 main audit: interpretation under review.** The observations below
are retained, but the J1 statement that both VCFs agree with the contig is not
established: the chr10 record has REF `T` and local ALT replacement `G`, while
the contig base aligned there is `T`. The J3 mate records carry reverse-
complemented 11-base literals, so their orientation relative to the derivative
must be checked separately before saying both spell the same junction. The J2
equivalence interpretation also needs an independent sequence-level check.
Do not use any of these three interpretations as accepted truth. The worker
stopped with a usage-limit error before this discrepancy could be resolved.
The [synthetic source replay](2026-11-04-nanomonsv-source-reproduction.md)
provides a plausible known converter explanation for the caller's J1 anchor;
it does not establish the truth file's provenance or the biological allele.

**Date:** 2026-11-03
**Scope:** one derivative contig; three junctions only.

## Original worker draft — interpretations not accepted

The assembly-derived sequence and both VCFs agree at J1. The caller and 2022 truth VCF use different coordinates at J2, but their paired ALT strings spell the same local sequence after reference context is applied. At J3, the assembly and ONT caller include an 11 bp insert. The truth VCF ALT strings omit it. This is a literal sequence difference between the files. It does not by itself show which file reflects the biological allele.

This candidate was selected after source inspection. It is exploratory evidence, not a blind prevalence result. This note does not analyze callset-wide statistics.

## Inputs and integrity

I read the five saved files in /Users/akm/aayushkrm-AlignSSL/runs/colo829-der3-20261103. SHA256 values match the earlier receipts.

| Local file | SHA256 |
|---|---|
| alignment.pif.gz | b0d63f7760252379cea3959427a9f8e3e90a7f21fa3a4c65329171f4c345866d |
| caller.vcf.gz | ae2d7b02fea3dda159e602c6124ef1911324efb692682ad9977eac697d6e5042 |
| derivative.fa.gz | c4dcc51426f515a50cf561810c94916620bf5f25711b502484e6424c9259a67c |
| segments.bed.gz | 0b65a9fee92b000d85c636083d99df94669bdce702dbdb5a0dbafb8440c11169 |
| truth.vcf | a8f38454367cf8837a7dba1d29c9bc338a8e62cadfee6d2489931f8105f0dcdc |

The derivative FASTA record is der3_RARB_BICC1_TRHDE, length 39,549 bp. The PIF query and derivative coordinates below are 0-based, half-open. VCF POS is 1-based. I interpret the BND ALT strings using VCF v4.3 §5.4: the local REF sequence s is replaced by ALT sequence t; the mate coordinate names the first mapped base of the joined piece; brackets state its orientation. See the [official VCF v4.3 specification](https://samtools.github.io/hts-specs/VCFv4.3.pdf).

## Assembly-derived path

The PIF and segment BED give this path:

| Derivative query interval | Reference interval | Strand |
|---|---|---|
| [0,32732) | chr3:[25326821,25359568) | + |
| [32732,32931) | chr10:[58717463,58717662) | + |
| [32932,33115) | chr12:[72273111,72273294) | − |
| [33126,39549) | chr3:[25352683,25359111) | − |

The derivative also has one unaligned base at q[32931,32932), C, and an 11 bp interval at q[33115,33126), TGATGGATTCA.

Path in derivative orientation: **chr3+ → chr10+ → C → chr12− → TGATGGATTCA → chr3−**.

The PIF gives exact, ungapped alignments for the chr10 and chr12 blocks (199M and 183M). The relevant chr3 block ends map to the VCF anchor bases listed below. The full chr3 alignments contain other indels away from these junctions.

I fetched only small GRCh38 primary-assembly reference intervals from NCBI RefSeq: NC_000003.12:25359100-25359580, NC_000010.11:58717450-58717675, and NC_000012.12:72273100-72273305. The returned records identify GRCh38.p14 Primary Assembly. No whole-genome reference or reads were downloaded. The [NCBI EFetch documentation](https://www.ncbi.nlm.nih.gov/books/NBK25500/) describes the interval request.

## Junction facts and comparison

### J1 — chr3 to chr10

**Assembly sequence.** Derivative base q32731 is G, aligned to chr3:25,359,568. The next base q32732 is T, aligned to chr10:58,717,464. There is no inserted base between them.

**Caller records.**

    r_12_1  chr3:25359568   REF G   ALT G[CHR10:58717464[
    r_12_0  chr10:58717464  REF T   ALT ]CHR3:25359568]G

**Truth records.**

    truthset_8_1  3:25359568   REF G   ALT G[10:58717464[
    truthset_8_2  10:58717464  REF T   ALT ]3:25359568]G

**Unreviewed worker interpretation, not accepted.** The pair coordinates, orientations, and local anchor bases match. Both VCFs encode this adjacency without inserted sequence. It matches the two assembly bases.

### J2 — chr10 to inverted chr12

**Assembly sequence.** q32930 is G, aligned to chr10:58,717,662. q32931 is an unaligned C. q32932 is C, the reverse complement of the GRCh38 G at chr12:72,273,294. The derivative sequence at the join is therefore G | C(insert) | C.

**Caller records.**

    r_13_0  chr10:58717662  REF G   ALT GC]CHR12:72273294]
    r_13_1  chr12:72273294  REF G   ALT GG]CHR10:58717662]

The caller gives SVINSLEN=1;SVINSSEQ=C on the chr10 record and SVINSLEN=1;SVINSSEQ=G on the reciprocal record.

**Truth records.**

    truthset_43_1  10:58717662  REF G   ALT G]12:72273295]
    truthset_43_2  12:72273295  REF T   ALT G]10:58717662]

**Reference context.** NCBI RefSeq has G at chr12:72,273,294 and T at chr12:72,273,295.

**Unreviewed worker interpretation, not accepted.** The truth VCF shifts the chr12 mate coordinate by one base. Its mate record also replaces the T at 72,273,295 with G. In chr12 forward orientation, the caller spells the retained G at 72,273,294 followed by an inserted G; the truth spells the same G,G sequence by retaining 72,273,294 and changing the next base from T to G. Both then join to the same chr10 piece. In the derivative's reverse orientation, this is the inserted C followed by the complement C of chr12:72,273,294. The one-base coordinate difference is an alternate BND representation of the same local sequence in these paired records. It is not a residual one-base allele mismatch.

### J3 — inverted chr12 to inverted chr3

**Assembly sequence.** q33114 is C, the reverse complement of chr12:72,273,112 G. q33115–q33125 contain the 11 bp TGATGGATTCA. q33126 is C, the reverse complement of chr3:25,359,111 G.

**Caller records.**

    r_24_1  chr3:25359111   REF G   ALT GTGATGGATTCA[CHR12:72273112[
    r_24_0  chr12:72273112  REF G   ALT ]CHR3:25359111]TGAATCCATCAG

The caller's SVINSSEQ is TGATGGATTCA on the chr3 record and its reverse complement, TGAATCCATCA, on the mate.

**Truth records.**

    truthset_7_1  3:25359111   REF G   ALT G[12:72273112[
    truthset_7_2  12:72273112  REF G   ALT ]3:25359111]G

Neither truth ALT has an inserted sequence. The retrieved local reference windows around both endpoints do not contain the full 11 bp string in either orientation.

**Unreviewed worker interpretation, not accepted.** The caller and truth pair use the same endpoint coordinates and orientations. Their ALT strings do not spell the same sequence: the caller inserts 11 bases, while the truth pair encodes no inserted bases. This is not the J2 one-base shift. The reference-context check gives no local sequence match that would absorb the full 11 bp through a simple breakpoint shift. The truth VCF may omit sequence that its evidence did not resolve, or it may assert a different exact junction. Event-specific validation for this insertion was not inspected, so that distinction remains unknown.

## Independence, phase, and limits

- The FASTA is an assembly-derived consensus. The JBrowse source describes it as a consensus of 29 tumor reads. The caller file is a separate nanomonsv-0.7.1 ONT VCF with sample COLO829; its header names GCA_000001405.15_GRCh38_no_alt_analysis_set.fasta.
- The 2022 truth VCF uses sample COLO829T and hg38-lifted coordinates. Its records are unphased 0/1. SUPP_SEQ and SUPP_VAL fields are present, but the event-specific validation evidence for these exact rows was not reviewed.
- The contig and caller are different outputs, but available provenance does not prove independent read evidence. Exact run, aliquot, passage, and read overlap are unknown. The truth VCF does not establish which phased chromosome carries this complete path.
- The caller records have MATEID pairs. They do not group the three pairs into a named or phased whole path. Whole-path caller status remains unknown.
- This note checks only this der(3) sequence and its six paired records. It does not make a dataset-wide accuracy, prevalence, or caller-failure claim.

## Source URLs

| Source | Public URL |
|---|---|
| Derivative FASTA | [JBrowse derivative FASTA](https://jbrowse.org/demos/cancer_sv/der3_RARB.derivative.fa.gz) |
| Segment BED | [JBrowse segment BED](https://jbrowse.org/demos/cancer_sv/der3_RARB.derivative_segments.bed.gz) |
| PIF alignment | [JBrowse GRCh38 PIF](https://jbrowse.org/demos/cancer_sv/der3_RARB.vs_reference.pif.gz) |
| ONT caller VCF | [COLO829 ONT VCF](https://ont-open-data.s3.amazonaws.com/colo829_2024.03/wf_somatic_variation/sup/COLO829.wf-somatic-sv.vcf.gz) |
| 2022 truth VCF | [Zenodo hg38-lifted VCF](https://zenodo.org/records/4716169/files/truthset_somaticSVs_COLO829_hg38lifted.vcf?download=1) |
| chr3 reference interval | [NC_000003.12:25359100-25359580](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=NC_000003.12&seq_start=25359100&seq_stop=25359580&rettype=fasta&retmode=text) |
| chr10 reference interval | [NC_000010.11:58717450-58717675](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=NC_000010.11&seq_start=58717450&seq_stop=58717675&rettype=fasta&retmode=text) |
| chr12 reference interval | [NC_000012.12:72273100-72273305](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=NC_000012.12&seq_start=72273100&seq_stop=72273305&rettype=fasta&retmode=text) |

The source files were read only. No raw reads, accounts, Git operations, or cluster jobs were used.
