# Inversion / artifact opportunity scout — 2026-10-14

## Decision

**Scientific STOP for the proposed public-HG002 filter-loss test.** I withdraw the earlier conditional lead below. The exact ONT run overlap is real, but the two resources do not measure inversion support in the same reference space. A coordinate join cannot repair that estimand mismatch.

This stop is limited to this published-table premise. It is not a biological null, and it does not show that Breakinator retains inversion support when reads are aligned to GRCh38. The molecular truth labels remain strong for complex germline inversions, but they do not model low-VAF mosaic events.

The prior S10 simple-INV case remains stopped as a new-method lead. That is not a biological null. This scout does not reopen it or inspect its reads.

## Correction: the proposed endpoint is not identified

Breakinator's primary Methods align HG002 reads separately to the maternal and paternal HG002v1.0.1 assemblies, select the alignment with the best alignment score, and prefer a greater-than-95%-contiguous alignment to one haplotype over a chimeric alignment across the other haplotype. For an inversion represented in one of those haplotype assemblies, the inversion allele is already a reference path. Its defining GRCh38-relative inversion breakpoints therefore need not appear as split-read breakpoints in these PAFs.

This is more than a coordinate-system mismatch. Liftover can translate positions, but it cannot make a read aligned to a personal inversion-bearing reference provide GRCh38-relative split-read support. Breakinator's classifications answer whether an alignment looks artifactual against its chosen haplotype reference. They do not say whether the filter removes evidence for the GRCh38-relative inversion. Complex sequence, assembly differences, or alignment errors can still produce splits, but this dataset does not identify those as support for the benchmark inversion.

So the proposed “support before/after filter at both inversion breakpoints” endpoint is invalid on these reports. A zero, low, or high overlap would not establish filter-induced loss or retention of inversion evidence. The earlier three-event threshold is withdrawn too.

## Relevant prior art

- **Artifact filtering is already active prior art.** Breakinator flags foldback and chimeric alignments by geometry. It uses minimum segment and mapping-quality thresholds, and calls a read artifact when it has a qualifying artifact breakpoint. The paper warns that genuine biological foldbacks can be hard to distinguish from artifacts. Its engineered self-complementary AAV control is a positive foldback control, not a genomic inversion control. [Heinz et al., *Detecting foldback artifacts in long-reads*, 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC12870357/).
- **Somatic calling is not an empty field.** SAVANA already removes putative fold-back-inversion-like alignments by default and classifies somatic calls against sequencing and mapping errors. It evaluates clonality and reports replicate concordance. A generic “low-VAF SV versus artifact” caller or filter is not a distinct lead here. [Elrick et al., *SAVANA*, 2025](https://www.nature.com/articles/s41592-025-02708-0).
- **There is a defensible complex-inversion truth set.** The 2026 benchmark builds truth from Strand-seq and phased assemblies, with higher-confidence tiers and orthogonal validation in its curated basis. It excludes Tier 3 from benchmarking; this scout will not turn unvalidated calls into negatives. For HG002 it reports 53 Tier 2 events, 46 heterozygous. [Cheng & Sedlazeck, *Multi-genome benchmark for simple and complex genome inversion detection*, 2026](https://link.springer.com/article/10.1186/s13059-026-04223-7).

These sources make a generic artifact-filter proposal non-distinct. The narrower question—whether a current geometry filter discards evidence for real, complex inversion alleles—remains important, but this public source intersection cannot test it in a common reference space.

## Finite alternative check — metadata only

No new source hunt or data acquisition is needed to decide this premise. The finite check is to read the already-published alignment-target description, run IDs, and truth-VCF reference metadata, then ask whether Breakinator released read classifications aligned to GRCh38 (or a GRCh38-relative call table) for these same runs. The Methods describe haplotype-assembly alignments, and no such GRCh38-aligned output is identified in the checked release metadata. **Result: STOP this test.** Do not download the 185.4 MB report archive or multi-gigabyte PAFs for this endpoint.

An alternative becomes eligible only if an already-existing, public result provides GRCh38-relative read alignments or event-support calls for the same reads, with the benchmark's independent inversion labels. No remapping is proposed here. Without that assay plane, there is no valid filter-loss endpoint in this source intersection.

**Source overlap still holds, but is insufficient:** the inversion benchmark supplement lists HG002 ONT runs `PAW70337` and `PAW71238`; these are the same run IDs used in Breakinator's HG002 ONT release. The inversion truth VCFs are small (Tier 2 about 6.2 KB; Tier 1 about 5.7 KB). Breakinator publishes a 185.4 MB report archive with classifications; its corresponding PAF inputs are multi-gigabyte. The reports are in personal-reference coordinates, so their size and run match do not make them suitable for the proposed endpoint. [Inversion truth VCFs](https://zenodo.org/records/17624133) · [Breakinator reports and alignments](https://zenodo.org/records/17567592).

**Finite cost:** metadata review only; no archive or PAF download, no analysis, and no new alignment. The proposed filter-loss study is closed unless a suitable GRCh38-relative result already exists.

## Limits and scope

- The benchmark provides orthogonally labeled complex **germline** inversion truth, not low-VAF mosaic truth. The current Breakinator alignments cannot establish filter-induced loss or retention of that truth; a suitable GRCh38-relative read result could. Neither source measures sensitivity at low allele fraction.
- A published Strand-seq mosaic inversion is not a matched long-read artifact control, so it does not make this test a mosaic benchmark. [Grimes et al., *Nature Genetics*, 2024](https://www.nature.com/articles/s41588-024-01754-2).
- No specific genomic spike-in with a published inversion/strand-switch truth label surfaced in this bounded pass. Do not broaden the source hunt on that basis.
- Exact sample/run overlap is established. It does not imply comparable reference-relative support.
- Even a future positive result on a matched assay would not show that chimeras are novel or establish a clinical claim.

## Search boundary and sources

Three targeted Exa queries were run, with ten result slots each: artifact-filter methods; independently validated inversion controls; and low-VAF/mosaic events versus artifacts. Thirty result slots were screened; the three primary methods/data papers above were checked in detail. The supplement and the released small truth VCF metadata were checked for source-run overlap. No broad catalogue search was done.

The scout did not inspect the retained case's raw data, download the Breakinator report archive or PAFs, run an experiment, write code, install software, launch a job, or make Git changes. Only this note is in scope.
