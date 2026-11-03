# Native SnpEff annotation replay

The [protocol and result](../../docs/research/2026-11-04-snpeff-annotation-replay.md)
cover two pinned native versions and a completely artificial genome. This
packet contains the input FASTA, GFF3 and VCF, both complete output VCFs,
command logs, per-record comparison and SHA256 receipt. The synthetic genes
are not validated biological transcripts; the SNV annotation reports a
missing-start-codon warning. No human genomic reads or reference are used.

Jars are retained outside Git. The first is from the [5.1d Bioconda package](https://conda.anaconda.org/bioconda/noarch/snpeff-5.1d-hdfd78af_0.tar.bz2).
The second is from the [5.4.0c Bioconda package](https://conda.anaconda.org/bioconda/noarch/snpeff-5.4.0c-hdfd78af_0.conda).
The latter package SHA256, as listed by the [package index](https://api.anaconda.org/package/bioconda/snpeff),
is `5c0f345385dd39fc6ebb5029fceb589a5c2c19c2abf516e46e49e2bb274e023f`.
The JAR identifies itself as `5.4c 2026-02-23`. JAR hashes, the exact Java
commands, exit codes, and per-packet hashes are in [receipt.json](receipt.json).

With the pinned JARs, rerun from the repository root with new output and
workspace paths. The runner builds both artificial databases in parallel.

```sh
python3 analysis/run_snpeff_annotation_replay.py \
  --jar-51d /path/to/5.1d/snpEff.jar \
  --jar-54c /path/to/5.4c/snpEff.jar \
  --workspace /tmp/snpeff-artificial-db-new \
  --output /tmp/snpeff-annotation-replay-new
```

The two builds turn off remote database downloads and usage telemetry. Both
annotation outputs are retained in full. Output INFO annotations are expected
to change; the comparison is restricted to record identity and core fields.
