# One limited SVUPP provenance/header check

Status: **FROZEN CANDIDATE, UNBOOKED, UNSTAGED, UNEXECUTED**. Code, controls,
wrappers and pins are complete. Independent exact review is pending. This
proposal approves no read.

## Scientific purpose

The [independently accepted metadata inventory](2026-10-09-svupp-inventory-result02.md)
identifies plausible genotype and truth resources, not usable scientific
inputs. The next cheap gate asks whether complete, specified provenance text
and VCF headers can establish the intended ONT ultra-long→HiFi source/target,
fixed SVUPP/kanpig caller outputs and published truth identity. Reject this
archive path if those required inputs are demonstrably incompatible. Do not
train a model, compare GTs, measure discordance, select loci or change the
1%label-discordance/10-point coverage investment question in this step.

Even compatible headers do not establish usable GTs, record identity,
callability, complete denominators or independent validation. A later complete
field/readiness and value protocol is separate, must fit the residual
allowance and receive independent review. This public archive remains
development evidence; no labels from it can become an untouched final test.
Current kanpig fitting/calibration controls and genericGQ prior art remain.

Latest objective attachment2fa04b13 SHA256
`74ba6450712e7f0e763cd81de896d3a71ca73f9c4a10fec3f1ecab59b3f1b0b8`
governs. The user explicitly requires useful efficient resource capacity and
full scaling of justified parallel experiments. This one-asset serial read
uses oneCPU/2GiB, no GPU/idle node. It is not an experiment campaign.

## Fixed source and exact eight-member scope

Read only the already acquired, immutable source:
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/svupp-inventory-20261009-02/SVUPP_paper.zip`.
Size47,443,427, publisherMD5`5469337ca9249691b2b376ceb9b67e1d`, SHA256
`b15665743d28151bf2e9f656ae32dc8de9a3d6a5582c8033dbf251fec71daa2c`.
No download, alternate archive, container, BAM/CRAM/FASTA, extra caller or
source-format repair. Inventory01/02 claims stay consumed and evidence intact.

| Complete selected member under `SVUPP_paper/` | Read scope | ZIP-declared decoded bytes |
|---|---|---:|
| `README.md` |Complete UTF8 provenance text|2,835|
| `samplesheet/platinum-ont-ul.csv` |Complete sample/technology/depth text|1,568|
| `pipeline/bench-force-calling.nf` |Complete text, never execute|6,496|
| `reproduceplot/discordance_per_GQ_noneighbors.R` |Complete text, never execute|5,329|
| `reproduceplot/discordance_per_GQ_withneighbors.R` |Complete text, never execute|5,346|
| `reproduceplot/platinum.withdist1000.vcf.gz` |Complete outerZIP member into RAM; nested VCF header only|9,222,119|
| `reproduceplot/kanpig.vcf.gz` |Same limited scope|10,950,303|
| `reproduceplot/svupp.vcf.gz` |Same limited scope|9,250,146|

All five text members total21,574bytes. The three decoded `.gz` members total
29,422,568 compressed-file bytes, not plain VCF bytes. All eight sum29,444,142;
their ZIP-compressed streams sum28,409,706. Exact selected names/types/decoded
sizes and that aggregate compressed total must agree. Complete selected
body CRCs must match the authenticated source's own ZIP directory values;
no separate per-member CRC/compressed-size pins are claimed. The whole-source
SHA before/after pins that directory. Missing/corrupt/unsupported members
stop, no substitute or repair.
Do not open the other18members, including other callers or cost summaries.

## Reader contract

Use the existing pinned directory-reference/leaf/snapshot guards with the
same sourceFD. Regular single-link source, NOFOLLOW parents/leaf, exact
prehash and posthash size/MD5/SHA, parent/name/descriptor identity checks
before/after each selected member. Read two complete opaque source hashes.
Use standard `zipfile.ZipFile` on a duplicate of that descriptor, never
reopen the name for member content and never use `extract`/author code.

Complete bounded outer-member reads verify selected ZIP CRCs atEOF. Text
decoding is strictUTF8; retain full exact text, no favorable excerpt. Hold
each gzip member in boundedRAM, use binary `gzip.GzipFile(io.BytesIO(...))`
to return the complete VCF header through its `#CHROM` line. Cap each header
at256KiB; no record before that line, malformed columns, duplicate sample
names, missing delimiter, invalid compression or cap failure is repaired.
Accept standard sites-only8-column headers as metadata with no samples,
not as scored genotype data. FORMAT headers must have valid sample columns.
Preserve complete header text and all sample names, no label-based selection.

No genotype row is interpreted, exported, joined or scored. The buffered
nested decoder may inflate unused lookahead; **do not claim all outcome
bytes remain undecoded**. Report member bodies decoded=true, records not
interpreted=true, full nestedgzip CRC/body integrity not assessed=true.
The selected outerZIP CRC pass does not imply full nestedVCF integrity.
Exclusive complete JSON report at most1MiB, no partial report promoted.
The combined serialized report can exceed1MiB after JSON escaping even if
each header is at most256KiB. That is a predefined resource-incomplete stop,
not a reason to raise the cap, truncate text or claim missing scientific data.

Main uses Firecrawl (connected plugin, notCLI) to read official
[Python ZIP API passages](https://docs.python.org/3.10/library/zipfile.html),
the complete [gzip API page](https://docs.python.org/3.10/library/gzip.html),
and only the `_update_crc`/adjoining excerpt of exact
[CPython3.10.20 source](https://raw.githubusercontent.com/python/cpython/v3.10.20/Lib/zipfile.py).
The indexed developer search did not provide primary evidence; the official
source fallback did. The query-only gzip response was insufficient; complete
page retrieval resolved it. Current3.10 documentation identifies3.10.22,
not the actual3.10.20 cluster binary. Source/API readings are not full-library
or installed-binary attestation; frozen actual-stack synthetic gates remain
required. No biological data or private account material was sent toFirecrawl.

Main also retrieves the official
[Zenodo record metadata](https://zenodo.org/api/records/17569072): recordDOI
10.5281/zenodo.17569072, creator`Li, Zilong`, contributor`Staeger, Frederik`,
versionv0.0.2, licenseobject`{"id":"cc-by-4.0"}`. Any published extracted
provenance text must retain that record/source attribution and identify the
unaltered authored text separately from this project's reader/analysis.
This records the archive's license metadata, not a license audit of bundled
third-party tools or a relicensing of the whole AlignSSL-SV repository.

## Prospective finite resource subset

Propose256MiB/60named allowance seconds, **UNBOOKED**, within the remaining
original1GiB/240. Retainedprior41,845,920,651; if booked42,114,356,107bytes.
Prior measurednamedCPU567.002707; plus allowance627.002707 is prospective,
not measured. Residual805,306,368bytes /180allowance seconds. No new complete
candidate envelope, refund of failures, or extra content allowance.

Conservative named passes: sourcehashes94,886,854; selected ZIP-compressed
reads28,409,706; selected outer decoded29,444,142; archive metadata1MiB;
nestedheader/unusedlookahead budget1MiB; six8MiB synthetic passes50,331,648;
six1MiB raw hash/transfer/verification passes6,291,456; stagedsource/log/claim
16MiB16,777,216. Total228,238,174bytes, below268,435,456. This names bounded
passes, not complete physical/cache/networkI/O. No full plainVCF pass here.
Do not duplicate SlurmCPU or test wall time in measuredCPU. Actual GNU
waited-tree user+system counted once; retain full byte charge on failure.

Frozen execution limits: oneCPU affinity/threadcaps,2GiB addressspace,
45s outerwall+5s killgrace,20/30per-processCPU,2MiB per-file cap,8MiB/4096
synthetic controltree,1MiB complete smallraw includingchecksum. Final scripts
must reconcile exact synthetic witness sizes with those file caps. All
frozen actual-stack controls pass with zero skips before any realmember read.
No package install is needed. Only metadata/report/logs transferred locally;
ZIP and compressedmember bodies remain on cluster/inRAM, never committed.

## Setup and decisions

Use a separate fresh physical root
`/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/svupp-provenance-20261009-01`.
It is a distinct provenance stage, not replay orinventory03. One exclusive
submission and payload claim. Freeze source/tests/count, wrappers, ledger,
bundle and literal command; require independent exact review and booking
before root creation/staging. Unknown acknowledgement consumes the slot.
Recheck live jobs/fresh-root/source presence/access/expiry, verify allpins.
Any failure closes this step with complete bounded evidence, no retry,
prefix promotion, cap enlargement or alternate path. Preserve old failures.

After complete reviewed output, map every sample to donor/technology/depth
using explicit text/header evidence, not guesses from filename. Verify
caller versions/score definitions, reference/catalogue/truth provenance and
native-support fields. Record missing/unresolved information explicitly.
Missing required source/target GT-bearing views or demonstrably incompatible
reference/allele/score identity stops this archive path. Ambiguous evidence
cannot become ready data. Compatible provenance only permits a separate
complete row-contract/value proposal within residual scope, not an outcome
read or model automatically. No source-shopping or endpoint substitution.

Before an expensive campaign or major positive claim, independently verify
current native/ordinary controls, fair labels/tuning/compute, leakage-safe
sample/locus/pretraining units, untouched final tests, uncertainty/multiplicity,
raw reproducibility and genuine useful novelty. No present result meets that
standard. DeepSV stays historical/baseline only; SSL has no preferred status.

## Exact pre-review freeze

Two requested Luna/max workers completed independent, disjoint reader/test
and launcher-test work. Those are requested configurations, not backend
attestation. Initial launcher controls found three missing completion gates
(outer CRC-EOF confirmation, nested-body-integrity-unassessed and gzip
read-ahead disclosure): 19 passed, 3 failed. Main added those gates; tests
were not weakened. Reader worker's initial 21 passes used Python3.9.6/
pytest9.0.3. Main added a real1MiB combined JSON-escape-cap witness and
strengthened the intended parent-symlink failure-cause check.

Main reads the complete reader, launcher, both test files and wrappers.
Latest local focused run uses Python3.11.13/pytest9.1.1: **44 passed, zero
skips, 0.31s**. This is not actual-stack or whole-repository validation.
Its retained temporary synthetic tree is407,568bytes/168entries, largest
regular file267,967bytes; within frozen8MiB/4096entries and2MiB/file limits.
Both shell syntax and two inline Python blocks parse. Frozen cluster gate
requires exact44passes/zero-skips on Python3.10.20/pytest8.4.2 before the
first real selected member is opened. No production data was read locally.

Eight-entry bundle (old pinned source guards, reader, launcher, two suites,
two wrappers, UNBOOKED reservation): SHA256
`94310367a5269b4354c081b43f52cc995d545a998b4068ea8a5bfef00312d5a2`.
Literal exclusive-claim-before-sbatch command SHA256
`a8a28da3e7a07261dac547c48d2d83ef85797e049379e4d69319382017890cc8`.
Files are in `results/data_audits/svupp_provenance/2026-10-09/`.
OneCPU/2GiB/2min Slurm allocation wraps the narrower45s runtime gate. No
source/book change, staging, root creation or submission has occurred.

Independent maintained Sol6.1/high reviewer must inspect this exact proposal,
all eight pins and literal, old accepted metadata/closed attempts, the source
and nested-read distinctions, resource totals, sample/truth inference scope
and the current-kanpig novelty boundary. A conditional acceptance may permit
only booking status/time and their dependent hash repin; all scientific
inputs, controls and limits must remain unchanged. New objections must be
resolved prospectively, not after observing headers or outcomes.
