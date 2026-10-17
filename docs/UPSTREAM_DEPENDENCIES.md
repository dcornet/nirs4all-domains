# Dependencies encountered in the unit/reference sprint

## Alpha.7 integration and observed constraint

The public DAG-ML 0.3.41 callback scheduler and Methods 1.3.6 PLS/summary/scoring
APIs suffice for scope-local training interventions; no generic kernel or second
optimizer is introduced. The alpha.6 callback extension applies target maps only
after native train data views are checked, then uses the same public native PLS
and N4ME replay. Whole-component closure/matching/exchangeability are task-level
identity protocols. No upstream repository was changed or issue posted.

Controlled factor holdout / size reduction demonstrated Methods numerical errors
"Y score vanished at component 5" and "X weights vanished at component 5" for a
six-component request after known rank loss. The native DAG campaign propagates
that candidate failure. The stress-control design fixes grid 1–3 before further
execution; analytical full-rank controls retain 1–6 and EcoSIS 1–5. No adaptive
retry or silent smaller-grid refit hides native failures. Optional upstream
proposal: explicit per-candidate failure receipts/selection policy plus a public
technical component/rank admissibility contract. This is separate from the
still-missing qualified HDBSCAN held-out assignment API.

## Alpha.6 outcome

No upstream modification is needed for the qualified metadata association and
group/residual baselines. Methods' public factor and summary kernels suffice.
DAG-ML's static native input route cannot encode a different residual Y per
inner fold; its public callback twin supplies native fold data views and owns
CV/selection/refit while a bounded Domains callback invokes native Methods PLS.
This removes the anticipated scientific blocker without a new optimizer.

Optional proposal, not posted: a native grouped target-baseline/residualization
role and a high-level fold-local target-transform example, including baseline
serialization, source metadata bindings, missing/unseen fallback, candidate
artifact invariance under holdout-target mutation and original-unit scoring.
The current qualified callback is host-local: replay of a combined predictor
needs its baseline record plus the selected N4ME, not a standalone PLS artifact
alone. Methods' constant-Y failure is explicitly a degenerate no-fit case.
HDBSCAN held-out assignment remains the separate outstanding upstream need.

## Alpha.5 structural integration

Existing public Methods ABI 2.19 HDBSCAN and ARI suffice for the completed
train-only slice. Exact buffer capacities, status/context errors, self-counting
min_samples, stable MST ties and undefined trivial ARI are respected. No missing
numerical kernel or upstream source change blocks training characterization.

**Proposed extension, not posted:** public fitted HDBSCAN state and qualified
out-of-sample assignment, with state ownership/serialization, compatible
preprocessing/metric, noise/membership diagnostics and documented approximate
assignment limits. Gates require independent train/test fixtures, unseen density
regimes, duplicates/ties, native/binding parity and no held-out fit. Current
batch arrays do not constitute this API. Domains does not read private hierarchy
state or substitute nearest-centroid classification. Test labels and discovered-
cluster predictive baselines remain unavailable until qualified.

Alpha.4 PCA getter/rank-deficiency, Preflight representation/reference, Datasets
metadata/access and DAG-ML facade proposals remain. The public factor-association
kernel can support alpha.6 descriptive group–Y work; its unrestricted permutations
cannot silently become dependency-aware inference. No issue was posted upstream.

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

## Alpha.4 bounded proposals, not posted issues

1. **Methods: public fitted PCA diagnostics.** FlexiblePCA already exposes
   public fit/transform and executes the complete real 390×2151 case. Propose
   getters for fitted affine state, retained eigenvalues and full trace, with
   optional exact squared covariance trace as a separate request/status/budget.
   This would replace Domains' public zero/coordinate transform queries without
   requiring a new eigensolver. Gates: analytical geometry, truncated versus full
   moments, large wide matrices, no held-out refit and unavailable moments
   preserving scores/coverage. Never infer exact full moments from retained PCs.
2. **Methods: large exact rank-one FlexiblePCA robustness.** On the published
   Windows 1.3.6 wheel, 390 rows × 2151 identical signal columns returned
   `FLEXIBLE_PCA_FIT_STATUS_8`, including a one-component request. Small analytical
   rank-one passes; a large control with deterministic small spectral variation
   and the real EcoSIS matrix pass. Propose a minimized native regression fixture
   and documented singular-rank behavior. No upstream fix or cross-platform
   reproduction is claimed. No acquisitions were removed to bypass this case.
3. **Preflight: evidence-backed unspecified spectral repeats.** Preserve the
   distinction between documented spectral replicates and known
   rescan/repositioning/repreparation subtypes. Require source evidence/context,
   expose the representation matrix/membership, and label within-ID dispersion
   without equating it to pure instrument noise. The published enum cannot carry
   this declaration: Domains passes `unknown` into the original full report and
   separately invokes the existing public repeatability kernel. The unchanged
   Preflight `not_applicable` status is retained, not relabeled as computed.
4. **Datasets: original validation metadata and restricted target access.** The
   public writer/getters work, but the audited descriptor does not expose all
   original plot/sampling fields. Propose explicit original identity/group
   declarations and metadata units, plus the previously requested partition-aware
   target accessor. Current local descriptor derivation and full-frame Y
   materialization are documented; algorithmic test-target exclusion is tested.
5. **DAG-ML: grouped workflow façade convenience.** Native published 0.3.41
   CV/SELECT/REFIT works with current Methods, so there is no missing numerical
   engine blocking this probe. Its strict high-level terminal-predict façade
   rejects this grouped workflow. Propose a high-level grouped nested example/API
   exporting selected artifacts and outer lineage. Gates: outer/inner scope
   isolation, reference-connected groups, fold-local centering and held-out
   invariance. No replacement validation engine is proposed.

No issue was posted and no upstream file was edited. These proposals are
separate from the next Domains PCA–HDBSCAN protocol, which reuses available
HDBSCAN/ARI kernels and needs its own scientific gates.
