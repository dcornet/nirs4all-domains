# Domains browser demonstration

The [F3 technical review](../docs/technical/F3_RELEASE_REPORT.md) records historical
dependency choices, verified published-WASM loading, worker ownership, bounded
performance measurements and actual CI evidence. The current release integration
selects Preflight0.3.0 and Methods1.5.1/ABI2.24, with its separate
[qualification limits](../docs/RELEASE_METHODS_1_5.md). Clean installs use the exact checked-in lockfiles;
existing local node_modules from an older cohort must be replaced with `npm ci`.

The [F2 user journey](../docs/ux/F2_USER_JOURNEY.md) explains four freely
navigable steps, metadata/import assistance, contextual FR/EN help and the
explicitly partial versus complete F1 report readings. See its
[accessibility scope](../docs/ux/F2_ACCESSIBILITY.md) and
[qualification record](../docs/ux/F2_VALIDATION.md).

This Vite/React application is an exploratory, local browser client for
`nirs4all-domains`. Its one-shot import may retain X/Y/M, original axes,
missingness and declared partitions in the main import state. Each later
scientific request selects only its permitted X/M values; no Y value is passed
to a request or report export. The app does not fit a predictive model, score a
validation split, or establish physical independence. No upload endpoint or
server-side analysis is part of the design.

## Build the existing Rust crate for WebAssembly

Use a Rust toolchain with `wasm32-unknown-unknown` and `wasm-pack` already
available. This builds the existing `nirs4all-domains` crate with its
`browser-wasm` feature; it does not add a crate or publish a scientific package.

```shell
rustup target add wasm32-unknown-unknown
cd bindings/wasm
npm run build:native
npm ci --ignore-scripts
cd ../../demo
npm ci
npm run typecheck
npm run build
npm run preview
```

`build:native` writes the generated binding and WASM under
`bindings/wasm/native/`; that generated build output is ignored. Keep the root
`Cargo.lock`. The demo's lockfile pins npm dependencies, including local
`@nirs4all/domains` from `../bindings/wasm`, `@nirs4all/io-wasm@0.2.14`,
`@nirs4all/formats-wasm@0.3.1`, `nirs4all-ui@0.2.5`, and React 19.2.3.
The local WASM package depends on `@nirs4all/methods@1.5.1`; its provider
contract comes through Preflight0.3.0 / Methods ABI2.24. `npm ci` does not
build Rust WASM: generate `native/` first. A clean checkout needs the Rust
target, wasm-pack and npm registry access before a complete browser build.

The Vite `browserWasm()` adapter is a narrow loader for the published IO 0.2.14 and
Formats 0.3.1 packages. It retains their parser and binary and replaces the
Node filesystem bootstrap with lazy browser `fetch` of the package WASM asset.
If those published glue files change, the adapter's generated-source marker
check fails; do not silently substitute a different parser or local checkout.

The configured Vite base path is `/nirs4all-domains/`. A static host must serve
the built files beneath that path and provide its normal SPA fallback. `npm
run preview` is a local preview command only. The Pages workflow publishes
`main` when GitHub Pages is configured to use GitHub Actions. The
[merged demo PR](https://github.com/dcornet/nirs4all-domains/pull/6) provides
qualification runs and downloadable static preview artifacts; public deployment
must be verified separately through the Pages workflow and hosted URL.

`src/main.tsx` supplies state, IO/worker orchestration, pure intention changes
and report exports to the presentation components. The commands above describe
the clean build sequence. F4.0 native/WASM, browser and CI qualification require
their own actual runs; historical F3.5 workflow evidence does not qualify the
current scoped import changes.

## Browser workflow and limits

The landing view accepts files by drag/drop or file picker and offers three
generated synthetic X fixtures plus a public saved tablet example. User files
are processed in the browser. The import path is capped at 32 files, 8 MiB
combined input, 2,000 observations and 1,000,000 spectral cells. Dropping or
selecting a file/folder starts inference and normal IO assembly automatically;
the initial IO preview is not a required review. The shared `DatasetBuilder`
is optional: opt in to edit after IO identifies sources but before final loading,
or open Data settings after loading. Import retains the dataset and missingness
without fitting. Implicit source fusion, aggregation,
imputation and silent row deletion are refused. Y remains in main import memory
for inventory/masking, but is not sent to a scientific request or report export.

Choose an operation separately: Train structure fits train rows only; raw
support uses train as reference and test as query; metadata audits provide
documentary counts, missingness, cardinalities, levels and literal overlap;
global descriptive structure requires explicit transductive consent and uses
train plus test while excluding predict rows. An unpartitioned source continues
through the legacy full-source descriptive route. If an auxiliary Y/M attachment
is unresolved, validated X can still load while the source stays separately
identified and dependent operations are restricted; a blocking ambiguity asks
for the specific missing choice. Metadata coloring is a
presentation-only mapping to existing PCA points. Statistical associations
and train-fitted PCA query projection remain unqualified. Groups can exclude
declared matching rows from neighbors, but do not prove that groups are
independent units.

See [F4.0 partition behavior](../docs/WASM_PARTITION_GUARD.md), [import
architecture](../docs/browser/F4_0_IMPORT_ARCHITECTURE.md), [native/WASM
compatibility](../docs/browser/F4_0_NATIVE_WASM_COMPATIBILITY.md), the
[one-shot import guide](../docs/browser/ONE_SHOT_IMPORT_USER_GUIDE.md), and
[remaining capabilities](../docs/browser/F4_0_REMAINING_CAPABILITIES.md).

### Legacy history: browser_x.v1 partition refusal

The legacy browser_x.v1 API still refuses declared test/prediction populations
before its full-source fit. The current F4.0 reviewed-import flow retains those
partitions and applies operation-specific row grants instead; see the legacy
amendment in [WASM_PARTITION_GUARD.md](../docs/WASM_PARTITION_GUARD.md).

Selecting one `.json` file opens the saved standalone Domains report path and
validates its existing schema; arbitrary JSON matrices are not a qualified X
format. The exception is an IO configuration with the exact lowercase suffix
`.nirs4all.json`, which must be selected together with its referenced source
files. A configuration alone provides no X. Malformed JSON or an incompatible
report is refused, without a numerical fit or an implicit format fallback.

`BrowserEngine` runs import and analysis in a module worker. Analysis has a
120-second wall-clock limit; cancellation terminates the worker, which also
interrupts synchronous WASM kernels. Payload limits and per-kernel work limits
are enforced by the existing Rust browser protocol. WASM and JSON copies mean
actual browser memory use can exceed the input byte count. There is no server
upload. Saved evidence remains a packaged public example; this demo does not
provide a cross-site library or upload user data for persistence.

Exports carry one semantic report model into HTML, Markdown and JSON, without
raw spectra by default. The host wires these controls to local Blob downloads;
HTML has no runtime/network dependency and retains the original evidence in an
expandable section. Print/PDF uses the browser print dialog. Verify actual
qualification through the matching PR's browser receipts.

The [F1 report guide](../docs/report/F1_REPORT_GUIDE.md) explains the shared
figure/table presentation, exact evidence navigation, bilingual explanations,
one-component PCA, saved readiness and offline/print exports. Original scientific
objects and their hashes remain present; an additive versioned presentation does
not replace them. Raw spectra remain screen-only, including in embedded SVGs.

## Scientific scope

See [WASM capabilities](../docs/WASM_CAPABILITIES.md) for the exact live versus
saved evidence boundary and [architecture](../docs/WASM_DEMO_ARCHITECTURE.md)
for the data path. Synthetic fixtures are deterministic UI/engineering
examples, not research datasets. The public tablet reading is a saved,
source-scoped evidence example and is not refit in the browser. Data rights and
attribution remain those recorded with each source; a software license does
not grant rights to redistribute a dataset.

The UI package is dual-licensed under CeCILL-2.1 or AGPL-3.0-or-later;
IO 0.2.14 and Formats 0.3.1 carry the same expression. Review their bundled notices and
the repository's [licensing guide](../LICENSING.md) before redistribution.
