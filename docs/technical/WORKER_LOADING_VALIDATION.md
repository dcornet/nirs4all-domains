# Worker loading validation plan and current evidence

Assessment recorded 2026-11-18. The production-preview Chrome receipt and
frontend test run are now recorded below. Hotfix CI and publication remain
pending.

## Evidence rules

This plan separates source review, executed behavior, and pending qualification.
The original user dataset is unavailable for this work and has not been
recreated. Synthetic fixtures below verify browser plumbing only; they do not
stand in for the user's data or qualify a scientific result. A test definition,
CI configuration, or artifact hash alone is not an executed browser result.

Post-fix browser cases use the production build and preview under the GitHub
Pages base path `/nirs4all-domains/`. Evidence should record the exact
commit/build, browser version, intercepted asset path, response status and MIME
type, worker messages, final diagnostic, whether a result exists, and recovery
outcome. Keep source values and original exception text out of public
diagnostic receipts. The current 13-case receipt records outcomes, phases,
diagnostics and intercepted status/MIME but does not embed the commit or exact
browser version.

## Completed observations

| Check | Evidence | Status |
| --- | --- | --- |
| Public main X-only baseline | Synthetic X, 3 observations × 1 variable; report present; recorded assets returned 200 and worker replies had no errors. | Passed on baseline commit `ada9ca3e44abf58011db5be04aadd580ada69e7f`; this predates the hotfix. |
| Public main X/Y baseline | Synthetic X plus one numeric Y, 8 observations × 2 variables; report present; recorded assets returned 200 and worker replies had no errors. | Passed on baseline commit; this predates the hotfix. |
| Public main worker 404 | Worker script intercepted as 404 `application/javascript`; browser error event contained no message or useful filename; no analysis result; visible `WORKER_LOADING_FAILED` without a technical diagnostic. | Reproduced before the fix. This establishes the old generic error path, not the original user's root cause. |
| Worker startup unit guards | Bootstrap guard tests passed as part of the frontend suite. | Included in the reported frontend run; do not treat the earlier 16-test subset as a separate final run. |
| Frontend suite | 189 tests across 26 files passed after the strict-type fix. | Passed for this hotfix checkout. This is frontend test evidence, not CI or publication evidence. |
| Production-preview Chrome cases | `demo/test-results/browser/worker-loading/loading.json`: 13 synthetic cases; two ordinary import/analysis flows and an explicit reload flow computed, ten injected failures refused without a report. | Passed for the recorded preview run. The receipt records outcomes and intercepted HTTP status/MIME; it does not record asset digests or integrity validation. |
| Domains WASM binding artifact | Public main workflow run `44288135712`, artifact `14421536534`, ZIP digest `sha256:682450a66c5c5f536fcba5ac56947fd281f19ad9f490079b14d084bddcd8bf53`. | Digest verified; artifact reused. No native kernel was rebuilt for this hotfix. This does not qualify the changed worker. |

The public baseline and controlled-fault receipts are local ignored audit
artifacts. Their observations are summarized above; they are not shipped as
runtime assets or scientific data.

## Requested 35-case adversarial inventory

`Unit suite` means the frontend suite above; it does not imply every row has an
isolated test. `Public baseline` means the public pre-fix fixture. `Pre-fix
fault` is the controlled old-worker 404 reproduction. `Chrome preview` refers
to a case in the 13-case receipt. `Pending` means no case-specific execution
evidence is available.

| # | Scenario | Evidence and disposition |
| ---: | --- | --- |
| 1 | Worker starts normally | Chrome preview: X-only, X/Y, and fresh worker after explicit reload all computed. |
| 2 | Worker inaccessible | Chrome preview worker-entry 404 refused with `WORKER_ASSET_UNAVAILABLE`; no report. Public pre-fix 404 also reproduced. |
| 3 | `worker.onerror` with a message | Unit suite covers mapping; the preview receipt does not isolate this event shape. |
| 4 | `worker.onerror` without a message | Public pre-fix reproduction and Chrome preview worker 404/HTML refusals; no dedicated post-fix event-shape injection in the receipt. |
| 5 | Static import evaluation failure | Entry now has no value imports, but the absence of a fault-injection test leaves this pending. |
| 6 | Dynamic import failure | Chrome preview operation-chunk 404 and HTML responses refused at `OPERATION_MODULE_LOADING`. |
| 7 | JavaScript chunk absent | Chrome preview worker-entry and operation-chunk 404 cases refused; no report. |
| 8 | HTML returned for JavaScript | Chrome preview worker-entry HTML response refused as `JAVASCRIPT_ASSET_INVALID_RESPONSE`; operation-chunk HTML also refused. |
| 9 | WASM 404 | Chrome preview IO 404 (`WASM_ASSET_UNAVAILABLE`) and Domains 404 (`DOMAINS_INITIALIZATION_FAILED`). Methods 404 not tested. |
| 10 | WASM wrong MIME | Chrome preview IO 200 `text/html` response refused as `WASM_ASSET_INVALID_RESPONSE`. |
| 11 | Corrupt WASM binary | Chrome preview corrupt IO bytes refused at compile as `WASM_COMPILE_FAILED`. |
| 12 | WASM lacks required exports | Chrome preview incompatible IO exports refused as `WASM_EXPORT_MISSING`. |
| 13 | IO initialization fails | Chrome preview exercised distinct IO missing, invalid response, compile, and export failures. |
| 14 | Formats fails after IO succeeds | No executed post-fix case; Formats integration and failure coverage pending. |
| 15 | Domains initialization fails | Chrome preview Domains WASM 404 refused at `DOMAINS_RUNTIME_LOADING`; no report. |
| 16 | Methods initialization fails | Chrome preview incompatible Methods ABI refused at `METHODS_RUNTIME_LOADING`; Methods asset-fetch subphases are not observable/tested. |
| 17 | ABI incompatible | Chrome preview Methods incompatible-ABI fixture refused with `METHODS_INITIALIZATION_FAILED`. |
| 18 | Invalid request after successful initialization | Worker rejection behavior is not yet separately browser-injected; pending. |
| 19 | Uncaught exception during startup | Worker has startup error handlers; no executed startup exception injection yet. |
| 20 | Unhandled promise rejection | Worker has a rejection handler; no executed rejection injection yet. |
| 21 | Structured-clone failure | Unit guard reported pass. |
| 22 | Cancel during bootstrap | Unit guard reported pass; no post-fix browser receipt yet. |
| 23 | Bootstrap timeout | Unit guard reported pass; no post-fix browser receipt yet. |
| 24 | Retry after recoverable error | Unit suite covers client recovery; Chrome preview confirms a fresh worker after explicit reload, not generic retry after every failure. |
| 25 | Late response from cancelled worker | Unit guard reported pass. |
| 26 | Two calls close together | Client cancellation/obsolete-reply guard reported pass; browser stress case pending. |
| 27 | Dataset changes during loading | Existing client cancellation test covers dataset replacement; startup-specific browser case pending. |
| 28 | Destroy and recreate worker | Chrome preview covers a fresh worker after explicit reload; standalone destroy/recreate under other failure states remains pending. |
| 29 | Inconsistent asset cache | No executed cache-skew reproduction; pending. |
| 30 | First open after deployment | Production-preview receipt exists; first-open after actual Pages publication remains pending. |
| 31 | Reload of an old tab | Chrome preview checks a fresh worker after explicit reload; old-tab/deployment skew remains pending. |
| 32 | Import X-only CSV | Chrome preview computed synthetic X-only import and report (3 observations × 1 variable). |
| 33 | Import X plus one Y CSV | Chrome preview computed synthetic X/Y train-only report (8 observations × 2 variables); Y was inventoried but not accessed by the operation. |
| 34 | Import partitioned X/Y/M | Import-draft unit fixture reported pass; final-build browser case pending. |
| 35 | X-only analysis after importing valid Y | Chrome preview X/Y case completed with `y_accessed=false`; report was produced without Y access. |

This inventory prevents the aggregate suite counts from obscuring untested
startup, network, cache, and recovery cases.

## Production-preview Chrome receipt

The ignored audit receipt `demo/test-results/browser/worker-loading/loading.json`
records a production-preview Chrome run of 13 synthetic cases. Its scope says
synthetic only, no raw values recorded, no Y used for train structure, and no
fabricated provider output. The three computed cases are X-only import/analysis,
X/Y import with train-only analysis, and a fresh worker after explicit reload.
All ten injected-failure cases are refused with no report. The recorded cases
include:

| Case | Fault or input | Required observation |
| --- | --- | --- |
| Normal X-only | 3 × 1 synthetic numeric X | Import and report computed; `y_accessed=false`. |
| Normal X/Y | 8 × 2 synthetic X plus one numeric Y | Import and train-only report computed; target inventory preserved; `y_accessed=false`. |
| Fresh worker after explicit reload | Healthy X/Y fixture | New worker computed a report after reload. |
| Worker entry 404 / HTML | 404 JavaScript / 200 `text/html` | `WORKER_ASSET_UNAVAILABLE` / `JAVASCRIPT_ASSET_INVALID_RESPONSE`; no report. |
| Operation chunk 404 / HTML | Failed dynamic operation import | `WORKER_DEPENDENCY_IMPORT_FAILED` at `OPERATION_MODULE_LOADING`; no report. |
| IO WASM 404 / wrong MIME / corrupt bytes / missing exports | 404, 200 `text/html`, invalid binary, or incompatible exports | Distinct `WASM_ASSET_UNAVAILABLE`, `WASM_ASSET_INVALID_RESPONSE`, `WASM_COMPILE_FAILED`, and `WASM_EXPORT_MISSING` refusals; no report. |
| Domains WASM 404 | 404 during Domains initialization | `DOMAINS_INITIALIZATION_FAILED` at `DOMAINS_RUNTIME_LOADING`; no report. |
| Methods incompatible ABI | Incompatible Methods ABI fixture | `METHODS_INITIALIZATION_FAILED` at `METHODS_RUNTIME_LOADING`; no report. |

The receipt records asset path/status/content type for the worker and IO asset
diagnostics and intercepted request path/status/MIME. It does not record a
content digest or an integrity-check result; no asset-integrity claim follows.
The Methods public loader does not expose its internal fetch/compile/instantiate
steps, so the Methods case establishes refusal at the Methods initialization
phase only. Formats failure, cancellation/stale reply in a real browser,
first-open after publication, and broader cache-skew behavior remain pending.

The Methods package's public `loadModule()` has no `wasmBinary` or
`locateFile` options. Tests must exercise the Vite-generated hashed asset path
and report the phase visible through the public loader; they must not monkey
patch `fetch`, replace the Emscripten loader, or claim an internal fetch vs
instantiate distinction that Methods does not expose.

## Release gates still required

The following hotfix checks remain pending:

- Hotfix CI on Windows and Ubuntu, with actual run IDs and artifacts recorded.
- Published Pages deployment and a post-publication first-open/old-tab check.
- Explicit cancellation, stale reply, generic retry, and recovery checks in the
  browser beyond the recorded fresh-worker-after-reload case.
- Formats failure coverage, Methods asset failure subphases, and cache-skew
  cases.
- Asset integrity/digest evidence; the current receipt includes status/MIME and
  selected compile/export failures but no integrity result.
- Firefox production-preview receipt; the current hotfix receipt is Chrome.
- Final dependency/version/asset inventory, privacy review, and PR commit/SHA.

The recorded preview validates the healthy synthetic flows and listed
injected failures, but it does not complete the release gates above. Keep the
original user's specific root cause labeled unconfirmed unless that incident
is reproduced with evidence.
