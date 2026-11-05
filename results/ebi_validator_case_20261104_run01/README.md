# Synthetic EBI validator case check

The [protocol and result](../../docs/research/2026-11-04-ebi-validator-case-protocol.md)
describe the five artificial VCFs, including deliberately malformed controls,
and the warning-level validator configuration. No human sequencing data or
reference FASTA were used. `input-manifest.json` pins the original synthetic
fixture, preparer script and each test input.

`attempt01-pending.*` preserves the debug-partition allocation attempt that
was cancelled before it started. `attempt02.stdout.json` contains all native
commands, exit statuses, stdout, stderr and summary-report contents from the
successful four-CPU batch; `attempt02.stderr.txt` contains scheduler messages.
`accounting.txt` contains Slurm records for both jobs. `receipt.json` hashes
the 11 packet files and the cluster runner; the validator binary hash matches
the official v0.10.2 Linux release asset.

The input files can be regenerated from the preceding synthetic SnpEff input:

```sh
python analysis/prepare_ebi_case_inputs.py \
  --source results/snpeff_annotation_replay_20261104_run01/input.vcf \
  --output /tmp/ebi-bnd-inputs-new
```

Run `analysis/cluster_ebi_case_batch.py` with the pinned Linux binary, the
generated `inputs` directory, and its `input-manifest.json`. The runner uses
four worker processes via threads and writes the complete results to stdout.
The validator was not supplied a FASTA, so its output is not an allele check.
