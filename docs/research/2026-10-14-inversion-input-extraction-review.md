# Independent review: bounded mapped-input extraction

14 October 2026, Asia/Tomsk. Replacement maintained scientific reviewer.
Requested Sol6.1/high is not backend attestation. Owns only this note.

## Decision

ACCEPT one cheap indexed extraction, conditional on the planned native pysam
synthetic fixture passing before source-case access in the same bounded job.
No blocking defect found in the reviewed extractor. Main owns fixes, execution
and integration. This decision accepts neither an actual case result nor an
expensive campaign, major positive claim, mechanism or publication conclusion.
Actual case evidence remains uninspected by this reviewer.

Use one CPU, 1 GiB RAM and at most 15 minutes. Keep the existing source BAM/BAI
in place. No GPU, new DNA, caller, model, index build or whole-genome scan is
needed. The fresh header/index interface supports access, not a locus finding.

## Basis and independent checks

Read the full attached goal, the full extractor and all 629 test-file lines,
plus the mapped-input trace protocol, equivalence-result review and residual
investment decision dated 13 October. No broad literature refresh is needed
for this implementation review. DeepSV is not the scientific foundation.

Reviewed source identities, computed locally without Git:

| File | Lines | SHA256 |
|---|---:|---|
| `analysis/extract_inv_mapped_case_input.py` | 851 | `27287805842e46ad3651f2e222d6ec85737bc9104fa43e126704c24123b336ef` |
| `tests/test_inv_mapped_case_input.py` | 629 | `af21e5e128aed698d750055521154e4101602ab6daf18cc2e234e827487c3a9b` |

Main reports 14 passing offline tests. Those tests use fake alignment readers;
they do not establish native pysam/HTSlib behavior. I reviewed all 14 but did
not rerun the filesystem tests. Local system Python lacks pytest and pysam.
I independently imported the extractor with bytecode disabled and ran checks
entirely in memory. All six check groups passed:

- Both strands: stored reference-oriented SEQ supplies equality comparisons;
  asymmetric clips give the expected normalized forward-query intervals.
  Raw cross-chromosome SA text and typed essential tags survive unchanged.
- Empty and nonempty iterators reach EOF; exact and excess record caps return
  INCOMPLETE without requesting another alignment.
- An oversized row is refused before writing; the header remains counted.
- An injected decoder error retains the prefix, returns FAILED and reports no EOF.
- CIGAR/query disagreement and missing hard-clipped payload remain UNKNOWN.
- The 9 MiB JSONL and 1 MiB manifest budgets sum to 10 MiB.

## Code and census assessment

The fixed fetch is chr2 [240675000,240704000). No MAPQ, strand, phase, genotype
or agreement filter is applied. Duplicate QNAMEs and secondary/supplementary
records remain. Flag-class counts can overlap when both nonprimary flags are
set; they must not be added as disjoint classes. QNAME counts are label counts.

SEQ/QUAL are retained in their BAM orientation, with forward-query hashes.
The CIGAR walk advances stored query for M/I/S/=/X and reference for M/D/N/=/X;
H/P do not advance stored query. Reverse intervals use [L-end,L-start).
Hard clips do not supply full molecule coordinates. The raw CIGAR and explicit
coordinate scope preserve that limit. Missing SEQ/QUAL, quality-length mismatch
and CIGAR/query mismatch do not become a complete query-payload assertion.

Only '=' positions with available unambiguous query bases are compared against
the supplied canonical context. M/X/D/N supply no equality observations.
A partial stored sequence can still supply a local base witness; that does
not repair its UNKNOWN full payload. Zero conflicts do not identify the
original mapper FASTA or certify uncovered sequence, mapping uniqueness,
alternate allele, genotype or phase. HP/PS remain raw unvalidated tags.

All essential tags, including exact SA, are retained. Other tag names are
listed while values stay in the original BAM. SA is not an independently
retrieved alignment. No record outside the indexed region is fetched from SA.
This is a regional alignment census, not complete molecule reconstruction,
all possible placements or an INV-support classifier.

The corrected output budget counts the JSONL header and every retained row.
At a record/payload/time cap, status is INCOMPLETE and CLI exit is nonzero.
Even exactly 1,000 records stays INCOMPLETE because EOF was not requested.
Decoder/record failures are FAILED. Neither a retained prefix nor zero retained
rows after an error supports absence. Accept a census only with COMPLETE,
region EOF, successful finalization and unchanged BAM/BAI/reference stats.

BAM and BAI stats are captured before and after; historical whole hashes are
clearly marked as historical. Stable stats are change detection, not a fresh
whole-file checksum or proof that the index is current. The earlier accepted
whole-input custody supports reuse; no 48 GB reread is required for this step.

## Execution conditions and claim limits

The native fixture must exercise real aligned-segment serialization, indexed
fetch and extractor output in the reported Python3.12.1/pysam0.24.1 runtime.
It should check reverse orientation, clips, missing payload and typed/raw tags
against known fixture expectations. A native failure stops source-case access;
it is not evidence that input is absent. I have not inspected that fixture.

The 120-second code clock is cooperative: a blocked native read or one large
record can exceed it before the next check. The scheduler supplies the hard
15-minute/1-GiB bound. Per-record expansion precedes the output-size test.
Manifest-size or output-I/O failure can leave a partial directory without a
valid manifest. Preserve it and logs as a failed attempt, never as a census.
These limits do not block the bounded diagnostic; do not claim a strict
120-second preemption or an always-written failure manifest.

The case is first S10 chr2:240685775–240688980, Tier 1 simple INV. It cannot
establish a complex-component mechanism. The 25-source panel and nine selected
declarations remain prior evidence; the accepted 36 conditional pure-INV
inequalities establish neither caller failure nor actual molecular inequality.
The existing Vollger/Stergachis processed mapped DNA is a separate input track,
not the published 20-result readset or reproduction of its outcome.

Next review uses the retained manifest and actual regional rows, if produced.
A useful later hypothesis must distinguish observed allele evidence from
repeat/alternative mappings before assigning a recoverable caller loss.
Applicable strong controls and held-out loci/samples are required before a
larger claim; all future controls or a clinical gate are not prerequisites
for this cheap inspection. The publication goal remains unmet.

Audit: no Git, job booking, source BAM access, secrets, download or other-file
write. Only this note was created. Independent reviewer role continues.

## Execution correction addendum

Main reports job1604869 FAILED0:53 at00:00:00, batch CANCELLED0:53, with no
execution/fixture/case outputs or study-body access. This is a failed launch,
not input absence. Compute HOME read-only and prior direct-srun success are
reported setup evidence; the cause of signal53 remains unproved.
I independently compared launchers01/02: only the comment and bundle path
change, to existing physical scratch/new02. Bash syntax passes. Launcher02
SHA256 is `d71dbaaf4acee6ae069b6c3297fdbd3ee766e42e1de30fa4f9fd0c3164182a47`;
it matches `results/inv_mapped_trace_20261014/SHA256SUMS-02`, which retains the
accepted extractor, fixture and reference hashes. No science or gate changes.
Accept one replacement direct-srun attempt with the same one-CPU/1-GiB/15-min
allocation, native fixture gate and outer timeouts. Main must preserve outputs
through login into separate permanent HOME02 and verify hashes before the
October22 scratch deadline. That preservation is pending, not attested here.
No scheduler diagnostics or jobs were duplicated. Case acceptance stays pending.

## Actual extraction review: job1604870

ACCEPT the retained COMPLETE02 regional extraction census, superseding the pending census statements above. Independently read all 52 local rows; recomputed JSONL SHA256 `ca77cd139dcb8344cf0697dc7468e97db35344c3d10dfdb42d28eedcbd43df18` and manifest SHA256 `80f29373616a355ce4c2b23dbba49ade7796ac28a094032c4598b65f508aae3a`; all four bundle and three output checksum entries match. JSONL4,527,955B + manifest462,702B =4,990,657B, below both individual and combined caps. Independently reproduced all census histograms, coordinate/CIGAR walks, forward SEQ/QUAL hashes and equality observations: 52 records, 47 QNAME labels, five duplicate-label records; 47 primary, five supplementary, zero secondary; MAPQ60/12/32 counts49/2/1. All stored SEQ/QUAL lengths and CIGAR consumption agree; no hard clipping or missing payload in these case rows. Recomputed 522,266 local '=' comparisons, zero conflicts, 28,991 covered positions; nine context positions remain unwitnessed. COMPLETE/EOF, no stop/failure, stdout and 195-SQ header agree. Recorded BAM/BAI/reference stats are unchanged; BAM/BAI sizes match custody, with no fresh whole hashes. Native fixture receipt, four saved rows including missing hard-clipped payload, raw SA and reverse orientation pass inspection; the hash-bound sequential launcher enforces fixture-before-case. Both stderr files are empty; retained job1604870 exit receipt is0. These verify packet consistency and the reported iterator completion, not an independent source-BAM enumeration or current-index proof. Main reports COMPLETED0:0, 2s allocation, 1s step, TotalCPU0.907s, MaxRSS17424K and matching scratch/permanent-HOME copies; scheduler accounting and remote preservation were not independently queried. The initial pre-SCP FileNotFoundError is a supplied transient local-read failure, not a rerun, source mutation or negative result. No INV-support, phase/genotype, molecular-inequality, caller-failure or campaign claim is accepted. This remains a separate Vollger/Stergachis input track. Review used local retained data only; no cluster/network, jobs, Git or other-file write. Reviewer continues; publication goal unmet.
