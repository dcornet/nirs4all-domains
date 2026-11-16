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

## Actual same-host measurement

The first completed comparison is [run 43925581695](https://github.com/dcornet/nirs4all-domains/actions/runs/43925581695),
candidate `3ebb0a6b498c32721c209e1166414bf3780504ce`, exact F2 comparison
`f4289f51fbae8cad2c460fc8ca1b1c1e0ba2ae13`. Both builds use Node 24.22.1 and
Chromium 159.0.8154.6 on the same GitHub-hosted Ubuntu 24.04 runner, three fresh
browser processes per build, serial execution. The virtual CPU/storage model was
not instrumented; OS/cache variation remains. All CSV and live-example scientific
values and hashes compare exactly before any performance summary is emitted.

| Ubuntu measurement | F2 baseline | F3 candidate |
|---|---:|---:|
| Complete static distribution, bytes | 13,422,135 | 13,433,368 |
| Initial index JS, bytes | 479,131 | 482,741 |
| Main stylesheet, bytes | 44,368 | 44,368 |
| CSV-loaded WASM modules | 4 | 3 |
| CSV-loaded WASM file bytes | 11,828,169 | 5,980,529 |
| Landing, median ms | 227.981 | 233.577 |
| CSV import to visible result, median ms | 326.907 | 276.063 |
| Import worker creation to final reply, median ms | 144.300 | 96.500 |
| Eight population-declaration edits, median ms | 190.075 | 185.563 |
| CDP script delta during edits, median ms | 57.442 | 46.093 |
| Layout delta during edits, median ms | 12.102 | 12.461 |
| Main-thread heap point sample, median bytes | 10,631,684 | 12,047,572 |
| JSON export, median ms | 56.099 | 56.631 |
| HTML export, median ms | 928.296 | 936.075 |
| Markdown export, median ms | 61.053 | 60.295 |
| Offline report rendering, median ms | 101.741 | 101.824 |
| Observed process-tree RSS peak, bytes | 845,361,152 | 839,843,840 |
| Entire three-repetition benchmark process, seconds | 7.574 | 7.404 |

The static distribution grows by **11,233 bytes**, including updated code and
notices. The four distributed WASM files are byte-identical across these two
builds: Domains 536,949; Methods 3,119,339; IO 2,324,241; Formats 5,847,640 bytes.
The Formats binary remains available for its existing non-table route but is not
requested for CSV. Worker lazy JS changes from 5,922 to 5,956 bytes; Domains glue
92,809 to 92,845; IO glue 8,236 to 8,109; Formats glue 8,404 to 8,277. A shared
660-byte asset initializer is added; Methods glue stays 127,474 bytes.

Median local HTTP completion times, before/after in milliseconds: IO 13.753/10.900,
Domains 2.502/2.435, Methods 11.038/10.304; Formats 43.202/not requested. Those are
request spans, not pure WebAssembly compilation/instantiation or decoding times.
The exact 11-byte CSV buffer changes from zero transferred bytes to 11 detached,
transferred bytes. Its synchronous postMessage median changes from below timer
resolution (0) to 0.100 ms; this tiny probe supports ownership correctness, not a
large-matrix transport-speed claim.

The higher heap sample, almost unchanged exports/rendering and small observed
RSS difference are retained as contrary/no-gain observations. **No general RAM
reduction or statistical speed claim is made.** Faster small CSV completion is
descriptive evidence consistent with omitting Formats; it does not isolate all
seven dependency updates or predict performance on real datasets.

That Ubuntu job's actual WASM build took 126.944 s, observed 2,842,861,568-byte
summed process-tree RSS and wrote 585,450 binding bytes. Free build-volume space
changed from 88,064,274,432 to 87,656,734,720 bytes. This hosted compiler observation
is separate from the 960 MiB browser benchmark sampling stop and the strict local
browser job guard. No before/after compiler speed or allocation bound is inferred.
Platform job durations and the final exact-head artifacts are recorded in the PR.

The Windows job in the same run also passed all three-repetition equality and
resource checks, with the same Node/browser versions. Its measured comparison:

| Windows measurement | F2 baseline | F3 candidate |
|---|---:|---:|
| Complete static distribution, bytes | 13,422,264 | 13,433,497 |
| CSV import to visible result, median ms | 326.381 | 296.196 |
| Eight declaration edits, median ms | 189.829 | 187.841 |
| CDP script delta during edits, median ms | 51.458 | 43.016 |
| Main-thread heap point sample, median bytes | 10,632,028 | 12,027,400 |
| JSON export, median ms | 58.150 | 55.742 |
| HTML export, median ms | 66.860 | 61.215 |
| Markdown export, median ms | 55.825 | 61.773 |
| Offline report rendering, median ms | 115.637 | 128.290 |
| Observed process-tree RSS peak, bytes | 522,231,808 | 507,068,416 |
| Entire three-repetition benchmark process, seconds | 5.375 | 5.204 |

Windows' Domains WASM is 537,078 bytes; its 129-byte difference from the Ubuntu
build is retained in each platform's manifest. Both builds preserve the four
original scientific report objects exactly. Binary equality is asserted within
each platform's before/after comparison, not across operating systems.
The Windows WASM build took 231.329 s, observed 2,552,647,680-byte summed RSS and
wrote 585,579 binding bytes. Free build-volume space changed from 155,796,099,072
to 155,428,700,160 bytes. These observations do not establish compiler efficiency.

Export spans include automation, download-event handling and Blob reading; the
large Linux/Windows HTML-span difference is not treated as pure HTML generation
cost. Opposite/no-gain outcomes (higher heap, slower Windows offline rendering
and Markdown export) remain in the record. Jobs took 388/759 seconds for browser,
313/502 for scientific gates and 49/66 for read-only contracts (Ubuntu/Windows).
Those include installation/build/test work and are not a same-machine F2/F3 CI
speed comparison. The PR records the delivered documentation-head runs separately.
