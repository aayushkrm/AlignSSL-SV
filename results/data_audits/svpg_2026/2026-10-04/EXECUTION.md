# SVPG source acquisition and header execution ledger

Scope: development source availability, not biological scoring. October 4,
2026 local. Source: https://zenodo.org/records/18456502 (v2, February 2, 2026).
Requested roles: Sol6.1/max decision, Sol6.1/high independent reviewer,
Luna/max supporting workers; actual execution configuration is unattested.

1. The 18,200-byte scripts archive passed publisher MD5, local SHA-256 and
   all-member ZIP CRC. Source was inspected as data, not run.
2. Strict remote central-directory reading of `SV_callsets.zip` failed closed
   when the EOF Range response did not preserve the HEAD validator. No member
   payload was requested and no inventory was published by that attempt.
3. Independent review approved exactly one whole transfer: <=3 GiB payload,
   <=30 minutes, >=10 GiB free, outside Git, no unpacking or outcome analysis.
   The transfer succeeded. Exact size 2,879,666,672 bytes, publisher MD5
   `a6ea80f613130c318d36632073c6de97`, SHA-256
   `fff2f1d2978234a1357c6a16ce5ed9fabf17925955247ae2f9ee2ee8564eb7ca`.
   Inventory was computed on `svpg-18456502-SV_callsets.zip.partial`; verified
   bytes were then promoted without overwrite to
   `/Users/akm/aayushkrm-AlignSSL/data/source_archives/svpg-18456502-SV_callsets.zip`.
4. The inventory has 203 entries / 13,178,958,258 declared decoded bytes.
   Whole MD5 was checked; all-member CRC was not. Do not unpack the bundle.
5. `header_protocol.json` froze all six full HiFi HG002 caller members before
   reading their headers. Existing `scripts/audit_verified_local_zip.py`
   reverified whole identity and read only through each `#CHROM` header.
   Returned header bytes total 33,048, below the 6-MiB bound. ZIP buffering can
   decompress unused bytes beyond a header; no body rows were parsed or saved.
6. All six contig declaration lists are identical (86 entries; SHA-256 of
   newline-joined declarations plus final newline:
   `0802c5536384ef21da5117529cc225e9283d0946e75d5753d3c97421f6195f5e`).
   There are no sequence MD5 declarations. Shared BAM path strings in three
   headers are not raw-input checksums. DeBreak and SVPG lack version fields;
   generic sample labels alone do not establish donor identity.
7. `analysis/probe_svpg_released_script_contracts.py --inspect-pinned-source`
   independently models synthetic event matching and statically checks source
   AST plus hashes. Fifteen focused tests pass, including bounded input checks.
   No downloaded code was compiled or executed; no real genotype comparisons.

The archive and raw genomic data stay outside Git. No GPU or cluster job was
started or cancelled. A read-only account queue was empty. Local free space
after transfer is about 18 GiB. The later scientific protocol is not approved
by this ledger; its selected decoded-file budget needs a reviewed amendment
from 256 MiB to include the full 1,037,019,267-byte six-caller selection.
