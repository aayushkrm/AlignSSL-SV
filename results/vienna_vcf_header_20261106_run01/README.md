# Vienna phased SV VCF: preserved header packet

The independent worker retrieved the public release metadata and the first
2,880-byte BGZF block. The block decompresses entirely to VCF header lines;
it contains no variant records. The worker's full source list, retrieval
details, checksums and limits are in the
[feasibility report](../../docs/research/2026-11-06-vienna-vcf-header-feasibility.md).

These are copies from the completed worker's `/tmp/vienna-vcf-header-check/`
scratch directory. `preservation.json` records their local SHA256 values and
sizes. Recheck the packet, header and exact RNA intersections with
`python3 analysis/check_vienna_vcf_header_packet.py` from the repository root.
The complete VCF and its published MD5 have not been verified.
