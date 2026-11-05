# EBI validator: synthetic BND contig-case sensitivity

## Protocol, written before execution

The observed SnpEff-to-comparator effect raises a narrow follow-up: does the
tested EBI VCF validator flag a BND mate contig absent from the VCF's declared
contig IDs? Use only artificial records and a pinned
[`vcf-validator` v0.10.2 Linux binary](https://github.com/EBIvariation/vcf-validator/releases/tag/v0.10.2)
with SHA256 `7326fc83425f5367f9974aaa223f2b48b1854bf9ecd5e9e5eae3899b3107fc87`.
This is a check of one validator and configuration, not a claim about all
validators or VCF conformance.

Start with the three-record artificial VCF used in the SnpEff annotation
replay. Create five inputs, differing only as stated:

1. Original header-matching BNDs and SNV.
2. Both BND ALT mate-contig names changed to uppercase `CHRA`/`CHRB`.
3. Both BND ALT mate-contig names changed to undeclared `chrZ`.
4. One record's local CHROM changed to undeclared `chrZ`.
5. One ALT replaced by a deliberately malformed non-DNA allele.

Use `-l warning -r summary`, no FASTA, and identical settings for all cases.
Retain input SHA256s, native exit codes, stdout/stderr and complete summary
reports. Run in parallel on four allocated CPU cores. The input lacks a
`##reference` line, so a missing-reference warning is expected. There is no
pre-run assumption that the validator is designed to check remote mate
contigs. The malformed-ALT control tests whether at least one known invalid
allele is flagged; it cannot validate every other semantic check.

Interpret warning and error classifications literally. An exit code of zero
does not prove complete validation, allelic correctness or clinical impact.
The `chrZ` input deliberately breaks reciprocal mate relationships as well as
the header alias; it is a sensitivity probe, not a biological variant.
Independent review remains pending.

## Result

The pinned validator returned these results:

| Artificial input | Exit | Summary outcome beyond missing-reference warning |
|---|---:|---|
| Header-matching input | 0 | No additional warning |
| Uppercase remote contigs | 0 | No additional warning |
| Undeclared `chrZ` remote contigs | 0 | No additional warning |
| Undeclared `chrZ` local CHROM | 0 | Warning that `chrZ` is absent from contig metadata |
| Malformed ALT `Z` | 1 | Error for invalid alternate allele |

All five summaries include the predicted missing-reference warning. For the
two remote-contig probes the validator says the input is valid under its
tested checks, while warning about an unknown local CHROM and rejecting the
malformed ALT control. This shows a **missing warning in these exact runs**;
it does not assert that the validator promises a remote-mate lookup, that all
validators behave this way, or that any biological variant is correct.

The first allocation attempt, job `1614658`, remained pending in the debug
partition for resource availability and was cancelled before allocation. No
scientific task ran and its scheduler stderr is retained. The unchanged
four-CPU batch ran as job `1614659` on the `amd_256M` partition and completed
`0:0` in one second; accounting reports 0.155 CPU-seconds and 14,800 KiB
maximum step RSS. The [packet](../../results/ebi_validator_case_20261104_run01/README.md)
retains both attempts, source-generated inputs, full native reports,
accounting and 11 verified file hashes. No unrelated job was touched.
Independent review of the wider findings remains pending.
