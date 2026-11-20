# Domains 0.2.0 — Methods 1.5 cohort

This release selects Methods 1.5 / ABI 2.24, DAG-ML 0.5 and Preflight 0.3. Python native fits require the qualified Methods 1.5.1 patch. The earlier release candidate separately qualified a Methods 1.5.0 browser artifact; concurrent F4.3 Main selects its own Methods 1.5.1 browser matrix with the integration limits below. It is a minor release because the upstream preprocessing and wide-branch Preflight PCA score corrections can change existing numerical results. The owner-cohort bump itself adds no numerical implementation, protocol or schema change. The integrated source also includes the separately accepted F4.3 preprocessing protocol and domains.portable_report.v2 from Main; those keep their own qualification boundary. Python selects the SDK 1.6 optional FastAOM entry point; unrelated pinned scientific references remain unchanged.

Current native and browser admission checks identify this cohort explicitly. The multiscale descriptor accepts the new Methods/ABI pair after all eight frozen native HDBSCAN reference cases passed unchanged, including their original 1e-12 tolerance. Historical provider pairs, evidence files and saved reports remain historical records.

## Python 1.5.1 / Datasets 0.3.22 qualification

The new-fit table requires exactly Methods 1.5.1, DAG-ML 0.5.0 and SDK 1.6.0.
The predictive extra requires Methods `>=1.5.1,<1.6`; other patch versions remain
explicitly unqualified for new fits. The metadata-only catalog inventory admits
Datasets 0.3.11 and 0.3.22 exactly, and refuses other versions before repository
or descriptor access. Adapter provenance records the actual installed version.

On Python 3.11.15 with sklearn 1.7.2, public Methods 1.5.1 native library
`b97d032c3810f4d4e536aa9b95bf279765789e3bbaeb807ae2eb0ba536f42dc9`,
public DAG/Core/IO owners, SDK 1.6.0 candidate wheel `75f3d0c3...` and the
Datasets 0.3.22 wheel from source `478ece43...`, the complete Python integration
suite passed **536 tests and 74 subtests, zero skips**. An independent Opus 5.5
review reran that suite at `019d4003...` and the unchanged eight-case native
HDBSCAN reference with its original `1e-12` tolerance; both passed. The subsequent
explicit installed-Datasets profile assertion passed all 14 bridge tests.
These are candidate qualification results, not claims that SDK/Datasets or
Domains were already published. No historical numeric fixture was regenerated.
CI selects the same owner versions through its constraints and installs the
SDK with normal dependency resolution and `pip check`.

## Earlier source and browser candidate qualification

On Linux, the source candidate used the actual public Methods 1.5 Python wheel (native library SHA-256 `215c57f294f43dc61c6b1ca9c2635758ce03fa15646834f01b134caa6869f042`), qualified DAG source `d3608565a5fe27875d4b64e54035eb8b4c05b204` and the Preflight 0.3 release source through an isolated, non-distributable Cargo configuration. The Python environment installed measured candidate SDK/Core/DAG wheels explicitly. These source-stage artifacts are distinct from public-registry builds.

- Rust workspace tests and all 31 explicit native tests pass; all eight frozen HDBSCAN cases pass without fixture or tolerance changes.
- Clippy on the installed Rust 1.96 toolchain passes. Three existing Boolean option predicates were simplified equivalently for that lint version.
- The installed Python bridge passes all 535 integration tests on Python 3.14.3, including native providers, FastAOM, held-out label adversaries and the new qualified multiscale pair.
- Actual Rust WASM and published Methods pass the binding tests; native/WASM parity also passes: 22 factor cases with 690 numeric comparisons and 27 support cases with 13,994 numeric comparisons, with the original tolerances and all pre-provider refusals preserved.
- The browser demo passes type checking, 246 unit tests, production build and the full actual Chromium and Firefox journeys. CI-mode Chromium also generated all 16 A4/Letter selection exports plus factor/support PDFs; structural text/bounds checks pass, and three representative raster pages were inspected separately. Local synthetic fixtures only were used; no experiment or data upload occurred.
- Static licensing includes the complete published Methods notice tree plus byte-identical source notices for the pinned owner commit. The coordinator verified source notice bytes against the pinned Git archive; the build records notice hashes and sizes. Superseded source notices remain in Git history and are removed from the current served tree.

Exact commands, exits, failures and corrected retries are retained in the release coordinator's `STATUS.md` and raw gate receipts. The final Cargo lock now selects actual registry Preflight 0.3.0, DAG-ML 0.5.0 and n4m 0.5.0 with their published checksums; the final native CLI builds successfully without source overrides. Final installed smokes, hosted CI, merge and served-site verification are recorded separately before delivery is claimed. Temporary source-stage locks are preserved outside the repository and are not distributed.

## Integration with concurrent F4.3 Main

The concurrent Main source `d644ec7` adds the F4.3 browser and its separately
reviewed Methods 1.5.1 admission. Its browser scientific comparators, fixture values, tolerances and explicit
unresolved strict numerical parity outcomes are preserved. The shared Rust
lock deliberately selects Preflight 0.3/DAG 0.5/n4m 0.5, which also changes the
browser build. Integrity receipts now report the compiled Preflight version;
this is a new integration cohort requiring browser qualification. The earlier browser 1.5.0
qualification above describes the earlier release candidate, not this integrated
F4.3 runtime. No passing old-browser result certifies F4.3. The integrated native Rust and Python source has now passed its affected
gates and independent reviews, recorded below. The browser cohort retains its
separate failed qualification.

The native preprocessing test profile explicitly selects the published
Methods 1.5.1/ABI2.24 provider. Only its provider-version admission changes;
all analytical expectations, lifecycle assertions and tolerances remain unchanged.
The source Main 1.3.13 qualification remains historical evidence.

On the integrated source, the public-owner Python profile passes 543 tests and
74 subtests without skips. The Rust qualification profile (dev optimization and
assertions, debug symbols disabled) passes all 97 tests, including every ignored
native case, on the actual published Methods 1.5.1 library. Schema drift checks,
protected alpha8–18 checks and synthetic CLI protocols pass. Independent Opus 5.5
source closure passes after the compiled Preflight provenance correction.
These results do not certify the browser cohort. Its required F4.3 strict
native/WASM parity gates ran and FAILED on 7 Ubuntu / 4 Windows fields; it remains
unqualified, including the cohort-level claim for F4.0–F4.2. Passing individual
factor/support/scoped checks do not qualify that whole browser consumer.

## Final native source release scope

The current native Rust/Python cohort passes the hosted scientific gates on
Ubuntu and Windows (run 44753856572), including the complete original numeric
references. The functional browser/lifecycle/export jobs pass on both platforms
(run 44753856604), while both strict F4.3 numerical jobs and their final aggregate
correctly FAIL. The warning/report contracts also pass (run 44753856565). No
expected-success wrapper, allowed failure, fixture rewrite or tolerance change
was added.

Against the accepted Main source 1e195a7 (run 44707228685), the current source
has bit-identical 7 Ubuntu / 4 Windows failure lists, including every native/WASM
value and path, with the same 1,045,533 / 1,045,536 comparisons. All 3,237,280
numeric paths, types and binary values across ten complete Linux native/WASM
preprocessing, factor, support, scoped and base reports are identical. This
shows no new numerical behavior from the owner-cohort integration; it does not
turn the existing failed browser qualification into a pass.

The source prerelease delivers the qualified native Rust and Python adoption.
The existing browser profile stays exploratory and unqualified, as its current
production declarations and exported reports state. No universal operation,
portability or predictive-performance certification is claimed. An independent
Opus 5.5 release-scope assessment found no new scientific or contract blocker for
these explicit claims; it neither approved a waiver nor qualified the browser.
