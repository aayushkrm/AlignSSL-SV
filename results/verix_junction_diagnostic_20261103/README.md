# Synthetic Verix junction diagnostics

These inputs are fully synthetic. The native tool reports breakpoint-based
matches; the results do not establish an error in a biological callset.
The [research record](../../docs/research/2026-11-03-verix-native-diagnostic.md)
explains the event construction, controls, actual results and limitations.

| Packet | Input structures | Native raw output |
|---|---|---|
| [run01](../verix_junction_diagnostic_20261103_run01/) | inversion versus deletion plus retained circle | seven command logs, VCF/JSON results and receipt |
| [run02](../verix_junction_diagnostic_20261103_run02/) | two distinct single-linear derivatives | seven command logs, VCF/JSON results and receipt |
| [run03](../verix_junction_diagnostic_20261103_run03/) | run01 with corrected `MATEID` header cardinality | seven repeated cases and header-difference receipt |
| [run04](../verix_junction_diagnostic_20261103_run04/) | run02 with corrected `MATEID` header cardinality | seven repeated cases and header-difference receipt |

The run02 [fixture check](linear-fixture-check.json) was produced by an
independent traversal of the reciprocal VCF links. It checks both saved
derivative sequences against the BND graph. The result and this README were
created after the native runs; each run's receipt binds its own native files.

## Reproduce

Use an isolated CPython 3.12.14 environment. Clone
[`PopicLab/verix`](https://github.com/PopicLab/verix) and check out commit
`7cb8524a941ce0d81dd04b0de51e009199386614`. Install the versions in
[`requirements-runtime.txt`](requirements-runtime.txt), then install this
checkout with `--no-deps`. The versions capture one macOS x86-64 execution;
they are version pins, not wheel hashes. Before the run, the installed Verix
Python modules matched the checkout byte-for-byte. The raw receipts retain
the exact CLI arguments and the SHA256 of every native output.
The [source check](source-install-check.json) also records untracked `build/`
and `verix.egg-info/` products created by installation; tracked source files
remain unchanged. A [receipt check](native-receipt-check.json) records the
hash and command-exit verification for both original packets.

From the repository root, with paths adjusted for the checkout and environment:

```sh
python -m analysis.run_verix_junction_diagnostic \
  --source /path/to/verix --verix /path/to/env/bin/verix --output /tmp/verix-run01
python -m analysis.run_verix_linear_junction_diagnostic \
  --source /path/to/verix --verix /path/to/env/bin/verix --output /tmp/verix-run02
python -m analysis.verify_verix_linear_fixture /tmp/verix-run02/fixtures
```

Each output directory must be new. Match-set ordering in native `MATCHES`
fields can vary; compare match classes, the content of the sets and controls,
not raw byte equality across environments. The stored SHA256s attest the
original packet, not deterministic serialization across reruns.

The [header-only runner](../../analysis/rerun_verix_header_correction.py)
reproduces the corrected copies and repeats, preserving the originals. The
[EBI validator batch](validator-batch-01.stdout.json) retains all 20 results,
including warnings; the [Slurm accounting](validator-batch-01.accounting.txt)
and [launcher log](validator-batch-01.stderr.txt) are also retained. The
validator accepted even the original incorrect reserved-field declarations,
so its pass cannot establish that particular header condition. It was not a
FASTA assembly check.

The native stdout files preserve Verix's trailing space on its blank `[INFO]`
line. They are original tool output and are excluded from authored-file
whitespace checks.
