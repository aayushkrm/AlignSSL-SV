# HG002 CDS-overlap cohort index

Development-only, DNA-first code. This is a preliminary event/gene/ALT index.
It is not an event/gene/alternate-haplotype denominator or final D.

## Use

```sh
python analysis/hg002_cds_overlap_cohort.py \
  --vcf calls.vcf.gz --gtf gencode.primary.gtf.gz \
  --sample HG002_WGS --output hg002_candidates.jsonl
```

Both inputs and an explicit sample are required. Match the VCF sample column
exactly; there is no HG002 alias or implicit sample/contig renaming.
Output uses exclusive creation: an existing file causes an error.
A nonempty VCF with no contig names shared with retained CDS features fails.
An empty VCF is valid. Partly unmatched contigs remain UNKNOWN.

## Coordinates and retention

GTF CDS [start,end] becomes zero-based [start-1,end).
An anchored symbolic DEL at POS=p, END=e removes [p,e), not the anchor.
Literal alleles trim their shared prefix and suffix with numeric slice stops.
A left-anchored INS uses boundary POS; a suffix-only INS uses POS-1.
INS at either CDS edge is included. DEL needs half-open base overlap.
All overlapping CDS isoforms and genes are retained; no canonical selection.
Exact duplicate representations share a row, with all source records retained.
This is not linked-event collapse or biological event normalization.
Source records retain POS, REF, raw INFO, FILTER, GT, and phase metadata.

## States and counters

Rows have overlap_status OVERLAPS_CDS, UNKNOWN, or OUTSIDE_CDS.
Unresolved geometry remains an event-level UNKNOWN row with no assigned gene.
Duplicate INFO keys, ambiguous cardinality, and conflicting END/SVLEN or
sequence lengths clear inferred geometry and size; they do not become negatives.
INFO Number=1/A is checked when declared; absent/variable headers permit scalar
or one value per ALT. Other cardinalities remain UNKNOWN.
A consistent known size below 50 bp is excluded, including symbolic alleles.
Filtered, invalid/out-of-range/missing GT, unphased/blockless heterozygotes,
symbolic/missing sequences, and uncertain annotations remain UNKNOWN.
Native PASS CANDIDATE is not a P1 functional negative; p1_state is NOT_ASSESSED.
The first JSONL record is a summary with final_D=null and source-ALT counters.
Counters report uncalled ALT, other type, known-small, outside-CDS, overlap,
and unresolved observations. They count duplicates and are not independent D.

## Verification and gaps

Existing venv: 31 synthetic tests passed on 2026-10-10 (source 217 lines,
tests 122 lines). Run python -m pytest -q -p no:cacheprovider
tests/test_hg002_cds_overlap_cohort.py with the project venv interpreter.
Controls cover both INS anchors, CDS edges, all isoforms/genes, duplicates,
FILTER/phase/GT, small symbolic calls, INFO conflicts/cardinality, exact samples,
contig mismatch/empty inputs, counters, and exclusive output.
No real datasets, installs, jobs, RNA, LiftOn, ORF tests, copy-state validation,
or alternate-haplotype denominator construction were used or implemented.
Main must pin the exact assets, reference build, and recipe; no build compatibility
or sequence completeness claim follows from a matching contig name.
