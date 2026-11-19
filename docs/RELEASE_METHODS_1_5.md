# Domains 0.2.0 — Methods 1.5 cohort

This release selects Methods 1.5.0 / ABI 2.24, DAG-ML 0.5 and Preflight 0.3. It is a minor release because the upstream preprocessing and wide-branch Preflight PCA score corrections can change existing numerical results. Domains adds no numerical implementation, protocol or schema change. Python selects the SDK 1.6 optional FastAOM entry point; unrelated pinned scientific references remain unchanged.

Current native and browser admission checks identify this cohort explicitly. The multiscale descriptor accepts the new Methods/ABI pair after all eight frozen native HDBSCAN reference cases passed unchanged, including their original 1e-12 tolerance. Historical provider pairs, evidence files and saved reports remain historical records.

## Executed candidate qualification

On Linux, the source candidate used the actual public Methods 1.5 Python wheel (native library SHA-256 `215c57f294f43dc61c6b1ca9c2635758ce03fa15646834f01b134caa6869f042`), qualified DAG source `d3608565a5fe27875d4b64e54035eb8b4c05b204` and the Preflight 0.3 release source through an isolated, non-distributable Cargo configuration. The Python environment installed measured candidate SDK/Core/DAG wheels explicitly. These source-stage artifacts are distinct from public-registry builds.

- Rust workspace tests and all 31 explicit native tests pass; all eight frozen HDBSCAN cases pass without fixture or tolerance changes.
- Clippy on the installed Rust 1.96 toolchain passes. Three existing Boolean option predicates were simplified equivalently for that lint version.
- The installed Python bridge passes all 535 integration tests on Python 3.14.3, including native providers, FastAOM, held-out label adversaries and the new qualified multiscale pair.
- Actual Rust WASM and published Methods pass the binding tests; native/WASM parity also passes: 22 factor cases with 690 numeric comparisons and 27 support cases with 13,994 numeric comparisons, with the original tolerances and all pre-provider refusals preserved.
- The browser demo passes type checking, 246 unit tests, production build and the full actual Chromium and Firefox journeys. CI-mode Chromium also generated all 16 A4/Letter selection exports plus factor/support PDFs; structural text/bounds checks pass, and three representative raster pages were inspected separately. Local synthetic fixtures only were used; no experiment or data upload occurred.
- Static licensing includes the complete published Methods notice tree plus byte-identical source notices for the pinned owner commit. The coordinator verified source notice bytes against the pinned Git archive; the build records notice hashes and sizes. Superseded source notices remain in Git history and are removed from the current served tree.

Exact commands, exits, failures and corrected retries are retained in the release coordinator's `STATUS.md` and raw gate receipts. The final Cargo lock now selects actual registry Preflight 0.3.0, DAG-ML 0.5.0 and n4m 0.5.0 with their published checksums; the final native CLI builds successfully without source overrides. Final installed smokes, hosted CI, merge and served-site verification are recorded separately before delivery is claimed. Temporary source-stage locks are preserved outside the repository and are not distributed.
