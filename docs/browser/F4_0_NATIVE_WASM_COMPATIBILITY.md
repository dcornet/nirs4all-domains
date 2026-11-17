# F4.0 native and WASM compatibility

This note records declared compatibility surfaces and their boundaries. It is
not a build, browser, provider-execution, qualification, or CI success report.
The F4.0 access contract is described in
[the data access policy](F4_0_DATA_ACCESS_POLICY.md); import ownership is in
[the import architecture note](F4_0_IMPORT_ARCHITECTURE.md).

## Declared package and binding boundary

The Domains WASM package is the local `@nirs4all/domains` binding. Its
`bindings/wasm/index.js` imports `@nirs4all/methods` and checks that the loaded
ABI major is 2 and minor is at least 20. The binding package declares Methods
1.3.13. The demo manifest pins IO and Formats WASM 0.2.14 and UI 0.2.5; its
existing installed UI directory is 0.2.1, so that directory does not verify
the published UI pin. The Methods package is installed under
`bindings/wasm/node_modules/@nirs4all/methods` at 1.3.13. These declarations
describe a possible host setup only.

The Rust WASM adapter in `bindings/wasm/rust.rs` implements Preflight's
`MethodsProvider` contract with a JSON callback. `bindings/wasm/index.js`
implements the callback using Methods' JS exports for PCA, summary,
nearest-neighbors, and HDBSCAN. Repeatability returns the explicit unsupported
reason `NO_BROWSER_REPEATABILITY_PROTOCOL`. Scoped JSON is parsed and validated
by `browser_scoped::parse` / `validate` before `browser_scoped::analyze` calls
that adapter. The existing unscoped `browser_x.v1` API remains a separate
entry point.

## PCA surfaces

Methods 1.3.13 declares two distinct public surfaces:

- `preflightPca(X, k)` returns one diagnostic result containing scores,
  loadings, eigenvalues, full covariance moments, a numerical resolution
  threshold, and unresolved flags. The existing browser callback uses this
  surface for its existing PCA operation. It returns scores for the matrix it
  receives; this alone does not expose a stored fit object for later query
  projection.
- `FlexiblePCA` is a separate generic estimator class exported through
  `estimatorRolesGenerated.d.ts`. Its base `NativeEstimator` declares
  `fit(X, y?, inputs?)`, and `FlexiblePCA` declares `transform(X)`. A public
  fit/transform declaration exists; F4.0 has not qualified the complete
  projected-state boundary needed to fit on train rows and transform a
  separate test query in this browser protocol. Do not treat the declaration
  as proof that a scoped query path is implemented or scientifically qualified.

The scoped `train_reference_test_query` operation currently uses raw-space
nearest-neighbor reference/query matrices. It emits PCA projection support as
unavailable with reason
`TRAIN_FITTED_PCA_TRANSFORM_BROWSER_PROTOCOL_UNQUALIFIED`. It does not use a
test-fitted projection or claim projected support.

## Metadata association surfaces

Methods also declares `preflightFactorAssociation` and
`statsFactorAssociationExact` for factor-code versus target-vector association;
it declares `statsCorrelationTest` and `statsCorrelationExact` for two numeric
vectors. The corresponding signatures expose permutation counts/seeds or an
exact enumeration cap. These are provider APIs, not an F4.0 metadata-field
protocol. They do not encode Domains' field grants, identity/dependency
closure, admissible exchangeability units, target-derived field exclusion, or
population scope. The scoped metadata audit therefore reports counts,
missingness, levels and literal nonmissing overlap; its association field is
unavailable with reason
`DOCUMENTARY_COUNTS_ONLY_NO_QUALIFIED_X_M_ASSOCIATION_PROTOCOL`.

No Methods or Preflight source, ABI, published artifact, or qualification is
changed by these notes. Availability of a symbol and compatibility of a JSON
boundary are recorded separately from actual execution and scientific
qualification.
