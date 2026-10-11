# Upstream formatter supports the synthetic mechanism, not a real-data claim

October9 cluster-local / October8 UTC. Firecrawl developer search returned no
usable matched formatter passage; main used direct official tagged source as
the alternative. No genomic data or cluster process was used for this check.

HTSlib1.23.1's `vcf.c` sends nonmissing QUAL and INFO floats to `kputd` and
uses the same formatter in floating-point arrays. This establishes the source
call path, not its execution in job1604204.
[Official VCF implementation](https://github.com/samtools/htslib/blob/1.23.1/vcf.c#L4099),
[array formatting](https://github.com/samtools/htslib/blob/1.23.1/vcf.c#L2894).

The tagged `kputd` implementation scales and rounds values to mostly six
significant digits; exponent cases use C `%g`. Its zero and boundary handling
mean that this is not a universal fixed-six-decimal rule. In particular, values
between100 and1000 are rounded after multiplication by1000. This is consistent
with the synthetic QUAL123.123456789 becoming printed123.123.
[Official numeric formatter](https://github.com/samtools/htslib/blob/1.23.1/kstring.c#L32).

Inference: the shorter VCF text can reparse to a different floating-point value,
even when a standard string comparison sees identical text. The local
synthetic witness demonstrates that inference on localpysam0.24.1. Current
cluster behavior and real affected fields still require the separately reviewed
diagnosis. Tag-source inspection is not installed-binary attestation, proof
of numeric harmlessness, a norm bug, biological performance or novelty.
