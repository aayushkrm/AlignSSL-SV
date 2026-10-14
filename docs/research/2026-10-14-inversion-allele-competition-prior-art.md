# Inversion allele competition: concrete existing controls

14 October 2026. This bounded prior-art check runs beside the post-census
investment decision. It selects no method or compute campaign. DeepSV is not
the foundation. The full publication goal remains unmet.

## Implication for the next experiment

Generic reference/alternate realignment, read linkage or local assembly is
not a new contribution. A useful next experiment must expose a specific
recoverable failure and distinguish it from existing genotyping/discovery
methods. A regional, known-allele test is not an equal-input comparison with
blind discovery. Our 47-QNAME regional input is also not all possible source
reads: repeat-mapped or unmapped reads outside the region remain unobserved.

## Verified primary-source methods

**SVJedi-graph** is a peer-reviewed known-catalog long-read genotyper, published
30 June 2023. Its Methods explicitly represent inversions in a variation graph
and map reads with minigraph. Allele-specific graph edges provide support;
the default overlap is 100 bp on each side. Both inversion junctions are
represented. A read spanning both counts twice under the reported support
scheme; that is not two independent molecules. The paper distinguishes
whole-graph mapping from reference-alignment-based preselection. This makes it
a relevant existing allele-competition control, not evidence that it solves
our particular case. Its reported HG002 real-data accuracy must not be read as
an inversion-specific validation result. [Primary Methods, sections 2.1–2.5](https://pmc.ncbi.nlm.nih.gov/articles/PMC10311344/).

**gSV** has a versioned primary preprint, posted 4 March 2026 (the identifier
contains 2 March). Its Methods combine sparse read/reference difference
encoding, read clustering, local wtdbg2 assembly and copMEM2 maximal exact
matches. It explicitly retains forward and inversion matches and addresses
multiple matches. Basic local assembly plus alternative matching therefore
has close prior art. Its complex-event evaluation includes region-level and
component-level metrics; those do not by themselves establish whole-haplotype
accuracy. The inspected PDF is a preprint, despite a journal-style template;
no peer-reviewed publication, runnable release or native performance is
attested here. [Version 1 primary Methods](https://www.biorxiv.org/content/10.64898/2026.03.02.703663v1.full.pdf).

Search also returned npInv's explicit repeat-mediated inversion/subalignment
method. That result reinforces a prior-art warning but is a search lead in this
note, not a separately verified current implementation or selected baseline.
No result in this note establishes exhaustive absence of another method.

## Search and reading scope

Used the Exa Search skill, its paper/code query guidance, source-quality and
synthesis references. Two distinct queries requested 10 results each:
known-allele repeat/placement competition, and inversion discovery under
repeat-driven ambiguity. Thus `sources_reviewed` under the skill's requested-
result-slot convention is 20 across two workstreams; this is **not** a claim
that 20 papers were validated or read in full. The combined search tool output
was truncated. Two primary pages were then fetched directly, at a 30,000-
character cap per page. Main inspected their relevant Methods portions and
publication/preprint headers, not every supplement or full article. The gSV
author PDF, not a search engine date field, establishes its version date.

Exa returned usable primary text. No Firecrawl dependency, CLI installation,
subscription change, model download, genomic download or cluster job followed.
The skill influenced the choice to use named existing controls and separate
genotyping from discovery before any further investment.
