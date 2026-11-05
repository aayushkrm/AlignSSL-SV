# CloneSeq-SV supplementary archive: prospective metadata inventory

## Question and limitations

The published [CloneSeq-SV study](https://doi.org/10.1038/s41586-025-09580-0)
already reports clone estimates from both SVs and SNVs. Before proposing a
comparison, determine whether the official supplementary archive lists
structured tables that could potentially document its measurements. File
names alone cannot establish patient-level pairing, independent truth,
equal sequencing budgets or the scientific value of a new analysis.

## Fixed source and procedure

The Life Sciences Literature PMC lookup on 2026-11-05 UTC identified
`https://pmc-oa-opendata.s3.amazonaws.com/PMC12629990.1/41586_2025_9580_MOESM1_ESM.zip?md5=053c2a18cbd1da4a250efc78e49b57e7`
as a public supplementary media file. Use the existing bounded remote-ZIP
reader, or a transparent wrapper around it, to inspect the ZIP central
directory only. Require HTTP range responses; cap the sum of returned body
bytes at 512 KiB. Preserve each returned range, source metadata, requested
offsets, file names, sizes, CRC values and local SHA256s. Check that reported
ETags do not change across requests. Do not open any archive member or
inspect patient observations. Do not claim that the complete archive MD5 or
any member CRC has been verified. No raw genomic data or clinical assay will
be downloaded or analyzed in this step.

If range access, consistent source identity or directory parsing fails, record
the actual failure and try an equivalent bounded route. Any later inspection
of table contents or hypothesis-driven comparison needs a separate scope that
states what data and claims are being tested. This protocol is pushed before
the archive request.
