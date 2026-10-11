# HG002 complete source-read extraction

Recovered authoritative terminal evidence on2026-10-11. Job1604284
COMPLETED0:0:7709allocatedCPU seconds at1CPU, reported TotalCPU01:56:28,
stepMaxRSS101784K. Process manifest records7708.222s wall/6988.313s CPU.
Frozen source40679be522fbf2dd582a6826d72cfc02b9d77443f60095dcabb5a9d4efec681a
matches the independently accepted02 extraction packet. No duplicate run.

The unchanged [raw readiness manifest](../../results/hg002_read_extract_20261010/readiness.json)
reports both complete EOF passes, each5,710,994records. It emits exactly
5,359,077original QNAME identities and80,344,827,828bases, matching archive
counts. Conflicting, malformed, constraint-mismatched and unknown identities
are all0. All351,917supplementary records are duplicate full-read payloads;
578unmapped records are retained. Hard clips/missing sequence or quality,
secondary/QC-fail/duplicate-flag counts are0 in the full object, not a prefix.
This is read extraction, not a biological positive/negative or paper result.

## Scope and integrity

Completed level1 gzip:41,582,125,285B, SHA256
`fd9fd85d7dfadca083cd101aad00932e16d23d8b5d90db4ddec7523abaabae88`.
SQLite1,040,932,864B. Source BAM SHA256 remains
`b7edeb4bbc2589039c6148a912857f26924ca8fd5971cd3141337d0ce24bbde4`.
No original genomic sequence or gzip is copied to the laptop or Git.
Counts match ENA but no independent raw ENA sequence/quality equivalence is
proved. A filename, extraction READY or count agreement alone cannot release
calling, reconstruction, phase/copy qualification or P1.

One source RG:HG002_WGS, sampleHG002_WGS, READTYPE=CCS, REVIO.
HP occurs on5,163,699records with values1/2;547,295records lack it.
PS has only one observed value1. These are record-level counts including
supplementary copies, not unique phased molecules or validated blocks.
FASTQ does not carry these tags. Old-reference identity is still unproved;
future calling must remap all source reads to the matched reference unless
exact compatibility is established. No old HP/PS transplantation is certified.

## Actual accounts and custody

S1 acquisition/raw custody8080s plus extraction7709s =15789allocatedseconds;
13011s remain of28800. Body transfer stays48,749,105,446B cumulative; no
second library/body is acquired. Manifest sampled peak140,176,254,335B fits
160GiB, but that observation is not continuous storage enforcement.

A planned recoverable atomic directory move is rejected before any change:
scratch and home have deviceIDs50/52. No move/copy/delete occurs in that failed
preflight; the subsequent home-only small-manifest fetch fails because the
destination does not exist. Main obtains the original final manifest from
scratch instead. Failures are not dataset incompleteness or an extraction replay.

A second full readset/index copy with both raw BAM copies would exceed S1's
160GiB cap. The existing protocol permits main to remove redundant scratch
only after custody verification. Main prepares read-only QA of both raw BAM/
BAI copies, the completed gzip hash and full EOF/CRC, SQLite quick_check and
matching whole census, metadata hashes, and unchanged before/after stats.
Only after PASS and independent finite audit may main remove the redundant
scratch BAM48,727,325,910B, keeping the original whole verified home BAM,
BAI and all acquisition logs/manifests/ledgers unchanged. Its bytes remain
recoverable from home. This is duplicate cleanup, never a read/locus crop.
Then one complete result copy to home projects about134GB aggregate S1,
including the remaining scratch readset, both SQLite copies and raw artifacts;
exact observed inventory must be checked before copying. No extra budget.

QA packet [verify_hg002_s1_custody.sh](../../scripts/verify_hg002_s1_custody.sh)
SHA256dc6bc3daa1c68f726610cc752518609634eee14537ca3332a3303fe7befabbd0,
1CPU/4GiB/1h inside remaining S1. Maximum additional3600s leaves9411s;
charge actual scheduler cost. No deletion is implemented by this script.
QA1604300 is now RUNNING on hydra-n1/amd_256M at1CPU/4GiB/1h.
At459elapsed seconds, both HOME/scratch raw BAM+BAI hashes and the whole
extracted gzip SHA have passed; gzip EOF/CRC and SQLite checks are pending.
The maintained independent reviewer accepts the completed extraction record
and the exact duplicate-cleanup contract, conditional on terminal QA PASS.
No duplicate cleanup or full HOME backup has occurred. Usable-input acceptance
remains pending terminal QA and complete HOME result verification.
Exact caller settings/resources/phase recipe need a
separate S2 review; S2–S4/RNA remain unreleased. Full publication goal unmet.
