# Independent finite review: Tier2 offline summary

16 October 2026, Asia/Tomsk. Requested Sol6.1/high is not independently
backend-attested. Owns only this note. Read both new worker files in full,
the collector contract and the native report helper. No study data, SSH,
job operation or Git operation was used. No result packet is accepted here.

Decision: APPROVE the inspected summary for offline accounting of the complete,
authenticated run02 packet. No blocking implementation defect found within
that scope. No broad redesign or new scientific gate is requested.

The summary validates the plan seal and frozen source identifiers, requires
53 events and 59 windows, and binds the collection manifest to that plan.
It requires COMPLETE, fetch completion, group EOF/completion and stable source
stats. Every manifest window must match the plan geometry and have fetch EOF.
It rejects duplicate group QNAMEs, invalid statuses and invalid or duplicate
endpoint-association keys. It checks association metadata against the plan,
recounts event/window group membership without counting a group twice in the
same event/window, and reconciles all event counts and the total record sum.
The group byte count must also match the manifest. A native report QNAME absent
from the groups is rejected. File sizes and SHA256 values identify all four
inputs actually read; each file is checked for change during its read.

Breakpoint rows are counted by native class and collector group status.
Distinct QNAME sets use any breakpoint of each class; a QNAME can occur in
both Foldback and Chimeric. Their union and intersection are explicit.
The code does not label these sets as the native final read classifications,
does not compute class dominance, and does not equate a missing report row
with a Pass read. The native route can retain a group without producing a
breakpoint row. Group denominators and breakpoint denominators stay distinct.

UNKNOWN groups remain in collection/event counts and in native row counts
split by status. Only eligible Foldback/Chimeric rows enter the detailed
candidate list. This omission from that list does not erase UNKNOWN flags:
their class/status counts and any-breakpoint QNAME labels remain reported.
UNKNOWN is explicitly not a negative result; SA consistency does not establish
complete molecules, authentic artifacts or true allele support.

Selected event associations come from each group's recorded original endpoint
associations. For each eligible flagged row, both native reference coordinates
are also compared independently with all original endpoint windows using
`start <= location < end`. Merged-window bounds do not replace those original
bounds. A breakpoint can therefore match another endpoint in the same merged
window without being assigned to the endpoint that selected the group. These
two types of association remain separate. The overlap result is geometric
context only; it does not authenticate the event or establish a junction.

Coordinate meaning was checked directly against the pinned upstream code,
not inferred from column names. In
[sam.rs at 2a5b7138](https://github.com/jheinz27/breakinator/blob/2a5b7138aee9368c6c613c0837f3d8152437957c/breakinator/src/sam.rs#L128-L161),
the first break uses reverse start or forward reference end; the second uses
reverse reference end or forward start. These are zero-based reference
boundaries. The report adds no one-based offset in
[lib.rs](https://github.com/jheinz27/breakinator/blob/2a5b7138aee9368c6c613c0837f3d8152437957c/breakinator/src/lib.rs#L20-L37).
The summary preserves raw coordinates and read-coordinate fields separately.
The same source's read-level rule resolves breakpoint class counts into one
read class; the summary correctly does not claim to reproduce that rule.
This was a narrow source-code check, not a literature review.

Binding limits: the summary checks internal consistency and reports hashes;
it does not compare those hashes to the execution receipts, authenticate the
report's BAM provenance, or prove native completion. A syntactically valid
truncated report whose QNAMEs remain present can pass these checks. Likewise,
it consumes the collector's associations rather than reconstructing them from
alignment records. These are limits of this offline summary, not evidence of
an actual mismatch. Completion, preserved-output hashes and report accounting
remain evidence to inspect in the already planned actual-packet review.
The summary alone must not certify a completed zero screen.

Independent verification: 27 combined tests passed in 0.77 seconds using the
specified project Python, bytecode disabled and pytest cache disabled: six
summary tests, ten collector tests and eleven native-helper tests. The summary
fixture exercises shared merged windows with distinct direct endpoint matches,
overlapping class labels, UNKNOWN flags, all 53 census rows, incomplete-fetch
rejection, foreign/duplicate QNAME rejection, record-sum mismatch and exclusive
JSON output. These are synthetic software checks, not run02 observations.
Only this review note was added; tests used temporary synthetic files.

Independent review remains pending for the actual packet. Native flags do not
establish false artifact labels, true inversion support, caller failure or a
publication result. The earlier S10 STOP and the no-automatic-retry rule remain.
