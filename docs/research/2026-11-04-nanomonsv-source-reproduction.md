# Synthetic reproduction of a known nanomonsv BND conversion fix

## Protocol, written before the run

The public COLO829 caller VCF identifies nanomonsv 0.7.1, but its exact
binary and input to the converter were not recovered. The v0.7.1 source code
uses the mate reference base for the first BND record when `Dir_1=-`; an
[upstream 2026 fix](https://github.com/friend1ws/nanomonsv/commit/04da795fa71adf495e50c857099ebf3a6ef6f64a)
explicitly changes that base. The commit also changes record sorting and
FILTER headers. This is known prior work, not a new method or a new bug claim.

Use two artificial 100-base contigs, `chrA` of A and `chrB` of C. Give the
unmodified native converter eight interchromosomal inputs: every `Dir_1` /
`Dir_2` pair and either no insertion or `ACG`. Run official v0.7.1 commit
`88cb30538c3e9004f317caec27dbc953b4c788f5` and official fix commit
`04da795fa71adf495e50c857099ebf3a6ef6f64a` in separate Python processes.
Compare output by record ID because the fixed converter also sorts records.

Before execution, source inspection predicts four of eight first records in
the old version will end their local ALT sequence with C while local REF is A,
all with `Dir_1=-`. The other four first records will have A at their local
ALT anchor. In the fixed commit, all eight first records should have A at the
local anchor. Mate anchors should remain C. Record every ALT and the exact
inputs; do not treat the mate insertion strings as a biological error without
an independent orientation analysis. These are controlled inputs, not reads,
caller accuracy estimates, or independent verification of any real allele.

Load `nanomonsv.vcf_convert` from each unmodified checkout via a minimal
package namespace to avoid importing the full caller. Pin the source commits,
check the converter and its two local dependencies for tracked modifications,
save commands, versions, logs and SHA256s, and refuse to overwrite a packet.

## Result and interpretation

Both native converters exited successfully. The observed first-record anchor
counts were:

| Converter | `Dir_1=+` | `Dir_1=-` | Mate anchor |
|---|---|---|---|
| v0.7.1 | 4 A | 4 C | 8 C |
| upstream fix | 4 A | 4 A | 8 C |

An additional direct comparison by record ID checked all 16 record pairs:
the four old `Dir_1=-` first ALT strings differ from the fixed strings only
in the final local base, and the mate records are identical. Both cases with
and without `ACG` are included for every orientation. Both commits reverse
complement the inserted literal on the mate; this replay does not establish
whether that orientation is correct for any real junction.

The [synthetic fixture, native VCFs, logs, per-case comparison and receipt](../../results/nanomonsv_bnd_source_repro_20261104_run01/)
allow the result to be checked. The runner used CPython 3.12 and pysam 0.24.1;
the exact source file hashes, Python version and commands are in the receipt.
All ten listed packet-file hashes were verified after the run.

The 15 unequal first-record anchors in the COLO829 caller file follow the
pattern expected from this old source, and the header reports version 0.7.1.
The original converter input and deployed binary were not recovered, so
this is a source-supported explanation, not a reconstruction of its complete
provenance. The truth VCF is a different file and no common cause is inferred.
The VCF specification permits a local replacement to differ from REF; source
inspection and the author's later fix are needed to interpret this case.
No new caller method, prevalence estimate or independent biological result
is claimed. Independent review of the real-data analysis remains pending.
