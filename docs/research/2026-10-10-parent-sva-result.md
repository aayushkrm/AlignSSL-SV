# Parental SVA native-policy diagnostic: completed result

**Main disposition:** retire this known case as a new caller-method premise.
Native mosaic mode already emits compatible insertion evidence. Germline
absence plus native mosaic visibility is the expected policy distinction,
not a novel failure or performance improvement. This is a development
diagnostic, not a publication result. Exact child-allele truth is unavailable.

## Fixed execution and observations

Protocol: [frozen parental diagnostic](2026-10-10-parent-sva-diagnostic-protocol.md).
Selection and prospective independent review remain linked there. Source
commit `7f37667a49dc78d76465d18731c36fd4dd8bb50b`.
The two native policies and fixed census ran concurrently without parameter
tuning on one indexed regional NA12878 CHM13 HiFi BAM.
Job **1604237** completed once on hydra-n1, exit0:0. Both native logs report
784 alignments in the regional input; each call used one worker.

| Measurement | Complete observed result |
|---|---|
| Native germline VCF | Present, valid header, zero records; command exit0 |
| Native mosaic VCF | One PASS INS at chr3 POS1=71589909, SVLEN3459; command exit0 |
| Actual mosaic genotype | `0/0`, GQ37, DR60, DV13, PS71380081; not relabelled heterozygous |
| Native support fields | SUPPORT6, SUPPORT_UNSCALED6, VAF0.178, PHASE haplotype2 |
| Fixed primary-read census | Six compatible insertions,97 reference-compatible,18 inadequate-flank names; two records excluded by flags |
| Scope of census | 123 examined records;121 unique retained primary names; six names have external SA declarations |

The six adequate-flank insertion reads have MAPQ60, HP2 and insertion lengths
3410–3466 at position0=71589909. None of those six has an external SA tag.
Native support and the census are **not identical sets**: five read names
overlap. One native support name is inadequate-left-flank in the census and
declares chr5 supplementary placement; one additional adequate-flank census
read is not among native RNAMES. No outside supplementary alignment was fetched.
This set difference is retained, not repaired or labelled a caller bug.
The native ALT hash matches the 3459-base insertion of one primary census
read. These are the same DNA source, not orthogonal validation.

The raw census fraction is6/103=0.0582524 under its frozen flank/MAPQ rules.
It is not native VAF, a prevalence estimate, the paper's denominator or a
test of the reported parental fraction. Eighteen unresolved flank names are
not counted as reference negatives. The caller's POS convention and the
workbook's unspecified convention do not establish exact breakpoint identity.

## Actual resources and complete custody

Slurm elapsed27s, TotalCPU4.228s, MaxRSS39776K, exit0:0. Runner reports
wall26.421046s and CPU4.217957s; do not add nested acquisition CPU again.
Three useful CPUs/4GiB RAM were requested; no GPU or whole idle node.
The earlier failed02 and read-only preflight add1.599s and0.864s measured
Slurm CPU respectively. First failed01 reports zero measured CPU.

Fresh03 upstream HTTP-body reads: **51,611,596B**. Prior prefix and failed02
charge: **39,225,292B**. Cumulative: **90,836,888B**, below the unchanged4GiB
cap. The fresh total includes a repeated37,783,472-byte BAI and all BAM
overfetch. Loopback index delivery, software, custody copies and TLS/header
bytes are not silently included in or claimed by this upstream-body measure.
Both complete request journals independently sum to their manifest charges.

Raw files remain off Git in both scratch and non-expiring project home:
`/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/parent_sva_native_20261010_03/raw-archive`.
Scratch expires October22; the home copy preserves the8,456,194-byte BAM,
both full-index copies, regional index, VCFs, original read evidence,
insertion FASTA, all logs, journal and manifests. Retained03 artifact bytes
excluding run.json:84,379,366. No historical output was overwritten.

Main verified all28 small local artifact hashes against run.json; the four
large BAM/index hashes were separately verified on the home copy. Local
small raw path: `/Users/akm/aayushkrm-AlignSSL/runs/parent-sva-native-20261010-03-raw`.
Run.json SHA256: `58af3dd9bc9d59d47757aeea28359f824c18708aa50c8804e89c40050b4d20cc`.
Unmodified02/03 run manifests are also [tracked in Git](../../results/parent_sva_native/2026-10-10/README.md).
Regional BAM SHA256: `61a570a03b0aa6790530575153c77e3182b1249116d209af147c988333a28e60`.
Full index SHA256: `14ee0700cf338cfde7e201b70ec0f285942677dffc32b805aa2080f2301795ff`.
See [execution failures](2026-10-10-parent-sva-execution.md) for intact01/02 history.

## Review availability and next work

The prospective independent review qualified the cheap assay before launch.
An actual-result review was sent to the maintained reviewer; its later handle
was missing, so no completed independent result audit is claimed. Two new
Luna/max-requested workers returned a service usage-limit error and subsequently
had missing handles. They produced no input recipe or cohort implementation.
Main's raw checks are not substituted for an independent reviewer role.

No major positive or expensive campaign is accepted. The next eligible
unknown-residual question remains HG002 DNA-first coding-path exclusion,
with RNA untouched and the executable P1/endpoint/staged-account conditions
still open. Do not train on, enlarge or tune this retired SVA case to force
novelty. The full publication goal remains active and unmet.
