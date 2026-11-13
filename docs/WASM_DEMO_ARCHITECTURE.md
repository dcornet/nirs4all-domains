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
JSON are report-only export formats with raw X excluded by default. The
controller in `main.tsx` wires the export callbacks to one semantic report
model and local Blob downloads. Offline HTML includes CSP and escaped values.

## Evidence and publication status

`demo/src/main.tsx` supplies state, input/runtime orchestration and callbacks to
the presentational `App`. Existing scientific and read-only reporting gates
remain separate from the demo workflow's actual WASM/build/browser gates.
After integration, main `d1b14cceba483b5b5a0a4d9d0a42a1dd36270c92` passed
[scientific gates](https://github.com/dcornet/nirs4all-domains/actions/runs/43508124497),
[report contracts](https://github.com/dcornet/nirs4all-domains/actions/runs/43508124550),
[browser qualification](https://github.com/dcornet/nirs4all-domains/actions/runs/43508124482)
and [Pages deployment](https://github.com/dcornet/nirs4all-domains/actions/runs/43508124463).
An additional actual public Chromium desktop/mobile smoke passed 25 checks,
including IO CSV, four WASM assets, retained-partition refusal, exports and no
external/upload request or console/page error. Its scope is distinct from CI's
Firefox WASM smoke. The Vite base is `/nirs4all-domains/`; deployment preserves
that prefix. See the [qualification review](qualification/README.md) for limits;
passing these checks does not establish scientific generalization or user utility.
