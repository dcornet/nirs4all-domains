# nirs4all-domains

Dataset characterization, calibration readiness and domain shift assessment.

Exploratory Rust-first diagnostics for an explicit **dataset + X source + Y target
+ split + evaluation policy**. Part of the [nirs4all ecosystem](https://nirs4all.org/).
Alpha.4 compares synthetic tasks, the historical Shootout split and real EcoSIS
spectral replicates through Methods kernels and Preflight protocols. It exports
JSON + Markdown and a separate development-only nested PLS sanity check through
DAG-ML. It provides no production calibration or global readiness score.

## Run locally

Prerequisites: Rust with a working native linker; Python 3.11+ for the optional
dataset/batch bridge. Preflight `=0.1.0-alpha.1` is downloaded from crates.io.
The optional native Methods library must expose ABI **2.18 or later**. The tested
Windows wheel is `nirs4all-methods==1.3.6`, ABI **2.19.0**.

```powershell
# In this prepared workspace, load the isolated toolchain and wheel DLL path:
. .\scripts\dev-env.ps1
cargo build --workspace --locked
target\debug\n4domains.exe validate tests/fixtures/translation.json
target\debug\n4domains.exe analyze tests/fixtures/translation.json --out results/translation
```

On another machine:

```sh
python -m venv .venv
# activate .venv using your platform's activation command
python -m pip install nirs4all-methods==1.3.6 './bridges/python[test,datasets,predictive]'
python -c 'from n4m._ffi import library_path; print(library_path())'
cargo build --workspace --locked
n4domains analyze tests/fixtures/translation.json --methods-library /explicit/path/to/libn4m --out results/translation
```

Use `target/debug/n4domains` or add its directory to PATH. On Windows also add the
wheel's sibling `nirs4all_methods.libs` directory to PATH. Native libraries are
selected explicitly or with `N4DOMAINS_METHODS_LIBRARY`; no checkout search occurs.
Without Methods, integrity remains available and dependent metrics are explicitly
`unavailable`. An explicitly selected but incompatible library produces a failed
report. CLI exit codes: 0 partial/success, 2 invalid input/engine failure.

```sh
n4domains batch --catalog-config configs/synthetic-batch.yaml --out results/synthetic
n4domains batch --catalog-config configs/pilot.yaml --catalog-root /prepared/catalog --out results/pilot
n4domains schema --out schemas
```

The Python bridge must be installed for `batch`; use `--python` to select its
interpreter. Shootout X1 is enabled after local qualification: 155 train, 460 test,
40 explicitly excluded validation observations. CORN and UCPH remain disabled
with precise prerequisites. See [real-data qualification](docs/REAL_DATA_PILOT.md)
to prepare the local catalog. This is a raw-data reproduction with recorded hashes;
identity with the registry's historical canonical bytes is unverified.

## Guarantees and current limits

- Every observation has an explicit train/test partition and physical/group IDs.
  Preflight validates linked identities and detects exact spectral duplicates.
  Physical dependencies crossing partitions invalidate the split. Reference-only
  anomalies block X-Y qualification while preserving pure X diagnostics.
- The dataset bridge supports explicit `exclude` partition mappings, preserving
  excluded observation IDs and native counts, plus optional target units.
  A requested target absent from canonical data is an error.
- PCA and centering fit train only. Test is projected with retained Methods
  loadings. Nearest-neighbor and reconstruction thresholds come only from train.
  Public FlexiblePCA fit/transform retains complete-axis coverage when full
  covariance moments exceed their budget. Only metrics requiring unavailable
  moments become unavailable; no truncated moment is represented as exact.
- Pre-training omits test target values from Preflight, fit, thresholds and report
  fingerprints. Post-evaluation declares target access and the need for a new
  independent evaluation after a strategy change.
- Alpha.3 adds `policy.representation: technical_mean`: one vote per eligible
  physical sample, with Methods means of known homogeneous technical repeats.
  Default `native` retains the previous policy. Native acquisitions, linked
  contexts, reference dependencies, exclusions and exact coverage populations
  are exported. Biological/unknown repeats and cross-context units are never
  implicitly averaged. See [unit and reference rules](docs/UNITS_REFERENCES.md).
- Alpha.4 adds explicit `grouped_native` geometry, evidence-backed
  `technical_unspecified` means and whole-component coverage/refit bootstrap.
  EcoSIS keeps all 390 primary train acquisitions and all 2151 bands. The separate
  nested group PLS check uses only 65 development means: OOF RMSE 110.87 versus
  null 146.99 g/m², R² 0.397. See [the real repeated pilot](docs/REPEATED_DATA_PILOT.md)
  and [predictive evidence and limits](docs/PREDICTIVE_SANITY_CHECK.md).
- Six result dimensions preserve missing capabilities. Clustering, conditional
  confounding, AOM and inferential shift tests are deferred. The canonical report
  does not execute the optional development-only predictive workflow.

See [example report](examples/translation/report.md),
[architecture](docs/ARCHITECTURE.md), [reuse matrix](docs/METHOD_REUSE_MATRIX.md),
[protocols](docs/SCIENTIFIC_PROTOCOLS.md), [integration](docs/INTEGRATION.md),
[roadmap](docs/ROADMAP.md) and [validation evidence](docs/VALIDATION.md).

## Verification

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
# Requires N4DOMAINS_METHODS_LIBRARY; fails if it is missing:
cargo test --workspace --locked -- --ignored
cargo doc --workspace --no-deps --locked
# Set N4DOMAINS_BIN to the built executable:
python -m unittest discover -s tests/integration -v
```

The native scientific tests are explicitly ignored in the provider-free suite;
CI runs them separately and requires a real provider. Tests for future protocols
check honest unavailability, not scientific validity of those future methods.

License: **AGPL-3.0-or-later**, selected by the owner on 2026-10-16. No upstream
repositories were modified. The owner authorized the first GitHub commit/push
on 2026-10-16.
