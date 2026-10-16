# Independent review of the complete Tier2 run02 packet

16 October 2026, Asia/Tomsk. Requested Sol6.1/high is not independently
backend-attested. Owns only this note. Reviewed the local small packet at
`/Users/akm/aayushkrm-AlignSSL/runs/tier2-geometry-result-20261016.5z8G6B`,
main's full `2026-10-16-tier2-geometry-result.md`, and its selected result
copies. No SSH, job action or Git operation. No study BAM was accessed.

Decision: ACCEPT the completed assay's local accounting. No blocking packet,
count or scope defect found. Seventeen actual eligible observed QNAME groups
have native Chimeric flags. Zero eligible Foldback flags were observed. These
are candidates for possible adjudication, not authenticated artifacts, true
inversion support, filter errors or caller failures. This review grants no
campaign permission and leaves investment judgment to the separate reviewer.

## Independent local reconciliation

The execution receipt names job1604949, start03:12:36UTC; the exit receipt
records exit0 at03:13:51UTC. Collection is COMPLETE with no incomplete reason,
fetch complete, group EOF/complete and source-stat stability. I compared the
recorded before/after BAM and BAI stat objects; each pair is identical. This
checks the receipts, not the source filesystem or a fresh whole-source hash.

The plan file hash matches the frozen
`bff54ad8c1d2e2fd51ae02a93fe9de611b13c2309dce7fb2c237923328264917`;
its internal seal is
`9d31881ee1b0c9496faf238546e4b3070bea884150f1c307c7e664b03a1828d8`.
There are53 ordered source rows,106 original endpoint windows and59 merged
fetch windows covering3,692,176bp. All59 manifest windows have fetch EOF.
All53 census rows are present; every row has eligible groups, range64–1,779.
These counts do not authenticate an allele or make rows independent events.

Window fetch counts sum to19,227; the deduplicated physical-record count is
19,206, with21 repeat retrievals across windows. Group record counts also sum
to19,206. The15,460 distinct QNAME groups comprise11,290 eligible and4,170
UNKNOWN. I independently rebuilt every original endpoint association from
the recorded reference intervals, then recomputed all event/window censuses.
They match the saved groups and manifest. This checks recorded intervals;
it does not independently reconstruct records from the absent study BAMs.
Event membership totals exceed unique-group totals because groups can touch
several rows; they must not be pooled as independent observations.

I parsed the TSV independently of the summary implementation. Its1,648 rows
on1,032 distinct QNAMEs reconcile with native stdout and the saved summary:

| Native breakpoint class | Eligible rows | UNKNOWN rows | Total |
|---|---:|---:|---:|
| Pass |1,378|249|1,627|
| Chimeric |17|4|21|
| Foldback |0|0|0|

All report QNAMEs exist in the group file; no exact duplicate report row was
found. Native stdout reports9,818 reads passing its own MAPQ/length filters,
21 final Chimeric reads and0 Foldback reads. Its retained-read denominator
differs from collector eligibility and cannot measure sensitivity. There are
1,012 any-Pass QNAMEs and21 any-Chimeric QNAMEs, with one shared QNAME:
`m84039_230418_220405_s4/195495556/ccs`. Their union is1,032. The any-class
sets are not final read classes. No missing breakpoint row was counted as a
Pass read, and no read-level dominance claim is needed for these counts.

UNKNOWN reasons overlap:3,663 groups describe an unobserved SA alignment,
3,107 lack exactly one observed primary and507 fail mutual SA consistency.
Their sum is not a group partition. Four Chimeric flags remain UNKNOWN and
do not enter the17 eligible candidates; they are not negative evidence.

## Eligible candidates and direct endpoint context

All17 eligible flagged rows have distinct QNAMEs. Thirteen are interchromosomal;
four join distant sites on the same chromosome. The latter are two chr1 joins
between16,680,841 and146,052,339 and two chr7 joins between60,985,169 and
62,432,906. All satisfy the native Chimeric distance/contig condition.

I independently checked each eligible row's raw reference boundaries against
its group's recorded strand-specific alignment boundaries, and compared both
breaks with all106 original endpoint windows using the frozen half-open rule.
All saved intersections match. Fifteen candidates have both breaks in original
endpoint windows and two have only one; none has neither. The two one-sided
cases are QNAME suffixes `/90179958/ccs` and `/234358165/ccs`: their
chr7:60,985,169 break is outside every original endpoint window. Their recorded
alignment overlaps row17's POS window, but this does not put that flagged
boundary inside it. Merged fetch windows do not change this result.

The17 flags touch14 source rows by direct breakpoint context:
3,4,6,10,11,12,16,17,20,21,36,37,39,51. No eligible flagged join has both
breaks inside endpoint windows of the same source row, including no opposite
POS/END pair. This is descriptive geometry only. It neither proves that a
candidate lacks biological support nor establishes a valid complex-event path.
Repeated coordinates, high MAPQ and cross-row overlap do not resolve that.

## Hashes, custody and review boundary

All six locally available output-receipt hashes pass: groups, manifest,
native report, native stdout, native stderr and controls/run.json. The two
study BAMs are absent locally; their hashes were not independently checked.
All four summary input hashes match fresh local calculations, and a fresh
in-memory summary recomputation equals the entire saved JSON object.
Summary SHA256:
`7fab499aa5c299b0d689402c735debc855131153e9e51635e108701d22dfc583`.
All eight selected files under `results/tier2_geometry_screen_20261014/run02/`
match their local originals byte for byte; its `manifest.json` maps to
`collection/manifest.json`. The repository selection is not a standalone copy
of every file named in the execution hash receipt.

The local native controls also reconcile: report/fixture hashes, version,
successful untimed-out command, expected three breakpoint rows and stdout
counts pass. These are synthetic controls, not study truth labels. The packet
records the expected executable hash0499... and pysam0.24.1; I did not execute
or freshly hash the remote native binary.

Main supplies remote scheduler completion0:0, oneCPU/2GiB/15min allocation,
75 allocated CPU-seconds,71.283 measured CPU-seconds and208436K MaxRSS. Main
also supplies whole-leaf329,789,011B, cp-a/recursive byte equality, and all
eight output hashes passing in scratch and permanent HOME. These remote
custody/resource facts were not independently rechecked here. The manifest
reports raw BAM159,825,049B, sorted BAM162,550,002B and collector71.211s;
local groups are6,437,205B. Receipts report both collection and storage gates
passing. The two-attempt totals134 allocated and126.377 measured CPU-seconds
are arithmetically consistent with supplied run01/run02 charges; the separate
ABI qualification remains separately charged.

Main's full result note matches these checks and correctly limits its claims.
The presence screen is nonzero within eligible observed groups, so a complete
zero-screen conclusion is unavailable. It has not yet established one
allele-authenticated flagged candidate. Any next scientific decision must
concern the fixed17 candidate set and unresolved context; whether a bounded
adjudication is worth doing belongs to the separate investment review. No
expanded screen, threshold change, caller run or campaign follows from this
packet acceptance. The old S10 STOP remains in force.

## Narrow challenge to the post-screen investment STOP

Read Meitner's complete investment note, including its closing execution
statement; reviewed version SHA256
`5ffe1b15c62e1b975b9f5675f4cf0ecaceaa0c50fbbe6652d932156728623b5e`.
The actual-packet acceptance above is unchanged.

Scoped acceptance: STOP is reasonable as the current allocation choice for
this available-HiFi filter-error lead. Zero Foldback flags, no same-row
endpoint pair among17 eligible Chimeric joins, and unresolved repeat/mapping
context provide weak direct evidence for the proposed inversion-support
problem. A further count of native labels or proximity would add little.
No new experiment is selected by this review.

Concrete criticism: the note's phrases "permitted next tests" and
"these executions are outside this finite task" cannot establish that no
useful cheap diagnostic exists. Meitner's no-execution assignment limits that
agent's actions. The full project goal permits future data acquisition and
compute when justified. Missing independent labels in this packet establish
an unresolved class; they do not make obtaining informative evidence
impossible. The note's provision for a later evidence-based proposal is the
correct limit on its opening zero-allocation language.

Existing metadata can guide such a proposal without becoming truth labels.
For example, the inspected plan retains haplotype source, ORIGINAL_LOCUS,
repeat annotations and endpoint offsets. Rows11/12 share an ORIGINAL_LOCUS;
the chr4-to-chr22 flags also touch row51. This supplies a concrete context for
looking for an independently derived HG002 haplotype path or orthogonal
sequence evidence at those actual joins. It does not authenticate any join,
justify shifting the frozen windows, or warrant assuming such evidence exists.
The packet's repeated joins and mixed-label group are already described;
repeating that inspection alone need not receive more investment.

A potentially useful cheap next question is whether an already released,
sample-matched assembly path or orthogonal read evidence can address one of
the fixed candidate joins with enough locus-specific sequence to distinguish
it from an alternative placement. Checking source availability and locus
coverage can change the next action before full adjudication. A convincing
independent path could motivate a small confirmation test; unavailable or
uninformative evidence can leave STOP in place. Assembly gaps or absent
coverage must not be counted as evidence that a flagged molecule is an artifact.
I have not searched for or verified such a source in this addendum.

Neither a novel method nor an observed caller failure must already be proved
before that diagnostic. Conversely, one authenticated real junction would
still not prove harmful filtering or a publication contribution. The cited
general prior-art overlap supports caution; it does not by itself decide
whether this particular case has informative evidence. Therefore accept
deprioritization now, but not a scientific claim of zero value for every cheap
exploration. The lead may remain stopped unless a concrete evidence route
changes that choice. Future work on this method family or other material is
not banned. No new search, SSH, jobs, Git operation or campaign accompanied
this append-only review; only this section was added.
