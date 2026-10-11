# Native CIGAR invariance: proposed diagnostic

2026-10-09. Experiment ID: `native-cigar-invariance-20261009-01`.
Latest status: **SCIENTIFICALLY SELECTED; NOT BOOKED OR EXECUTED**.
[Value decision](2026-10-09-native-invariance-value-decision.md) selects the
diagnostic; [independent review](2026-10-09-native-invariance-review.md) accepts
the corrected code/observation contract. Exact launch/account review remains
pending. The specification below began as a candidate and does not constitute
an execution bundle. This does not reopen the released-callset
screen or select a publication direction.

## Question

Can two valid alignments of the **same molecules to the same reference**
produce different native allele recovery? Does an existing native evidence
setting remove that difference? The source predicts a difference in one
CIGAR-evidence branch. The experiment asks about the complete caller, not
just that predicate. It is a controlled software diagnostic, not a simulation
of HiFi error, a mapper comparison, or a human performance benchmark.

```text
One reference + one exact ALT haplotype + fixed molecules
              |
              +-- one 60I -------- default caller ------- positive control
              +-- 20I/5=/20I/5=/20I -- default caller ---- diagnostic
              +-- same fragmented CIGAR -- native margin30 -- rescue control
REF-only molecules ---------------- default caller ------- negative control
```

The reference is `chrSynthetic`, 4,000 bases: seeded random 1,000-base
flanks around 2,000 A bases. The ALT inserts 60 A bases before reference
offset 1,500 (zero-based), giving an exact 4,060-base haplotype. Each primary
arm has 20 REF and 20 ALT reads. The REF-only arm has 40 REF reads.
Endpoints vary by a fixed rule. Within the primary pair, read names, bases,
qualities, MAPQ, endpoints, flags, read group, NM and MD are identical.
Only the 20 ALT CIGARs change. Every `=` operation must match actual reference
bases; both CIGARs must consume the same query and reference lengths.
This does not assert equal alignment optimality or natural mapper frequency.

## Fixed caller and arms

Sawfish v2.2.1 author Linux asset is the candidate executable. Its declared
SHA256 is `869d866d1399bd9803b3c60cc0e260ed1f60aa38a6f40d46f3093cd4bf5631f4`;
the downloaded bytes and runtime still need verification. Inspected tagged
source is `8fdf4cf1b16e366ae8291d4547a1da06affc5c4a`.
No mapper is needed for this edited-alignment diagnostic.

| Order | Input | Discovery setting | Purpose |
|---|---|---|---|
| 1 | Canonical heterozygous | Defaults, CNV disabled | Exact-allele positive control |
| 2 | Fragmented heterozygous | Same defaults | Representation contrast |
| 3 | REF-only | Same defaults | Exact-allele negative control |
| 4 | Same fragmented input as arm2 | Noise margin30; reporting minimum35 unchanged | Existing native rescue control |

Use the complete tiny reference, not debug `--target-region`. Use one thread
in every command. Do not use fast-CNV mode, clobber, threshold sweeps,
different assemblies, or a new read set after outcomes.
Pinned source gives default CIGAR evidence25bp, and margin30/report35 gives
5bp. This is not a universal locus cutoff or installed-binary attestation.

Source-supported command shapes, to be frozen with actual executable and
input paths before launch:

```sh
sawfish discover --threads 1 --ref <reference.fa> --bam <arm.bam> --disable-cnv --output-dir <fresh-discover>
sawfish joint-call --threads 1 --sample <fresh-discover> --disable-cnv --output-dir <fresh-joint>
```

Only arm4 adds `--min-indel-size-noise-margin 30` to discovery. Do not change
the reporting threshold, minimum quality, MAPQ or identity filters.
Main re-read the full pinned shared CLI through the connected Firecrawl
plugin: `--threads` is global and rejects zero. Other command facts come from
the prior pinned guide/CLI audit; executable acceptance is still untested.
[Shared source](https://github.com/PacificBiosciences/sawfish/blob/8fdf4cf1b16e366ae8291d4547a1da06affc5c4a/src/cli/shared.rs).

## Endpoints and stops

Parse all records in each explicitly named output. A literal record counts
as exact only if its REF matches the reference and applying REF->ALT to the
whole reference yields the exact frozen 4,060-base ALT haplotype. Left shifts
within the A run are admissible because the resulting haplotype is identical.
No coordinate/length tolerance or overlap proxy is used. Symbolic and
multiallelic records remain counted as unresolved; do not silently exclude
them or interpret them as confirmed negatives. Multiple nonmatching edits
that could jointly encode the expansion also prevent a full-haplotype
absence claim unless a valid joint reconstruction resolves them. This
diagnostic does not assume phase from sites-only candidates.

Observation states: PRESENT when an exact single-record allele is found;
ABSENT from that output only when all records are examined and no relevant
unresolved representation remains; otherwise UNRESOLVED. A known exact
match still establishes presence when other records are unresolved.

Report discovery candidate exact-allele counts (sites-only is allowed), final
exact-allele counts, FILTER counts, PASS exact counts and exact heterozygous
GT counts, including a **joint exact+PASS+heterozygous count**. PASS means an
explicit `PASS` filter, not bare `.`. The intended final recovery endpoint
is an exact allele with explicit PASS and GT0/1 or1/0, phased or unphased.
Final outputs must contain sample `SYNTH`. Keep the distinction
between an absent record, a non-PASS record, and a wrong genotype. Report
assembly BED coverage and contig counts/lengths as stage metadata only;
they are not exhaustive rejected-signal traces or causal absence labels.
Read each bounded `discover.settings.json` to verify resolved35/10 or35/30;
do not replace observed settings with the source defaults.

If the canonical arm has no exact PASS heterozygous recovery, stop this
execution incomplete: the positive control did not establish the intended
assay. Do not increase depth, shorten the repeat, add reads, or tune settings
inside this experiment. Any missing/unparseable output, changed input,
unresolved-only endpoint or failed negative control prevents a complete
invariance claim. Retain raw outputs and logs. These are diagnostic stops,
not a biological null or a permanent rejection of all native research.

| Complete result | Permitted interpretation |
|---|---|
| Both primary arms meet exact+PASS+heterozygous recovery | This fixture does not support loss of that final endpoint from fragmentation. Report candidate presence separately. |
| Canonical meets that endpoint; fragmented retains the exact allele but fails PASS or GT | Final-endpoint sensitivity, not exact-allele disappearance. |
| Canonical meets that endpoint; fragmented loses resolved exact-allele presence; margin30 recovers | A local representation sensitivity is removable by an existing native setting. No new generator or learned rescue contribution follows. |
| Canonical meets that endpoint; fragmented fails it; margin30 also fails it | The chosen native setting is insufficient here. Separate absence, filtering and genotype failure; no unique causal stage or novel rescue is established. |
| Positive/negative control or integrity fails | Assay incomplete/invalid. No biological or invariance result. |

Generic fragmentation merging and consensus rescue are already prior art
(TRsv, Svirlpool, Qin/Li). A single synthetic contrast cannot establish real
prevalence, clinical importance, label efficiency, purity causality or novelty.
No learned arm, significance test or performance gain is justified here.
A real read-backed follow-up would require a separate scientific design.

## Proposed finite account and execution boundary

The prior retained account is40,235,307,915 bytes and556.722707 named CPU
seconds. Keep all historical charges. Proposed new allowance: **256MiB**,
not yet booked. Proposed retained total40,503,743,371 bytes remains below
68,719,476,736. Proposed600 named CPU seconds gives prospective1,156.722707
below7,200. This is a named conservative allowance, not measured physical
I/O or total historical project CPU. No old unbooked screen margin is moved.

The allowance includes the <4MiB asset, bounded extraction/verification,
synthetic inputs, controls, code, multiple explicitly bounded output reads,
hashes and raw archive. Before launch, freeze a concrete allocation of these
passes and output caps; this paragraph alone is not a complete I/O ledger.
One fresh scratch root, one CPU-only submission, at most four discover and
four joint-call payload commands. No genomic input, raw-data download,
training, all-six preparation, production contract change or other users'
jobs. Exact runtime containment, submission claim, code hashes, full-tree CPU
measurement and archive limits still require code/command review.

Metadata preflight at2026-10-09T09:16:53+07: account queue empty, x86_64,
glibc2.34. Scratch expires2026-10-22T23:02:50+07, one extension available.
Local free18,414,352KiB (about17.6GiB). These are timestamped observations,
not continuing guarantees or caller compatibility checks. No jobs changed.

The previous agents failed on account limits and saved no implementation.
A fresh account query now permits ordinary use. New workers request Luna/max;
the decision requests Sol6.1/max; the maintained replacement reviewer requests
Sol6.1/high. Configurations are requested, not independently attested. No
scientific reservation or native run is implied by software development.
