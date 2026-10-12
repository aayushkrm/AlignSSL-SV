# Weller2025 published construct-table inventory

Completed 2026-10-12; retained and rechecked 2026-10-13. This is a read-only
source inventory, not a natural-SV fitness benchmark or publication result.

| Complete published table check | Result |
|---|---:|
| Records / columns | 10,471 / 136 |
| Unique construct IDs | 10,471 |
| Numeric L2FC outcomes / missing outcomes | 10,466 / 5 |
| Author threshold L2FC < −1 / L2FC > 1 | 1,196 / 82 |
| Threshold/flag disagreement on known rows | 0 |
| Explicit positive-control/exonic subgroup | 450 records, 336 depleted |

The subgroup is **not** the paper's 1,003-row essential-coding denominator.
Literal `gene_name` has 150 distinct strings, including control labels; this
is not a claim of 150 independent target loci. Missing annotation flags for
110 records remain missing, not false. `main_gene_essentiality` occurs at
zero-based columns30/39; all duplicate cells agree across the complete table.
The parser verifies equality before using a named field. No source is edited.

The measured outcome is paired-guide abundance in cell populations. Header
fields for late BFP integration do not establish per-construct endogenous edit
fractions. No genotype truth, causal fitness, neutral label for missing records,
or biological false-negative rate is inferred. The paper's selected PCR/Sanger
and competition validations remain evidence for those tested conditions.

## Original source

[Preprint, posted 2025-11-04](https://www.biorxiv.org/content/10.1101/2025.11.03.686307v1.full)
and [Table S4](https://www.biorxiv.org/content/biorxiv/early/2025/11/04/2025.11.03.686307/DC3/embed/media-3.tsv?download=true).
The preprint DOI stem and some January metadata are not the posting date.
The supplement page was read with Firecrawl; its links worked after a normal
web page fetch failed. Firecrawl's targeted TSV query returned INVALID_ARGUMENT;
direct capped HTTP retrieval supplied the table instead. No CLI plugin install.

Original TSV retained outside Git:
`/Users/akm/aayushkrm-AlignSSL/runs/prime-deletion-source-check-20261012.6a96JV/media-3.tsv`.
Complete size13,221,638B / SHA256
`6b622cef1e49c3eed46a1d5d039f145744ca0c1469f32f163b8cb94bdf3e2f0a`.
The October13 whole-file SHA matches. Original data are not committed.
`inventory.json` SHA256
`795e6694618ef533d5bb75a6ac275d4af94b0aec43646a615e637785270963dc`.

Code SHA256
`aff052e33a3fc2afa4ceb5307a5bf7f166d8ec4bbf7266cf72de6a0927c5001f`.
The author repository was observed at commit
`e1a1a58711bf8237b0ed565d3155c8f70194fccc` (2025-11-02).
No author scripts were executed; the plots script's `data.csv` input is not
silently substituted for the actual supplementary TSV.

```sh
/Users/akm/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B -m unittest tests/test_prime_deletion_table_inventory.py
/Users/akm/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B analysis/prime_deletion_table_inventory.py /Users/akm/aayushkrm-AlignSSL/runs/prime-deletion-source-check-20261012.6a96JV/media-3.tsv
```

Six author controls passed in0.005s. An independent reviewer ran eight
additional in-memory parser checks and read only the real header, not all TSV
rows. Its completed scope is in
`docs/research/2026-10-12-deletion-screen-rigor-review.md`.
Initial probes stopped at a missing L2FC value and then a missing flag before
any result was emitted. `first-attempts.log` transcribes the errors. The final
inventory handles declared NA values explicitly and rejects other invalid data.
It writes `--output` exclusively; reruns above do not overwrite history.

October13 local regression selection:99tests+62subtests pass5.01s. The
spreadsheet skill guided read-only handling and source/missing-value separation.
No source workbook/TSV was modified or exported, model inference or training
ran, package was installed, or cluster job was launched for this inventory.
