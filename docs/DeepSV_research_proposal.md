# Extending DeepSV: A Literature Review, Gap Analysis, and Novel Research Proposal for Deep-Learning Structural-Variant Detection

*Scope: structural-variant (SV) detection with a focus on deletions from short- and long-read sequencing, deep-learning input representations and architectures (CNN, Transformer, Vision Transformer, attention, Mamba/state-space models, graph neural networks), self-supervised and foundation-model approaches, and multi-scale / multi-modal / representation learning. Literature coverage 2015–2026, centred on the period since DeepSV (Cai et al., 2019).*

All in-text citations link to a DOI; a consolidated reference list appears at the end. Sixty-two primary and review works were retrieved and screened through OpenAlex and the DeepSV/DeepVariant citation graphs; the survey table (Part 1) contains the core set most relevant to extending DeepSV.

---

## Executive summary

DeepSV ([Cai et al. 2019](https://doi.org/10.1186/s12859-019-3299-y)) recast long-deletion calling as image classification, hand-crafting an RGB pileup image in which each base's colour encodes four binary alignment signatures (paired, discordant, mapping-quality, split) and training a CNN on 1000 Genomes data. It was an early demonstration — following DeepVariant ([Poplin et al. 2018](https://doi.org/10.1038/nbt.4235)) — that the image-classification paradigm generalizes from SNPs to structural variants. Six years on, three of its core design choices have aged poorly: (i) the **hand-designed, static RGB encoding** that discards information and cannot adapt to context; (ii) the **single fixed-length 50-bp window**, which cannot simultaneously resolve base-precise breakpoints and span kilobase-scale events; and (iii) the **fully supervised, deletion-only, short-read-only** scope that ignores the enormous unlabeled BAM corpus now available and the multi-platform truth sets built since 2019.

The field has moved decisively toward long-read imaging (SVision, Cue), transformer and graph encoders for reads (SVHunter, GKNnet), and reference-sequence DNA foundation models (Nucleotide Transformer, DNABERT-2). Yet a specific combination remains unoccupied: **a self-supervised, alignment-aware representation of the read pileup that replaces the hand-crafted RGB encoding with a learned one, coupled to a multi-scale encoder that adapts its genomic context to the event, and calibrated with uncertainty for short-read SV discovery.** This document surveys the literature (Part 1), dissects DeepSV (Part 2), performs a citation-grounded novelty check on eighteen candidate directions (Part 3), ranks twenty research gaps (Part 4), proposes ten candidate projects (Part 5), selects and details the strongest (Part 6), stress-tests its novelty (Part 7), and delivers a full journal-style proposal (Final Output).

---

## Part 1 — Literature survey

The table groups sixty-two works into six themes: (A) the image-based variant-calling lineage DeepSV belongs to; (B) deep-learning SV callers and filters published since; (C) classical non-DL callers that serve as baselines; (D) benchmarks and truth sets; (E) reviews; and (F) foundation models and architecture backbones that a next-generation method would draw on. "Research Gap" names the specific opening each work leaves for a DeepSV successor.


#### A. Image-based variant calling (DeepSV lineage)

| # | Paper (year, venue) | Dataset | Input Representation | Model Architecture | SV Types | Platform | Strengths | Weaknesses / Limitations | Research Gap |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [A universal SNP and small-indel variant caller using deep ne](https://doi.org/10.1038/nbt.4235) — Poplin et al. 2018, *Nature Biotechnology* | GIAB (HG001-007), 1000G | Pileup RGB image (read base/qual/strand channels) | Inception-v2 CNN | SNV, short indel | Illumina short-read; extended to PacBio/ONT | First image-based caller; state-of-art SNP accuracy; platform-transferable | Small indels only (<50 bp); heavy compute; fixed image window; Not designed for SVs; localized pileup cannot span long events | No SV support; static RGB encoding |
| 2 | [DeepSV: accurate calling of genomic deletions from high-thro](https://doi.org/10.1186/s12859-019-3299-y) — Cai et al. 2019, *BMC Bioinformatics* | 1000 Genomes Phase 3 (20 individuals, chr1-22) | Hand-crafted RGB pileup image; base color modulated by 4 binary signature bits (paired, discordant, mapQ>20, split) | Custom CNN (TensorFlow), 256x256 images | Long deletions (>50 bp) | Illumina short-read (10x-60x) | Extends image-calling to SVs; integrates depth+split+discordant in one image; strong precision vs 8 callers | Deletions only; k-means clustering candidate step is brittle; manual color scheme; Fixed 50 bp windows; single-scale; short-read only; no long-read/CNN-alternative | The whole DeepSV design space this project targets |
| 3 | [Training Genotype Callers with Neural Networks](https://doi.org/10.1101/097469) — Torracinta & Campagne 2016, *bioRxiv (preprint)* | Simulated + GIAB | Read tensor | Feedforward/CNN | SNV genotype | Illumina | Early proof NN can learn genotype calling | Toy scope; No SV | No SV |
| 4 | [Clairvoyante: a multi-task convolutional deep neural network](https://doi.org/10.1101/310458) — Luo et al. 2018, *bioRxiv (preprint)* | GIAB HG001 | Pileup summary tensor (base counts per position) | Multi-task CNN | SNV, indel | Illumina; PacBio; ONT | First multi-task NN caller across platforms; fast | Small variants only; tensor summary loses read-level detail; No SV; limited context window | No SV support |
| 5 | [A multi-task convolutional deep neural network for variant c](https://doi.org/10.1038/s41467-019-09025-z) — Luo et al. 2019, *Nature Communications* | GIAB, single-molecule reads | Pileup summary tensor | Multi-task CNN (Clairvoyante) | SNV, indel | PacBio, ONT | Runs on noisy long reads; multi-task genotype output | <50 bp variants; summary tensor; No SV; limited receptive field | No SV support |
| 6 | [Symphonizing pileup and full-alignment for deep learning-bas](https://doi.org/10.1038/s43588-022-00387-x) — Zheng et al. 2022, *Nature Computational Science* | GIAB, ONT/PacBio HiFi | Pileup + full-alignment representation, two-stage | Pyramid CNN (Clair3) | SNV, indel | ONT, PacBio HiFi, Illumina | SOTA long-read small-variant accuracy; combines pileup and full-alignment | Small variants; not SV-aware; Two representations hand-designed; no SV | No SV; representation still engineered |
| 7 | [Haplotype-aware variant calling with PEPPER-Margin-DeepVaria](https://doi.org/10.1038/s41592-021-01299-w) — Shafin et al. 2021, *Nature Methods* | GIAB, ONT | Pileup image (DeepVariant) + haplotagging | RNN (PEPPER) + CNN (DeepVariant) + Margin | SNV, indel | ONT | Haplotype-aware; nanopore small-variant SOTA in 2021 | No SV; pipeline complexity; SV out of scope | No SV support |
| 8 | [Accurate, scalable cohort variant calls using DeepVariant an](https://doi.org/10.1093/bioinformatics/btaa1081) — Yun et al. 2020, *Bioinformatics* | GIAB cohorts | DeepVariant pileup + gVCF merge | CNN + GLnexus joint genotyping | SNV, indel | Illumina | Scalable cohort joint calling | Small variants only; No SV | No SV support |
| 9 | [DeNovoCNN: a deep learning approach to de novo variant calli](https://doi.org/10.1093/nar/gkac511) — Khazeeva et al. 2022, *Nucleic Acids Research* | In-house trios | Parent-child pileup images | CNN (DeNovoCNN) | De novo SNV/indel | Illumina | Trio image encoding for de novo detection | Small variants; trio-specific; No SV; needs trios | Trio-conditioned SV calling unexplored |

#### B. Deep-learning SV callers & filters

| # | Paper (year, venue) | Dataset | Input Representation | Model Architecture | SV Types | Platform | Strengths | Weaknesses / Limitations | Research Gap |
|---|---|---|---|---|---|---|---|---|---|
| 10 | [LSnet: detecting and genotyping deletions using deep learnin](https://doi.org/10.3389/fgene.2023.1189775) — Luo et al. 2023, *Frontiers in Genetics* | 1000G, GIAB | Pileup-style image of alignment signals | CNN (LSnet) | Deletions + genotyping | Illumina short-read | Short-read DEL detection + genotyping; DeepSV-like lineage | Deletions only; single-scale image; Fixed window; static encoding; CNN-only | Direct successor space to DeepSV: multi-scale/attention/learnable encoding |
| 11 | [ResNet Combined with Attention Mechanism for Genomic Deletio](https://doi.org/10.3103/s0146411624700147) — Yang et al. 2024, *Automatic Control and Computer Sciences* | 1000G deletion set | Pileup image (DeepSV-style) | ResNet + attention module | Deletions | Illumina short-read | Adds attention + residual to image DEL calling | Deletions only; incremental over DeepSV; Still fixed RGB image; single-scale | Confirms attention helps but leaves encoding/multi-scale open |
| 12 | [Automated filtering of genome-wide large deletions through a](https://doi.org/10.1016/j.ymeth.2022.08.001) — Hu et al. 2022, *Methods* | 1000G large deletions | Pileup image | Ensemble CNN | Large deletions | Illumina short-read | Ensembling improves DEL precision | Deletions only; ensemble cost; Fixed image; no multi-scale | Single unified multi-scale model |
| 13 | [sv-channels: filtering genomic deletions using one-dimension](https://doi.org/10.1101/2024.10.17.618894) — Santuari et al. 2024, *bioRxiv (preprint)* | GIAB, 1000G | 1-D per-position signal channels (depth/split/discordant) | 1-D CNN (sv-channels) | Deletions | Illumina short-read | Lightweight 1-D encoding avoids RGB overhead; filters deletions | Deletions; filter-oriented; Fixed channels; single-scale | Multi-scale, learnable 1-D encoding; more SV types |
| 14 | [An ensemble deep learning framework to refine large deletion](https://doi.org/10.1109/bibm52615.2021.9669571) — Hu et al. 2021, *2021 IEEE International Conference on Bioinformatics and Biomedicine (BIBM)* | Linked-read data | Barcode/alignment features image | Ensemble deep learning | Large deletions | 10x linked-reads | Uses linked-read barcodes for DEL refinement | Linked-read specific; refine only; Platform-specific | General learnable representation across platforms |
| 15 | [MaxDEL: Accurate and Efficient Calling of Genomic Deletions ](https://doi.org/10.2174/1574893618666230224160716) — Yu et al. 2023, *Current Bioinformatics* | Single-molecule reads | Alignment features | ML/DL hybrid (MaxDEL) | Deletions | Long-read | Efficient DEL calling from single-molecule reads | Deletions; long-read; Feature engineering | Learnable representation, more SV types |
| 16 | [NPSV-deep: a deep learning method for genotyping structural ](https://doi.org/10.1093/bioinformatics/btae129) — Linderman et al. 2024, *Bioinformatics* | GIAB HG002-007 | Simulated-read pileup image around candidate SV | CNN (NPSV-deep) | SV genotyping (DEL/INS) | Illumina short-read | Genotyping via in-silico simulation matching; short-read | Genotyping only (needs input calls); simulation cost; Fixed image; per-locus simulation | Discovery (not just genotyping); learnable representation |
| 17 | [BreakNet: detecting deletions using long reads and a deep le](https://doi.org/10.1186/s12859-021-04499-5) — Luo et al. 2021, *BMC Bioinformatics* | HG002 GIAB | Read-alignment matrix from long reads | CNN + BiLSTM (BreakNet) | Deletions | ONT, PacBio | Combines CNN + sequence model for long-read DEL | Deletions only; long-read; Fixed window; supervised | Other SV types; short-read; attention |
| 18 | [cnnLSV: detecting structural variants by encoding long-read ](https://doi.org/10.1186/s12859-023-05243-x) — Ma et al. 2023, *BMC Bioinformatics* | HG002, simulated | Encoded long-read alignment image (multi-feature) | CNN (cnnLSV) | DEL, INS, DUP, INV | PacBio, ONT | Multi-type SV from long reads; filters caller output | Long-read; depends on upstream callset; Fixed encoding | Short-read; end-to-end discovery |
| 19 | [SVcnn: an accurate deep learning-based method for detecting ](https://doi.org/10.1186/s12859-023-05324-x) — zheng & Shang 2023, *BMC Bioinformatics* | HG002, simulated | CIGAR/alignment-derived image | CNN (SVcnn) | DEL, INS, DUP, INV | PacBio, ONT | Accurate long-read multi-type SV | Long-read only; Fixed image; supervised | Short-read; representation learning |
| 20 | [SVision: a deep learning approach to resolve complex structu](https://doi.org/10.1038/s41592-022-01609-w) — Lin et al. 2022, *Nature Methods* | HG002, simulated complex SV | Multi-channel similarity/CIGAR image from long reads | CNN + segmentation (SVision) | Complex SVs, DEL/INS/DUP/INV/translocation | PacBio, ONT | Resolves complex/nested SVs; graph-like output; image from long reads | Long-read only; needs high coverage; Image still hand-designed; supervised | Short-read complex-SV imaging; learnable encoding |
| 21 | [De novo and somatic structural variant discovery with SVisio](https://doi.org/10.1038/s41587-024-02190-7) — Wang et al. 2024, *Nature Biotechnology* | HG002, tumor-normal | Comparative multi-channel image (case vs control) | CNN (SVision-pro), instance segmentation | Somatic/de novo complex SV | PacBio, ONT | De novo & somatic complex SV; reference-free comparison | Long-read only; compute-heavy; Hand-designed comparative image | Somatic short-read learnable representation |
| 22 | [Cue: a deep-learning framework for structural variant discov](https://doi.org/10.1038/s41592-023-01799-x) — Popic et al. 2023, *Nature Methods* | HG002, simulated | 2D image: read features binned to genomic intervals | CNN (stacked hourglass, keypoint detection) | DEL, DUP, INV, INS, translocation | Illumina, long-read | Multi-SV-type; single model; genotyping; image keypoints for breakpoints | Coarse binning loses base resolution; Fixed bin/window; encoding fixed | Adaptive/multi-scale binning; learnable encoding |
| 23 | [SVHunter: long-read-based structural variation detection thr](https://doi.org/10.1093/bib/bbaf203) — Gao et al. 2025, *Briefings in Bioinformatics* | HG002, long-read benchmarks | Alignment signal sequence tokens | Transformer (SVHunter) | DEL, INS, DUP, INV | ONT, PacBio | Transformer attention over long-read signals; strong recall | Long-read; large model; Tokenization hand-designed; no pretraining | Short-read transformer; self-supervised pretraining |
| 24 | [GKNnet: an relational graph convolutional network-based meth](https://doi.org/10.1093/bib/bbaf200) — Guo et al. 2025, *Briefings in Bioinformatics* | Long-read SV benchmarks | Read/feature graph with knowledge features | Relational Graph Convolutional Network (GKNnet) | SV detection/genotyping | Long-read | Graph representation of reads; knowledge-augmented | Long-read; graph construction hand-designed; Supervised; feature engineering in graph | Short-read GNN; learnable graph construction |
| 25 | [CSV-Filter: a deep learning-based comprehensive structural v](https://doi.org/10.1093/bioinformatics/btae539) — Xia et al. 2024, *Bioinformatics* | HG002, long-read | Multi-type alignment image | CNN filter (CSV-Filter) | SV filtering (all types) | PacBio, ONT | Reduces false positives across callers | Filter only; needs input calls; Fixed representation | End-to-end learnable discovery+filter |
| 26 | [SVDF: enhancing structural variation detect from long-read s](https://doi.org/10.1093/bib/bbae336) — Hu et al. 2024, *Briefings in Bioinformatics* | Long-read SV sets | Alignment features + autoencoder embedding | Autoencoder + classifier (SVDF) | SV filtering | ONT, PacBio | Self-supervised autoencoder to filter SVs | Filter only; long-read; Not full discovery; supervised head | Self-supervised discovery on short read |
| 27 | [Indel calling from ONT sequencing data of family trios via s](https://doi.org/10.1093/bib/bbaf430) — Shi et al. 2025, *Briefings in Bioinformatics* | ONT family trios | Alignment tokens with sparse attention | Sparse-attention Transformer | Indels (family trios) | ONT | Sparse attention for long-context indel calling in trios | Indel/trio scope; Tokenization fixed; trio-specific | SV-scale sparse attention; short-read |
| 28 | [Concod: an effective integration framework of consensus-base](https://doi.org/10.1504/ijdmb.2017.10005212) — Cai et al. 2017, *Int. J. Data Mining and Bioinformatics* | 1000G | Manually selected consensus features | SVM (Concod) | Deletions | Illumina short-read | Consensus-based ML DEL calling; DeepSV's ML baseline | Manual feature selection; SVM ceiling; Not deep; feature-limited | Superseded by deep learning; shows feature-engineering bottleneck |

#### C. Classical (non-DL) SV callers & genotypers — baselines

| # | Paper (year, venue) | Dataset | Input Representation | Model Architecture | SV Types | Platform | Strengths | Weaknesses / Limitations | Research Gap |
|---|---|---|---|---|---|---|---|---|---|
| 29 | [Long-read-based human genomic structural variation detection](https://doi.org/10.1186/s13059-020-02107-y) — Jiang et al. 2020, *Genome biology* | HG002, simulated | Alignment signatures (split/clip/depth) | Heuristic clustering (cuteSV) | DEL, INS, DUP, INV, BND | ONT, PacBio | Fast, accurate long-read SV; widely used baseline | Not learning-based; parameter sensitive; Signature heuristics; no learning | Learning-based replacement of heuristics |
| 30 | [Detection of mosaic and population-level structural variants](https://doi.org/10.1038/s41587-023-02024-y) — Smolka et al. 2024, *Nature Biotechnology* | HG002, population, mosaic | Split/alignment signatures | Heuristic + Gaussian modeling (Sniffles2) | All SV types incl. mosaic | ONT, PacBio | Population & mosaic SV; scalable; standard baseline | Heuristic; not end-to-end learned; Manual signature model | Deep-learning mosaic/population SV |
| 31 | [NanoVar: accurate characterization of patients’ genomic stru](https://doi.org/10.1186/s13059-020-01968-7) — Tham et al. 2020, *Genome biology* | Patient genomes, simulated | Alignment signatures + small NN filter | Heuristic + shallow NN (NanoVar) | All SV types | ONT low-depth | Low-depth nanopore SV; some NN filtering | Mostly heuristic; Shallow model | Deep representation learning |
| 32 | [SVDSS: structural variation discovery in hard-to-call genomi](https://doi.org/10.1038/s41592-022-01674-1) — Denti et al. 2022, *Nature Methods* | HG002, hard regions | Sample-specific strings (assembly-free) | Specific String algorithm (SVDSS) | DEL, INS | PacBio HiFi | Hard-to-call regions; assembly-free | Not learning-based; Algorithmic, no learning | Learning in hard/repetitive regions |
| 33 | [Paragraph: a graph-based structural variant genotyper for sh](https://doi.org/10.1186/s13059-019-1909-7) — Chen et al. 2019, *Genome biology* | 1000G, GIAB | Graph alignment of reads to SV alleles | Graph genotyper (Paragraph) | SV genotyping | Illumina short-read | Short-read graph genotyping of known SVs | Genotyping only; needs SV catalog; No discovery; no learning | Learnable graph discovery on short reads |
| 34 | [Pangenomics enables genotyping of known structural variants ](https://doi.org/10.1126/science.abg8871) — Sirén et al. 2021, *Science* | 5202 genomes | Pangenome graph | PanGenie k-mer genotyper | SV genotyping | Illumina short-read | Population-scale pangenome genotyping | Genotyping only; catalog-dependent; No discovery; no deep learning | Deep pangenome-aware discovery |
| 35 | [CNVkit: Genome-Wide Copy Number Detection and Visualization ](https://doi.org/10.1371/journal.pcbi.1004873) — Talevich et al. 2016, *PLoS Computational Biology* | Targeted panels, WGS | Read-depth bins | Statistical CBS (CNVkit) | CNV / large DEL-DUP | Illumina | Standard CNV baseline; depth-based | CNV only; low breakpoint resolution; No learning; depth only | Deep multi-signal CNV |
| 36 | [VolcanoSV enables accurate and robust structural variant cal](https://doi.org/10.1038/s41467-024-51282-0) — Luo et al. 2024, *Nature Communications* | HG002, diploid | Phased assembly + alignment | Assembly-based (VolcanoSV) | All SV types | PacBio HiFi | Accurate diploid SV via local assembly | Long-read; compute-heavy; Not learning-based | Learning + assembly hybrid |
| 37 | [Deciphering the exact breakpoints of structural variations u](https://doi.org/10.1038/s41467-023-35996-1) — Chen et al. 2023, *Nature Communications* | HG002, long-read | Long-read alignment at breakpoints | Algorithmic breakpoint refinement | SV breakpoints | PacBio, ONT | Base-precise breakpoints from long reads | Long-read; not learning-based; Algorithmic | Learnable base-resolution breakpoints on short read |

#### D. Benchmarks, truth sets & resources

| # | Paper (year, venue) | Dataset | Input Representation | Model Architecture | SV Types | Platform | Strengths | Weaknesses / Limitations | Research Gap |
|---|---|---|---|---|---|---|---|---|---|
| 38 | [A robust benchmark for detection of germline large deletions](https://doi.org/10.1038/s41587-020-0538-8) — Zook et al. 2020, *Nature Biotechnology* | HG002 GIAB Tier1 | N/A | Benchmark truth set | DEL, INS | Multi-platform | Gold-standard SV truth set for evaluation | Benchmark only; Limited to HG002 | Reference truth for any new method |
| 39 | [Comprehensive evaluation of structural variation detection a](https://doi.org/10.1186/s13059-019-1720-5) — Kosugi et al. 2019, *Genome biology* | GIAB, simulated benchmark | N/A | Benchmark of 69 callers | All SV | Short-read | Comprehensive benchmark; shows no caller dominates | No new method | Motivates ensemble/learning approaches |
| 40 | [Multi-platform discovery of haplotype-resolved structural va](https://doi.org/10.1038/s41467-018-08148-z) — Chaisson et al. 2019, *Nature Communications* | HGSVC (9 genomes) | Multi-platform integration | Ensemble of callers | All SV | Illumina, PacBio, Strand-seq | Haplotype-resolved multi-platform SV resource | No learning method | Rich multi-modal training data source |
| 41 | [Haplotype-resolved diverse human genomes and integrated anal](https://doi.org/10.1126/science.abf7117) — Ebert et al. 2021, *Science* | HGSVC 64 haplotypes | Multi-platform | Ensemble/assembly | All SV | Multi-platform | Diverse haplotype-resolved SV catalog | No learning method | Diverse ground-truth for training |
| 42 | [Comprehensive evaluation of structural variant genotyping me](https://doi.org/10.1186/s12864-022-08548-y) — Duan et al. 2022, *BMC Genomics* | HG002, long-read | N/A | Benchmark of genotypers | SV genotyping | Long-read | Evaluates SV genotyping methods | Benchmark only | Genotyping accuracy gap |

#### E. Reviews & surveys

| # | Paper (year, venue) | Dataset | Input Representation | Model Architecture | SV Types | Platform | Strengths | Weaknesses / Limitations | Research Gap |
|---|---|---|---|---|---|---|---|---|---|
| 43 | [Structural variant calling: the long and the short of it](https://doi.org/10.1186/s13059-019-1828-7) — Mahmoud et al. 2019, *Genome biology* | Review | N/A | N/A (review) | All SV | Short & long read | Authoritative review of short vs long read SV tradeoffs | No new method | Frames the short-read sensitivity gap |
| 44 | [Variant calling and benchmarking in an era of complete human](https://doi.org/10.1038/s41576-023-00590-0) — Olson et al. 2023, *Nature Reviews Genetics* | Review, T2T era | N/A | Review | All variants | All platforms | Reviews benchmarking with complete genomes | No new method | Highlights evaluation gaps in hard regions |
| 45 | [A survey of algorithms for the detection of genomic structur](https://doi.org/10.1038/s41592-023-01932-w) — Ahsan et al. 2023, *Nature Methods* | Survey | N/A | Survey of long-read SV algorithms | All SV | Long-read | Systematic survey of long-read SV methods | No new method | Maps current algorithmic landscape/gaps |
| 46 | [Tradeoffs in alignment and assembly-based methods for struct](https://doi.org/10.1038/s41467-024-46614-z) — Liu et al. 2024, *Nature Communications* | HG002, assemblies | N/A | Comparison of alignment vs assembly | All SV | Long-read | Quantifies alignment vs assembly tradeoffs | No new method | Motivates hybrid representations |
| 47 | [Structural variant detection in cancer genomes: computationa](https://doi.org/10.1038/s41698-021-00155-6) — Belzen et al. 2021, *npj Precision Oncology* | Cancer genomes review | N/A | Review | Somatic SV | Short & long read | Reviews somatic SV computational challenges | No new method | Somatic SV detection under-served by DL |
| 48 | [A review of deep learning applications in human genomics usi](https://doi.org/10.1186/s40246-022-00396-x) — Alharbi & Rashid 2022, *Human Genomics* | Review | N/A | Review of DL in genomics | All variants | NGS | Broad DL-in-genomics review | No new method | Identifies SV-DL as immature area |
| 49 | [A comprehensive review of deep learning-based variant callin](https://doi.org/10.1093/bfgp/elae003) — Junjun et al. 2024, *Briefings in Functional Genomics* | Review | N/A | Review of DL variant callers | SNV/indel/SV | All | Focused review of DL variant calling | No new method | Notes scarcity of end-to-end DL SV callers |
| 50 | [Deep learning: new computational modelling techniques for ge](https://doi.org/10.1038/s41576-019-0122-6) — Eraslan et al. 2019, *Nature Reviews Genetics* | Review (Eraslan) | N/A | Review of DL architectures | N/A | N/A | Canonical DL-genomics methods review | No new method | Architectural playbook for genomics |
| 51 | [A primer on deep learning in genomics](https://doi.org/10.1038/s41588-018-0295-5) — Zou et al. 2018, *Nature Genetics* | Primer | N/A | Tutorial/primer | N/A | N/A | Accessible DL genomics primer | No new method | Foundational reference |
| 52 | [Transformer Architecture and Attention Mechanisms in Genome ](https://doi.org/10.3390/biology12071033) — Choi & Lee 2023, *Biology* | Review | N/A | Review of transformers/attention in genomics | N/A | All | Surveys attention/transformer use in genomics | No new method | Shows transformers underused for SV |

#### F. Foundation models, DNA language models & architecture backbones

| # | Paper (year, venue) | Dataset | Input Representation | Model Architecture | SV Types | Platform | Strengths | Weaknesses / Limitations | Research Gap |
|---|---|---|---|---|---|---|---|---|---|
| 53 | [DNABERT: pre-trained Bidirectional Encoder Representations f](https://doi.org/10.1093/bioinformatics/btab083) — Ji et al. 2021, *Bioinformatics* | Human genome | k-mer tokenized DNA | BERT Transformer (DNABERT) | N/A (representation) | Reference sequence | First DNA BERT; transferable embeddings | No SV task; k-mer tokenization; Short context (512) | DNA-LM embeddings for SV unexplored |
| 54 | [DNABERT-2: Efficient Foundation Model and Benchmark For Mult](https://doi.org/10.48550/arxiv.2306.15006) — Zhou et al. 2023, *arXiv (Cornell University)* | Multi-species genomes | BPE tokenized DNA | Transformer (DNABERT-2) | N/A | Reference | Efficient multi-species DNA LM | No SV task; Sequence-only (no alignment) | Alignment-aware DNA-LM for SV |
| 55 | [Nucleotide Transformer: building and evaluating robust found](https://doi.org/10.1038/s41592-024-02523-z) — Dalla-Torre et al. 2024, *Nature Methods* | 3202 genomes, multi-species | Tokenized DNA | Transformer foundation model (Nucleotide Transformer) | N/A | Reference | Robust genomic foundation embeddings; benchmarked | No SV/alignment task; Reference-sequence only | Read-level foundation embeddings for SV |
| 56 | [DNA language models are powerful predictors of genome-wide v](https://doi.org/10.1073/pnas.2311219120) — Benegas et al. 2023, *Proceedings of the National Academy of Sciences* | Arabidopsis, human | DNA sequence | Convolutional LM (GPN) | Variant effect (SNV) | Reference | Unsupervised variant-effect prediction | SNV effects, not SV discovery; Sequence-only | SV effect/discovery via LM |
| 57 | [Genomic language models: opportunities and challenges](https://doi.org/10.1016/j.tig.2024.11.013) — Benegas et al. 2025, *Trends in Genetics* | Review | N/A | Review of genomic LMs | N/A | N/A | Reviews opportunities/challenges of genomic LMs | No new method | Notes LMs largely reference-only, not alignment-aware |
| 58 | [Evaluating the representational power of pre-trained DNA lan](https://doi.org/10.1186/s13059-025-03674-8) — Tang et al. 2025, *Genome biology* | Regulatory benchmarks | DNA sequence | Eval of pre-trained DNA LMs | N/A | Reference | Critically evaluates DNA-LM representational power | Eval only; regulatory focus | Cautions on DNA-LM utility; motivates task-specific models |
| 59 | [Mamba: Linear-Time Sequence Modeling with Selective State Sp](https://doi.org/10.48550/arxiv.2312.00752) — Gu & Dao 2023, *arXiv (Cornell University)* | LM/genomics benchmarks | Sequence tokens | Selective State Space Model (Mamba) | N/A | N/A | Linear-time long-sequence modeling; SSM backbone | General ML, not SV; Not applied to SV | Mamba/SSM for read-alignment SV modeling |
| 60 | [Predicting effects of noncoding variants with deep learning–](https://doi.org/10.1038/nmeth.3547) — Zhou & Troyanskaya 2015, *Nature Methods* | ENCODE, Roadmap | One-hot DNA sequence | Deep CNN (DeepSEA) | Noncoding variant effect | Reference | Landmark sequence-to-chromatin CNN | Regulatory, not SV; Sequence-only | — |
| 61 | [Predicting the sequence specificities of DNA- and RNA-bindin](https://doi.org/10.1038/nbt.3300) — Alipanahi et al. 2015, *Nature Biotechnology* | Protein/DNA binding data | One-hot sequence | CNN (DeepBind) | Binding specificity | Reference | Pioneering genomics CNN | Not variant calling | — |
| 62 | [Basset: learning the regulatory code of the accessible genom](https://doi.org/10.1101/gr.200535.115) — Kelley et al. 2016, *Genome Research* | ENCODE DNase | One-hot sequence | CNN (Basset) | Accessibility | Reference | Learns regulatory code with CNN | Not SV | — |


---

## Part 2 — DeepSV in detail

### 2.1 What DeepSV does, precisely

DeepSV ([Cai et al. 2019](https://doi.org/10.1186/s12859-019-3299-y)) calls **long deletions (>50 bp)** from Illumina short reads in three stages. First, a **denoising + clustering** stage: read depth is smoothed with a 61-bp sliding-window filter, and each genomic position is represented as a triple *(read depth, negated discordant-pair count, negated split-read count)*. A *k*-means clustering (k = 3) using a weighted Euclidean distance partitions positions into upstream / deletion / downstream clusters; the cluster with the minimum mean feature value is taken as the deletion body, and a two-pointer sweep refines the breakpoints. This step both proposes candidates and removes false positives from an input VCF. Second, a **visualization** stage: the reference is partitioned into non-overlapping 50-bp windows, and each window's pileup is rendered as a 256×256 RGB image. Each nucleotide gets a base colour (A = red, T = green, C = blue, G = black); the colour is then perturbed by four binary per-read features — *is-paired, concordant/discordant, mapping-quality > 20, split/not* — packed into the low-order colour bits, plus column-level counts of discordant and split reads. Third, a **CNN** (built in TensorFlow, batch size 128, trained on 1080Ti GPUs) classifies each image as deletion (1) or wild-type (0). It was benchmarked on 40 BAMs (20 individuals, YRI/CHB/CEU) from 1000 Genomes Phase 3, training on chromosomes 1–11 and testing on 12–22, and compared against Pindel, BreakDancer, DELLY, CNVnator, Breakseq2, Lumpy, GenomeStrip2, SVseq2, and the ML baseline Concod ([Cai et al. 2017](https://doi.org/10.1504/ijdmb.2017.10005212)).

### 2.2 Why it worked

Three factors explain its reported precision advantage (e.g. 0.72–0.93 precision across 12×–48× coverage, exceeding all eight callers at every coverage). **(1) Signature integration without manual weighting.** Classical callers each lean on one or two signatures — BreakDancer on discordant pairs, the original Pindel on split reads — and combining them requires choosing weights that are known to be brittle ([Kosugi et al. 2019](https://doi.org/10.1186/s13059-019-1720-5)). By painting depth, discordant-pair, and split-read evidence into a single image, DeepSV let the CNN learn the combination from data, echoing DeepVariant's core insight ([Poplin et al. 2018](https://doi.org/10.1038/nbt.4235)). **(2) Noise handling.** The sliding-window filter and clustering removed spurious depth fluctuations that would otherwise corrupt candidate generation — the paper shows a large drop in false positives after clustering. **(3) Breakpoint refinement.** The two-pointer sweep over the deletion cluster produced breakpoints "only up to a few base pairs" from truth in many cases, competitive with GenomeStrip2. **(4) Robustness across regimes.** Because the image integrates multiple signals, DeepSV degraded gracefully across coverage, deletion length, and population frequency where single-signature callers each failed in some regime.

### 2.3 Why it was innovative in 2019

DeepVariant had shown images work for SNPs and short indels, but SVs are qualitatively harder: they are **non-local** (the two ends of a discordant pair spanning a long deletion map thousands of bases apart) and carry **more heterogeneous signatures** than a SNP. DeepSV was among the first to demonstrate that the image paradigm could be *engineered* to capture these long-range, multi-signature phenomena, providing "a positive answer" to whether deep learning generalizes beyond small variants. In 2019 this was a genuine conceptual extension, not a mechanical re-application.

### 2.4 Assumptions that no longer hold

1. **"Short reads are the substrate."** In 2019 long reads were expensive and error-prone. Since then, long-read SV detection has become the reference-quality standard: cuteSV ([Jiang et al. 2020](https://doi.org/10.1186/s13059-020-02107-y)), Sniffles2 ([Smolka et al. 2024](https://doi.org/10.1038/s41587-023-02024-y)), and long-read imaging methods such as SVision ([Lin et al. 2022](https://doi.org/10.1038/s41592-022-01609-w)) now resolve events short reads cannot. DeepSV's short-read-only design is now a niche, though a valuable one given the vast existing short-read cohorts.
2. **"Labeled deletions are the ceiling of available signal."** DeepSV is fully supervised on 1000 Genomes calls. The field now has vastly larger unlabeled BAM corpora and self-supervised pretraining paradigms ([Ji et al. 2021](https://doi.org/10.1093/bioinformatics/btab083); [Dalla-Torre et al. 2024](https://doi.org/10.1038/s41592-024-02523-z)) that DeepSV cannot exploit.
3. **"A fixed 50-bp window is adequate."** SVs span 50 bp to >10 kb; DeepSV itself notes "a single pileup image cannot cover an entire deletion." The single-scale assumption is fundamentally mismatched to the length distribution of SVs.
4. **"Hand-designed RGB colour is a good code for alignment evidence."** The 64-combination colour table is an information bottleneck chosen by intuition, not learned; modern practice replaces such fixed encodings with learned embeddings.
5. **"The 1000 Genomes call set is ground truth."** GIAB Tier-1 SV benchmarks ([Zook et al. 2020](https://doi.org/10.1038/s41587-020-0538-8)) and haplotype-resolved HGSVC resources ([Ebert et al. 2021](https://doi.org/10.1126/science.abf7117)) are now the accepted truth sets, and the 2019 evaluation split (train chr1–11 / test chr12–22, same individuals) leaks population structure and is weaker than modern cross-sample protocols.

### 2.5 Outdated components

- **RGB image encoding** — superseded conceptually by learned read/pileup embeddings and by 1-D channel encodings that avoid the RGB overhead entirely ([Santuari et al. 2024](https://doi.org/10.1101/2024.10.17.618894)).
- **k-means candidate generation** — a brittle, unsupervised heuristic; modern callers use signature clustering with statistical models (Sniffles2) or learn candidate proposal end-to-end (Cue, [Popic et al. 2023](https://doi.org/10.1038/s41592-023-01799-x)).
- **Plain CNN backbone** — no attention, no long-range context; the field has since added attention/residual blocks ([Yang et al. 2024](https://doi.org/10.3103/s0146411624700147)), transformers ([Gao et al. 2025](https://doi.org/10.1093/bib/bbaf203)), and graph encoders ([Guo et al. 2025](https://doi.org/10.1093/bib/bbaf200)).
- **Fixed square 256×256 images at one scale** — cannot represent both base-precise breakpoints and multi-kb spans.
- **Deletion-only output** — no insertions, duplications, inversions, or translocations; no genotype confidence.

### 2.6 Limitations still unsolved today (for short reads)

Even with all the progress since, several DeepSV-era problems remain genuinely open for **short-read** data specifically: (i) **base-resolution breakpoints from short reads** remain hard — the long-read breakpoint-refinement work of [Chen et al. 2023](https://doi.org/10.1038/s41467-023-35996-1) does not transfer; (ii) **no learned, self-supervised representation of the short-read pileup** exists — DNA foundation models operate on the *reference sequence*, not on aligned reads with their quality/strand/clip signals ([Benegas et al. 2025](https://doi.org/10.1016/j.tig.2024.11.013)); (iii) **calibrated uncertainty** for SV calls is essentially absent across all callers, deep or classical; (iv) **multi-scale context** — jointly modelling the local breakpoint neighbourhood and the kilobase-scale event — has no clean solution in short-read SV imaging; and (v) **explainability** — DeepSV's images are visually interpretable but the model's decisions are not attributed to specific reads/signatures.

### 2.7 Every bottleneck, enumerated

| # | Bottleneck | Consequence | Where the field stands |
|---|---|---|---|
| B1 | Hand-crafted static RGB encoding | Information loss; not adaptive; intuition-chosen | No learned pileup encoder for short-read SV exists |
| B2 | Single fixed 50-bp window / one scale | Cannot span long SVs *and* localize breakpoints | Multi-scale imaging unaddressed for short-read SV |
| B3 | k-means candidate generation | Brittle to depth noise; unsupervised | End-to-end proposal exists only for long-read (Cue) |
| B4 | Plain CNN, no attention/long-range | Misses non-local discordant-pair evidence | Attention/transformer added piecemeal, not with learned encoding |
| B5 | Fully supervised, small labeled set | Cannot use unlabeled BAMs; data-hungry | Self-supervised BAM pretraining largely unexplored |
| B6 | Deletion-only | No INS/DUP/INV/BND; limited utility | Multi-type DL callers exist mostly for long-read |
| B7 | No calibrated uncertainty | Cannot triage/curate calls; unsafe for clinical use | Uncertainty-aware SV calling essentially absent |
| B8 | Short-read only; weak breakpoints | Low breakpoint resolution vs long-read | Unsolved for short reads |
| B9 | Weak evaluation split (same individuals) | Optimistic accuracy; population leakage | Modern GIAB/HGSVC cross-sample protocols available |
| B10 | Not explainable at read/signature level | Hard to trust/curate | Attribution for SV callers under-developed |

---

## Part 3 — Novelty check of candidate directions

Each direction below is rated **Published / Partially explored / Largely open**, with the specific prior work that determines the rating and what remains unexplored. Ratings reflect the literature retrieved for this review (2015–2026); "largely open" means no directly competing method surfaced, not a guarantee of absence.

**1. CNN + genomic (DNA sequence) models (hybrid).** *Partially explored.* Clair3 fuses a pileup CNN with a full-alignment representation ([Zheng et al. 2022](https://doi.org/10.1038/s43588-022-00387-x)) and GPN-style sequence models predict variant effects ([Benegas et al. 2023](https://doi.org/10.1073/pnas.2311219120)), but no method fuses a read-pileup CNN with reference-sequence *foundation-model embeddings* for SV discovery. **Open:** injecting a DNA-LM prior of the reference into short-read SV calling.

**2. CNN + Transformer hybrid for SV.** *Partially explored / bordering published.* BreakNet combines CNN with BiLSTM for long-read deletions ([Luo et al. 2021](https://doi.org/10.1186/s12859-021-04499-5)); ResNet+attention has been applied to short-read deletion prediction ([Yang et al. 2024](https://doi.org/10.3103/s0146411624700147)); SVHunter uses a full transformer over long-read signals ([Gao et al. 2025](https://doi.org/10.1093/bib/bbaf203)). **Open:** a CNN-tokenizer + transformer for *short-read* multi-type SV with a *learned* pileup encoding rather than hand-crafted images.

**3. Vision Transformer replacing the CNN.** *Largely open for SV.* ViTs are reviewed for genomics broadly ([Choi & Lee 2023](https://doi.org/10.3390/biology12071033)) but no SV caller in this review uses a ViT on pileup images. **Open — but low novelty ceiling:** a pure ViT swap is the "not merely replacing CNN with Transformer" trap the brief warns against.

**4. Multi-scale windows.** *Largely open.* DeepSV, LSnet ([Luo et al. 2023](https://doi.org/10.3389/fgene.2023.1189775)), and Cue ([Popic et al. 2023](https://doi.org/10.1038/s41592-023-01799-x)) all use a single fixed window/binning; Cue bins reads to fixed genomic intervals but does not model multiple scales jointly. **Open:** jointly encoding base-resolution and kilobase-scale context for short-read SV.

**5. Adaptive / dynamic genomic windows.** *Open.* No retrieved method selects window size/context per candidate event. **Open:** content-adaptive context selection driven by predicted event size.

**6. Learnable genomic representation (of reads).** *Partially explored.* SVDF learns an autoencoder embedding to *filter* long-read SVs ([Hu et al. 2024](https://doi.org/10.1093/bib/bbae336)); DNA-LMs learn reference-sequence embeddings ([Ji et al. 2021](https://doi.org/10.1093/bioinformatics/btab083); [Dalla-Torre et al. 2024](https://doi.org/10.1038/s41592-024-02523-z)). **Open:** an end-to-end learned encoder of the *aligned short-read pileup* (with quality/strand/clip/pair channels) for SV *discovery*.

**7. Learnable replacement for the RGB encoding.** *Open.* DeepSV's colour scheme is fixed; sv-channels replaces RGB with fixed 1-D channels ([Santuari et al. 2024](https://doi.org/10.1101/2024.10.17.618894)) but the channels are still hand-defined. **Open:** replacing the hand-crafted colour/channel code with a learned per-base/per-read embedding — a direct DeepSV successor.

**8. Self-supervised pretraining on BAM / aligned reads.** *Largely open.* Self-supervision dominates reference-sequence DNA-LMs but, in this review, no method pretrains on *aligned reads* (pileups) to learn a general SV-relevant representation. SVDF's autoencoder is the closest, and it is a supervised-adjacent filter, not a pretraining corpus. **Open — high value:** masked-pileup or contrastive pretraining on unlabeled BAMs.

**9. Contrastive learning for SV detection.** *Open.* No SV-specific contrastive method surfaced. **Open:** contrasting variant vs wild-type pileups, or augmentation-invariant pileup representations.

**10. Graph neural networks for SV.** *Partially explored.* GKNnet applies relational GCNs to (long-read) SV with knowledge features ([Guo et al. 2025](https://doi.org/10.1093/bib/bbaf200)); pangenome graph *genotypers* exist ([Chen et al. 2019](https://doi.org/10.1186/s13059-019-1909-7); [Sirén et al. 2021](https://doi.org/10.1126/science.abg8871)). **Open:** learned read-overlap graphs for *short-read* SV *discovery*.

**11. Retrieval-augmented SV detection.** *Open.* No retrieved work applies retrieval augmentation (querying a panel/database of known SV pileups at inference) to SV calling. **Open — but risky:** feasibility and benefit unproven.

**12. Foundation-model embeddings for SV.** *Partially explored (reference-only).* DNA foundation models are reference-sequence embeddings ([Dalla-Torre et al. 2024](https://doi.org/10.1038/s41592-024-02523-z); [Zhou et al. 2023](https://doi.org/10.48550/arxiv.2306.15006)); their utility is contested ([Tang et al. 2025](https://doi.org/10.1186/s13059-025-03674-8)). None is an *alignment-aware* foundation model. **Open:** a foundation model over aligned reads.

**13. Multi-modal fusion.** *Partially explored.* Clair3 fuses two representations; multi-platform integration resources exist ([Chaisson et al. 2019](https://doi.org/10.1038/s41467-018-08148-z)). **Open:** learned fusion of pileup image + reference-sequence embedding + long-range signature summary in one SV model.

**14. Uncertainty-aware SV detection.** *Largely open.* No retrieved SV caller reports calibrated predictive uncertainty. **Open — high value:** Bayesian/ensemble/evidential uncertainty for triage and clinical use.

**15. Explainable SV detection.** *Largely open.* Reviews cover XAI generally; no SV caller in this review provides read/signature-level attribution. **Open:** attribution mapping calls back to supporting reads/signatures.

**16. Dynamic context selection.** *Open.* Overlaps (5); no retrieved SV method learns which genomic context to attend to per event. **Open.**

**17. Hybrid CNN + Mamba.** *Open for SV.* Mamba/SSMs are established generally ([Gu & Dao 2023](https://doi.org/10.48550/arxiv.2312.00752)) but no SV caller in this review uses a state-space model. **Open:** SSM over long-range read/signature sequences to capture non-local discordant-pair evidence linearly.

**18. Hybrid Transformer + Mamba.** *Open for SV.* No genomics-SV instance retrieved. **Open — but at risk of being "architecture-swap" novelty** unless tied to a genuine representational advance.

**Summary of the novelty landscape.** The *architecture* axis (Transformer, ViT, GNN, attention, ResNet) is increasingly occupied — mostly on **long reads** (SVHunter, GKNnet, SVision, Cue) or as **filters** (CSV-Filter, SVDF). The **representation** axis for **short-read SV** — replacing DeepSV's hand-crafted RGB encoding with a *learned, self-supervised, alignment-aware* representation, and modelling **multiple scales** with **calibrated uncertainty** — is the least crowded and most consequential opening.

---

## Part 4 — Research gap analysis: top 20 gaps

Ranked by a combined score of novelty, feasibility for a university group, biological/computational importance, and fit for *Bioinformatics* / *Briefings in Bioinformatics*. Each gap satisfies the brief's constraints (novel, feasible, non-incremental, not a mere CNN→Transformer swap, solves a real limitation).

1. **Learned, self-supervised replacement for the hand-crafted pileup encoding (short-read SV).** DeepSV's RGB colour table is fixed and lossy (B1, B5). No method learns a general pileup representation from unlabeled BAMs for SV. *Highest value: attacks the single most outdated component and unlocks unlabeled data.*
2. **Multi-scale short-read SV representation.** Jointly resolve base-precise breakpoints and kilobase spans (B2). Unaddressed for short reads.
3. **Calibrated uncertainty for SV calls.** Predictive uncertainty for triage/clinical curation (B7). Essentially absent field-wide.
4. **Masked / contrastive pretraining on aligned reads.** A pretraining objective over pileups analogous to DNA-LMs but alignment-aware (B5). Open.
5. **Adaptive context selection per candidate event.** Window/context size chosen by predicted event size (B2, B8-context). Open.
6. **Multi-type SV from short reads with one learned model.** Move beyond deletion-only (B6) without long reads.
7. **Learned read-overlap graph for short-read SV discovery.** GNNs used for long-read/genotyping only; discovery on short reads open (B4).
8. **Fusion of reference DNA-LM prior with read pileup.** Give the caller a learned prior of what the reference "should" look like (multi-modal, novelty check #1/#13).
9. **State-space (Mamba) modelling of long-range signature sequences.** Capture non-local discordant-pair evidence in linear time (B4).
10. **Read/signature-level explainability for SV calls.** Attribution to supporting reads (B10).
11. **Base-resolution breakpoints from short reads via learned refinement.** Transfer the spirit of long-read breakpoint refinement to short reads (B8).
12. **Cross-sample / cross-population generalization protocol + method.** Fix DeepSV's leaky split (B9) with a method robust across ancestries.
13. **Label-noise-robust training for SV.** DeepSV acknowledges noisy breakpoints; principled noisy-label learning is unexplored for SV.
14. **Semi-supervised SV using unlabeled cohorts.** Exploit large unlabeled BAM collections alongside GIAB labels.
15. **Coverage-adaptive SV calling.** A single model robust from 5× to 60× without retraining (DeepSV retrains per regime).
16. **Somatic/mosaic SV from short reads with DL.** Under-served (B6; [Belzen et al. 2021](https://doi.org/10.1038/s41698-021-00155-6)).
17. **Foundation-model-style transfer across species/platforms for SV.** Pretrain once, fine-tune on new organisms/platforms.
18. **Active learning for SV truth-set curation.** Use uncertainty to select loci for expert review.
19. **Retrieval-augmented SV calling against a known-SV panel.** Higher risk, novel.
20. **Unified discovery+genotyping+filtering in one differentiable pipeline.** Replace DeepSV's separate k-means/CNN stages end-to-end (B3).

Gaps 1–5 cluster into a single coherent thesis: **a self-supervised, multi-scale, uncertainty-aware learned representation of the short-read pileup.** This cluster is the basis for the selected project.

---

## Part 5 — Ten candidate projects

Each entry is compressed to the brief's required fields. Novelty score (1–10) and publication probability are the author's calibrated estimates.

### P1 — PileupSSL: Self-supervised learned pileup representations for short-read SV
- **Motivation / gap:** DeepSV's fixed RGB encoding is the most outdated component and cannot use unlabeled BAMs (Gaps 1, 4). **Novelty:** first masked/contrastive pretraining on *aligned short-read pileups* + learned encoder replacing RGB. **Feasibility:** high — GIAB/1000G/HGSVC data public; single 24-GB GPU sufficient for short-read tiles. **Contribution:** a reusable pretrained pileup encoder + SV caller. **Datasets:** GIAB HG002-007, 1000G, HGSVC. **Software:** PyTorch, pysam, Truvari, samtools. **Hardware:** 1–2× A100/RTX-4090. **Risks:** pretraining may not beat supervised baseline; **defense:** ablate pretraining, show low-label regime gains. **Reviewer criticism:** "just BERT on pileups"; **defense:** alignment-aware objective + SV-specific evaluation + calibration. **Baselines:** DeepSV, Manta/DELLY/Lumpy, LSnet, sv-channels. **Benchmarks:** GIAB SV Tier-1, Truvari. **Venue:** *Bioinformatics* / *Briefings in Bioinformatics*. **Novelty:** 8.5. **Pub prob:** 0.75.

### P2 — MultiScaleSV: Multi-scale pyramid encoder for short-read SV
- **Gap 2.** **Novelty:** joint base + kb-scale representation for short-read SV. **Feasibility:** high. **Risk:** marginal gains; **defense:** show length-stratified improvement, especially long deletions where DeepSV degrades. **Novelty:** 7. **Pub prob:** 0.65.

### P3 — UncertainSV: Calibrated uncertainty-aware SV calling
- **Gap 3.** **Novelty:** first calibrated predictive uncertainty for SV (deep ensembles / evidential). **Feasibility:** high. **Reviewer criticism:** "uncertainty is bolt-on"; **defense:** show triage/AURC and clinical curation value. **Novelty:** 7.5. **Pub prob:** 0.7.

### P4 — GraphPileupSV: Learned read-overlap graph for short-read discovery
- **Gap 7.** **Novelty:** GNN discovery on short reads (vs long-read GKNnet). **Risk:** graph construction cost; **defense:** sparse local graphs. **Novelty:** 7.5. **Pub prob:** 0.6.

### P5 — RefPriorSV: Fusing DNA-LM reference embeddings with pileups
- **Gaps 8, 13.** **Novelty:** multi-modal fusion of a reference foundation-model embedding with the read pileup. **Risk:** DNA-LM utility contested ([Tang et al. 2025](https://doi.org/10.1186/s13059-025-03674-8)); **defense:** ablate the LM branch. **Novelty:** 8. **Pub prob:** 0.6.

### P6 — MambaSig: State-space modelling of long-range signatures
- **Gap 9.** **Novelty:** first SSM for SV; linear-time non-local evidence. **Risk:** "architecture swap"; **defense:** tie to a representational claim (linear long-range vs quadratic attention on kb spans). **Novelty:** 7. **Pub prob:** 0.55.

### P7 — ExplainSV: Read/signature attribution for SV calls
- **Gap 10.** **Novelty:** attribution mapping calls to supporting reads. **Risk:** eval is hard; **defense:** synthetic ground-truth attribution + curator study. **Novelty:** 6.5. **Pub prob:** 0.55.

### P8 — NoisySV: Label-noise-robust SV training
- **Gap 13.** **Novelty:** principled noisy-label learning for SV breakpoints. **Novelty:** 6.5. **Pub prob:** 0.55.

### P9 — CoverAdaptSV: Coverage-adaptive single-model SV calling
- **Gap 15.** **Novelty:** one model robust 5×–60× (DeepSV retrains per regime). **Novelty:** 6. **Pub prob:** 0.55.

### P10 — SV-Foundation: Cross-platform/species transferable SV encoder
- **Gaps 4, 17.** **Novelty:** pretrain-once, fine-tune-anywhere SV representation. **Risk:** scope/compute large for one group; **defense:** limit to 2 platforms. **Novelty:** 8. **Pub prob:** 0.5.

---

## Part 6 — Selected project

**Selected: a synthesis of P1 + P2 + P3 — `PULSE-SV` (Pretrained, Uncertainty-aware, Learned, multi-Scale Encoder for Structural Variants).**

### 6.1 Why this is the strongest
It attacks the three most outdated and most consequential DeepSV components at once — the hand-crafted encoding (B1), single-scale window (B2), and absence of calibrated confidence (B7) — under one coherent thesis (learned multi-scale pileup representation with uncertainty). It is squarely feasible for a university group (public data, one or two GPUs), it is *not* a CNN→Transformer swap (the contribution is the learned self-supervised representation and the multi-scale/uncertainty design, architecture-agnostic), and each component is independently publishable, de-risking the project. It targets **short reads** deliberately — the regime where the representation gap is widest and where enormous legacy cohorts make the method immediately useful.

### 6.2 Architecture diagram (textual)

```
                         ┌──────────── Self-supervised pretraining (unlabeled BAMs) ───────────┐
                         │  Masked-pileup + contrastive objective over aligned read tiles       │
                         └──────────────────────────────┬──────────────────────────────────────┘
                                                         ▼ (initialize encoder weights)
  BAM + reference                                Learned Pileup Encoder
   │                                            (per-base/per-read embedding
   ▼                                             replaces DeepSV RGB code)
 Candidate SV locus ──► Tile extractor at 3 scales ──►  ├─ fine  (base-res, ~256 bp)   ─┐
                        (adaptive to predicted size)    ├─ mid   (~2 kb)               ─┤─► Multi-scale
                                                        └─ coarse(~20 kb, spans event) ─┘   fusion (attention
                                                                                            over scale tokens)
                                                                          │
                                                                          ▼
                                               Prediction head ──► {SV type, genotype, breakpoints}
                                                                  + Uncertainty head (deep ensemble /
                                                                    evidential) ──► calibrated confidence
```

### 6.3 Training pipeline
1. **Pretrain** the pileup encoder on unlabeled BAMs (1000G + HGSVC + extra cohorts): mask a fraction of read/base tokens and reconstruct; add a contrastive term pulling together augmentations (down-sampled coverage, strand flips, quality jitter) of the same locus and pushing apart different loci. 2. **Fine-tune** on GIAB/HGSVC-labeled SVs with the multi-scale fusion + prediction head. 3. **Uncertainty**: train a deep ensemble (K=5) or an evidential head; **calibrate** on held-out chromosomes (temperature scaling). 4. **Evaluate** with Truvari against GIAB Tier-1, cross-sample (train HG002/5/6, test HG007 + 1000G individuals not in training).

### 6.4 Loss functions
- Pretraining: `L_pre = L_masked_recon (cross-entropy over masked base/read tokens) + λ·L_contrastive (InfoNCE)`.
- Fine-tuning: `L_ft = L_type (focal CE over {none, DEL, INS, DUP, INV}) + α·L_geno (CE 0/1/2) + β·L_bp (smooth-L1 on breakpoint offsets) + γ·L_uncert (evidential NLL or ensemble disagreement regularizer)`.
- Calibration: post-hoc temperature scaling minimizing NLL; report ECE.

### 6.5 Input representation
Per aligned read within a tile: token = learned embedding of (base, base-quality bucket, strand, mapping-quality bucket, is-paired, concordant/discordant, soft/hard-clip flag, is-split). Depth is implicit in the number of read tokens per column. Three tiles per candidate (fine/mid/coarse); adaptive scaling sets tile spans from an initial size estimate. This *is* the learned replacement for DeepSV's four-bit RGB code — the contribution.

### 6.6 Model architecture
Encoder: a convolutional tokenizer over columns feeding a compact transformer (or Mamba block for the coarse, kb-scale tile to keep long-range cost linear — an ablatable design choice, not the headline). Scale-fusion: cross-attention over three scale summary tokens. Heads: linear type/genotype classifiers + breakpoint regressor + uncertainty head.

### 6.7 Evaluation metrics
Precision, recall, F1 (Truvari, per SV type and per length stratum: 50 bp–1 kb, 1–10 kb, >10 kb); breakpoint error (bp); genotype concordance; **calibration**: ECE, reliability diagrams, AURC (accuracy–rejection); low-label-regime F1 (1%, 10%, 100% of labels) to demonstrate pretraining value; runtime/memory.

### 6.8 Ablation studies
(i) learned encoder vs DeepSV RGB vs sv-channels 1-D channels; (ii) with/without self-supervised pretraining (the key claim); (iii) 1 scale vs 3 scales vs adaptive; (iv) uncertainty head vs none; (v) transformer vs Mamba coarse tile; (vi) contrastive term on/off; (vii) label-fraction sweep.

### 6.9 Comparison experiments
Baselines: DeepSV ([Cai et al. 2019](https://doi.org/10.1186/s12859-019-3299-y)), Manta/DELLY/Lumpy (classical short-read), LSnet ([Luo et al. 2023](https://doi.org/10.3389/fgene.2023.1189775)), sv-channels ([Santuari et al. 2024](https://doi.org/10.1101/2024.10.17.618894)), and — as a short-read genotyping reference — Paragraph ([Chen et al. 2019](https://doi.org/10.1186/s13059-019-1909-7)). Long-read callers (cuteSV, Sniffles2) reported as an upper-bound context, not direct competitors.

### 6.10 Timeline (12 months, one PhD student)
- M1–2: data pipeline, tile extraction, DeepSV/sv-channels re-implementation baselines.
- M3–5: pretraining objective + encoder; sanity ablations.
- M6–8: multi-scale fusion + fine-tuning; GIAB evaluation.
- M9–10: uncertainty + calibration; low-label experiments.
- M11: full ablations, cross-sample generalization.
- M12: writing, revisions.

### 6.11 Expected challenges
Pretraining not beating supervised (mitigate: low-label regime is where SSL wins); tile extraction throughput (mitigate: precompute, cache); coverage sensitivity (mitigate: coverage augmentation in pretraining); breakpoint resolution from short reads is intrinsically limited (frame honestly, report per-stratum).

---

## Part 7 — Novelty verification (adversarial)

Here I actively try to disprove PULSE-SV's novelty by searching for the closest prior work under alternative terminology, then judge whether reviewers would still consider it novel.

**Closest competitors and the exact overlap:**

- **sv-channels** ([Santuari et al. 2024](https://doi.org/10.1101/2024.10.17.618894)) — *closest on representation.* It replaces DeepSV's RGB image with hand-defined 1-D per-position channels and a 1-D CNN for short-read deletions. **Overlap:** moves past RGB; short-read. **Difference:** its channels are still *hand-designed*, it is *single-scale*, *deletion-oriented/filter-like*, has *no self-supervised pretraining*, and *no uncertainty*. PULSE-SV's encoding is *learned*, multi-scale, and calibrated. **Verdict:** clearly distinct.
- **LSnet** ([Luo et al. 2023](https://doi.org/10.3389/fgene.2023.1189775)) — *closest on the DeepSV short-read lineage.* CNN on alignment-signal images for deletion detection + genotyping. **Overlap:** short-read image-based DEL. **Difference:** hand-crafted image, single-scale, supervised, no uncertainty. **Verdict:** distinct.
- **SVDF** ([Hu et al. 2024](https://doi.org/10.1093/bib/bbae336)) — *closest on "learned representation."* Uses an autoencoder embedding. **Overlap:** learned features. **Difference:** it is a *filter* for *long-read* callsets, not a from-scratch short-read discovery encoder, and its "self-supervision" is a reconstruction stage on candidate features, not masked/contrastive pretraining on raw pileups. **Verdict:** distinct.
- **SVision / Cue** ([Lin et al. 2022](https://doi.org/10.1038/s41592-022-01609-w); [Popic et al. 2023](https://doi.org/10.1038/s41592-023-01799-x)) — *closest on multi-type imaging.* **Difference:** long-read (SVision) or fixed-bin imaging (Cue); both hand-crafted, single-scale, no uncertainty, no SSL. **Verdict:** distinct.
- **SVHunter / GKNnet** ([Gao et al. 2025](https://doi.org/10.1093/bib/bbaf203); [Guo et al. 2025](https://doi.org/10.1093/bib/bbaf200)) — *closest on modern architectures.* **Difference:** transformer/graph on *long-read* signals; the contribution is architectural, not a learned self-supervised short-read pileup representation with multi-scale + uncertainty. **Verdict:** distinct.
- **DNA foundation models** ([Ji et al. 2021](https://doi.org/10.1093/bioinformatics/btab083); [Dalla-Torre et al. 2024](https://doi.org/10.1038/s41592-024-02523-z); [Zhou et al. 2023](https://doi.org/10.48550/arxiv.2306.15006)) — *closest on self-supervision.* **Difference:** these are *reference-sequence* models; PULSE-SV pretrains on *aligned reads* (pileups), a different modality, for SV discovery. **Verdict:** distinct, and the review by [Benegas et al. 2025](https://doi.org/10.1016/j.tig.2024.11.013) confirms alignment-aware genomic LMs are not established.

**Would reviewers consider it novel?** Yes, with the caveat that the *combination* is the novelty, not any single ingredient. The defensible, non-incremental core is: **the first self-supervised, alignment-aware learned pileup representation for short-read SV discovery, made multi-scale and uncertainty-calibrated.** Each competitor matches at most one of {learned encoding, self-supervision on pileups, multi-scale, uncertainty}; none matches the set, and none does so for short-read discovery. The primary novelty risk is that a preprint appears combining SSL pretraining with pileup encoding during the project; mitigations are to lead with the *alignment-aware pretraining objective* and the *calibration* results, which are the hardest to duplicate.

**No rejection required:** the selected project survives the adversarial check. I did not need to discard and regenerate.

---

## Final Output — Research proposal

### Title
**PULSE-SV: Self-Supervised, Multi-Scale, Uncertainty-Calibrated Learned Pileup Representations for Structural-Variant Discovery from Short-Read Sequencing**

### Abstract
Image-based structural-variant callers such as DeepSV demonstrated that convolutional networks can detect genomic deletions from short reads, but they rest on a hand-crafted RGB encoding of the read pileup, a single fixed genomic window, and fully supervised training on modest labeled sets. We propose PULSE-SV, which replaces the hand-crafted encoding with a *learned*, *alignment-aware* pileup representation pretrained self-supervisedly (masked-pileup reconstruction plus contrastive coverage/strand/quality augmentation) on large unlabeled BAM cohorts; encodes each candidate at multiple genomic scales with an adaptive tile extractor and cross-scale fusion; and emits *calibrated* predictive uncertainty alongside SV type, genotype, and breakpoints. We hypothesize that a learned self-supervised representation will (i) match or exceed hand-crafted encodings at full supervision and substantially exceed them in low-label regimes, (ii) improve long-deletion recall through multi-scale context, and (iii) yield well-calibrated confidence enabling triage. Evaluation follows GIAB Tier-1 SV benchmarks with Truvari under strict cross-sample splits, against DeepSV, classical short-read callers, LSnet, and sv-channels.

### Introduction
Structural variants are a dominant source of genomic diversity and disease, yet short-read SV detection remains error-prone and no single caller dominates ([Kosugi et al. 2019](https://doi.org/10.1186/s13059-019-1720-5); [Mahmoud et al. 2019](https://doi.org/10.1186/s13059-019-1828-7)). Deep learning reframed variant calling as image classification ([Poplin et al. 2018](https://doi.org/10.1038/nbt.4235)) and DeepSV extended this to deletions ([Cai et al. 2019](https://doi.org/10.1186/s12859-019-3299-y)). Since then, progress has concentrated on long reads and on architectural changes, while the *representation* of the short-read pileup — the part DeepSV hand-engineered — has scarcely advanced.

### Research gap
No method learns a self-supervised, alignment-aware representation of the short-read pileup for SV discovery, models multiple genomic scales jointly, or reports calibrated uncertainty (Part 4, Gaps 1–5; Part 7 verification). sv-channels and LSnet remain hand-crafted and single-scale; SVDF learns features only to filter long-read callsets; DNA foundation models operate on the reference sequence, not aligned reads.

### Related work
See Part 1 (survey table) and Parts 3/7. In brief: image-based calling (DeepVariant, DeepSV, LSnet, Cue, SVision); modern architectures for (mostly long-read) SV (SVHunter, GKNnet, BreakNet); learned-feature filters (SVDF, CSV-Filter); classical baselines (cuteSV, Sniffles2, DELLY-class); benchmarks (GIAB, HGSVC); and reference-sequence foundation models (DNABERT/-2, Nucleotide Transformer, GPN), whose alignment-aware analogue does not yet exist.

### Methodology
As detailed in Part 6: learned per-read/per-base token embeddings; self-supervised pretraining (`L_masked_recon + λ·InfoNCE`); adaptive multi-scale tiling with cross-scale attention fusion; multi-task heads (type/genotype/breakpoints) with focal, CE, and smooth-L1 losses; deep-ensemble/evidential uncertainty with temperature-scaling calibration.

### Experimental design
Data: GIAB HG002-007, 1000G, HGSVC. Truth/eval: GIAB Tier-1 SV with Truvari, length-stratified and per-type. Splits: strict cross-sample and cross-population (no individual or chromosome shared between train and test). Baselines: DeepSV, DELLY/Manta/Lumpy, LSnet, sv-channels; Paragraph for genotyping context; cuteSV/Sniffles2 as long-read upper-bound context. Ablations: encoding (learned vs RGB vs 1-D), pretraining on/off, scale count, uncertainty on/off, backbone (transformer vs Mamba coarse tile), label-fraction sweep.

### Expected results
(1) Learned encoding ≥ RGB at full labels; (2) large low-label-regime gains from pretraining (the headline); (3) improved recall on >1 kb deletions from multi-scale context; (4) ECE substantially lower than softmax baselines with useful accuracy–rejection curves; (5) competitive breakpoint error within short-read limits.

### Novelty statement
PULSE-SV is, to our knowledge and per the Part 7 adversarial search, the first **self-supervised, alignment-aware, learned** pileup representation for **short-read SV discovery**, made **multi-scale** and **uncertainty-calibrated**. The novelty is the combination and the alignment-aware pretraining objective, not an architecture substitution.

### Risk analysis
- *Pretraining fails to help* → emphasize low-label regime; keep the multi-scale + uncertainty contributions standalone.
- *A competing SSL-pileup preprint appears* → lead with the alignment-aware objective + calibration, and with short-read discovery specifically.
- *Breakpoint resolution intrinsically limited on short reads* → report per-stratum and frame honestly against long-read upper bound.
- *Compute* → tiles are small; one to two GPUs suffice; pretraining corpus can be subsampled.

### Publication strategy
Target *Bioinformatics* or *Briefings in Bioinformatics*. Stage as: (a) methods paper (full system) → *Briefings in Bioinformatics*; (b) if pretraining alone is strong, a focused *Bioinformatics* Application Note on the pretrained encoder as a reusable resource. Release code, pretrained weights, and tiling pipeline for reproducibility.

### Future extensions
Extend the learned pileup encoder to long reads and to somatic/mosaic SV ([Belzen et al. 2021](https://doi.org/10.1038/s41698-021-00155-6)); fuse a reference DNA-LM prior (project P5); scale toward an alignment-aware foundation model across platforms/species (P10); add retrieval augmentation against known-SV panels (P9).

### Explicit verdict — "Would this project likely survive novelty review at a Q1 journal?"
**Yes, conditionally.** It occupies a genuinely under-explored intersection (learned + self-supervised + alignment-aware + multi-scale + uncertainty, for short-read SV discovery), each competitor matches at most one axis, and it is framed to avoid the "CNN→Transformer swap" objection. The main residual risk is a fast-moving preprint on self-supervised pileup encoding; the calibration and alignment-aware-pretraining components provide defensible differentiation regardless.

| Criterion | Rating (/10) | Rationale |
|---|---|---|
| **Novelty** | 8.5 | Unoccupied combination; alignment-aware pileup SSL is new; not an architecture swap. |
| **Technical difficulty** | 6.5 | Standard components (SSL, transformers, calibration) but non-trivial integration and tiling. |
| **Publication potential** | 8 | Strong fit for *Briefings in Bioinformatics*; multiple publishable sub-results. |
| **Risk of prior work** | 4 | Some adjacent work (sv-channels, SVDF, DNA-LMs) but none matches the set; moderate preprint risk. |
| **Reviewer confidence** | 7.5 | Clear baselines, ablations, and honest framing of short-read breakpoint limits. |

*Lower "risk of prior work" is better (4/10 = relatively low risk).*

---

## References

1. Mian Umair Ahsan; Qian Liu; Jonathan E. Perdomo et al. (2023). A survey of algorithms for the detection of genomic structural variants from long-read sequencing data. *Nature Methods*. [10.1038/s41592-023-01932-w](https://doi.org/10.1038/s41592-023-01932-w)
2. W. Alharbi; Mamoon Rashid (2022). A review of deep learning applications in human genomics using next-generation sequencing data. *Human Genomics*. [10.1186/s40246-022-00396-x](https://doi.org/10.1186/s40246-022-00396-x)
3. Babak Alipanahi; Andrew Delong; Matthew T. Weirauch et al. (2015). Predicting the sequence specificities of DNA- and RNA-binding proteins by deep learning. *Nature Biotechnology*. [10.1038/nbt.3300](https://doi.org/10.1038/nbt.3300)
4. Ianthe A. E. M. van Belzen; Alexander Schönhuth; Patrick Kemmeren et al. (2021). Structural variant detection in cancer genomes: computational challenges and perspectives for precision oncology. *npj Precision Oncology*. [10.1038/s41698-021-00155-6](https://doi.org/10.1038/s41698-021-00155-6)
5. Gonzalo Benegas; Sanjit Singh Batra; Yun S. Song (2023). DNA language models are powerful predictors of genome-wide variant effects. *Proceedings of the National Academy of Sciences*. [10.1073/pnas.2311219120](https://doi.org/10.1073/pnas.2311219120)
6. Gonzalo Benegas; Chengzhong Ye; Carlos Albors et al. (2025). Genomic language models: opportunities and challenges. *Trends in Genetics*. [10.1016/j.tig.2024.11.013](https://doi.org/10.1016/j.tig.2024.11.013)
7. Lei Cai; Jingyang Gao; Yufeng Wu et al. (2017). Concod: an effective integration framework of consensus-based calling deletions from next-generation sequencing data. *Int. J. Data Mining and Bioinformatics*. [10.1504/ijdmb.2017.10005212](https://doi.org/10.1504/ijdmb.2017.10005212)
8. Cai, Wu, Gao (2019). DeepSV: accurate calling of genomic deletions from high-throughput sequencing data using deep convolutional neural network. *BMC Bioinformatics*. [10.1186/s12859-019-3299-y](https://doi.org/10.1186/s12859-019-3299-y)
9. Mark Chaisson; Ashley D. Sanders; Xuefang Zhao et al. (2019). Multi-platform discovery of haplotype-resolved structural variation in human genomes. *Nature Communications*. [10.1038/s41467-018-08148-z](https://doi.org/10.1038/s41467-018-08148-z)
10. Sai Chen; Peter Krusche; Egor Dolzhenko et al. (2019). Paragraph: a graph-based structural variant genotyper for short-read sequence data. *Genome biology*. [10.1186/s13059-019-1909-7](https://doi.org/10.1186/s13059-019-1909-7)
11. Yu Chen; Amy Wang; Courtney A. Barkley et al. (2023). Deciphering the exact breakpoints of structural variations using long sequencing reads with DeBreak. *Nature Communications*. [10.1038/s41467-023-35996-1](https://doi.org/10.1038/s41467-023-35996-1)
12. Sanghyuk Roy Choi; Minhyeok Lee (2023). Transformer Architecture and Attention Mechanisms in Genome Data Analysis: A Comprehensive Review. *Biology*. [10.3390/biology12071033](https://doi.org/10.3390/biology12071033)
13. Hugo Dalla-Torre; Liam Gonzalez; Javier Mendoza‐Revilla et al. (2024). Nucleotide Transformer: building and evaluating robust foundation models for human genomics. *Nature Methods*. [10.1038/s41592-024-02523-z](https://doi.org/10.1038/s41592-024-02523-z)
14. Luca Denti; Parsoa Khorsand; Paola Bonizzoni et al. (2022). SVDSS: structural variation discovery in hard-to-call genomic regions using sample-specific strings from accurate long reads. *Nature Methods*. [10.1038/s41592-022-01674-1](https://doi.org/10.1038/s41592-022-01674-1)
15. Xiaoke Duan; Mingpei Pan; Shaohua Fan (2022). Comprehensive evaluation of structural variant genotyping methods based on long-read sequencing data. *BMC Genomics*. [10.1186/s12864-022-08548-y](https://doi.org/10.1186/s12864-022-08548-y)
16. Peter Ebert; Peter A. Audano; Qihui Zhu et al. (2021). Haplotype-resolved diverse human genomes and integrated analysis of structural variation. *Science*. [10.1126/science.abf7117](https://doi.org/10.1126/science.abf7117)
17. Gökçen Eraslan; Žiga Avsec; Julien Gagneur et al. (2019). Deep learning: new computational modelling techniques for genomics. *Nature Reviews Genetics*. [10.1038/s41576-019-0122-6](https://doi.org/10.1038/s41576-019-0122-6)
18. Runtian Gao; Heng Hu; Zhongjun Jiang et al. (2025). SVHunter: long-read-based structural variation detection through the transformer model. *Briefings in Bioinformatics*. [10.1093/bib/bbaf203](https://doi.org/10.1093/bib/bbaf203)
19. Albert Gu; Tri Dao (2023). Mamba: Linear-Time Sequence Modeling with Selective State Spaces. *arXiv (Cornell University)*. [10.48550/arxiv.2312.00752](https://doi.org/10.48550/arxiv.2312.00752)
20. Fengyi Guo; Yuanbo Li; Hongyuan Zhao et al. (2025). GKNnet: an relational graph convolutional network-based method with knowledge-augmented activation layer for microbial structural variation detection. *Briefings in Bioinformatics*. [10.1093/bib/bbaf200](https://doi.org/10.1093/bib/bbaf200)
21. Yunfei Hu; V Mangal Sanidhya; Zhang Lu et al. (2021). An ensemble deep learning framework to refine large deletions in linked-reads. *2021 IEEE International Conference on Bioinformatics and Biomedicine (BIBM)*. [10.1109/bibm52615.2021.9669571](https://doi.org/10.1109/bibm52615.2021.9669571)
22. Yunfei Hu; Sanidhya Mangal; Lu Zhang et al. (2022). Automated filtering of genome-wide large deletions through an ensemble deep learning framework. *Methods*. [10.1016/j.ymeth.2022.08.001](https://doi.org/10.1016/j.ymeth.2022.08.001)
23. Heng Hu; Runtian Gao; Wentao Gao et al. (2024). SVDF: enhancing structural variation detect from long-read sequencing via automatic filtering strategies. *Briefings in Bioinformatics*. [10.1093/bib/bbae336](https://doi.org/10.1093/bib/bbae336)
24. Yanrong Ji; Zhihan Zhou; Han Liu et al. (2021). DNABERT: pre-trained Bidirectional Encoder Representations from Transformers model for DNA-language in genome. *Bioinformatics*. [10.1093/bioinformatics/btab083](https://doi.org/10.1093/bioinformatics/btab083)
25. Tao Jiang; Yongzhuang Liu; Yue Jiang et al. (2020). Long-read-based human genomic structural variation detection with cuteSV. *Genome biology*. [10.1186/s13059-020-02107-y](https://doi.org/10.1186/s13059-020-02107-y)
26. Ren Junjun; Zhang Zhengqian; Wu Ying et al. (2024). A comprehensive review of deep learning-based variant calling methods. *Briefings in Functional Genomics*. [10.1093/bfgp/elae003](https://doi.org/10.1093/bfgp/elae003)
27. David R. Kelley; Jasper Snoek; John L. Rinn (2016). Basset: learning the regulatory code of the accessible genome with deep convolutional neural networks. *Genome Research*. [10.1101/gr.200535.115](https://doi.org/10.1101/gr.200535.115)
28. Gelana Khazeeva; Karolis Šablauskas; Bart van der Sanden et al. (2022). DeNovoCNN: a deep learning approach to de novo variant calling in next generation sequencing data. *Nucleic Acids Research*. [10.1093/nar/gkac511](https://doi.org/10.1093/nar/gkac511)
29. Shunichi Kosugi; Yukihide Momozawa; Xiaoxi Liu et al. (2019). Comprehensive evaluation of structural variation detection algorithms for whole genome sequencing. *Genome biology*. [10.1186/s13059-019-1720-5](https://doi.org/10.1186/s13059-019-1720-5)
30. Jiadong Lin; Songbo Wang; Peter A. Audano et al. (2022). SVision: a deep learning approach to resolve complex structural variants. *Nature Methods*. [10.1038/s41592-022-01609-w](https://doi.org/10.1038/s41592-022-01609-w)
31. Michael D. Linderman; Jacob Wallace; Alderik van der Heyde et al. (2024). NPSV-deep: a deep learning method for genotyping structural variants in short read genome sequencing data. *Bioinformatics*. [10.1093/bioinformatics/btae129](https://doi.org/10.1093/bioinformatics/btae129)
32. Yichen Henry Liu; Can Luo; Staunton G. Golding et al. (2024). Tradeoffs in alignment and assembly-based methods for structural variant detection with long-read sequencing data. *Nature Communications*. [10.1038/s41467-024-46614-z](https://doi.org/10.1038/s41467-024-46614-z)
33. Ruibang Luo; Fritz J. Sedlazeck; Tak‐Wah Lam et al. (2018). Clairvoyante: a multi-task convolutional deep neural network for variant calling in Single Molecule Sequencing. *bioRxiv (preprint)*. [10.1101/310458](https://doi.org/10.1101/310458)
34. Ruibang Luo; Fritz J. Sedlazeck; Tak‐Wah Lam et al. (2019). A multi-task convolutional deep neural network for variant calling in single molecule sequencing. *Nature Communications*. [10.1038/s41467-019-09025-z](https://doi.org/10.1038/s41467-019-09025-z)
35. Junwei Luo; Hongyu Ding; Jiquan Shen et al. (2021). BreakNet: detecting deletions using long reads and a deep learning approach. *BMC Bioinformatics*. [10.1186/s12859-021-04499-5](https://doi.org/10.1186/s12859-021-04499-5)
36. Junwei Luo; Runtian Gao; Wenjing Chang et al. (2023). LSnet: detecting and genotyping deletions using deep learning network. *Frontiers in Genetics*. [10.3389/fgene.2023.1189775](https://doi.org/10.3389/fgene.2023.1189775)
37. Can Luo; Yichen Henry Liu; Xin Zhou (2024). VolcanoSV enables accurate and robust structural variant calling in diploid genomes from single-molecule long read sequencing. *Nature Communications*. [10.1038/s41467-024-51282-0](https://doi.org/10.1038/s41467-024-51282-0)
38. Huidong Ma; Cheng Zhong; Danyang Chen et al. (2023). cnnLSV: detecting structural variants by encoding long-read alignment information and convolutional neural network. *BMC Bioinformatics*. [10.1186/s12859-023-05243-x](https://doi.org/10.1186/s12859-023-05243-x)
39. Medhat Mahmoud; Nastassia Gobet; Diana Ivette Cruz-Dávalos et al. (2019). Structural variant calling: the long and the short of it. *Genome biology*. [10.1186/s13059-019-1828-7](https://doi.org/10.1186/s13059-019-1828-7)
40. Nathan D. Olson; Justin Wagner; Nathan Dwarshuis et al. (2023). Variant calling and benchmarking in an era of complete human genome sequences. *Nature Reviews Genetics*. [10.1038/s41576-023-00590-0](https://doi.org/10.1038/s41576-023-00590-0)
41. Victoria Popic; Chris Rohlicek; Fabio Cunial et al. (2023). Cue: a deep-learning framework for structural variant discovery and genotyping. *Nature Methods*. [10.1038/s41592-023-01799-x](https://doi.org/10.1038/s41592-023-01799-x)
42. Ryan Poplin; Pi-Chuan Chang; David H. Alexander et al. (2018). A universal SNP and small-indel variant caller using deep neural networks. *Nature Biotechnology*. [10.1038/nbt.4235](https://doi.org/10.1038/nbt.4235)
43. Luca Santuari; Sonja Georgievska; Arnold Kuzniar et al. (2024). sv-channels: filtering genomic deletions using one-dimensional convolutional neural networks. *bioRxiv (preprint)*. [10.1101/2024.10.17.618894](https://doi.org/10.1101/2024.10.17.618894)
44. Kishwar Shafin; Trevor Pesout; Pi-Chuan Chang et al. (2021). Haplotype-aware variant calling with PEPPER-Margin-DeepVariant enables high accuracy in nanopore long-reads. *Nature Methods*. [10.1038/s41592-021-01299-w](https://doi.org/10.1038/s41592-021-01299-w)
45. Ying Shi; Chen‐Xu Wu; Shifu Luo et al. (2025). Indel calling from ONT sequencing data of family trios via sparse attention and 3D convolution. *Briefings in Bioinformatics*. [10.1093/bib/bbaf430](https://doi.org/10.1093/bib/bbaf430)
46. Jouni Sirén; Jean Monlong; Xian Chang et al. (2021). Pangenomics enables genotyping of known structural variants in 5202 diverse genomes. *Science*. [10.1126/science.abg8871](https://doi.org/10.1126/science.abg8871)
47. Moritz Smolka; Luis F. Paulin; Christopher M. Grochowski et al. (2024). Detection of mosaic and population-level structural variants with Sniffles2. *Nature Biotechnology*. [10.1038/s41587-023-02024-y](https://doi.org/10.1038/s41587-023-02024-y)
48. Eric Talevich; A. Hunter Shain; Thomas Botton et al. (2016). CNVkit: Genome-Wide Copy Number Detection and Visualization from Targeted DNA Sequencing. *PLoS Computational Biology*. [10.1371/journal.pcbi.1004873](https://doi.org/10.1371/journal.pcbi.1004873)
49. Ziqi Tang; Nirali Somia; Yiyang Yu et al. (2025). Evaluating the representational power of pre-trained DNA language models for regulatory genomics. *Genome biology*. [10.1186/s13059-025-03674-8](https://doi.org/10.1186/s13059-025-03674-8)
50. Cheng Yong Tham; Roberto Tirado-Magallanes; Yufen Goh et al. (2020). NanoVar: accurate characterization of patients’ genomic structural variants using low-depth nanopore sequencing. *Genome biology*. [10.1186/s13059-020-01968-7](https://doi.org/10.1186/s13059-020-01968-7)
51. Remi Torracinta; Fabien Campagne (2016). Training Genotype Callers with Neural Networks. *bioRxiv (preprint)*. [10.1101/097469](https://doi.org/10.1101/097469)
52. Songbo Wang; Jiadong Lin; Peng Jia et al. (2024). De novo and somatic structural variant discovery with SVision-pro. *Nature Biotechnology*. [10.1038/s41587-024-02190-7](https://doi.org/10.1038/s41587-024-02190-7)
53. Zeyu Xia; Weiming Xiang; Qingzhe Wang et al. (2024). CSV-Filter: a deep learning-based comprehensive structural variant filtering method for both short and long reads. *Bioinformatics*. [10.1093/bioinformatics/btae539](https://doi.org/10.1093/bioinformatics/btae539)
54. Hai Yang; Wenjun Kao; Jinqiang Li et al. (2024). ResNet Combined with Attention Mechanism for Genomic Deletion Variant Prediction. *Automatic Control and Computer Sciences*. [10.3103/s0146411624700147](https://doi.org/10.3103/s0146411624700147)
55. Xinyu Yu; Yaoxian Lv; Lei Cai et al. (2023). MaxDEL: Accurate and Efficient Calling of Genomic Deletions fromSingle Molecular Real-time Sequencing Using Integrated Method. *Current Bioinformatics*. [10.2174/1574893618666230224160716](https://doi.org/10.2174/1574893618666230224160716)
56. Taedong Yun; Helen Li; Pi-Chuan Chang et al. (2020). Accurate, scalable cohort variant calls using DeepVariant and GLnexus. *Bioinformatics*. [10.1093/bioinformatics/btaa1081](https://doi.org/10.1093/bioinformatics/btaa1081)
57. yan zheng; Xuequn Shang (2023). SVcnn: an accurate deep learning-based method for detecting structural variation based on long-read data. *BMC Bioinformatics*. [10.1186/s12859-023-05324-x](https://doi.org/10.1186/s12859-023-05324-x)
58. Zhenxian Zheng; Shumin Li; Junhao Su et al. (2022). Symphonizing pileup and full-alignment for deep learning-based long-read variant calling. *Nature Computational Science*. [10.1038/s43588-022-00387-x](https://doi.org/10.1038/s43588-022-00387-x)
59. Jian Zhou; Olga G. Troyanskaya (2015). Predicting effects of noncoding variants with deep learning–based sequence model. *Nature Methods*. [10.1038/nmeth.3547](https://doi.org/10.1038/nmeth.3547)
60. Zhihan Zhou; Yanrong Ji; Weijian Li et al. (2023). DNABERT-2: Efficient Foundation Model and Benchmark For Multi-Species Genome. *arXiv (Cornell University)*. [10.48550/arxiv.2306.15006](https://doi.org/10.48550/arxiv.2306.15006)
61. Justin M. Zook; Nancy F. Hansen; Nathan D. Olson et al. (2020). A robust benchmark for detection of germline large deletions and insertions. *Nature Biotechnology*. [10.1038/s41587-020-0538-8](https://doi.org/10.1038/s41587-020-0538-8)
62. James Zou; Mikael Huss; Abubakar Abid et al. (2018). A primer on deep learning in genomics. *Nature Genetics*. [10.1038/s41588-018-0295-5](https://doi.org/10.1038/s41588-018-0295-5)

---

*Methodology note: the corpus was assembled programmatically via OpenAlex (topic queries plus forward/backward citation expansion from DeepSV and DeepVariant), scored for relevance, and curated to 62 core works; all DOIs are OpenAlex-verified. Ratings and gap rankings are the author's calibrated estimates grounded in the cited literature.*
