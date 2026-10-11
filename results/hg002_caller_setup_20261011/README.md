# Native caller CLI receipts

Job1604301,2026-10-11: COMPLETED0:0,1 allocated CPU second,
0.543 measured CPU seconds, stepMaxRSS2988K. These unchanged small receipts
record CLI readiness only; no genomic input, caller run or S2 release.

Whole software packets are retained under cluster scratch and HOME
`experiments/hg002_dna_callers_s0_20261010_01`; binaries/assets stay off Git.
The original artifact-sha256sums.txt is a reference to that full packet, not
a claim that all its named files exist here. Original HOME hashes all pass.
That list matches scratch byte-for-byte; its own SHA256 is
195683792c5f93c4b1432c0685e3506a110b16d88c5fffd1500c9d08ae4499e7.

Outer Slurm stdout/stderr are retained separately and byte-match their HOME
copies. Their SHA256s are a571948026e22c9ac1675d2474a97e68a0d0859b302d5f490af19ab0515e853b
and e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.
They were added after the original packet hash list, so are not covered by it.

The asset table distinguishes pbsv's observed SHA from its NULL release-API
digest. Embedded dependency versions are runtime self-reports.
See [setup and scope](../../docs/research/2026-10-10-hg002-caller-setup.md).
