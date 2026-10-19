# Full-bank exploratory reference protocol

Protocol identifiers: `domains.same_export.v0.1`,
`domains.bank_reference.v0.1`, `domains.bank_stress.v0.1`.
Frozen before outcome decoding/fitting. H1-H5 and historical protocols remain
unchanged. This operational first pass has no hyperparameter selection: its
singleton grids are PLS with min(3, p, minimum training n - 1) components and
Ridge alpha=1, raw X, centered X/Y, no variable scaling. Methods owns fitting,
scoring and summaries; DAG-ML validates identity FoldSets. No copied algorithms.

## Expected scientific behavior and tolerances

Exact shared export identity, owner attestation, equal counts and no conflicting
keys admit exploratory alignment. Equal counts alone do not. If explicit IDs
are present, join them; contradictory X/M order with unkeyed Y refuses that
source/target. Numerical axis order does not affect generic multivariate
geometry: preserve every original column and its label, use logical indices
only for the native contract when labels are not finite/increasing; disable
physical-axis interpretations and operations. Known retained labels are filtered
before numeric conversion and never influence task, fold or parameter selection.

Analytical synthetic linear-signal fixtures should give finite native predictions
and improve over the training mean; tolerances are 1e-8 for direct repeat scores
and 1e-10 for native analytical means. No minimum real-data accuracy threshold.
Adversarial fixtures must refuse unattested positional counts and conflicting
keys, preserve unsorted columns exactly, and exclude an invalid retained-target
sentinel before numeric conversion. Constant/invalid outcomes, failed models,
negative skill/R2 and missing covariance moments remain explicit.

## Population, targets and evaluation

All 171 declared sources and 2,054 source/target declarations stay in the matrix.
Numeric metadata eligibility is followed by genuine outcome/name, finite-data,
split and mathematical checks. IDs, categorical codes, latitude/longitude and
experimental counters are not automatically chemical outcomes. Any exclusion
has a reason and denominator. All X observations and bands enter descriptive
profiles; no target availability filtering is applied to X-only characterization.

For supervision, absent target values define an explicitly reported available-
case development population, consistently subsetting X/Y/M. Invalid nonmissing
values fail only that target. Known identity components are never divided;
partial component missingness is reported, not called independent sampling.
Small targets need at least 12 finite development observations, at least three
nonempty identity components, and nonconstant train outcomes. Units pass through;
missing units permit within-target scores and unit-free skill only.

Use explicit original split membership even when catalog says not applied.
`train`, `training`, `calibration`, `cal` and development are development;
`test`, `testing`, `validation`, `val` and holdout are retained and excluded from
this first pass entirely. Unknown nonempty membership blocks the affected
source unless it is an explicit no-split/grouping recommendation. No retained
target is decoded or scored here. Original train/test transfer is a later,
separately frozen endpoint. Group-only recommendations do not create holdouts.

Connect rows sharing declared sample/leaf/joint/reference/block identity where
available. Missing keys are never collapsed together. Three deterministic
identity-hash folds preserve those components; logical observation IDs represent
singleton groups only when no repeated identity is documented. The latter is
potentially optimistic within-dataset CV, not group-safe biological transfer.
Group identity quality and grouping columns are reported. No outcome stratification,
target-driven fold allocation, tuning, preprocessing search or family selection.

Report per-family/fold and pooled native RMSE, MAE, R2 where defined,
training-only mean RMSE, S=1-RMSE/RMSE_null, target-range extrapolation, training/
evaluation counts, groups and fit failures. A failed fold makes pooled family
OOF unavailable; successful folds remain evidence. Raw RMSE is never pooled
across unrelated target units. OOF and exact memberships stay protected.

## Stress and confrontation

Select up to 24 tasks before outcomes using eligible, sufficiently populated
declared contexts and catalog order, round-robin one target per source before
additional targets. Contexts may describe instrument, site, material, experiment,
batch or treatment; an X cluster is never named as a biological context.
Contexts need at least two levels and components nested within context. Hold
out a deterministic subset of one context for evaluation; compare training
with that context excluded against a whole-component, exact-size reference
subset on the SAME evaluation observations. The reference must contain the
chosen context; otherwise the matched endpoint is unavailable. Also retain
the full reference. Report D_RMSE=stress-reference and
D_skill=S_reference-S_stress, component counts, support and target range.
Different training populations still confound a causal interpretation. These
are declared-context exploratory comparisons, not independent confirmation.

Freeze descriptor fingerprints before supervision. Join raw PC1, effective
dimension when exact, neighborhood dispersion/proximity and raw/SNV agreement
to unit-free outcomes. Per-view native median skill avoids treating each target
as a study; paired stress comparisons are separate from ordinary-CV screens.
Use existing native fixed absolute Pearson screens (.50/.80/.95); no invented
coefficient/sign/p-value. No pooled observation-level significance. Families,
shared study provenance and unknown overlap limit interpretation. Historical
discovery cases are flagged; untouched independent studies are not assumed.
Report null and contradictory cases as readily as supportive ones.

H1-H5 retain their registered estimands: ordinary CV skill cannot validate a
hypothesis about deterioration. No universal shortcut-risk score is produced.
Source-level publication terms govern aggregates; catalog private tier alone
does not prohibit publication. Protected matrices/identifiers remain private.
