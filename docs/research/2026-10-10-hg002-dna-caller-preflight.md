# HG002 calling-before-assembly preflight — UNBOOKED

2026-10-10. Independent planning sidecar; requested Luna/max, not backend/effort-attested. Main owns scientific choices and release. This note neither books work nor changes the [stage decision](2026-10-10-hg002-dna-stage-investment.md), [intake protocol](2026-10-10-hg002-dna-intake-protocol.md), or [maintained review](2026-10-10-public-paired-falsifier-review.md). S2–S4, GPU calling and RNA remain unreleased.

**Yes: ordinary pbsv can produce the called non-reference DEL/INS input for the preliminary CDS index before new small-variant calling/phasing.** Its documented chain is alignment → SV signatures → SV calls and genotypes; neither a small-variant VCF nor HP/PS is an input requirement. This is a calling/cohort interface conclusion, not a completed cohort, phase certificate, P1 result or biological positive. [Official pbsv workflow](https://github.com/PacificBiosciences/pbsv/blob/v2.11.0/README.md#workflow).

```text
S1 complete reads + accepted exact S2 recipe
  → same-exact-GENCODE-reference remap → pbsv discover/call → full CDS index
      ├─ no called eligible events, unresolved records accounted: existing stop
      └─ overlap / unresolved potential overlap: retain; main reviews next stage
          → local SV–coding-sequence–target phase/copy proof → P1, separately gated
```

Calling-first can avoid buying small-variant phasing or assembly for an empty called cohort. It does not make whole-genome remapping/calling cheap by measurement. No phase-only UNKNOWN may be used to manufacture an empty cohort.

## 1. Source and reference readiness, separately

| Item | Existing evidence | Required before use |
|---|---|---|
| Exact BAM | S1a completed; home custody hashes matched. BAM 48,727,325,910 B, SHA256 `b7edeb4bbc2589039c6148a912857f26924ca8fd5971cd3141337d0ce24bbde4`. [Intake result](2026-10-10-hg002-intake-result.md). | Source integrity is not complete-read readiness. Do not substitute ENA FASTQ, split assembly BAMs, a second library or a partial extraction. |
| Full-source extraction | Job1604284 remains incomplete in the supplied state; no live query here. [Exact S1b packet](2026-10-10-hg002-read-extraction.md). | Final `readiness.json`: `READY_FOR_DNA_INPUT_REVIEW`, both passes complete, `archive_differences.complete_census=true`, all original identities resolved/emitted, no unresolved sequence/quality constraints; reconcile counts with archive, explain differences. Verify complete `source_reads.fastq.gz` size/hash and non-expiring custody. A filename, exit0 or prefix counter is insufficient. |
| Old alignment | Header: pbmm2 1.10.0, `hg38.analysisSet.fa`, no SQ M5. | Names/lengths and REF spot checks do not prove old-reference base identity. No existing evidence certifies reuse against the selected GENCODE FASTA. Plan full-read remapping, unless main establishes exact compatibility and reviews reuse. |
| Matched reference | Five expanded GENCODE50 products have CRC/hash and home-custody evidence. [Expansion record](2026-10-10-hg002-reference-expansion.md), [manifest](../../results/hg002_reference_expand_20261010/manifest.json). | Use that same complete primary-assembly FASTA for pbmm2, pbsv and any later phasing; keep comprehensive GTF/GFF, not canonical/cropped annotation. Validate new BAM dictionary and VCF REF against these bytes. |

Reference home leaf: `/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/hg002_reference_expand_20261010_01`.
`GRCh38.primary_assembly.genome.fa`: 3,151,417,447 B; SHA256 `e49b92b3e4f321bf254c042f25b726d9931c4d74c7523e8b6bb530e63b0cfd4b`.
`gencode.v50.primary_assembly.annotation.gtf`: 4,688,772,094 B; SHA256 `04af7379ad6c214f49758db270938a38c41bebbf7b9dc8e24065d8f3a9f08d0d`.
These are retained manifest facts, not newly measured genomic bytes here. The expansion payload totals 12,807,281,629 B per copy.

FASTQ extraction preserves original QNAME and forward sequence/quality, but does not carry per-record RG/HP/PS. A new alignment RG is declared run metadata, not restoration of all source tags. Full S1b RG/movie census, not the small prefix, determines whether a combined single-sample representation needs further provenance accounting. Keep every source molecule; no primary-only or phased-read subset.

## 2. Version and native-policy packet

GitHub release API returned the following on this check. These are documentation anchors, **not selected or installed runtimes**. Main must pin the actual executable, dependency/build versions, resolved path, binary/package hash, license and complete help/version logs. The existing native LiftOn aligner build does not attest pbmm2/pbsv/HiPhase availability.

| Tool | Official release API metadata | Versioned text blob SHA |
|---|---|---|
| pbsv | [v2.11.0](https://github.com/PacificBiosciences/pbsv/releases/tag/v2.11.0), published 2025-02-26T16:13:25Z | README `93dec00c8ac80d457d0acda55a47ea22cff0f044` |
| pbmm2 | [v26.2.0](https://github.com/PacificBiosciences/pbmm2/releases/tag/v26.2.0), published 2026-06-30T19:36:50Z | README `a1b484e21dfc5722bbb3063914454e4c7a666069` |
| HiPhase | [v1.7.0](https://github.com/PacificBiosciences/HiPhase/releases/tag/v1.7.0), published 2026-05-27T20:18:52Z | user guide `ffdd914aad46767da7b1a8118adda3006dfe9e21` |

Release tags/blob SHAs identify checked documentation, not executable hashes. pbsv's tagged README still labels latest as 2.10.0; pbmm2's as 26.1.99. Do not promote either heading to a runtime pin. The pbmm2 README's minimap2-version table is not independent proof of the dependency in a newer binary. [Versioned pbmm2 README](https://github.com/PacificBiosciences/pbmm2/blob/v26.2.0/README.md).

Native policy to retain and resolve before launch:

- pbmm2: explicit CCS preset, sorted output, declared `SM:HG002_WGS` and RG ID; retain unmapped reads with `--unmapped`, because omission is default. README describes a default 70% gap-compressed-identity filter, other identity filters disabled, supplementary/repeated-match handling and no secondary output by default. Record actual preset/filter/help settings; no identity-filter relaxation or new secondary policy is selected here. [Alignment and filters](https://github.com/PacificBiosciences/pbmm2/blob/v26.2.0/README.md#faq).
- pbsv: `discover` takes aligned BAM(s), transfers RG sample names into signatures; `call --ccs` takes reference plus signature file(s), emits a VCF with genotypes. Freeze exact RG/sample propagation, discover mode/MAPQ/size settings and call settings. Changelog says discover gained a HiFi preset in2.7.0 and MAPQ changed to5 in2.9.0; its exact preset flag/default and executable behavior remain **UNKNOWN** here. Do not invent a `discover --hifi` contract from that changelog. [Workflow/changelog](https://github.com/PacificBiosciences/pbsv/blob/v2.11.0/README.md).
- README reports CCS support settings `-A 3 -B 2 -O 3 -S 0 -P 10` and `--gt-min-reads 1`, but elsewhere describes strand evidence with `[1]` and the general `-P` with `[20]`. Actual support defaults, strand units/threshold and long-option spellings are **UNKNOWN pending pinned-binary help**. Do not copy these numbers into a purported exact recipe. Record emission thresholds separately from emitted FILTER flags; records rejected before emission are not recoverable by retaining FILTER rows. [Calling/filtering](https://github.com/PacificBiosciences/pbsv/blob/v2.11.0/README.md#calling-and-genotyping).
- Retain the whole native VCF, including `NearReferenceGap`, `NearContigEnd`, `Decoy`, `InsufficientStrandEvidence`, `NotFullySpanned` and PASS. README describes gap/end distances of1kb, an insertion maximum of15kb, and large deletions represented as translocations above100kb; confirm actual limits. The ≥50bp DEL/INS cohort is downstream selection, not permission to tune native limits after outcomes. DUP/BND/INV remain outside the frozen primary class, with their accounting retained. [Native limits](https://github.com/PacificBiosciences/pbsv/blob/v2.11.0/README.md#algorithm-overview-and-advanced-parameters).
- Tandem-repeat BED is strongly recommended for discover, not a formal required input. The linked `human_GRCh38_no_alt_analysis_set.trf.bed` is not certified for this exact primary FASTA by its name. Main must choose and hash a demonstrably compatible annotation or explicitly accept omission and its sensitivity limit. No BED/data fetch or annotation generation is authorized by this note. [Repeat annotation contract](https://github.com/PacificBiosciences/pbsv/blob/v2.11.0/README.md#2-discover-signatures-of-structural-variation).

This would be a declared modern reproduction from the selected study reads, not the published callset. Published pbsv version/filters/reference digest and direct VCF identity remain unpinned in the [unchanged provenance note](2026-10-10-hg002-published-calling-recipe.md). The paper's HiPhase1.2.1 is not the checked modern1.7.0 release.

## 3. Existing command contracts — not a launch script

All variables below require main's frozen absolute paths, new exclusive output leaf and accepted resource/settings packet. No command was executed. Native output overwrite behavior is not certified: enforce fresh filenames externally; preserve partials/failures instead of reusing a leaf. No repo caller wrapper currently implements these steps.

```sh
# REF/GTF: the exact expanded home products above; READS: accepted S1b gzip.
# BAM/SIG/VCF/COHORT/SORT_TMP: distinct paths in the new writable scratch leaf.
# First retain pinned-tool evidence, using the resolved executable paths:
pbmm2 --version
pbmm2 align --help
pbsv --version
pbsv discover --help
pbsv call --help

# Basic documented shape; actual thread/memory values require acceptance.
TMPDIR="$SORT_TMP" pbmm2 align "$REF" "$READS" "$BAM" \
  --preset CCS --sort --unmapped --sample HG002_WGS \
  --rg '@RG\tID:HG002_WGS\tSM:HG002_WGS' \
  -j "$ALIGN_THREADS" -J "$SORT_THREADS" -m "$SORT_MEMORY"
# Documented basic discover interface, NOT a frozen modern HiFi-mode recipe:
pbsv discover "$BAM" "$SIG"
# Add only accepted discover settings / compatible --tandem-repeats BED.
pbsv call --ccs -j "$CALL_THREADS" "$REF" "$SIG" "$VCF"

# Existing repo CLI; retain all native calls and all comprehensive transcripts:
python -B analysis/hg002_cds_overlap_cohort.py \
  --vcf "$VCF" --gtf "$GTF" --sample HG002_WGS --output "$COHORT"
```

Sorted pbmm2 output normally generates BAI; verify the actual index and whole-output completeness. Do not reuse the old BAM's BAI. Direct FASTA input avoids an unproven old `.mmi`; a new index, if selected, needs the same reference hash/preset. The official per-chromosome discover alternative must enumerate the **entire** new BAM dictionary, retain every shard and prove collection completeness; no CDS-only call crop. [pbmm2 interface](https://github.com/PacificBiosciences/pbmm2/blob/v26.2.0/README.md#usage), [pbsv sharding](https://github.com/PacificBiosciences/pbsv/blob/v2.11.0/README.md#parallel-processing-per-chromosome).

The [existing cohort code](../../analysis/hg002_cds_overlap_cohort.py) requires exact sample text, accepts plain/gzip VCF/GTF, refuses an existing output, and does not rename contigs. DEL uses half-open removed bases; INS uses its anchor boundary, including CDS edges. It retains all overlapping coding isoforms/genes and source GT/FILTER/INFO/phase. Valid reference GT excludes that ALT; missing/invalid GT stays unresolved. Non-PASS, symbolic/ambiguous alleles and unphased/blockless heterozygotes stay UNKNOWN. No reference FASTA input or REF-base validation exists in this CLI: caller/reference validation is a separate prerequisite.

Inspect `overlap_status`, source-ALT counters and `unknown_reasons`, **not only `candidate_state==CANDIDATE`**. An ordinary unphased0/1 overlap is still a retained potential cohort row. Homozygous-alt may pass this preliminary index without PS; `alt_copy_count` is a genotype allele count, not validated genomic copy number. `final_D=null` and `p1_state=NOT_ASSESSED` remain correct. Exact duplicate merging is not biological normalization or linked-event collapse. A zero index is interpretable only after full call/shard/sample/reference/annotation accounting and unresolved-geometry inspection; main applies the existing no-called-eligible-event stop. It is not proof that HG002 has no coding SVs.

## 4. Phase alternatives after the calling-only result

| Alternative, for main/reviewer | Exact prerequisites / limit |
|---|---|
| Stop before new phasing/assembly | Complete accepted calling output has no called eligible events, with unresolved records accounted under the existing gate. Empty PASS/CANDIDATE counts alone do not qualify. |
| Keep candidates; qualify local phase later | Complete same-source context remains available. New-reference read support must connect each SV allele, relevant coding sequence and local target/phase block; test switches, gaps, alternative placement and collapse/purging/copy ambiguity. No automatic phase or S3 release follows. Small-variant calls may be deferred if an accepted local proof suffices. |
| SV-only HiPhase, if separately accepted | Documented CLI accepts a VCF; the guide recommends both small and structural variants, rather than making a small-variant VCF mandatory. SV-only use is interface-permitted by that contract, **not demonstrated sufficient here**. Sparse/disconnected variants can leave unphased or singleton blocks; assigning0\|1 to a singleton does not link it to a coding allele/target. Keep global realignment for SV inputs unless main accepts a different recipe. |
| Joint small-variant + SV HiPhase | Newly called, same-reference small-variant VCF with exact model/caller/filter/build/hash and its own accepted CPU/RAM/disk account; no automatic GPU allowance. Indexed single-sample BAM(s), indexed VCF(s), matching sample in every VCF, same reference. Pair each input VCF with an output in order. |

Both HiPhase alternatives require indexed single-sample BAM(s), indexed VCF(s), exact matching RG SM/VCF sample and the same reference, plus actual pinned-runtime help/version evidence. These alternatives follow [HiPhase v1.7.0's input/output and singleton contracts](https://github.com/PacificBiosciences/HiPhase/blob/v1.7.0/docs/user_guide.md). A future single-VCF contract is `hiphase --bam BAM --vcf INDEXED_VCF --output-vcf NEW_VCF --reference REF --sample-name HG002_WGS --threads T`; joint mode repeats the VCF/output pair. Retain `--blocks-file`, `--summary-file`, `--stats-file` and, if needed, `--haplotag-file`. A read/block table can avoid a second full tagged BAM; `--output-bam` is optional and adds I/O/storage. None is run or selected here.

Original HP/PS are **not proof on the new reference**; no tag transplantation is certified. HiPhase explicitly ignores existing phase and removes/overwrites it in outputs. New PS is shared across joint VCFs, can point to a small-variant position, and scopes HP1/2 within a block; HP values need not agree across different blocks. Unphased/ambiguous mappings and calls remain unresolved. New tags alone do not prove local coding-chain linkage or target copy state. [Phase reuse and output semantics](https://github.com/PacificBiosciences/HiPhase/blob/v1.7.0/docs/user_guide.md#can-i-provide-pre-existing-phase-information-to-hiphase).

Without accepted new/local phase proof, do not claim alternate-haplotype assignment, linked-event grouping, two complete phased target sets, D/N, same-termini coding retention/loss, or attributable RNA rescue. Homozygous alternate still requires local sequence, copy state and placement. Calling can precede those proofs; final qualification cannot be replaced by unphased GT, old tags, a haplotype filename or sequence identity alone.

## 5. Resource/custody packet still to fill

S2's conditional ceilings remain **96 allocated CPU h, 64GiB RAM, 384GiB peak disk**, no second DNA library. Concurrent stages share **256GiB RAM / 512GiB total disk**, including retained home copies; do not add stage disk maxima. Existing S1 costs stay in S1; new alignment/calling/indexing/cohort work, failed attempts and any required small-variant/phasing work need concrete stage accounting, not a new free account.

pbmm2's explicit `-j A -J S` means A alignment threads **plus** S sorting threads, with BAM I/O overhead; do not interpret A as the whole allocation. Example documentation contract4+2+I/O is not a measured seven-CPU scaling result or booking. Freeze scheduler CPU/time, native thread values and sorting memory; avoid defaults that consume all visible CPUs. `-m` is per sorting thread, not total RAM. Put sort temporaries on writable scratch, not read-only compute home. [Thread/sort contract](https://github.com/PacificBiosciences/pbmm2/blob/v26.2.0/README.md#sorting).

Before booking, ledger all raw BAM/BAI copies, extracted gzip copies, S1 SQLite/journals, compressed/expanded reference copies, new index/BAM/BAI, signatures, whole VCFs, cohort rows, sort temporaries, software/bundles/logs, and later phase derivatives. Include overlap with other active tasks. Existing cohort code loads/indexes all CDS and retains rows in memory; the4.69GB GTF's RAM/runtime cost is **UNKNOWN**, not its file size. Do not crop isoforms to force a fit. HiPhase's guide recommends4GB/thread for typical30x human data; that is upstream guidance, not this source's measurement or permission to allocate64GB. [HiPhase resources](https://github.com/PacificBiosciences/HiPhase/blob/v1.7.0/docs/user_guide.md#recommended-resources).

Record allocated CPUs×elapsed for every job plus measured CPU, wall, MaxRSS, sampled/observed disk and their limitations. No throughput or feasibility is attested. Preserve failures/checkpoints at limits; revisions belong to main/reviewer. Compute home is read-only; preserve new results via writable login-side I/O, hash-check complete non-expiring home copies before scratch expiryOctober22. A future home-copy peak must fit alongside scratch, not after an assumed deletion. No deletion is proposed here.

Outstanding: final S1b audit/custody and counts; actual caller/aligner availability and hashes; exact discover HiFi interface; authoritative native thresholds/limits; repeat-annotation compatibility or accepted omission; new-reference dictionary/REF validation and VCF representation check against the existing index; complete resource ledger/thread/time packet; main/reviewer decision on calling-first and later phase proof. None is converted to release by this note.

## Bounded actual coverage

Local reads: stage decision, intake protocol/result, input recipe and published-provenance note; extraction/expansion/cohort notes; relevant HG002 and latest S1b/synthetic-interface reviewer sections; frozen-decision HG002/gate passages; full217-line cohort source and122-line tests, extraction state/CLI/publication sections, expansion source, retained small expansion manifest. Exact-name `rg` found no existing HG002 pbmm2/pbsv/HiPhase launch wrapper. No source BAM, FASTQ, genomic FASTA/GTF body or live cluster state was read.

Remote: Firecrawl skill and developer reference read fully. Three known official repository-page attempts (pbsv/pbmm2 succeeded; HiPhase504), one exact pbsv-interface developer query (only official README evidence used; two secondary hits not relied on). Fallback GitHub JSON/text only: HiPhase README and main user guide; three latest-release metadata endpoints; three tag-specific content endpoints (pbsv/pbmm2 README and HiPhase guide). Versioned pbsv/pbmm2 sections and HiPhase inputs, phase reuse, outputs/singletons/resources were checked; not an exhaustive source-code or executable audit. No assets, archives, BED/VCF/genomic bodies, paper refetch, install, native run, job, Git operation, RNA or implementation. Only this note was written; no tests were run for this documentation task.
