# Proposed train-fitted spectral support protocol

The [methodological review and final approval candidate](TRAIN_FITTED_PROTOCOL_REVIEW.md)
now resolves this initial draft's component boundaries, exclusion policies,
residual definitions and calibration limits. Neither document implements or
authorizes browser fitted-state execution or real-data fitting.

Status: **draft requiring owner validation; not implemented or authorized for
real-source execution**. This proposal does not amend H1–H5 or substitute a
browser full-X fit for native training-only evidence.

## Question, estimand and ownership

For a declared evaluation population, describe its geometric support relative
to an immutable representation/reference fitted only on admitted training X.
This is an observed-X diagnostic, not predictive performance, physical identity,
future-population assurance or a probability of failure.

IO/Datasets must supply content-bound original axes, roles and identities;
Methods owns fit/transform/distances/summaries; DAG-ML owns validation/lineage;
Domains validates scope and interprets results. Native `FittedPca`,
`Methods::fit_pca`/`fit_flexible`, `FlexibleProjection::transform` and
`protocol.rs` already provide relevant seams. The browser's current PCA report
contains scores/moments, not reusable mean/loadings/fitted state. Any browser
fit-state binding must be specified with its owner and independently qualified;
no second numerical implementation or upstream edit is authorized here.

## Preconditions and fixed design

Freeze dataset/version/source hashes, original axis/unit, complete train/eval
observation IDs, intended population, representation, model/provider versions,
dependency evidence and excluded factors before execution. Keep acquisitions,
specimens and assay/reference units distinct. Use verified connected indivisible
groups where available; crossed factors do not become a fabricated hierarchy.
Unknown units allow explicitly exploratory observation-level descriptions, not
an independence claim. No automatic LOGO/KFold choice is made.

The minimal proposed representation is raw centered X, no scaling, imputation,
feature selection or preprocessing search. Fit the mean/PCA solely on train.
The proposed component rule is the smallest resolved prefix reaching 95% of the
exact **training** covariance trace, capped at 20. This is a prespecified design
choice for review, not an optimality or risk threshold. If the cap/resolution
prevents reaching it, report the shortfall explicitly; do not assert 95% coverage.
Exact squared moments remain optional: no truncated-eigenvalue substitution.

Transform evaluation X with that unchanged training state. Never fit on pooled
X, use Y_test for choices, or tune the rule after seeing evaluation distances.
Retain all admissible observations/bands and original ordering; refuse a
population/axis/work incompatibility instead of silently dropping rows.

Report resolved score-space nearest-training-reference distance (k=1) and
reconstruction residual separately. Train calibration distances exclude self
and all matching verified/declaration-scoped dependency groups; evaluation
queries apply the same documented exclusion semantics. No admissible neighbor
is unavailable, not zero distance. Retain counts and exclusions. A 95th training
percentile may be shown as a descriptive calibration reference, labeled with
its population/group/finite-sample limitations; it is not a p-value, universal
support boundary or guarantee about future X. Selection of thresholds from
evaluation outcomes is forbidden. PC1 historical-range evidence remains a
separate narrow diagnostic.

## Prospective checks before any feature promotion

- Freeze expected behavior/tolerances before implementation. Use analytical
  tiny fixtures and the existing native provider independently of the new
  browser transport; exact IDs/order/states, abs 1e-10 analytical scalars,
  abs/rel 1e-8 platform comparisons, sign/tied-space-invariant geometry.
- Mutate/reorder/expand retained X and mutate Y_test: training artifacts,
  component choice, mean/loadings and train calibration must remain identical.
  Use a fit-denial spy after train fit. Evaluation order may only permute outputs.
- Test an in-span shift versus an orthogonal shift: score distance and residual
  answer different questions. Include constant/rank-deficient, unresolved,
  >20-component/truncated and ill-conditioned finite inputs; missing full
  moments must leave only dependent metrics unavailable.
- Test repeated acquisitions, overlapping reference groups, crossed factors,
  no admissible neighbor, mismatched axes and finite resource refusals. No
  physical grouping may be invented to make a split executable.
- Keep support and predictive labels separate: a far spectrum can be predictable
  and a nearby spectrum can have an unmodeled target relationship. Counterexamples
  are acceptance tests, not failed experiments to remove.

Initial software qualification can use bounded synthetic fixtures after owner
protocol validation. Real-data interpretation requires a separately approved
content-bound task; independent-study confirmation and user usefulness need
their own designs. Persist fitted IDs/content/model hashes, representation,
exclusions, query lineage, states/reasons and all negative/refused cases.
