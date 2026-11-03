# SnpEff 5.1d synthetic VCF parser replay

This is a two-record artificial input. The native 5.1d parser and serializer
changed `chrB` to `CHRB` and `chrA` to `CHRA` inside BND ALT fields while
preserving the other record fields. See the [protocol and limitations](../../docs/research/2026-11-04-snpeff-case-reproduction.md).
This is not the SnpEff annotation workflow or proof of a historical run.

The Bioconda package is `snpeff-5.1d-hdfd78af_0.tar.bz2` from
<https://conda.anaconda.org/bioconda/noarch/snpeff-5.1d-hdfd78af_0.tar.bz2>.
Its MD5 matches the [Bioconda package metadata](https://api.anaconda.org/package/bioconda/snpeff).
The native jar reports `SnpEff 5.1d 2022-04-19`. The Eclipse Java compiler is
from [Maven Central](https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/3.38.0/ecj-3.38.0.jar);
its SHA1 matched the published Maven sidecar. The JARs and package are outside
Git; their SHA256 hashes, runtime version and exact commands are in
[receipt.json](receipt.json).

With those pinned jars available, compile and run from the repository root,
replacing the paths:

```sh
java -jar /path/ecj-3.38.0.jar -11 -classpath /path/snpEff.jar \
  -d /tmp/snpeff-classes analysis/SnpEffVcfRoundTrip.java
java -cp /tmp/snpeff-classes:/path/snpEff.jar SnpEffVcfRoundTrip \
  results/snpeff_case_repro_20261104_run01/input.vcf
```

`output.vcfbody` contains the raw two-line program output. Empty stdout and
stderr files are retained for the compiler, and stderr is retained for the
run. The original script did not produce a complete VCF header.
