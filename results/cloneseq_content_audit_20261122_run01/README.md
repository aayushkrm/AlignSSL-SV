# Preliminary content audit — superseded

This first execution followed the prospective
[content protocol](../../docs/research/2026-11-22-cloneseq-content-protocol.md).
It recorded row and join availability without scoring outcomes. During the
run, the orchestrator noticed that a uniquely joined metadata row could be
counted as clone-linked even when its clone label was missing. Consequently,
the `marker_to_clone_metadata` statuses in `audit.json` are **not accepted**.

The exact executed source is preserved as `audit_source_v1.py` and its hash
matches the original result. A corrected second run checks label presence and
preserves this first result; neither run establishes biological accuracy,
independent truth or equal assay budgets.
