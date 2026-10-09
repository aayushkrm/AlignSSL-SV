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
