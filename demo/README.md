# Domains browser demonstration

This Vite/React application is an exploratory, local browser client for
`nirs4all-domains`. It keeps the imported X population and original axis in
scope, and shows provider evidence with its limitations. It does not accept a
target, fit a predictive model, score a validation split, or establish physical
independence. No upload endpoint or server-side analysis is part of the design.

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
`@nirs4all/formats-wasm@0.2.14`, `nirs4all-ui@0.2.1`, and React 19.2.3.
The local WASM package depends on `@nirs4all/methods@1.3.13`; its provider
contract comes through Preflight 0.1.6 / Methods ABI 2.20. `npm ci` does not
build Rust WASM: generate `native/` first. A clean checkout needs the Rust
target, wasm-pack and npm registry access before a complete browser build.

The Vite `browserWasm()` adapter is a narrow loader for the published IO and
Formats 0.2.14 packages. It retains their parser and binary and replaces the
Node filesystem bootstrap with lazy browser `fetch` of the package WASM asset.
If those published glue files change, the adapter's generated-source marker
check fails; do not silently substitute a different parser or local checkout.

The configured Vite base path is `/nirs4all-domains/`. A static host must serve
the built files beneath that path and provide its normal SPA fallback. `npm
run preview` is a local preview command only. GitHub Pages deployment and
public deployment require owner integration and Pages activation. The
[stacked PR](https://github.com/dcornet/nirs4all-domains/pull/6) provides actual
qualification runs and downloadable static preview artifacts; those are distinct
from a deployed public website.

`src/main.tsx` supplies state, IO/worker orchestration, pure intention changes
and report exports to the presentation components. The commands above are the
clean build sequence; actual qualification is recorded by the PR workflow runs.

## Browser workflow and limits

The landing view accepts files by drag/drop or file picker and offers three
generated synthetic X fixtures plus a public saved tablet example. User files
are processed in the browser. The import path is capped at 32 files, 8 MiB
combined input, 2,000 observations and 1,000,000 spectral cells. IO/Formats
infer and assemble the source; multi-source fusion, aggregation, imputation,
nonfinite X, and silent row deletion are refused. Original partitions are
preserved by IO. Declared test/prediction populations are refused before this
full-source route; a train-fitted browser protocol is not yet qualified. A live
fit of an unpartitioned source is descriptive/transductive. A group column only excludes declared matching groups from
neighbor references; it does not prove that groups are independent units.

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

## Scientific scope

See [WASM capabilities](../docs/WASM_CAPABILITIES.md) for the exact live versus
saved evidence boundary and [architecture](../docs/WASM_DEMO_ARCHITECTURE.md)
for the data path. Synthetic fixtures are deterministic UI/engineering
examples, not research datasets. The public tablet reading is a saved,
source-scoped evidence example and is not refit in the browser. Data rights and
attribution remain those recorded with each source; a software license does
not grant rights to redistribute a dataset.

The UI package is dual-licensed under CeCILL-2.1 or AGPL-3.0-or-later;
IO/Formats 0.2.14 carry the same expression. Review their bundled notices and
the repository's [licensing guide](../LICENSING.md) before redistribution.
