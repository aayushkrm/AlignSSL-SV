# Fixed inversion source diagnostic

13 October 2026, Asia/Tomsk. Frozen before main/worker reads caller VCF bodies.
This is a cheap published-case check, not a new method or accuracy campaign.

## Case and question

Use the first HG002 row in the published Table S10: chr2:240685775–240688980,
3,205 bp. Selection is document order, not a favorable comparator outcome.
The [completed source scout](2026-10-13-inversion-case-feasibility.md) reports
orientation/assembly support and a miss across20 long-read calling results.
Repeat/mapping artifacts, exact sequence and independent per-case Strand-seq
support remain unresolved. This author-selected miss is development evidence;
no prevalence, unbiased recall or untouched final test follows.

Question: what do the released fixed-case declarations actually show, and is
there a source-supported residual worth tracing beyond existing methods?
Do not switch cases if a strong released comparator resolves the premise.

## Frozen source panel and scope

Pin author repository jamesc99/INV-Benchmark at
ee77a2f336bf055e5234d7565389aafda56b85cd (main observed December2,2025).
Acquire the20 HG00230x VCFs for cuteSV2/Severus/Sniffles2/SVIM/SVision-pro ×
ONT/PacBio × Minimap2/VACmap. Add Manta/Gridss2 short-read VCFs as distinct
extra controls, not members of the20-result claim. Use merged/Tier1/Tier2
HG002 truth files from the same commit. Its filenames include T2Tv1.1;
that name is not proof of the mapping reference or coordinate convention.
The older source release is not automatically the nine-caller publication's
exact executed panel. Versions/commands/sample/reference identity must stay
explicitly unknown unless source records establish them.

The fixed endpoint window is chr2:240684775–240689980 inclusive. Select POS,
INFO/END and breakend-mate endpoints; separately retain spanning intervals
whose endpoints are outside the window. Keep full raw records and relevant
headers. No count is scored as recovery until representation/reference scope
is understood. An INV-only released file may omit complex components/BNDs;
absence there does not prove absence from all original caller outputs.

Budget: seven MiB for these small source bodies plus one MiB pinned tree
metadata; three MiB per body, enforced before and during reading. Full sizes,
Git blob SHA1, SHA256 and gzip EOF/CRC must pass. Retain originals outside
Git; commit only small receipts/selected records/code. No raw genomes, BAM,
model, graph, caller installation, training, native run or cluster job.

## Interpretation rules and next action

- A compatible strong call with the declared allele closes this candidate's
  unmet-presence premise. It does not prove sequence identity independently.
- A reported absence reproduces a selected published miss only. Trace input,
  alignment, candidate formation and filtering before claiming its cause.
- Unknown reference/version/representation or incomplete original output is
  a scope limit, not a caller failure. Do not manufacture an exact-allele label.
- A distinguishable current-method residual can justify a separately costed
  mechanistic diagnostic. Known complete-structure callers must be controls;
  simple linkage/normalization/union is not new merely because it adds calls.

Independent reviewer scrutiny is required before expensive work or acceptance
of a major positive result. A one-case finding cannot establish publication
readiness. HG002 annotation/HG008 generic detection stops remain in force;
DeepSV is not the scientific foundation. The full goal remains active/unmet.
