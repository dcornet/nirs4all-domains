# F4.2 validation record

**Local evidence recorded 2026-11-18, followed by hosted qualification on the F4.2 executable delivery SHA.** Protocol: `domains.browser_train_fitted_support.v1`, frozen before scientific tests in [F4_2_SCIENTIFIC_PROTOCOL.md](F4_2_SCIENTIFIC_PROTOCOL.md). Branch `feat/domains-train-fitted-support-f4-2`, based on `b2d35182a174381a8b6ffac876316c83d78d21ba`. The local table below retains its original provenance; the separate hosted closure documents the successfully executed Windows/Ubuntu tests on `4b9ee761e32e798fd8b4466b420a4ce479e561ab`. A later documentation-only synchronization commit does not turn earlier checks into checks on its own SHA; use GitHub Actions for any subsequent exact-head qualification.

## What is implemented and checked locally

The operation fits public Methods `FlexiblePCA` on the complete declared train X, then transforms train and test through that fitted owner state. `Methods.statsPcaMonitor` is a separate call and result. Existing F4.0 raw-space train-reference/test-query neighbors and F4.1 score provenance remain independent. No Y enters the operation, no predict row is requested, and the browser does not use the F4.1 PCA basis. No numerical kernel was copied into Domains.

| Local check | Recorded result | Evidence boundary |
|---|---|---|
| Workspace compile | `cargo check --workspace --all-targets --locked` passed | Local run; exact candidate SHA binding remains for delivery. |
| Clippy | `cargo clippy --locked --offline --profile qualification --workspace --all-targets -- -D warnings` passed after the final native lifetime fix | Local staged-source check; hosted exact-SHA checks remain separate. |
| Native provider transport | Seven spy/provider tests passed, checking train fit, train/test transform and monitor populations and refusals | `crates/nirs4all-domains/tests/browser_support.rs`; includes no-call refusal checks. |
| Native actual-Methods regression | Ignored native regression passed: an unrelated summary error and invalid-width transform do not destroy the live FlexiblePCA handle before explicit destroy | `crates/nirs4all-domains/tests/browser_support_native.rs`. The fix is lifecycle/RAII handling; no numerical kernel changed. Failed logs/source are retained. |
| Compiled native/WASM parity | 27 computational cases plus 7 pre-provider adversaries; 13,994 numeric comparisons at absolute and relative `1e-10` | See [F4.2 native/WASM parity record](F4_2_NATIVE_WASM_PARITY.md). Exact ordered inputs/roles/call scopes are compared. Serialized fit-state/evidence hashes are not required to match cross-platform. |
| Published Methods adapter | Six direct actual-Methods adapter tests passed | `bindings/wasm/tests/support-provider.test.mjs`; not a replacement for compiled parity. |
| Schemas | Nine targeted JSON Schema tests passed | `bindings/wasm/tests/support-schema.test.mjs`; includes runtime and separate documentary local-refusal shapes. |
| Demo tests | Full frontend suite passed: 23 files / 172 tests; typecheck passed | Local run; complete hosted reruns are required. |
| Chromium browser | Eight focused F4.2 support checks passed on actual built UI, compiled WASM and Methods; two axe target contexts reported zero violations | Ignored local `support-browser-second` receipts. No Firefox, cross-platform or hosted CI claim. |
| Browser preservation/export | F4.0 and F4.1 evidence remained exact; French/English, HTML/Markdown/JSON exports omitted Y and predict sentinels; zero external requests, non-GET traffic or browser errors observed | Focused local Chromium run. The separate Methods export permission was unchanged. |
| PDF inspection | Structural review passed: A4, 514 pages / 1,885,274 bytes; Letter, 551 pages / 1,920,674 bytes | Root visually inspected A4 page 106: graph, labels and limits legible and within page. This is a partial visual sample, not full-document certification; no accessibility certification claimed. |
| WASM distribution build | Remapped WASM and frontend distribution builds passed with no absolute owner paths | Distribution check: 16,074,962 bytes, 79 files, four WASM assets. Binding suite: 34 passed, one existing parity test intentionally skipped locally; compiled parity is checked separately. |

## Deterministic scientific fixture map

`bindings/wasm/tests/support-fixtures.json` is the deterministic synthetic input source. The protocol harness replays these exact requests through actual compiled WASM and native Methods, records ordered keys and access receipts, and compares numeric result fields at the frozen `1e-10` tolerance. The fixture set exercises 27 computational inputs and 7 pre-provider access refusals. Representative IDs below map the user-facing cases to fixture source; adversarial combinations are encoded in the fixture requests and native spies.

| User case | Deterministic source IDs / evidence |
|---|---|
| Train-only fit, query transform, translations and orthogonal residual | `baseline-two-feature`, `joint-translation`, `line-orthogonal-query`, `line-positive-negative-query` |
| Magnitude/scale behavior, duplicates and rank deficiency | `variance-scale-high`, `variance-scale-low`, `exact-spectrum-duplicate`, `near-spectrum-duplicate`, `rank-one-two-feature`, `isotropic-equal-eigenvalues` |
| Zero-component and small/constant domains | `degenerate-all-constant`, `constant-single-band`, `small-train-one-row`, `single-query-row` |
| Declared repeated/shared identities and unknown identity | `repeated-physical-unit-across-folds`, `physical-unit-shared-with-query`, `unique-unknown-identity`, `nested-context-dependencies` |
| External conditional plan and row-order behavior | `synthetic-external-plan`, `permuted-train-rows`, `large-reference-query-within-budget` |
| Invalid values, axes, grants and no fit on non-train | `invalid-projection-components-zero`, `invalid-monitor-fold-count`, `invalid-monitor-alpha-one`, `projection-fit-on-test-forbidden`, `incompatible-axis-nonmonotone`, `incomplete-spectrum-needs-imputation`, `Y-grant-refused`, `manifest-fit-reference-order-mismatch`, `nonfinite-raw-json` |
| Operation-specific budget and numeric domain | `raw-neighbor-budget-does-not-veto-projection`, `extreme-numeric-scale`, `extreme-numeric-range-refusal`, `admission-manifest-budget-refusal` |
| Actual UI projection, monitor, preservation and exports | `demo/scripts/support-browser.mjs`: focused Chromium qualification; eight checks recorded locally. See browser helper receipt for per-check evidence. |

In addition to the fixtures, native spy tests check exact fit/transform/monitor keys, train-only selection, label/predict exclusion, local monitoring refusal, state mutation, and conditional dependence qualification. Browser checks cover 1D projection, default unknown/not-qualified empirical limits, F4.0/F4.1 preservation, locale changes without execution, HTML/Markdown/JSON exports, stale cancellation and dataset reset. This is a local focused run, not a full 35-case cross-browser certification.

The constant-reference fixture preserves owner Q values when `effective_components=0`, records undefined T² entries and remains `not_qualified` with `MONITORING_REFERENCE_HAS_NO_RESOLVED_COMPONENT`. Extreme scale may leave FlexiblePCA projection available while monitor reports `NUMERICAL_DOMAIN_EXCEEDED`; summary can independently be unavailable. No result converts these states into an invented value.

## Existing records and preservation

The four historical `bindings/wasm/tests/parity-fixtures.json` cases and comparator remain unchanged. F4.0 neighbor guards remain as recorded in [F4_0_VALIDATION.md](F4_0_VALIDATION.md); F4.1 score source and provenance remain as recorded in [F4_1_VALIDATION.md](F4_1_VALIDATION.md). Neither historical qualification is overwritten by F4.2.

Useful reproducible entry points include:

```text
cargo check --workspace --all-targets --locked
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo test --workspace --locked
cargo test --workspace --locked -- --ignored
node bindings/wasm/tests/support-provider.test.mjs
node --test bindings/wasm/tests/support-schema.test.mjs
node bindings/wasm/tests/support-protocol.mjs wasm demo/test-results/support-wasm.json
python scripts/check_support_parity.py --native demo/test-results/support-native.json --wasm demo/test-results/support-wasm.json --out demo/test-results/support-parity-receipt.json
cd demo && npm run typecheck
cd demo && npm test
cd demo && npm run test:browser
```

The native replay in `.github/workflows/demo-ci.yml` produces the matching input-bound native JSON before running the parity comparator. Do not rerun scientific fits on real data to generate qualification artifacts. The exact staged commands/artifacts from hosted workflows must be read back before release claims.

## Hosted closure — completed on F4.2 executable SHA

The delivered executable HEAD `4b9ee761e32e798fd8b4466b420a4ce479e561ab` was qualified through three GitHub Actions workflows, each with successful Windows and Ubuntu jobs:

- [scientific-gates #44276323605](https://github.com/dcornet/nirs4all-domains/actions/runs/44276323605): native workspace, ignored scientific tests, formatting, linting, bridge and schema checks;
- [warning-report-contracts #44276323608](https://github.com/dcornet/nirs4all-domains/actions/runs/44276323608): report and compatibility contracts;
- [Domains browser qualification #44276323611](https://github.com/dcornet/nirs4all-domains/actions/runs/44276323611): actual native/WASM, Chromium/Firefox, Windows/Ubuntu, exports, print and accessibility checks.

The PR receipt reports **27 computational cases**, **7 pre-provider refusals** and **13,994 native/WASM numeric comparisons** with unchanged absolute/relative tolerance `1e-10`, exact scopes and ordered identities. Browser qualification reports **97 checks per platform**, without observed off-origin traffic, blocking browser errors or data upload; four F4.2 automated axe contexts per platform have no detected violations. These are automated checks, **not** a WCAG or screen-reader certification.

All 16 earlier report-selection PDF cases and two F4.1 PDF cases remain covered. F4.2 full-annex prints passed all-page structural/text-bounds checks: **Ubuntu 527 A4 / 562 Letter pages; Windows 514 A4 / 551 Letter pages**. Representative pages were visually sampled, not every page. No page cap or missing scientific annex was introduced.

Verified [Ubuntu proof artifact](https://github.com/dcornet/nirs4all-domains/actions/runs/44276323611/artifacts/14415840590), [Windows proof artifact](https://github.com/dcornet/nirs4all-domains/actions/runs/44276323611/artifacts/14416870021), [Ubuntu preview](https://github.com/dcornet/nirs4all-domains/actions/runs/44276323611/artifacts/14415785771) and [Windows preview](https://github.com/dcornet/nirs4all-domains/actions/runs/44276323611/artifacts/14415053915) are attached to [PR #14](https://github.com/dcornet/nirs4all-domains/pull/14). Its receipt records the tested virtual-merge tree as identical to the executable head tree.

The initial hosted Ubuntu failure in run `44275017115` exceeded the existing screenshot-size limit after overly broad captures; targeted figure/form captures fixed the harness without relaxing that cap or scientific assertions. This failure remains attributed to the original run.

The final F4.2 resource report records **22,037,721,556 measured aggregate bytes**, **3,374,394,579 / 4,000,000,000 cumulative engineering bytes**, **625,605,421 remaining engineering bytes**, unchanged `18,663,326,977`-byte baseline and unchanged `2,015,788,498 / 2,023,410,176` scientific reservations. Historical journal and 1,031 frozen files plus five references were verified in the PR evidence. These are reported local private-resource observations, not independently remeasured by GitHub.

**Provenance boundary:** the figures above qualify executable commit `4b9ee761…`. A subsequent documentation-only commit documenting this closure requires its own workflow status check before one can claim exact-head CI success. Public Pages remains on the then-current `main` until merge and deployment.

Scientific interpretation remains descriptive. FlexiblePCA's public fitted state exposes no eigenvalues or numerical rank resolution. Monitor limits remain unknown/not qualified without supported external evidence of independent units. Projection does not reuse F4.1 PCA, predict query data, establish physical/reference independence, support predictive utility, or establish real-study performance. The advanced external plan is API-only; the GUI remains descriptive.
