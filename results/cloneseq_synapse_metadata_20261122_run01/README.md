# Anonymous CloneSeq Synapse access check

`receipt.json` records five anonymous metadata or download-reference requests
made on 2026-11-22, their response hashes and HTTP status. Project, children
and archive metadata were readable; the archive file-handle and documented
download-reference requests returned 403. No archive was downloaded. A 403
does not prove that authenticated access would fail or specify access terms.

Run from the repository root with
`python3 analysis/check_cloneseq_synapse_metadata.py` and an absent output
directory. Successful download references are redacted instead of stored
because they may contain signed credentials.
