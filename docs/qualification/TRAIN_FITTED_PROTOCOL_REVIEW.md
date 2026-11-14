# Train-fitted support: methodological review and approval candidate

Status: **candidate for owner approval, not an implemented browser feature or a
real-data execution grant**. Reviewed source: 4656e98; candidate ID
`domains.train_fitted_support.candidate.v1`. This adds no amendment to canonical
v0.3, historical H1–H5, old native results or the frozen browser full-X protocol.

## Decisions on the previous proposal

| Choice | Classification | Decision / scientific reason |
|---|---|---|
| Observed evaluation X relative to a train-fitted reference | Justified | A conditional geometric estimand; it neither estimates prediction error nor certifies an unseen future distribution. |
| Raw centered, unscaled X | Arbitrary but acceptable | Minimal declared anchor, not the universally best NIRS representation. Preserve units/axis and require a separate design for preprocessing comparisons. |
| Fit mean/state only on train | Justified | Evaluation X/Y must not change fitted parameters, component selection or train calibration. Evaluation X may be transformed and described after the state is locked. |
| 95% of full training covariance trace | Arbitrary but acceptable | A reproducible compression convention, not a predictive/safety threshold. Numerically computed full-spectrum trace must use the same covariance normalization as eigenvalues. |
| Cap 20 and numerical rank | Modify | Never claim 95% if the cap/resolution prevents it. Do not split a numerically tied eigenspace to obtain a convenient score space. |
| Missing moments | Modify / separate | Missing squared eigenvalue sum disables exact effective-dimension metrics, not a known trace, scores or projection. Missing full trace disables the 95% rule; do not substitute a retained-eigenvalue sum. |
| Immutable transform / reconstruction | Justified, API qualification incomplete | Verify fitted mean, orthonormal loading convention, selected columns and inverse/reconstruction access through owner APIs. Existing native code is a seam, not browser portability evidence. |
| Euclidean score nearest-reference distance, k=1 | Arbitrary but acceptable | A local geometric distance in an unwhitened selected score space; no probability, density estimator or invariant cross-dataset scale. |
| Always exclude every metadata group | Modify | Match a predeclared reference policy to prediction novelty. A categorical batch/instrument/site column alone does not prove an indivisible physical dependency. |
| Orthogonal reconstruction residual | Justified with explicit definition | Report squared residual Q and optionally RMS residual in the original feature units, separately from score distance. Different axes/weights are not directly comparable. |
| 95th training percentile | Insufficiently qualified as a threshold | Retain only as a descriptive in-sample reference. Group-excluded neighbors do not undo the query's contribution to PCA fitting; residuals are also fitted in-sample. No 5% false-alarm or future-coverage claim. |
| Quantile convention and small calibration counts | Arbitrary but acceptable, API qualification required | Fix Type 7 interpolation if supplied by a qualified owner API; m<2 is unavailable, m<20 is a coarse-tail annotation. These are reporting conventions, not guarantees. A quartile-only summary API does not establish a 95th-percentile operation. |
| Equal acquisition weighting | Arbitrary but acceptable for observation geometry | Preserve all admitted acquisitions and disclose repetitions. This is not an independent-specimen-weighted covariance; do not aggregate/weight silently. |
| Crossed factors / small populations | Modify / explicit limits | Preserve qualified relations and counts; no forced hierarchy, pseudo-independent repetitions or confidence interval from an unknown effective-unit count. |

## Final candidate contract

**Inputs and admission.** Freeze exact dataset/content/source/view, provider and
representation versions; original ordered axis values and units; train/eval
observation IDs; intended population; actual split; and evidence for acquisition,
specimen and shared-reference relationships. No target enters fitting or support
selection. Numeric finiteness, axis equality, population membership and work/RAM
bounds are checked before numerical execution. Refuse incompatible axes, missing
cells, duplicate/ambiguous identities and budget overflow; never silently sort,
filter, impute, merge sources or downsample. Unknown physical units allow a
clearly labeled exploratory observation-level result, not independent transfer.

**Reference policy.** Select one policy in the task freeze, before evaluation:
acquisition-only novelty, or novelty of verified indivisible specimen/reference
components. Always exclude identical acquisition/self references. For new-unit
claims, verified same-unit/shared-reference relations are hard exclusions and
must not cross the intended split. Connected components apply only to qualified
indivisible relationships, not every crossed categorical context. Known-unit/new-
acquisition use can deliberately retain other acquisitions of that known unit;
record the overlap and narrower estimand. Declaration-only group exclusion is
allowed as declared, without authenticating physical independence. Unknown use
requires conditional policies or a request for the missing objective; do not
select whichever policy gives a favorable result. An empty reference set is
unavailable, never zero distance.

**Training and PCA selection.** Fit the raw-X mean and PCA on train once. Use
sample-covariance normalization consistently. Let T be the complete training
trace and use the owner's resolution/unresolved flags. T must be finite and
positive; zero variance makes PCA-dependent metrics unavailable. Select the
smallest resolved prefix reaching 0.95 T, subject to cap 20 and n_train-1.
Retain actual achieved coverage and reason if the target cannot be reached.
Missing T does not permit guessing coverage. Missing sum(lambda squared) only
removes quantities requiring it. Near-resolution behavior is not physical rank.

Group adjacent eigenvalues whose descending gap is at most twice the documented
absolute owner eigenvalue resolution (overlapping numerical-accuracy intervals).
This is a conservative numerical block convention, not a confidence interval.
If the 95% boundary cuts such a block, retain the whole block only if it fits the
cap. Otherwise use a known complete prefix before that block and report coverage
shortfall; if no resolved prefix remains, PCA support is unavailable. A boundary
at component 20 needs the next eigenvalue or equivalent owner evidence to rule
out a tied block; requesting one guard eigenvalue does not retain a 21st score
component. If that evidence/API is unavailable, report boundary ambiguity rather
than certify a unique retained subspace. Do not round an uncertain coverage
across 95%; coverage within 1e-10 of the target is explicitly numerically
borderline, an engineering convention rather than an error bound. No evaluation
value chooses k. Unknown owner resolution cannot certify a tied boundary.

**Projection and distances.** Lock state/mean/loadings/component IDs and their
content hashes before eval. Transform using the same immutable state. In the
unwhitened selected score space, return the minimum Euclidean distance to an
admissible training reference, its provenance and available-reference count.
Never fit a new PCA to eval or concatenate train/eval. All original evaluation
observations stay in the result with individual states/reasons.

For orthonormal retained loadings V and train mean mu, define
`Q = ||x - mu - (x - mu) V V^T||^2` and `RMS = sqrt(Q/p)` with p unchanged bands.
Methods must own the numerical transform/reconstruction/norm; Domains composes
scope and named outputs. If qualified loadings/inverse/residual APIs are absent,
keep residual metrics unavailable while retaining supported projection/distance.
Do not silently copy a kernel or substitute another normalization. These are
unweighted ordered-feature metrics, not a physical wavelength integral.

**Calibration and reporting.** Report train-reference distance and residual
distributions separately with the selected exclusions, actual observation/unit
counts, zero/tie fractions and finite coverage. Each 95th percentile uses fixed
Type 7 linear interpolation on eligible training values through a separately
qualified owner operation. If only quartile summaries are exposed, this optional
percentile remains unavailable; transport must not implement a quantile backend. Fewer
than two finite values makes that percentile unavailable; fewer than 20 gives
a coarse-tail warning, not a fabricated interval. Unknown independent-unit count
stays unknown. A zero reference percentile is reported as zero; no division by
zero, infinite score or arbitrary replacement. These percentiles are descriptive
in-sample references, not calibrated detection cutoffs. Independent calibration
or whole-unit cross-fitting would be a separate owner-approved protocol.

The output states retained dimension/coverage, missing moments, scope/policy,
distances/residuals, calibration limitations and the absence of Y-based or causal
evidence. Support does not become poor predictive skill, a risk probability or a
certificate of future generalization. Native, browser and predictive evidence
remain separate.

## Minimal synthetic acceptance plan (not executed here)

Four training families, <=32 rows x 24 bands, native and future portable owner
routes on Windows/Ubuntu: **<=16 PCA fits total**, <=32 transforms, <=32 neighbor
queries and <=16 summary calls. Reuse fitted states within adversaries; no refit
after train lock. Serial workers, 960 MiB RAM, 15-minute measurement bound per
worker, <=8 MiB controlled output. Toolchain/build admission is separate; no real
data or scientific reservation is included. Run only after protocol/API approval.

| Case | Fixed counterexample / expected behavior |
|---|---|
| F1: score versus residual | Train (-1,0),(0,0),(1,0); eval (2,0) has Q=0 with score novelty, (0,10) has Q=100 with zero nearest score distance when admissible. They must not receive the same interpretation. |
| F2: zero/rank limits | Constant training X has unavailable PCA coverage, not an arbitrary dimension. Raw-distance metrics can remain independently available. |
| F3: tied cap | 32-row centered orthogonal-sign design with 21 equal-variance columns: an arbitrary 20/21 slice must not be presented as a uniquely justified 95% space. |
| F4: finite conditioning | A declared two-scale analytical design tests the owner's resolution and finite/refusal states; no arbitrary eigenvalue is invented near numerical resolution. |
| F5: axes/degenerate input | Permuted or incompatible axes, missing cells and malformed shapes are refused before transform; no implicit alignment or row deletion. |
| F6: dependencies | Shared-reference crossed components, deliberate known-unit overlap and no admissible neighbor exercise distinct policies; never infer groups from clusters. |
| F7: non-leakage | Mutate/reorder/expand eval X and alter Y_test; fit-denial spy, mean/loadings/k/train calibration hashes stay unchanged. Eval order only permutes outputs. |
| F8: optional moments | Simulate unavailable squared moments/full trace independently through the existing provider contract. Only dependent metrics lose availability; no new fit is needed. |

Use exact IDs/order/states. Normal-scale analytic scalars use absolute 1e-10;
platform values use abs/rel 1e-8 with units/resolution recorded. Use Gram/projector
comparisons for signs/tied bases; conditioning tests require declared scale-aware
expectations, not a large absolute tolerance hiding errors. Source numerical
owners, ABI/publication/binding and executable evidence must all exist before
promotion. No fitted-state browser implementation is part of this review.

Sources: [original proposal](TRAIN_FITTED_SUPPORT_PROPOSAL.md),
[`methods.rs`](../../crates/nirs4all-domains/src/methods.rs),
[`protocol.rs`](../../crates/nirs4all-domains/src/protocol.rs),
[ownership](../METHOD_REUSE_MATRIX.md), and existing native scientific tests.
