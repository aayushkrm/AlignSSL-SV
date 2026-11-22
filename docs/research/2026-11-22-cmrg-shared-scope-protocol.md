# CMRG and v5.0q shared scope protocol

Can an exact, shared development denominator support a pilot on the HG002
short-read candidate gap reported by dicast? Freeze the following source
comparison before reading any VCF rows. A useful pilot needs enough loci
for paired case inspection. Both releases represent HG002 and can share
upstream evidence.

- Use the official GRCh38 [CMRG v1.00 VCF and BED](https://catalog.data.gov/dataset/challenging-medically-relevant-genes-benchmark-set)
  and [v5.0q stvar VCF and BED](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/v5.0q/).
  Verify the v5.0q VCF and BED against its published MD5. Record the actual
  CMRG source hashes and corroborate the bytes with the public GIAB S3 mirror
  where available. Preserve downloaded assets outside Git.
- Enumerate all PASS CMRG biallelic substitutions to A/C/G/T sequence on
  autosomes where trimming shared prefixes and suffixes leaves an insertion
  or deletion of more than 50 bases. Track every exclusion by reason. This
  is a fixed allele definition. It can differ from the published dicast
  subset. Indices and metadata may be relaxed only in a new analysis.
- An allele qualifies for shared scope when its full raw REF span, including
  its anchor, fits inside both unioned BEDs. Convert VCF POS to zero-based
  start. Count each disjoint failure category. Summarize the base-pair
  intersection separately. Coverage by this mask is necessary for this
  screen. Exact REF validation against sequence is beyond this step.
- Count exact normalized sequence-and-position matches in the v5.0q VCF.
  Apply the same sequence and span rules and retain duplicate eligible
  keys as ambiguous. The normalization trims only shared sequence. It
  performs no reference-based left shifting or complex haplotype alignment.
  Treat every unmatched eligible CMRG allele as unresolved. Do not infer
  caller errors, truth-set errors, or equivalence from proximity.
- Report counts by source eligibility, INS and DEL, and exact match status.
  Report every CMRG row with a reproducible status. Qualifying records
  retain the build label and minimally normalized representation metadata.
  Keep sequence, reads and public VCFs out of the repository. No caller
  output, genotype performance, or clinical phenotype enters this screen.

A shared scope with only a few records cannot support the broad blind
candidate thesis. A larger shared scope establishes an input for a design
and review, followed by sequence-aware reconciliation and true pre-score
and post-score caller outputs if justified. An exact match here does not
independently confirm biological truth. This is a real-data denominator
check, with at most 64 MiB transfer and two CPU minutes for scoring. No new
caller or cluster job is part of this check.
