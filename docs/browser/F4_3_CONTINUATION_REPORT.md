# F4.3 continuation: isolated PCA discrepancy, qualification remains partial

Executed under `OWNER-F43-EXECUTION-20261119` and the unchanged approved plan.
The [staged expectations](F4_3_CONTINUATION_PLAN.md) preceded these executions.
The original scientific protocol, provider cohort, tolerances, hash comparator
and failed evidence remain unchanged. This is a bounded engineering/diagnostic
continuation, not a new real-data experiment or release qualification.

## Integration

Merge commit `30d6dbc` integrates main `f7b88270b3168335159aa85fedb7353bf6d25f74`
into F4.3 without rewriting either history. Worker loading, one-shot import and
dependency ranges/qualified locks are retained. Import acceptance, data-setting
replacement and reset clear both sensitivity histories and frozen references.
Existing worktrees and local modifications remain preserved. TypeScript and all
257 frontend tests passed after integration. PR #16 remains a draft; no PR merge,
release or deployment is authorized or performed.

The separate documentation PR #19 corrects the completed Windows/Ubuntu browser
CI on main and the obsolete README claim that Research is a future repository.
It remains a separate unmerged documentation proposal.

## Same-input numerical attribution: local Windows execution

The [79,399-byte frozen synthetic fixture](../../bindings/wasm/tests/preprocessing-isolation-fixture.json)
retains the exact low-frequency and baseline reference-only requests from the
original WASM artifact. SHA-256:
`5f6312f4655385c26b292812b6f5e36c0113df90300104667e1d1d0d1c388c5f`.
It contains constructed X, ordered keys/axes and declared synthetic factors;
there is no Y, test fit or real dataset. Original artifact SHA-256 remains
`295729f134798353128e516ec367e8a6028c795c3912fa388fb4f3970307557f`.

The [JS driver](../../bindings/wasm/tests/preprocessing-isolation.mjs) and
[native transport](../../crates/nirs4all-domains/examples/browser_preprocessing_isolation.rs)
call the same existing public Methods 1.3.13 / ABI 2.20 APIs. Exact IEEE-754
inputs are transported and independently fingerprinted before each provider call.
The [diagnostic](../../scripts/diagnose_same_input_preprocessing.py) verifies
request-file, request-order, operation and per-vector fingerprints against both
results. Six new adversaries include two backends agreeing on a false input hash.
No local PCA, correlation, ANOVA or preprocessing implementation was introduced.

| Isolated operation | Actual observation | Consequence |
|---|---|---|
| SNV on identical original X, low-frequency and baseline controls | Transformed matrices are exactly equal; both exported SNV states have the same hash | Preprocessing perturbation is unnecessary to reproduce this case |
| PCA on the identical frozen derived matrix | Score Gram, eigenvalues, moments, resolution and unresolved flags pass the frozen comparisons; low-frequency SNV PC5 remains resolved and distinguishable | Geometric agreement does not certify its component-wise factor estimates |
| Pearson / eta-squared on identical frozen scores and metadata | 320 native/WASM requests; zero failures at absolute and relative 1e-10; maximum owner-output difference 4.440892098500626e-15 | The statistic APIs agree for these identical vectors |
| Same official statistic API on the two PCA score vectors | PC5 Pearson difference 5.262218247703565e-6; eta-squared difference 3.082494986032802e-7; eigenvalue 1.3653581275388415e-10 | The PCA-path output difference alone reproduces the original association discrepancy |

There were 332 paired native/WASM requests (332 owner calls per backend), all
with verified IEEE input bindings. Repeated diagnostic attempts are retained
separately; this is a per-run comparison count, not a total across the mission.
All 20 requested axes and their original unresolved flags remain in the diagnostic;
no weak resolved axis was removed. Sign context and indistinguishable eigenvalue
blocks are recorded separately. The diagnostic is `DIAGNOSTIC_ONLY_NOT_A_PARITY_GATE`.
The original full strict comparison was rerun on the original bound artifacts and
still exits 1. The existing five parity adversaries still pass.

This isolates the public PCA path as sufficient to explain the demonstrated
Windows PC5 association discrepancy. It does not establish the internal solver cause,
eigenpair residual or a general numerical error bound: residual/conditioning
evidence is unavailable from this pinned public API. Numerical correction belongs
in Methods. No upstream repository was modified.

At implementation commit `1cf58b7dbb508d34fc0b0764b8a6c06f4f56b55d`,
[actual Windows/Ubuntu CI](https://github.com/dcornet/nirs4all-domains/actions/runs/44527798393)
completed the new diagnostic before the unchanged failed parity gate:

| CI platform | Same-score statistic pairs / failures | Resolved factor mismatches in the two fixed controls | Differing scalar fields in the original full 35-case diagnostic |
|---|---|---:|---:|
| Windows | 320 / 0 | 2 | 144 (27 cases) |
| Ubuntu | 320 / 0 | 0 | 189 (28 cases) |

The small controls therefore isolate the Windows case; they do not reproduce
every Ubuntu discrepancy or qualify generic portability. Full-diagnostic field
counts include repeated owner outputs and are not independent effects or studies.
These are dated, exact-head observations; final delivery CI is recorded separately
in the coordination handoff.

## Explicit hash disposition

| Hash family | Required identity / integrity | Current disposition |
|---|---|---|
| Original source, plan, ordered keys, original/cropped axes, original metadata and reference input | Original declared identity must remain exact | Preserved by existing binding checks; no exemption proposed |
| Fitted state and transformed matrix | Bind each backend's own exact state/derived source | SNV states/matrices agree in the isolated cases; this does not qualify other operators or all opaque state formats |
| Native/WASM raw result JSON | Exact original bytes and per-backend canonical evidence | Historical raw artifacts are retained; original diagnostic validates their links and backend-own ancestors |
| Frozen-reference hash | Link to that backend's exact earlier result | Preserve backend-own lineage; never substitute the other runtime's reference |
| Provider request/payload and derived diagnostic source | Bind the actual invoked values/derived source | Input-vector hashes in this isolation are independently recomputed; other opaque/legacy fields remain unqualified |
| Result evidence hash | Integrity of the full result, including any divergent numeric field | Cross-backend equality fails in the original strict gate; no broad exclusion or replacement semantics were activated |

The active comparator is unchanged and fail-closed. An eventual distinction
between backend-local integrity and portable evidence requires a separately
reviewed, prospectively versioned contract and its adversaries. Classifying these
roles does not waive any existing failure or qualify F4.3.

## Reporting resource findings

Static profiling of the preserved six-family export measured 41,912,332 HTML
bytes, 18,962,476 JSON bytes and 655,755 source elements. Exact duplicate tables
account for 9,054,900 bytes beyond their first copies. These are exported-source
counts, distinct from the historical 245,656 live DOM nodes. Equal tables identify
presentation repetition; they do not authorize omitting requested scientific
content, machine evidence or companions. The original exports were not rewritten.

An experimental Windows Job probe gated the child workload until assignment and
tested aggregate commit limits with an allocation adversary. At nominal 128 MiB
and 256 MiB limits, recorded Job peaks were 156,864,512 and 291,700,736 bytes;
both children failed, and both owned jobs were closed. These measurements do not
demonstrate the proposed ceiling. Job committed memory also does not certify
renderer working set or shared-memory containment. The probe is explicitly
unqualified and is not connected to product or CI print admission.

Consequently the affected printing stage was refused under the prospective plan:
no exhaustive retry, new PDF or successful containment claim. The existing 8 MB
HTML guard remains active. Complete A4/Letter output, incremental browser-memory
profiles, pagination/readability/completeness and final browser qualification
remain unverified. No presentation-contract or multi-volume change was made.

An independent local Chromium pass exercised the actual integrated six-family
reference panel, frozen test audit, invalid-SG refusal, targeted EN/FR automated
accessibility, complete HTML/Markdown/JSON, cancellation and pending-work reset.
It preserved earlier scientific histories and rejected obsolete work after source
replacement. The helper was aligned with the one-shot file chooser and its
scheduling-only cancellation adversary now waits for termination instead of racing
a one-second timer against full-report layout. No numerical output was stubbed.
The final helper deliberately exits 1 at `F43_PRINT_RESOURCE_QUALIFICATION_REQUIRED`;
its receipt has `success:false`. This is partial Chromium execution, not a passing
complete browser/PDF gate or Firefox qualification. Earlier failed selectors and
cancellation-race runs remain preserved separately.

## Checks and bounded next decisions

Actual local checks: formatting; warnings-denied workspace/all-target clippy;
locked workspace library tests (zero unit tests, not full integration coverage);
four retained native ignored preprocessing gates; eight retained protocol spies;
14 public adapter/schema tests; six new identity adversaries; five original parity
adversaries; TypeScript and 257 frontend tests. Retained native binaries reuse
unchanged test sources and the pinned provider; final fresh CI is separate.
Build, public smoke, exact final-head CI, resource closure and publication receipts
must be read from the final handoff rather than inferred from this source document.

1. Methods owner: use the committed small fixture and exact IEEE transport to
   investigate PCA score accuracy/conditioning while retaining resolved PC5 and
   both factor discrepancies. Supply public residual/accuracy evidence or a
   corrected provider cohort through a separately authorized upstream task.
2. Reporting owner: establish effective process-tree physical-memory containment
   with negative/oversized-allocation tests. Then qualify deterministic bounded
   preparation/pagination into one complete A4/Letter PDF, preserving all selected
   content and exact evidence links. A multi-volume alternative requires review.
3. Qualification owner: keep PR #16 draft until the unchanged numerical/hash and
   complete reporting gates pass on the final supported native/WASM/browser matrix.

No new real-data fit, Y access, scientific reservation, budget amendment, Research
campaign, upstream modification, PR merge, product release or deployment occurred.
