# Worker loading validation plan and current evidence

Assessment recorded 2026-11-18. The expanded production-preview Chromium
receipt, frontend suite, and asset comparison are recorded below.
[PR #15](https://github.com/dcornet/nirs4all-domains/pull/15) is a draft with
CI running; no hotfix CI success or Pages publication is claimed.

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
diagnostic receipts. The earlier 13-case receipt is superseded by the expanded
18-case receipt below, which embeds a browser version and dirty build-info
identity; it does not identify the clean PR #15 source SHA.

## Completed observations

| Check | Evidence | Status |
| --- | --- | --- |
| Public main X-only baseline | Synthetic X, 3 observations × 1 variable; report present; recorded assets returned 200 and worker replies had no errors. | Passed on baseline commit `ada9ca3e44abf58011db5be04aadd580ada69e7f`; this predates the hotfix. |
| Public main X/Y baseline | Synthetic X plus one numeric Y, 8 observations × 2 variables; report present; recorded assets returned 200 and worker replies had no errors. | Passed on baseline commit; this predates the hotfix. |
| Public main worker 404 | Worker script intercepted as 404 `application/javascript`; browser error event contained no message or useful filename; no analysis result; visible `WORKER_LOADING_FAILED` without a technical diagnostic. | Reproduced before the fix. This establishes the old generic error path, not the original user's root cause. |
| Frontend suite and typecheck | 196 tests across 27 files passed; TypeScript typecheck passed. | Passed for the current hotfix worktree; this is not hosted CI evidence. |
| Expanded production-preview Chromium cases | `demo/test-results/worker-priority-01/worker-loading/loading-chromium.json`: 18 synthetic cases; three computed flows and 15 injected failures refused without a report. Chromium `157.0.8103.79`; build info reports demo `0.1.0-alpha.17`, commit `ada9ca3e44abf58011db5be04aadd580ada69e7f`, `dirty: true`; 13 production asset SHA-256 digests recorded. | Passed for this receipt. Its embedded build identity is dirty and does not attest the clean PR #15 SHA. It is not deployed Pages evidence. |
| Public-main Pages artifact comparison | `.audit/worker-loading/public-main-artifact-check.json`: 14 asset requests returned 200 and all 14 SHA-256 values matched the exact public-main Actions artifact; workflow run `44288135629`, artifact `14419499742`, ZIP SHA-256 `0d0c6ef5a5cb2b8abbe266d748087d9d2a92e31ef2b66f72b5749406a02082c3`. | Passed for public main at `ada9ca3e44abf58011db5be04aadd580ada69e7f`. This proves those published assets match that artifact, not that hotfix PR assets are deployed. |
| Broader browser checks | Owner reports successful normal/scoped/factor/support/report-export flows, FR/EN, accessibility/mobile checks, and the older F3 fault-recovery case. A separate helper MIME assertion initially used the wrong expected argument; the test assertion was corrected without changing runtime code, and the expanded 18-case helper then passed. | Recorded as completed browser work for the worktree; do not conflate with the 18-case case list or hosted CI. |
| Domains WASM binding artifact | Public main workflow run `44288135712`, artifact `14421536534`, ZIP digest `sha256:682450a66c5c5f536fcba5ac56947fd281f19ad9f490079b14d084bddcd8bf53`. | Digest verified; artifact reused. No native kernel was rebuilt for this hotfix. This does not qualify the changed worker. |

The public baseline and controlled-fault receipts are local ignored audit
artifacts. Their observations are summarized above; they are not shipped as
runtime assets or scientific data.

## Requested 35-case adversarial inventory

`Unit suite` means the frontend suite above; it does not imply every row has an
isolated test. `Public baseline` means the public pre-fix fixture. `Pre-fix
fault` is the controlled old-worker 404 reproduction. `Chromium preview`
refers to the expanded 18-case receipt. `Pending` means no case-specific
execution evidence is available.

| # | Scenario | Evidence and disposition |
| ---: | --- | --- |
| 1 | Worker starts normally | Chrome preview: X-only, X/Y, and fresh worker after explicit reload all computed. |
| 2 | Worker inaccessible | Chrome preview worker-entry 404 refused with `WORKER_ASSET_UNAVAILABLE`; no report. Public pre-fix 404 also reproduced. |
| 3 | `worker.onerror` with a message | Unit suite covers mapping; the preview receipt does not isolate this event shape. |
| 4 | `worker.onerror` without a message | Public pre-fix reproduction and Chrome preview worker 404/HTML refusals; no dedicated post-fix event-shape injection in the receipt. |
| 5 | Static import evaluation failure | A top-level worker-entry throw was injected and refused; a separate static runtime-dependency failure is inapplicable because the entry has no runtime imports. |
| 6 | Dynamic import failure | Chrome preview operation-chunk 404 and HTML responses refused at `OPERATION_MODULE_LOADING`. |
| 7 | JavaScript chunk absent | Chrome preview worker-entry and operation-chunk 404 cases refused; no report. |
| 8 | HTML returned for JavaScript | Chrome preview worker-entry HTML response refused as `JAVASCRIPT_ASSET_INVALID_RESPONSE`; operation-chunk HTML also refused. |
| 9 | WASM 404 | Chromium preview IO and Formats 404 (`WASM_ASSET_UNAVAILABLE`) plus Domains 404 (`DOMAINS_INITIALIZATION_FAILED`). Methods 404 not tested. |
| 10 | WASM wrong MIME | Chromium preview IO `text/html` and non-HTML invalid MIME responses were refused with distinct content-type diagnostics. |
| 11 | Corrupt WASM binary | Chrome preview corrupt IO bytes refused at compile as `WASM_COMPILE_FAILED`. |
| 12 | WASM lacks required exports | Chrome preview incompatible IO exports refused as `WASM_EXPORT_MISSING`. |
| 13 | IO initialization fails | Chrome preview exercised distinct IO missing, invalid response, compile, and export failures. |
| 14 | Formats fails after IO succeeds | Chromium preview Formats 404 was refused at `FORMATS_RUNTIME_LOADING`; other Formats failure classes remain pending. |
| 15 | Domains initialization fails | Chrome preview Domains WASM 404 refused at `DOMAINS_RUNTIME_LOADING`; no report. |
| 16 | Methods initialization fails | Chromium preview injected a Methods initialization failure at `METHODS_RUNTIME_LOADING`; it did not test an actual valid-module ABI-version mismatch. Methods loader subphases are not observable. |
| 17 | Valid module has incompatible ABI version | Not tested. The injected Methods initialization failure is not proof that a valid ABI 2.x module with a version mismatch is rejected. |
| 18 | Invalid request after successful initialization | Worker rejection behavior is not yet separately browser-injected; pending. |
| 19 | Uncaught exception during startup | Chromium preview top-level worker-entry throw refused with `WORKER_STARTUP_EXCEPTION`. |
| 20 | Unhandled promise rejection | Chromium preview rejection after READY refused with `WORKER_UNHANDLED_REJECTION`. |
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

## Expanded production-preview Chromium receipt

The receipt `demo/test-results/worker-priority-01/worker-loading/loading-chromium.json`
records a production-preview Chromium run of 18 synthetic cases. Its scope says
synthetic only, no raw values recorded, no Y used for train structure, and no
fabricated provider output. The three computed cases are X-only import/analysis,
X/Y import with train-only analysis, and a fresh worker after explicit reload.
All 15 injected-failure cases are refused with no report. The receipt records
Chromium `157.0.8103.79`, build info and SHA-256 digests for 13 production
assets. The build info identifies a dirty `ada9ca3` worktree, so it is not an
exact clean-PR build attestation. The recorded fault groups include:

| Case | Fault or input | Required observation |
| --- | --- | --- |
| Normal X-only | 3 × 1 synthetic numeric X | Import and report computed; `y_accessed=false`. |
| Normal X/Y | 8 × 2 synthetic X plus one numeric Y | Import and train-only report computed; target inventory preserved; `y_accessed=false`. |
| Fresh worker after explicit reload | Healthy X/Y fixture | New worker computed a report after reload. |
| Worker entry failure | 404 JavaScript, 200 `text/html`, top-level throw | `WORKER_ASSET_UNAVAILABLE`, `JAVASCRIPT_ASSET_INVALID_RESPONSE`, or `WORKER_STARTUP_EXCEPTION`; no report. |
| Unhandled rejection after READY | Injected rejection at `OPERATION_MODULE_READY` | `WORKER_UNHANDLED_REJECTION`; no report. |
| Operation chunk 404 / HTML | Failed dynamic operation import | `WORKER_DEPENDENCY_IMPORT_FAILED` at `OPERATION_MODULE_LOADING`; no report. |
| IO WASM faults | 404, wrong MIME (`text/html` and non-HTML), invalid binary, missing exports, expected-digest mismatch | Distinct unavailable/invalid-response/content-type/compile/export/integrity refusal codes; no report. |
| Formats WASM 404 | 404 while loading Formats | `WASM_ASSET_UNAVAILABLE` at `FORMATS_RUNTIME_LOADING`; no report. |
| Domains WASM 404 | 404 during Domains initialization | `DOMAINS_INITIALIZATION_FAILED` at `DOMAINS_RUNTIME_LOADING`; no report. |
| Methods initialization failure | Injected invalid/incompatible Methods module | `METHODS_INITIALIZATION_FAILED` at `METHODS_RUNTIME_LOADING`; no report. This does not demonstrate a valid Methods ABI 2.x module rejected for a minor-version mismatch. |

The 18-case receipt records per-build asset digests and exercises the IO digest
mismatch refusal. A separate public-main comparison confirms that 14 deployed
assets matched the exact public-main Actions artifact. This is not a hotfix
Pages publication check. The Methods public loader does not expose its internal
fetch/compile/instantiate steps; the injected Methods failure establishes
refusal at its initialization phase only. Formats has a 404 case, but other
Formats fault classes, cancellation/stale reply in this helper, first-open
after hotfix publication, and broader cache-skew behavior remain pending.

The Methods package's public `loadModule()` has no `wasmBinary` or
`locateFile` options. Tests must exercise the Vite-generated hashed asset path
and report the phase visible through the public loader; they must not monkey
patch `fetch`, replace the Emscripten loader, or claim an internal fetch vs
instantiate distinction that Methods does not expose.

## Release gates still required

The following hotfix checks remain pending:

- PR #15 is draft at `9b73c942` and CI is running. Windows/Ubuntu hotfix CI
  success and uploaded artifacts are pending.
- A clean production build with an embedded identity matching PR #15. The
  current expanded preview receipt identifies a dirty `ada9ca3` worktree.
- Published Pages deployment and a post-publication first-open/old-tab check.
- Explicit cancellation, stale reply, generic retry, and recovery checks in the
  browser beyond the recorded fresh-worker-after-reload case.
- Formats fault classes beyond 404, Methods fault classes/valid-module ABI
  mismatch, and cache-skew cases.
- A clean-PR asset digest comparison against its exact hosted artifact and
  eventual Pages publication. The current preview has 13 asset digests and a
  digest-mismatch refusal; the separate exact 14-asset match is for public main.
- Firefox production-preview receipt; the expanded hotfix receipt is Chromium.
- Final dependency/version/asset inventory, privacy review, and PR commit/SHA.

The recorded preview validates the healthy synthetic flows and listed
injected failures, but it does not complete the release gates above. Keep the
original user's specific root cause labeled unconfirmed unless that incident
is reproduced with evidence.
