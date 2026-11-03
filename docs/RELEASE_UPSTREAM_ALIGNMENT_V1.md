# Upstream alignment v1 (Rust 0.1.0-alpha.17, bridge 0.1.0a22)

Tag `v0.1.0-alpha.17` names the Rust crate version. It is unrelated to the
historical scientific milestone "alpha.17" (bridge 0.1.0a17, 2026-10-18), whose
evidence under `docs/benchmarks/alpha17/` is unchanged.

This release integrates D1 ([PR #1](https://github.com/dcornet/nirs4all-domains/pull/1),
selected-branch persistence) and D3 ([PR #2](https://github.com/dcornet/nirs4all-domains/pull/2),
comparison interpretation) unchanged, then moves Domains to the published
ecosystem providers. No protocol, estimator, schema or historical artifact is
added or rewritten, and no bank campaign is rerun.

| Provider | Before | Now |
|---|---|---|
| Rust `nirs4all-preflight` | `=0.1.0-alpha.1` | `=0.1.6` (pins `dag-ml-core =0.3.44`) |
| Methods (`nirs4all-methods`, native library) | 1.3.6 / ABI 2.19 | 1.3.13 / ABI 2.20 |
| DAG-ML (`dag-ml`, predictive extra) | 0.3.41 | 0.3.44 |
| Optional FastAOM entry point (`nirs4all`) | 1.4.10 | 1.4.14 |
| Datasets (optional extra) | 0.3.11 | 0.3.11 |

## Code changes

- Preflight 0.1.6 changed `ProviderError` from a string tuple to
  `{kind, reason, detail}`. Adapters read the stable `reason` code, as before.
  The alpha.13 qualified transport sources (`unsupervised.rs`, `methods.rs`)
  differ from their frozen digests only by this accessor;
  `providers.frozen_transport_digest` maps it back and proves that no other byte
  changed (used by `check_alpha13_results.py` and the multiscale pin test).
- Report provenance records the actual Preflight engine version instead of a
  hard-coded `0.1.0-alpha.1`.
- The exact-version gates of new native fits (bank, dependence, predictive,
  split stress, multifamily, FastAOM) read one table, `providers.QUALIFIED_NATIVE`
  / `QUALIFIED_NIRS4ALL`. Replaying historical evidence still needs its recorded
  providers and Domains commit; a 1.3.6 library cannot load under Preflight 0.1.6,
  which requires ABI 2.20.
- Selected-branch persistence is qualified for Methods 1.3.13 / ABI 2.20.0 in
  addition to 1.3.6 / 2.19.0: under 2.20 the native gate reproduces the eight
  frozen public HDBSCAN reference cases, with labels, cluster counts and tree
  parent/size/label exactly equal and persistence, lambdas and stability within
  `1e-12 * max(1, |expected|)`.
  Any other version/ABI pair stays `PROVIDER_PERSISTENCE_SEMANTICS_NOT_QUALIFIED`.
- Provenance labels of factor association and correlation screens report the
  installed Methods version instead of a hard-coded 1.3.6.
- Clippy on Rust 1.96: one `nonminimal_bool` rewritten with `is_none_or`
  (identical truth table).

## Scientific behaviour: what changed and why

The baseline (D3 head, Preflight alpha.1, Methods 1.3.6, DAG-ML 0.3.41) and this
release were run through every CI step on the same Linux host and their JSON
outputs compared field by field.

1. **Unchanged within rounding.** Every Domains-computed status, label, count,
   cluster assignment, selection and finding is identical in the analyze,
   structure, dependence, split-stress, batch, multiscale, comparison and
   validation-intent outputs. Floating values differ by at most 1e-11 absolute
   (1.6e-8 relative on values above 1e-8, on near-degenerate trailing PCA
   directions), from Methods' compensated accumulation and from Preflight's
   transitive `serde_json/float_roundtrip` feature, which now parses JSON floats
   exactly as Python wrote them (previously possibly 1 ulp off). Input hashes of
   Rust-parsed requests change for that reason.
2. **Embedded Preflight object.** `report.preflight` is upstream output. Preflight
   0.1.6 adds descriptors (clustering, confounding, domain shift, quasi-duplicates,
   SNV sensitivity, and `probe.*` entries of a grouped validation probe), and
   drops unresolved zero PCA eigenvalues (`[36, 0, 0]` becomes `[36]`). Domains
   supplies no validation provider, so every `probe.*` metric is `unsupported`
   and no probe fit runs. Retained-test references are still never passed to
   Preflight. Domains does not consume the new descriptors; its findings are
   unchanged.
3. **Methods numerical domain (deliberate upstream rule 13/15).** HDBSCAN and
   exact PCA moments now refuse inputs whose max/min nonzero |x| exceeds 2^32
   (`N4M_ERR_UNSUPPORTED`). Rank-deficient retained scores (a round-off trailing
   component next to unit-scale ones) are therefore refused. On the 34 alpha.13
   controlled transport requests, clustering becomes
   `unavailable/METHODS_HDBSCAN_STATUS_10` for exact repeats, close independents,
   known acquisitions, scatter, SNV-erased and SNV-enhanced (raw and SNV), and
   the close-independent raw effective dimension becomes
   `EXACT_COVARIANCE_MOMENTS_UNAVAILABLE:METHODS_PCA_STATUS_10`. Status and reason
   are explicit; no value is invented. Two-band SNV inputs, and generally SNV
   inputs with no more bands than retained components, now meet this refusal.
4. **Methods PLS null components (deliberate upstream change).** A component
   beyond the numerical rank of X is published as a flagged null component
   (predictions equal to the truncated model) instead of failing the fit.
   Inner grids that previously failed on rank-deficient training folds now
   succeed, and the selected count may include null components. Grids beyond
   min(n - 1, p) are still refused natively and propagate without retry.

Committed historical results (bank, campaign, alpha.8–18 evidence) were produced
with the providers they record and stay valid; they were not regenerated.

## Upstream proposals (not applied)

- Methods: the 2^32 spread rule on HDBSCAN coordinates refuses rank-deficient
  PCA scores although Euclidean distances are not harmed by a round-off
  coordinate. Applying the rule to distances, or treating resolved-zero
  coordinates as exact zeros, would restore these inputs.
- Domains could read Methods' `unresolved_components_` flags to report the
  effective PLS component count; this needs its own protocol change.

## Licence

Domains is now dual-licensed `CECILL-2.1 OR AGPL-3.0-or-later`, like the rest of
the ecosystem ([LICENSING.md](../LICENSING.md)). All Rust and Python dependencies
are permissive or carry the ecosystem's dual/CeCILL licence; none blocks it.

## Validation

See [validation](VALIDATION.md). Next D1–D5 priority is unchanged: **D4**.
