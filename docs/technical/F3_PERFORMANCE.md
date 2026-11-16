# F3 engineering performance measurements

Measurements are technical, on existing tiny synthetic fixtures, not scientific
validation or whole-bank resource predictions. Before/after use exact F2 source
`f4289f5` and F3 on one CI runner, one pinned Node/browser environment and three
fresh browser processes per build, executed serially. The benchmark first requires
identical CSV and synthetic-example scientific values **and hashes**. The F3 PR
links actual exact-head JSON receipts and summarizes the measured numbers.

Fixtures: existing three-row, one-band CSV (`1000` header; values 1,2,3) and the
existing 48-by-24 two-populations synthetic example. No real-source fit, parameter
optimization, row/band reduction, or added scientific diagnostic. Each build uses
three repetitions of the same two routes; all resource limits remain unchanged.

| Measurement | Method / limit |
|---|---|
| Total assets / four WASM / initial and lazy JS | Actual distribution file sizes/SHA-256; static size differs from downloaded/transferred bytes |
| Landing and import-to-visible result | Monotonic elapsed time including automation and two animation frames; complete route, not kernel time |
| Module HTTP loading | Browser-context request timing/body lengths, including worker-origin requests; main-window ResourceTiming alone misses them |
| Worker import/analyze/postMessage | Actual worker events and synchronous postMessage span, input/transfer counts and detached ownership; no numeric payload logging |
| Declaration edits / script and layout | Eight fixed field edits, CDP ScriptDuration/LayoutDuration deltas; not pure React-only attribution |
| Report generation / offline rendering | Actual HTML/Markdown/JSON Blob creation/read and offline page rendering; no external report requests |
| Main-thread heap sample | CDP point sample, not a process peak and not WASM-only memory |
| Process-tree peak | External 50 ms RSS sampler, including Node/automation/browser, with 960 MiB sampling stop and 300 s wall bound; shared pages may be double-counted |
| CI job duration | Actual job timestamps; different hosted machines/queue/cache states prevent causal speed claims across old/new jobs |

Published modules do not expose separate IO decode/assembly or Methods numerical
call timing hooks to this consumer. Initialization/serialization/transport overlap
inside grouped request spans; those individual costs are **not separately measured**.
Local HTTP loading is not Internet latency; OS caches and automation contribute.
Medians of three samples are descriptive, not significance/confidence estimates.

Implemented allocation/work reductions: fresh import buffers transfer once rather
than cloning, the binding fills a single Float64 buffer without an intermediate
flat JS array, obsolete controller references clear when new data starts, and
F1 presentation/evidence HTML memoize by result/locale/intent. No scientific
subsampling or output truncation. The CSV path omits unused Formats initialization;
the four WASM files remain in the complete distributable.

The local baseline (Windows, Node 24.22.1, Chrome 157, F2 dependencies/compiled
WASM reused) observed 13,421,998 static bytes; Domains/Methods/IO/Formats WASM were
536,812 / 3,119,339 / 2,324,241 / 5,847,640 bytes. The corrected one-sample probe
observed four loaded WASM modules, 490.077 ms CSV-to-visible, 123.896 ms for eight
declaration edits, 425,943,040-byte peak job commit and 759,508,992 observed summed
RSS under the existing strict local job guard. This is not the controlled CI
comparison or evidence of improvement by itself. An earlier main-window-only
network probe missed worker requests; its receipt is preserved as incomplete.

Authoritative comparison artifacts are `technical-before.json`,
`technical-after.json`, their `.resources.json` siblings and
`technical-comparison.json`. No performance claim is made before those succeed;
lack of a measured speed/RSS improvement does not invalidate a demonstrated
reliability/security/reproducibility correction.
