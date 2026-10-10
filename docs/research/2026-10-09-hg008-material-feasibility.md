# HG008 document-only material feasibility: CLOSED INCOMPLETE

2026-10-09. The one attempt started at14:29:51UTC and closed at14:50:53UTC,
21min02sec of elapsed time, before the90-active-minute limit. It does not
qualify the proposed16-positive/32-control M1 package. **No M1 booking,
genomic-input acquisition, caller, score, training or cluster job occurred.**
This is an input-feasibility finding, not a biological null, global data
absence, native-caller failure or publishable method result. The full goal
remains active and unmet.

## Sources and actual read scope

Main used the Spreadsheets skill for read-only inspection of the published
version1 supplemental tables. The workbook was not edited, recalculated,
exported or repaired. The bundled Artifact Tool imported the original file.
Main read the S9 header and selected fields for the19 rows below. Automatic
counts cover405 data rows; this is not a manual audit of all405 variants,
all15 sheets, sequence alleles or images. Earlier large printouts were
truncated; they do not establish a full-sheet read.

The exact-v1 [supplement page](https://www.biorxiv.org/content/10.64898/2026.05.01.722316v1.supplementary-material)
links the [original published tables](https://www.biorxiv.org/content/biorxiv/early/2026/05/06/2026.05.01.722316/DC2/embed/media-2.xlsx?download=true).
Node retrieval returned429. ONE bounded curl request for the same file then
returned200,962941bytes. No alternative release was substituted.

Read-only GitHub API requests retrieved22 label definitions and two pages
of issues carrying the exact label `Tandem Repeat`:100+37=137 records.
An initial query without the space returned0; that was a query spelling
error, not evidence of absent cases. Main read selected non-centromeric
clonal issue-body passages, label/date metadata and comparison-term matches,
not all137 full bodies, comments, screenshots or read alignments. A separate
request read issue323 because it is linked by S9 but has no labels.
The [curation README](https://github.com/jzook/HG008SVcuration/blob/main/README.md)
was read FULL. Repository issues are mutable; some records were updated or
created after the publication. Current labels cannot pin the historical
four-callset comparison.

The publication-linked [V0.5 folder](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/data_somatic/HG008/Liss_lab/analysis/NIST_HG008-T_somatic-stvar-CNV_DraftBenchmark_V0.5-20260318/)
listing and all259 lines of its [README](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/data_somatic/HG008/Liss_lab/analysis/NIST_HG008-T_somatic-stvar-CNV_DraftBenchmark_V0.5-20260318/README.md)
were read. The listing shows benchmark files, indexes, a column-description
workbook, checksums and README; it exposes no named four-callset comparison
result. This is a statement about that listing, not the whole publication's
repository or all available data. No VCF, BED, BAM, index, assembly, release
ZIP or comparison output was downloaded.

## A useful candidate crosswalk, not the fixed miss set

S9 sheet name is `S9. SV and CNV Benchmark on GRC`, header row2, rangeA2:AT407.
It has46 columns, including event type, curation links, confidence flags,
normal-v6.3 coordinates and svviz support. It has no explicit per-caller
comparison outcome or all-four-miss field.

The following transparent document filter yields19 rows: SVTYPE in INS/DEL,
EVENTTYPE containing `TR`, possibly_subclonal=n, likely_correct=y, lt50=n,
and in_GRCh38_benchmark=1. All selected event types are `CNV:TR`. This does
not claim to identify every tandem-repeat event: other event-type labels
can occur in repeats. IDs and issue links below come from the unchanged
publication table, not prediction outputs.

| S9 row | ID | Curation issue | Load-bearing qualification |
|---|---|---|---|
|35|SV_219|[326](https://github.com/jzook/HG008SVcuration/issues/326)|Haplotype1 expansion; normal mosaicism reported|
|36|SV_242|[326](https://github.com/jzook/HG008SVcuration/issues/326)|Haplotype2 expansion at same locus; not an independent donor/locus|
|55|SV_220|[322](https://github.com/jzook/HG008SVcuration/issues/322)|Exact representation and noisy ONT qualification|
|57|SV_221|[323](https://github.com/jzook/HG008SVcuration/issues/323)|No current issue labels; germline deletion is reduced|
|63|SV_16|[107](https://github.com/jzook/HG008SVcuration/issues/107)|Earlier SUPP_VEC lists caller support|
|73|SV_222|[324](https://github.com/jzook/HG008SVcuration/issues/324)|Noisy reads and germline expansion|
|77|SV_243|[344](https://github.com/jzook/HG008SVcuration/issues/344)|GRCh38 representation uncertainty|
|97|SV_245|[386](https://github.com/jzook/HG008SVcuration/issues/386)|Normal mosaicism reported|
|121|SV_223|[435](https://github.com/jzook/HG008SVcuration/issues/435)|Other inherited allele absent in tumor; copy/haplotype context matters|
|137|SV_356|[453](https://github.com/jzook/HG008SVcuration/issues/453)|Normal variability/mosaicism reported|
|166|SV_69|[209](https://github.com/jzook/HG008SVcuration/issues/209)|Earlier SUPP_VEC lists caller support|
|199|SV_236|[320](https://github.com/jzook/HG008SVcuration/issues/320)|Germline expansion contraction; representation uncertainty|
|200|SV_227|[321](https://github.com/jzook/HG008SVcuration/issues/321)|Germline context and representation uncertainty|
|202|SV_244|[355](https://github.com/jzook/HG008SVcuration/issues/355)|Normal-assembly56bp deletion differs from GRCh38 representation|
|245|SV_233|[434](https://github.com/jzook/HG008SVcuration/issues/434)|Normal mosaicism and uncertain repeat length reported|
|248|SV_246|[404](https://github.com/jzook/HG008SVcuration/issues/404)|Somatic deletion inside complex germline insertion|
|284|SV_125|[261](https://github.com/jzook/HG008SVcuration/issues/261)|Earlier SUPP_VEC lists caller support; assembly size differs|
|316|SV_247|[417](https://github.com/jzook/HG008SVcuration/issues/417)|Near-telomere germline insertion contraction|
|406|SV_344|[440](https://github.com/jzook/HG008SVcuration/issues/440)|Normal insertion/tumor deletion vs GRCh38|

Subtracting the three earlier caller-supported rows leaves16 rows at15
curation issues. That matches the paper's count but **is not a verified
one-to-one map to the exact four published comparison callsets**. Candidate
discovery SUPP_VEC is not that comparison. No absence of a SUPP_VEC or issue
label is taken as proof that all four missed an event. The four mosaic
issues overlap this candidate crosswalk at five rows; this still does not
prove which belong to the fixed16, invalidate their published truncal status,
or provide a discrete stable-normal allele for all five.

## Controls, versions and usable context

Only one of the137 currently repeat-labeled issues has `Likely FP`:448,
whose body describes a possible normal-assembly error. This is not a pool
of32 supported unchanged tumor/normal inherited alleles. It does not even
certify one such control. The publication's somatic table, caller-support
strings and benchmark regions cannot supply these negatives by absence.
No prospective eligible pool/matching rule and retained-haplotype stability
evidence were established. Other public material may support them; that was
not established in this selected attempt.

The benchmark README's V0.5 changelog and phasing section explicitly describe
normalv6.3/tumorv3.2-based fixes and phasing. This improves on the paper's
v3.1 phasing wording. It does not prove unchanged local alleles for each
candidate. The README also distinguishes passage23 subclonal benchmarking
from other passages and warns about VNTR representation matching. Its
older development-callset list contains pending-upload entries; this is
not proof that the current files are unavailable everywhere. The list of
eleven development comparisons is not the four callsets behind the paper's
reported16 misses.

No complete native-context/input package or actual bounded source-span,
decoded/custody-pass or CPU-cost estimate was established for the proposed
SV, diploid donor-specific and paired repeat policies. Native remote access
documentation alone does not pass that gate. Cropping selected loci and
calling absence a negative would change the promised scientific contrast.
The earlier1GiB/180CPU M1 envelope therefore remains UNBOOKED and inadequate
as evidence of feasibility, not a measured resource use.

## Preservation and terminal decision

Unchanged publication/API sources and the disposable read-only inspection
script are preserved OFF Git in
`/Users/akm/aayushkrm-AlignSSL/runs/literature/hg008-v1-document-check-20261009/`.
No sources were deleted. Four saved source files total2,290,819bytes; these
are literature/curation documents, not M1 HTS input material or experimental
outcomes. The separate retained experimental account42,114,356,107bytes /
568.552707 measuredCPU seconds is unchanged. No model-serving attestation
is inferred from requested agent settings.

| Preserved file | Bytes | SHA256 |
|---|---:|---|
|source.xlsx|962941|ca100745c285b9962edcde224bee14d849c204e6bfab65cd84553e9ecac5bb73|
|repeat-issues.json|978621|31aac6a79e2d906fd182d37f04bd7944e92b033811f406d506747410d1ea1d6e|
|repeat-issues-page2.json|311956|6e5c486d02b12cd91860d4db52c74c7a713fb48522c67245fb03519ddf5586a5|
|benchmark-readme.md|37301|357e4b8007ce16014a40ead7c84a301883ab7c4f9c6babab17ae56b835741497|

**CLOSED INCOMPLETE / TRUTH INCONCLUSIVE for this selected M1 package.**
Stop early because the actual fixed16 comparison bridge, supported32
controls and complete native-context finite cost are not established.
Do not lower the truth standard, relabel the19 candidates as the16 misses,
shrink controls, enlarge this cap, substitute another release, or start a
transport/protocol repair loop. This closes one package, not all somatic
repeat research. Any later distinct investment needs a concrete new
scientific rationale and independent scrutiny; no automatic fallback or
launch follows. Source checks and documentation tests are not empirical SV
performance. The broader publication objective is still unmet.
