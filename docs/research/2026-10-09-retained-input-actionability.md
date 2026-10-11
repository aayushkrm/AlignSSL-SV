# Retained-input and tool metadata audit

Date: 2026-10-09. Question: which retained biological inputs and installed
tools can support a distinct, consequential SV experiment soon, without a new
large genomic download?

Requested model record: GPT-6 Luna / max. The backend and effort are not
independently attested. The governing objective was read in full; its SHA-256
matches `74ba6450712e7f0e763cd81de896d3a71ca73f9c4a10fec3f1ecab59b3f1b0b8`.

## Decision

**No distinct experiment is ready to run from the inputs verified here.** Six
caller VCFs are present on project scratch. Their manifest labels do not
establish one shared donor, technology, reference, truth set, callable region,
or untouched test split. The one HG002 HiFi BAM path in the manifest is
missing at that path. The checked tool paths expose `samtools` and `truvari`,
but this pass did not attest their versions or runtime dependencies. It found
no mapper or caller in the checked `bioinfo/bin` paths.

The only small, distinct falsifier worth keeping conditional is a truth-anchored
review of cross-caller genotype disagreements in the six existing VCFs. Ask
whether sequence-aware allele matching changes exact diploid-genotype
conclusions in a frozen, callable truth region. This tests whether benchmark
disagreements change a consequential genotype, not whether a new score ranks
calls better. Broad harmonization is established prior work. Keep this pilot
only if it changes a predeclared, consequential dosage conclusion beyond
existing sequence-aware controls. If sample resolution yields one donor, treat
this as a development pilot, not a final test or publication result. Close it
if the files do not share a verified sample, reference, truth, and callable
denominator. Do not acquire a large dataset to make this path work.

The audit did not inspect biological file bodies, VCF headers or rows, truth
labels, reads, or archive contents. It did not inspect or replay SVUPP headers,
1604214, or the closed 01/02 inventory/native routes. The main task's SVUPP
header preservation and review remain separate.

## Evidence matrix

| Candidate and explicit path | Presence, identity, and size | Donor, technology, reference, truth, and callability | Exposed split and tools | One cheap distinct action; remaining contract |
|---|---|---|---|---|
| **Six staged caller VCFs**. Manifest: [`caller_preparation01/manifest.json`](../../results/data_audits/svpg_2026/2026-10-08/caller_preparation01/manifest.json). Remote paths:<br>`/scratch/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01/inputs/cutesv.vcf`<br>`/scratch/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01/inputs/debreak.vcf`<br>`/scratch/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01/inputs/sawfish.vcf`<br>`/scratch/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01/inputs/sniffles.vcf`<br>`/scratch/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01/inputs/svim.vcf`<br>`/scratch/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01/inputs/svpg.vcf` | One bounded metadata query found all six as regular, single-link files. Sizes matched the local manifest: cuteSV 29,410,475 B; Debreak 935,962,599 B; Sawfish 25,716,015 B; Sniffles 15,004,300 B; SVIM 6,682,295 B; SV-PG 23,624,851 B. Each resolves under `/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/released-caller-preparation-20261008-throughput01/inputs/`; each reported UID 1638200118. This is path/size identity evidence, not a content hash. | Manifest sample fields are inconsistent: cuteSV `NULL`, Debreak contains a BAM path, Sawfish `HG002`, Sniffles `SAMPLE`, SVIM `Sample`, SV-PG `Sample`. No common donor or technology is established. The manifest does not give a matching reference digest, truth path, or callability mask. | The files were staged in a prior preparation. The manifest does not declare train/test splits. Treat their outputs as development-exposed; untouched loci or donors are **UNKNOWN**. `truvari` exists in the checked `truvari_env`; its version and runtime are unverified. | If a common truth contract already exists, compare all predeclared cross-caller disagreements in one frozen callable region and count exact dosage conclusions that change under sequence-aware matching. First prove sample joins, allele identity, reference build/digest, truth provenance, callable denominator, and split history. Otherwise stop. |
| **HG002 HiFi BAM path recorded by the Debreak manifest**: `/data1/huheng/HG002/hifi.bam`. | `lstat` returned ENOENT. No size, file type, owner, or physical target is available at this path. The string appears in a field named `expected_sample_label`, not in a dedicated read-input field. | The path name suggests HG002 HiFi; this is not verified sample provenance. No reference, truth, or callability link is stated. | No held-out status is stated. `samtools` exists at the checked `bioinfo/bin` path, but its version and runtime are unverified. No mapper or assembler was found in the checked tool paths. | No read-backed adjudication can use this path now. The BAM may exist elsewhere; this missing path does not prove that it does not. Do not search other directories without a manifest path. |
| **HGSVC3 v1.0 GRCh38 insertion/deletion callset**: [`variants_GRCh38_sv_insdel_alt_HGSVC2024v1.0.vcf.gz`](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/release/Variant_Calls/1.0/GRCh38/variants_GRCh38_sv_insdel_alt_HGSVC2024v1.0.vcf.gz) (published path; no current cluster path was found in the inspected manifests). | The September audit records 53,014,672 B for the published VCF. Current local or cluster presence, physical identity, and size were not checked. | Release provenance: 65 phased genomes; PAV 2.4.0.1 calls merged with SV-Pop; GRCh38-NoALT. The inspected header declared GT only. The release is positive variant evidence, not independent truth. No donor-wide callable-negative BED was listed. A missing row or site-level `.` is not a callable reference label. | No train/test or untouched-family split is established in the inspected notes. No read or assembly path was verified. `samtools`/`truvari` might support callset comparison if versions and references qualify; neither makes negatives valid. | Do not use this callset as a negative-label or genotype-error denominator. A small positive-only haplotype comparison is possible only after verifying retained files and reference identity; it has no clear consequential endpoint yet. |
| **PAV 2.4.0.1 callable outputs and 20240307 archives**: [`20240307_PAV_VCF_hg38_mm2.tar`](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/working/20240307_PAV_VCF/20240307_PAV_VCF_hg38_mm2.tar) and [`20240307_PAV_VCF_hs1_mm2.tar`](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/working/20240307_PAV_VCF/20240307_PAV_VCF_hs1_mm2.tar); no retained cluster path was found. | Prior bounded archive-member audits report 12,630,108,160 B and 12,857,282,560 B. They found no BED or `callable`-named members in those two TARs. These are archive-level metadata results, not current remote file checks. | PAV 2 can produce per-haplotype, reference-coordinate callable BEDs. The documented `_500` output can bridge unaligned gaps up to 1,000 bp, so it cannot alone certify a negative. The two scanned TARs contain intermediate calls, not those complete callable outputs. | No split or independent final-test contract is established. No exact callable BED, assembly, or aligner path was found in the inspected manifests. | Do not download either large TAR. If a validated unsmoothed callable BED for both haplotypes of one donor is already retained, a small blinded interval check could test negative-label safety. First verify its exact path, reference, raw-alignment basis, QC exclusions, and independent truth. |
| **GIAB HG002 truth, reference, query reads, and assemblies**: no individual source path for these assets appears in the inspected current input manifests. The only explicit HG002 read path above is missing. | Current presence, size, and file identity are **UNKNOWN**. The `truth_preparation_inventory_v3.json` schema has sample and eligibility/outcome counters but no input path; I did not read its values. | No current truth version, reference digest, Tier 1 mask, read technology, assembly accession, or shared coordinate contract is established by this audit. Do not infer readiness from old cluster notes or a prepared-truth report. | No untouched split is established. The six staged VCFs do not prove a held-out donor or family. | This would be the best source for an orthogonally grounded genotype adjudication only if the exact truth, mask, and matching query calls are already retained. No new download is approved by this audit; first locate exact paths in a current manifest. |

## Tool check

One call through the existing `tools/cluster.sh` checked seven data paths from
the caller-preparation manifest and twelve named environment-bin paths. It
used `lstat` only for those paths. It did not scan directories or read any
biological content. No version or help command ran, so versions and runtime
dependencies remain unknown.

| Exact checked path | Metadata result | Use limit |
|---|---|---|
| `/home/igorno/miniconda3/envs/bioinfo/bin/samtools` | Present; regular executable; 507,088 B; two links; UID 1638200118; physical path `/beegfs/datasets/home/igorno/miniconda3/envs/bioinfo/bin/samtools`. | Could support BAM metadata or read access if runtime works. An older missing-library failure is recorded in [`native-tool-metadata.md`](2026-10-09-native-tool-metadata.md). No version check was made. |
| `/home/igorno/miniconda3/envs/truvari_env/bin/truvari` | Present; executable script; 202 B; one link; UID 1638200118; physical path `/beegfs/datasets/home/igorno/miniconda3/envs/truvari_env/bin/truvari`. | Candidate for VCF comparison only after version and dependency checks. It was not run. |
| `/home/igorno/miniconda3/envs/truvari_env/bin/python` | Present symlink to `/beegfs/datasets/home/igorno/miniconda3/envs/truvari_env/bin/python3.10`; it ran the bounded metadata script. | This confirms that this interpreter can run the metadata script. No package or caller was invoked. |
| `bioinfo/bin/{bcftools,bedtools,minimap2,pbmm2,sniffles,cuteSV,svim,sawfish,truvari}` | No file at these exact paths. | This is not a cluster-wide absence claim. Other named environments, modules, containers, or paths were not checked. Assembly-builder availability is **UNKNOWN**. |

The last recorded scratch-expiry snapshot in the October 8 metadata result was
`2026-10-22T23:02:50+07:00`; this audit did not refresh it. Current files are
on scratch, so preserve their source manifest and expiry when planning any
later work.

## Investment recommendation

Use **no-go pending input contract** for a new experiment. The six VCF files
are real retained inputs, but current metadata cannot support a clean
biological comparison. The missing HG002 BAM, inconsistent sample labels,
unverified truth and reference, unknown callability, and unknown split history
block an honest error estimate.

If those inputs already exist under paths in a current manifest, the next
distinct pilot should ask whether representation-aware matching changes exact
diploid genotype conclusions against independent callable truth. Predeclare
the locus set and effect that would change the investment decision. Report
unresolved truth as unknown. Do not turn benchmark F1, record counts, a
single-donor result, or successful tool invocation into evidence of broad
benefit. Do not extend the pilot into training or a large download if the
contract fails.

This question concerns accurate structural genotypes and reliable truth. It
does not depend on DeepSV or SSL, and it does not replace the main task's
SVUPP work.

## Read scope and limits

Read in full: `2026-10-09-post-native-opportunities.md`,
`2026-10-09-post-native-value-decision.md`,
`2026-10-09-independent-somatic-mixture-inputs.md`,
`2026-10-09-native-tool-metadata.md`,
`2026-10-08-metadata-census-result.md`,
`2026-09-23-hgsvc3-callability-audit.md`,
`2026-09-23-pav-callable-availability.md`, and
`2026-10-09-svupp-provenance-header-result01.md`. Also read the full objective
and `tools/cluster.sh`. I inspected only path/schema fields from current
manifests; I did not inspect their biological outcome values. The synthetic
screen-control path was excluded as a real-data asset. No external endpoint,
archive, VCF header, genotype row, truth label, read, assembly, job, or caller
was accessed or run. No Git action was taken.

## Main's scope qualification

Main reads this entire completed note. The six staged files are verified
present, but this bounded19-path check is not a complete inventory of project
data or installed software. The `/data1/huheng/HG002/hifi.bam` string came
from an expected sample-label field in released-call provenance, not a
verified, previously staged read-input manifest. Its ENOENT on this cluster
does not show loss of a retained BAM or absence of HiFi reads elsewhere.
Likewise unlocated HGSVC3/GIAB paths in these selected notes do not prove
those datasets absent. Do not call existing data old/useless from this check.

The suggested cross-caller representation pilot is conditional and overlaps
established harmonization and a stopped released-callset route. It is not a
selected experiment or publication lead. Necessary new data remain possible
under the broad research goal after a distinct consequential question,
explicit prospective scope/account and independent review; this note's
metadata limits do not impose a universal download ban or reopen the closed
SVUPP/generic-filtering pilot. The Max-effort decision receives these caveats.
