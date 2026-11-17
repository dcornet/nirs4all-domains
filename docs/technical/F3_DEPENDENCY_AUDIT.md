# F3 dependency decisions

Snapshot date: 2026-11-16. Baseline installed/locked frontend is F2 `f4289f5`.
The [complete snapshot](F3_DEPENDENCY_SNAPSHOT.json) records every npm/Cargo lock
entry, archive integrity/checksum, declared licence, latest stable registry lookup
and the qualified Python cohort. Availability does not prove compatibility.
Candidate installations must be verified by the exact-head Windows/Ubuntu runs
linked from the F3 PR. The constrained local installation remains the baseline;
it is not mislabeled as the candidate. No installed owner package is patched.

| Dependency | Baseline | F3 selection | Stable available at audit | Reason / compatibility checks |
|---|---:|---:|---:|---|
| Preflight Rust | 0.1.6 | **=0.1.6** | 0.1.7 | Absolute owner lock; source, API and ABI remain unchanged |
| Methods native/WASM | 1.3.13 | **1.3.13** | 1.3.17 | Frozen ABI 2.20 and version-bound evidence; no unqualified cohort migration |
| IO WASM | 0.2.14 | **0.2.14** | 0.3.3 | New materialization/numeric-wire surfaces require separate identity/population qualification; published idiomatic ESM still depends on Node glue |
| Formats WASM | 0.2.14 | **0.2.14** | 0.2.17 | Published Node glue remains; no qualified public browser artifact replacing the adapter; keep IO/record cohort |
| nirs4all-ui | 0.2.1 | **0.2.5** | 0.2.5 | Published qualification entry/props retained, optional table/reference additions; actual figures, statuses, exports and accessibility rechecked |
| AJV | 8.17.1 | **8.20.0** | 8.20.0 | Reviewed ReDoS advisory; schema validation/status/hash regression gates |
| Vite | 7.3.6 | **7.3.8** | 8.3.8 | Supported security backport; avoid unrelated major bundler migration |
| React plugin | 5.0.0 | **5.2.0** | 6.3.0 | Same major, declared Vite 7 support; build, strict typing and browser tests |
| TypeScript | 5.8.3 | **5.9.3** | 7.0.2 | Same-major maintenance; avoid unmeasured compiler migration; actual typecheck required |
| Node types | 22.20.1 | **24.19.2** | 26.6.6 | Align types with selected Node 24 runtime; no Node 26 API assumption |
| Playwright Core | 1.58.2 | **1.65.1** | 1.65.1 | Current engine maintenance; all existing APIs/interactions plus actual Chromium/Firefox WASM |
| React / DOM | 19.2.3 | **19.2.3** | 19.3.1 | No relevant installed-package alert or measured reason for runtime minor migration |
| React / DOM types | 19.2.7 / 19.2.3 | unchanged | 19.3.0 / 19.3.0 | Keep coherent React 19.2 typing surface |
| Vitest | 4.1.12 | unchanged | 5.1.0 | Latest 4.x already; supports Vite 7, no necessary major migration |
| axe-core | 4.14.1 | unchanged | 4.14.1 | Test-only MPL-2.0, outside production bundle |
| CommonMark / types | 0.31.2 / 0.27.10 | unchanged | same | Existing escaping/AST adversaries preserved |
| Rust compiler | moving stable | **1.100.0** | 1.100.0 | Explicit toolchain; declared MSRV 1.85 is not separately requalified |
| wasm-pack | 0.13.1 | **0.13.1 + archive SHA-256** | 0.15.1 | Existing path sufficient; do not change generated-binding toolchain without need |
| Serde / JSON / schemars | 1.0.229 / 1.0.154 / 1.2.3 | unchanged | same | Exact Cargo.lock; no schema/order/hash churn |
| SHA2 / libloading | 0.10.9 / 0.8.9 | unchanged | 0.11.1 / 0.9.1 | No applicable advisory; avoid trait/native-loader migration |
| wasm-bindgen / js-sys | 0.2.130 / 0.3.107 | unchanged | same | Paired generated glue, actual compile and execution |
| rand / rand_chacha | 0.8.5 / 0.3.1 | unchanged | 0.10.4 / 0.10.0 | Seeded historical controls; advisory reachability assessed separately |

All npm selections are exact, with reproducible lockfiles. The dependency-free
Playwright entry is updated from its version-specific registry metadata/integrity;
actual clean `npm ci` validates the result. Other candidate changes use npm's lock
resolver; no force-fix, owner edits or fallback packages. Runtime licences remain
the published declarations, including Methods' exact CeCILL-2.1 declaration.

Python constraints freeze the actual successful F2 Windows/Ubuntu cohort from
`scientific-gates` run 43898470343, rather than moving numerical oracles. That
includes Methods 1.3.13, DAG-ML 0.3.44, Datasets 0.3.11, scikit-learn 1.7.2,
NumPy 2.4.6, pandas 3.1.1, SciPy 1.17.1 and the existing FastAOM dependencies.
The CI installer is pinned to pip 26.3 and the bridge build backend to setuptools
84.2.1. Only engineering-only psutil 7.2.2 is added for process-tree observations. These
constraints do not install optional providers in the read-only workflow. Linux
uses the observed Python 3.11.18; Windows uses the observed available 3.11.9.
This platform difference is explicit, not a claim of identical Python binaries.
Broader Python/runtime security maintenance remains a separately qualified change.

Local Python happens to contain older Methods/DAG versions; it is not used for
native scientific qualification. Hosted CI selects the exact 1.3.13 library/DLL
directory before every bridge/native gate. Existing local compiled WASM 1.3.13
is reused only for the bounded synthetic binding checks.

GitHub actions are updated to reviewed Node-24-based releases and pinned by full
commit SHA: checkout 7.0.1, setup-node/setup-python 7.1.0, upload-artifact 7.0.2,
upload-pages-artifact 5.0.0 and deploy-pages 5.0.1. Rust action is SHA-pinned with
explicit compiler input. Node is 24.22.1. All gates remain; feature branches use
PR triggers instead of duplicate push+PR runs. See [security](F3_SECURITY_AND_LICENSING.md)
for transitive composite-action limitations and advisory scope.
