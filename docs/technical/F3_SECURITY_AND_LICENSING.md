# F3 bounded security and distribution review

This review is not a security certification. Production scientific definitions,
Preflight =0.1.6 / ABI 2.20, Methods 1.3.13 and Domains' dual licence remain intact.
No owner repository, generated owner package or historical evidence is patched.

The initial npm audit reported two affected direct dependencies:

- [AJV GHSA-2g4f-4pwh-qvx6](https://github.com/advisories/GHSA-2g4f-4pwh-qvx6)
  concerns the `$data` option. Domains uses fixed checked-in schemas without that
  option, limiting the described execution path. AJV is nevertheless updated to
  8.20.0; actual schema/status/null/source-binding tests must remain equal.
- [Vite GHSA-587h-7wmj-h5pm](https://github.com/advisories/GHSA-587h-7wmj-h5pm)
  and related launch-editor/middleware advisories affect the old dev tool. Static
  Pages does not run a Vite development server; local dev binds loopback. The
  supported 7.3.8 security backport is selected instead of a bundler major migration.

An OSV query of all 88 registry Cargo packages reports the aliases
`RUSTSEC-2026-0097` / `GHSA-cq8v-f236-94qc` for rand 0.8.5. The
[primary advisory](https://rustsec.org/advisories/RUSTSEC-2026-0097.html) requires
the log feature, a reentrant custom logger and ThreadRng reseeding. Current Cargo.lock
contains no log package, and the native source uses explicitly seeded ChaCha8Rng,
not `thread_rng`/`rng`. That described path is therefore not reached in this
qualified cohort. Rand remains frozen to preserve historical sequences; the alert
is disclosed, not suppressed or described as patched. A downstream application
enabling new features/custom logging requires another reachability review.

Exact npm lock integrity, full action commit SHAs and exact Rust/Node/Python
cohorts reduce moving-input ambiguity. wasm-pack 0.13.1 archives were fetched from
the official release, hashed, and are verified on every install before extracting
one regular explicitly named member. This is SHA-256/source pinning, not a signed
vendor attestation. Upstream composite actions can still reference their own
floating action tags; pinning our top-level action does not claim an immutable
transitive action graph. Hosted OS images and registries remain external inputs.

The exact published IO/Formats glue and binary hashes are checked before applying
the known bootstrap adaptation. No parser fallback, owner modification, force-fix
or wholesale dependency upgrade. Existing HTML CSP, safe Markdown fences, hostile
source fixtures, no-script/no-network offline reports and raw-X exclusion remain.
No import is uploaded; sharing exports can still disclose IDs/PCA/declarations.

`prepare-licenses.mjs` first validates installed versions against the locked
production closure, then regenerates allowed notices. A stale installation can
no longer erase the previous notices before failing. Candidate notices must be
reviewed/committed from actual installed packages, then regenerated with no diff
on the final CI head. Test-only axe/Playwright/compiler dependencies are outside
the production bundle; published production notices include actual runtime
transitives and preserve Methods' known upstream licence-wording discrepancy.

Windows' available tested Python 3.11.9 is pinned separately from Linux 3.11.18;
F3 does not claim these have identical maintenance/security status. No implicit
new Python numerical-oracle/runtime migration is made. Native providers are loaded
only from the explicitly selected trusted library location.
