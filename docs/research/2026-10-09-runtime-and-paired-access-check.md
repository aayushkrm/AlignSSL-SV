# Runtime, retained assets and paired-data access check

9 October 2026. Main checks in parallel with scientific selection. No caller
experiment, genomic acquisition, job launch/cancellation or installation.

## Current cluster and local state

At 23:47:30+07, the project account queue was empty. Direct version commands
completed: `/home/igorno/miniconda3/envs/bioinfo/bin/samtools --version`
reports samtools1.9/htslib1.9; the installed Truvari reports5.4.0. The older
missing-library report is historical, not a current runtime failure. These
checks do not validate every command, caller, package or data input.

Scratch remains `/scratch/igorno-alignssl_restart_20260922`, expires
22 October 2026 at23:02:50+07, with one extension available. No extension
was used. Local `df -k` reports68,595,252KiB available (about65.4GiB), above
the10GiB guard. Genomic downloads are not selected by this storage finding.

A depth-four filename inventory of this scratch workspace, the project home
and `/home/igorno/deletion_calling` found the old HG002 pilot, synthetic native
test files, manifests and the Manta image. It also listed other assay trees
(Cell_lines, ImprovedFCNsignal_hg38, MCF-7_replics); their contents were not read,
repurposed, removed or treated as this project's SV truth. No unrelated job
was inspected or changed. This was not a complete cluster-wide data inventory.

Exact metadata confirms the pilot BAM is a regular single-link file owned by
igorno,123,564,646bytes; its manifest is11,535bytes. The GIAB-v5-GRCh37 and
HGSVC3-v1-GRCh38 staging directories still exist. A selected32-line BAM-header
view shows the old novoalign/hs37d5 short-read provenance and coordinate-sorted
output. No whole read traversal or new integrity/reference/coverage claim.
These assets do not become matched long-read DNA/RNA material. Their prior
development exposure and scientific limitations stand.

## What the four public multi-ome hubs actually expose

The [primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC12077378/) links
four benchmark-line track hubs. Main read selected complete benchmark/Table1,
DNA/RNA preparation, genomic calling/phasing, transcript calling and data
paragraphs. The same-cell Fiber-seq/MAS-Seq pairing is real; genomic calling
and haplotype analysis are already part of the native study. Transcript reads
may include PCR duplicates. The controlled patient is not interchangeable
with these reference lines, and a new causal or clinical result is not shown.

Each public `hub.txt` names `genomes.txt`, which names hg38 and `trackDb.txt`.
Exa retrieved those eight small manifests. Firecrawl live retrieval returned
four complete normalized track bodies, each HTTP200. A full-field parse of
those returned bodies, rather than a clipped display, produced:

| Line | Normalized characters | Track definitions | bigDataUrl fields | .bw / .bb |
|---|---:|---:|---:|---:|
| GM12878 |17,616|74|63|16 /47|
| HG002 |16,516|71|60|16 /44|
| GM20129 |66,136|258|246|19 /227|
| HG02630 |66,136|258|246|19 /227|

All bigDataUrl fields in each manifest are unique. Types are bigWig and
bigBed; these are FIRE/accessibility/visualized read-bin tracks, not declared
sequence-alignment BAMs. None of these four manifests declares BAM, CRAM,
RNA, transcript, FASTA or VCF fields, or an include directive. A separate live
bounded curl/awk check of the HG002 raw text agrees with71tracks,60URLs,
16bw and44bb. No binary track object was read or downloaded. These finite
manifest findings do not show that processed RNA, assemblies or variant files
are absent elsewhere in the BioProject.

The roots, directly linked by the paper, are:

- [GM12878 hub](https://s3-us-west-1.amazonaws.com/stergachis-manuscript-data/2023/Vollger_et_al_long-read_multi-ome/GM12878_pacbiome/trackHub/hub.txt)
- [HG002 hub](https://s3-us-west-1.amazonaws.com/stergachis-manuscript-data/2023/Vollger_et_al_long-read_multi-ome/HG002_pacbiome/trackHub/hub.txt)
- [GM20129 hub](https://s3-us-west-1.amazonaws.com/stergachis-manuscript-data/2023/Vollger_et_al_long-read_multi-ome/GM20129_PS00447/trackHub/hub.txt)
- [HG02630 hub](https://s3-us-west-1.amazonaws.com/stergachis-manuscript-data/2023/Vollger_et_al_long-read_multi-ome/HG02630_PS00445/trackHub/hub.txt)

Exa supplied manifest navigation and Firecrawl supplied the full track text.
No discovery search or complete paper audit occurred in this check. The
Max-effort scientific decision is pending; access checks alone select no
experiment or publication lead. The broader goal remains active and unmet.
