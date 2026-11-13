# Domains browser binding

This private, additive demo binding builds the existing Domains library as a
WASM cdylib. It adds no third Rust crate and consumes the public Preflight 0.1.6
provider contract with the published Methods 1.3.13 / ABI 2.20 WASM kernels.
It does not load a native shared library, DAG, Python or a numerical fallback.

From this directory, `npm run build:native` runs wasm-pack against the existing
crate with `--no-default-features --features browser-wasm`. A wasm32 target and
wasm-pack must already be installed. The generated `native/` directory is a build
artifact. Commit the workspace Cargo.lock; build on an authorized runner with
locked dependencies. Package version stays aligned with Rust alpha.17; this
private demo is not a new published scientific release.

```js
import { createDomainsRuntime } from '@nirs4all/domains';
const runtime = await createDomainsRuntime(); // inside an analysis worker
const report = runtime.analyze(input);        // BrowserRequest in index.d.ts
const reading = runtime.interpret(report, 'new_context'); // no new provider calls
```

`domains.browser_x.v1` accepts a single complete imported dense X source, its
unchanged strictly monotonic axis (in either direction), unique observation IDs and a
declared source-content SHA256. IO/Formats own parsing and assembly before this
call. No Y, target, split assignment, imputation, source fusion, aggregation or
physical-independence assertion is accepted. Optional group IDs exclude matching
groups from neighbor references but do not certify their scientific meaning.
The full imported X population is descriptive and explicitly transductive.

The protocol freezes raw representation, PCA up to min(20,p,n-1), the public
Preflight `resolved()` component contract, exact full-reference 8-neighbor
queries, and one HDBSCAN EOM setting (min_cluster_size=8, min_samples=4 including
self, allow_single_cluster=false). PCA scores, labels and membership strengths
are display data; the report never includes input spectra. Summary statistics
use Methods. It never retries a refused kernel with another setting. A missing
capability, budget refusal, numerical error, zero variance or malformed response
retains its reason and null value. All-noise output is descriptive, not low risk.

Limits precede fits: 32 MiB input JSON, 2,000 rows, 1,000,000 spectral cells and
25,000,000 products per kernel. Complete populations and references remain
intact; work over a per-kernel limit becomes unavailable, never an implicit
subset. Terminate the worker for cancellation; no asynchronous callback crosses
the synchronous Rust provider boundary. Actual process memory can exceed payload
size because WASM buffers and JSON copies coexist.

`domains.browser_reading.v1` is a pure intent-conditioned reading of the exact
scope/metrics fingerprint. It makes no provider call and cannot grant authority
or execution. D1-like within-fit persistence is descriptive only; this live
subset is explicitly **not** qualified parity with saved D1/D2/D6/D6.1 companion
APIs. Metadata associations, independent support, resampling robustness and
predictive performance stay unavailable. Existing saved-report consumers retain
their own schemas and qualification. Intent changes leave scientific evidence
and its fingerprint unchanged.

Expected engineering behavior before tests: reject duplicate IDs, nonfinite
cells, changed axes, unknown fields (including Y), and group length mismatch;
never silently delete a row or band; no self/shared-group neighbors; preserve
undefined provider states; reject forged evidence during pure interpretation;
keep metrics byte-identical across intent changes. Analytical mock fixtures
test orchestration only. Actual WASM execution against the pinned published
Methods package is separately required before calling the live chain tested.
Tolerance: identities, counts, statuses, fingerprints and fixed settings are
exact; fixture floating values use an absolute 1e-12 bound. No real fit is part
of this engineering qualification.

Native orchestration check: `cargo test --locked -p nirs4all-domains --no-default-features --test browser`.
Run `cargo fmt --all --check`, the existing workspace gates and clippy with
warnings denied on a build-authorized runner. After `npm run build:native` and
package dependency installation, `npm test` in this directory requires actual
WASM files and fails if they are missing. It checks the analytical three-point
variance (1, then 4 after doubling X), real full-reference neighbors, two
synthetic compact separated populations under the frozen HDBSCAN setting,
malformed callback/error mapping, intent invariance and leakage-field rejection.
Expected two-population behavior is two selected clusters; exact labels are not
compared across providers. These are engineering fixtures, with no real-source
qualification or fit.
