# Domains browser binding

## F4.2 train-fitted support

`analyzeSupport` accepts the additive `SupportRequest` and returns separate
projection and monitoring evidence. The public schemas are
`support-input.schema.json` (register the existing scoped schema too),
`support-result.schema.json`, and the distinct documentary-only
`support-local-refusal.schema.json`. Runtime admission failures throw; the UI
records them without inventing a successful provider receipt or evidence hash.

After building the binding, this example runs from the repository root:

```js
import {readFile} from 'node:fs/promises';
import {createDomainsRuntime} from './bindings/wasm/index.js';
const wasmModule = await readFile('bindings/wasm/native/nirs4all_domains_bg.wasm');
const fixtures = JSON.parse(await readFile('bindings/wasm/tests/support-fixtures.json'));
const request = fixtures.find(f => f.id === 'baseline-two-feature').request;
const runtime = await createDomainsRuntime({wasmModule});
const result = runtime.analyzeSupport(request); // actual public synthetic data
console.log(result.projection.status, result.monitoring.status, result.limit_qualification);
```

Only train enters `FlexiblePCA.fit`; train/test transforms use its unchanged live
N4ME state. State bytes remain internal and are never exported. Monitoring uses
the separate Methods indexed-fold protocol; it is not F4.1's original PCA or the
same serialized model. An optional externally sourced `SupportLimitPlan` is
available through the API; the browser defaults to descriptive/unknown-unit
interpretation. No data or model is sent to a server. Predict queries, Y access,
grouped replacement folds and inferred independence are not admitted.
See [the scientific contract](../../docs/browser/F4_2_SCIENTIFIC_PROTOCOL.md).

## Existing binding and numerical ownership

This private, additive demo binding builds the existing Domains library as a
WASM cdylib. It adds no third Rust crate and consumes the public Preflight0.3.0
provider contract with the published Methods1.5.1 / ABI2.24 WASM kernels.
This integration has separate [qualification limits](../../docs/RELEASE_METHODS_1_5.md);
old evidence does not certify the current build.
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

F4.1 adds `runtime.analyzeFactor(request)` / `analyzeFactorJson(json)` with the
versioned `domains.browser_factor_association.v1` contract in `index.d.ts`.
Pass a compact original X-only PCA report and its matching successful scoped
fit receipt, exact population keys and explicitly selected keyed M columns.
Do not pass X or Y values. Rust validates the original evidence/fit fingerprints
and scope before the Methods callback. Train is the main population; an
unpartitioned source is descriptive, and global train+test needs separate
explicit consent and an already transductive source PCA. No PCA is fit here.

Each resolved PC is reported separately: categorical eta²/F or explicitly
selected Pearson/Spearman. Missing M uses complete pairs without modifying the
source PCA. Descriptive B=0 is the default; p-values remain unavailable without
the separate externally qualified exchangeability/family record. The bounded
exact path does not authenticate that record or establish physical independence.
See [the scientific contract](../../docs/browser/F4_1_SCIENTIFIC_PROTOCOL.md)
and [qualification](../../docs/browser/F4_1_VALIDATION.md). Existing `browser_x.v1`
metadata metrics remain unchanged; the association is a separate result.

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
