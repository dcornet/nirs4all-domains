# nirs4all-domains

**Can the structural properties of NIRS datasets, measured before training a predictive model, help anticipate when that model's apparent performance will depend on dataset-specific shortcuts and fail to generalize?**

nirs4all-domains studies how spectral population structure, experimental context,
sample similarity and distribution shift influence NIRS model evaluation, so that
estimator and pipeline comparisons can be made on scientifically understood benchmarks.

[![Scientific gates](https://github.com/dcornet/nirs4all-domains/actions/workflows/ci.yml/badge.svg)](https://github.com/dcornet/nirs4all-domains/actions/workflows/ci.yml)

## Why study structure before comparing models?

Good NIRS prediction may reflect useful chemistry, population composition, close
samples, acquisition context, shared references, or interacting mechanisms.
Conventional validation may not distinguish them. Estimators and preprocessing
pipelines can respond differently to the same population structure. The long-term
target is the predictive usefulness of X-only descriptors for anticipating
**generalization fragility**, rather than an unsupervised structure score alone.

| Evidence level | What it establishes | What it does not establish |
|---|---|---|
| Observable X structure | Subpopulations, gradients, neighborhoods/proximity, representation sensitivity, stability and support | A cluster is not proof of shortcut learning; weak clustering is not low-risk certification |
| Potential shortcut susceptibility | Frozen, falsifiable predictions about validation sensitivity | Genuine chemistry may generate strong structure; no universal shortcut probability |
| Observed predictive sensitivity | Model responses to estimator, preprocessing, split, grouping and support changes | Poor transfer alone does not identify causal shortcut reliance |
| Scientific generalization evidence | Reproducibility on genuinely independent studies or supported experimental units | Views, folds and targets are not automatically independent studies |

## Scientific workflow

1. Characterize the authorized bank systematically, mainly with X.
2. Freeze structural-susceptibility hypotheses and descriptor definitions.
3. Evaluate simple standardized supervised models across broad source/target coverage.
4. Compare reference evaluation with meaningful structural-stress designs.
5. Test whether the frozen descriptors anticipate fragility, retaining contrary and null cases.
6. Build purpose-qualified benchmark suites for future estimator and pipeline comparisons.

Discovery, exploratory confrontation and independent confirmation remain distinct
while these activities overlap operationally. Existing H1-H5 stay frozen.

## Implemented methods

Catalog-driven screening; raw/SNV geometry; PCA and applicable exact effective
dimension; neighborhood, density and near-proximity profiles; HDBSCAN and
conditional stability; metadata corroboration; supported group/structural splits;
native PLS/Ridge and historical FastAOM experiments. Methods/Preflight/DAG own
numerical kernels. Missing full covariance moments do not disable valid PCA or
neighborhood evidence. [Method ownership](docs/METHOD_REUSE_MATRIX.md) and
[scientific protocols](docs/SCIENTIFIC_PROTOCOLS.md) state actual capabilities.

## Current scientific evidence

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

[Machine-readable status](docs/campaign/status.json) is the status source. These
are source views, not independent studies. The full-bank campaign accounts for
every entry; local limitations restrict only the affected stage or claim.

The new campaign includes 682 complete primary quantitative tasks. Across 35
source-permitted paired views, none of six tested X descriptors exceeds absolute
Pearson correlation .50 with median target CV skill for either fixed model.
Context experiments show that SNV reduces matched stress deterioration on tablets,
increases it on aquatic-leaf LMA, and has opposite effects on PLS and Ridge for
leaf nitrogen. These exploratory effects combine context, chemistry and training
composition. [Outcomes and limitations](docs/ALPHA18_SCIENTIFIC_RESULTS.md)
retain null and adverse cases. **No general cross-study predictive relationship
between X-only descriptors and future fragility has been validated.**

## Permanent scientific milestones

| Milestone | Scientific output | Current evidence/status |
|---|---|---|
| M1 - Comprehensive structural characterization | Multidimensional X-only profile for every accessible eligible source | 137/171 complete raw/SNV profiles; every source accounted for |
| M2 - Hypothesis formation | Frozen, interpretable predictions with possible falsifying outcomes | H1-H5 registered; definitions remain unchanged |
| M3 - Broad supervised confrontation | Source x target x estimator x evaluation-design matrix | 682 complete primary quantitative tasks, plus context and plot sensitivity; failures retained |
| M4 - Cross-dataset scientific validation | Predictive usefulness, false positives/negatives and uncertainty | Independent-study relationship not established; matched outcomes and adequate study support needed |
| M5 - Qualified benchmark suites | Frozen purpose-specific benchmark subsets | Task-specific exploratory suites exist; stronger general-purpose qualification remains pending |

Goals and completion measurements are stable in the [scientific roadmap](docs/ROADMAP.md).
Only status and supporting evidence change between releases.

## Use the scientific evidence

- [Scientific findings, distributions and figures](docs/ALPHA18_SCIENTIFIC_RESULTS.md).
- [Per-source structural matrix and limitations](docs/campaign/source-matrix.md).
- [Machine-readable structural matrix](docs/campaign/structural-matrix.json).
- [Supervised task matrix and limitations](docs/campaign/experiment-matrix.md).
- [Descriptor, model, context and pipeline confrontation](docs/campaign/confrontation.json).
- [Frozen hypotheses and outcome contracts](docs/ALPHA13_SUPERVISED_PREREGISTRATION.md).
- [Source attribution and derived-output permissions](docs/campaign/source-attribution.md).
- [Benchmark registry and task protocols](docs/SCIENTIFIC_PROTOCOLS.md).
- [Storage and reproducibility instructions](docs/STORAGE_AND_REPRODUCIBILITY.md).

The matrices cover the consolidated bank, structural profiles, tasks and outcomes.
Ordinary aggregates follow actual source terms, irrespective of catalog private
tier. Raw data, sensitive identities and explicit restrictions remain protected.

## Technical integration and reproducibility

Two Rust crates provide the core/CLI; Python supplies dataset transport and batch
orchestration. Public Methods/Preflight and DAG APIs provide native computation.
Keep Cargo.lock and explicit dataset/content/source/target/split/policy contracts.
[Architecture](docs/ARCHITECTURE.md), [validation](docs/VALIDATION.md), and
[upstream capability notes](docs/UPSTREAM_DEPENDENCIES.md) document integration.

Actual native, bridge, report and package execution is recorded in the
[validation report](docs/audit/alpha18-validation.json); completed Windows/Ubuntu
execution is recorded in [CI evidence](docs/audit/github-ci-alpha18.json). Data sources
retain their own licenses and attribution, including the noncommercial conditions
on the two new aquatic-plant aggregate sets. Software is AGPL-3.0-or-later.

Historical citations, full scientific reports and alpha-by-alpha implementation
notes remain in [release history](docs/RELEASE_HISTORY.md). Historical artifacts
are preserved; no past result is relabeled as independent confirmation.
