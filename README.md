# nirs4all-domains

Dataset characterization, calibration readiness and domain shift assessment.

Exploratory Rust-first diagnostics for an explicit **dataset + X source + Y target
+ split + evaluation policy**. Part of the [nirs4all ecosystem](https://nirs4all.org/).
This first slice compares a synthetic train/test task through real Methods kernels
and Preflight protocols, and exports JSON + Markdown. It does not estimate
calibration performance or provide a global readiness score.

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
python -m pip install nirs4all-methods==1.3.6 './bridges/python[test,datasets]'
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
n4domains batch --catalog-config configs/pilot.yaml --out results/pilot
n4domains schema --out schemas
```

The Python bridge must be installed for `batch`; use `--python` to select its
interpreter. Real pilot candidates are intentionally disabled with precise
acquisition, identity and split prerequisites. No real dataset campaign has been
completed. The catalog's advertised historical split is not proof that usable
partition labels are accessible.

## Guarantees and current limits

- Every observation has an explicit train/test partition and physical/group IDs.
  Preflight validates linked identities and detects exact spectral duplicates.
  Domain evaluation policy additionally rejects shared dependency/reference keys.
- PCA and centering fit train only. Test is projected with retained Methods
  loadings. Nearest-neighbor and reconstruction thresholds come only from train.
  Full covariance moments determine effective dimension even with truncated PCA.
- Pre-training omits test target values from Preflight, fit, thresholds and report
  fingerprints. Post-evaluation declares target access and the need for a new
  independent evaluation after a strategy change.
- Geometric diagnostics currently require one observation per physical sample.
  Repeated units retain Preflight diagnostics but geometry is `not_identifiable`
  until an explicit aggregation protocol is qualified.
- Six result dimensions preserve missing capabilities. Clustering, conditional
  confounding, nested PLS/PCR, AOM and inferential shift tests are deferred.

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
