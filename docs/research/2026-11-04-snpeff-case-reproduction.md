# SnpEff 5.1d synthetic BND contig-case check

## Protocol, written before execution

The ONT COLO829 VCF header reports SnpEff 5.1d, while its BND mate-contig
tokens are uppercase and its header contigs are not. Official SnpEff 5.1d
source at commit `070889b7c638e9c64ecb52d911a85402ee28c7a1` uppercases the
entire ALT field when parsing. We will test whether the released 5.1d Java
parser and serializer actually change a synthetic BND's mate-contig case.

Use a two-record invented VCF with local contig names `chrA` and `chrB` and
matching mixed-case mate tokens. Invoke the native `VcfFileIterator` and
`VcfEntry.toString()` from the Bioconda 5.1d build; no annotation database or
real reads are needed. Predict, from the inspected source, that local CHROM
will retain case while each ALT mate token becomes `CHRA` or `CHRB`. Capture
the full command, package and jar hashes, version, fixture and output. The
package is an accessible 5.1d build, not the unverified binary used in the
2024 production run. A positive replay is a plausible mechanism, not proof
of that file's exact intermediate history or of clinical impact.

## Result

The native round trip exited successfully on both synthetic records. It
preserved each local `CHROM` and uppercased the mate-contig token in `ALT`:

| Input ALT | Output ALT |
|---|---|
| `A[chrB:20[` | `A[CHRB:20[` |
| `]chrA:10]C` | `]CHRA:10]C` |

For these two records, an independent field-by-field check found no other
changed field. The harness calls the native parser and serializer directly;
it does not run SnpEff's annotation pipeline or serialize a complete header.
The 5.1d package, Java runtime, compiler, exact commands and checksums are
recorded in the [small replay packet](../../results/snpeff_case_repro_20261104_run01/README.md).

The observed version's parser behavior can produce the case pattern found
in the public COLO829 VCF, whose header also names SnpEff 5.1d. The original
intermediate VCF and deployed binary were not recovered. This does not prove
the exact historical pipeline sequence, imply a biological variant error,
or establish behavior for all versions and tools. A later [full annotation
replay](2026-11-04-snpeff-annotation-replay.md) reproduces the behavior in the
tested 5.1d and 5.4c builds on a separate synthetic fixture. The real-data
comparison remains provisional pending independent review.
