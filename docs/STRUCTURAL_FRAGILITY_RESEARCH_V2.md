# Structural fragility research design v2

Design ID: `domains.structural_fragility.research.v2`. Revision: 2026-10-28.
Status: **proposed research design; no new numerical execution**. Inspected local
and GitHub HEAD: `de803ef7e5496147fad692942dfc4d9702790e3a`. Current coverage is
read from [status.json](campaign/status.json): 164 entries, 171 views, 137 complete
raw/SNV profiles and 682 complete primary quantitative tasks. These are not
independent-database counts. Historical reports, outcomes and the
[H1-H5 register](ALPHA13_SUPERVISED_PREREGISTRATION.md) remain unchanged.

## Question and evidence boundaries

Do structural properties contribute to statistically detectable, estimator- and
target-dependent deterioration from representative/within-group evaluation to
structurally independent or out-of-support prediction, even while useful X-Y
signal remains? Unsupervised descriptors are explanatory candidates for validation
sensitivity, rather than unconditional RMSE or absolute estimator quality.

Useful chemical signal and a small group-dependent contribution can coexist.
Statistical detectability does not require a dominant contribution, and no 20% or
30% minimum deterioration is imposed. Report effect size, uncertainty and practical
importance separately. Predictive dependence is not, by itself, a causal or
undesirable shortcut. No universal risk score or leakage probability is proposed.

This addendum extends the research questions, not the registered meaning of H1-H5.
Already observed outcomes and any new derivation from them remain exploratory.
A future confirmatory freeze must identify untouched databases/outcomes, exact
contrasts, hypotheses, parameters, statistical families and analysis code before
response evaluation. The document alone is not that freeze.

## Primary macro-unit and hierarchy

`repository/portal -> original experimental database -> source/view -> target -> validation protocol -> estimator`

The original experimental database is the default macro-analysis unit, defined by
the actual experimental collection and its population, not a catalog slug.
EcoSIS collections may represent many different databases: a shared portal,
namespace, publication venue or material family does not establish shared
experimental identity. Multiple views of the same specimens and many Y columns
do not increase the independent database count.

Record original database identity and evidence, catalog/content/source links,
study/publication relationships, physical population overlap, repeated specimens,
view relationships and target families. One publication can describe multiple
databases; one database can appear in multiple publications. Established overlap
induces a higher dependency level across databases. Unknown overlap stays unknown;
it is not independence and does not automatically merge every portal collection.

Retain all admissible quantitative targets. Within each database, estimator,
representation and contrast, report median target effect and dispersion, task
counts, missingness, failures and target-family composition. Avoid weighting a
database by its number of Y columns or spectral views. Shared-specimen views are
paired/nested evidence, not extra macro-replicates. Compare equal-database summaries
with prespecified alternative within-database target-family/view weighting, mean
versus median, and leave-family-out sensitivity. No cross-unit raw-RMSE average.
Illustrative single targets require an explicit pre-outcome semantic rule and do
not replace the all-target synthesis. Partial/failed cases retain their states.

Report mapped database records and independently supported dependency blocks
separately. Effective independent support remains unavailable until justified by
the mapping and analysis, rather than being set to 164, 171, 137 or 682.
Use the existing [study import](STUDY_EVIDENCE_IMPORT.md); no provenance framework
or renewed unresolved source-owner investigation is required.

## Two distinct real-target contrasts

| Contrast family | Scientific question | Interpretation and required controls |
|---|---|---|
| A: SPXY versus LOGO | How do representative calibration and group-excluded benchmark protocols differ? | A protocol gap mixing sampling, training composition/size, target and X support, group novelty and estimator response; not a causal shortcut effect |
| B: known-group versus unseen-group | How does prediction change when the evaluation context is represented in training versus excluded? | Common evaluation observations and whole-group size controls where feasible; residual composition/support differences remain |

For A, SPXY uses only eligible development X/Y to select calibration observations.
An untouched outer evaluation population is removed first, including its Y from
selection, scaling, tuning and split generation. Report whether evaluation groups
are known or new to each training regime. If a classical retrospective partition
uses all development Y, label its within-development score accordingly; it cannot
be advertised as prospective external-test performance. Never use sealed external
test labels to choose a representative split.

For B, distinguish context groups from indivisible specimen/reference components.
Known-context training can contain other independent components of the context;
the same specimen/reference component can never cross the boundary. When these
requirements make a known/unseen contrast impossible, mark that contrast
unavailable. Do not manufacture groups or split indivisible units to obtain it.

True LOGO holds out each eligible declared context in turn. GroupKFold excludes
sets of groups per fold and has a different estimand. A few selected group
holdouts are not exhaustive LOGO. Record exact design, group evidence and sizes,
same/different evaluation membership, matched/unmatched training counts, missing
targets, and X/Y support changes. Per-fold transforms fit on training only.
If evaluation observations differ, preserve the protocol-gap outcome but mark
paired/common-null contrasts unavailable; do not pretend the populations match.

## Outcomes conditional on baseline skill

For each database, source, target, estimator, representation and contrast:

`G = log(RMSE_stress / RMSE_reference)`

`S_reference = 1 - RMSE_reference / RMSE_training_null`

Where common evaluation populations and an explicit reference training-mean
predictor permit it:

`S_stress_common = 1 - RMSE_stress / RMSE_null_common`

`D_skill_common = (RMSE_stress - RMSE_reference) / RMSE_null_common`

The same null predictions and evaluation IDs must define both common-null errors.
Record whether the reference is full training or a whole-component size control;
do not substitute one for the other. A positive G denotes deterioration. Retain
both errors in target units, both population definitions and reference skill.
A relative increase from a useful baseline is not equivalent to the same increase
from an already negative-skill reference. Neither case is discarded.

G requires two positive finite RMSE values. Zero-error cases retain their errors
but G is unavailable with an explicit reason; no epsilon or clipped arbitrary
log score. A zero null RMSE makes its skill unavailable. Unsupported paired
populations, missing intervals and failed models similarly retain reason/value
states. Do not backfill intervals or silently average incomparable target units.

Each effect carries group/sample counts and evidence, train-size change, target
family/units, X and Y support diagnostics, preprocessing/model identity, and an
uncertainty scope. Frozen-OOF resampling describes conditional prediction
uncertainty; refit and new-group/database uncertainty require different designs.
Existing one-PC range diagnostics are limited support evidence, not full support
certificates. Unknown physical independence stays explicit.

## Database-aware statistical analysis

The research association is between frozen X descriptors and G **conditional on
baseline skill**, with estimator, representation, target-family and protocol
interactions. Analyze within-database effects before macro-synthesis; preserve
dependencies between targets, views, folds and related databases. Do not treat
each repeated target realization or CV fold as an independent experimental database.

Before new outcomes, freeze the descriptor set, transforms, baseline-skill
adjustment, interactions, primary tests, uncertainty/resampling unit and
multiple-testing family. A proposed primary family uses Holm family-wise control;
separately declared exploratory screens may use false-discovery-rate control.
Both require qualified upstream statistical kernels, sufficient independent
support and reported family denominators. No p-value or interval is inferred
from the existing native absolute-correlation threshold flags.

Reference error enters both G and reference skill, creating mathematical coupling
and measurement error. Include joint paired uncertainty and prespecified
cross-fitted/alternative-reference sensitivity where feasible; an adjusted
coefficient does not establish causality. Database-level/block uncertainty and
aggregation/family sensitivity must accompany any pooled association. If effective
independent support or exchangeability is unresolved, report descriptive effects
and unavailable significance rather than specimen-level pseudoreplication.

## Negative controls and engineered mechanisms

| Program | Frozen target mechanism | What it measures | Interpretation limit |
|---|---|---|---|
| IID null | Independent target realizations, independent of X/group labels | Out-of-sample skill distribution and apparent favorable outcomes under a true null | One positive score does not prove leakage; score > 0 is not itself a significance test |
| Group random | `Y_star[i] = random_effect[group[i]]` | Group recognition/memorization in known versus excluded contexts | Deliberately shared labels are not evidence of real-target leakage |
| Signal plus group | `Y_star[i] = f_signal(X[i]) + lambda * random_effect[group[i]] + noise[i]` | Additional structural contribution across weak, zero and stronger effects while spectral signal remains useful | An engineered mechanism does not identify a chemical shortcut |
| Optional real-target perturbation | `Y_star = Y_real + lambda * group_effect` | Sensitivity to an injected perturbation | Does not identify the original chemical or group mechanism |

For IID controls, distinguish (i) random targets evaluated under previously frozen
splits and (ii) complete regeneration of each Y-dependent SPXY partition, including
its selection/tuning steps, for every randomized target. Holding a real-Y-derived
SPXY split fixed tests a conditional split, not the full SPXY pipeline. Untouched
outer labels remain excluded even in the regenerated design.

Freeze generator functions, coefficient/feature ordering, random streams, seeds,
signal/noise scales, lambda grid, group assignments and model settings before
response evaluation. Preserve paired memberships/configurations across compared
models; no seed search for favorable examples. A useful spectral component should
remain when lambda is small. Negative/zero, weak and opposite-model effects stay.
The optional real-Y perturbation is a separate future experiment, not an excuse
to expose retained labels. Target generation is controlled test data, not a new
numerical model backend.

Report Monte Carlo uncertainty and finite-draw resolution. Favorable-score
frequency is descriptive unless a prespecified, calibrated decision rule defines
a false positive at a nominal error level. Elevated rates require separate
diagnoses of selection bias, random variation, retained-label exposure,
preprocessing and split effects; they are not a universal leakage probability.

## LOCO-X and continuous support

When experimental group metadata are unavailable, qualified X-only clustering or
continuous spectral-region partitions can support exploratory stress. Call cluster
holdout **LOCO-X: Leave-One-X-Cluster-Out**, not experimental LOGO. Complete-X
construction is permitted only as an explicitly transductive X-aware experiment;
prospective support prediction needs train-fitted representations/assignment.
Never use held-out Y to choose partitions, features or representation.

Report clustering stability, representation sensitivity, noise handling, sizes and
support. All-noise or continuous populations do not justify forced clusters.
Use a continuous-region design or mark LOCO-X inapplicable, with size-matched
random pseudo-groups where informative. Engineered group-random targets based
on X clusters deliberately create learnable X structure. Successful prediction
does not show biological groups, physical independence or real-data label leakage.

## Reusable evidence versus missing experiments

| Existing evidence at inspected HEAD | Reuse | Still missing for v2 |
|---|---|---|
| 137 frozen paired X profiles; 43 source-permitted public profiles | Descriptors and representation/neighborhood changes without refitting | Curated original-database support and overlap; no portal-level collapsing |
| 682 complete primary quantitative tasks, fixed PLS/Ridge | Baseline skill, target semantics, eligible development populations | Common paired stress outcomes for most targets; conditional-G database model |
| 35 public / 48 authorized-local descriptor/outcome joined views | Exploratory source-view screens | These ordinary-CV screens are not baseline-adjusted deterioration tests |
| Five selected raw/SNV stress contexts; four local paired successes, three public; one unsupported pair | Matched evaluation, exact-size control, model/pipeline effects | Broader all-target database coverage, intervals and independent confirmation |
| Five declared-plot tasks | Paired common-observation grouping sensitivity | Exact size control and verified independence; these were grouped folds, not exhaustive LOGO |
| Historical Perten/litter/tablet/FastAOM experiments | Existing declared scopes, predictions and limitations | Compatible new estimands/designs, not retrospective confirmation |
| No TabICL execution manifest found in tracked evidence | Record it as unavailable here; import an accessible content-bound result only if supplied | Provider/configuration, split, target and prediction-lineage parity before comparison |
| No recorded v2 random-target or weak-group-signal program; no SPXY campaign identified | Existing native PLS/Ridge and split infrastructure | Qualified SPXY provider, frozen generators, complete null pipeline and database-aware inference |

All current cross-source associations, context/pipeline contrasts, plot contrasts,
single-target illustrations and retrospective v2 derivations remain exploratory.
None validates a universal risk scalar, causal shortcut fraction, nominal leakage
probability, genuine new-biological-population independence or low-risk certificate.
Absence of a strong ordinary-skill correlation is not failure of this revised
question. Future preregistration, random-target calibration and independent
database confirmation are **missing experiments**, not accomplished findings.

## Deliverables and operational boundary

The proposed [hierarchical schema](../schemas/structural-fragility-research.v2.schema.json)
and [illustrative design](examples/structural-fragility-v2.design.json) separate
portal, original database, source, target, split/protocol, model and synthetic
mechanism. Unknown original identities and overlap are explicit. This is a proposed
research record format, not a replacement for existing result schemas or a new
framework. Runtime cross-reference/identity checks would be qualified before use.

Schema fields distinguish an internal `database_record_id` from a potentially
unknown `original_database_id`. Protocol records carry the split, group basis,
outer-label boundary and reference/stress regimes; experiment records bind source,
target or synthetic mechanism, estimator, representation, support and outcome
states. Numeric errors cannot be negative; unsupported outcomes have null values
and explicit reasons. LOGO cannot be assigned an X-derived group basis.
Record-ID resolution, duplicate identities, overlap blocks, paired-membership
parity and frozen generator completeness remain semantic checks required before
execution, not guarantees supplied by JSON Schema alone. The schema deliberately
does not assert independent confirmation.

The design example contains no actual observations or model outcomes. Validate it
with the installed JSON Schema provider, without any fitting:

```python
import json
from jsonschema import Draft202012Validator

with open("schemas/structural-fragility-research.v2.schema.json") as stream:
    schema = json.load(stream)
with open("docs/examples/structural-fragility-v2.design.json") as stream:
    example = json.load(stream)
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(example)
```

The [bounded pilot](STRUCTURAL_FRAGILITY_V2_PILOT_PLAN.md) estimates fits, time and
resources. This revision makes zero model fits, reserves zero campaign bytes and
raises no storage ceilings. Public Methods/Preflight/DAG remain kernel owners;
missing generic SPXY, inference or interval capabilities are upstream proposals,
not Python numerical fallbacks. No data, frozen scientific artifact, package
behavior, numerical implementation or upstream repository is changed.

Documentation/schema checks, repository test execution, preserved-file counts and
measured storage are recorded in the [revision review](audit/structural-fragility-research-v2-review.json).
