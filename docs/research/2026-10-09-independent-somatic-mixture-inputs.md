# Independent somatic-mixture input check

Date: 2026-10-09. This is a bounded metadata and literature check. It does not
select a study, rank callers, or approve a campaign. The main task retains the
SVUPP provenance review.

Requested model and effort: GPT-6 Luna / max. Actual backend and effort are
**not backend attested**.

I read the full governing objective. Its SHA-256 matched the requested value:
`74ba6450712e7f0e763cd81de896d3a71ca73f9c4a10fec3f1ecab59b3f1b0b8`.
I also read both named October 9 research notes in full. I read the Search
skill and its `searching`, `patterns-papers`, `source-quality`, `extraction`,
and `filtering` references in full.

## Finding

**No second independent physical biological mixture is verified.** MIMS is one
physical six-donor pool distributed to sequencing centers. The nearest other
long-read mixture in the reviewed methods is an in-silico read mixture of
HG002 and HG00733. Qin, Heinz, and Li describe public somatic-call resources
from matched tumor-normal samples, not a physical dilution mixture.

The papers describe public benchmark truth or call files. That does not verify
an available, score-bearing query VCF for each candidate. I did not inspect
archive members, VCF records, labels, or score values. This check does not
establish novelty or identify a leakage-safe final test.

## Evidence table

| Dataset | Donors and mixture independence | Dilution design | Long-read technologies | Truth, reference, and masks | Per-call outputs, scores, and public access | Source and read scope | Qualifies as a second independent mixture? |
|---|---|---|---|---|---|---|---|
| **SMaHT MIMS** | One physical HapMap DNA pool: HG005 83.5%; HG02622 10%; HG002, HG02257, and HG02486 2% each; HG00438 0.5%. The same pool went to five GCCs. Center, depth, and platform runs are replicates of that pool. | One fixed blend, not a verified series of separately prepared pools. The mixture creates expected allele fractions down to 0.25%; ddPCR checked six representative SNV mixture fractions. | PacBio HiFi and ONT, plus Illumina. The paper reports five Illumina, four HiFi, and two ONT replicate datasets across the centers. | Assembly-based SV calls from the same six HPRC donor assemblies were merged and harmonized. The paper reports 34,140 INS/DEL benchmark events across 90.2% of GRCh38 autosomes, with high-confidence regions; its abstract describes over 21,000 pseudo-somatic events. The [v2.0 repository](https://github.com/BCM-HGSC/SMaHT_MIMS) lists `hard`/`easy` truth VCFs and standard/complex BED regions. The default BED excludes some multi-SV haplotypes; the complex BED retains them. | The paper reports 12 pipelines and 45 discovery results. The README describes a benchmark VCF/BED as the baseline and expects a caller VCF as comparison input. The README does not list a per-caller score-file inventory or score schema. The paper points to [data.smaht.org](https://data.smaht.org/) and the associated-data statement names `phs004193`; file-level access and query-call availability were not checked. | [MIMS paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12458932/): mixture construction, assemblies, methods, and public-data statement. [Official repository](https://github.com/BCM-HGSC/SMaHT_MIMS): README and benchmark/mask metadata only. | **No.** It is the existing physical mixture. Replicates do not create a second mixture. Per-caller query files and score fields remain unverified. |
| **Sniffles2 HG002/HG00733 spike-in** | HG002 and HG00733 are distinct donors, but the methods combine their reads computationally. No physical DNA mixture is described. | Synthetic coverage pairs: HG00733/HG002 at 63×/5×, 63×/7×, 60×/10×, 55×/15×, and 50×/20×. The paper reports 7–28% spike-in VAFs. | ONT for the synthetic mixture (inferred from the paired ONT sources and the methods); HG002 HiFi is a separate benchmark input. | Truth uses HG002 SVs not found in HG00733, restricted to GIAB Tier 1 overlap; the low-frequency analysis covers insertions and deletions. The paper’s GIAB reference is GRCh37. This is donor-genotype truth, not orthogonally established somatic mutation truth. | The paper points to public individual Sniffles VCFs at [Zenodo 8144524](https://doi.org/10.5281/zenodo.8144524). It does not identify a mixture-specific query VCF or a calibrated per-call score schema. It describes supporting-read edit distance as a filtering confidence measure, not a reported probability. | [Sniffles2 paper](https://www.nature.com/articles/s41587-023-02024-y): methods for the read mixture, GIAB restriction, and data availability. The linked Zenodo record was not opened. | **No.** The sample is a digital read mixture. Donor-derived truth and query reads come from the same two genomes; this is a benchmark/development comparison, not a second physical mixture or a leakage-safe final test. |
| **Qin, Heinz, and Li somatic-SV resource (2026)** | Six named cell-line pairs: COLO829, HCC1395, HCC1937, HCC1954, H1437, and H2009, each with a matched normal. COLO829 tumor/COLO829BL blood cells are one pair. The paper also lists five osteosarcoma tumor-normal pairs. These are separate pairs, not a pooled mixture. | No dilution series is described. | PacBio HiFi and ONT. The paper uses GRCh38, a pangenome built from 464 HPRC Release 2 assemblies, and a normal-sample self-assembly when available. | A COLO829 section uses a prior 58-SV call set as truth. A later six-pair section says no curated truth was available for those cell lines. The article therefore does not establish truth labels across the full six-pair set. Code-availability metadata lists VNTR and evaluation-region BEDs in Supplementary Table S1. | The paper says all SV calls and de novo assemblies are deposited at [Zenodo 14715664](https://doi.org/10.5281/zenodo.14715664). It also lists SRA and EGA sources. Per-sample/caller archive members and score fields were not inspected, so a score-bearing query file is **not verified**. | [Qin, Heinz, and Li paper](https://aacrjournals.org/cancerrescommun/article/6/9/2282/788607/Improving-Long-Read-Somatic-Structural-Variant): methods, named cell lines, truth descriptions, and data availability. The Zenodo archive and source-code repositories were not opened. | **No, for this ask.** It is a relevant matched tumor-normal somatic resource, not an independently constructed mixture. Its public call/assembly statement does not establish a score-bearing file or locked external test. |

## Search and source accounting

| Item | Record |
|---|---|
| Search angles | Three: MIMS mixture and center replicates; other long-read somatic/mosaic mixture truth; Qin/Heinz/Li methods and data resource. |
| Requested result-slot ceiling | Up to five per angle: 15 total. The built-in search call had no per-query result-count control. |
| Search results returned | I mistakenly ran the three initial queries through built-in web before confirming Exa was available. The tool returned 25 result cards in its combined response, above the requested 15-slot cap. I stopped discovery there and ran no follow-up searches. |
| Exa use | Exa fetch read four unique primary pages: the MIMS paper, MIMS official repository README, Sniffles2 paper, and Qin/Heinz/Li paper. No Exa search was run after the built-in result-card over-return. No CLI search was used. |
| Other page attempt | A BioRxiv mirror of the MIMS paper returned HTTP 403. The PMC page was recovered through Exa fetch. |
| Unique primary pages read | Four: [MIMS paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12458932/), [MIMS repository](https://github.com/BCM-HGSC/SMaHT_MIMS), [Sniffles2 paper](https://www.nature.com/articles/s41587-023-02024-y), and [Qin/Heinz/Li paper](https://aacrjournals.org/cancerrescommun/article/6/9/2282/788607/Improving-Long-Read-Somatic-Structural-Variant). The MIMS repository read was its README and public resource metadata, not source files. |

The search was limited. It does not prove that no other mixture exists. A
mosaic SNV/indel benchmark also surfaced, but it does not meet the long-read
SV criterion and was not fetched.

## Interpretation and limits

Input availability and scientific novelty are separate. MIMS exposes truth and
region files, and the Qin/Heinz/Li paper reports a call-and-assembly archive.
Neither fact establishes a second physical mixture, a score-bearing query
file, or novelty. The Sniffles2 spike-in is digital. The Qin/Heinz/Li resource
uses tumor-normal biology but does not provide the requested dilution-mixture
design.

No source reviewed here establishes a leakage-safe, finalized test set for a
new method. MIMS truth derives from assemblies of the same six donor identities
used in its pool. Sniffles2 defines spike-in truth from the same donor genomes
used to build the synthetic reads. The Qin/Heinz/Li paper evaluates published
and author-generated calls against a prior COLO829 truth set and other cell-line
pairs; this metadata check did not audit sample overlap or test-set locking.
No test labels were read.

Conclusion: **not yet verified**. This is not an exhaustive-absence claim and
does not approve a campaign. No sequence or callset data contents were
downloaded or opened.
No Git, cluster, job, booking, install, code-file, archive, VCF, BAM, FASTA,
raw-read, or label-content operation was performed. No message was sent to
another chat.
