# Fixed HG008 comparator case: close the generic detection premise

13 October 2026, Asia/Tomsk. **STOP this named case as evidence for a new
generic deletion-detection method.** A strong caller in the published panel
already reports its deletion geometry and genotype. This is a source/control
finding, not a new method, biological validation or publication result.

## Frozen question and actual records

The [SVPG paper, Fig.4d](https://www.nature.com/articles/s41592-026-03219-2#Fig4)
names a 419 bp HG008 deletion at chr7:19196736. Before reading new comparator
outcomes, the source check fixed that case and the endpoint window
chr7:19195736–19198155. Selection uses POS, INFO/END or breakend-mate endpoints;
it is not an interval-overlap query. A long spanning INV with both endpoints
outside the window is outside this selection, not a hidden deletion recovery.
No other case was substituted when a strong control resolved this premise.

| Archived source | Full / filtered VCF records | Fixed-case reported content |
|---|---:|---|
| Truth, SV_62 | 149 / 119 | PASS DEL419; POS19196736, END19197155 in full VCF; explicit REF420 bases and ALT A; GT0/1. Filtered record retains the explicit allele but lacks END. |
| Severus_v1.5 | 224 / 176 | PASS DEL419 at the same POS/END; GT0/1 in both files; HP1, VAF0.44, DR27/DV21. Symbolic REF N/ALT `<DEL>`, no deleted sequence. |
| SVPG, exact version unknown | 189 / 163 | Nearby INS130 at19196745 and DEL191 at19196966–19197157; both GT1/1 in both files. Neither declares the full419 bp deletion. |
| miniSV, exact version unknown | 186 / 168 | DEL195 at19196966–19197160, GT1/1 in both files; not the full419 bp deletion. |
| nanomonsv-0.7.2 | 1049 / 634 | No record selected by the fixed endpoint/mate rule in either file. This is not a genome-wide or current-native-caller absence claim. |

Raw selected records, header excerpts, complete VCF record counts and all11
member hashes are in [sources.json](sources.json). Positive SVLEN in Severus
is a caller convention: the comparison uses the declared deletion magnitude.
Matching endpoints/length/GT does not prove sequence identity, reference base
identity, independent phase, normal absence, purity, copy number or somatic
origin. Differing GT fields are not independently validated genotype errors.
No recall, precision, F1, prevalence or equal-information superiority is computed.
The paper's selected misses are not a random or held-out evaluation cohort.

## Source integrity and resource use

Source: [Zenodo record18456502](https://zenodo.org/records/18456502),
SV_callsets.zip2,879,666,672 bytes. The [directory-only receipt](../svpg_archive_index_20261013/index.json)
reads23,727 remote bytes and lists189 non-directory entries. It reads no member
bodies. The subsequent fixed11-member retrieval reads236,857 remote bytes,
checks each complete member's ZIP CRC and stores decoded bodies outside Git:
`/Users/akm/aayushkrm-AlignSSL/runs/svpg-named-case-20261013.wDDbXj/`.

During this check main rediscovered the existing October4 full archive cache.
The small remote reads duplicate cached source bytes; this is not a new2.88GB
transfer. The [October4 ledger](../data_audits/svpg_2026/2026-10-04/EXECUTION.md)
had inspected six HG002 headers only, with no biological rows or HG008 scoring.
The current fixed HG008 body comparison is new analysis, not a repeat experiment.
Future access uses the local cache instead of further range requests.

The separate [fresh cache receipt](cache_verification.json) records a complete
stable-file reread: author MD5a6ea80f613130c318d36632073c6de97 and whole SHA256
fff2f1d2978234a1357c6a16ce5ed9fabf17925955247ae2f9ee2ee8564eb7ca match.
All11 exact cached members match the range-retrieved size/SHA256/CRC32.
Other members' CRCs were not checked. The earlier immutable sources/index
reports still correctly say their own remote operations did not verify the
whole archive; the new local receipt does not rewrite those reports.

## Review and decision limits

The [maintained independent reviewer](../../docs/research/2026-10-13-comparator-case-review.md)
checked all11 decoded bodies independently and ACCEPTED the scoped comparison.
The [max-effort investment review](../../docs/research/2026-10-13-svpg-mode-investment-decision.md)
also accepts STOP for this generic presence-calling lead. Configurations were
requested Sol6.1/high and Sol6.1/max; backend/effort were not independently attested.

No matching guided-mode HG008 output was found in the inspected panel.
The [native-mode check](../../docs/research/2026-10-13-svpg-native-mode-check.md)
supports an original-BAM deletion fallback in code, not an observed rescue.
The archived SVPG version is unknown; paper/supplement version declarations
conflict. Filename `.filter` does not identify biological subtraction or
candidate stages. No BAM/GAF, graph, raw reads or model were acquired here;
no caller, training or cluster job was launched. Do not acquire them merely
to repeat this already reported detection control.

Exact-sequence recovery, current native guided behavior and somatic origin
remain unresolved. These unknowns do not create a novel contribution.
Complex INV is a separate conditional opportunity, not released by this DEL
finding. HG002 annotation remains stopped; the full research goal is unmet.

## Software checks and retained failures

The first offline contract suite had15passes/2failures. The
[failure transcription](first-control-attempt.txt) retains both: an unbudgeted
one-byte response-size probe and a single compressed-body read exceeding the
per-request cap for an otherwise permitted member. Main corrected the probe
budget and switched member acquisition to one-MiB ZipExtFile chunks through
EOF. Original source/index/cache reports remain unchanged; no data were fetched
again. This is software correction, not a change in scientific outcomes.

The corrected17contracttests plus prior regression selection pass:
**116tests +62subtests in5.00s**. Independently from test fixtures, main reread
the ten complete cached VCFs with the parser: all record counts, selected
headers and fixed-window raw records reproduce sources.json exactly.
These tests do not run native callers or validate biological truth.
The worker independently reran all17controls successfully and reported a
separate in-memory ZIP check: unrelated member body untouched, valid CRCs
pass, corrupted named member raises BadZipFile. That extra check is worker-
reported, not a saved native/source experiment. No file or network mutation.

```sh
/Users/akm/aayushkrm-AlignSSL/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_svpg_case_source_contracts.py tests/test_prime_deletion_table_inventory.py tests/test_sven_source_table_audit.py tests/test_readme_research_landing.py tests/test_hg002_reference_inventory.py tests/test_hg002_calling_interface_fixture.py tests/test_hg002_cds_overlap_cohort.py
```
