# nirs4all-domains

**nirs4all-domains characterizes structural organization, population support and
evaluation-related limitations in NIRS datasets, helping researchers choose
appropriate validation strategies and interpret calibration results.**

[![Scientific gates](https://github.com/dcornet/nirs4all-domains/actions/workflows/ci.yml/badge.svg)](https://github.com/dcornet/nirs4all-domains/actions/workflows/ci.yml)

Domains is a reusable diagnostic product. It is useful with X alone, without Y,
complete group metadata, a trained predictor, a demonstrated shortcut mechanism
or a known deployment scenario. Descriptive diagnostics do not wait for H1–H5
confirmation. Missing evidence limits the relevant interpretation, not every
available diagnostic.

## Structural evidence and its limits

| Capability | Available evidence and qualification |
|---|---|
| X-only geometry and populations | Raw/SNV PCA, applicable exact effective dimension, continuity and density profiles; missing full moments remain explicit |
| Neighborhoods, proximity and support | Native distances/neighbors and dependency-aware comparisons; query sampling and admissible references are documented |
| Discrete and multi-scale structure | Qualified selected-branch persistence/support sidecar, original hierarchy references and explicit missing/resampling states |
| Representation sensitivity | Paired raw/SNV geometry, partition agreement and neighborhood changes |
| Metadata corroboration | Factor associations, agreement/disagreement and unknown correspondence; crossed factors need not form a tree |
| Evaluation partitions | Train-fitted projection, overlap/extrapolation diagnostics and known identity/reference guards |
| Compatible model results | Exploratory PLS/Ridge and historical FastAOM sensitivity evidence, bound to source, target, split and pipeline |
| Reusable reporting | Explicit status/reason/value, uncertainty scope, provenance, original axes and source-specific limitations |

A cluster is an X observation, not a biological batch or proof of a harmful
shortcut. Membership strength is not a probability. Weak clustering does not
certify low risk; a protocol gap is not a causal shortcut percentage. There is
no universal deployment-quality label or mandatory low-risk certification.
See [method ownership](docs/METHOD_REUSE_MATRIX.md) and the
[multi-scale audit and research concept note](docs/MULTISCALE_AND_AUGMENTATION_NOTES.md).

The optional [D1 persistence/support descriptor](docs/SELECTED_BRANCH_PERSISTENCE.md)
describes one existing density fit without Y or another model. It reports
selected branches, noise, per-cluster persistence and observation support,
keeping resampling robustness and independent-unit support distinct.
The [public worked example](docs/examples/multiscale/README.md) retains the original tree.

```shell
python -m nirs4all_domains.multiscale docs/examples/multiscale/source-report.json --out results/branches.json
```

The evidence vocabulary separates **structural observation**, **validation
concern**, **empirical sensitivity**, **scientific mechanism hypothesis** and
**validated interpretation**. Domains can generically report the first three;
mechanism and validated-scope conclusions require their own supporting evidence.

## Which validation answers the intended prediction question?

| Intended use | Candidate evaluation, subject to actual dependencies | Supported interpretation |
|---|---|---|
| Within-experiment proof of concept | Representative/within-population validation with repeat and shared-reference controls | Exploitable X–Y relation within observed support, not independent transfer |
| Operational prediction in a stable known context | New-specimen, acquisition/session, batch or time holdout matching the process | New predictions within the defined domain, subject to verified unit assumptions |
| Prediction outside the experimental context | Hold out the relevant genotype, treatment, site, campaign, instrument, lab or entire experiment; external data where supported | Transfer only to the kind of unseen context actually tested |

KFold, SPXY, GroupKFold and LOGO answer different questions; none is universally
superior. A categorical column alone does not justify GroupKFold. Genotype
holdout is not new-experiment validation; block holdout is not new-instrument
transfer. Entire-experiment holdout has a different scope from a group excluded
inside that experiment. SPXY must not use external evaluation Y for calibration
selection. Indivisible specimens and reference dependencies always remain intact.

If intended use is unknown, report several conditional interpretations rather
than choose a single correct split. The optional [validation-intent annotation](docs/VALIDATION_INTENTS.md)
records population, group basis, unseen context, support, transduction, limitations
and supported/unsupported claims. The Python API/CLI reads existing reports;
it adds no fit and leaves their predictions and metrics unchanged.

```shell
python -m nirs4all_domains.validation_intent docs/benchmarks/alpha17/tablet-pilot-summary.json --intent docs/examples/validation-intent/tablet.request.json --out results/tablet-intent.json
```

This writes a linked JSON annotation and Markdown interpretation. Omit `--intent`
for three conditional readings. See the [worked example](docs/examples/validation-intent/README.md)
and [API/CLI reference](docs/VALIDATION_INTERPRETATION_API.md).

LOCO-X (Leave-One-X-Cluster-Out) remains an exploratory geometric support test.
Full-X construction is explicitly transductive and must not use held-out Y.
Treating it as a proxy for a particular deployment shift requires separate
evidence; it is not automatically physical or experimental LOGO.

The optional [D3 comparison interpreter](docs/COMPARISON_INTERPRETATION_API.md)
explains two existing predictive results without refitting. It checks target
and unit compatibility, evaluation identity matching, training/model conditions
and separate null definitions before describing an RMSE contrast. The
[public tablet example](docs/examples/comparison/README.md) shows why worse
absolute error can coexist with better skill against a different null.

```shell
python -m nirs4all_domains.comparison_interpretation reference.json stress.json --request comparison.json --out results/comparison.json
```

## Current implemented and experimental evidence

<!-- scientific-status:start -->
| Scientific unit | Executed full-bank status |
|---|---:|
| Catalog entries / declared source views | 164 / 171 |
| Complete raw/SNV source profiles | 137 |
| Partial profiles / failed X attempts | 0 / 14 |
| Views with source-permitted public profile values | 43 |
| Resource-deferred / analysis-not-authorized views | 12 / 8 |
| Declared source/target tasks | 2054 |
| Complete / partial reference tasks | 713 / 5 |
| Complete primary quantitative reference tasks | 682 |
| Successful native reference fits / attempts | 4353 / 4368 |
| Public source views joined to quantitative outcomes | 35 |
<!-- scientific-status:end -->

The table is generated from [campaign status](docs/campaign/status.json).
Source views, catalog entries, targets and folds are not independent experimental
databases. Original-database/overlap support remains incompletely curated; EcoSIS
collections are not collapsed into one database merely because they share a portal.
Research fit counts document executed evidence, not completed product features.
No universal structural-risk model or causal mechanism has been validated.

- [Per-source structural evidence](docs/campaign/source-matrix.md) and [JSON matrix](docs/campaign/structural-matrix.json).
- [Compatible supervised task results](docs/campaign/experiment-matrix.md) and [context/pipeline comparison](docs/campaign/confrontation.json).
- [Scientific results, figures and limitations](docs/ALPHA18_SCIENTIFIC_RESULTS.md).
- [Source attribution and aggregate permissions](docs/campaign/source-attribution.md).

## Product roadmap

| Milestone | Permanent product objective | Current status |
|---|---|---|
| D1 - Comprehensive structural evidence | Authorized X, factors, proximity and qualified multi-scale geometry | 137/171 complete raw/SNV profiles; selected-branch persistence/support v1 qualified; broader multi-scale families remain partial |
| D2 - Validation interpretation | Deployment intent, dependencies, group evidence and support | Optional v1 API/CLI annotation with scenario and compatibility tests; no automatic selector |
| D3 - Model-result contextualization | Compatible prediction results alongside scope, support and limitations | Optional read-only comparison v1 API/CLI; target/units, ID matching, null scope and baseline-context guards; 682 historical primary tasks |
| D4 - Usable integration | Stable reports and public Datasets/Preflight/Methods/model interfaces | Existing two-crate core/CLI and thin bridge; read-only research interface specified |
| D5 - Evidence-supported guidance | Validated and calibrated diagnostic interpretation | Task-specific evidence exists; no universal shortcut or deployment certification |

[D1–D5 roadmap and bounded next decisions](docs/ROADMAP.md) distinguish implemented,
planned and unverified capabilities. Research success does not automatically add a
product feature, and missing causal confirmation does not remove useful diagnostics.

## Associated research, with a separate owner

A prospective program investigates mechanisms, database-level inference, random
and weak group-dependent targets, model remedies and synthetic spectra. Useful
chemical signal may coexist with small structural contributions. It reuses
Domains evidence; speculative estimators and generators do not become product
behavior by default. [Product–research ownership](docs/PRODUCT_RESEARCH_BOUNDARY.md)
defines promotion criteria and upstream model ownership.

The proposed future repository is `nirs4all-structural-research`; this assignment
does not create it. [R1–R5 research program](docs/STRUCTURAL_GENERALIZATION_RESEARCH_PROGRAM.md)
and the [read-only interface/transition plan](docs/RESEARCH_INTEROPERABILITY_AND_TRANSITION.md)
are proposals, not authorization for fitting, GPU setup, archive migration or publication.

The [v2 research design](docs/STRUCTURAL_FRAGILITY_RESEARCH_V2.md),
[bounded v2 pilot](docs/STRUCTURAL_FRAGILITY_V2_PILOT_PLAN.md), associated schema/example,
[frozen H1–H5](docs/ALPHA13_SUPERVISED_PREREGISTRATION.md) and
[M1–M5 research lineage](https://github.com/dcornet/nirs4all-domains/blob/5b0354a236318e42188a17f9703363a33e6df706/docs/ROADMAP.md)
remain intact and accessible. Their research questions do not define the generic product.

## Integration and reproducibility

Two Rust crates provide core/CLI contracts; Python provides transport and batch
orchestration. Public Methods/Preflight and DAG APIs retain numerical ownership.
No new estimator, recursive clustering engine or result schema is introduced by
this separation. [Architecture](docs/ARCHITECTURE.md), [protocols](docs/SCIENTIFIC_PROTOCOLS.md),
[validation](docs/VALIDATION.md) and [storage/reproducibility](docs/STORAGE_AND_REPRODUCIBILITY.md)
describe actual interfaces and evidence.

Raw inputs, sensitive identifiers and explicit restrictions remain protected.
Ordinary publishable aggregates follow source terms, not a catalog private-tier
veto. Data retain their source licenses; software is AGPL-3.0-or-later.
[Release history](docs/RELEASE_HISTORY.md) preserves earlier reports and citations.
The [transition validation review](docs/audit/product-research-transition-review.json)
records documentation continuity, regression/package checks and measured resources.
