# Validation evidence — 2026-10-16

Executed locally on Windows x86_64, Python 3.11, Rust/Cargo 1.99.1. Preflight
0.1.0-alpha.1 came from crates.io; the numerical provider was the PyPI Methods
1.3.6 Windows wheel reporting ABI 2.19.0. Binary SHA-256 and source snapshots are
in [audit/upstreams.json](audit/upstreams.json); Rust dependency versions and
declared licenses are in [audit/rust-dependencies.json](audit/rust-dependencies.json).

| Gate | Actual evidence |
|---|---|
| Rust formatting | `cargo fmt --all --check` |
| Static analysis | `cargo clippy --workspace --all-targets --locked -- -D warnings` passes |
| Contracts / policy | 4 provider-free tests pass, including shared physical, individual, reference, reference-group and independent-group split rejection |
| Native science | 3 required-provider tests pass; combined run: **7 passed, 0 ignored**, using `--include-ignored` |
| Analytical geometry | Rank-one covariance trace 36, effective dimension 1, zero center shift / ratio 1 for identical empirical distributions, variance ratio 4, deliberate far/orthogonal shifts fully flagged |
| Reproducibility / leakage | Equal serialized scientific reports on repeated execution; Y_test mutation leaves pre-training report unchanged; test X cannot change fitted mean/loadings/thresholds; row-order scalar invariance within 1e-10 |
| Python transport | **7 tests pass**, including shuffled identity joins, ambiguous/absent split rejection, content pinning, explicit physical identity assumption, post-audit access and actual installed Datasets API to Rust CLI |
| Actual Datasets seam | 0.3.11 `get/sources/x/wavelengths/sample_ids/observation_ids/y/metadata/split/descriptor` exercised on synthetic canonical Parquet generated in a temporary local catalog |
| Batch resilience | Failed first task retained; later task still emits JSON/Markdown; rerunning a failed task cannot reuse a stale report |
| Export | CLI JSON validated against generated report schema and availability invariants; all controlled task fixtures validated against task schema |
| Native build / docs | Workspace executable, local `cargo install --debug` and rustdoc build pass |
| Python packaging | Bridge wheel built locally with `pip wheel --no-deps` |
| Campaign commands | Three synthetic tasks complete as exploratory partial reports; three real pilot candidates yield documented unavailable reasons |

`examples/translation/report.json` and `report.md` are actual CLI outputs. The
deliberate train/test translation produces center distance ~24.49489743,
dispersion ratio ~1 and outside fraction 1. These are controlled-input checks,
not empirically calibrated risk thresholds.

The synthetic suite includes all initial mandatory scenarios, plus missing X and
an orthogonal shift. Cluster, confounding and predictability fixtures assert
explicit unavailability because those protocols are deferred. They do **not**
validate HDBSCAN, conditional factor attribution or nested OOF PLS/PCR. Similarly,
the exact-duplicate fixture correctly warns even though the compared empirical
distributions are identical: distribution equality does not establish independent
evaluation samples.

No real pilot bytes were acquired or analyzed; no upstream scientific test suite
was rerun; no Linux or GitHub-hosted workflow execution has occurred. CI for
Windows/Linux is configured, with a mandatory separate native gate. Its future
successful execution must be recorded before claiming platform qualification.

Remaining release gates include a true real-data campaign, repetition/context
aggregation, reference precision, grouped nested model validation, calibrated
coverage/shift uncertainty, full runtime dependency notices/SBOM if bundling and
remote publication approval. The repository remains an exploratory alpha.
