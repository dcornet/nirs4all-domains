# nirs4all-domains

[![Scientific gates](https://github.com/dcornet/nirs4all-domains/actions/workflows/ci.yml/badge.svg)](https://github.com/dcornet/nirs4all-domains/actions/workflows/ci.yml)

**Characterizing dataset structure, split sensitivity, calibration readiness,
and structural shortcut risks in near-infrared spectroscopy.**

A predictive model can perform well because it recognizes sample groups,
instruments, batches or spectral neighbors. That performance may not transfer
outside those structures. Domains develops reproducible diagnostics and
controlled evaluation protocols to investigate this distinction. Group structure
can also carry genuine chemistry: the objective is to measure dependence on
structure, without claiming causal identification of the underlying mechanism.

## Quick start

In this prepared Windows workspace:

```powershell
. .\scripts\dev-env.ps1
cargo build --workspace --locked
target\debug\n4domains.exe validate tests/fixtures/translation.json
target\debug\n4domains.exe analyze tests/fixtures/translation.json --out results/alpha5-quickstart/translation
target\debug\n4domains.exe structure tests/fixtures/structure/separated.json `
  --config configs/pilots/structure-v1.json --out results/alpha5-quickstart/structure
```

Structural output directories must be new. Structure, canonical coverage and the
optional predictive workflow emit separate versioned reports. See [setup](docs/INTEGRATION.md)
and [the frozen structural protocol](docs/CLUSTERING_STABILITY_PROTOCOL.md).

## Scientific motivation

Random splits may place repeated spectra, related physical samples or shared
laboratory references on both sides of an evaluation. Even without direct
leakage, a split can preserve group-specific X–Y relationships that disappear
when instruments, batches, sites or subpopulations change.

Dataset topology therefore matters alongside regression metrics. Predicting
between-group differences is different from predicting within-group variation.
Good regression performance alone does not establish a transferable trait
relationship. Stable X clusters alone do not establish shortcut learning.
Domains keeps intrinsic properties, structural associations, split effects and
predictive reliance as distinct scientific questions.

## Implemented features

Alpha.6 builds on the qualified alpha.4/5 protocols:

- Explicit versioned dataset/content/source/target/split/policy contracts.
- Physical/reference dependency checks, strict split guards and keyed joins.
- Native acquisitions and admissible homogeneous technical means, with membership,
  evidence, linked contexts and explicit exclusions.
- Train-fitted Methods PCA and held-out projection; heuristic neighbor/residual
  coverage; whole-component uncertainty and train-fit stability experiments.
- Separate train-only PCA–HDBSCAN–ARI characterization through Methods ABI 2.19:
  component subsampling, matched physical IDs, noise diagnostics, co-membership
  support, frozen parameter sensitivity and exploratory structural classification.
- Physical consensus for a bounded native-acquisition comparison.
- Reproducible JSON/Markdown reports, schemas and real Shootout/EcoSIS pilots.
- Optional development-only nested grouped PLS through DAG-ML and native Methods,
  with fold-local centering, selection and a fold-local mean baseline.
- Native metadata group–target association, physical-unit SS decomposition and
  whole-component uncertainty, with explicit saturated/missing-factor limits.
- Matched group-only, null, spectral and group+residual OOF predictions. Group
  means and residual targets are fitted independently in every inner/outer scope;
  unseen labels use the training global mean. Seen-level skill has its own
  eligibility and denominator.
- Algorithmic exclusion of retained Y_test from pre-training fits and selection.

HDBSCAN held-out assignment remains **unavailable**. No train+test fit is presented
as cluster prediction. Canonical slots for separate structural/predictive
workflows retain their earlier availability semantics.

## Structural shortcut risk research programme

| Experiment | Status |
|---|---|
| Unsupervised X structure and resampling stability | Implemented, separate alpha.5 report |
| Descriptive metadata-group/target variance decomposition | Implemented alpha.6; complete factor/target physical units only |
| Group-only prediction versus null and spectra | Implemented alpha.6; explicit seen/unseen fallback and matched OOF |
| Within-group predictive skill | Implemented alpha.6; qualified seen-level populations and fold-local residual fitting |
| Group-safe random, group-holdout and leave-group-out sensitivity | Alpha.7 design only |
| Global and within-group training-target permutation controls | Alpha.7 design only |

The [research specification](docs/STRUCTURAL_SHORTCUT_RISK.md) defines metrics,
populations, fold ownership, negative controls and gates. Eta-squared alone will
not establish predictive reliance. Spectral-group baselines require fold-local
construction and qualified held-out assignment. No universal shortcut probability
or calibrability ranking is provided.

Try the bounded workflow after installing the predictive bridge:

```sh
target/debug/n4domains dependence tests/fixtures/dependence/mixed.json --config configs/pilots/dependence-controls-v1.json --out results/dependence-demo --python python
python scripts/check_dependence_report.py results/dependence-demo/report.json
```

The output directory must be new. A metadata audit is written before fitting;
`--audit-only` stops there. `group-target` exposes the native-backed descriptive
slice separately. [Protocols](docs/STRUCTURAL_PREDICTIVE_BASELINES.md) describe
the exact populations, fold-local lineage and no-fit constant-residual case.

## Architecture and ecosystem

| Project | Responsibility |
|---|---|
| nirs4all-methods | Numerical PCA, summaries, neighbors, HDBSCAN, ARI, regression and association kernels |
| nirs4all-preflight | Intrinsic validity, identities, repetitions and descriptive characterization |
| nirs4all-domains | Task-specific structure, split/generalization protocols, evidence and provenance |
| nirs4all-datasets | Canonical data, catalog versions, accessors and provenance |
| DAG-ML | Native CV, model selection and refit in the optional predictive workflow |
| nirs4all-quality | Potential operational consumer; no integration claimed here |

Two Rust crates remain the core and CLI. Python provides keyed transport, batch
orchestration and a bounded native predictive adapter, without numerical fallbacks.
See [architecture](docs/ARCHITECTURE.md) and [method ownership](docs/METHOD_REUSE_MATRIX.md).

## Setup on Windows and Linux

Use Rust with a native linker and Python 3.11+ for optional workflows. Preflight
is pinned to `=0.1.0-alpha.1`. Tested Methods: `nirs4all-methods==1.3.6`, ABI
**2.19.0**. Structure requires ABI >=2.19; canonical coverage supports >=2.18.
Optional extras pin Datasets 0.3.11, DAG-ML 0.3.41 and scikit-learn 1.7.2
(Methods estimator facade base classes only, not a numerical backend).

```sh
python -m venv .venv
# Activate .venv/bin/activate on Linux, or .venv/Scripts/Activate.ps1 on Windows.
python -m pip install nirs4all-methods==1.3.6 './bridges/python[test,datasets,predictive]'
python -c 'from n4m._ffi import library_path; print(library_path())'
cargo build --workspace --locked
```

Select the printed library with `--methods-library` or
`N4DOMAINS_METHODS_LIBRARY`. On Windows, also add the sibling
`nirs4all_methods.libs` directory to PATH; `scripts/dev-env.ps1` handles this
prepared workspace. On Linux the executable is `target/debug/n4domains`.
Missing providers/capabilities yield explicit reasons, without numeric substitutes.

```sh
target/debug/n4domains batch --catalog-config configs/synthetic-batch.yaml --out results/synthetic
target/debug/n4domains batch --catalog-config configs/pilot.yaml --catalog-root /prepared/catalog --out results/pilot
target/debug/n4domains schema --out schemas
```

Batch requires the installed Python bridge; `--python` selects its interpreter.
The real catalog path is an explicit local input. CORN/UCPH remain disabled with
prerequisites in [the historical pilot](docs/REAL_DATA_PILOT.md). Data preparation
is documented in [the repeated pilot](docs/REPEATED_DATA_PILOT.md).

## Real-data evidence

| Task | Population / split | Exploratory outcome |
|---|---|---|
| Shootout X1 / assay | 155 train, 460 test; 40 validation exclusions | 73/460 coverage flags; both singleton representations agree |
| EcoSIS freeze-dried / LMA | 82 samples, 492 acquisitions; 65/17 primary sample split, 45/12 plots | 16/102 acquisition flags versus 4/17 mean flags; same four physical samples |
| EcoSIS development PLS | 65 means / 45 plots; five outer, three inner group folds | OOF RMSE 110.87 versus null 146.99 g/m²; R² 0.397 |
| EcoSIS train structure | 65 means / 45 components; 100 paired 80% subsamples, five settings | Insufficient information: primary all-noise; smaller clusters appear with weak sensitivity support |
| Shootout train structure | 155 source-row identity aliases; same structural design | Fragile structure: primary three groups, 27.10% noise; median eligible ARI 0.533 |
| EcoSIS genus baseline | Same 65 development means / 45 plots; 55 seen-level OOF samples | Group RMSE 114.78; group+residual 101.35 g/m²; exploratory paired gain 13.43 [0.60, 26.08] |

These are not established production or new-region performance. Coverage
fractions have different denominators and are not prediction-failure probabilities.
All 390 primary train acquisitions and 2151 bands remain in native coverage;
unavailable full moments do not block scores/coverage. See [predictive evidence](docs/PREDICTIVE_SANITY_CHECK.md)
and [actual structural results](docs/CLUSTERING_REAL_DATA_PILOT.md).
The [alpha.6 pilot](docs/STRUCTURAL_DEPENDENCE_REAL_DATA_PILOT.md) separates
association (genus eta²=.608 on 61 nonmissing means) from prediction on all 65.
Plots have eta²=.709 but every OOF plot is unseen, so their group baseline is
exactly the null. Taxonomic labels predict variation; this does not identify
shortcut learning, causal confounding or a fraction of chemical information.

## Scientific limitations

Coverage thresholds are heuristic. Metadata may not establish biological
independence, replicate subtypes or independent laboratory precision. Stable X
groups do not prove target confounding, predictive reliance or causality. Grouped
development CV is not production calibration. Structural categories are
operational and sensitive to native ordering/tie conventions at specified scales.
All-noise or a trivial cluster is not proof of stable grouping or a continuum.
Held-out HDBSCAN labels remain unavailable.

Datasets' public target accessor may materialize a full frame: algorithmic label
exclusion is tested, storage isolation is not promised. See [protocols](docs/SCIENTIFIC_PROTOCOLS.md),
[upstream proposals](docs/UPSTREAM_DEPENDENCIES.md) and [roadmap](docs/ROADMAP.md).

## Verification and project status

Exploratory **0.1.0-alpha.6**. **35 Rust + 34 Python = 69 tests pass locally**,
retaining all 56 alpha.5 tests. Two complete EcoSIS runs give byte-identical
reports; alpha.4 PLS predictions/artifacts and 30 old reports are unchanged.
[Alpha.6 Windows/Ubuntu CI passed](https://github.com/dcornet/nirs4all-domains/actions/runs/39007794047)
on source commit `28b99e9`. Detailed execution evidence is in
[VALIDATION.md](docs/VALIDATION.md); the badge links the actual workflow.

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
# Requires real N4DOMAINS_METHODS_LIBRARY, including ABI 2.19 structure gates:
cargo test --workspace --locked -- --ignored
cargo doc --workspace --no-deps --locked
# Set N4DOMAINS_BIN to the built CLI:
python -m unittest discover -s tests/integration -v
```

Provider-free tests do not qualify unavailable methods. CI executes real native
gates on Windows and Ubuntu. Validate structural output with
`python scripts/check_structure_report.py <report.json>`.
The [alpha.7 design](docs/SPLIT_STRESS_ALPHA7_PROTOCOL.md) proposes split-size
controls and training-target interventions; that programme is not executed here.

License: **AGPL-3.0-or-later**, selected by the owner. Native upstream libraries
and raw dataset bytes are not redistributed here. No upstream repository was modified.
