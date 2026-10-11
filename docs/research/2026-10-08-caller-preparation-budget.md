# Six-caller preparation drafts and budget

Status: prospective planning only. These six JSONs are not approvals or runnable
protocols. No caller source was read, statted, or re-hashed here. The source
locators are historical hints; their presence on a cluster is unverified.

The drafts use `analysis/prepare_released_callers.py` protocol-v1 field names.
They pin the recorded source metadata and exact header sample labels. The source
SHA-256, byte count, and source-row count come from
`standard_transport_report.json`'s compatibility records; the local source path
hints come from that report and `standard_transport_protocol.json`. The transport
protocol pin is `6c39249b38d990304251f19b16f14c5a632b123443f38d4426990542a2a0a472`.
These are recorded pins, not a new verification of the source files.

| Caller | Sample label | Source rows | Recorded bytes | Three-pass source floor | Recorded SHA-256 |
|---|---|---:|---:|---:|---|
| cuteSV | `NULL` | 51,561 | 29,410,475 | 88,231,428 | `9603595adebb54e656513c3ffba416e0d2173763030abef20f804e1c877209c1` |
| DeBreak | `/data1/huheng/HG002/hifi.bam` | 26,421 | 935,962,599 | 2,807,887,800 | `82f8ec62332691118329f4ef995229409b86144f5011d25eae67dece096056d1` |
| Sawfish | `HG002` | 43,944 | 25,716,015 | 77,148,048 | `fd35b27c44e2506491ce0d5706908349ef534a6fe43e87a48ae4efa201e00f9c` |
| Sniffles | `SAMPLE` | 32,567 | 15,004,300 | 45,012,903 | `c2b0220af2867c5017b9c6c0861b318eb806a77e2cc28950fdd525f1c9926cbb` |
| SVIM | `Sample` | 49,512 | 6,682,295 | 20,046,888 | `efb823e8d4022290279400ff632a529d4adcc4c7081479fe2a76456e736f81ce` |
| SVPG | `Sample` | 31,720 | 23,624,851 | 70,874,556 | `8a50b1213be4878801f2466b907f5357e1e5bcc9478053a3e75b7d176f916b7f` |

The full DeBreak input is retained: **935,962,599 bytes**. The six callers remain
fixed. Both downstream screen arms are caller-only filters over the same
11,490-record truth population, with truth SHA-256
`c908217f7ec8eba1efe93f51605675a8a8b9676d9c9ca443d1348ad0a00f68d2` and ordered-ID
SHA-256 `13db07d2c659f578144067d45eea85684816cce6482230e190a1b01b8d627e37`.
Preparation must not filter that truth, alter its order, or score it.

## What the schema lets us budget

The REF run completed under exact independent review. Its 7-GiB reservation was
booked before staging. The current full retained charge is 16,208,704,797 bytes;
this is not an unbooked projection. Raw result review is pending. This does not
validate the denominator or establish a score. The fixed 64-GiB limit is
68,719,476,736 bytes, leaving **52,510,771,939 bytes**.

The six recorded sources sum to 1,036,400,535 bytes. If each `max_source_bytes`
is set to its recorded `source_bytes`, the preparer reserves three source-sized
passes plus the one-byte over-cap/EOF probe on each pass:

```text
Σ 3 × (source_bytes + 1) = 3,109,201,623 bytes
52,510,771,939 − 3,109,201,623 = 49,401,570,316 bytes
```

The second number is the maximum remaining for all weighted output passes,
opaque I/O, the two later screen arms, and their repeated reads/logging. It is
not an observed physical-I/O estimate. The preparation schema weights its nine
output files by `PASSES = (2, 2, 2, 7, 5, 4, 5, 3, 2)`, a sum of 32 per caller;
`sort_temp` has no named-pass weight and must be covered by the opaque-I/O
reservation. For caller `c`, the minimum named input reservation is:

```text
3 × (max_source_bytes_c + 1)
+ 2×annotated_cap + 2×split_cap + 2×derived_cap + 7×sorted_cap
+ 5×released_cap + 4×released_index_cap + 5×native_cap
+ 3×native_bgzf_cap + 2×native_index_cap
+ opaque_io_reservation_c
```

The protocol also requires `preparation_reservation_bytes >= input_read_cap_bytes`.
For storage, `storage_cap_bytes` must cover the sum of all nine output caps plus
the `sort_temp` cap and 1 MiB. The final phase also checks actual outputs,
temporary files, and that 1-MiB allowance. No physical disk quota is established
by these schema fields.

The schema's maximum legal output cap is 4 GiB for each of its ten cap fields.
At that maximum, the nine weighted output passes would cost
`6 × 32 × 4 GiB = 824,633,720,832` bytes, exceeding the entire remaining global
headroom by **772,122,948,893 bytes**, before source passes, opaque I/O, or the
two screen arms. The corresponding minimum storage cap would be 42,950,721,536
bytes per caller; retaining all six maximum-cap output trees would require at
least 257,704,329,216 bytes. These are schema-maximum stress bounds, not selected
caps or storage reservations.

## Unresolved means not approved

Pre-outcome metadata does not give the per-record ALT multiplicity or the
resulting sizes of annotated, split, derived, sorted, compressed, indexed, and
native outputs. A source-row count is not a child count. Therefore every draft
marks `max_children`, all `output_caps`, `storage_cap_bytes`,
`opaque_io_reservation_bytes`, `input_read_cap_bytes`, the sequential
`charged_prior_global_bytes`, and `preparation_reservation_bytes` unresolved.
The present source-size limit and line caps are finite input guards, not
observed line-size claims. Null cap fields intentionally make each draft fail
protocol validation; do not pass them to the preparer.

The fixed schema maxima do not fit. Smaller evidence-supported caps might fit,
but the allowed metadata does not establish them or a safe screen-arm I/O
reserve. Thus this sidecar cannot certify that all six preparations plus both
arms fit the remaining 64-GiB budget. Do not expand the aggregate limit, omit a
caller, assume unobserved child counts, or claim measured physical reads. Main
and the independent reviewer must resolve the bounds and review the exact
bundle before any source access. Every draft keeps
`caller_preparation_approved: false` and
`independent_approval_ref: "pending"`.

## Main integration after the sidecar

The independent REF raw-result review now accepts technical completion only.
Caller preparation/scoring remains unapproved. The schema-maximum stress
bound is not a lower bound on required work, nor proof that useful smaller
caps cannot fit. Pre-outcome child/output/storage limits can be chosen as
finite guards, without asserting that those limits are observed populations.
A breach must fail the whole preparation, not drop records, omit callers or
increase caps after outcomes. Main will freeze such an all-six account and
the later screen margin before execution review. No new inventory pass is
required merely to turn an unknown future output size into a chosen guard.
