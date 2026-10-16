# Run02 small export

These files are unchanged copies from complete cluster job1604949, except
`summary.json`, which is generated offline by
`analysis/summarize_tier2_geometry_screen.py`. Full execution context and
claim limits are in the [result note](../../../docs/research/2026-10-16-tier2-geometry-result.md).

`manifest.json` was `collection/manifest.json` in the full run. The output
checksum receipt retains its original full-run relative paths. This export
does not contain the two study BAMs or `collection/groups.jsonl`; do not treat
missing files here as absent raw evidence or run `sha256sum -c` here expecting
the full packet. Use the permanent cluster leaf identified in the result note.
The source plan is retained unchanged in [selection/plan.json](../selection/plan.json).

All1,648 native breakpoint rows and all53 event census rows are retained.
Summary hashes name the four full inputs it actually read. Native labels are
not authenticated artifacts or true inversion support. UNKNOWN is not negative.
