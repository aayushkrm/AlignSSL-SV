# HG002 DNA and matched reference intake: actual result

Both bounded transfers completed once, with no replacement or retry. This
is acquisition and custody evidence, not a read census, variant call, native
annotation, P1 result or publication contribution. RNA remains untouched.
The full publication goal is active and unmet.

| Stage | Job | Slurm outcome | Elapsed | Measured CPU | MaxRSS |
|---|---|---|---|---|---|
| S1a exact DNA BAM+BAI |1604251| COMPLETED0:0 |2:13:56|201.510s|33160K|
| S0 five GENCODE50 products |1604257| COMPLETED0:0 |24:45|9.446s|29368K|

S1a used8036 allocatedCPU seconds, not its4h reservation. Its manifest
reports8035.241 wall/201.385 processCPU seconds; scheduler and process
measurements are distinct. Fresh body48,748,908,838B; cumulative including
prior196,608B prefixes48,749,105,446B. Remaining52GiB account7,085,469,402B.
Both source ETags, exact ranges and lengths match. The full journal contains
46,503 events; main reconciles all body-read entries to the manifest total.
All four attempts close verified. No decode/read readiness follows from SHA.

S0 fresh reference body1,152,186,383B, prior0, separate2GiB account; remaining
995,297,265B. All five whole-object published MD5s pass, plus SHA256s.
The1,132-event journal reconciles all body reads and verified attempt endings.
The manifest reports1484.170 wall/9.321 processCPU seconds. This does not
attest native annotation compatibility, external binaries or GFF semantics.
Prior software bodies were not metered exactly; do not combine these into
an exact total software/reference transfer claim.

## Complete metadata and non-expiring custody

Unmodified small [DNA manifest](../../results/hg002_intake_20261010/dna_manifest.json)
and [reference manifest](../../results/hg002_intake_20261010/reference_manifest.json)
are in Git. Whole genomic/reference files and complete journals are off Git.
Original scratch leaves and matching non-expiring home leaves use the same
experiment names:

```text
/beegfs/scratch/ws/ws1/igorno-alignssl_restart_20260922/experiments/
/beegfs/datasets/home/igorno/alignssl_restart_20260922/experiments/
  hg002_dna_s1a_20261010_01
  hg002_gencode_s0_20261010_01
```

Login-side file copies preserve the original metadata; no compute-node home
write or genomic download to the laptop. Read-only compute verification
1604280 rehashes all seven **home** objects and matches their original SHA256s.
Its [unchanged JSON stdout](../../results/hg002_intake_20261010/custody_check.json)
prints CUSTODY_HASHES_VERIFIED,42.817s process wall. Slurm COMPLETED0:0,
44allocatedCPU seconds/40.273 measuredCPU seconds/25368K MaxRSS. Conservatively
charge this entire mixed reference/DNA verification to S1: total8080allocated
seconds, remaining20720seconds of8h before any S1b launch. This proves copies,
not source BAM/index/reference biological readiness. The executed checker
SHA256 is7ccac74782c8373363a71bd065dd0dff2758b695fac96fafcd20226931e55396
in the dedicated immutable `hg002_intake_custody_20261010_01` bundle.
The later source adds duplicate-name rejection; no executed bundle is changed.
The temporary upload into the earlier reference bundle was moved to this
dedicated bundle before execution; its original frozen source files stay intact.

Both initial/final manifests and journals match scratch versus home SHA256.
DNA hashes: final4becc6bc9ad1072ae172ff83a68f3dc820e41c6782140ea748d4f2e176f7a0cf,
initialc436875e00bba7845b29ef802f5f35b956863b138ecada15e0aa95f265780be8,
journal2a4007283a6ba0c92d7926ad9780fea5a967867cac6f8e82722310963babff87.
Reference hashes: finalb5558370d4213f64c0f9b25c3334b9b8d42deb35e33b68ea659d98a65c289be7,
initialfaf7e976127fd2e0e725d73742112a31a79129d5f90f2150edde038792c4387b,
journal9807ddde87ab71849ddb00aac7de93f34e3b6fc4f3f3cc96619aa936e6dceada.
No sole needed copy remains in scratch, which expiresOctober22.

## Next actual boundary

S1b [complete-read extraction](2026-10-10-hg002-read-extraction.md) remains
UNBOOKED, pending concrete independent code acceptance and deployed controls.
Worker35 controls reproduced locally; main's disk/quality refinements pass41.
The old worker and reviewer stop with reported usage-limit errors; history
is retained. Replacement maintained Sol6.1/high reviewer Gibbs is requested,
not backend-attested. No main self-review is called independent acceptance.
S1 remainder must subtract actual custody and later allocation costs before
booking; raw copies and extraction/custody outputs share the160GiB peak.
S2–S4 and RNA retain separate gates even if S1b succeeds.
