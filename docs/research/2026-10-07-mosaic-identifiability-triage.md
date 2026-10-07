# Competing question: evidence for a rare allele, not merely an SV family

Date: October 7, 2026. Literature-based triage only. The released-callset
screen is closed after its real metadata failure. This note does not replace
its inputs, relax its contract or reopen it. DeepSV is not a foundation;
SSL and any particular architecture are not requirements.

## Strong prior art; reject an easy pivot

The SMaHT MIMS preprint uses a six-donor physical mixture, assembly-derived
truth and replicate sequencing centers. Its beta-binomial support analysis
already connects depth, allele fraction and read thresholds to detection
limits. A study that adds another low-VAF coverage curve or caller ranking
would duplicate this contribution. The paper also documents nearly identical
germline/somatic alleles and collapses similar alleles for its primary
benchmark. [Primary methods](https://www.biorxiv.org/content/10.1101/2025.09.18.677206v1.full).

The official repository distinguishes an `easy` collapsed benchmark from a
`hard` allele-resolved benchmark. It requires germline and somatic calls to
be matched together and warns against multi-matching for somatic recall.
These are existing controls, not new discoveries. Its default territory
excludes complex nearby-haplotype variants; the wider territory can have
representation-related false classifications.
[First-party README](https://github.com/BCM-HGSC/SMaHT_MIMS).

Pangenome/personal-assembly filtering of germline-induced somatic false calls
is also prior art, not an unoccupied pivot. The 2026 Qin/Heinz/Li article
describes exactly that joint filtering strategy.
[Primary abstract](https://pubmed.ncbi.nlm.nih.gov/42696744/).

## Hypothesis to challenge, not a selected method

Can an SV call distinguish a minority **specific allele** from an abundant,
near-identical background allele, and can it abstain when the reads cannot
identify that difference? Event-family presence is a different target from
the presence of that specific minority haplotype. This is an inference from
the prior work's explicit allele-collapse problem, not proof of a new gap.

| Gate | Cheap falsifier or required evidence | Stop condition |
|---|---|---|
| Importance | Determine whether rare-allele attribution changes a useful call or uncertainty statement, not just a benchmark label | Only a matching/representation difference |
| Novelty | Compare native Sniffles, SVDSS, Severus, graph callers, genotypers and MIMS hard-allele analysis before proposing a model | Existing evidence/likelihood controls already address the target |
| Identifiability | On a fixed small allele-pair set, compare evidence supporting shared SV structure with evidence distinguishing the two alleles; use simple likelihood/alignment controls first | No recoverable signal, or a simple native/classical rule fully solves it |
| Labels | Verify exact assembly/haplotype identity, uncollapsed alleles, masks, mixture metadata and held-out read runs | Only easy/collapsed labels or unsupported negatives |
| Transfer | Predefine locus/allele-family splits and an untouched sequencing-center or independent-mixture test | Same locus/donor evidence leaks, or center replicates are misrepresented as biological replication |

No read-level experiment, input download or method implementation is approved
by this note. Start with prior-art and metadata feasibility, not full WGS
transfer. Lack of distinguishing reads can justify abstention; it cannot prove
an absent allele. A coverage curve alone is expressly rejected as the novelty.

## Data feasibility and limits

The paper points to the SMaHT portal and an official code/benchmark repository;
the latter's README currently identifies benchmark v2.0. Exact file hashes,
reference compatibility, licenses/access, uncollapsed donor genotypes and
read-range/index availability have **not** been verified here. The paper's
public-data statement is not proof that every required file is accessible.
No biological input was acquired.

Six donors in one physical mixture and sequencing-center replicates provide
useful controls, not independent mixtures or proof of population-wide transfer.
Some donors overlap already exposed development resources, including HG002;
none can be relabelled as an untouched final test without a leakage audit.
The excluded complex territory cannot silently become certified truth.

## Retrieval record

Today minus twelve calendar months is **October 7, 2025**. The dated PubMed
search used October 7, 2025–October 7, 2026. The MIMS September 20, 2025
preprint is older close prior art and is included explicitly for that reason;
its current PubMed record labels it a preprint. Exa's January 1 date for the
bioRxiv page is rejected in favor of Entrez's named-record metadata.
[PubMed record](https://pubmed.ncbi.nlm.nih.gov/41000761/).

Main used Exa Search and Life Sciences Literature Entrez. Two Exa searches
requested ten slots, with duplicate MIMS results and off-target SNV/indel
results. Requested slots are not ten fully read independent papers. Fetches
read the MIMS primary abstract/methods, its PubMed record, the first-party
README and the Qin/Heinz/Li abstract; repeated longer extraction reached
MIMS data/code availability and relevant methods. No failed lookup supplies
evidence. Entrez esearch returned ten records; esummary resolved named dates
and titles. A compact efetch hid the requested abstracts through truncation;
Exa's PubMed-page fetch supplied the relevant Qin abstract instead. Broad
livestock/bacterial/clinical hits were not efficacy evidence.

This is not an exhaustive novelty review. The strongest current reason to
reject this idea is that MIMS, existing genotypers or modern graph methods
may already solve the useful target. Compare this candidate with the separate
copy-number/uncertainty triage before selecting any experiment.
