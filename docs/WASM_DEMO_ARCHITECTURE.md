# Browser demo architecture

The browser app is a transport and presentation host for existing scientific
providers. It adds no numerical kernel, third Rust crate, server API or Python
runtime.

```text
Browser File / Folder Picker
  -> module worker: published Formats-WASM decode
  -> published IO-WASM inference and preview
  -> shared DatasetBuilder review: roles, explicit keys, joins, partitions
  -> published IO-WASM validation and reviewed assembly (X/Y/M, missingness)
  -> operation-specific Domains scoped request (selected X/M, no Y values)
  -> existing Domains Rust crate compiled to WASM
  -> public Preflight provider contract
  -> Methods WASM kernels: PCA, summary, exact neighbors, HDBSCAN
  -> report projection -> presentational nirs4all-ui components
```

`demo/src/engine/import-draft.ts` uses IO and Formats to prepare a review draft,
translate selected roles and keys into an IO spec, and assemble the confirmed
dataset. It preserves declared partitions, axes, identities, nullable X/Y/M and
missingness; import performs no fit. Aggregation, implicit source fusion, row
deletion and imputation are not introduced. Y remains in the main import state
for inventory and masks, but is omitted from report exports and scientific
worker requests. `demo/src/engine/scoped.ts` constructs an independent grant for
each selected operation. Train structure uses train rows; raw support uses train
as reference and test as query; global descriptive analysis requires explicit
transductive consent, includes train plus test, and excludes predict rows.
Unpartitioned data retain their legacy full-source descriptive route. User
files and analysis stay in the browser. The runtime carries declared identities
without inferring physical or reference independence.

`demo/src/engine/worker.ts` imports the browser binding and executes import,
scoped analysis and declaration-only interpretation off the UI thread.
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
shape. F3 additionally pins the exact published glue/binary fingerprints and
shares retryable/coalesced asynchronous loading. Table imports initialize IO
without the unused Formats module; non-table paths retain Formats. Imported
buffers transfer to their worker once, and worker errors are bound to their own
request. Scientific values/identities and the 120-second deadline are unchanged.
The demo locks `nirs4all-ui@0.2.5`, whose official `nirs4all` logo
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

## Historical F3.5 integration evidence

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

## F4.0 verification status

F4.0 adds the reviewed import and scoped request paths described above. The
historical F3.5 workflow receipts do not qualify these changes. Native/WASM
builds, browser execution and the current CI gates remain pending their own
actual runs; this document makes no F4.0 pass claim. See the
[F4.0 access policy](browser/F4_0_DATA_ACCESS_POLICY.md), [import
architecture](browser/F4_0_IMPORT_ARCHITECTURE.md), [native/WASM
compatibility](browser/F4_0_NATIVE_WASM_COMPATIBILITY.md), and [remaining
capabilities](browser/F4_0_REMAINING_CAPABILITIES.md).
