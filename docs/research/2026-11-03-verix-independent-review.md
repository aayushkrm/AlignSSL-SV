# Independent review: native Verix junction diagnostic

**Decision: accept the narrow, descriptive native-interface result for the two received packets, subject to the VCF-header and provenance limits below.** The records encode different reciprocal adjacency sets while the native grouped breakpoint comparison calls both self and rewired inputs `complete`. This is consistent with Verix's stated breakpoint-set contract. It does not establish a real caller error, a biological result, a defect in Verix, or a publishable research opportunity.

I inspected the [run01 packet](../../results/verix_junction_diagnostic_20261103_run01/), [run02 packet](../../results/verix_junction_diagnostic_20261103_run02/), [run01 generator](../../analysis/run_verix_junction_diagnostic.py), [run02 generator](../../analysis/run_verix_linear_junction_diagnostic.py), [native diagnostic note](2026-11-03-verix-native-diagnostic.md), both antecedent research notes, and the local Verix v0.0.2 source and installed Python files. I did not rerun either generator or Verix. The model and effort level were requested; they are not independently attested.

## Structural check

Here `R` is a breakend whose retained reference segment ends at POS; `L` is one whose retained segment starts at POS. A VCF breakend ALT describes a local side and a remote side. The [VCF 4.3 specification](https://github.com/samtools/hts-specs/blob/master/VCFv4.3.tex) defines the bracket orientations and reciprocal-mate representation.

```text
run01 reference:  P | B | S                 cuts: 1000/1001, 30000/30001
truth:             P - reverse-complement(B) - S
rewired:           P - S          plus      circle(B)

run02 reference:  P | B | C | S             cuts: 1000/1001, 15000/15001,
                                                    30000/30001
truth:             P - reverse-complement(B) - reverse-complement(C) - S
rewired:           P - C - B - S
```

For run01, `P=1..1000`, `B=1001..30000`, and `S=30001..40000`, all inclusive. The truth edges are `R1000--R30000` and `L1001--L30001`; the alternative edges are `R1000--L30001` and `L1001--R30000`. I checked all ALT coordinates, local and remote bracket orientations, REF bases, reciprocal `MATEID`s, `EVENT`, and genotypes in both files. Each of the four oriented ends is used once. The modeled alternative is balanced **only if the internal circle is retained in one copy**. `EVENT` does not establish that retention or a shared physical molecule. An intact second haplotype and one copy of the circle are synthetic assumptions. The all-A reference makes placement in sequence highly ambiguous, so this is a labeled-graph interface test.

Run02 avoids the circle. `P=1..1000`, `B=1001..15000`, `C=15001..30000`, and `S=30001..40000`. Its truth pairs are `ac, be, df`; its rewired pairs are `ad, be, cf`. With segment-internal connections `b--c` and `d--e`, each pairing gives one path from `a` to `f`, with every segment used once. No selected pair is a reference junction (`ab`, `cd`, or `ef`). An independent enumeration over the two segment orders and their orientations gives four eligible pairings, in the same lexical order recorded in `construction.json`; the first two are the selected pairings. This verifies the selection rule from the available artifacts, not an independent timestamped preregistration.

I checked the actual six-record VCFs and reciprocal ALT/MATEID semantics. The only shared novel junction is `be`: exact oriented-junction overlap is **1/3**, not zero. Independently reconstructing both derivative FASTAs from the reference gives the stored sequences exactly. Both are 40,000 bases; they differ both directly and after reverse-complementing a whole derivative. All 39,970 canonical 31-mers in the synthetic reference are unique. This is a finite exact check on this artificial reference, not a claim of general mappability. The FASTAs are generated from the same engineered reference and VCF design; they are not independent biological validation.

**Header caveat for both packets:** the files declare `VCFv4.3` but define `MATEID` with `Number=1`; the VCF 4.3 reserved-field definition uses `Number=.`. Each record here has exactly one mate and the native parser accepted it, and the reciprocal breakend semantics above are correct. I did not run an independent full VCF validator, so I do not attest full VCF 4.3 header conformance. A future separate packet should use the version's reserved-field declaration and validate it without changing these received files.

## Native observations

All cases explicitly use `--formats multi multi --csv_links EVENT EVENT`, with one query event and one target event. Thus “default” below means default **matching parameters**, not Verix's default input-grouping format. The default logs show `match_thr=500`, `merge_thr=2`, and no breakend mode. The strict logs show `--breakend_mode --match_thr 0 --merge_thr 0 --enforce_type --enforce_genotype --enforce_ins`. Every native command has recorded exit code 0.

| Packet and comparison | Native class | Matched / query ends after merge | Target coverage |
|---|---:|---:|---:|
| run01 default self | complete | 2/2 | full |
| run01 default rewired | complete | 2/2 | full |
| run01 strict self | complete | 4/4 | full |
| run01 strict rewired | complete | 4/4 | full |
| run01 strict position | partial | 3/4 | partial |
| run01 strict orientation | partial | 3/4 | partial |
| run01 strict genotype | spurious | no candidate; 4 spurious | none |
| run02 default self | complete | 3/3 | full |
| run02 default rewired | complete | 3/3 | full |
| run02 strict self | complete | 6/6 | full |
| run02 strict rewired | complete | 6/6 | full |
| run02 strict position | partial | 5/6 | partial |
| run02 strict orientation | partial | 5/6 | partial |
| run02 strict genotype | spurious | no candidate; 6 spurious | none |

The complete cases have zero breakpoint distance, zero spurious endpoints, and native `f1=1.0` for one grouped event. The negative-control reports omit the F1 field; do not present an invented value. The default matched sites are the merged pairs, not the original individual endpoints. The strict result retains six oriented ends in run02, so default merging alone cannot explain its result. These are two tested combinations, not a full factorial test: standard mode with zero thresholds and breakend mode with default thresholds were not run in these packets.

The controls are informative within this limited contract. The position control changes one endpoint and updates its mate ALT; the orientation control flips one local orientation and updates the mate bracket; the genotype control changes all records from `0|1` to `1|1`. Their BNDs remain reciprocal. The first two are **parser-sensitivity perturbations**, not demonstrated complete single-copy chromosome models: moving one end leaves the complementary cut end unaccounted for, and flipping `R15000` to `L15000` in run02 also changes the interbase cut from after base 15000 to before it. Do not assign them the same balanced-derivative interpretation as the main fixtures. No separate negative controls test `--enforce_type` or `--enforce_ins`; those enabled flags do not themselves prove those checks are effective. No inserted sequences are present.

The source explains the observation for this checkout: `io.py` groups records and collects local breakpoint position and, in breakend mode, local orientation; `sv.py` matches those points with type and genotype checks, not paired adjacency edges. ALT mate positions are also used in grouping, and original records exist during parsing, so the precise claim is about **the tested matching decision**, not that Verix never reads or retains an ALT field. `--enforce_ins` compares insertion versus non-insertion categories in this matching path; the present data do not test inserted-sequence identity. The tool's [user guide](https://github.com/PopicLab/verix/blob/main/docs/user_guide.md) describes multi-record grouping and breakpoint/breakend matching.

The main input fixtures use `0|1`; their generated `query.vcf`, `target.vcf`, and `matches.vcf` use `0/1`. The genotype-control query similarly changes `1|1` to `1/1`. The source retrieves the GT allele tuple and writes it without setting phased status; it does not compare a phase set or a phased derivative path. The summary VCFs use a synthetic `<SV>` and coordinate-only `BKPS`; they do not preserve original ALT/MATEID edges or breakpoint orientations. In the strict orientation control, the summarized query and target can therefore look identical even though the native comparison reports `partial`. Preserve the input VCFs for any adjacency or phase audit. The genotype control tests allele-tuple disagreement, not phased versus unphased distinction or global haplotype-label equivalence.

## Evidence and reproducibility boundary

- I independently recomputed all receipt hashes: **55/55** non-receipt files in run01 and **58/58** in run02 matched, with no missing or unlisted files. Receipt SHA-256 values were `5754b2b0133a5d7904241117ef11af1c080d9af885e7e85ac8c145c5ab7cda1f` and `2475b12fc876b42317f7b4b23dbf4a37b4c2d536b5d5eca3be263701bb0ee16c`, respectively. These are consistency checks, not signatures or proof of execution history.
- The receipts report Verix commit `7cb8524a941ce0d81dd04b0de51e009199386614`; the logs report v0.0.2. At review time, all seven installed Verix `.py` files matched the adjacent source checkout byte for byte. The receipts do not hash the runner, executable, source checkout, or complete dependency environment, and I did not use Git or independently replay the commands. The commit and execution provenance are therefore reported, not independently attested.
- The two packets use the same tool, grouping policy, synthetic design family, and runner infrastructure. They are related demonstrations, not independent experimental replications. A shared `EVENT` is an explicit grouping assumption; an event ID or `0|1` alone is not proof that a caller resolved a whole derivative path.

## Fair comparison and decision boundary

For these exact coordinates, a simple undirected oriented-junction comparison has the following hand-checkable expectations. This is a transparent synthetic oracle, not an independently run published baseline:

| Comparison | Matching junctions | Junction precision / recall | Exact whole-event edge set |
|---|---:|---:|---|
| Either truth against itself | all | 1 / 1 | equal |
| run01 rewired against truth | 0 of 2 | 0 / 0 | different |
| run02 rewired against truth | 1 of 3 | 1/3 / 1/3 | different |

Count each reciprocal pair once. An adjacency metric is still weaker than a phased derivative-path comparison: homolog assignment, segment order, copy number, circularity, and unresolved grouping require separate evidence. If a real caller does not assert grouping or phase, its path status is **unknown**, not wrong.

Verix remains the fair baseline for its published grouped breakpoint-completeness and fragmentation objective, not a strawman graph scorer. A later study would need directly comparable event definitions and appropriate published controls: [Truvari](https://doi.org/10.1186/s13059-022-02840-6) for supported component records, [TT-Mars](https://doi.org/10.1186/s13059-022-02666-2) for supported assembly-based per-call validation, and [vcfdist](https://doi.org/10.1186/s13059-024-03394-5) and [phab](https://github.com/ACEnglish/truvari/wiki/phab) for phased sequence comparison where their inputs and practical conditions permit. A tool's unsupported representation must be recorded as unevaluable rather than scored as a failure. A study would also need independently resolved real truth and explicit caller-reported adjacency or phase, with missing relationships treated as unevaluable. The [literature delta](2026-11-03-literature-delta.md) and superseding addendum in the [complex-event note](2026-10-14-complex-event-evaluation-opportunity.md) already restrict novelty and feasibility claims. These synthetic results justify no biological prevalence, caller-failure, clinical, or publication-novelty claim and do not by themselves select an expensive campaign.

## Addendum: header-only repeats and external validation

**Decision: the additional packets support the same narrow native-interface finding.** I inspected [run03](../../results/verix_junction_diagnostic_20261103_run03/), [run04](../../results/verix_junction_diagnostic_20261103_run04/), their correction manifests and receipts, the native outputs, and the [validator batch](../../results/verix_junction_diagnostic_20261103/validator-batch-01.stdout.json), including its [accounting](../../results/verix_junction_diagnostic_20261103/validator-batch-01.accounting.txt) and [stderr](../../results/verix_junction_diagnostic_20261103/validator-batch-01.stderr.txt). I did not run the repeat or validator, access the cluster, or change the received packets.

### Input and receipt audit

For each of the ten corrected VCFs, I compared bytes with its named original. The **only** change is one `MATEID` header declaration from `Number=1` to `Number=.`. All other fixture files are byte-identical: one reference in run03, and the reference, two derivative FASTAs, and construction JSON in run04. The manifests name the correct original directories and receipt hashes, and both original and corrected per-fixture hashes match their manifests.

| Packet | Relation | Receipt entries verified | Receipt SHA-256 |
|---|---|---:|---|
| run01 | original | 55/55 | `5754b2b0133a5d7904241117ef11af1c080d9af885e7e85ac8c145c5ab7cda1f` |
| run02 | original | 58/58 | `2475b12fc876b42317f7b4b23dbf4a37b4c2d536b5d5eca3be263701bb0ee16c` |
| run03 | header-only copy of run01 | 56/56 | `358f76e5089a7574f01d29c0b0a28029001f74325599723923732f0f604cd413` |
| run04 | header-only copy of run02 | 59/59 | `f433b63b9c421e5eb203e215ff03b6ec06ba8b263d5f1b609bd3428c9212ce5b` |

There are no missing or unlisted non-receipt files in the four directories. The original receipt hashes also match those independently recorded above, so the listed original files and their receipts remain unchanged since that review. These hashes establish internal consistency, not a cryptographic signature of who ran the tools.

### Native repeat audit

All 14 repeat commands have recorded exit code 0. Their arguments and flags match the corresponding original commands after substituting the run directory; both repeats still explicitly group on `EVENT`. All **14 `report.json` files are byte-identical** to their counterparts. All query and target VCFs are byte-identical, and all match VCF headers and data records agree after normalizing the order of the `MATCHES` endpoint list; two match VCFs are byte-identical without normalization. Thus the differences in the other match VCF bytes do not change the compared match records.

| Repeated fixture | Default self and rewired | Strict self and rewired | Strict position / orientation | Strict genotype |
|---|---|---|---|---|
| run03, from run01 | complete, 2/2 merged sites | complete, 4/4 ends | partial, 3/4 each | spurious, 4 ends |
| run04, from run02 | complete, 3/3 merged sites | complete, 6/6 ends | partial, 5/6 each | spurious, 6 ends |

The repeat receipts record eight workers and `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, and `MKL_NUM_THREADS=1`; the runner source sets these values. This is recorded execution configuration, not an independent measurement of live processes. The existing controls, phase-output, grouping, and biological-interpretation caveats remain in force.

### Validator audit and limits

The batch contains exactly five VCFs from each of runs 01–04. All **20 recorded input SHA-256 values match the corresponding local fixture bytes**. Every invocation used `-l warning -r summary`, recorded exit code 0, and produced one summary reporting the input valid plus one warning that valid `reference` metadata is absent. No other summary warning or error is recorded. The accounting artifact reports Slurm job `1614653` as `COMPLETED`, `0:0`, with four CPUs and one second elapsed. The batch JSON's SHA-256 at review was `0cb6cbd46049be94702fa36fba33d0595a9fa268354bcdd87c0ab7a3e2e9bf59`.

The batch records Linux validator SHA-256 `7326fc83425f5367f9974aaa223f2b48b1854bf9ecd5e9e5eae3899b3107fc87`, which matches the [official v0.10.2 Linux release asset digest](https://github.com/EBIvariation/vcf-validator/releases/expanded_assets/v0.10.2). I could not independently rehash the remote binary or attest the execution history; the recorded hash and logs are consistent with that release. The validator also accepted all ten **original** `Number=1` files without a cardinality warning in these runs. Therefore its success does not itself establish that the reserved `MATEID` declaration was checked; the corrected declaration follows the VCF 4.3 listing, and no broader validator behavior is inferred from this example.

This was the syntax/semantic validator in warning mode, not the separate FASTA-based `vcf_assembly_checker`; the [validator documentation](https://github.com/EBIvariation/vcf-validator/blob/v0.10.2/README.md) distinguishes their scopes. No FASTA was passed to the validator. The earlier independent REF-base and graph checks remain separate evidence, and the missing-reference warning remains part of the result. A zero exit here is not a proof of full VCF conformance, complete reciprocal-event biology, phase, or the structural validity of the sensitivity controls. These header-only repeats are not independent biological samples and do not change the publication decision above.
