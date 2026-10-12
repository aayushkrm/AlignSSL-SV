# Independent review of the fixed inversion case

13 October 2026, Asia/Tomsk. Maintained reviewer; requested Sol6.1/high continues.
Model and effort are not independently attested. Only this sidecar is owned.
Main owns integration, source analysis, worker acquisition and PROGRESS.

## Decision

**ACCEPT the frozen source diagnostic. A small inspection of existing case inputs
is worthwhile if compatible outputs leave a residual. HOLD a new mechanism claim,
the original complex-INV hypothesis and any expensive campaign.**
The fixed Tier 1 simple inversion can expose an alignment, candidate or filtering
loss. It does not establish failed complex-allele linkage. Its strongest present
value is cheap discrimination among known explanations, with an early exit if
an existing strong call already resolves the declared event.

I fully read the goal objective, [feasibility note](2026-10-13-inversion-case-feasibility.md)
and [frozen protocol](2026-10-13-inversion-fixed-case-protocol.md).
The supplied freeze commit is 8e8c76e, before main/worker VCF-body inspection;
I did not check Git. Keep the first Table S10 HG002 row:
chr2:240685775–240688980, reported 3,205 bp. No case substitution follows a closure.
HG002 annotation and HG008 generic-detection stops remain in force.
The full publication goal remains active and unmet; DeepSV supplies no foundation.

## Independent supplement check and pending panel

I checked main's retained official Supplement 3 DOCX: 4,974,841 bytes, SHA-256
`2361934370695d00ef6844d8f77a036bb4313ec45228909b0596d683e9cff5af`.
I read the complete relevant text/table/caption and inspected existing render
pages 5–7 for Table S10/Figure S15. No second download or render was performed.
The [official source](https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs13059-026-04223-7/MediaObjects/13059_2026_4223_MOESM3_ESM.docx)
lists the first row and reports eight Tier 1 misses with assembly/Strand-seq signals.

| Evidence | Claim supported | Limit |
|---|---|---|
| Supplement panel definition | Five callers × ONT/PacBio × Minimap2/VACmap = 20 results | Includes cuteSV2, Severus, Sniffles2, SVIM and SVision-pro. Not all nine publication callers; combinations sharing inputs are not independent replicates. |
| Table S10, pages 5–6 | Author-selected Tier 1 residual; fixed row and printed size | No coordinate convention is proved by the size difference. Simple-INV scope does not imply a complex linkage defect. |
| Figure S15, pages 6–7 | GRCh38/hg38 label; four read tracks and four maternal/paternal assembly-alignment tracks | Screenshot support is inspectable. It does not supply read identities, mapping ambiguity, exact junction sequence, biological CN or an independently resolved allele. |
| Accompanying prose | Authors assert Strand-seq and assembly signals for all eight | No case-specific Strand-seq track in S15. Orientation support and assembly-derived breakpoint/phase claims retain separate scopes. |

At the initial review inventory, results/inv_fixed_case_20261013/sources.json
was absent. Acquisition is pending here; no caller/truth body was read or scored.
The frozen 20 long-read files, Manta/Gridss2 extra controls and three truth files
are an adequate finite source panel for this first comparison, not an exhaustive
current-caller benchmark. Preserve the ≤7-MiB body cap, pinned full Git blob SHA1,
SHA256, byte limits and gzip EOF/CRC receipts. Missing/incomplete files stay pending.

The source commit is ee77a2f336bf055e5234d7565389aafda56b85cd, dated December 2, 2025
as supplied. It remains an older seven-caller release. Do not claim it reproduces
the August 2026 nine-caller execution. Inspect headers before judging the
HG002_T2Tv1.1_asm_ref_2aligners.merged* filenames: T2Tv1.1 may name an input
assembly. Contig names/lengths alone do not certify reference bases or sample identity.
Figure hg38 labels and source headers need a declared crosswalk, not guessed liftover.

## What must precede a mechanism claim

Use the frozen inclusive endpoint window chr2:240684775–240689980. Retain POS,
END and BND-mate endpoints, plus separately identified spanning intervals.
Keep raw records, FILTER, genotype, orientation fields and relevant header provenance.
Resolve anchored VCF versus table coordinates explicitly; do not silently shift truth.
For symbolic INV, coordinates and size are declarations, not full allele sequence.

Separate two questions: is an inversion representation in the released files,
and does the original all-types output recover the relevant allele structure?
An INV-only export can discard BND/DEL/DUP or joined complex records. Absence from
that export cannot identify original candidate failure. Where original output is
unavailable, keep the narrower result; do not label the whole caller as failed.

Main reports author matching scripts use `--pctseq 0`, `--pctsize 0.3`, `--pickmulti` and
1-kb/10-kb/100-kb reference-distance allowances. These settings test permissive
declaration matching, not sequence identity or complete structural truth.
Inspect nearby compatible records, both breakpoints and orientation separately.
Report any normalization/matching discrepancy as such. A metadata/parser correction
or altered matching rule is not automatically a new scientific contribution.

| Source outcome | Consequence for the next step |
|---|---|
| Strong compatible existing call declares the event | Close this fixed case's unmet-presence premise. Exact sequence/phase may remain unresolved; no input trace solely to reproduce known detection. |
| Compatible source panel lacks an INV declaration | Reproduce a selected reported miss only. A small existing-input inspection can distinguish alignment loss, insufficient evidence, candidate loss, filtering or export loss. |
| Reference/version/coordinate scope cannot be resolved | HOLD interpretation. Headers and existing provenance are the next bounded checks; incompatible inputs are untested, not failures. |
| All-types output already encodes equivalent structure | Close the original calling-gap claim for this case. An export/evaluator issue may be real without supplying a new calling method. |
| Input distinguishes the allele but a strong applicable method loses it | Retain one explicit mechanism hypothesis. Need the loss stage and distinguishing evidence before any intervention or larger release. |

## One useful next inspection if the residual survives

Use existing released per-read alignments, candidate logs or a small qualified
case-input excerpt, if available. Main must separately state availability and cost;
this review authorizes no acquisition or native job. Do not require a full assembly
proof before inspecting those inputs. Full input absence is a feasibility HOLD.

Trace a declared discriminating chain: a read/contig's ordered query coordinates
and strand changes support the two inversion junctions; those signals enter a
candidate; candidate support passes/fails configured filters; output/export retains
or loses the event. Record each unknown stage. A screenshot cannot establish this
chain, and a negative final VCF does not locate its cause.
Inspect alternative mapping placements and whether both junctions are linked on
observed molecules. Compare an inverted path with plausible reference/repeat or
different-structure alternatives. Do not insert truth sequence into caller input.
Assembly alignment and assembly-derived truth share evidence; Strand-seq mainly
tests orientation. High allele fraction/read-stack density is not biological CN truth.

Main's supplied [SVision-pro primary check](https://www.nature.com/articles/s41587-024-02190-7)
already describes read-ordered M/V/I candidates, segmented subcomponents and joined
complex structures, with default 10-read candidate support. I did not re-audit it.
Thus basic junction linkage/segmentation is prior art. A real 10-read threshold
loss would require the case's actual command and support counts, not a default
or visual count; lowering a threshold also requires false-positive controls.
Keep Severus, SVision-pro and the strongest compatible platform/aligner outputs.
Missing access to every model is not a universal entry gate. A later superiority
claim must test applicable strong methods or restrict its stated comparison.

Hold information equal within each input track: reads, reference, allowed priors
and available normal/assembly evidence. Disclose graph-panel and training/sample
membership if a later comparator uses them. Extra truth-building contigs or phase
labels are extra information; distinguish discovery from assembly-conditioned recovery.
Clinical phenotype is unnecessary for a molecular calling question. Exact clinical
or CN/phase claims would need evidence for those endpoints.

```text
qualified frozen outputs -> existing equivalent allele? -> yes: close case
                         -> no: inspect existing case inputs
                                ambiguous/insufficient -> limit or HOLD
                                distinguishable -> trace one loss stage
```

Any residual here is development evidence from a selected HG002 simple inversion.
It cannot confirm a complex-INV mechanism without an explicit supported complex
structure. Freeze a cause before selecting future confirmation loci/samples;
hold those out from tuning, include hard negative/nearby alternate structures,
and test precision as well as recovery. Reuse of HG002 truth in design is disclosed,
not an untouched test. One rescue does not establish prevalence or publication value.

Audit: documents skill, read/review and writing references read; bundled runtime
used for read-only DOCX extraction/hash; existing main render reused. No VCF outcomes,
genomes, BAMs or models inspected; no installs, downloads, jobs, Git or historical edits.
Only this note was written. Maintained scrutiny continues before costly work or
acceptance of a major positive claim; neither is approved by this initial review.

## Actual packet addendum 13 October 2026

**ACCEPT the completed local source packet and its fixed selection. Reject the
zero-INV-record premise. HOLD allele equivalence and calling-mechanism claims.
A bounded comparison of pure-inversion strings on an existing qualified reference
is worthwhile before an input trace. No native or expensive work is released.**
This updates the earlier pending status. I independently read the 25 cached bodies
listed in [sources.json](../../results/inv_fixed_case_20261013/sources.json), status
COMPLETE, under runs/inv-fixed-case-20261013.EBNrEy outside the repository.
All listed sizes, SHA256 and Git blob SHA1 pass; total 6,087,705 source bytes.
All three gzip files pass complete decompression/EOF/CRC, within expanded limits.
EOF record counts and raw endpoint/mate/spanning selections match the packet.
The additional 168,192 tree bytes are packet-reported, not a new remote audit.
Reviewed sources.json SHA256:
`8f49e113eb3dd0e0071694d340a4b0701fed8ea42475d5993c16894e35bfe52e`.
This accepts these finite contents; it does not certify pending worker checks.

All 25 files declare chr2 length 242193529, consistent with the hg38 figure label.
Some commands/reference paths name GRCh38. Neither fact certifies reference bases.
Merged/Tier1/Tier2 truth counts are 125/72/53. The fixed record is identical in
merged and Tier1, absent from Tier2: REF N, ALT<INV>, FILTER PRECISE, GT0/1,
POS240685775, END240688980, SVLEN3205, SOURCE MATERNAL, with ORIGINAL_LOCUS
chr2_240685789_240688966. PRECISE is the actual filter token, not PASS.
Repeat_ge5Kb=rp2sides and Repeat_ge10Kb=rp2sides are source annotations;
I did not independently validate repeats. CIPOS/CIEND are also declarations.
Main retains coordinate-writer analysis; no correction or truth shift is inferred.

| Released caller selection | Raw declared POS–END and length | GT and limit |
|---|---|---|
| Severus ONT/Minimap2, one endpoint in window | 240685789–240702018; 16229 | PASS, GT0/0, DR22/DV3, VAF0.12. Start equals ORIGINAL_LOCUS start; far end differs. Candidate presence is not a heterozygous call or exact allele. |
| Severus ONT/VACmap, three spanning | 240676267–240698636; 22369. 240676330–240698570; 22240. 240680925–240693788; 12863. | PASS; GT0/0,0/1,0/1 respectively. Endpoints outside the window; intervals retained under the frozen rule. |
| Severus PacBio/VACmap, two spanning | 240676309–240698591; 22282. 240680925–240693788; 12863. | PASS; GT0/0,0/1 respectively. |
| Sniffles2 ONT/VACmap, two spanning | 240676330–240698570; 22240. 240680925–240693788; 12863. | PASS; both GT0/1. Shared alignment/intervals do not give independent biological confirmation. |
| Sniffles2 PacBio/VACmap, one spanning | 240680927–240693790; 12863. | PASS, GT0/1. |
| Other 15 long-read files and Manta/Gridss2 extras | No selected endpoint/mate or spanning record | Qualified absence from these exports under the frozen rule, not from original all-types outputs. |

Thus nine caller declarations survive the frozen selection: one nearby and eight
spanning. None declares the literal target POS/END/3205-bp geometry. Repeats and
larger intervals could reflect equivalent representations or different alleles;
neither follows from overlap, an INV tag, GT or the qualitative IGV tracks.
Severus headers name v1.1 and Sniffles2 2.7.0. Files named svisionpro say
SVision v1.9; that label alone does not qualify the exact SVision-pro executable,
weights, command or its all-types output. Source-2025/publication-2026 limits remain.

## Bound the reference equivalence diagnostic

Use one existing reference with qualified base identity and a small common outer
interval containing the fixed truth and all nine retained declarations, with
identical unchanged flanks. Main must first resolve the declared interval/anchor
semantics. Preserve every raw candidate and treat any ORIGINAL_LOCUS hypothesis
as separately labeled. Do not search breakpoint shifts to obtain a match.

For each declared pure inversion, replace only its interval with its reverse
complement; compare the resulting complete local alternate strings exactly.
Keep genotype as a separate field. This tests a reference-conditioned pure-INV
model, not actual sequence-resolved haplotypes. Unknown bases, unmatched reference
identity or unresolved coordinate semantics make equality inconclusive.
No genomes, assemblies or models need acquisition for this reviewer action.

```text
same qualified reference + declared interval semantics + fixed candidates
       exact alternate strings equal -> equivalent under pure-INV model
       exact alternate strings differ -> distinct under that model
       reference/semantics unresolved -> HOLD without caller-failure label
```

Equality with a GT0/1 candidate can close the unmet declared-presence premise
under that explicit model. Equality with GT0/0 shows candidate representation,
leaving genotype recovery unresolved. Neither proves maternal phase, copy state,
the actual molecular allele or correctness of the benchmark's permissive matching.
Inequality removes that particular pure-INV equivalence explanation; complex
components, actual haplotype sequence and export loss can still alter interpretation.
It does not prove a distinguishable input or locate a caller defect.

Proceed to the earlier small existing-input trace only if a residual remains and
case inputs can distinguish it from alternatives. Keep strong applicable controls
and inspect original output scope before attributing failure to candidate linkage.
No case reset, metric change, or threshold tuning is supported. This selected
simple-INV diagnostic still cannot confirm the original complex-INV mechanism.
Any intervention remains development work; independent held-out confirmation and
false-positive controls are required before major claims or a larger campaign.

Audit: local bounded reads only, no re-fetch or native run. Original 137 lines
are preserved byte-for-byte; only this owned note is appended. No source, history,
PROGRESS, jobs, installations or Git state changed by this review.
