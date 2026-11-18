# F4.2 native/WASM parity record

Local actual-owner qualification recorded 2026-11-18 for `domains.browser_train_fitted_support.v1`. Protocol and expected behavior were frozen in [F4_2_SCIENTIFIC_PROTOCOL.md](F4_2_SCIENTIFIC_PROTOCOL.md) before the computational comparison. The worktree is based on `b2d35182a174381a8b6ffac876316c83d78d21ba`; bind all run receipts to the exact final delivery SHA before making release claims.

## Executed comparison

| Item | Result |
|---|---|
| Computational fixtures | 27 deterministic synthetic requests through compiled WASM and native Methods |
| Access adversaries | 7 pre-provider refusals; zero Methods calls on refusal |
| Numeric comparisons | 13,994 values compared at absolute and relative tolerance `1e-10` |
| Exact comparisons | Fixture IDs, exact original request/input hashes, fit/query role keys, ordered populations, access flags, provider operation scopes, statuses/reasons and structural output fields |
| Actual owner | Methods 1.3.13 / ABI 2.20 on compiled Domains WASM and native binding; no mock numerical backend |
| Fit lifecycle | One train FlexiblePCA fit, train and test transforms through same retained state; owner state unchanged through transforms and explicitly destroyed |
| Cross-platform hashes | Serialized fit-state and evidence hashes are not required to match native vs WASM |
| Rotational degeneracy | Two constant/isotropic cases compare combined Gram/subspace invariants; component coordinates are not forced to match under rotation |

The synthetic fixture source is `bindings/wasm/tests/support-fixtures.json`. The replay and comparison entry points are `bindings/wasm/tests/support-protocol.mjs`, the `browser_support_qualification` example, and `scripts/check_support_parity.py`. The workflow's reproducible stages are:

```text
node bindings/wasm/tests/support-protocol.mjs wasm demo/test-results/support-wasm.json
```

```text
cargo run --quiet --locked -p nirs4all-domains --example browser_support_qualification -- demo/test-results/support-wasm.json
```

The example's stdout is saved as `demo/test-results/support-native.json`; then:

```text
python scripts/check_support_parity.py --native demo/test-results/support-native.json --wasm demo/test-results/support-wasm.json --out demo/test-results/support-parity-receipt.json
```

These commands reproduce the local fixture protocol when run from a built worktree with pinned dependencies. Their presence in the workflow is not itself execution proof. Hosted Windows/Ubuntu job results and final artifacts remain pending in [F4_2_VALIDATION.md](F4_2_VALIDATION.md).

## Robustness and boundaries

The local native regression summary-error/invalid-transform sequence initially exposed premature PCA handle destruction. The provider adapter now explicitly preserves/destroys the handle correctly, with RAII cleanup. Its ignored actual-native regression passed. This is a lifecycle correction and does not change any numerical kernel or tolerance.

Expected and observed owner limits remain explicit:

- FlexiblePCA publishes scores and its fitted state, but not eigenvalues or numerical-rank resolution. Those output fields remain unavailable with reasons.
- A constant reference can return `effective_components=0`; finite Q values are retained and undefined T² values carry owner reason metadata. Empirical limits are not qualified because there is no resolved reference component.
- At extreme scale, projection and score summaries can remain available while the monitor returns `NUMERICAL_DOMAIN_EXCEEDED`; operation statuses are independent.
- Cross-backend parity does not claim portability of identical serialized-state bytes or identical coordinates in rotationally ambiguous eigenspaces.
- All fixtures are generated and deterministic. They do not establish real-study utility or independent-unit calibration.

The unchanged historical F4.0 four-case comparator remains separate. F4.1 keyed score evidence is likewise not regenerated or consumed as the F4.2 fit. Exact final run URLs, artifact digests and host OS details will be attached after hosted CI completes.
