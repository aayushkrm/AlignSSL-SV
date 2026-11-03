# Synthetic nanomonsv BND source replay

The [protocol and result note](../../docs/research/2026-11-04-nanomonsv-source-reproduction.md)
describes this eight-case synthetic fixture and the known upstream fix.
`synthetic.fa`, its index and `synthetic.tsv` are invented inputs, not human
genome or sequencing data. The two VCFs are unmodified converter output.
`comparison.json` lists the records by synthetic case. `receipt.json` records
the exact source commits, source file hashes, Python, pysam, commands, logs
and ten original packet-file SHA256s.

To replay, check out the two commits below into separate clean directories
from [nanomonsv](https://github.com/friend1ws/nanomonsv), use Python 3.12 with
`pysam==0.24.1`, and run from the repository root with a new output path:

```sh
python analysis/reproduce_nanomonsv_bnd.py \
  --old-source /path/to/nanomonsv-88cb305 \
  --fixed-source /path/to/nanomonsv-04da795 \
  --output /tmp/nanomonsv-source-replay
```

The runner checks both commit IDs and tracked local converter dependencies.
It loads the unmodified converter through a minimal package namespace and uses
separate processes to prevent one source version from replacing the other.
