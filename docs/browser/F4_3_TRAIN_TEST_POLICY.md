# F4.3 train/test access policy

F4.3 has two explicit stages: `reference_only` and `test_audit`. Both use
`domains.browser_preprocessing_sensitivity.v1`; the stage, row keys, source
identity and access grant are validated by Domains. No stage admits Y values.

## Reference-only stage

For partitioned input, the reference population is exactly the ordered
manifest rows declared `train`. Assigned test and predict rows are not included
in the X matrix passed to the provider. A fully unpartitioned source may be
analyzed as an explicitly labelled full-source descriptive population. Mixed
assigned and unpartitioned populations are refused. Preserve all rows and
their declared keys; no hidden sorting, deletion, aggregation or identity
inference is performed.

Fit each learned preprocessing stage on reference X only. This includes MSC
reference statistics, StandardScale means/scales, Normalize column norms, and
any other state the Methods operator learns. Save the actual exported state and
transform reference X through the same public Methods lifecycle. Store exact
plan, dataset/content, ordered reference-key, axis, input/output and state
fingerprints in the result. A fit or transform failure stays unavailable for
that representation; never hand-code a fallback.

Eligible optional factors are selected from declared metadata roles and
projected onto reference keys. The browser adapter excludes target-derived and
unknown-kind fields and limits selection to two factors. Declared dependency,
reference, repetition, group, instrument and campaign metadata may be included
under the request's explicit M-field grant for dependency/exclusion checks.
These fields document relationships; they do not prove physical or reference
independence. Y access is an empty list in the request grant.

## Explicit test audit

The second action is available only for partitioned data with declared test
rows and a computed, frozen `reference_only` result. The submitted plan,
dataset/content identity, reference keys, reference input hash, result hash,
provider version and representation order must match. Any plan or factor
change creates a new exploratory revision and requires a new reference run
before test audit.

Only after the frozen binding validates does the protocol transform test X
using the corresponding reference-fitted states. It does not fit or update
preprocessing state on test. The reference rows are recomputed through Methods
and their saved axis/state fingerprints are checked against the frozen result
before query transforms proceed. A mismatch refuses the test audit. Test X and
declared dependency fields may be read in this explicit audit; no test factor
association or test-driven preprocessing selection is performed.

The receipt must state whether test X was accessed and preserve reference and
query keys. Examining test X can influence later decisions, so this stage is a
descriptive audit after a frozen plan, not an untouched final evaluation or
authorization to choose a pipeline. It never reads `Y_test`; in fact this
protocol contains no Y field for either stage. Supervised AOM selection on
`Y_train` is deferred to a separately versioned protocol with prospective
folds and its own leakage tests.

## Refusal and interpretation

Missing or mixed partition declarations, absent train/test populations,
ambiguous keys, mismatched frozen evidence, nonfinite X, invalid axes and
provider/budget failures produce explicit refusals or entry-local unavailable
values. A refused test audit must not create a partial scientific report.
Neither stage establishes independent sampling units, predictive performance,
transferability, causal mechanism, or a safe validation split.

The schema and binding declarations are linked from the
[representation contract](F4_3_REPRESENTATION_CONTRACT.md). This document does
not certify that native/WASM execution or the complete adversarial suite has
run; the F4.3 validation record reports that separately.
