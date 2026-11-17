# Published WASM loading and lifecycle

The selected IO/Formats 0.2.14 packages publish Node-target generated glue. Their
browser README examples describe rebuilding an upstream package with a web
target; an equivalent ready-to-use public browser bootstrap is not exported by
these locked artifacts. Current IO 0.3.3 adds idiomatic/numeric-wire/public-dataset
entries but still imports the Node bootstrap. Formats 0.2.17 also publishes the
Node entry. Rebuilding/editing owners, vendoring parsers or using future Preflight
work is outside F3. The known adapter is therefore retained deliberately.

`demo/scripts/wasm-loaders.lock.json` admits the exact version and SHA-256 of both
published glue files and both binaries. Their registry archives/integrities were
checked against the installed files before recording the fingerprints. A lone
substring marker no longer admits an arbitrary generated prefix. Unknown version,
changed glue, changed binary or multiple/missing markers fail at build time.
The original generated parser/export prefix and binary remain unchanged; only
Node filesystem initialization is replaced with a bundled asset URL.

The shared small `createWasmInitializer` owns asynchronous transport only. It
coalesces concurrent requests, caches success, resets the failed promise for
retry, rejects HTTP failure/HTML/corrupt binaries and propagates failed owner
initialization. No partial result or alternate parser is admitted. The module's
exports are restored if its start hook fails. Network/compile causes remain in
the exact technical reason; F2 supplies the localized explanation/action.

IO alone handles CSV/TSV/text. Formats initializes only when a non-table source
will actually call its decoder. Explicit IO configuration remains owner-driven;
the original observation rows, metadata joins, original axis, file binding hashes
and test/predict refusal are unchanged. All four assets remain distributable;
this is lazy execution, not deletion of supported formats.

Checks distinguish scope: small unit modules exercise actual WebAssembly and
promise lifecycle; full browser tests load the actual published IO/Formats and
Methods/Domains binaries under `/nirs4all-domains/`. They test first/lazy load,
transfer, replacement/cancellation, HTTP 404, HTML response, corrupt binary,
wrong exports, fresh-worker recovery, and a corrupt non-table source that reaches
Formats. No successful new scientific reader/format qualification is inferred
from that refusal. Public Pages is checked separately at its deployed main SHA.

Owner-internal instantiation/decode/assembly costs remain opaque in grouped worker
timings. A standards-compliant, versioned owner browser entry/numeric wire could
remove this adapter or further copies later; F3 supplies the required contract
description only and makes no upstream edit or automatic issue.
