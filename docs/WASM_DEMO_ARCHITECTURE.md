# Browser demo architecture

The browser app is a transport and presentation host for existing scientific
providers. It adds no numerical kernel, third Rust crate, server API or Python
runtime.

```text
Browser File / Folder Picker
  -> module worker: published Formats-WASM decode
  -> published IO-WASM role inference, validation and assembly
  -> Domains browser request (complete X, original axis, identities, groups)
  -> existing Domains Rust crate compiled to WASM
  -> public Preflight provider contract
  -> Methods WASM kernels: PCA, summary, exact neighbors, HDBSCAN
  -> report projection -> presentational nirs4all-ui components
```

`demo/src/engine/dataset-io.ts` sends input through IO and Formats; it preserves
partitions, headers, metadata and missingness, and refuses implicit
aggregation, fusion or imputation. It passes only a single dense X source to
the Domains request. User files and analysis stay in the browser; the report
does not contain raw spectra. The runtime accepts declared observation IDs and
optional groups but does not infer physical or reference identity.

`demo/src/engine/worker.ts` imports the browser binding and executes import,
analysis and declaration-only interpretation off the UI thread.
`BrowserEngine` in `client.ts` enforces a 120-second wall-clock limit, uses
request IDs and terminates the worker on cancellation. Rust applies separate
JSON, row, cell and per-kernel work caps. Termination interrupts synchronous
WASM work; it is not a progress callback into the kernel. Browser memory can
exceed payload size while WASM and JSON copies coexist.

`bindings/wasm/package.json` packages the generated glue and binary from the
existing crate with the `browser-wasm` feature. Build via
`npm run build:native` in `bindings/wasm`; generated `native/` output is
ignored. The application pins Methods 1.3.13 and gets its Preflight 0.1.6 /
ABI 2.20 provider binding from the native wrapper. The web binding does not
vendor or reimplement Methods algorithms.

The Vite plugin in `demo/scripts/browser-wasm.ts` adapts the published
`@nirs4all/io-wasm@0.2.14` and `@nirs4all/formats-wasm@0.2.14` glue for browser
loading. It reads package glue at build time, preserves its exports and binary,
and replaces only Node filesystem bootstrapping with an asset URL and lazy
fetch. Its marker check intentionally rejects an unknown generated wrapper
shape. The demo locks `nirs4all-ui@0.2.1`, whose official `nirs4all` logo
assets and qualification charts are imported from the package; it does not
copy an ignored archive or checkout tree. The package currently has no
Domains-specific logo asset.

The app view uses English/French dictionaries, a light/dark CSS token layer,
keyboard focus indicators, skip navigation, live status/error regions,
semantic tables and the shared accessible SVG qualification charts. Charts
are presentational; the host supplies values. The screen-reader and cross
browser accessibility scope still requires its own verification.

Live interpretation preserves the exact evidence fingerprint and changes
only a contextual declaration. It cannot authorize or execute a verification
action. Saved D1-D6.1 companion reading uses the exact packaged source report
and saved annotations; it is not a live-protocol fallback. HTML, Markdown and
JSON are the intended report-only export formats with raw X excluded by
default, but the view exposes callbacks and a host exporter must be verified
before the controls can be considered operational.

## Evidence and publication status

The checked-in CI workflow covers repository scientific gates; it does not
build or publish this Vite demo. A successful Rust/native gate is not evidence
of generated WASM execution. Clean browser build, browser execution, GitHub
Pages CI and deployed preview availability are pending verification. The Vite
base is `/nirs4all-domains/`; deployment must preserve that prefix. Do not cite
a CI configuration or this architecture page as proof of a published site.

At this checkout, `demo/index.html` references a missing `src/main.tsx`, and
`App` still needs host-supplied state and callbacks. The demo shell/runtime
adapter is therefore incomplete; the build commands are a staged recipe, not
a claim that the current tree compiles or runs.
