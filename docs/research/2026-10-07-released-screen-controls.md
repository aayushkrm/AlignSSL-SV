# Released-callset screen: bounded metadata and control sidecar

Status: control note for the draft screen in
[`2026-10-04-released-callset-outcome-protocol.md`](2026-10-04-released-callset-outcome-protocol.md).
No screening result is approved by this note.

## Current preparation state

| Gate | State | Meaning |
|---|---|---|
| Frozen six-member header map | Pass | The six released `HG002_benchmark/*/hifi.vcf` members, sample labels, GT declarations, and contig dictionaries are recorded below. |
| Truvari/pysam control fixtures | Pass | Installed versions and synthetic-only normalization/filter behavior were checked on `scc`. |
| Header-only DeBreak/whole-archive feasibility check | Complete | Frozen declarations and inventory metadata only; no member body was read for this check. |
| Stage 02 cuteSV derivative | Complete; reverified | 51,561 records; Stage 03/04 reused and verified it. It still needs sorting because its contig-order check reports 23 violations. |
| Stage 03 DeBreak | Historical failure at 32 MiB | After streaming `INFO/RNAMES`, a retained line exceeded 33,554,432 bytes. Stage 04 later used the separately recorded 128 MiB cap. |
| Stage 04 final bounded preparation | **Stopped: incomplete** | cuteSV 51,561 (reused), DeBreak 26,421, Sawfish 43,944, Sniffles 32,567; SVIM stopped on an invalid-position validation error; SVPG was not opened. |
| Six-caller screen | Not run | No caller union, denominator, residual, or biological outcome exists. |

Stage 04 is the final custom-source-path attempt. Its failure JSON records
`failed_caller=svim`, `exception_message="Invalid VCF position"`, the 128 MiB
line cap, and no SVPG completion. The offending position value is not present
in that manifest. Do not infer that it was malformed: zero may be a legal
telomeric position in a caller’s convention, and the retained evidence does
not distinguish zero from a negative, nonnumeric, or otherwise unknown value.
The validator stopped; the value and context need separate review.

Stage 04 completed DeBreak at 26,421 records, with a maximum retained line of
60,480,492 bytes. It also completed Sawfish and Sniffles, and reused the
verified cuteSV derivative. Thus four caller files have complete preparation
records at this checkpoint: the reused cuteSV derivative plus DeBreak,
Sawfish, and Sniffles. It did not complete the frozen six-member roster.
Do not omit SVIM, treat SVPG as empty, or call a five-caller union the frozen
six-caller diagnostic. No four-thread execution was used.

Stop the custom source path here: no fifth pass, no further custom parser or
line-cap escalation, and no source-body read is authorized by this note. Any
standard-HTSlib handling proposal or new-source alternative is a separate
decision with its own review and frozen six-caller plan. It must not silently
drop a caller or reuse this failed preparation as a scored result. The two
128 MiB synthetic probes passed (child `ru_maxrss` 819,613,696 and 828,129,280
bytes; sampled peaks 713,273,344 and 826,945,536 bytes). Those synthetic
results do not grant source-read permission or validate biological input.
The source reports and partial staged outputs remain outside Git; this note
read JSON metadata only, not staged VCF bodies. The control fixtures used
temporary directories on `scc` and were removed at exit.

The reported full-suite checkpoint is 617 passed and 29 skipped. This is a
software-test result only; it does not resolve the SVIM stop or score a
callset.

## Frozen archive evidence

The two metadata files read for this note are:

| File | SHA-256 |
|---|---|
| `results/data_audits/svpg_2026/2026-10-04/header_protocol.json` | `f76981810ea38dcb13074f040beb47cfd871125e746e0db4bf7b6b3c352dc07c` |
| `results/data_audits/svpg_2026/2026-10-04/full_hifi_headers.json` | `4deadb0fe4435b92ec75c6f9977d14655b3db6a5fbd9005ec88485fbacd7fc34` |

The inventory pins `svpg-18456502-SV_callsets.zip` at SHA-256
`fff2f1d2978234a1357c6a16ce5ed9fabf17925955247ae2f9ee2ee8564eb7ca` and
2,879,666,672 bytes. The recorded whole-archive MD5 matches the official value
`a6ea80f613130c318d36632073c6de97`. The frozen selection rule chose the six
root `hifi.vcf` members under `SV_callsets/HG002_benchmark/`, from central
directory metadata before reading headers or records
(`header_protocol.json` fields `/selection_rule` and `/members`).

The 2026-10-04 header inventory says the archive payload had been downloaded,
but at that inventory checkpoint no member was extracted, zero biological
records were parsed, and no truth or performance output was scored
(`full_hifi_headers.json` fields
`/whole_archive_payload_downloaded`, `/member_extraction_performed`,
`/biological_records_parsed`, `/truth_or_performance_outputs_scored`). This
note read frozen JSON and preparation-report metadata only; it did not read a
VCF body. The earlier header inventory says per-member CRC validation was not
performed. ZIP CRC32 values below are central-directory metadata, not verified
per-member hashes. The archive pin does not replace a streamed member
SHA-256 in a preparation pass.

## Exact released sample columns and header evidence

Each `header_lines` array index below is zero-based. Every GT pointer resolves
to the exact declaration
`##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">`.
Every sample pointer resolves to the exact `#CHROM` line shown in the table.

| Caller | Exact ZIP member | Sample column label | GT declaration pointer | `#CHROM` pointer | Contig declaration indices |
|---|---|---|---|---|---|
| cuteSV | `SV_callsets/HG002_benchmark/cutesv/hifi.vcf` | `NULL` | `/vcf_headers/0/header_lines/107` | `/vcf_headers/0/header_lines/113` | `3–88` |
| DeBreak | `SV_callsets/HG002_benchmark/debreak/hifi.vcf` | `/data1/huheng/HG002/hifi.bam` | `/vcf_headers/1/header_lines/108` | `/vcf_headers/1/header_lines/110` | `4–89` |
| Sawfish | `SV_callsets/HG002_benchmark/sawfish/hifi.vcf` | `HG002` | `/vcf_headers/2/header_lines/115` | `/vcf_headers/2/header_lines/122` | `5–90` |
| Sniffles | `SV_callsets/HG002_benchmark/sniffles/hifi.vcf` | `SAMPLE` | `/vcf_headers/3/header_lines/95` | `/vcf_headers/3/header_lines/133` | `4–89` |
| SVIM | `SV_callsets/HG002_benchmark/svim/hifi.vcf` | `Sample` | `/vcf_headers/4/header_lines/12` | `/vcf_headers/4/header_lines/111` | `25–110` |
| SVPG | `SV_callsets/HG002_benchmark/svpg/hifi.vcf` | `Sample` | `/vcf_headers/5/header_lines/97` | `/vcf_headers/5/header_lines/100` | `2–87` |

The six `body_records_parsed` values are zero. Their member records in the
central-directory array are `/members/15`, `/members/39`, `/members/58`,
`/members/75`, `/members/99`, and `/members/123`, respectively. Their declared
compressed and uncompressed byte counts are:

| Caller | Compressed bytes | Uncompressed bytes | Declared CRC32 |
|---|---:|---:|---|
| cuteSV | 6,118,453 | 30,029,207 | `aa90b5d1` |
| DeBreak | 204,459,727 | 935,962,599 | `de4ce2da` |
| Sawfish | 5,155,442 | 25,716,015 | `f900b7a6` |
| Sniffles | 2,767,454 | 15,004,300 | `c390dcc2` |
| SVIM | 1,377,734 | 6,682,295 | `3c58306d` |
| SVPG | 4,769,710 | 23,624,851 | `3c2eddd3` |

### Shared declared contig dictionary

All six headers contain the same 86 `##contig` declarations, byte for byte and
in the same order. The ranges are listed in the table above. The SHA-256 of
the joined declaration lines, each followed by LF, is
`0802c5536384ef21da5117529cc225e9283d0946e75d5753d3c97421f6195f5e`.

```text
ID                  length
1                   249250621
2                   243199373
3                   198022430
4                   191154276
5                   180915260
6                   171115067
7                   159138663
8                   146364022
9                   141213431
10                  135534747
11                  135006516
12                  133851895
13                  115169878
14                  107349540
15                  102531392
16                  90354753
17                  81195210
18                  78077248
19                  59128983
20                  63025520
21                  48129895
22                  51304566
X                   155270560
Y                   59373566
MT                  16569
GL000207.1          4262
GL000226.1          15008
GL000229.1          19913
GL000231.1          27386
GL000210.1          27682
GL000239.1          33824
GL000235.1          34474
GL000201.1          36148
GL000247.1          36422
GL000245.1          36651
GL000197.1          37175
GL000203.1          37498
GL000246.1          38154
GL000249.1          38502
GL000196.1          38914
GL000248.1          39786
GL000244.1          39929
GL000238.1          39939
GL000202.1          40103
GL000234.1          40531
GL000232.1          40652
GL000206.1          41001
GL000240.1          41933
GL000236.1          41934
GL000241.1          42152
GL000243.1          43341
GL000242.1          43523
GL000230.1          43691
GL000237.1          45867
GL000233.1          45941
GL000204.1          81310
GL000198.1          90085
GL000208.1          92689
GL000191.1          106433
GL000227.1          128374
GL000228.1          129120
GL000214.1          137718
GL000221.1          155397
GL000209.1          159169
GL000218.1          161147
GL000220.1          161802
GL000213.1          164239
GL000211.1          166566
GL000199.1          169874
GL000217.1          172149
GL000216.1          172294
GL000215.1          172545
GL000205.1          174588
GL000219.1          179198
GL000224.1          179693
GL000223.1          180455
GL000195.1          182896
GL000212.1          186858
GL000222.1          186861
GL000200.1          187035
GL000193.1          189789
GL000194.1          191469
GL000225.1          211173
GL000192.1          547496
NC_007605           171823
hs37d5              35477943
```

This is a matching *declared dictionary*. It does not establish that the six
callers used the same reference sequence bytes, or that the declared
`hs37d5` sequence is byte-identical to the pinned FASTA.

## What the headers do and do not say about inputs

The release path and filename call these six files HG002 benchmark HiFi
outputs. That is release organization and a generic platform label. It does
not establish that all six used the same BAM bytes, donor aliquot, read set,
run, or depth.

Three headers contain command-like metadata and name the same BAM path.
cuteSV declares
`/data1/huheng/HG002/hifi.bam` and a reference path ending in
`/data/huheng/dataset/human/HG002_PacBio_CCS_15kb/ref/hs37d5.fa`
(`/vcf_headers/0/header_lines/112`). DeBreak declares the same BAM and
reference path strings (`/vcf_headers/1/header_lines/109`). Sniffles uses the
lowercase key `##command` at `/vcf_headers/3/header_lines/2`; its value names
`/data1/huheng/HG002/hifi.bam` as `--input`. The Sawfish, SVIM, and SVPG
captured headers have no command-like field or BAM path. A matching path
string is not a BAM or FASTA checksum. No
common input checksum, read-group/run identifier, read manifest, or comparable
depth is recorded in this inventory. Common input and run identity are
**unverified**; this does not show that the callers used different inputs.

Header `fileDate` values are not run IDs. The `##source` declarations identify
cuteSV 2.1.1, DeBreak without a version, Sawfish 2.0.3, Sniffles2 2.3.3, and
SVIM 1.4.1. The SVPG header has no `##source` declaration. Those fields do
not establish pipeline stage, record completeness, or filtering provenance.
The sample labels above map released columns only; they do not verify donor
identity.

## Installed tool identity and behavior

All checks in this section ran through:

```text
ssh scc /home/igorno/miniconda3/envs/truvari_env/bin/python
```

| Component | Installed identity |
|---|---|
| Truvari | 5.4.0; 40-file Python source-tree SHA-256 `8d5f13e4505e3be978c66cb2a443974071d4a4404114bb67456089ed1e555a3e` |
| `truvari/bench.py` | SHA-256 `be242bfae4f3ed51a8cc1f2b6699429b57d2db4686c499b6d45b776a39cdea1d` |
| `truvari/variant_record.py` | SHA-256 `f2ea168e76be5ee694b9e9cf4baa4dd62849934e2e7c0af21a8758be2145f32a` |
| pysam | 0.24.0 |
| `pysam/bcftools.py` | SHA-256 `6385d8616825043dce50920f799ffd7628175ab4db49c185fef3a3b973ff3cd1` |
| pysam `libchtslib` extension | SHA-256 `3fbc73c9002a6854c04300b91d95dc940c58e5d3e649f332465471da38596e6a` |
| bcftools bundled by pysam | Synthetic output reports `1.23.1 (pysam)+htslib-1.23.1` |

### Truvari FILTER and genotype controls

Truvari 5.4.0 bench help says `--passonly` means “Only consider calls with
FILTER == PASS.” The installed source takes a broader path: `filter_call()`
calls `is_filtered()`, and `is_filtered()` returns false for an empty FILTER
set (`.`) as well as for `PASS` (`variant_record.py:418–441, 539–540`). A
synthetic VCF confirmed that `PASS` and `.` are retained, while `LowQual` is
filtered. Therefore the draft’s secondary `--passonly` arm is **not** strict
`FILTER == PASS` on this installation; report `.` separately.

The help for `--no-ref a` names `0/0` and `./.`. On biallelic records, the
source tests whether GT contains allele `1` (`variant_record.py:455–477,
543–546`). The synthetic fixture confirmed that `./1` remains present, while
`./.` and `0/0` do not. So `--no-ref a` is not a complete-missing-GT filter.
Keep partial and missing GT counts explicit in both arms. Do not infer a
reference allele from a missing allele.

### bcftools multiallelic behavior

Installed `pysam.bcftools.norm` help states:

```text
-m, --multiallelics -|+TYPE   Split multiallelics (-) or join biallelics (+)
--multi-overlaps 0|.           Fill in the reference (0) or missing (.) allele
                               when splitting multiallelics [0]
```

A temporary synthetic VCF had three rows, each `REF=A, ALT=C,G`: source
ordinal 1 had GT `1/2`, ordinal 2 had `0/0`, and ordinal 3 had `./1`. It also
had duplicate VCF IDs (`dupID`) and a missing ID (`.`). Under
`-m -any --multi-overlaps .`, the output was:

| Source ordinal / source GT | ALT index 1 (`C`) child GT | ALT index 2 (`G`) child GT |
|---|---|---|
| 1 / `1/2` | `1/.` | `./1` |
| 2 / `0/0` | `0/0` | `0/0` |
| 3 / `./1` | `./1` | `./.` |

Under `--multi-overlaps 0`, the same rows became:

| Source ordinal / source GT | ALT index 1 (`C`) child GT | ALT index 2 (`G`) child GT |
|---|---|---|
| 1 / `1/2` | `1/0` | `0/1` |
| 2 / `0/0` | `0/0` | `0/0` |
| 3 / `./1` | `./1` | `./0` |

The fixture carried `SRCORD` as `Number=1` and `ALTIDX` as `Number=A` INFO
fields. Both survived splitting, with ALT indices 1 and 2 on their respective
children. The original VCF ID was duplicated on the two `dupID` children, and
the missing ID stayed missing. VCF ID alone is therefore not a unique parent
key. Each mode produced six children from three source records. The source
record denominator must remain three; do not count split children as new
source records.

The dot mode does not impute the competing ALT as reference. It can create
missing alleles in child GTs even when the source GT was fully called (`1/2`).
Keep source-GT missingness and projection-created missingness as separate
fields. Never rewrite `.` to `0` after decomposition.

### Sorting behavior checked on synthetic contigs

`pysam.bcftools.sort` was run on a tiny unsorted fixture whose declared contig
order was `2, 10, 1, GL000207.1`. Its output used that same header order and
sorted positions within each contig. The six released headers share one exact
86-contig order, so use that frozen declaration order as the contig rank. Do
not use lexical chromosome sorting or add/remove a `chr` prefix.

A second synthetic fixture included two source records at the same POS, with
the earlier source ordinal multiallelic. After `norm -m -any` and `sort`, this
installed build emitted `(POS, source ordinal, ALT index, ID)` as
`(10,1,1,row1), (20,2,1,row2), (20,2,2,row2), (20,3,1,row3)`. The exact
synthetic assertion is included below. This proves the observed order for
that fixture, not a general tie-order guarantee from `bcftools sort`.

For a deterministic child view, define the full key as:

```text
(contig_rank, POS, source_record_ordinal, original_ALT_index)
```

Split with `bcftools norm`, then sort each caller with `bcftools sort` using
the frozen header order. Validate the full key
`(contig_rank, POS, source_record_ordinal, original_ALT_index)` after sorting;
`bcftools sort` is not configured with the last two fields as sort keys. Keep
the ordinal/ALT tie order only when the assertion passes. The equal-POS
stability gate remains **open**: one fixture does not prove tie behavior for
other input orders, ties, or external-sort spill. Do not claim that bcftools
guarantees source-ordinal tie ordering. Preserve duplicate rows. Fail if a
record names a contig outside the frozen map or if the input
header dictionary differs. Do not add a custom sort/parser if the full-key
assertion fails; that requires a separate standard-HTSlib or alternative-source
decision. Before any later use, also recheck the pinned reference bytes. A
matching VCF dictionary does not validate reference sequence identity.

## Reusable identity and decomposition contract

These controls describe how to preserve identities if a separate reviewed
analysis is selected. They do not authorize another read or a new custom
source pass. Keep any immutable source view separate from derived children.

| Field/artifact | Contract |
|---|---|
| Source member key | Archive SHA-256 + exact ZIP member path + SHA-256 of the uncompressed original member bytes, computed during the approved stream. The last value is not in the header inventory yet. |
| Source record identity | One-based ordinal among **all** original non-header VCF rows, assigned before filters or decomposition. |
| Source ID | Preserve the exact original VCF ID, including repeated values and `.`. It is descriptive, not unique. |
| Child identity | Source member key + source record ordinal + 1-based original ALT index. Do not join by position, allele string, or VCF ID alone. |
| Original GT | Preserve the exact source GT and phase. Count source missing alleles before projection. |
| Child GT | Preserve bcftools output. Record missing alleles introduced by `--multi-overlaps .` separately from missing source alleles. |
| Staged source VCF | Outside Git; all fields and records unchanged except removal of INFO/RNAMES and allowed ordering. Any unsupported field or over-limit row stops that member. |
| Decomposed/sorted VCF | Separate per-caller artifact outside Git. Use `-m -any --multi-overlaps . -N --no-version`; this view does not replace the source VCF. |
| Identity map | Outside Git: member key, ordinal, original ID, original ALT index, original GT, child GT, and transformation status. Do not store long allele strings or read names in Git. |
| Control manifest | Small JSON: archive/header JSON hashes, selected member paths, sample/GT/contig map, tool/source hashes, gate states, counts, and output hashes. Keep under the 4 MiB metadata limit. |
| Logs and summaries | Keep full logs and raw callset artifacts outside Git. Git may contain small counts, hashes, selected identities, and this protocol note. |

Use temporary `CTRL_SRCORD` (`Number=1`) and `CTRL_ALTIDX` (`Number=A`)
fields only in a derived working copy if the chosen HTSlib transformation
needs in-VCF linkage.
Reject a source header that already declares either name; do not overwrite
caller metadata. Remove temporary tags from any final comparison view only
after the external identity map is complete and checked. The synthetic fixture
verified that a `Number=A` index field is split with its matching ALT.

The primary source view and the derived child view have different counting
units. Report original source rows once. Keep child counts as transformation
metadata. For a source record with several ALTs, any later allele-level
compatibility must map back to the parent identity and must not inflate the
source-record denominator.

## Final checkpoint and next decision

The next executable gate is a metadata-only assertion over the Stage 04
failure manifest. It confirms the recorded stop and caller roster. It reads no
VCF body and does not authorize a new pass:

```sh
jq -e '
  .status == "incomplete" and
  .failed_caller == "svim" and
  .exception_message == "Invalid VCF position" and
  .max_line_bytes == 134217728 and
  .completed_callers.cutesv.records == 51561 and
  .completed_callers.debreak.records == 26421 and
  .completed_callers.debreak.streaming_buffers.max_retained_line_bytes == 60480492 and
  .completed_callers.sawfish.records == 43944 and
  .completed_callers.sniffles.records == 32567 and
  ((.completed_callers | has("svim")) | not) and
  ((.completed_callers | has("svpg")) | not)
' /Users/akm/aayushkrm-AlignSSL/data/derived/svpg_2026/2026-10-07-stage-04/failure.json
```

After this checkpoint, stop. Do not run a fifth pass, omit SVIM, or describe
SVPG as empty. A standard-HTSlib treatment of the unknown SVIM position or a
new source is a separate decision. It must state how it preserves the frozen
six-caller diagnostic, source IDs/ordinals/ALT indices, and missing GTs. No
future source-read approval is asserted here. Do not add another custom parser
or increase the cap.

The installed-tool synthetic gate is executable as written. It creates only synthetic VCFs
under a temporary directory, uses one Python process, and prints one JSON
status line. It submits no job and takes no caller path:

```sh
ssh scc /home/igorno/miniconda3/envs/truvari_env/bin/python - <<'PY'
import importlib.metadata as md
import json
import pathlib
import tempfile
import textwrap
import pysam
import pysam.bcftools as bcftools
import truvari

assert md.version("truvari") == "5.4.0"
assert pysam.__version__ == "0.24.0"
with tempfile.TemporaryDirectory(prefix="released-screen-control-") as td:
    root = pathlib.Path(td)
    source = root / "synthetic.vcf"
    source.write_text(textwrap.dedent("""\
    ##fileformat=VCFv4.2
    ##contig=<ID=chrSynthetic,length=10000>
    ##INFO=<ID=SRCORD,Number=1,Type=Integer,Description="Synthetic ordinal">
    ##INFO=<ID=ALTIDX,Number=A,Type=Integer,Description="Synthetic ALT index">
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH
    chrSynthetic\t10\tdupID\tA\tC,G\t.\tPASS\tSRCORD=1;ALTIDX=1,2\tGT\t1/2
    chrSynthetic\t20\tdupID\tA\tC,G\t.\tPASS\tSRCORD=2;ALTIDX=1,2\tGT\t0/0
    chrSynthetic\t30\t.\tA\tC,G\t.\tPASS\tSRCORD=3;ALTIDX=1,2\tGT\t./1
    """))
    expected = {
        ".": [(1,1,(1,None)),(1,2,(None,1)),(2,1,(0,0)),
              (2,2,(0,0)),(3,1,(None,1)),(3,2,(None,None))],
        "0": [(1,1,(1,0)),(1,2,(0,1)),(2,1,(0,0)),
              (2,2,(0,0)),(3,1,(None,1)),(3,2,(None,0))],
    }
    counts = {}
    for overlap in (".", "0"):
        output = root / ("dot.vcf" if overlap == "." else "zero.vcf")
        bcftools.norm("-m", "-any", "--multi-overlaps", overlap,
                      "--no-version", "-N", "-Ov", "-o", str(output),
                      str(source), catch_stdout=False)
        with pysam.VariantFile(str(output)) as vcf:
            rows = [(r.info["SRCORD"], r.info["ALTIDX"][0],
                     r.samples[0]["GT"]) for r in vcf]
        assert rows == expected[overlap], (overlap, rows)
        counts[overlap] = len(rows)

    filters = root / "filters.vcf"
    filters.write_text(textwrap.dedent("""\
    ##fileformat=VCFv4.2
    ##contig=<ID=chrSynthetic,length=10000>
    ##FILTER=<ID=LowQual,Description="synthetic">
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH
    chrSynthetic\t10\tpass\tA\tC\t.\tPASS\t.\tGT\t0/1
    chrSynthetic\t20\tdot\tA\tC\t.\t.\t.\tGT\t0/1
    chrSynthetic\t30\tfiltered\tA\tC\t.\tLowQual\t.\tGT\t0/1
    chrSynthetic\t40\tpartial\tA\tC\t.\tPASS\t.\tGT\t./1
    chrSynthetic\t50\tmissing\tA\tC\t.\tPASS\t.\tGT\t./.
    chrSynthetic\t60\tref\tA\tC\t.\tPASS\t.\tGT\t0/0
    """))
    observed = {
        r.id: {"filtered": r.is_filtered(), "present": r.is_present()}
        for r in truvari.VariantFile(str(filters))
    }
    expected_filters = {
        "pass": {"filtered": False, "present": True},
        "dot": {"filtered": False, "present": True},
        "filtered": {"filtered": True, "present": True},
        "partial": {"filtered": False, "present": True},
        "missing": {"filtered": False, "present": False},
        "ref": {"filtered": False, "present": False},
    }
    assert observed == expected_filters, observed

print(json.dumps({
    "biological_input": "none",
    "gate": "PASS",
    "norm_children_per_mode": counts,
    "pysam": pysam.__version__,
    "truvari": md.version("truvari"),
    "truvari_filter_gt_cases": len(observed),
}, sort_keys=True))
PY
```

The observed result was:

```json
{"biological_input": "none", "gate": "PASS", "norm_children_per_mode": {".": 6, "0": 6}, "pysam": "0.24.0", "truvari": "5.4.0", "truvari_filter_gt_cases": 6}
```

Equal-POS tie assertion, also run through the same installed environment:

```sh
ssh scc /home/igorno/miniconda3/envs/truvari_env/bin/python - <<'PY'
import pathlib, tempfile, textwrap
import pysam
import pysam.bcftools as bcftools

with tempfile.TemporaryDirectory(prefix="released-screen-tie-") as td:
    root = pathlib.Path(td)
    src, split, out = root / "tie.vcf", root / "tie.split.vcf", root / "tie.sorted.vcf"
    tmp = root / "sort-tmp"
    tmp.mkdir()
    src.write_text(textwrap.dedent("""\
    ##fileformat=VCFv4.2
    ##contig=<ID=chrSynthetic,length=10000>
    ##INFO=<ID=SRCORD,Number=1,Type=Integer,Description="Synthetic source ordinal">
    ##INFO=<ID=ALTIDX,Number=A,Type=Integer,Description="Synthetic original ALT index">
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH
    chrSynthetic\t10\trow1\tA\tC\t.\tPASS\tSRCORD=1;ALTIDX=1\tGT\t0/1
    chrSynthetic\t20\trow2\tA\tC,G\t.\tPASS\tSRCORD=2;ALTIDX=1,2\tGT\t1/2
    chrSynthetic\t20\trow3\tA\tT\t.\tPASS\tSRCORD=3;ALTIDX=1\tGT\t0/1
    """))
    bcftools.norm("-m", "-any", "--multi-overlaps", ".", "--no-version",
                  "-N", "-Ov", "-o", str(split), str(src), catch_stdout=False)
    bcftools.sort("-m", "512M", "-T", str(tmp), "-Ov", "-o", str(out),
                  str(split), catch_stdout=False)
    with pysam.VariantFile(str(out)) as vcf:
        observed = [(r.pos, r.info["SRCORD"], r.info["ALTIDX"][0], r.id) for r in vcf]
    expected = [(10,1,1,"row1"),(20,2,1,"row2"),(20,2,2,"row2"),(20,3,1,"row3")]
    assert observed == expected, observed
    print({"gate":"PASS", "rows":observed, "biological_input":"none",
           "pysam":pysam.__version__})
PY
```

Observed: `PASS`; rows were `(10,1,1,row1), (20,2,1,row2),
(20,2,2,row2), (20,3,1,row3)`. This is a fixture assertion, not a universal
`bcftools sort` tie-order guarantee.

For reference only, the exact pysam calls exercised for a synthetic derived
view were:

```python
bcftools.norm(
    "-m", "-any", "--multi-overlaps", ".", "--no-version", "-N",
    "-Oz", "-o", split_vcf, staged_source_vcf,
    catch_stdout=False,
)
bcftools.sort(
    "-m", "512M", "-T", temp_dir, "-Oz", "-o", sorted_vcf, split_vcf,
    catch_stdout=False,
)
```

`catch_stdout=False` is required when the pysam wrapper writes to the explicit
`-o` path. `--no-version` avoids run-time command/date text in the output
header. `-N` prevents reference-dependent indel normalization in this
decomposition-only view. These calls are not authorization or an instruction
to process any released member. Stage 04 used its historical 128 MiB line cap,
4 GiB cumulative source ceiling, 12 GiB global engineering ceiling, single
process, 1,800 CPU-second limit, and sampled 3 GiB RSS stop. It stopped at
SVIM; do not rerun it or extend it with a fifth pass.

### Checkpoint artifact map

These are existing metadata/results outside or inside Git. This note created
none of them. Do not read or transform the staged VCFs as part of this
checkpoint.

| Artifact | Location | Status/evidence |
|---|---|---|
| Stage 04 protocol and reservation | `results/data_audits/svpg_2026/2026-10-07/stage_04_protocol.json`; `.../traffic_reservation_04.json` | Protocol SHA-256 `4858cd824ea81a9be998a62043d3c2eb1736d724ea34b09ceb86e5973aab95ac`; historical run cap and traffic accounting. |
| Stage 04 stop manifest | `/Users/akm/aayushkrm-AlignSSL/data/derived/svpg_2026/2026-10-07-stage-04/failure.json` | Final recorded status, completed-caller counts, DeBreak max line, SVIM failure, and no SVPG completion. |
| Stage 04 runtime report | `/Users/akm/aayushkrm-AlignSSL/data/derived/svpg_2026/2026-10-07-stage-04-runtime/resources.json` | Return code 2; sampled single-process resource report; not an outcome score. |
| Existing staged outputs | `/Users/akm/aayushkrm-AlignSSL/data/derived/svpg_2026/2026-10-07-stage-04/` | DeBreak, Sawfish, Sniffles completed; SVIM partial at stop. cuteSV is the verified Stage 02 derivative. SVPG has no staged output because it was not opened. Preserve; do not extend this custom-source path. |
| Synthetic probe reports | `/Users/akm/aayushkrm-AlignSSL/data/derived/svpg_2026/2026-10-07-stage-04-synthetic-runtime/resources.json` and `.../2026-10-07-stage-04-synthetic-02-runtime/resources.json` | Both 128 MiB synthetic probes completed; resource figures are reported above. They are not biological evidence or permission. |

The manifest checkpoint command above is the only proposed next executable
gate. A later standard-HTSlib treatment or alternative source needs a separate
decision and protocol; this note does not propose a command to read more
source data.
