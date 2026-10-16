# Complete Tier2 geometry screen: native flags, not biological labels

16 October 2026. Run02 completes the frozen assay. It does not establish a
filter error, true inversion support or a publication contribution. No new
caller, training run, genomic acquisition or threshold sweep follows from it.

## Actual execution and custody

Direct job1604949 ran on hydra-n1 from03:12:36 to03:13:51UTC and completed
0:0. The allocation was one CPU,2GiB RAM and15min; actual elapsed75s,
measuredCPU71.283s, MaxRSS208436K. The serial job used no GPU. Four bundle
hashes and the native synthetic controls passed before study classification.

All59 planned windows reached source-fetch EOF. Group EOF/completion and source
BAM/BAI stat stability passed. All53 source rows remain in the census, including
duplicates and dot IDs. No event/threshold selection changed after run01.
The collector took71.211s. It fetched19,227 records and retained19,206 distinct
physical records. Raw derived BAM159,825,049B; sorted BAM162,550,002B;
group metadata6,437,205B. Both BAMs are below512MiB. The complete outer leaf
is329,789,011B, below2GiB. Guards are sampled checks, not hard quotas.

The entire unmodified leaf is in both scratch and permanent cluster HOME:

```text
/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/tier2_geometry_screen_20261016_02
/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/tier2_geometry_screen_20261016_02
```

Main copied through login, obtained recursive byte comparison with no
differences, and passed all eight retained-output hashes in both copies.
Source48GB BAM was not rehashed; its whole hashes remain explicitly historical.
Only small metadata/report/control files were downloaded locally, to
`/Users/akm/aayushkrm-AlignSSL/runs/tier2-geometry-result-20261016.5z8G6B`.
Six available local output hashes match the execution receipt. The two study
BAMs remain on the cluster, outside Git. Permanent copies precede22October
scratch expiry. Run01 remains intact and incomplete, not replaced by02.

Both real-input attempts cost134 allocated CPU-seconds and126.377 measured
CPU-seconds in total. The separate synthetic qualification job remains charged
as well. No failed attempt is omitted from the history.

## Complete accounting

| Unit | Observed count |
|---|---:|
| Distinct observed QNAME groups |15,460|
| SA-consistent eligible observed groups |11,290|
| UNKNOWN observed groups |4,170|
| Native reads passing its MAPQ/length filters |9,818|
| Native breakpoint rows |1,648|
| QNAMEs with any reported breakpoint |1,032|
| Native Pass breakpoint rows |1,627|
| Native Chimeric breakpoint rows |21|
| Native Foldback breakpoint rows |0|

Every source row has nonempty eligible observed groups; the per-row count range
is64–1,779. Rows, overlapping windows and QNAMEs are not independent biological
replicates. Native passing-read counts have a different filter and denominator
from collector eligibility; do not divide one into the other as sensitivity.

| Native breakpoint class | Eligible groups' rows | UNKNOWN groups' rows |
|---|---:|---:|
| Pass |1,378|249|
| Chimeric |17|4|
| Foldback |0|0|

There are21 distinct any-Chimeric QNAMEs and1,012 any-Pass QNAMEs. One QNAME
has both Pass and Chimeric breakpoints; their union is1,032. These overlapping
any-breakpoint sets are not native final read-level class assignments. Native
stdout separately reports21 final Chimeric reads and0 Foldback reads. A group
without a breakpoint row must not be called a native Pass read.

UNKNOWN reasons overlap:3,663 groups declare unobserved SA alignment(s),3,107
do not have exactly one observed primary and507 fail mutual observed/SA
consistency. These counts do not sum to a partition. UNKNOWN is not negative.
Eligibility does not establish unique placement or a complete source molecule.

## All17 eligible flagged joins: descriptive context

All17 are native Chimeric, each on a distinct observed QNAME. Thirteen join
different chromosomes. Four join distant sites on the same chromosome: two
chr1 joins between16,680,841 and146,052,339, and two chr7 joins between
60,985,169 and62,432,906. Raw coordinates are retained, not shifted toward a
truth convention. They are zero-based reference boundaries in the pinned
native implementation.

Main compares both reported ends of every eligible flagged join with every
original frozen endpoint window, not only the merged fetch region. No eligible
flag has opposite endpoints of the same truth row within those windows. This
is a geometric observation, not a new truth criterion or an estimate of support
loss. A flag can touch different truth rows, and an actual complex junction
can differ from printed inversion endpoints. In particular, the absence of a
same-row pair does not show that a read is an artifact or lacks biological
support. Repeated coordinates and high MAPQ do not resolve that ambiguity.

The machine-readable [summary](../../results/tier2_geometry_screen_20261014/run02/summary.json)
retains all53 censuses, all17 eligible flag rows, both endpoint intersections,
selected-read associations, UNKNOWN counts and all any-class QNAME sets.
Its SHA256 is
`7fab499aa5c299b0d689402c735debc855131153e9e51635e108701d22dfc583`.
The unchanged [native report and receipts](../../results/tier2_geometry_screen_20261014/run02/)
retain all1,648 rows, including UNKNOWN-group flags. Group metadata and study
BAMs remain in the permanent full leaf identified above.

## Review and decision boundary

The [offline-summary review](2026-10-16-tier2-summary-review.md) approves the
accounting implementation, with explicit limits: summary consistency alone
does not authenticate native completion or a report against its BAM. The
execution/hash evidence above is separate. The combined seven-file regression
selection passes80 tests; adding the fixed-source tests gives101 passing tests
across eight test files in6.54s. The collector/native/summary tests alone pass27.

The maintained Sol6.1/high-requested reviewer
[accepts the actual local accounting](2026-10-16-tier2-result-review.md).
It independently rebuilds endpoint associations/censuses from recorded
intervals, checks native coordinates against strand-specific boundaries,
reconciles all counts and recomputes the exact summary. Fifteen eligible flags
have both breaks in some original endpoint windows; two have only one. None
connects the same source row at both ends. Remote custody/BAM hashes remain
main's supplied evidence, not independently repeated by the local reviewer.
A separate [Sol6.1/max-requested investment review](2026-10-16-tier2-post-screen-investment.md)
recommends STOP at the current investment point. Main accepts deprioritization,
not a field-wide conclusion. The independent challenge preserves the potential
value of a cheap source-availability check for orthogonal evidence at actual
joins. No such source is verified or test selected here. Agent no-execution
limits do not restrict the project's authority to acquire data or compute.
Useful diagnostics need not begin with pre-proved novelty or caller failure.
Requested backend configurations are not independently attested. Neither review
can turn these flags alone into authenticated artifacts, true allele support,
filter/caller error, clinical evidence or a publication result. No follow-up
campaign is authorized here. Full research goal remains active and unmet.
