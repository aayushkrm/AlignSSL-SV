# Independent review: family SVs and repeat outcome sources

2026-10-08. Final verdict: accept main's narrow stops for all three current framings, the qualified zero-count mathematics, and the deletion-origin counterexamples; no new lead is selected.
Main can reject weak routes without choosing a replacement method. The wider publication goal remains unachieved.
Requested reviewer configuration: GPT-6.1 Sol/high. Actual backend model/effort is not independently attested; no additional reviewer was launched.
The full attached goal was read earlier in this reviewer session. All four source notes below and main's completed three-direction disposition were read in full across this review and addendum.

## Family SVs: accept the narrow stop, qualify the proposed falsifier

Reviewed [family territory note](2026-10-08-family-sv-territory.md). Its named TRHR hypothesis is concrete, but its independent sample is unverified.
The reported 65 candidates and 15 confirmed calls describe ascertainment/validation, not a measured gametic recurrence fraction.
Neither these counts nor paternal bias estimate the sperm mosaic fraction for REACH000479.

| Observation | Supported interpretation | Still unresolved |
|---|---|---|
| Child ALT; zero ALT in sampled parental tissue under a support rule | Operational de novo call | Undetected parental mosaicism, tissue restriction, assay error, mutation timing |
| Child ALT on paternal H1 | Chromosome/haplotype origin | Whether mutation arose in the father, one sperm, or the child's early development |
| Exact variant detected in independent paternal sperm targets | Parental germline mosaicism in that sample, after assay validation | Fraction at conception, transmission probability, clinical outcome |

Distinguish a true new mutation from a variant absent only in the assayed parental tissue. A real germline mosaic can pass a trio de novo calling rule.
A mutation confined to one transmitted sperm and a child's early postzygotic mutation are also different histories; paternal phase alone does not distinguish them.
Parental somatic REF support is not evidence that every germ cell is REF. Conversely, zero sperm detections do not establish absence in the germline.
The older missed-parent and sperm-mosaic studies are affirmative controls as reported, not an absence-based novelty argument.
Small-variant sperm assays establish precedent, not validated Alu-junction sensitivity or a new SV contribution.

Correction to the zero-count gate: for N independent, identically sampled callable haploid targets with perfect ALT detection, p_upper = 1 - 0.05^(1/N).
At N=300 this is about 0.9936%, so the stated one-sided 95% bound is below 1% under that model.
For fixed known ALT detection sensitivity 0 < s <= 1 and negligible false positives, the corresponding bound is min(1, [1 - 0.05^(1/N)]/s).
A passing 1% positive control alone does not establish s=1, the effective N, or uncertainty in s. Sensitivity uncertainty requires a justified conservative calculation.
N must count independent callable gametic targets, not reads, PCR copies, overlapping fragments, or repeated observations of one sperm.
The two aliquots must share a declared sampling model; assay specificity, allele-dependent recovery, and exact insertion/junction identity also need validation.
The 1% threshold is a hypothesis threshold. A measured sperm fraction is only a conditional transmission proxy: fertilization/selection, sample timing, and representativeness matter.
It is not an unconditional recurrence probability or clinical penetrance estimate.
Retain rejection of this route: sample availability is unknown and the current contribution is a known assay applied to one unverified family sample.
Do not turn a sample-availability inquiry into a publication lead. No sperm assay or clinical recommendation is authorized here.

## Repeat sources: accept linked observations, preserve their estimands

Reviewed [main's repeat outcome audit](2026-10-08-repeat-outcome-source-audit.md); primary-source facts below remain reported inspections.

| Evidence | What it can support | What it does not identify by itself |
|---|---|---|
| Handsaker repeat-bearing RNA and expression linked to the same nucleus | Cross-sectional repeat-estimate/expression association in sampled nuclei | That cell's earlier DNA lengths, expansion trajectory, or later death |
| UMI consensus and native long/short-library controls | Technical precision and tested assay artifacts | All uncaptured alleles, transcripts, lengths, or missing nuclei |
| Kay brain/blood distributions and neuronal measurements | Tissue-specific observations and native LOI overlap | Individual cell transitions or a universal blood-to-brain transfer rule |
| Edited CAGinSTEM clones and neuronal phenotypes | A controlled cis-interruption contrast within the tested culture system | Clinical progression or a human nucleus's longitudinal fate |

Do not dismiss RNA-derived measurements merely because they are RNA-derived. Same-nucleus linkage is stronger than an unlinked bulk association.
It remains cross-sectional. Expression state, capture, and survival can affect which alleles and nuclei enter the measured distribution.
UMI consensus reduces errors among captured molecules; precision conditional on capture does not establish length-independent capture or identify dropout.
The maximum per-cell UMI estimate is an order statistic. Dependence on molecule count/noise is a concrete calibration concern, not a demonstrated native bias.
Check what the native paired-transcript, library, chimera, unaligned-read, and regression controls already establish before proposing any repair.
Donor/subtype/library-size adjustment is native prior work; regression adjustment alone does not reconstruct missing cell histories.
Edited-clone interventions can supply causal evidence in their tested system with appropriate clone/replicate controls; lack of clinical labels does not erase that evidence.
Separate the intervention's total phenotypic effect from its proposed expansion/selection mediation, and both from clinical prediction.
Neither a bulk clone time series nor a processed-cell archive automatically supplies independent transition or death labels.

## Expansion versus selection: current question is not a method target

The proposed question names a familiar mixture/ascertainment problem, not a demonstrated residual error or a distinct algorithmic contribution.
Native expansion modeling, loss assumptions, distortion controls, and cis interventions already overlap it according to main's note.
The completed native-control note supplies reported overlap, qualified in the addendum; this review does not claim that all possible extensions are known.
Observed short/long class odds can change through transitions, differential population growth/survival, or differential capture.
Even without transitions, final observed odds equal initial true odds times the relative population multiplier times the final relative capture probability.
Different parameter settings can therefore match the same measured distributions while assigning different expansion histories.
Exact native assumptions and independent controls can restrict this ambiguity; generic mixture fitting cannot remove it by naming the latent mechanisms.
An apparently new tail is not decisive if baseline support, detection limits, or capture remain unresolved.
No universal impossibility is asserted: independent transitions, survival/cell-count measurements, or justified restrictions can change identifiability.

Required consequential falsifier before further method framing:

1. Fix a named native cis contrast, allele, clone/replicate set, assay/time points, and a specific biological conclusion that would change.
2. Specify the native observation/measurement model and the proposed alternative; expose the assumption that makes their predictions differ.
3. Exhibit competing expansion/selection explanations that fit all retained native controls, or demonstrate why those controls exclude one.
4. Name an independent adjudicating observation, its error model, and a pre-set disagreement/stop criterion for the changed conclusion.
5. Show why native inference or a standard constrained mixture/likelihood analysis does not already answer that test.
This is a definition gate, not permission to acquire inputs or run assays. No exact contrast or adjudicating observation is established by these notes.
Open processed cells, an SRA accession, or data-on-request status do not meet the gate. A data inventory is not an independent outcome label.
STOP the current generic framing rather than produce an availability wrapper. Reconsider only a concrete falsifier surviving native controls.

## Final qualified addendum: all three dispositions reviewed

Both [repeat native controls](2026-10-08-repeat-native-controls.md) and [mitochondrial territory](2026-10-08-mitochondrial-sv-territory.md), plus [main's disposition](2026-10-08-three-direction-disposition.md), were read in full. This addendum is complete; accept the disposition's narrow stops and claim limits.
Repeat: reported SCIA v3 distribution-shift metrics and MosaicTR v1 haplotype instability are affirmative overlap, not peer-reviewed confirmation or native replication here; retain STOP for generic distribution/noise inference.
TRGT sequence/methylation summaries are another reported control, but its abstract-only inspection proves no feature absence or joint-state novelty.
The interruption–methylation hypothesis is unproven. Same-haplotype association can reflect baseline length, capture, cell mixture, or a consequence of instability; it does not identify a joint causal effect.
A replicated changed joint-state or stable/expanding call from the same assay establishes reproducibility, not correctness, functional consequence, or methylation causality. Paired tissues are not same-cell histories; CAGinSTEM PCR does not preserve native methylation, as reported by main.
Require the concrete falsifier above and an independent adjudicator appropriate to the claimed distribution, transition, or functional estimand; no such labels are verified.
Mitochondria: independent cell-clone/lineage labels are NOT independent deletion-origin-event labels. MitoTracer's reported lineage benchmark cannot adjudicate recurrent deletion origins by itself.
Hand counterexample: one ancestral deletion J, then a cell-lineage split, then private linked mtDNA SNVs a and b in daughters gives J+a and J+b with distinct external clone IDs despite ONE deletion origin.
Conversely, independent J events in two cells sharing an ancestral mtDNA haplotype give identical sequence features. The worker figure's "separate lineages -> repeated origin" inference is unsupported.
Phasing can resolve which sequence features coexist on a deletion molecule. It cannot by itself date or count deletion events; private/neutral labels do not establish their history or selective neutrality.
Cell-lineage expansion and within-cell replication/segregation of deletion-bearing mtDNA are distinct processes. Lineage prediction plus orthogonal deletion-presence confirmation does not validate origin events.
The proposed augmented log-loss test could assess lineage prediction only. SNV-only and shuffled-linkage controls do not convert its labels into deletion-event truth; freeze the prediction target and splits, including treatment of unseen clone classes.
Cluster evaluation/uncertainty at independent biological units and exclude donor/clone leakage; a positive bootstrap gain alone proves neither novelty nor origin identification.
No joint deletion-junction/linked-molecule/independent-event artifact is verified. Even the worker's proposed four-field table would need event-history evidence beyond clone membership for an origin claim.
Reject the origin framing: the permitted hand histories expose a label failure before artifact access, not observed events or universal impossibility. No MitoTracer availability hunt follows; these logical/label failures are not biological nulls or publication results.
No primary fetch was used. These are note-level claim-scope checks and hand reasoning; papers, supplements, archives, code, and native performance were not independently re-audited.
Source dates, completeness, assay performance, and availability retain each note's inspection limits, including abstract-only lineage controls and NanoDel preprint-method fallback.
Only this review file was written. No literature expansion, raw data, code execution, install, experiment, job, or Git action; no lead, campaign, native-performance effect, or expensive approval is accepted.
