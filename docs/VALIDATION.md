# Validation evidence — 2026-10-16

Executed locally on Windows x86_64, Python 3.11, Rust/Cargo 1.99.1. Preflight
0.1.0-alpha.1 came from crates.io; the numerical provider was the PyPI Methods
1.3.6 Windows wheel reporting ABI 2.19.0. Binary SHA-256 and source snapshots are
in [audit/upstreams.json](audit/upstreams.json); Rust dependency versions and
declared licenses are in [audit/rust-dependencies.json](audit/rust-dependencies.json).
The table below records the initial alpha.1 baseline. Alpha.2 adds a real local
Shootout reproduction, explicit native-partition exclusion and unit transport;
the alpha.2 local suite had **7 Rust + 13 Python tests passing**. See
[the pilot evidence](REAL_DATA_PILOT.md) and
[aggregate machine-readable record](audit/shootout-qualification.json).

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

The initial baseline did not analyze real pilot bytes. Alpha.2 now analyzes a
local Shootout raw reproduction, with registry canonical parity still unverified.
No upstream scientific test suite was rerun. The published alpha.1 baseline CI
passed on Windows and Ubuntu at commit `2855b6de48a01327001d458867b08f6ccb67724c`;
its private-data-independent gates include real native Methods execution.

Remaining release gates include broader real-data campaigns, repetition/context
designs on real grouped data, reference precision, grouped nested model validation, calibrated
coverage/shift uncertainty, full runtime dependency notices/SBOM if bundling and
remote publication approval. The repository remains an exploratory alpha.

## Alpha.3 unit/reference sprint

Expected behavior was written in UNITS_REFERENCES.md before the new tests.
The expanded suite is **12 Rust + 17 Python = 29 tests**. Native gates use the
actual Methods 1.3.6 / ABI 2.19.0 wheel, not a numerical mock. Runtime lookup was
rechecked for PCA, summary, neighbors, repeatability and three deferred ABI 2.19
symbols; PCA/summary/neighbors/repeatability execute in the suite.

New scientific evidence: known technical repeats retain native acquisitions and
contribute one physical-sample weight; a nonzero within-sample difference gives
the analytical mean; duplicating an identical repeat leaves the fit unchanged;
cross-partition physical identities block fitting; biological/unknown/missing-
context and multi-instrument repeats have explicit exclusions; shared references,
contradictions, censoring/composites and unit anomalies block X-Y while retaining
X. Known repeated test references contribute one post-evaluation outcome.
Native and aggregated no-test-fit/no-hidden-Y invariants pass. The report gives
every comparison row's physical ID and coverage denominator, mapped back to
native acquisition IDs.

Transport gates additionally cover equal X/Y dimensions with permuted IDs,
missing target join IDs, per-acquisition context/reference transport, duplicate
acquisition IDs, absent context and native validation exclusions. The pilot runner
refuses a nonempty output directory, preserving previous reports.

Formatting, clippy with warnings denied, workspace/native tests, rustdoc, bridge
integration, generated schemas and CLI report invariants are required for this
iteration. The real Shootout run executes both policies twice, reproduces each
report exactly, and matches all four retained alpha.2 scalar metrics. The 40
validation exclusions and unavailability of original reference IDs remain
explicit. See REAL_DATA_PILOT.md and its alpha.3 aggregate record.

These tests qualify the stated representation rules and small controlled means;
they do not establish laboratory independence, arbitrary ICC parity, paired
multi-instrument geometry, independent-component uncertainty or leakage-safe
nested model selection. Those remain separate scientific gates.
