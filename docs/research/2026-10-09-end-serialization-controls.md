# Synthetic INFO/END serialization controls

## Scope

This sidecar uses a six-record VCF created under pytest's temporary
directory. It calls the unchanged `analysis/prepare_released_callers.py`
`_annotate` helper on that synthetic file. It then reads the written VCF text
directly and parses the file again with pysam. It does not call caller data,
truth data, the real preparation job, bcftools norm, SSH, or a network service.
It does not change the END guard or any production helper.

The test captures `_semantic_child` at the same point as `_annotate`: after
the helper adds its synthetic identity tags and before it writes the record.
For each record it compares that projection with the raw emitted INFO text,
the re-parsed `_row(record)` END tokens, the re-parsed `_semantic_child`, and
`record.stop`. Projection equality below ignores only `stop`, explicit END
tokens, and any END key in the INFO mapping, so it tests whether every other
projected field stayed equal.

## Local result

The test passed on Python 3.11.13, pysam 0.24.1, HTSlib 1.24, and pytest
9.1.1. The unchanged helper pins the cluster stack to pysam 0.24.0 and
HTSlib 1.23.1. This is a local-stack observation; it is not a cluster-stack
reproduction.

| Synthetic record | Source and pre-write END | Annotated file raw END | Re-parsed `_row` END | `stop` before → after | Other projection fields |
|---|---|---|---|---:|---|
| Literal INS, no END | absent | absent | absent | 10 → 10 | equal |
| Literal DEL, no END | absent | absent | absent | 21 → 21 | equal |
| Literal INS, redundant END | `END=30` | absent | absent | 30 → 30 | equal |
| Literal DEL, redundant END | `END=41` | absent | absent | 41 → 41 | equal |
| Symbolic DEL, redundant END | `END=50` | `END=50` | `END=50` | 50 → 50 | equal |
| Symbolic DEL, nonredundant END | `END=80` | `END=80` | `END=80` | 80 → 80 | equal |

The two literal records with explicit redundant END are witnesses. Before the
write, `_row(record)` serialized END and `_semantic_child` included that token
in its explicit-END field. The ordinary pysam write omitted END from the raw
output. On re-read, `_row(record)` and `_semantic_child` also had no END. The
parsed `stop` stayed at the reference-span end, and all other projected
fields stayed equal. In this local case, END-only projection changes can
therefore arise from ordinary serialization of literal variants.

The negative control edits only the emitted symbolic record's END from 80 to
81 in a temporary copy. Re-parsing changes `stop` from 80 to 81 and changes
the projected END token from `END=80` to `END=81`; all other projected fields
remain equal. The test detects a real END/stop change.

## Limit

This establishes a possible serialization mechanism under local pysam 0.24.1 /
HTSlib 1.24. It does not show that the same mechanism produced any row in the
separate real-data diagnosis, which used the cluster-pinned versions. In
particular, this toy cannot assign a cause to its reported 48,286 END-only
differences. The real-data result, its archived artifacts, and its review
remain owned by the main diagnosis.

## Run

```text
/Users/akm/aayushkrm-AlignSSL/.venv/bin/python -m pytest -q tests/test_caller_end_serialization_diagnostic.py
1 passed
```
