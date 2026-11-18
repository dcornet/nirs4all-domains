# F4.2 prospective scientific contract

Frozen before the new scientific tests, 2026-11-18; base
`b2d35182a174381a8b6ffac876316c83d78d21ba`. This additive protocol is
`domains.browser_train_fitted_support.v1`; it changes no historical protocol,
F4.0 numerical definition, F4.1 PCA score or scientific reservation.

Three evidence families stay distinct: existing F4.0 raw train-reference/test-query
neighbors; a new public FlexiblePCA train fit and out-of-sample transform; and
the public Methods indexed-fold PCA monitor. No numerical kernel is implemented
in Domains. Preflight remains 0.1.6 and Methods 1.3.13 / ABI 2.20.

## Expected behavior before execution

Fit FlexiblePCA once on every declared train row in its original order. Export
the actual owner N4ME state internally; transform train and then test through
that same handle. Re-export after both transforms and require unchanged state
bytes. Destroy the handle on success or failure. Test-only changes must leave
the train fit state and train scores invariant within the same runtime.
Changing language, display color or report selection performs no provider call.

The default explicit projection dimension is two returned components; one is
permitted. Methods clamps according to its own dimensions. Scores are transported
verbatim. Per-component train summaries come from Methods, not React. Exactly
constant returned coordinates are noninformative; no substitute PC2 is created.
FlexiblePCA does not publish eigenvalues or numerical-rank resolution, so those
quantities remain unavailable. Nonzero score dispersion is not certified rank.
Do not infer a variance ratio or resolution threshold from truncated scores.

Same-structure test should preserve geometric position; a subspace translation
should move scores, and an orthogonal displacement can leave those scores
unchanged while increasing monitor Q. Increased/decreased variance, duplicates,
near neighbors and contradictory cases remain in qualification. A small or
degenerate reference can make one protocol unavailable while preserving another.
For a constant reference Methods can return zero effective components, undefined
T² and finite residual Q. Preserve those owner Q values and mark undefined T²
entries explicitly; empirical-limit interpretation remains not qualified because
there is no resolved reference component. No zero T² or substitute axis is made.

Monitoring defaults, fixed before execution, are `max_components=2`, `n_folds=5`,
`alpha=0.05`; each is explicit and never selected from test output. Methods
assigns reference fold `i % n_folds`, fits on its complement and obtains
out-of-fold reference T²/Q. It fits its own full reference PCA for monitored
statistics. The two PCA objects are not asserted to be the same fitted basis.
Dimensions, fold-rank constraints, domain limits and owner errors are retained;
no fold count is automatically repaired. Parameter changes append a new result.

Dependent/unknown units do not prohibit admissible descriptive geometry or owner
monitor values. They do prohibit a claim of independently calibrated coverage.
Reported empirical limits/counts remain labeled as indexed-fold descriptions.
An external plan can support a conditional interpretation only when bound to
the exact dataset, ordered train keys, parameters and unique independent-unit
keys, explicitly authorizing the provider's modulo folds. Domains checks internal
consistency, not the scientific truth/authorship of that source.

## Access and output

The unchanged F4.0 train-reference/test-query envelope validates X, ordered keys,
partitions, axis, grants and optional declared exclusion. Its `fit=none` denotes
that old access envelope; the F4.2 outer `fit=train` is the only permitted actual
fit. This does not invoke the F4.0 neighbor operation or change its contract.
Neither retained Y nor predict X is transported. No imputation, band intersection,
reordering or representation conversion is performed. Documentary dependency
fields have their own exact grant list and train/test keys; target-derived fields
are refused. Source metadata alone cannot establish physical independence.

Results contain separate projection/monitor status, reason and nullable value,
parameters, actual fit/query keys, provider calls, input/state/result digests,
numerical limitations, dependency summaries and conditional-limit qualification.
N4ME bytes, raw X/Y and per-row M values never appear in exported evidence.
Observation identifiers and numerical score/T²/Q results retain their scope.
F4.1 per-observation M colors keep their separate permission mechanism; this
projection initially distinguishes train/test without exporting M colors.

The complete original scientific objects remain in JSON and the technical report
space. Mandatory core evidence cannot be unchecked; documentary annexes remain
selectable and uncapped. Refusals are local to this operation and never erase
imported data, F4.0 operations or F4.1 associations.

## Bounds and evidence standards

Access validation is shared with F4.0; numerical admission is separate. The
private access-only helper retains identical identity/grant/axis/cell/JSON
checks, while the unchanged public F4.0 validator still enforces its raw-neighbor
product budget. F4.2 applies its own fit/transform/monitor budgets. An expensive
raw-neighbor operation therefore cannot veto an affordable projection.

Reuse the browser limits: 2,000 rows, 1,000,000 cells, 32 MiB input JSON and
25,000,000 estimated operation products. Explicit bounded component/fold counts
and a 2 MiB serialized state bound protect transport. Projection and monitoring
receive separate cost/domain refusals. These are engineering bounds, not
scientific subsampling or OS memory quotas; worker termination cancels work.

Parity uses existing absolute/relative `1e-10` tolerances for well-conditioned
recorded values, exact identities/counts/statuses and within-handle state equality.
Cross-platform serialized-state hashes need not match. Sign changes and rotations
inside degenerate eigenspaces are compared by mathematical invariants in the
independent synthetic tests, not by forcing historical score coordinates.
Adversaries verify actual call arguments, Y/predict exclusion, stale replies and
cancellation. Configuration and CI YAML are not execution evidence.

No distance, threshold crossing or fraction is a leakage probability, predictive
failure probability, non-calibrability score or independent generalization
certificate. No new real-study utility is established by synthetic qualification.
