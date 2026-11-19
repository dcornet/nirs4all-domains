# nirs4all-domains

F4.2 adds an explicit **train-fitted PCA / test projection** operation and a
separate indexed-fold T²/Q monitor. Import and review train/test partitions,
then use “How do test observations sit relative to train?”. FlexiblePCA is fitted
on train only; its live state is checked before and after both transforms.
No Y or predict spectrum is accessed. Raw F4.0 neighbors and F4.1 factor–PCA
associations retain their original evidence and fitted bases.

Monitoring values and empirical thresholds come from Methods 1.3.13 / ABI 2.20.
Unknown/dependent experimental units do not gain independently calibrated limits.
Neither a distance nor a crossing is a prediction-failure or leakage probability.
FlexiblePCA eigenvalues/rank resolution remain explicitly unavailable, rather
than borrowed from another PCA. See the [protocol](docs/browser/F4_2_SCIENTIFIC_PROTOCOL.md),
[user guide](docs/browser/F4_2_USER_GUIDE.md), [fit/transform contract](docs/browser/F4_2_FIT_TRANSFORM_CONTRACT.md)
and [qualification record](docs/browser/F4_2_VALIDATION.md).

F4.1 adds explicit factor–PCA associations to the local browser workflow.
Import and review keyed X/Y/M, run an admitted train-only (or declared
unpartitioned) structure operation, then select a factor under “Which factors
are associated with spectral structure?”. The operation reuses that PCA;
categorical factors report component-wise eta², continuous factors use explicit
Pearson or Spearman. Y is absent and test M is excluded from the main analysis.
Counts, missingness, dependencies and inference limitations accompany each
result. Color changes are display only; exporting observation-level factor
colors requires a separate source-permission declaration, independently of
report annex selection. See the [scientific contract](docs/browser/F4_1_SCIENTIFIC_PROTOCOL.md),
[binding usage](bindings/wasm/README.md) and
[execution record](docs/browser/F4_1_VALIDATION.md) for qualification.

Advanced inference uses a separate local JSON design record attached after PCA
(64 KiB maximum), with the exact dataset/PCA fingerprints and prospective family.
It is not part of the hashed IO import specification. Loading it performs no
calculation and establishes no independence; an explicit subsequent run asks
Rust to check the external assumptions and dependencies. Ordinary use remains
descriptive, including when stronger inference is unavailable.

[F3.5 report customization](docs/report/F3_5_USER_GUIDE.md) adds selectable
documentary supplements around a mandatory scientific core, integral machine
evidence and uncapped printing. Qualification and publication are tracked in its PR.

The [F3 technical consolidation](docs/technical/F3_RELEASE_REPORT.md) documents
selective dependency updates, the unchanged Preflight/Methods contract, actual
WASM/worker checks and bounded before/after measurements. Its PR preview and
qualification are separate from publication of main on GitHub Pages.

The [browser demonstration](demo/README.md) adds an optional Rust/WASM consumer
with one-shot local X/Y/M import through IO/Formats. A file or folder drop
starts normal import without mandatory review or confirmation; the shared
Dataset Builder remains an opt-in editor before final loading or under Data
settings after loading. Import preserves declared partitions and missingness
without fitting. Each selected operation receives its own X/M access scope,
and no Y value enters
a scientific request or report export. Current paths include train-only
structure, raw train-reference/test-query neighbors, documentary metadata
audits, and explicit transductive train-plus-test structure that excludes
predict rows. Unpartitioned data retain the legacy full-source descriptive path.
The F4.1 association and F4.2 train-fitted support operations have separate
qualification records; they do not broaden this original F4.0 protocol. The demo
also provides conditional intended-use reading and offline
HTML/Markdown/JSON exports. The
[one-shot import guide](docs/browser/ONE_SHOT_IMPORT_USER_GUIDE.md) explains
the default workflow and optional settings. Qualified saved D1–D6.1 examples
retain their original annotations and are explicitly separate from browser
calculations. See the
[capability matrix](docs/WASM_CAPABILITIES.md), [user guide](docs/WASM_DEMO_GUIDE.md),
and F4.0 [access policy](docs/browser/F4_0_DATA_ACCESS_POLICY.md),
[import architecture](docs/browser/F4_0_IMPORT_ARCHITECTURE.md),
[native/WASM compatibility](docs/browser/F4_0_NATIVE_WASM_COMPATIBILITY.md), and
[remaining capabilities](docs/browser/F4_0_REMAINING_CAPABILITIES.md).
Worker startup phases, asset-failure diagnostics, and the current browser
validation evidence are documented in the [worker-loading record](docs/technical/WORKER_LOADING_VALIDATION.md).

### Historical F3.5 browser publication

The [public demonstration](https://dcornet.github.io/nirs4all-domains/)
was verified after integration on `d1b14cceba483b5b5a0a4d9d0a42a1dd36270c92`,
with successful Pages/Windows/Ubuntu workflows and a 25-check public smoke.
Those F3.5 receipts do not qualify current F4.0 changes.
The [qualification review](docs/qualification/README.md) separates implementation,
tested numerical behavior, scientific scope and unvalidated practical utility.
F4.0 qualification is reported separately after its actual gates run.

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

The optional [conditional structural warnings](docs/STRUCTURAL_WARNINGS_API.md)
turn qualified saved evidence into concrete checks about physical units,
experimental factors, representation sensitivity, observed spectral support and
missing context. They reuse validation intent, work without Y and preserve
predictions/metrics. Each caution states its prerequisites and scientific limits.

```shell
python -m nirs4all_domains.structural_warnings docs/examples/structural-warnings/tablet.report.json --request docs/examples/structural-warnings/tablet.request.json --out results/tablet-warnings.json
```

```shell
python -m nirs4all_domains.multiscale docs/examples/multiscale/source-report.json --out results/branches.json
```

The evidence vocabulary separates **structural observation**, **validation
concern**, **empirical sensitivity**, **scientific mechanism hypothesis** and
**validated interpretation**. Domains can generically report the first three;
mechanism and validated-scope conclusions require their own supporting evidence.

## Which validation answers the intended prediction question?

The [standalone report consumer](docs/STANDALONE_REPORT_API.md) brings existing
D1/D2/D3 companions together in new HTML, Markdown and JSON artifacts. It validates
each companion against its original report, preserves source/population scopes,
and reads native Preflight reports without modifying Preflight or inventing
missing annotations. The HTML opens offline without a server or scientific runtime.

The [D5 decision-consistency qualification](docs/D5_WARNING_UTILITY.md) tests
contrasting simulated objectives on the same saved observations, including
negative and unavailable cases. Intended use and deferred checks are visible;
automated consistency is not expert-validated user effectiveness or a prediction
of calibration failure.

The optional [verification-readiness companion](docs/VERIFICATION_READINESS_API.md)
separates existing observation evidence, verification inputs, protocol readiness,
declared authorization and actual execution. It preserves old warning semantics
and requires an exact linked receipt before describing an action as executed.
It neither grants permission nor runs the proposed check.

The optional [D6.1 decision reading](docs/DECISION_SUMMARY_API.md) distinguishes
density settings from spectral representation changes, documentary checks from
new calculations, and conditional deployment questions from the selected D6
checks. Add `--decision-summary` to the existing report command for a compact
reading followed by expandable original evidence. It changes no scientific values.

[D1–D6.1 integration notes](docs/D1_D6_1_INTEGRATION.md) describe baseline,
licence/provider preservation and verification. Historical release pages retain
their original execution scope; a feature branch becomes `main` only after review
and an explicitly authorized merge.

```shell
python -m nirs4all_domains.report_view existing-report.json --d1 warnings.json --out results/review
python scripts/run_standalone_example.py --out results/tablet-review
```

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

The separate [nirs4all-structural-research repository](https://github.com/dcornet/nirs4all-structural-research)
now contains the owner's research work and source-specific qualification records.
The original boundary documents retain their historical proposal context.
[R1–R5 research program](docs/STRUCTURAL_GENERALIZATION_RESEARCH_PROGRAM.md)
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
describe actual interfaces and evidence. [Upstream alignment v1](docs/RELEASE_UPSTREAM_ALIGNMENT_V1.md)
records the current Preflight 0.1.6 / Methods 1.3.13 / DAG-ML 0.3.44 providers.

The [prospective 2026-11-17 storage policy](docs/technical/STORAGE_POLICY_50GB.md)
documents the owner's staged 50 GB ceiling and controller boundaries. Its CI
contract tests use synthetic temporary fixtures; local activation is measured
separately and does not claim an OS-level hard quota.

Raw inputs, sensitive identifiers and explicit restrictions remain protected.
Ordinary publishable aggregates follow source terms, not a catalog private-tier
veto. Data retain their source licenses.
[Release history](docs/RELEASE_HISTORY.md) preserves earlier reports and citations.
The [transition validation review](docs/audit/product-research-transition-review.json)
records documentation continuity, regression/package checks and measured resources.

## License

`nirs4all-domains` is dual-licensed open-source — **`CECILL-2.1 OR AGPL-3.0-or-later`**
(your choice), like the rest of the nirs4all ecosystem. See [`LICENSING.md`](LICENSING.md)
and the texts under [`LICENSES/`](LICENSES/). Data retain their source licenses.
