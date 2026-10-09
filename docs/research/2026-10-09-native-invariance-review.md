# Independent native CIGAR invariance review

2026-10-09. Initial disposition: **CONDITIONAL ACCEPT for a bounded scientific diagnostic; HOLD acceptance of any result until the endpoint rules below are fixed and the completed observer is reviewed.** This is not execution approval or selection of a publication direction. No paper-level novelty is required to justify this diagnostic. Requested maintained reviewer configuration: Sol6.1/high; actual backend model and effort are not independently attested.

## Scope and evidence

Read the complete goal attachment, prior post-diagnosis review, Sawfish seed/target source note, native-control source check, fragmentation prior-art note, trace-interface note and tool-metadata note. After main reported it complete, read the full candidate protocol `native-cigar-invariance-20261009-01`. After user authorized completed-file inspection, read the full fixture and its tests. Did not read partial observer or decision-worker files, and did not wait for them.

This review reads local documentation and code only. Source and prior-art facts below are reported evidence from those notes, not a new source or literature audit. No native execution, test execution, installation, network, SSH, genomic input or Git operation occurred. Only this review file was written. No live result exists in the evidence inspected here.

| Read document | Observed SHA256 before fixture follow-up |
|---|---|
| Full objective | `624de4ace478d0476cc8d899197c61db22a32c55543edb61f79ac7e9bd4145a0` |
| Candidate protocol | `0526d5772824705357502f2149d18daf3ba0a4083953aa2baab2854efd247a58` |
| Prior maintained review | `28bbd1ecf2683ccfafccac570b1479d9706b4a6ff2ffaf14f910edad32735258` |
| Seed/target source note | `021dac404e657bbcaf7faacfc066ce3318670841dae354894076ee57560c3fcd` |
| Fragmentation prior art | `47f8620f3d18ea8a64e225b09d3f29d040db9ef7cf9dee15d55a9353be6986b8` |

Reviewed completed code: [fixture](/Users/akm/aayushkrm-AlignSSL/repo/analysis/native_cigar_fixture.py) and [tests](/Users/akm/aayushkrm-AlignSSL/repo/tests/test_native_cigar_fixture.py). These are source-reading findings, not claims that tests passed or that Sawfish accepts the input.

## Scientific value and inference limit

The useful question is whether a fixed caller changes exact allele recovery when valid CIGAR representation changes while the molecules remain fixed. This can falsify a proposed local whole-pipeline failure cheaply. It can also show that a native setting already addresses that failure. Either outcome can inform investment before a larger study. It cannot measure mapper prevalence, human performance, HiFi error behavior, repeat-purity effects or publication value by itself.

```text
Same reference, molecules, tags and endpoints
                 |
       +---------+------------------+
       |                            |
     60I                   20I 5= 20I 5= 20I
       |                            |
    default                  default / margin30
       |                            |
       +---- exact candidate allele + final PASS/GT ----+

40 REF molecules -- default -- exact-allele negative control
```

The prior source note reports `max(report_minimum, noise_margin) - noise_margin`: 35/10 gives 25 bp; 35/30 gives 5 bp. It reports that a non-I/D operation flushes the accumulated CIGAR evidence. Thus 60I clears the default predicate, while three 20I pieces separated by `=` do not individually clear it. The fragmented pieces clear the 5-bp predicate under margin30. This is arithmetic for an inspected branch, conditional on prior filters and region intersection. It is not an observed binary setting or whole-pipeline outcome. Other evidence paths, clustering, assembly and genotyping can remove or preserve the apparent contrast.

Margin30 is a whole discovery-setting intervention. Even if it rescues the allele, do not attribute rescue uniquely to that branch or declare universal threshold invariance. It leaves report minimum35 unchanged, but can affect discovery beyond this locus. The REF-only default arm does not establish specificity under margin30. Four arms are sufficient for the stated local question; no fifth arm is required for this initial diagnostic. A later specificity claim would need its own design.

TRsv already supports same-read repeat fragmentation and merging. The inspected notes also establish overlap with native repeat seeding and consensus methods. Do not promote generic fragmentation or merging as new. This diagnostic needs no fresh prior-art campaign to justify its limited information value.

## Fixture constraints and completed-code findings

Freeze the actual 4,000-base reference sequence, including both seeded random flanks, and the 4,060-base truth obtained by inserting 60 A bases before offset1500. Record the sequence hash basis. The truth is an A-run expansion; many insertion coordinates within that run yield the same complete haplotype. Do not require the caller to report offset1500.

For a read spanning reference interval `[s,e)`, the two allowed ALT CIGARs are:

```text
canonical:  (1500-s)= 60I (e-1500)=
fragmented: (1500-s)= 20I 5= 20I 5= 20I (e-1510)=
```

Both consume `e-s` reference bases and `e-s+60` query bases. The two internal matches use A-run bases at offsets1500–1509. Their presence makes the second alignment valid for the same query sequence. With no mismatches or deletions, both have NM60 and MD equal to the number of matched reference bases. Read validity does not imply equal alignment score or natural mapper frequency: fragmentation adds gap opens under many scoring systems.

The completed fixture implements this arithmetic. Starts are300–399; ends are3646–3700. Every read therefore includes at least601 bases of the left random flank and646 of the right random flank. This resolves the concern that reads could span only the insertion site inside the homopolymer. It does not prove that the caller will assemble the 2-kb repeat correctly; the canonical positive control must establish assay suitability.

The validator checks all expected read names, coordinate order, primary flag0, MAPQ60, Q40 qualities, reference dictionary, sample/read group, exact sequences and CIGARs, query/reference consumption, each `=` block against reference, NM/MD and indexed retrieval. It compares serialized SAM fields outside CIGAR between primary arms and requires exactly the20 ALT CIGAR changes. The four-arm protocol must reuse the identical fragmented BAM in arms2 and4. Avoid generating a new molecule set for rescue.

REF-only has40 genuine reference reads. Its query bases, lengths, tags and names necessarily differ from the removed ALT molecules. The fixed-molecule requirement applies to the primary pair and rescue reuse, not to this negative control. All40 negative reads cover the full A run. Its endpoint distribution is not exactly the primary pair's distribution; that is acceptable for the narrow false-allele canary, not evidence of comprehensive matched specificity.

All reads are error-free synthetic sequences with imposed MQ60, Q40 and forward primary flags. Forty reads supply depth to one deterministic software witness. They are not40 independent loci or biological replicates. No significance test, confidence interval for prevalence, or platform-performance estimate follows.

Main's proposed hash correction is scientifically sound. A compressed BAM manifest hash can change across pysam/HTSlib stacks without changing alignment semantics. Freeze the reference sequence SHA independently; retain complete semantic validation and deterministic manifest equality within the same stack. Record actual file hashes for provenance. At read time the test still asserted fixed manifest hash `20f609f41e25a352a4fe4f854de54f7b1e7f46e7626a7758080e188a5a0b26f5`; the described replacement was pending. Do not treat that cross-stack byte assertion as a biological-input requirement. Conversely, removing it without a frozen reference hash would leave the generator and its validator sharing the same unfrozen truth construction. Inspect the completed correction at follow-up; no code change was made by this reviewer.

## Sufficient observation rules; scientific HOLD items

The protocol's whole-reference REF-to-ALT comparison is appropriate. Fix the following rules before accepting results; verify them in the completed observer rather than inferring them from its intended behavior.

1. **Separate the endpoints.** For candidate output and final output, report exact truth-allele presence independently. For final output also report exact allele FILTER, explicit PASS, sample `SYNTH` and GT. Define intended final recovery as an exact truth allele with PASS and heterozygous GT0/1 or1/0, including phased equivalents. An exact PASS1/1 record proves allele presence but fails the intended heterozygous endpoint. A filtered exact allele proves presence but fails PASS recovery. The interpretation table's word “recover” must identify the endpoint being compared.
2. **Validate against independent truth.** Verify contig identity, bounds and every literal REF before applying an allele to the frozen full reference. Require exact equality to the frozen 4,060-base truth. Preserve all records, including wrong alleles, filters, missing GT and unexpected calls. Do not accept size60, proximity, BED overlap or the original offset alone. A bare FILTER`.` does not establish explicit PASS. An empty output after a successful, complete stage is different from a missing or failed output.
3. **Use three observation states.** Exact match found = PRESENT. All records successfully examined, with no truth match and no representation that could conceal it = ABSENT FROM THAT OUTPUT. A symbolic, multiallelic or unparseable representation that remains unresolved = UNRESOLVED for a negative inference. The protocol conservatively leaves multiallelic records unresolved; that is acceptable. A known literal exact match can still establish presence while other records remain unresolved. Counts must retain that uncertainty. Nonmatching literal records alongside unresolved records do not certify truth absence. “Unresolved-only endpoint” must not be implemented as a rule that clears uncertainty merely because some other literal record exists.
4. **Declare the representation unit.** The present literal-record rule tests whether one output record reconstructs the full truth. If no individual record matches but a compatible set of records might jointly encode it, do not call full-haplotype absence without a declared, valid joint reconstruction. Candidate sites-only records do not establish phase across several edits. Either resolve the relevant joint representation or retain UNRESOLVED. This does not demand a general haplotype assembly algorithm for the diagnostic; it bounds the claim when the simple observer cannot decide.
5. **Keep contig and BED claims distinct.** Record assembly BED entries/coverage and contig identities, lengths and relevant alignment metadata. These are supporting observations, not exhaustive causal traces. A local assembled contig need not be4,060 bases. Counts or lengths cannot establish exact haplotype identity. If contig sequence is used to resolve candidate presence, declare its candidate association, covered anchors and reconstruction rule; padding uncovered sequence with reference is not direct evidence that the missing contig sequence was assembled. The current protocol can retain contigs as metadata and rely on exact candidate records, leaving unsupported representations unresolved.
6. **Keep settings fixed and observable.** Run the full miniature reference without debug targeting, with the same ordinary filters and CNV-disabled path in all arms. Confirm resolved discovery settings, including35/10 versus35/30, rather than reporting source defaults as observed settings. No post-outcome change to flanks, repeat length, reads, report threshold, score filters or output matching is allowed inside this experiment.

These are sufficient constraints for this bounded contrast. No stage-causal absence claim is required or supported. The scientific HOLD concerns precise negative-evidence semantics and endpoint interpretation, not an unmet requirement to prove paper-level novelty. Fixture source inspection substantially satisfies the input-control requirements; observer correctness and the announced hash correction remain unverified here.

## Result disposition and stops

| Valid observations | Permitted conclusion |
|---|---|
| Canonical fails exact PASS heterozygous endpoint | Assay suitability not established; stop incomplete without tuning this experiment. |
| REF-only contains the exact expansion, or relevant outputs are unresolved/failed | Control or observation failure prevents a complete invariance conclusion. Preserve observed positives and uncertainty. |
| Both primary arms have exact PASS heterozygous recovery | No loss of the intended final endpoint on this fixture. Reject this local whole-pipeline loss premise. Candidate observations still must be reported separately. |
| Canonical succeeds; fragmented loses exact allele presence; margin30 restores intended recovery | Local representation sensitivity with recovery under an existing setting. No unique causal stage or new rescue method follows. |
| Canonical succeeds; fragmented retains exact allele but loses PASS or heterozygous GT | Sensitivity at the declared final endpoint, not exact-allele disappearance. Candidate presence may independently exclude candidate-output absence. |
| Canonical succeeds; fragmented fails intended recovery; margin30 also fails it | This setting does not restore the intended endpoint here. Distinguish allele absence, filtering and genotype failure; no unique stage cause follows. |

No BED absence, empty contig file or candidate-record absence alone establishes failure of the inspected CIGAR branch. Candidate truth presence can reject absence from that candidate output; it does not reconstruct every upstream event. Stop rules must preserve executed-arm results and mark skipped arms unexecuted. A failed positive control is not a biological null or a permanent rejection of native research.

## Execution boundary and next review

The proposed256MiB and600 named CPU seconds remain UNBOOKED. Their stated totals are proposals, not measured costs or a complete allocation. Historical charges, preservation guards and STOP of the generic released-callset route remain unchanged. The incomplete allocation is not a scientific rejection of this diagnostic; exact command, executable, containment, I/O-pass, CPU-tree and archive review is a separate later boundary if selected. No execution approval is requested or issued here.

Initial scientific disposition remains CONDITIONAL ACCEPT of the four-arm diagnostic, with the narrow HOLD above on result acceptance. Available for completed fixture-correction, observer and protocol follow-up within this review file. Decision-worker selection and broader investment judgment remain outside this owned scope.

## Bounded follow-up: selection and fixture correction

2026-10-09. **ACCEPT the decision to select one bounded diagnostic, the revised scientific endpoint rules, and the fixture hash/semantics correction at source-review level. The observer HOLD remains OPEN.** This supersedes only the initial statement that the hash correction and endpoint wording were pending. The initial snapshot above remains preserved. No native execution, reservation or publication direction is approved.

Read FULL the completed [value decision](/Users/akm/aayushkrm-AlignSSL/repo/docs/research/2026-10-09-native-invariance-value-decision.md), revised [protocol](/Users/akm/aayushkrm-AlignSSL/repo/docs/research/2026-10-09-native-invariance-protocol.md), fixture and tests. Also read the full owned initial review. Did not read the observer, which has not been reported complete. No test or fixture generation was performed. The main-reported result of15 passed,0 skipped in0.40s is not independently reproduced here. Only this owned review was appended; no other file was edited and no installation, network, SSH, genomic input, native run or Git action occurred. Requested Sol6.1/high remains backend-unattested.

| Follow-up read snapshot | Observed SHA256 |
|---|---|
| Completed value decision | `484b11b384b859cedcfbaa38fb8ff3ff76872d78a80f77c6ae144ff9bbd45a95` |
| Revised protocol | `fc25e51999c854280bc8f4cdd777b60263e843fc01c5090874d758cbadcf5f57` |
| Completed fixture | `d26fbfc1199e06d6506f65369e14036bc3936d0ac94a6793a3914f5d2d6c9bd7` |
| Completed tests | `25379f739735d14c939935ce03465206bff8431349fa9ca8b1e47d08cdf564dd` |
| Owned initial review before this append | `f1cbcbd5aa99a611a8f4142aab21c21ccc08cb5f285c9311b661481bc65c4dc2` |

### Selection scrutiny

The decision gives an adequate information-value reason for this one test. It selects a complete caller observation that source arithmetic cannot supply. The canonical control tests whether this difficult synthetic repeat is usable at all. The default pair tests local sensitivity to valid alignment representation; margin30 tests whether an existing setting restores the intended endpoint. Either recovery, failure, or positive-control failure has a declared stopping consequence. This is sufficient for a diagnostic without a paper-level novelty demand.

ACCEPT its restrictions: one fixed fixture, four cases, no tuning or retry after outcomes, and no automatic follow-on campaign. Generic fragmentation/merging prior art remains acknowledged. Existing settings do not become a new method when they rescue this fixture. An unsuccessful rescue does not establish novelty or justify a learned generator. The negative control supplies no margin30 specificity estimate; the absence of a fifth arm remains acceptable within the stated claim.

The known25/5-bp predicate difference remains distinct from whole-pipeline recovery. A change in BED or contig metadata can accompany recovery without proving that the inspected branch was the exclusive cause. Candidate truth presence rules out absence from that output; it does not prove that every subsequent failure has one isolated cause. The decision's accepted-result table must be read with its stated integrity and negative-control conditions, and with the revised protocol's UNRESOLVED rule.

The decision selects the diagnostic, while the revised protocol's opening still says scientific selection is pending. This is a status-label mismatch, not a failure of the scientific contrast. Selection is documented by the completed decision; executable readiness, observer review and launch/account approval remain pending. Preserve the decision's older protocol hash as its read snapshot rather than silently replacing it with the later protocol hash.

### Hash and alignment semantics

The completed test replaces the fixed compressed-manifest hash with reference sequence SHA256
`1e9e223b565b9f0847946d777a5c7fd4f2ba09f076174e4fab96f473156fe9ef`.
The hash basis remains uppercase sequence ASCII bytes, excluding FASTA header and wrapping. Two independently generated fixture directories must still have identical manifest bytes within one software stack. The manifest still records actual artifact sizes/hashes, and validation recomputes them. This correctly separates frozen scientific content from compression-stack provenance. It does not relax the molecules, CIGARs, qualities, tags, reference or index semantics.

One exact implementation limit must carry into launch review: `FROZEN_REFERENCE_SHA256` is asserted in the test, while `validate_fixture()` recomputes its reference/truth from the generator. The validator alone does not compare against that external frozen constant. Therefore a future exact-stack gate must verify the frozen sequence hash, through the pinned test or an explicit preflight comparison, rather than assuming that a successful fixture CLI enforces it. This is a verification requirement, not evidence that the present reference changed. No generated reference bytes were independently hashed by this reviewer.

Static review confirms that the primary-arm comparison still requires equality of every serialized SAM field except CIGAR, exact20 ALT CIGAR changes, valid match blocks, NM/MD, coordinate order and all indexed records. The added mutation cases cover MAPQ, flags, read group, start and name, alongside the prior sequence, quality, NM, MD and CIGAR cases. There are five ordinary tests and ten parameterized mutation cases, consistent with the reported15-test total.

The revised start mutation changes the first sorted ALT000 start from300 to299. This preserves record order for mutant BAM indexing and allows the unchanged validator's start check to reject the mutation. Moving another record below an earlier record could instead fail during index creation before reaching that check. The correction addresses the test setup, and source inspection shows no weakened production start or sorting check. The main's reported initial failed attempt remains a test-development failure, not a native result.

The new parent-link guard rejects symlink ancestors before directory creation, and its test checks that the target receives no output. Existing destination refusal, artifact file-set checks, per-file regular-file checks, indexes and aggregate fixture-size validation remain present. These improve fixture handling; they do not establish process containment, runtime output caps or a complete I/O account for native execution.

### Endpoint correction and remaining HOLD

| Initial concern | Follow-up disposition |
|---|---|
| Separate allele presence, PASS and genotype | RESOLVED in protocol wording: independent counts plus a joint exact+explicit-PASS+heterozygous count. Verify implementation later. |
| Treat bare FILTER`.` as PASS | RESOLVED in protocol wording: explicit PASS required. Verify implementation later. |
| Treat unresolved records as negatives | RESOLVED in protocol wording: PRESENT/ABSENT/UNRESOLVED; known exact positives remain positive with other unresolved records. Verify implementation later. |
| Several nonmatching edits could encode the full expansion | RESOLVED in protocol wording: retain UNRESOLVED unless valid joint reconstruction resolves them; no phase inferred from sites-only records. Verify implementation later. |
| Source defaults substituted for observed settings | RESOLVED in protocol wording: read bounded resolved discovery settings35/10 or35/30. Verify implementation and actual output later. |
| Fixed compressed-BAM hash across software stacks | RESOLVED at fixture/test source-review level; exact-stack frozen-reference verification remains a launch gate. |
| Completed observer correctness | OPEN: observer deliberately not inspected in this follow-up. |

For the REF-only control, zero exact single-record counts alone is insufficient if relevant unresolved representations remain in either candidate or final output. “Control passes” must mean resolved absence under the revised three-state rule. The completed value decision's zero-exact-count wording and its “unresolved-only” stop language do not override that stronger rule. This qualification also governs mixtures of nonmatching literal records and unresolved records. A resolved exact positive can still be retained when other representations are unresolved; absence cannot.

The observer review must check that the joint endpoint belongs to the same exact allele record and the intended sample. Separate counts cannot manufacture a joint success from a PASS allele with wrong GT plus another filtered allele with heterozygous GT. It must also preserve candidate-versus-final presence, unresolved joint representations, missing versus empty output, all filters and genotypes, and BED/contig metadata limits. These checks are stated requirements, not claims about unseen worker code.

The revised protocol supplies the sufficient scientific rules for the selected contrast. Their implementation remains unverified, so the result-acceptance HOLD stays OPEN. The proposed256MiB and600 named CPU seconds remain UNBOOKED; the incomplete account, exact commands, binary verification, process containment and archive limits await a separate bounded launch review. No resource allocation or native execution authority follows from accepting this scientific selection. The historical STOP, all prior charges/guards and H_R UNTESTED status remain unchanged.

## Completed observer review and in-turn integration correction

2026-10-09. **ACCEPT the joint exact+explicit-PASS+heterozygous implementation and the corrected native-format/metadata controls. HOLD negative-result integration: the joint-edit uncertainty guard still misses valid padded representations.** Scientific selection remains accepted. This is code/observation review before integration, not paper acceptance, native execution approval or a reservation.

Read FULL the completed [observer](/Users/akm/aayushkrm-AlignSSL/repo/analysis/observe_native_fixture.py) and [tests](/Users/akm/aayushkrm-AlignSSL/repo/tests/test_observe_native_fixture.py). The first completed snapshot had observer SHA256 `73623453a3665ff54a6ebf3334b710f74f85219ecf621dc516b2ded27d3721bc` and tests SHA256 `ea0b9088d752926f278512f16fad549c4f29417d4a1cdfdebbd2864352551834`. After main reported its integration corrections complete, read both files FULL again. No partial file was read. The current protocol hash remains `fc25e51999c854280bc8f4cdd777b60263e843fc01c5090874d758cbadcf5f57`; the revised scientific rules reviewed above still govern.

| Corrected read snapshot | Observed SHA256 |
|---|---|
| Observer | `e4243b92ea0391276a2f8a5ee30b3a212794b70ac97c3f4aec4f04ab0ce36fbd` |
| Observer tests | `87b0d1cab09efdd470e6b2e0c8302c66badf5caa013d9da1bd64a275028a72bf` |
| Owned review before this append | `9666dd90895c9b10c9d172a6e94ba9d05b03608f0682bfa2f783165f8729de30` |

The worker's14-test result and main's corrected combined32 passed,0 skipped in0.65s are reported evidence, not reviewer reruns. Current source contains17 observer tests; together with the15 fixture cases this is consistent with32. No native caller, test, generated input, installation, network, SSH, genomic read or Git action occurred in this review. Only the owned note was appended. The initial98-line snapshot was independently checked after the preceding append and retained its original hash.

### Accepted observation checks

The literal-allele comparator validates REF and applies its replacement to the frozen full4,000-base reference, then requires exact equality with the4,060-base truth. The observer independently checks the frozen reference sequence hash at runtime and validates the exact truth schema. This supplies an additional reference guard beyond the fixture validator's generator-based check. It does not replace pre-launch fixture/record validation.

For an exact, single-ALT record in final output, `filter_names == ("PASS",)` defines PASS. GT must be `(0,1)` or `(1,0)` in the sole sample `SYNTH`; either phasing state is counted. `pass_heterozygous` increments only inside that same exact record's qualifying GT branch. ACCEPT this joint implementation. The test with a PASS0/0 record, a LowQual1|0 record and a bare-dot0/1 record correctly expects zero joint recoveries despite separate positive counts. A separate test expects recovery for PASS1|0. Candidate sites-only output is accepted independently of final genotype requirements.

Symbolic, multiallelic, off-contig, invalid-REF and other unresolved records contribute reasons for uncertainty. An exact literal positive takes precedence over those reasons and establishes PRESENT. This is appropriate for positive allele presence, without claiming that every unresolved allele was interpreted. Two simple nonmatching literal edits wholly inside the A-run produce UNRESOLVED in the existing test. That control is useful but does not cover the representation boundary below.

| Issue in first completed snapshot | Corrected source/test disposition |
|---|---|
| Compressed native final VCF was rejected as the wrong file type | CLOSED: VCF.gz is now accepted; a BGZF `genotyped.sv.vcf.gz` test expects joint recovery. Plain VCF and BCF remain supported. |
| BAM summary contained only reference-header lengths | CLOSED for bounded metadata: unique nonmissing qname count and query-length distribution per alignment are now reported, separately from reference lengths. They remain metadata, not exact contig-sequence recovery. |
| Empty test row lists selected defaults rather than an empty callset | CLOSED: helper distinguishes None from an empty list; header-only candidate/final files return resolved single-record absence, while a missing candidate file errors without a report. |
| Changed-input test attempted a no-op1200-to1201 replacement | CLOSED: default candidate position900 now changes to901, and the test asserts that bytes differ before writing them. |

Query lengths are explicitly per alignment; supplementary records can repeat a contig and hard-clipped records can omit sequence. Do not present that histogram as unique complete assembled-haplotype lengths. The unique-name count and honest field names are sufficient bounded metadata for the current diagnostic. BED currently reports row counts and whether offset1500 is covered. That does not measure coverage of the entire repeat or certify allele assembly; any broader repeat-coverage statement needs separate bounded observation.

### Remaining scientific HOLD: compatible padded joint edits

At [observer line370](/Users/akm/aayushkrm-AlignSSL/repo/analysis/observe_native_fixture.py:370), the uncertainty counter includes a nonmatching literal record only when its full REF span lies within `start >= 999` and `ref_end <= 3000`. At [line419](/Users/akm/aayushkrm-AlignSSL/repo/analysis/observe_native_fixture.py:419), at least two such counted records are required to add the joint-edit unresolved reason. Valid REF/ALT records can include unchanged reference padding outside those bounds. This means two compatible edits can jointly encode the expansion while only one qualifies for the counter.

Concrete source-derived counterexample, using `R` for the frozen reference and zero-based slices:

| Record | VCF POS | REF | ALT | Added A bases |
|---|---:|---|---|---:|
| Padded edit crossing the left boundary | 999 | `R[998:1002]` | `R[998:1001] + A*20 + R[1001:1002]` | 20 |
| Ordinary insertion inside the run | 1500 | `A` | `A*41` | 40 |

Both REF strings are valid. The padded first record inserts20 A bases at reference offset1001 inside the A-run, while preserving the two flank bases and both matched A bases in its REF span. The second inserts40 A bases at offset1500. Their REF spans do not overlap. Applied compatibly, the two edits yield the exact frozen expansion: the same flanks and2,060 A bases. Neither individual record yields the full truth.

Under the current code, the first start is998, so it is excluded from the repeat-literal counter. The second counts once. With no other unresolved record, exact count is zero, the repeat counter is1, and output state becomes ABSENT_FROM_OUTPUT rather than the protocol-required UNRESOLVED. This is a static counterexample; it was not executed by this reviewer. Unknown phase in candidate output is precisely why the possible joint representation must remain unresolved.

`full_haplotype_absence_claim=False` correctly limits the report, but does not close this gap: a downstream controller could use ABSENT_FROM_OUTPUT to pass the REF-only negative control or declare fragmented exact-allele loss. The single-record absence statement is true; the missing joint-uncertainty flag violates the stronger integration rule. Do not promote that state to a resolved full-allele negative.

Sufficient correction: conservatively mark two or more nonmatching literal records on chrSynthetic as UNRESOLVED whenever no exact single-record positive exists, without relying on their padded REF spans being wholly inside the run. This may overflag harmless combinations, which is acceptable for this finite diagnostic. Alternatively use a validated representation-aware rule that cannot miss the padded case. No general phasing engine or extra native arm is required. Add a regression for the two valid records above, in candidate and final observation paths, and retain positive precedence when an exact record also exists. Include padding across the right repeat boundary if retaining any boundary-specific heuristic. The reviewer owns no implementation file and made no code changes.

### Integration and execution boundary

The observer's `status=complete` and exit0 mean its six inputs were read and parsed with matching before/after snapshots and hashes. They do not mean canonical recovery, negative-control success or experiment completion. Integration must explicitly check each required endpoint/state, retain uncertainty, distinguish missing/empty artifacts and apply the predeclared stops. Raw artifacts and bounded record inspection remain needed for detailed allele/GT evidence; aggregate reports are not a rejected-signal trace.

`discover.settings.json` is not among the observer's six inputs. Its resolved35/10 and35/30 checks therefore remain a separate required integration step under protocol line99. Bounded parser copies and posthash passes also have costs: native-format payloads are materialized in temporary files, read by pysam, and original inputs are hashed again. The8-MiB per-file,16-MiB aggregate and64-KiB report caps do not alone form the complete launch account or limit decompressed parser memory/CPU. Exact pass accounting and process containment remain for launch review, not new scientific rejection criteria.

Disposition: observer positivity/joint-endpoint checks and reported integration corrections ACCEPTED at source-review level; negative-result integration HOLD remains OPEN for the padded joint-edit case. The selected diagnostic is still scientifically justified within its fixed limits. No native execution or booking is approved;256MiB/600 named CPU seconds remain UNBOOKED. Earlier selection, fixture review, historical snapshots, STOP, charges and guards are preserved.

## Narrow joint-edit correction: code/observation HOLD CLOSED

2026-10-09. **ACCEPT the exact correction and CLOSE the padded joint-edit code/observation HOLD.** This supersedes the preceding OPEN disposition for that defect only. All earlier snapshots and findings remain preserved. Execution-account and launch review remain pending; no native result, reservation or execution approval is supplied.

Read FULL the current observer and its tests. Independently measured hashes match main's stated pins:

| Read snapshot | Observed SHA256 |
|---|---|
| Observer | `22b5294b3865c7bd22121d0b136dc227892212aad05f54bcb0caaabbdeb4d9a9` |
| Observer tests | `44182c5ccb9d30579c2e859efbf65247e9365d675d5592c09ebdc17d3654e5e9` |
| Owned review before this append | `b5b6139e9880317283c53a7625b69298f7ba99fa8efbff8b1f0c4e8fd262dd06` |

The observer now uses the total `non_equivalent_literal_records` count to add `multiple_non_equivalent_literal_records_on_chrSynthetic` when that count is at least2. These records have already passed chrSynthetic, literal-allele and REF validation. Neither repeat boundary nor padded REF span controls the uncertainty decision. The inside-A counter remains metadata only. An exact single-record positive still takes precedence and yields PRESENT. This implements the sufficient conservative correction requested above. It can leave harmless multiple-edit outputs unresolved, but cannot use that guard to manufacture recovery or certify a false negative.

The new parameterized regression covers candidate/final output, each without/with an exact positive: four cases. It constructs the padded20-A and ordinary40-A records from the frozen reference and first asserts that their two nonoverlapping replacements jointly yield the complete truth. It then checks zero/one exact records, UNRESOLVED/PRESENT respectively, retention of the two-record uncertainty reason, and no full-haplotype absence claim. Candidate sites-only and final SYNTH0/1 paths both reach the guard. The known-positive final case also reaches the existing joint PASS/heterozygous branch by source inspection.

| Relevant literal observations | Required state now implemented |
|---|---|
| Padded20-A plus ordinary40-A; neither individually exact | UNRESOLVED |
| Same two records plus a known exact literal allele | PRESENT, with uncertainty reason retained for the other records |

Integration must use the observation state and uncertainty reasons. The `unresolved_records` counter counts individually unresolved records; it can be zero while a joint-edit uncertainty reason makes the output UNRESOLVED. Checking only that counter or only the exact-record count would discard the correction. This is the existing three-state integration contract, not a new HOLD. `status=complete` continues to mean successful parsing, not successful negative control or experiment completion.

Main reports39 tests passed,0 skipped in0.69s, including3 README tests. That is consistent with the previously reviewed15 fixture cases,17 observer cases, these4 regressions and3 reported README cases. This reviewer did not run tests or inspect the README tests. Acceptance here rests on the narrow source/regression review and matching file hashes, not an independent rerun or native-input compatibility claim.

Only this owned note was appended. No implementation file, test, protocol or ledger was changed by the reviewer; no test execution, fixture generation, installation, native caller, network, SSH, genomic input or Git action occurred. Requested maintained Sol6.1/high remains backend-unattested. The observer code/observation HOLD is now CLOSED at the pinned source-review level. Separate resolved-settings integration, exact-stack verification, complete byte/CPU accounting, containment, commands and archive review remain required before a launch disposition.256MiB and600 named CPU seconds remain UNBOOKED; historical STOP, charges and guards remain unchanged.

## Exact launch review: conditional ACCEPT of the pinned one-attempt bundle

2026-10-09. **CONDITIONAL ACCEPT of this exact bounded launch, including its scientific stops, code, literal submission and complete named account.** No outstanding scientific/code HOLD was found in the final reviewed snapshot. Booking, fresh-root/live-state checks, remote hash verification and exact-stack/runtime gates remain conditions. This review does not perform or attest those steps. The candidate remains UNBOOKED, UNSTAGED and UNEXECUTED in the evidence read here.

Read FULL the execution note, runner, settings validator, launcher/settings/integrity tests, both shell scripts, and then the final corrected runner, execution note, protocol, bundle manifest, literal submission file and reservation candidate. Existing fixture/observer source pins match their previously reviewed versions. All12 manifest entries were checked against their actual local source mappings, with12 OK results. No test or native command was executed; main's70 passed,0 skipped in0.79s is reported local evidence. The five selected suites contain15 fixture,21 observer,8 launcher,15 settings and11 integrity cases, totaling70. Requested maintained Sol6.1/high remains backend-unattested.

| Final execution identity | Independently observed SHA256 |
|---|---|
| `bundle.sha256` | `5fb12fce0d6a5a43a170827af88405214af59c98f99718a14733dc1503c3cfad` |
| Literal `submission_command.txt` | `cf3c89a8e773c74fce34d9d430fc6945092525d1a4d73aab0344ac487f1049f9` |
| Candidate `reservation.json` | `fc776c7bc7001b762ba040f451d4da9a96c13c194433e0a29315c72666ca513f` |
| Final execution note | `6d008e2bf8f1dcafd81bc9ade40e9a5e1aa722e1b3e3983137f9fa11954675d2` |
| Final runner | `2a6ae0fc6c04075702c021bb7860fa89e7c88ae0676048bb124286bf18d97867` |
| Settings validator | `2c32586e019ce3d5f1de36c10bffeb3a894f50ac18962c65019f8fc70899d556` |
| Outer wrapper | `acdbc90680fd02e0712f4dc25f0144e71b0c9dd830cd5bae69dde095c597a9ff` |
| Corrected payload wrapper | `928dca3f02c26d0b379f2533efafd840a40a89342558a686abfb3db1ef0cf1a5` |
| Staged protocol source | `d4a0f851bd4536e5a3b6275dd8a11c2bc5832af9c26672b9b8fc8bfa58c6953e` |
| Owned review before this append | `070dd599caf9f83fd90df9996b94296041cfc22e5fd2b211bd4f507a1db47787` |

The manifest maps its nine `code/analysis` and `code/tests` entries to the corresponding repository `analysis` and `tests` files; its two shell entries map to the dated local launch directory; `protocol.md` maps to the current research protocol. The fixture and observer retain hashes `d26fbfc1199e06d6506f65369e14036bc3936d0ac94a6793a3914f5d2d6c9bd7` and `22b5294b3865c7bd22121d0b136dc227892212aad05f54bcb0caaabbdeb4d9a9`. The actual manifest, not an inferred list, controls remote verification. The separate submission and reservation hashes above bind the inspected operational/account candidates; they are not additional manifest entries.

### Scientific gates and observed settings

ACCEPT the common `--cov-regex '^chrSynthetic$'` correction before outcomes. Main reports a full pinned discover-CLI read showing flat snake_case serialization and a mandatory header regex match even with CNV disabled. This reviewer did not fetch that source. The same regex is used in all four discovery commands, so it changes input acceptance without changing the reference, molecules, allele truth or primary contrast. No outcome-driven tuning occurred in the evidence inspected here.

The settings validator reads and posthashes a stable, bounded regular file; rejects links, duplicate JSON keys, nonstandard numbers and imprecise types; checks reporting minimum35, noise margin10/30, the common regex, CNV disabled, no fast mode, ordinary identity/MAPQ/QUAL and no target-cluster or external annotation setting; and checks exact canonicalized input paths and output directory. It returns all serialized fields. The runner compares every returned field across arms except BAM filename, output directory and the intended margin. ACCEPT that observed-settings contract; no default is substituted for actual saved settings. This is not proof that the binary will emit the expected schema: a mismatch stops the attempt.

The controller uses `single_record_output_state`, not individually unresolved-record counts. UNRESOLVED in candidate or final output stops incomplete. Canonical requires at least one same-record exact+explicit-PASS+heterozygous recovery; failure stops all later arms. REF-only requires ABSENT_FROM_OUTPUT in both candidate and final, even if an exact false allele is filtered or reference-genotyped. Known exact positives remain visible with uncertainty about other records. No candidate/BED absence is assigned a unique causal stage.

The full miniature reference and fixed arm order are preserved. Rescue reuses `fragmented.bam`; only its discovery noise margin differs. CNV is disabled in both stages, with one thread and no target/debug/fast mode. Every discover/joint-call command is claimed and logged before execution. Fixture validation follows each native stage, and final validation follows all arms. The observer reads frozen copies and posthashes its original inputs; settings have their own two-read check. Missing files, parser failures, changed bytes, threshold drift or invalid controls cannot become a biological negative. The new integrity tests exercise damaged BGZF/BAM, malformed VCF tails, strict truth types and missing/wrong GT. Local passing tests do not establish native recovery or exact-stack compatibility.

### Claims, version correction and containment

The final literal submission file fixes a concrete issue in the earlier execution-note shape. That shape used only `set -C`; failed exclusive claim creation could otherwise be followed by `sbatch`. The reviewed literal file starts with `set -euo pipefail` and `set -C`, writes the experiment ID and actual bundle hash to the exclusive submission claim, then issues exactly one `sbatch`. Claim-write failure now terminates that block. Unknown acknowledgement consumes the claim; inspect the same job/root rather than submit again. Use this pinned literal file, not the preserved placeholder example in the execution note.

The outer wrapper verifies the supplied manifest hash and all manifest entries before creating its exclusive timed-payload claim. The payload verifies the bundle after controls and after the runner. The fixed native root and fresh fixture/arm directories, exclusive JSON claims and logs, and one submission/control slot support the no-replay rule. Any change to the accepted bundle needs a new hash and review of the material change before staging or launch; no failed-arm replay is permitted inside this attempt.

The first wrapper copied local pytest9.1.1 into the cluster assertion. Main's09:52:20+07 metadata preflight reports Python3.10.20, pysam0.24.0, HTSlib1.23.1 and pytest8.4.2, with taskset and GNU time available. The corrected payload asserts exactly those versions and requires70 passing controls without skips before fixture creation or asset acquisition. Its original hash was `a7fa228a0e7fad2f0d3b543fdfa9ab65611f34b8e816e7a494fecbfdc3d81587`; the corrected hash is pinned above. This is a preserved setup-draft correction before staging/outcomes, not an executed caller failure or an environment upgrade. Exact-stack test success remains a runtime gate.

The tool acquisition is restricted to the pinned author v2.2.1 asset, inside the timed payload after controls. The runner checks its exact3,616,061-byte length, streaming SHA256 and independently re-read stored SHA256 before extraction. Extraction permits at most64 safe regular/directory members and16MiB declared expansion, refuses absolute/traversal/link/special entries, and writes only the sole `sawfish` member exclusively. It records the extracted binary hash and requires measured version text `sawfish 2.2.1`. Source-tag correspondence alone is not binary attestation; these runtime gates supply the required observations or stop incomplete. This scoped isolated acquisition is part of the already authorized workflow, not a new sidebar or permission request.

Taskset chooses one allowed CPU and binds the timed payload and inherited children. GNU time measures the waited tree once. Timeout480s with5s kill grace is the tree wall bound; subprocess native/version calls have120s timeouts. Inherited per-process CPU soft300/hard450 seconds and4GiB virtual address-space limits are additional limits, not independent tree-CPU totals. Slurm requests one task/CPU,4GiB and9 minutes on amd_256M. No GPU or unrelated job is involved. The600-second named allowance leaves room beyond the one-CPU timed tree for bounded setup/collection. Retain the outer timing even on failure and avoid adding inner or Slurm CPU again as a second charge for the same work.

### Complete named account and output/archive limits

ACCEPT the prospective allocation as a complete **named conservative allowance** for this one attempt, including failed paths. It is not a measured physical-I/O bound or a validated native memory/runtime forecast.

| Component | MiB |
|---|---:|
| Pinned asset transfer, stored hash, extraction and verification | 64 |
| Code staging, exact-stack controls and test artifacts | 32 |
| Eight native-command opaque allowance | 96 |
| Fixture/settings checks and explicit output writes, reads, parser copies and posthashes | 24 |
| Raw archive source hash, transfer and destination hash | 24 |
| Failure, metadata and timing margin | 16 |
| Full retained charge on booking | 256 |

The six components total268,435,456 bytes. Prior40,235,307,915 plus that charge is40,503,743,371, below68,719,476,736. Prior measured named CPU556.722707 plus the600-second allowance is1,156.722707, below7,200. Reservation status is explicitly UNBOOKED. Book the full byte charge before root creation/staging, retain it on every setup/control/native failure, and preserve every old charge. Do not transfer the old unbooked screen margin. Use actual measured CPU for the named timing account after completion; do not relabel the600-second allowance as observed consumption.

The64KiB launch fixture cap bounds repeated fixture checks. Control artifacts have a32MiB tree postcheck, including the approximately24MiB oversized-input fixtures. Intentional test links are counted without following them only in that control-tree call; native trees reject links. Native commands inherit a1MiB per-file limit; each arm has a1MiB/64-file tree postcheck after discover, joint-call and observation. Successful command logs now have a64KiB postcheck. Four completed arms therefore bound their combined trees at4MiB; the named five explicit output passes use at most20MiB, leaving the declared4MiB fixture/settings/check margin in that component. The selected raw archive cap is8MiB; its source hash, transfer and destination hash fit the24MiB component.

These tree/log checks are postchecks. They do not prevent temporary aggregate growth, and the successful-log check is not reached when a command itself fails. Keep that limit explicit: if a failed/incomplete root cannot be collected under the archive cap, preserve its raw evidence remotely, mark collection incomplete and stop rather than silently trim scientific outputs or enlarge the account. Do not present the8MiB archive cap as a guarantee that every possible failure fits it. Collection must check exact selected paths, regular-file types, size and aggregate cap before transfer, then require matching source/destination manifests. Assets, executable and control fixtures are excluded from scientific-result archival by the declared design, not based on allele outcomes.

### Exact conditional disposition

| Condition | Review disposition |
|---|---|
| Scientific control/stops and observer STATES | ACCEPT at the pinned code level |
| Flat resolved settings and common chromosome regex | ACCEPT; validate actual output at runtime |
|12 local bundle mappings and literal fail-closed submission | VERIFIED/ACCEPT |
|256MiB/600 named CPU complete prospective account | ACCEPT as a named allowance; still UNBOOKED |
| Fresh/live setup, booked ledger, staged remote pins | Must pass before the single submission; not observed by this reviewer |
| Exact-stack70 controls, asset integrity/version, output caps and raw result review | Runtime/collection gates; not yet observed |

CONDITIONAL ACCEPT permits the main's already authorized normal workflow to book, stage and submit this one exact diagnostic once the stated pre-submit gates pass. It grants no retry, threshold sweep, changed molecule set, new method, real-data campaign or major-result acceptance. No additional human permission is required by this review. Review the actual raw outcomes before any scientific conclusion, and preserve an incomplete attempt as incomplete.

Only this owned review was appended. No ledger was booked, no root staged, no dependency or asset acquired, and no tests, native execution, network, SSH, genomic input or Git action occurred by this reviewer. The broader publication objective remains unmet; H_R remains UNTESTED and the generic released-callset STOP remains in force. Earlier review snapshots, charges and guards are preserved.

## Actual attempt01: raw setup failure and account ACCEPTED

2026-10-09. **ACCEPT attempt01 as CLOSED INCOMPLETE: setup path-alias failure before the diagnostic fixture or native caller. ACCEPT the retained byte charge and single outer CPU charge.** This is acceptance of the documented failure and account, not a native allele result, biological null or approval of a replacement. Attempt01 remains closed with no replay or selective continuation.

Read the complete [result01 note](/Users/akm/aayushkrm-AlignSSL/repo/docs/research/2026-10-09-native-invariance-result01.md), all14 payload files in the [local raw archive](/Users/akm/aayushkrm-AlignSSL/repo/results/data_audits/native_invariance/2026-10-09/raw01/archive.sha256), its checksum manifest, and the complete current live reservation journal. Read the current PROGRESS opening for consistency only. All14 payload checksums independently passed. Directory inspection shows15 regular files including the checksum manifest; byte counting confirms16,696 payload bytes plus1,175 checksum bytes, totaling17,871. No replacement code was inspected, and no test, native command, network, SSH, installation, genomic input or Git action occurred. Only this owned review was appended. Requested maintained Sol6.1/high remains backend-unattested.

| Evidence snapshot | Independently observed SHA256 |
|---|---|
| Raw archive checksum manifest | `634822693a0e0aba7dd75b1b6ab3a542b73c48381776e2e3d55236a1ed0b16e0` |
| Frozen staged reservation in raw01 | `f8906fb0e99bb88b9dd329ce6e9a3b105b82aef8af91e0ad10cf5102d93ccfd0` |
| Current live reservation journal | `2de94f34ed696e85cf45eb51121e7de37408f15deb575c79827b1d0a818feb2f` |
| Result01 note | `c253e8793537dcf94b27330651b44228025f9edbf8f23e4fb687afae41516d3f` |
| Owned review before this append | `d7ff68681882702dd611e75820144a831ebe86556962728a54cfe18d30850b5b` |

### Raw observations and inference boundary

The submission claim contains the exact attempt01 ID and accepted bundle hash `5fb12fce0d6a5a43a170827af88405214af59c98f99718a14733dc1503c3cfad`; the archived literal submission hash remains `cf3c89a8e773c74fce34d9d430fc6945092525d1a4d73aab0344ac487f1049f9`. Outer and payload claims are present. Slurm stdout records initial manifest/hash checks; launch stdout records all12 bundle entries OK after controls. The archived manifest matches the reviewed12-entry bundle.

Controls stdout lists all70 PASSED cases and ends `70 passed in 2.58s`, without skipped cases. Launch stdout records the exact stack Python3.10.20/pysam0.24.0/HTSlib1.23.1/pytest8.4.2 and control-tree size25,894,309 bytes, below33,554,432. Captured missing-index messages arise in the sequential temporary BCF/VCF parsing controls; the CRC error is inside the deliberate damaged-BAM rejection test. They are not the cause of this attempt's setup failure. Empty controls/Slurm stderr files are preserved as actual zero-byte files, not missing outputs.

The complete launch traceback reaches `run -> create_fixture -> _new_output_directory -> _require`, ending `ValueError: output directory ancestors must not be links`. `failure.json` records the same reason and INCOMPLETE status. In the previously pinned source, that ancestor check precedes directory creation, and `install_tool()` follows fixture creation and validation. Thus the intended diagnostic fixture was not created and tool acquisition/version/discover/joint-call were not reached. The controls did create their own unit-test fixtures; “no fixture” must mean the intended native-input fixture, not absence of all synthetic test artifacts.

The traceback's source paths use `/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922`, while the accepted launcher root/claim uses the logical `/scratch/igorno-alignssl_restart_20260922`. This is consistent with the guard encountering a workspace alias. Main's10:11:35+07 `readlink -f` observation explicitly maps that logical workspace to the physical path; this reviewer did not repeat the remote filesystem check. The evidence supports a filesystem compatibility failure between the literal logical root and the fixture's ancestor policy. It supplies no candidate sequence, native FILTER/GT, recovery matrix, threshold-rescue outcome or native compatibility result.

Job1604208, scheduler FAILED1:0 and00:00:05 elapsed are recorded in the live journal/result note. The archived timer independently records exit1 and4.52 wall seconds, consistent with the reported scheduler duration. The archived Slurm log does not itself contain a scheduler accounting row or job ID, so those scheduler identity/status facts remain main-reported, not an independent live Slurm query. Similarly, main reports post-failure all12 staged hashes still matching; the archived raw logs directly show checks before the failing fixture call, not a separate post-failure verification command. Preserve that distinction without weakening the supported setup-failure conclusion.

### Frozen booking versus live journal

The frozen staged reservation is `RESERVED_BEFORE_STAGING_PENDING_RUNTIME_GATES`, booked at03:03:09 UTC, with the accepted bundle, prior retained40,235,307,915 bytes, full new268,435,456 bytes and prospective40,503,743,371 bytes. The current live journal keeps those values and the staged-reservation hash, then adds submission, failure, timing, archive and closure observations. The different reservation hashes reflect preserved pre-run and post-run states; they are not evidence of corruption. Their common execution/account fields agree. Booking/root/staging chronology is journal-reported; local hashes authenticate the inspected snapshots, not the original remote clock events independently.

| Account observation | Accepted value |
|---|---:|
| Full new retained byte charge | 268,435,456 |
| Cumulative retained bytes | 40,503,743,371 |
| Outer user CPU | 1.00 seconds |
| Outer system CPU | 1.07 seconds |
| CPU charged once for the timed tree | 2.07 seconds |
| Cumulative measured named CPU | 558.792707 seconds |
| Outer wall time / maximum RSS | 4.52 seconds /55,120KiB |

The CPU arithmetic is556.722707 +1.00 +1.07 =558.792707. Test elapsed2.58s is a nested wall duration, not another CPU charge; scheduler accounting is not added again. The600-second reservation was an allowance, not600 seconds consumed. The complete256MiB byte charge remains retained despite unused native/asset slots. The raw archive fits its8MiB cap by a wide margin. GNU time filesystem counters are not used to replace the named allowance or claim complete measured physical I/O.

The live journal also preserves an initial failed archive transport with no file, followed by successful transfer and matching local hashes. This is reported collection history, not a native replay or justification for refunding any charge. Original raw claims, failures and staged reservation remain intact.

### Closure and replacement boundary

ACCEPT the result01 note's incomplete disposition and its account. Seventy controls passed on the actual cluster stack, but the whole-input native assay never began. The selected scientific question remains untested by this attempt; H_R and publication readiness are unaffected.

Attempt01's consumed claims and closed root must not be reused. This review does not approve attempt02, a new reservation, path-resolution code or new submission. Main's plan to preserve the exact01 code/history before a separately reviewed physical-path replacement is consistent with reproducibility, but the commit was not checked and no Git action was authorized to this reviewer. Keep the fixture guard and fixed scientific inputs; assess any concrete replacement under its own ID, pins, root checks and full account. Earlier reviews, all charges, guards and the released-callset STOP remain preserved.

## Fresh replacement02: exact conditional ACCEPT

2026-10-09. **CONDITIONAL ACCEPT of the separately pinned replacement02, its root-resolution correction, literal single submission and fresh256MiB/600 named CPU allowance. No concrete scientific/code HOLD remains in this snapshot.** This supersedes only the preceding absence of attempt02 approval. Attempt01 stays CLOSED INCOMPLETE, with no replay, refund or reuse of unused command slots. Replacement02 remains UNBOOKED, UNSTAGED and UNEXECUTED at this review.

Read FULL the [replacement02 note](/Users/akm/aayushkrm-AlignSSL/repo/docs/research/2026-10-09-native-invariance-replacement02.md), common runner, new root tests, both replacement wrappers,13-entry manifest, reservation and literal submission file. Re-read the complete attempt01 result note and live journal for cumulative-account continuity. Independently checked all13 manifest entries against their actual local source mappings:13 OK. No tests, shell syntax checks, native commands, booking, staging, installation, network, SSH, genomic input or Git operation were performed by this reviewer. Only this owned note was appended. Requested Sol6.1/high remains backend-unattested.

| Reviewed replacement snapshot | Independently observed SHA256 |
|---|---|
| Replacement02 note | `b6557135417f4333e7e2cbd394d24fddfa083c508c681bfa658f1016c21d4ded` |
| Physical-root runner | `d41f3f2784cf9ff70d1dd77f679577155a79397d49b9c6942da0600ef7808f8a` |
| New root tests | `ed09fc1d17fce431e8709d16841f573f8d287f4e61c864d4a50693a40a8f7b28` |
|13-entry bundle manifest | `9941bcff343013e9e231135d89498a8720e52c45bfc90a9642a9151a3185c460` |
| Outer wrapper | `b74ae514cc75d60eb2017c712533f160589375e1920e19d9aa8f67dfbcf0e278` |
| Payload wrapper | `584ab29db870da82b9b4402009430cb9276306eccc8ab08c3a7fe76faa4cabd7` |
| UNBOOKED reservation candidate | `18441b8c0f67b549f44706ebdb9b6dfe9f72a658b3fc8612715d25cd93845457` |
| Literal submission file | `c7d070657cce0bbb2b063f3ee936e978108a80cd32cd6775045634f478f318ff` |
| Owned review before this append | `d0d0269e345973f6d789f3093624887318c03de89ab1d38956213f37b753b633` |

Main reports that exact01 source, wrappers and all14 raw payload files were preserved and pushed in commit `ea7f2fb48c2f6d43b762993ce7b8d4ba1c85c6d1`, with matching remote hash. That commit/push remains main-reported; this reviewer obeyed the no-Git boundary. The prior raw checksum verification and retained charge were independently reviewed above. The fresh replacement does not amend that failed outcome.

### Narrow path correction and controls

The runner's ID is now `native-cigar-invariance-20261009-02`. `resolve_experiment_root()` allows exactly its logical root under `/scratch/igorno-alignssl_restart_20260922` or its pinned physical root under `/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922`. It requires an existing directory and rejects a symlink experiment leaf before resolving. Strict resolution must equal the exact pinned physical leaf; any destination drift or linked spelling of the pinned physical path fails. The returned physical root is used for the payload claim, fixture, tool, arms, settings and observations. The claim records both supplied and resolved paths. Failure reporting resolves and validates the root again before writing `failure.json`, avoiding a fallback write into an unapproved destination.

This corrects the observed setup incompatibility without weakening `create_fixture()` or its ancestor guard. The wrappers still enter the approved logical workspace and place their wrapper/control files there; those paths name the same managed physical workspace. Scientific/native artifacts are built from the validated physical root. Before staging, recheck that the logical workspace resolves to that same pinned physical workspace, that both02 root spellings are absent and that the new leaf is created as a real directory. The helper does not replace those pre-staging checks.

The eight new controls comprise logical and physical acceptance, allowed-logical-spelling redirection rejection, linked leaf rejection, missing leaf rejection, aliased physical spelling rejection, unexpected relative/parent path rejection, and actual fixture creation through the resolved path while logical-alias creation still fails the unchanged factory guard. Main's redirect strengthening is meaningful: it changes the allowed logical spelling's destination and reaches the trusted-destination check, rather than merely submitting a disallowed name. The factory test checks creation and a manifest on the physical path. This is proportional evidence for the specific filesystem correction; no new scientific direction or model-max decision is needed.

Main reports78 passed,0 skipped in0.94s on its existing workspace environment and passing shell syntax. These are not reviewer reruns. The original70 controls plus8 root cases equal78. Payload startup still verifies the actual cluster Python3.10.20/pysam0.24.0/HTSlib1.23.1/pytest8.4.2 and now requires78 passes without skips. The factory regression uses `importorskip`, but startup requires pysam and the pass-count gate rejects a skipped control. No environment upgrade is part of this change.

### Scientific and exact submission continuity

Fixture, observer, settings checker, the original five test suites and protocol hashes all match the accepted01 pins. Protocol remains `d4a0f851bd4536e5a3b6275dd8a11c2bc5832af9c26672b9b8fc8bfa58c6953e`. There is no changed reference, molecule, CIGAR, allele truth, arm order, evidence/reporting threshold or endpoint. The fixed common chromosome regex, observed flat-settings checks, exact same-record PASS/heterozygous recovery, conservative joint-edit UNRESOLVED state and strict REF-only candidate/final absence gates remain implemented. Canonical failure or uncertainty stops later arms. No native compatibility or recovery is asserted before execution.

The literal command uses02 in the claim, job name, logs and outer-wrapper path and the actual bundle hash in both the claim and wrapper argument. `set -euo pipefail` plus `set -C` ensures failed exclusive claim creation cannot proceed to sbatch. Outer and payload claims are exclusive; the outer wrapper verifies the manifest hash and entries, and the payload verifies entries around its run. Unknown acknowledgement consumes this02 submission claim. All01 paths/claims remain separate and cannot be used as a retry mechanism.

One-CPU affinity, GNU-time waited-tree accounting,480s timeout/5s grace,120s command timeouts, per-process CPU300/450s,4GiB address space, native1MiB file limit,1MiB/64-file per-arm postchecks,64KiB successful logs/fixture cap,32MiB control tree and8MiB raw archive cap are unchanged. Only the control tree permits intentional test links without following them; native trees reject links. The original distinction between postchecks and hard aggregate/physical-I/O bounds remains essential. Preserve any oversized failure remotely and stop bounded collection rather than trim results or increase the allowance silently.

### Fresh account and proceed conditions

| Account item | Replacement02 value |
|---|---:|
| Prior retained bytes, including full attempt01 charge | 40,503,743,371 |
| New full byte reservation, to book before staging | 268,435,456 |
| Prospective cumulative retained bytes | 40,772,178,827 |
| Prior measured named CPU, including attempt01 once | 558.792707 seconds |
| Fresh named CPU allowance | 600 seconds |
| Prospective named CPU with allowance | 1,158.792707 seconds |

The same64/32/96/24/24/16MiB components sum to256MiB, with separate asset, controls, native opaque, explicit fixture/output passes, archive and failure/metadata coverage. The totals fit68,719,476,736 bytes and7,200 named CPU seconds. They are a named conservative allowance, not measured physical I/O. Book this new full byte charge before02 root creation/staging; retain it on failure. After execution add only replacement02's measured outer user+system CPU once. No old byte charge is refunded and no01 allowance or slot is transferred.

Main's10:20:56+07 empty queue, absent02 logical/physical roots, exact workspace resolution and Oct22 expiry are timestamped reported preflight facts, not reviewer live checks. Recheck the relevant state before staging/submission, verify the booked ledger and all staged13 pins remotely, then use this exact single-submission file. Exact-stack controls, authenticated asset/executable version, settings/input integrity, scientific stops and bounded raw collection remain runtime gates. No result is accepted before raw-result review.

CONDITIONAL ACCEPT allows the main's already authorized workflow to book, stage and submit this fresh02 once those gates pass. It is limited to this filesystem correction and fixed diagnostic; no repeat of01, selective native replay, post-outcome tuning, new method, real-data campaign or publication claim follows. No additional user confirmation is required by this review. This reviewer took no launch/book/Git action and changed only the owned note. All earlier review snapshots, incomplete01 evidence, charges, guards and the released-callset STOP remain preserved.
