# Exploratory COLO829 BND anchor census

## Question and observed counts

An initial inspection of one three-junction tutorial contig showed that one
caller BND's local ALT anchor differed from its local REF. This prompted a
whole-file census of both public callsets. The observation and this analysis
are **exploratory**, not a pre-registered discovery or an estimate of how
often callers fail. The tutorial case and candidate pattern were already seen
before the census was written.

| File and subset | BND records | ALT local anchor equals REF | ALT local anchor differs from REF |
|---|---:|---:|---:|
| ONT caller VCF, all FILTER values |66|51|15|
| ONT caller VCF, PASS only |36|27|9|
| ONT caller VCF, `Too_low_VAF` |30|24|6|
| hg38-lifted truth VCF, PASS |26|13|13|

These denominators are **records**, not independent structural events. All
66 caller BNDs and all 26 truth BNDs fit the parser's explicit single-base REF
and single-ALT grammar, and each has one uniquely reciprocal record under the
stated rules. The 66 caller records provide MATEID links; none of the 26 truth
records does. Truth mates are inferred from uniquely reciprocal coordinates
and orientations, not validated as independent biological alleles.

Among the 15 caller records with different local anchors, all 15 are on the
left-local ALT form and have an anchor equal to the paired record's REF. In
the truth file, 9 of 13 differing anchors equal the paired REF and 4 do not.
Each caller difference occurs in one of 15 pairs; the other 18 caller pairs
have neither record differing. The truth has nine pairs with one differing
anchor, two with two, and two with neither. These are descriptions of the
two supplied files, whose histories and sequencing inputs may overlap.

The VCF specification allows the local replacement string to differ from REF.
Counts alone therefore do **not** show a serialization error, a false SV,
or a base-level sequencing error. Subsequent source inspection and a
[synthetic native replay](2026-11-04-nanomonsv-source-reproduction.md) show
that the reported caller version has a specific behavior consistent with the
caller pattern; its author fixed that behavior upstream in 2026. The exact
binary and converter input for this file were not recovered. No common cause
is inferred for the separate truth VCF. There is no estimate of prevalence
outside these files.

## Provenance and limits

The ONT VCF identifies sample `COLO829`, GRCh38 no-alt reference, and
nanomonsv 0.7.1 in its header. The truth VCF identifies `COLO829T` and is
labeled hg38-lifted. Names alone do not verify identical passage, aliquot, or
independent reads. The truth set is a different analysis resource, not
automatically independent of the ONT data at every event. The tutorial
derivative contig and ONT caller also share ONT data. Neither dataset supplies
a verified phase assignment for this complete path in the checked records.

The [small source packet and reproducible per-record output](../../results/colo829_bnd_anchor_census_20261103/README.md)
give exact public links and SHA256s. Full source files remain outside Git.
Eight targeted parser controls pass, including the four VCF orientations,
a permissible local replacement, unknown/ambiguous mates and a full-file
denominator. The independent actual-data audit is pending after its subagent
encountered a usage-limit error. An accepted result will remain limited to the
exact inputs above.

## Next checks

Independently recompute all counts and inspect the matching code and the
specific derivative contig's junction sequences. If a specific source has
supplied reference and alternate bases,
compare the spelled alleles under the VCF convention before attributing an
error. Do not treat an unsupported representation or an ungrouped set of BND
records as a wrong phased path. A reproducible sequence inconsistency, if
established, would still need orthogonal evidence, other independent files,
appropriate established baselines, and an assessment of practical impact
before motivating a publication claim.
