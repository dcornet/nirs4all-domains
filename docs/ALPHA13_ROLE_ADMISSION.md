# Alpha.13 study-role and outcome admission checks

These checks supplement the frozen H1–H5 bindings without changing their
descriptors, thresholds or response definitions. Expected behavior is declared
before the adversarial tests. No empirical outcome informs these rules.

Different study names alone do not establish independent populations. A source
pair crossing discovery and potential/actual confirmation requires an explicit
verified-disjoint relation with an evidence SHA-256. Actual confirmation also
requires these relations between distinct admitted studies. Shared or unresolved
populations cannot increase the independent-confirmation count. Admission flags
must be JSON booleans set to true; truthy strings and numbers are insufficient.
Unknown relation types, contradictory duplicate relations and empty identities
must fail closed.

Paired responses require nonempty, unique evaluation identities, identical target
definitions/units, native metrics and a training-only null. Identity order may
change; identity membership may not. Undefined or nonfinite relative skill is
unavailable with a reason. Finite input metrics do not authorize infinite output.

Outcome retention never filters on direction. A supplied frozen observation
roster must match exactly, including explicit unavailable/failed observations.
Without a roster, retention establishes only that all supplied observations were
kept; it cannot certify completeness of the planned experiment.
