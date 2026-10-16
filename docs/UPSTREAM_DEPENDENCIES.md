# Dependencies encountered in the unit/reference sprint

Audit: Methods source `131a15a`, Preflight `2f0574a`, Datasets `e68d1be`;
published Rust Preflight =0.1.0-alpha.1; installed Methods 1.3.6 / ABI 2.19.0.
No upstream repository was edited and no issue was posted.

## Public representation result (Preflight)

The published facade privately builds physical × instrument × campaign means in
`crates/nirs4all-preflight/src/lib.rs`, but only exposes diagnostics. It cannot
return a train representation usable for held-out projection. Domains uses
existing `MethodsProvider::summary(SummaryRequest).mean` to assemble its explicit
task representation. No missing generic numerical mean kernel was found.

Proposed public Rust API:

```rust,ignore
build_representation(input: &QualificationInput, policy: &RepresentationPolicy,
                     provider: &impl MethodsProvider) -> RepresentationResult
```

Policy: native/technical_mean; required context keys source/instrument/campaign;
optional site/lot separation; allowed technical types; complete-case policy;
strict partition separation; contradictory-reference exclusion; cross-context
handling = retain_linked. Result: native IDs; sample-context matrix and axis;
row-to-acquisition membership; physical and validation-component IDs; per-row
weight; excluded IDs/reasons and denominators; backend/protocol version. Cross-
context rows must remain separate and not silently acquire independent weights.
No Y mean is implied by an X representation.

Scientific gates: balanced/unbalanced technical groups; one physical-sample vote
regardless of acquisition count; hand-computed nonzero means; missing context;
mixed/biological/unknown types; partition crossing; contradictory references;
linked multi-instrument contexts; row order and no-test-fit invariance. A repeated
acquisition can change its physical sample's mean when its value differs; it
cannot create another physical-sample vote. Desired bindings: public Rust first,
then Python/JS serialization of the same membership and exclusion contract.

## Identity-only references (Preflight; transport in Datasets)

Proposed `ReferenceIdentity { reference_id, reference_group_id, physical_sample_ids,
target_id, unit, status, precision, partition }`, separate from an optional
authorized value payload. Status must distinguish hidden, unknown, exact,
censored and composite; precision is optional and never inferred. Validation
must return connected dependency components and scoped reference anomalies
without requiring test values or invalidating pure X diagnostics.

Gates: one reference reused by many acquisitions; reference shared by objects;
transitive groups spanning partitions; contradictory values/units; censoring;
test-value accessor that throws on any pre-training access. Desired Rust + Python
contract. Datasets additionally needs a partition-aware target accessor if
storage-level exclusion is required; its current public `y()` materializes a
whole frame. Current Domains guarantees algorithmic exclusion only.

## Retained PCA transform (Preflight adapter)

Extend `PcaDiagnostics` or add `fit_pca/transform` with retained mean, loadings,
eigenvalues/full covariance moments, input axis, backend version and solver
metadata where available. The Methods C ABI already supplies loadings; no new
eigensolver is requested. Test train-only fit, held-out orthogonal shifts, full-
moment effective dimension, input order and analytical projection. Public Rust
state serialization is needed before removing Domains' small owning ABI adapter.

Datasets' `qualify/metrics.py` already contains noise, PCA Q/T2, RMS/SAM,
artifacts and repeatability heuristics (`spectral_profile`,
`pca_outlier_metrics`, `repeatability_metrics`). They were inspected and not
copied. This sprint uses existing Preflight repeatability and Methods numerical
primitives. Migrating broader Datasets/Quality diagnostics is independent work
and does not block this lot. HDBSCAN, nested models and advanced shift remain
outside these requests.
