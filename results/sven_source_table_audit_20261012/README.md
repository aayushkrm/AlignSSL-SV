# SVEN published-figure source check

2026-10-12 local; completed at 2026-10-11 21:46 UTC. This is a source-table
reproduction, not a model experiment or publication result.

| Complete source range | Numeric pairs, no dropped rows | Spearman correlation |
|---|---:|---:|
| `Figure 3a!A2:B94367` | 94,366 | 0.9208479244746964 |
| `Figure S4!A2:B94367` | 94,366 | 0.8410704403295711 |

The first rounds to the paper's 0.921. The paper describes the second figure
as its Enformer comparison. Both are absolute log10-expression measurements.
Neither sheet includes gene/sample identifiers or paired reference predictions.
The proposed reference-only or gene-balanced contrast cannot be computed from
these sheets. No causal SV-effect accuracy, independence of rows, biological
null, model failure, or novelty conclusion follows. Other repository or study
files could supply a crosswalk; their absence is not established.

`audit.json` records original source hashes, member inventory, declared workbook
dimensions and complete selected-sheet checks. Dimensions of other sheets are
metadata, not full value checks. No source cell, formula, or workbook was changed,
recalculated, or exported. No rows were excluded or selected by favorable outcomes.

## Original source and reproducibility

Primary article: https://www.nature.com/articles/s41467-024-55392-7.
DOI-based Europe PMC lookup resolves PMID39738063 / PMC11685779.
The earlier attempted PMID39738006 resolved an unrelated antibody paper and was
excluded; it supplied no SVEN evidence. The publisher ZIP web fetch failed with
cache miss; a 30-second HEAD timed out with zero bytes. The public archive
alternative succeeded; no paid account or permission change.

Original download, retained outside Git:
`/Users/akm/aayushkrm-AlignSSL/runs/sven-source-table-check-20261012.xWvtZS/PMC11685779_SupplementaryFiles.zip`.
URL: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11685779/supplementaryFiles.
Outer archive 14,139,308 B / SHA256
`4dea345e3bb3f6c16cc893d52e6f295b3cfdde993c712d1d56e8ef76a8d2e902`.
Wrapper metadata can differ on a new archive download. Embedded original
`41467_2024_55392_MOESM10_ESM.zip` is 10,105,269 B, MD5
`94d0a1d10a542bcef0071baa050ebfad`, matching the article XML. Its SHA256 is
`8ed8b5ff791d3ba5b0ecdb4d06b8690d65a75359c559677794aba7e82f62aeac`.
Workbook member SHA256
`102d510aed55318b206d1dde5359084fa89b1e70e636e9da682f6783ad44ec42`.
No source ZIP, workbook, bigWig, model or genomic read is committed.

Run from repo with bundled Python/openpyxl3.1.5:

```sh
/Users/akm/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B -m unittest tests/test_sven_source_table_audit.py
/Users/akm/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B analysis/sven_source_table_audit.py /Users/akm/aayushkrm-AlignSSL/runs/sven-source-table-check-20261012.xWvtZS/PMC11685779_SupplementaryFiles.zip
```

Initial six synthetic tests passed in0.002s. Expanded eight pass in0.003s;
they cover average tie ranks, perfect and
reversed order, a hand-computable tied value, zero correlation, invalid lengths
and constant vectors, member caps, missing/duplicate members, exact header and
row count, and rejection of missing, boolean, nonfinite and formula cells.
First implementation
attempt failed importing unavailable SciPy before any table analysis or output
write; retained `first-attempt.log` transcribes that tool output. No install was
needed: final code computes Pearson correlation of average ranks with standard
library arithmetic. Script refuses an existing `--output` path; reruns above
print only and do not overwrite historical results.

The spreadsheet skill guided read-only source handling and missing-value
treatment. No authoring or rendering claim. Local small-table work used one
serial process; no cluster allocation or model inference. Own cluster queue
was empty at the 2026-10-11 21:45 UTC check. The HG002 scientific stop stands.
Later maintained independent review accepts the scoped reported reproduction.
It read code/tests/audit.json, rehashed the latter and reran synthetic controls;
it did not independently reread the original workbook or recompute correlations.
See `docs/research/2026-10-12-opportunity-screen-independent-review.md` in repo.
No causal claim or campaign is approved.

Final software check:93tests+53subtests pass in5.17s across the source-audit,
README, reference-inventory, caller-interface and CDS-cohort selection. The
first repo-relative `.venv/bin/python` runner lookup failed before collection;
the correct absolute project venv ran the selection. The workbook reader is
imported only by `audit`, so pure rank/schema controls do not require openpyxl.
This small import-placement change and two extra control tests do not alter
the completed figure results or overwrite audit.json. Independent review's
earlier six-test checkpoint stays intact; its raw-workbook verification limit
still applies. No biological or native-run claim follows from software checks.
