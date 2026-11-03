# Full SnpEff annotation replay

## Question and design, written before execution

The preceding 5.1d check exercised its parser and serializer directly. Does
the actual `snpEff` annotation command also uppercase mixed-case mate contig
names, and does this occur in the available Bioconda 5.4.0c build as well?
The latter was the package index's latest listed version on 2026-11-03 UTC;
it is not assumed to represent every installation or release channel.

Create a wholly artificial 100-base `chrA`/`chrB` reference, minimal GFF3
genes, two reciprocal BND records with exact mixed-case mate contigs, and one
ordinary SNV as a basic control. Build a local annotation database separately
for each version, without downloads or usage telemetry. Run the native
annotation command on the same VCF. Record package and jar hashes, commands,
versions, outputs, log messages and exit codes. Compare CHROM, POS, ID, REF,
and ALT by record ID; annotation INFO changes are expected. Report failures
and unsupported BND handling rather than treating them as a pass or as a
biological result.

Pre-run prediction from source and the earlier 5.1d parser replay: both BND
mate names become uppercase while local CHROM names retain their original
case. The ordinary SNV has no embedded contig token. A successful result
would show behavior in these exact local builds and synthetic inputs. It
would not establish production prevalence, clinical harm, or that 5.1d
produced the historical COLO829 intermediate. Independent review remains
required before any major claim.

## Result

Both separate database builds and both native annotation commands exited 0.
On the same artificial input, the tested `5.1d` and `5.4c` jars produced:

| Record | Input CHROM | Input ALT | Both output CHROM | Both output ALT |
|---|---|---|---|
| `a` | `chrA` | `A[chrB:20[` | `chrA` | `A[CHRB:20[` |
| `b` | `chrB` | `]chrA:10]C` | `chrB` | `]CHRA:10]C` |
| SNV control | `chrA` | `G` | `chrA` | `G` |

Both output files retain all three record IDs and the original CHROM, POS,
and REF fields. The BND mate coordinate and orientation strings are unchanged
apart from the case of their embedded contig names. The synthetic output's
`ANN` fields contain the changed BND ALT. The SNV control is annotated with
`WARNING_TRANSCRIPT_NO_START_CODON`, expected for the deliberately artificial
all-A gene; the database was built with protein/CDS checking disabled. This
is not a test of biological annotation correctness. Process stderr files are
empty. All 16 packet-file hashes in the receipt pass.

The earlier parser-only check is therefore supported by a full annotation
replay in both tested versions. This is still a synthetic mechanism check,
not an estimate of prevalence or downstream biological/clinical harm. The
exact historical binary and intermediate COLO829 input are not established.
The [replay packet](../../results/snpeff_annotation_replay_20261104_run01/README.md)
preserves the artificial reference, GFF, VCF, outputs, logs and commands.
