# AlignSSL-SV

This repository supports research on structural-variant (SV) calling and
genotyping. The goal is to identify and test an important, rigorous research
question. Compare directions. Use small falsification checks before expensive
experiments. Self-supervised learning (SSL) is optional. DeepSV is historical
context only. It is not the foundation for new work.

## Verified and planned

Completed engineering diagnostics (2026-10-08): 20 native controls passed; all
11,490 unchanged rows are metadata-compatible. 41 REF controls passed; all
11,490 anchored REF spans agree. Source and row-order pins remained stable.

These checks do not validate the truth denominator, ALT alleles, phase,
callability, or scoring. Caller preparation follows a fixed reviewed process.
Check the current progress record for its status. No novel method, publication
lead, or performance claim is established. Keep null and failed results in the
record. A passing engineering check is not a biological result.

## Use this repository

- [Research index](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/README.md) lists research notes and reviews.
- [Restart state](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/RESTART_STATE.md) records current checks and open gates.
- [PROGRESS](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/PROGRESS.md) is the authoritative progress log.
- Technical records: [native controls](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-08-native-throughput-result.md),
  [REF controls](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-08-reference-throughput-result.md), [metadata census](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-08-metadata-census-result.md), and
  [caller preparation review](https://github.com/aayushkrm/AlignSSL-SV/blob/research/genotype-confidence-contracts-20261001/docs/research/2026-10-08-caller-preparation-review.md).
- [results/](results/) contains earlier SSL benchmarks and technical audit
  outputs. Use the research notes to interpret them.
- [Archived README](docs/archive/README-legacy-ssl.md) preserves the former
  results page.

The progress and research-note links above point to the research branch
research/genotype-confidence-contracts-20261001 because default main may not
contain those records. Historical results and the archived README use
repository-relative paths.
