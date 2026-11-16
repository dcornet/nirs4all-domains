# F2 qualification and release record

Base: `c8e7f183886381aa9986055ebb0b190e643d4cf8`, branch
`feat/domains-ux-f2`, PR base `feat/domains-report-f1`. PR #8 was verified open,
unmerged and at this exact head before F2. No automatic merge or public deployment
is part of F2. The F2 PR records delivered SHA, exact-head hosted workflows,
verified preview and screenshots/report artifacts; configuration alone is not
evidence of successful CI execution.

## Executed local checks

- TypeScript strict check, **73 Vitest tests** (65 existing F1/historical tests
  plus 8 F2), production Vite build, public saved-example schemas/owner replay,
  bounded distribution audit and `git diff --check` pass.
- **7 actual compiled WASM tests** pass against pinned published Methods,
  without a native rebuild. The four original parity reports remain exactly
  equal to the previous qualified artifacts, including the computed all-noise
  partition and zero admissible-neighbor rows. This is reuse/verification of
  already-qualified synthetic kernels, not new-function native/WASM parity.
- The complete local no-capture Chromium run passes **38 checks**, including
  real IO/Methods WASM, live/saved, metadata, full/partial exports, retained
  partition refusal, cancellation, intent-invariant measurements/display state,
  mobile, offline/print and deliberate WASM-failure recovery. No console/page
  error or off-origin/upload request occurs on normal paths. Deliberately
  blocked-WASM expected console failures are isolated and recorded separately;
  unexpected failures still fail. No substitute numerical result is accepted.
- The full functional run takes 29.469 seconds, with OS process-tree peak commit
  584,732,672 bytes and observed summed RSS 895,660,032 under the unchanged
  960 MiB commit/RSS guard. Native Firefox execution is left to existing CI;
  local second-engine coverage is explicitly marked not executed.
- Actual desktop/mobile screenshots were opened for visual review: landing,
  import help, source, spectra, PCA/scree, density, contextual warning/intention,
  unavailable evidence, synthesis, complete saved report, offline/print and dark
  French mobile. Layouts retain exact evidence and scrollable technical tables.
  This is AI visual inspection, not real-user effectiveness evidence.

Initial failures remain recorded: the first new Markdown assertion ignored
intentional CommonMark colon escaping; the first new security assertion also
mistook the trusted embedded logo for an external image. Those tests were corrected
to verify actual safe rendering/JSON, without removing historical adversaries.
A new progress test initially used the wrong component props. The initial axe
audit found step-number contrast 3.38:1; opacity was removed and the audit passes.
The combined capture run was stopped by the RSS guard at 1,047,785,472 observed
bytes, with no RAM-limit increase. Remaining captures were separated. One local
capture-only helper had a shell-encoding-corrupted theme locator; it was stopped
and the mobile capture rerun with the actual button selector. The product's full
mobile path already passed. Failed/partial receipts are not successful runs.

## Mandatory scenario coverage

| Scenario | Actual check / scientific boundary |
|---|---|
| 1 Valid CSV | IO WASM 3 acquisitions × 1 variable, variance one |
| 2 Invalid import | Missing/nonfinite cells, malformed JSON and oversize real File refused; no repair |
| 3 Metadata | Explicit IO configuration with X/M CSV; 3 named columns and original rows |
| 4 X without metadata | Actual simple CSV retains unknown physical independence |
| 5 Retained test | Both test and predict refused before full-X fitting; exact reason/action |
| 6 Synthetic live | Actual Rust/Methods WASM example; explicitly synthetic |
| 7 Saved tablet | Original public companions and intent variant; zero worker fit |
| 8 Two-component PCA | Live actual score/eigenvalue figures retain exact F1 evidence |
| 9 One component | Actual CSV produces one component; 1D display without measured PC2 |
| 10 PCA unavailable | Actual constant X preserves reason/null and no points |
| 11 All-noise density | Frozen eight-row geometry imported through IO; computed labels all -1, zero clusters |
| 12 No admissible neighbors | Original actual-WASM declared-group-exclusion fixture has zero neighbor rows; no synthetic distance substituted |
| 13 Intent | Original hash/metrics and axis display state unchanged; no split selected |
| 14 Language | FR/EN live/saved readings, unchanged original source objects |
| 15 Theme | Real theme controls and dark/mobile captures |
| 16 Cancel | Actual worker constructed/terminated, stale result absent |
| 17 WASM error | Real asset abort, labeled recovery action, no result fallback |
| 18 Keyboard | Skip, four open step links, native help and destination focus |
| 19 Proof | Exact links resolve/reveal their original evidence object |
| 20 Short export | Explicit partial label, full source JSON retained, safe CommonMark |
| 21 Complete export | Default full F1 figures/tables/originals across three formats |
| 22 Offline/print | Script-free CSP HTML, no requests, printed partial/full scope; A4/Letter PDFs in CI |
| 23 X exclusion | Original full model omits raw X, no upload/off-origin; hostile filenames/source escaped |
| 24 Mobile | Actual 390 px viewport, no document overflow, FR dark and PCA/table captures |
| 25 Return to data | Report-to-data link focuses the same dataset without changing measurements |

The no-neighbor test uses the actual public binding contract; it does not claim
that the metadata-only import example certifies group keys. Historical F1/D1–D6.1
tests, fixtures, scientific schemas and expected numerical values remain intact.
The new eight frontend tests exercise exact source preservation, both locales,
safe partial HTML/CommonMark, all statuses, actual guidance semantics and anchors.

## Hosted qualification, resources and delivery

The unchanged Windows/Ubuntu workflows run native fmt/warnings-denied Clippy,
workspace/ignored native/bridge/schema/history gates, read-only report contracts,
actual WASM/common-fixture native parity, frontend and Chromium/Firefox checks.
Exact-head successes, counts and artifacts are recorded in the PR after completion.
Large previews, complete/partial HTML/Markdown/JSON examples and PDFs are CI
artifacts rather than extra local copies. Serve the downloaded preview beneath
`/nirs4all-domains/`; it is distinct from GitHub Pages on main.

Initial combined footprint: **20,755,598,282 / 20,826,468,033 bytes**, with
70,869,751 bytes headroom. Campaign remains **2,015,788,498 / 2,023,410,176**.
An intermediate measurement was **20,782,371,965**; retained npm cache/browser
temporary files required correcting the internal engineering estimate from
16 to 32 MiB, plus unchanged 4 MiB essential evidence. Global ceilings and
reservations increase by **zero**; 2 GiB volume reserves remain. Final actual
measurement and protected-history/journal verification are recorded in the PR.
The only dependency addition is test-only axe-core 4.14.1; scientific/provider
versions, production notices, package versions and product licences do not change.

No scientific algorithm, real-source fit, raw-data acquisition, Research/upstream
write, release, tag, merge, risk probability or human validation claim. Remaining
[debt](F2_REMAINING_DEBT.md), [accessibility scope](F2_ACCESSIBILITY.md),
[user guide](F2_USER_JOURNEY.md) and [baseline contract](F2_BASELINE_AUDIT.md)
bound the delivered behavior.
