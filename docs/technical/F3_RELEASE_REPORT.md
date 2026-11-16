# F3 technical consolidation release report

This is a source/PR engineering delivery, not a package release or deployment.
Baseline is F2 `f4289f51fbae8cad2c460fc8ca1b1c1e0ba2ae13`; its still-open PR
requires [F3 PR #10](https://github.com/dcornet/nirs4all-domains/pull/10) to target
`feat/domains-ux-f2`. Implementation head `3ebb0a6` passed all three Windows/Ubuntu
workflows; [validation](F3_VALIDATION.md) records the actual runs and artifact
review. The PR supplies the delivered documentation SHA, its own final-head CI
and the justified readiness status. No automatic merge or deployment.

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

Measured three-repeat median CSV completion improves from 326.907 to 276.063 ms
on Ubuntu and 326.381 to 296.196 ms on Windows. CSV omits the unused 5,847,640-byte
Formats binary (four loaded modules become three). Complete static distribution
grows by 11,233 bytes; the main-thread heap point sample rises. No general memory,
statistical speed or real-dataset claim is made. Full numeric/hash equality and
all four frozen native/WASM objects hold; full/partial originals, plots/tables and
offline exports remain integral. See [the complete measurements](F3_PERFORMANCE.md).

Updated exact npm pins: AJV 8.20.0, Vite 7.3.8, React plugin 5.2.0, TypeScript
5.9.3, Node types 24.19.2, Playwright 1.65.1 and UI 0.2.5. Retained scientific/IO
cohort: Preflight 0.1.6, Methods 1.3.13/ABI 2.20, IO/Formats 0.2.14 and Cargo.lock.
React/DOM 19.2.3 and Vitest 4.1.12 stay qualified. The reviewed action/toolchain
and Python pins, exact installed runtime notices and advisory limitations are
listed in the dependency/security documents. Rand's disclosed advisory remains
unreachable in the current no-log/seeded cohort; it is not described as patched.

Public Pages remains F1 main `81207cf77a0030203707eb8f4ea63ba41995a79c`, workflow
43908488554, with GitHub Actions publication source and nine actual public
desktop/mobile smoke checks passing. New Pages deployment-action execution must
wait for owner merge; the branch's checked static and Pages-format previews are
not a public F3 deployment. No new scientific finding or independent validation.

Local storage/reservation ceilings do not increase. The staged plan retains 16 MiB
engineering plus 2 MiB essential receipts, 2 GiB free-volume reserves and original
journal/history. The oversized new npm metadata cache was removed on a verified
path; candidate installations and native builds run in CI. Final measured actuals,
including this incident, belong in the PR closure rather than inferred headroom.

The final history check verifies 1,031 protected files, five additional Research
documents and the original reservation journal unchanged. The removed new npm
download cache was 101,486,835 bytes; an exact combined transient peak was not
measured and is not invented. At the pre-documentation checkpoint the combined
scope was 20,804,788,613 / 20,826,468,033 bytes, still with zero new reservations
or ceiling increase; final actuals are recorded in the PR. Remaining work is the
versioned owner browser entry, copy/heap profiling and the separately scoped
appendix selection feature; no Preflight change is made here.
