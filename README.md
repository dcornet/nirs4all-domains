# nirs4all-domains

**To what extent do structural properties of NIRS spectral data contribute to statistically detectable, estimator- and target-dependent performance degradation when evaluation moves from representative or within-group sampling to structurally independent or out-of-support prediction — even when substantial genuine X–Y predictive signal remains?**

nirs4all-domains studies how spectral population structure, experimental context,
sample similarity and distribution shift influence NIRS model evaluation, so that
estimator and pipeline comparisons can be made on scientifically understood benchmarks.

[![Scientific gates](https://github.com/dcornet/nirs4all-domains/actions/workflows/ci.yml/badge.svg)](https://github.com/dcornet/nirs4all-domains/actions/workflows/ci.yml)

## Why study structure before comparing models?

Good NIRS prediction may reflect useful chemistry, population composition, close
samples, acquisition context, shared references, or interacting mechanisms.
Conventional validation may not distinguish them. Useful chemical signal and a
small group-dependent contribution can coexist. A statistically detectable
structural effect need not dominate prediction, and statistical significance
and practical magnitude answer different questions. Predictive dependence alone
does not identify a causal or undesirable shortcut.

The primary outcome is **validation sensitivity conditional on baseline skill**,
not absolute RMSE or unconditional model quality. For positive paired errors,
`G = log(RMSE_stress / RMSE_reference)` accompanies
`S_reference = 1 - RMSE_reference / RMSE_training_null` and, where valid,
common-null stress skill. Negative-skill tasks remain included. Effect sizes,
uncertainty, independent-database support and multiple comparisons matter;
there is no minimum 20%/30% deterioration rule or universal risk scalar.

| Evidence level | What it establishes | What it does not establish |
|---|---|---|
| Observable X structure | Subpopulations, gradients, neighborhoods/proximity, representation sensitivity, stability and support | A cluster is not proof of shortcut learning; weak clustering is not low-risk certification |
| Potential shortcut susceptibility | Frozen, falsifiable predictions about validation sensitivity | Genuine chemistry may generate strong structure; no universal shortcut probability |
| Observed predictive sensitivity | Model responses to estimator, preprocessing, split, grouping and support changes | Poor transfer alone does not identify causal shortcut reliance |
| Scientific generalization evidence | Reproducibility across original databases/populations with study and specimen dependencies accounted for | Views, folds and targets do not create additional independent databases |

## Scientific workflow

1. Characterize X and map original experimental databases, views and dependencies.
2. Freeze descriptors, target-aware questions and evaluation-specific estimands.
3. Compare representative/within-group and group- or support-exclusive prediction.
4. Test deterioration conditional on baseline skill, estimator and preprocessing.
5. Add IID random targets, group-random targets and useful spectral signals with weak injected group effects.
6. Synthesize at database level and build purpose-qualified benchmark suites.

Discovery, exploratory confrontation and independent confirmation remain distinct
while these activities overlap operationally. Existing H1-H5 stay frozen.

## Databases, validation contrasts and controls

The hierarchy is **repository/portal → original experimental database → spectral
source/view → target → validation protocol → estimator**. The original database
is the default macro-analysis unit. EcoSIS hosts multiple experimental databases;
sharing its portal, namespace or biological material does not make them one
database. Conversely, extra views, targets and folds do not create independent
replications. Known study/specimen overlap requires hierarchical dependence;
unknown overlap remains unknown. A curated independent-database count is not yet
available. Retain all admissible targets, report within-database median effects
and dispersion, give databases comparable influence, and examine aggregation and
source-family sensitivity. Never pool raw RMSE across different target units.

Two contrasts remain distinct. **SPXY versus LOGO** measures a benchmark-protocol
gap combining sampling, coverage, group novelty, training size and model response.
SPXY selection uses development labels only, with outer evaluation labels kept
untouched. **Known-group versus unseen-group prediction** preferably compares
common evaluation observations with whole-group size controls. True LOGO and
GroupKFold have different estimands. Neither contrast alone isolates a causal
shortcut contribution; indivisible sample/reference identities always stay intact.

When experimental groups are missing, **LOCO-X (Leave-One-X-Cluster-Out)** is an
exploratory X-defined stress test, not experimental LOGO or proof of physical-domain
transfer. Full-X partitions are explicitly transductive; held-out Y cannot choose
clusters or representations. Stability, noise, sizes, continuous geometry and
size-matched random pseudo-groups must be considered without forcing clusters.

The proposed controls complement real outcomes: IID Y audits null response;
group-random Y probes group recognition; controlled spectral signal plus weak
group effects probes additional dependence while useful signal remains. SPXY
needs both frozen-split randomization and per-realization split regeneration.
Favorable null scores or learning engineered cluster labels alone do not prove
real-target leakage. These extensions are **planned, not executed or validated**.
See the [versioned research design](docs/STRUCTURAL_FRAGILITY_RESEARCH_V2.md) and
[bounded pilot proposal](docs/STRUCTURAL_FRAGILITY_V2_PILOT_PLAN.md).

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
retain null and adverse cases. The correlation screens concern ordinary CV
skill, not the new conditional deterioration question; their weak associations
do not establish that the research question has failed. **No database-level
conditional fragility model, calibrated random-target program or independent
confirmation under this new design has been validated.**

## Permanent scientific milestones

| Milestone | Scientific output | Current evidence/status |
|---|---|---|
| M1 - Full-bank structural characterization | Database and view coverage with multidimensional X profiles | 137/171 complete raw/SNV profiles; database support not yet curated |
| M2 - Scientific structural hypotheses | Frozen X descriptors and conditional, target-aware questions | H1-H5 unchanged; v2 addendum is a prospective design proposal |
| M3 - Broad comparative supervised experiments | Distinct protocol-gap and known/unseen-group comparisons | 682 complete primary quantitative tasks; exploratory context/plot contrasts |
| M4 - Mechanism testing and statistical validation | Conditional deterioration, null controls and database-aware inference | Conditional model, null calibration and independent confirmation pending |
| M5 - Purpose-qualified NIRS benchmark suites | Benchmarks frozen by purpose and supporting evidence | Exploratory suites exist; weak clustering or favorable CV does not certify low risk |

Goals and completion measurements are stable in the [scientific roadmap](docs/ROADMAP.md).
The v2 revision refines their research questions while preserving M1-M5 and all
historical evidence; future releases update their status and supporting evidence.

## Use the scientific evidence

- [Scientific findings, distributions and figures](docs/ALPHA18_SCIENTIFIC_RESULTS.md).
- [Per-source structural matrix and limitations](docs/campaign/source-matrix.md).
- [Machine-readable structural matrix](docs/campaign/structural-matrix.json).
- [Supervised task matrix and limitations](docs/campaign/experiment-matrix.md).
- [Descriptor, model, context and pipeline confrontation](docs/campaign/confrontation.json).
- [Proposed database/source/target/model/synthetic hierarchy](schemas/structural-fragility-research.v2.schema.json).
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
