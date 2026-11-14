# Software qualification, anomalies and residual limits

Sources inspected at baseline d1b14cc: browser Rust/binding, React controller,
worker/client/IO transport, report model/exporter, dependency notices, parity
fixtures/checker and existing Windows/Ubuntu execution receipts. Inspection is
bounded; absence of another demonstrated defect is not a security certification.

## Demonstrated anomalies

| ID / severity | Evidence and consequence | Scoped response |
|---|---|---|
| S1 / medium | `scripts/check_browser_parity.py` used platform abs/rel 1e-8 for an independent analytical scalar despite the frozen plan's absolute 1e-10. Direct WASM already checked eigenvalues 1 and 4 at 1e-12. No incorrect numerical output was found. | Keep platform tolerance unchanged; analytical checks now use absolute 1e-10 without a relative escape. Three adversarial checker tests distinguish agreeing backends from analytical correctness. |
| S2 / medium | `browser.rs::neighbors` accepted decreasing distances or a missing-value sentinel before a valid neighbor, then summarized slot zero. These are counterexamples to response validation; no actual Methods response was shown to be wrong. | Reject malformed ordering/padding with `INVALID_PROVIDER_RESPONSE` and null value. Do not sort/recompute. Adversaries exercise raw/projected routes and verify no summary call after rejection; ties and valid padding remain accepted. |
| S3 / low | `WASM_DEMO_ARCHITECTURE.md` described a missing controller/exporter and pending hosting; source and actual execution contradicted those statements. README also retained pre-integration hosting text. | Correct only the current product documentation; preserve historical plans and reports. |
| S4 / medium, downstream-renderer concern | Plain source names/finding text could introduce Markdown image/link syntax outside the original JSON fence. An image-capable external Markdown viewer could fetch that image; no application upload or HTML CSP failure was observed. | Escape Markdown delimiters in prose. A regression fixture checks literal image, inline/reference link text and unchanged report/evidence; original JSON remains fenced and exact. |
| Closed deployment issue | Initial Pages run 43505935281 omitted `npm ci` for the binding, causing license preparation ENOENT. The first public deployment also requested a nonexistent root favicon. | efe1033 installs the same pinned dependency as browser CI; d1b14cc declares the official shared icon and tests its subpath. Both fixes are already on main with successful final workflows. |

The corrective validation tests are prospective enforcement of the existing
provider contract, not evidence that an old scientific result was false.

## Ownership, reproducibility and confidentiality

Methods owns PCA, full moments, summaries, neighbors and HDBSCAN. Preflight owns
the public provider/error types; Domains owns scope/refusal/interpretation.
IO/Formats own parsing and assembly; shared UI owns charts/brand assets. No
algorithm, parser or numerical fallback is copied. Native defaults and two
existing crates remain; Python is transport/protocol/report assembly.

Import preserves original columns/order and observation coordinates, rejects
nonfinite/missing X instead of dropping rows, and refuses implicit aggregation,
fusion and retained/prediction populations before full-source fitting. Declared
group exclusions do not authenticate physical specimens or independent units.
An isolated JSON is a schema-validated saved report; exact lowercase
`.nirs4all.json` configurations require their referenced files. No generic JSON
matrix fallback is qualified.

One worker per request receives cloned data; JSON, nested arrays, Float64 buffers
and WASM memory can coexist. The 8 MiB import and 32 MiB serialized-request
limits are not RAM quotas. Rust separately caps 2,000 rows, 1,000,000 cells and
25,000,000 work products; kernels can become unavailable within the input cap.
Worker termination actually interrupts synchronous computation; request epochs
reject obsolete responses. The 120 s client timer is distinct from OS containment
used for qualification. Boundary tests cover finite/shape/identity and major
refusal cases, not the entire admitted shape space.

The public smoke observed only same-origin GET/HEAD requests for static assets
and public examples, with no user-data upload. This is not a claim of zero
network traffic. File names and declared metadata can be sensitive even when raw
X is excluded from reports: users must inspect an export before sharing it.
Saved reports have schema and content binding, not authenticated authorship.
HTML escapes dynamic text and has a restrictive CSP, no scripts/runtime/network
dependency; Markdown/JSON retain evidence. Existing hostile-string and offline
tests passed. No universal sanitizer or new disclosure framework is introduced.

Locks pin Methods 1.3.13 / ABI 2.20, Preflight 0.1.6, IO/Formats 0.2.14 and UI
0.2.1. [Dependency notices](../../demo/DEPENDENCIES.md) distinguish the published
Methods artifact's CeCILL-2.1 declaration and supplemented exact source notices
from generic dual-license repository wording. Registry availability, the narrow
IO generated-glue adapter and version-specific ABI contracts remain maintenance
dependencies. No new vulnerability-free or supply-chain certification is claimed.

## Numerical and performance measurements

The platform comparison remains abs/rel 1e-8; scalar analytical assertions use
abs 1e-10, direct WASM rank-one tests 1e-12. Gram geometry permits sign/tied-space
rotations; pairwise membership/noise permits label permutations. These are
engineering tolerances, not scientific risk thresholds. The common checker
first correctly refused local CRLF fixture bytes against LF-bound CI receipts;
replay with the exact original Git blob passed all four fixtures under the
stricter analytical gate. Hashes were not weakened and no old output was changed.

A pre-bounded single 32-by-2 deterministic fixture measurement reused compiled
WASM: module import 61.913 ms, runtime initialization including file/WASM load
38.241 ms, first complete Domains analysis 13.894 ms. Direct warmed Methods
microbenchmarks: PCA 0.095 ms, PCA-neighbor query 0.188 ms, HDBSCAN 0.112 ms.
These direct timings omit application transport/rendering and are not timings
of individual calls inside that full analysis. No repetitions, distribution,
confidence interval, comparative ranking or scaling claim is justified.

The measurement made at most two PCA, three neighbor and two HDBSCAN calls in
total, no real-source fit. OS process-tree peak commit was 149,438,464 bytes and
observed summed RSS 76,607,488 under 960 MiB; wall time 0.531 s. Browser public
smoke separately peaked at 528,289,792 commit / 779,313,152 summed RSS. Neither
is a universal client memory guarantee. Baseline asset sizes: Domains WASM
536,812 bytes; Methods WASM 3,119,339; IO 2,324,244; Formats 5,847,643. The initial
application JS is about 402 kB uncompressed, with additional lazy chunks; byte
sizes are not download latency or resident memory. Cold public network/paint
timings and maximum-admissible-shape timings are not yet qualified.

## UX and accessibility priorities

1. Preserve observed/hypothetical/unsupported distinctions, explicit scope and
   unknown intended-use alternatives. Keep original-source scientific prose
   separate from translated headings; FR/EN is not a complete prose translation.
2. Explain isolated-JSON routing and exact configuration suffix near import;
   documentation now does so. Do not add an unqualified parser to remove friction.
3. Explain work refusal before large input, copy amplification, and missing
   carried metadata versus absence in the original source. Add per-stage timing
   hooks before claiming meaningful kernel profiling of the app.
4. Qualify keyboard paths beyond the tested skip link, screen-reader reading
   order, chart alternatives, contrast and translated errors with actual users.
   Existing semantic controls/focus/status regions and mobile tests are useful
   implementation evidence, not WCAG conformance or user effectiveness.
