# Worker loading failure: root-cause report

## Finding

The original user incident is **not yet reproduced**. The report named
`WORKER_LOADING_FAILED` and `LOCAL_ANALYSIS_REFUSED` for a small X/Y import, but
there is no captured browser trace or retained copy of that user's dataset.
Those codes do not establish that the dataset caused the failure.

A separate, controlled failure was reproduced against the public main build at
`ada9ca3e44abf58011db5be04aadd580ada69e7f`. Agent A intercepted the worker
entry request and returned HTTP 404 with `application/javascript` while
importing a minimal synthetic X-only CSV. The browser received no useful
`worker.onerror.message` or filename, displayed `WORKER_LOADING_FAILED`, and
created no analysis result. The ignored audit receipt records the intercepted
URL, status, content type, visible code, and empty error event fields.

This establishes a defect in the old error path: an inaccessible worker module
was reduced to a generic code even when the HTTP failure was known to the
browser's network layer. It does **not** establish that the user's original
incident was caused by a worker 404. In the controlled 404 case the worker code
did not start, so IO parsing, Domains WASM, Methods WASM, ABI checks, and the
scientific analysis were not reached.

## Baseline evidence

The same public main build also completed ordinary synthetic browser flows:

| Fixture | Imported shape | Observed outcome |
| --- | --- | --- |
| X only | 3 observations × 1 variable | Import and report completed. |
| X plus one numeric Y | 8 observations × 2 variables | Import and train-only report completed. |

The recorded assets for these flows returned HTTP 200, and worker replies had
no errors. These small fixtures show that the public import and analysis paths
can work; they do not reproduce the user's data or rule out an intermittent,
cache-dependent, or environment-specific failure.

All four required main CI workflows were green for that baseline commit. Those
results predate the hotfix and do not qualify this branch.

Potential stale/missing deployment assets or browser cache skew remain
hypotheses only. The controlled 404 supports the claim that such a failure was
masked by the old client. It does not show that stale assets were present in
the user's session. No evidence currently implicates dataset size, missing
values, Y cardinality, or any numerical kernel.

## Corrective change in this branch

The hotfix makes worker startup observable and carries structured loader
diagnostics while leaving scientific methods and their results unchanged:

- The main-thread client waits for a versioned worker `READY` handshake before
  posting the request or transferring import buffers.
- The worker entry has no static runtime imports. It installs error handlers,
  sends bootstrap events, then dynamically imports the operation module inside
  a catchable request path.
- IO, Formats, Domains, and Methods initialization report the phases they
  actually reach. Domains' runtime API brackets its Rust initialization,
  Methods initialization, and ABI check with an optional lifecycle callback.
- The client probes only a same-origin worker asset under the app's Vite asset
  prefix when the browser error event lacks a message. It distinguishes a
  non-2xx response, HTML response, and invalid JavaScript content type when
  observed. Failed or inconclusive probes remain an unknown startup cause.
- Diagnostics retain a strict `rt_error.v1` envelope. Technical phase,
  component, asset metadata, version, and recovery details live in the separate
  versioned `domains.worker_diagnostic.v1` object.
- A confirmed missing or invalid deployment asset offers an explicit reload.
  Other failures require an explicit retry or inspection; no automatic second
  scientific execution is started.

Files changed for this focused hotfix include the worker client, entry and
operation modules; import/runtime lifecycle reporting; the Domains WASM
binding's optional lifecycle callback; diagnostic view/model and localization;
worker-loading browser harness; and the three hotfix documents. No upstream
repository, Methods kernel, Preflight protocol, or scientific result definition
is changed.

## Validation state

The hotfix now has frontend test and production-preview browser evidence, but
CI, publication, and the original incident diagnosis remain open:

- The frontend suite passed 189 tests across 26 files after the strict-type
  fix.
- A production-preview Chrome receipt records 13 synthetic cases: three
  computed flows (X-only, X/Y train-only, and a fresh worker after explicit
  reload) and ten refused fault injections. Failure cases produced no report.
- The receipt verifies worker-entry 404 and HTML handling, dynamic operation
  import 404/HTML failures, IO WASM 404/wrong MIME/corrupt bytes/missing
  exports, a Domains WASM 404, and an incompatible Methods ABI. It records
  actual status/MIME evidence but contains no asset digest or integrity result.
- The public-main X-only and X/Y baseline flows and the controlled pre-fix 404
  reproduction are captured in local ignored audit receipts.
- The Domains WASM binary was reused from public CI artifact `14421536534`
  (workflow run `44288135712`); its ZIP digest was verified. No native kernel
  was rebuilt for this hotfix.
- Hotfix CI, Pages publication, Firefox preview, broader recovery/cache tests,
  and a reproduction of the original user's incident remain pending.

See [the bootstrap contract](WORKER_WASM_BOOTSTRAP_CONTRACT.md) and
[validation plan](WORKER_LOADING_VALIDATION.md) for the required remaining
checks. A green historical main workflow is not evidence that this unmerged
branch or the original user's session is fixed.
