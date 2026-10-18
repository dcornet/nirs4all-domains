# Concrete canonical target-axis transport requirement

The bounded preflight asked a new technical question for already-profiled views:
does the standardized target table expose `observation_id` or `sample_id`? None
of the 53 Y headers does. In the two new proposed extension tasks, X and M expose
observation keys, but M has no declared sample key and Y has no observation key.
These are verified schema facts, not claims about absent original experimental
identities or a failure of every possible public data-access route.

The installed Datasets 0.3.11 canonical variable builder requires an observation
key in Y and warns/skips targets when it is absent. Its consumer `NirsDataset.y`
already exposes a keyed `sample_id` frame when a valid canonical variables table
exists. Do not implement a replacement numerical backend or silently align three
unrelated files by row count.

Minimal evidence to unblock a standardized task: an exporter/code receipt or a
content-bound target-axis manifest declaring which observation/sample key owns
each target record, complete membership, target column meaning, unit status,
duplicate/conflict policy and any original partition labels. This binding can
be canonical and exploratory; it need not certify biological specimen or assay
independence. A manifest must refer to the exact files; a generic assertion that
equal row counts normally align is insufficient.

Proposed upstream transport work, without changing upstream: the standardized
exporter should preserve explicit target keys, or Datasets should consume an
authoritative declared target-axis relation and emit keyed variables without
dropping conflicts. Before a retained-label task, select its allowed row keys
before numeric target decode. Existing full-frame access is appropriate only
when every decoded target is already in the frozen development scope.

No external issue or message is sent. This requirement is recorded once; do not
repeat owner provenance investigations while waiting. Existing X science and
historical, already-qualified model results remain usable.
