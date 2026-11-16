# F3 technical consolidation release report

This is a source/PR engineering delivery, not a package release or deployment.
Baseline is F2 `f4289f51fbae8cad2c460fc8ca1b1c1e0ba2ae13`; its still-open PR
requires F3 to target `feat/domains-ux-f2`. The F3 PR supplies the exact final SHA,
actual workflow outcomes and justified `PR_READY`, `PARTIAL` or `BLOCKED` status.
Do not infer a final status from this document alone while CI is still pending.

Implemented: lazy Formats for table imports; exact published-glue/binary admission;
retryable/coalesced asynchronous asset initialization; worker ownership/cleanup,
deserialization/clone failure handling; zero-copy import-buffer transfer; removal
of a flat matrix-copy intermediate; stale controller-reference cleanup; memoized
F1 presentation and evidence HTML; prevalidated notice generation; selective exact
npm updates; reviewed SHA-pinned Actions and explicit toolchain/Python cohorts;
verified wasm-pack downloads; retained gates without duplicate feature pushes;
same-host before/after measurements and actual published-WASM failure tests.

Preflight **=0.1.6**, Methods **1.3.13**, **ABI 2.20**, Cargo.lock, Rust numerical
source, four reference fixtures, tolerances, F1/F2 report model and scientific
populations remain unchanged. Other repositories/Research are read-only. The
current Domains dual licence is retained. No new scientific campaign or real-data
fit, no version bump/tag/release, no automatic merge, and no F3 Pages deployment.

The [dependency audit](F3_DEPENDENCY_AUDIT.md), [complete snapshot](F3_DEPENDENCY_SNAPSHOT.json),
[compatibility matrix](F3_COMPATIBILITY_MATRIX.md), [loader review](F3_WASM_LOADER_REVIEW.md),
[performance methods](F3_PERFORMANCE.md), [security/licensing review](F3_SECURITY_AND_LICENSING.md),
[validation](F3_VALIDATION.md) and [remaining debt](F3_REMAINING_DEBT.md) distinguish
implemented changes, intentionally retained contracts, externally blocked options
and deferred F4 work. Matching final-head artifacts include full original reports,
partial/full examples, browser captures, exact numeric parity and technical
measurement/resource receipts. A downloadable preview is distinct from Pages.

Local storage/reservation ceilings do not increase. The staged plan retains 16 MiB
engineering plus 2 MiB essential receipts, 2 GiB free-volume reserves and original
journal/history. The oversized new npm metadata cache was removed on a verified
path; candidate installations and native builds run in CI. Final measured actuals,
including this incident, belong in the PR closure rather than inferred headroom.
