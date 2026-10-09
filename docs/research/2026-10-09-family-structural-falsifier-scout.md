# Family structural-allele falsifier scout

Date: 2026-10-09

## Decision

Test one specific inheritance assumption: **does a current ordinary germline caller miss a real, low-level parental mosaic that a mosaic-aware mode can detect?** A miss could make a child’s inherited allele look de novo and hide a parental transmission mechanism.

The best supported case is a 3,407-bp full-length SVA insertion reported in child G3-NA12887. The paper reports the insertion on the child’s maternal haplotype and about 11% read support in parent G2-NA12878. It reports that the insertion is absent from the grandparental transmitting haplotype, consistent with a postzygotic event in G2. Supplementary Table 10 identifies the event as `chr3-71589910-INS-3407`, at chr3:71,589,909–71,593,317 in T2T-CHM13. Its row marks maternal inheritance and lists pggb-hifiasm, pggb-verkko, and pav as source callers. This gives an observed family mechanism and a direct measurement target. It does **not** show that a current caller fails. That is what the test must determine. [Primary paper](https://doi.org/10.1038/s41586-025-08922-2), [Supplementary Table 10](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-025-08922-2/MediaObjects/41586_2025_8922_MOESM12_ESM.xlsx)

```text
G1 transmitting haplotype: insertion absent (reported)
                     │
                     ▼  postzygotic origin in G2 is the paper's interpretation
G2 NA12878: ~11% read support
                     │
                     ▼
G3 NA12887: 3,407-bp SVA on maternal haplotype (reported)

Test: does current germline mode find the parent allele, and does --mosaic change that call?
```

The consequence is specific: the child’s event may be attributed to a transmitting parent’s mosaic rather than first arising in the child. That can change the inheritance mechanism and recurrence interpretation. This is not a Mendelian-consistency score. It is not evidence of prevalence, and it does not establish a current-method failure.

## One-case falsifier

Use the public, indexed HiFi BAM for the same parent, NA12878, mapped to T2T-CHM13. This matches the supplementary-table coordinates. The exact object is [NA12878.CHM13.haplotagged.bam](https://platinum-pedigree-data.s3.amazonaws.com/data/hifi/mapped/CHM13/NA12878.CHM13.haplotagged.bam); its public index is [NA12878.CHM13.haplotagged.bam.bai](https://platinum-pedigree-data.s3.amazonaws.com/data/hifi/mapped/CHM13/NA12878.CHM13.haplotagged.bam.bai). The [Platinum Pedigree data repository](https://github.com/Platinum-Pedigree-Consortium/Platinum-Pedigree-Datasets) lists the public data and the controlled-access samples.

Run one locus-level comparison with current **Sniffles2 2.8.1**: its ordinary germline mode versus its documented `--mosaic` mode, on the same NA12878 reads at T2T-CHM13 chr3:71,589,909–71,593,317. Sniffles2 documents both the ordinary long-read call and mosaic mode in its [official README](https://github.com/fritzsedlazeck/Sniffles/blob/master/README.md). Keep the comparison fixed to this locus, sample, reference, and caller version.

The paper’s published Sniffles version was 0.12.0. The proposed 2.8.1 run is a current-method test, not a claim about the paper’s older call.

Read the result against the published event identity: breakpoint and inserted sequence should match the reported SVA, not just its approximate length. The outcomes are simple:

- If germline mode misses the event but mosaic mode calls the matching allele, the ordinary germline call alone does not rule out this parental transmission mechanism.
- If germline mode already calls the matching parental allele, this case does not support that failure for Sniffles2.
- If neither mode calls it, the observation remains unresolved for this caller and locus. Do not generalize from one case.

The same-sample germline run is the closest ordinary-method control for the mosaic-mode run. The published grandparental haplotype is an additional pedigree-negative observation. No donor replication or campaign-level power threshold is needed to decide this single-case falsifier.

## Data access and boundary

The T2T-CHM13 BAM object is 203,640,216,494 bytes; the BAI is 37,783,472 bytes. A metadata-only HTTP check confirmed the BAM supports byte ranges and the index is public. No genomic reads were downloaded, and no caller was run. **Inference:** the index and range support should allow a small event-centered extraction without staging the full BAM; this extraction path was not tested.

The main text does not state the exact coordinate. I checked the single matching row in Supplementary Table 10 through Firecrawl. The row supplies the T2T-CHM13 event interval and SV ID. A targeted read query is therefore defined without a coordinate conversion. No workbook or genomic reads were saved locally. Do not substitute a whole-genome download.

The child’s reads and assemblies, plus whole-family variant calls, are controlled-access. So this is a parent-side falsifier anchored by the published child assembly and haplotype result. It is **not** a full trio rerun or an independent reanalysis of the child. The observation is still useful: it tests whether a current ordinary caller sees the specific parental mosaic that the paper reports. It cannot establish how often this happens.

## Evidence and search limits

- Exa discovery used three distinct queries, with 10 requested result slots per query (30 requested). The merged tool output was truncated before result-card counts could be audited. The actual returned count is unknown; I do not treat 30 as the number returned or read. Exa fetches defaulted to 3,000 characters and exposed front matter only, so they do not count as full-text reads.
- Firecrawl live markdown supplied full article bodies for three distinct primary studies: the selected 2025 four-generation pedigree paper (291,183 characters); a 2025 complex de novo SV study (131,843 characters); and a 2026 57-trio optical-mapping preprint (183,633 characters). I also checked only the matching row in the selected paper’s Supplementary Table 10 to recover the event interval. The latter two studies did not provide this falsifier: one concerns complex event architecture with restricted raw data; the other reports orthogonally checked trio calls but makes data available on request. [Complex dnSV paper](https://doi.org/10.1038/s41467-025-64722-2); [57-trio OGM preprint](https://doi.org/10.64898/2026.01.16.26344264).
- A separate 2026 trio paper was accessible only as an abstract and data-availability statement; I did not count it as a full-body validation. Scite full-text access returned `INVALID_ARGUMENT` for the paid-plan/trial gate. I did not request a billing change. Life Sciences Literature execution scripts or connectors were not exposed in this session, so Firecrawl and official source pages were used instead.
- Prior family/mosaic and strategy-reset notes were reviewed. This is a different, specifically reported event from the earlier REACH000479 sperm-mosaic lead. The HG008 repeat-rescue package remains closed and incomplete; it is not treated as a biological null. No DeepSV foundation, SSL claim, acquisition, native caller run, or broader campaign is proposed here.

**Scope of claim:** a supported outcome would justify reporting this one current-caller result and its inheritance implication. It would not establish prevalence, novelty, or a general defect in structural-variant genotyping.
