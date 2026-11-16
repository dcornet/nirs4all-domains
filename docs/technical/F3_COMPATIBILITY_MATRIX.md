# F3 compatibility boundary

| Boundary | Retained contract | Executable evidence |
|---|---|---|
| Rust Domains / Preflight | Existing two crates, Preflight =0.1.6, unchanged Cargo.lock/source | fmt, check/Clippy, workspace/ignored tests, doc/native build, schema no-diff |
| Public Methods provider | 1.3.13, ABI 2.20, unchanged operations and exact conventions | Native/WASM four-fixture comparison and original malformed-response/order adversaries |
| Binding / Rust WASM | Same JSON requests/results/status/reason/value; no fitted-state API | Actual compiled binding suite, budget/error tests, exact old report comparison |
| IO / Formats | Published 0.2.14 binaries/glue, identical parsers and roles/materialization | Registry archive integrity + glue/binary fingerprints; actual CSV/metadata, axis/identity/partition guards |
| Worker transport | Same operations/values/epochs/120 s deadline; imported byte buffers consumed once | Real detached sender buffers, exact original content/evidence hashes, cancellation, replacement and recovery |
| Loader lifecycle | One in-flight initialization, retry after failure, no fallback | Actual WebAssembly unit tests and published-module browser HTTP/HTML/corruption/incompatible-export failures |
| UI / TypeScript | Existing qualification chart props remain; optional new props unused | Actual 0.2.5 package source/type review, strict typecheck, same figure inputs and browser interaction |
| F1 presentation | Existing semantic model, exact source pointers/numbers/units/nulls | All original frontend/AST/escape/export tests; memoization keyed by result/locale/intent |
| F2 journey / readings | Four open steps, FR/EN, intent is a declaration, full originals retained | Existing keyboard/live/saved/partial/full/offline/print tests and five axe states |
| Source / scientific population | No row deletion/fusion/imputation/new split or fitted test | Retained test/predict rejection, original axes/IDs/groups, fixed scientific budgets |

No public scientific schema, tolerance, provider contract, algorithm, protocol
version or package version is changed. F3's new benchmark/loading receipts are
engineering artifacts, outside scientific reports. Fingerprints are not relaxed
to accommodate a dependency. A changed scientific value or hash fails comparison.

The selected UI's theme, qualification CSS and official logo bytes match the old
package. Chart changes add accessible data tables and optional independently
labeled reference lines; Domains supplies no new reference lines or export
checkboxes. Spectral/score/eigenvalue values remain owner-provided. The additional
tables do not include raw spectra in exported F1 HTML/Markdown/JSON.

The benchmark builds exact F2 frontend source separately on the same runner and
uses the same pinned browser/Node process environment for both builds. It first
asserts Rust source/Cargo.lock unchanged, then reuses that job's compiled WASM;
it does not claim two independent numerical implementations from two JS bundles.
Native public Methods remains the separate numerical comparison path. New UI,
schema and bundler packages must pass actual installation/build/browser gates;
compatible-looking semver and typechecking alone are not sufficient.
