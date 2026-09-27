# Independent review of the PAV TAR header inventory

**Date:** 2026-09-27. **Scope:** the two `20240307_PAV_VCF` TAR header walks,
their saved member logs and SHA-256 manifests, PAV source options, and the
Manta signal-53 reassessment. This is not a donor-callability, candidate-recall,
or model-efficacy review.

**Reviewer dispatch:** An independent subagent was requested as `gpt-6-sol`
with `high` reasoning effort. Its runtime did not expose an independently
verifiable actual model/effort identifier; the configuration is recorded as a
request, not attested execution.

The reviewer checked both local manifests, recomputed member counts, unique
names, and header-offset chains, and checked current HEAD lengths/ETags against
the saved summaries. It found no demonstrated parsing error. The evidence
supports the narrow claim that each named TAR has 391 logged members and no
BED-suffixed or `callable`-named member. It does **not** establish the contents
of other HGSVC3 sources, donor callability, confident negatives, or a valid
truth/caller comparison. Whole-TAR publisher MD5s were not recomputed.

## Findings and disposition

1. **P2 — HG00514 assembly/callset provenance remains open.** The corrected
   [assembly notice](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/HGSVC3/working/20241001_verkko_HG00514_fix/20241001_verkko_HG00514_fix.README.txt)
   says older dependent results would be updated later. The
   [source-options note](2026-09-24-pav-callable-source-options.md) now treats
   HG00514 as a concrete but provenance-risky example and explicitly forbids
   automatic pairing of a regenerated mask with older merged calls. Exact
   assembly revision behind any intended truth callset remains unverified;
   HG00514 labels remain unresolved.
2. **P3 — Manta failure wording overreached.** `sacct` records signal 53, not
   who sent it or precisely when the batch script stopped. The current
   [diagnosis](2026-09-24-manta-signal53-diagnosis.md), restart gates, and
   research index now use this narrower interpretation. No caller result is
   inferred; an identical relaunch is not justified.
3. **P3 — HTTP failure paths needed tests.** The scanner already enforced
   exact 206 status, URL, ETag, range, and length, but only TAR parsing had
   direct unit tests. `tests/test_remote_tar_headers.py` now includes mocked
   ignored-Range, redirect, changed-ETag, malformed-Content-Range, and success
   cases. All 10 targeted tests pass. This improves future scan safety; it
   does not retroactively verify whole-TAR MD5s.

The donor-callability and read-alignment gates remain closed. A future
candidate-recall pilot needs exact donor/reference/assembly/truth provenance,
prespecified matching and callable denominators, held-out confirmation, and
independent review before a claim or larger compute campaign.
