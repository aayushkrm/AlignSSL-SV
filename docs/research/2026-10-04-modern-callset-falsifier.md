# Modern same-input call-set completeness: bounded development falsifier

Date: October 4, 2026 local / October 3 UTC. Status: high-impact direction
decision; outcome protocol not frozen, no biological scoring approved.

## Why this test

The Sol6.1/max-requested decision agent Aristotle selected this test after
the [updated-goal/prior-art review](2026-10-04-updated-goal-and-prior-art.md).
The generic open-panel confidence and personal-normal rescue proposals are
stopped as publication leads. Do not acquire the Locityper database to rescue
them. Actual agent model execution is not independently attested.

Question: do contemporary, complementary caller outputs on the same HG002
read dataset leave stable, confidently callable structural alleles missing
from their union in Q100-defined hard regions? Surviving misses must have a
recoverable observation mechanism before a new generator is justified.
A caller union alone is neither a method contribution nor an internal
candidate-generation ceiling. This donor is development-only.

The proposed scientific stage uses sequence-resolved autosomal INS/DEL >=50 bp,
an exact Q100 truth release and its confidence BED, a fixed hard-region mask
and ordinary-region comparator, native caller filters, two existing fixed
matching approaches including local haplotype equivalence, block uncertainty
and deterministic adjudication of at most 20 stable misses. Thresholds,
versions, selected files, truth/territory hashes and matching rules remain
unfrozen until concrete compatible inputs are identified. No scoring is allowed
by this note alone. An independent Sol6.1/high protocol review is required.

Reject a discovery investment if no stable eligible misses remain, or all
apparent misses are representation/truth artifacts. Reject a read-recovery
method if surviving misses lack usable read evidence. Incompatible data and
inadequate precision are feasibility failures or inconclusive results, not
biological nulls. Unrelated donors and independent event-cluster confirmation
are required before a major positive claim. Record graph membership, including
HG002 and relatives. Count truth construction and graph/alignment production
costs, not just cheap scoring of precomputed outputs.

## First-party source evidence

The published [SVPG article](https://www.nature.com/articles/s41592-026-03219-2)
links the versioned [Zenodo 18456502 release](https://zenodo.org/records/18456502).
The API manifest describes v2, published February 2, 2026, with:

| File | Bytes | Publisher MD5 | Current handling |
|---|---:|---|---|
| `scripts.zip` | 18,200 | `57dce6316194c5147628b9cb933367fb` | Downloaded outside Git; size/MD5 and ZIP CRC passed |
| `SV_callsets.zip` | 2,879,666,672 | `a6ea80f613130c318d36632073c6de97` | One transfer completed; whole size/MD5 and local SHA-256 verified |
| `augment_graph.zip` | 3,392,957,239 | `d5d89b7009f2e14638bf4ba394611da9` | Not requested; not needed for this initial test |

The latest-version API returned a redirect to the same record. This is not
proof that the February archived calls were generated with September's final
paper executable versions; check their actual run provenance before pooling.

The scripts ZIP contains 12 entries, 11 files totaling 53,971 uncompressed
bytes. Its SHA-256 is
`cc7f077cee6a1e0c503aa21d04e935feae44f79ee32857343017bdb16215091e`.
Only source was read, not executed. Saved whole-file inventory and SHA-256 are
under `results/data_audits/svpg_2026/2026-10-04/`. The source-only inspection of
`eval_inconsistency.py` shows directional event matching, not a test requiring
genotype agreement between matched records. `merge_specfic.vcf.py` subtracts
same-type normal calls within 1,000 bp without allele-sequence equivalence.
These are code semantics, not an estimate of biological error or a claim that
they produced every final-paper figure.

The existing strict remote-ZIP reader attempted a central-directory inventory
under a 1-MiB network cap. HEAD declared the expected size and Last-Modified,
but the subsequent EOF range omitted or changed the validator. The reader
failed closed at offset 2,879,666,650, before publishing an inventory. No
member payload was requested. Do not lower its validator requirement or call
the publisher MD5 verified without the entire file.

## Separate acquisition scope approved after that failure

Anscombe's independent Sol6.1/high-requested review approved this scope after
reading the separate proposal. Actual model execution remains unattested.
This stage does not change the prior Locityper gate or approve scientific
outcomes. It allows exactly one complete download:

- URL: `https://zenodo.org/api/records/18456502/files/SV_callsets.zip/content`.
- Exact size/MD5: the table above. Retain a local SHA-256 as well.
- Store outside Git in the existing source-archive directory. Use a new partial
  path and do not overwrite an existing verified object.
- Maximum payload: 3 GiB; maximum transfer wall time: 30 minutes; one transfer,
  no graphs, read alignments, genomes or additional large archives.
- The initial local filesystem check reports about 20 GiB free. Retain at
  least 10 GiB of free local space; do not unpack the full archive.
- After size/MD5 verification, inspect central-directory names/sizes and frozen
  selected source/readme or VCF headers only. No archive extraction, script
  execution, genotype/truth comparison or outcome/performance-table reading.
- At most 256 MiB of subsequently selected VCF/truth input for the proposed
  scientific stage, at most two CPU-hours and 4 GB RAM, no GPU or cluster job.
  Any biological scoring requires the separate exact-file outcome protocol.

Why this larger transfer may be justified: it can settle modern, same-input
caller availability where the old Parliament2 and concatenated-package routes
could not. A complete publisher-MD5 check is the alternative to unreliable
partial HTTP reads. It does not justify repeated full archives if the run or
reference gate fails. This approval excludes extraction, code execution, VCF
records, outcome scoring and additional downloads.

## Close-prior-art mechanism sidecar

Raman (Luna/max requested) inspected the primary
[Qin and Li low-complexity paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12758381/).
It already relates misses to long low-complexity alleles and illustrates
alignment instability in an imperfect repeat. Generic LCR stratification,
realignment or the statement that repeats cause errors is not a new contribution.
Repeat purity after controlling variant and repeat length is a proposed
diagnostic extension, not an established novel mechanism or selected experiment.
The paper's released LCR mask is GRCh38; our tentative HG002 package route is
GRCh37. Do not apply that mask across references or assume call sets are loaded.
No repeat-purity outcome has been measured. Treat this as a future hypothesis
only after compatible truth, sequence and native outputs exist.

The sidecar made two Exa queries with five requested results each (10 slots,
not 10 papers read), checked the primary Qin/Li Methods and Results, and checked
selected minisv sections. It corrected its initial claim that SVPG calls were
already loaded; only scripts were verified when it made that claim. Main
separately checked the Qin/Li primary methods. No sidecar project outcomes
were inspected or scored.

The already staged cluster data include an indexed hs37d5 FASTA and current
GRCh37 HG002 v5.0q SV truth/BED. NIST's current README identifies **Q100 assembly
V1.1** as its source too. Assembly version and variant-benchmark release are
different identities: the older November 2024 DeFrABB v0.019 release and current
v5.0q/DeFrABB v0.020 release are not interchangeable, even though both use that
assembly. The paper's Q100 V1.1 label alone does not identify the variant-release
bytes. A diagnostic using v5.0q must be named explicitly, not called a replication
of the paper's exact benchmark. A fresh read-only account queue is empty.

## Completed acquisition and frozen header check

The single whole transfer completed within the approved scope. Whole size and
publisher MD5 passed before the partial file was promoted, without overwrite,
to `data/source_archives/svpg-18456502-SV_callsets.zip` outside Git. Its local
SHA-256 is `fff2f1d2978234a1357c6a16ce5ed9fabf17925955247ae2f9ee2ee8564eb7ca`.
The inventory report truthfully names the pre-promotion `.partial` file; the
header report names the verified final object with the same identity.
There are 203 entries with 13,178,958,258 declared uncompressed bytes. No full
extraction or all-member CRC check was performed. The publisher checksum is a
whole-file integrity check, not proof of biological validity. About 18 GiB free
space remains, above the 10-GiB guard.

Before any member header or outcome was read, `header_protocol.json` froze all
six full-HiFi caller members under `HG002_benchmark`, excluding downsampled,
pedigree, rare and somatic files. The existing verified-ZIP reader read 33,048
header bytes in total, under 1 MiB per member / 6 MiB overall. All six have
byte-identical declarations for 86 contigs; none declares sequence MD5s.

| Caller directory | Header identity | Raw input evidence | Decoded file bytes |
|---|---|---|---:|
| cutesv | cuteSV 2.1.1 | Shared HG002 BAM and hs37d5 path strings | 30,029,207 |
| debreak | DeBreak; version absent | Same BAM and reference strings | 935,962,599 |
| sawfish | Sawfish 2.0.3 | HG002 discover-directory; reference path; raw BAM absent | 25,716,015 |
| sniffles | Sniffles 2.3.3 | Same HG002 BAM string | 15,004,300 |
| svim | SVIM 1.4.1 | No command/input identity | 6,682,295 |
| svpg | Version and command absent | Generic sample name only | 23,624,851 |

This supports reference-dictionary compatibility and declared shared inputs
for three callers, **not** exact raw-byte identity, depth, donor identity for
generic sample columns, graph membership, or final-paper executable identity.
The independent reviewer is checking the permissible development estimand.
Do not claim a controlled same-input ceiling from these headers. The six files
declare 1,037,019,267 decoded bytes; DeBreak alone exceeds the earlier 256-MiB
scientific-stage bound. Including all six therefore needs a separately reviewed
streaming budget amendment. Do not omit it merely to obtain a favorable union.
No biological rows have been parsed or scored at this checkpoint.

### Supporting source-contract diagnostic

Poincare's Luna/max-requested worker implemented an independent synthetic
model and static AST checks of the pinned evaluator. Main reviewed it and
added bounded source reads and two wrong-identity controls. All 15 focused tests
pass. `synthetic_script_contract.json` records one event match and zero event
inconsistencies for identical geometry with GT `0/1` versus `1/1`; a phased
`0|1` is excluded. Four identity/geometry negative controls remain unmatched.
Downloaded source was parsed as data, never compiled or executed. This is a
narrow source-contract counterexample. It does not establish real frequency,
genotype accuracy, final-paper figure execution or a publication contribution.
