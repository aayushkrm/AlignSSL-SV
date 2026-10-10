# Projection serialization controls

## Scope

This note records a local synthetic VCF control. The test uses a one-record
VCF created under pytest's temporary directory. It does not read caller data,
truth data, or partial job output. It does not use SSH or network access.

The control covers `QUAL`, INFO and FORMAT Float values, multiallelic
`Number=A`, `Number=R`, and diploid `Number=G` projections, the original ID,
explicit `END`, and one deliberate INFO corruption.

## Local witness

The local environment was Python 3.11.13, pysam 0.24.1, HTSlib 1.24, and
pytest 9.1.1. The project virtualenv has pysam 0.24.1; the cluster stack is
pysam 0.24.0, so this is not an exact-stack reproduction.

For the synthetic high-precision record, `_row(record)` had the same text
before and after an ordinary pysam VCF write/read. `_semantic_child` still
changed because the first parsed record held Float values from the full input
decimals, while the writer serialized shorter decimal text and the next parse
created nearby Float values.

| Field | Input text | `_row` text | Parsed before | Parsed after |
| --- | --- | --- | ---: | ---: |
| QUAL | `123.123456789` | `123.123` | `123.12345886230469` | `123.12300109863281` |
| INFO/IA | `0.123456789` | `0.123457` | `0.12345679104328156` | `0.12345699965953827` |

The same precision change appears in INFO/IR and FORMAT/FA, FORMAT/FR, and
FORMAT/FG. Both ALT projections retain the expected A/R/G cardinalities.
The original ID `original_id`, `END=200`, stop coordinate, alleles, GT, and
phase remain the same. The negative control changes INFO/IA in the serialized
record and confirms that `_semantic_child` detects that corruption.

This is a concrete local serialization fragility witness. It does not establish
the cause of callerprep job 1604204's 51,561 matching identities with a field
multiset mismatch. The exact real-data cause remains undiagnosed. This test
does not run the cluster stack or the real normalization path.

## Run

```text
/Users/akm/aayushkrm-AlignSSL/.venv/bin/python -m pytest -q tests/test_caller_projection_serialization_diagnostic.py
2 passed
```
