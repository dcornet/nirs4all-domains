# F4.3 preprocessing Methods API matrix

## Scope and evidence

This is a read-only API audit for `@nirs4all/methods` 1.3.13, ABI 2.20.0. The installed public WASM package reported `version() = "1.3.13+abi.2.20.0"` and `abiVersion() = [2, 20, 0]`. The upstream source evidence is pinned to `GBeurier/nirs4all-methods` commit [`fa8ff57603ec23bce95f73d52170285e8f3e2861`](https://github.com/GBeurier/nirs4all-methods/tree/fa8ff57603ec23bce95f73d52170285e8f3e2861), not an assumed current branch head.

The package declarations and runtime manifest establish the published JS/WASM class names, parameter defaults/types, fit-input requirements, state-format labels, and serializer methods. The pinned C headers establish native contracts for the corresponding numerical operators and the generic native estimator ABI. A small probe on synthetic 2×5 matrices checked only the crop endpoint and Normalize mode behaviors noted below. These observations establish availability/contracts; they do **not** qualify the full F4.3 protocol, cross-runtime parity, or every class’s numerical edge cases.

This document covers Methods preprocessing APIs only. AOM is a separate provider and version surface; its preprocessing bundle is not evidence for Methods 1.3.13 and is not audited here.

## Shared estimator lifecycle

Each listed transform is exported as a generated class extending `NativeEstimator` and implements the `Transformer` role:

1. Construct with the class’s typed parameter object.
2. Call `fit(X_train, y?, inputs?)`; for this X-only panel omit `y` and fit inputs except the Resampler axis.
3. Call `transform(X)` on the intended rows. Reuse the same fitted instance for held-out data when the transform learns state.
4. Export fitted state with `toN4me()` if it must be persisted, restore with `NativeEstimator.fromN4me(bytes)`, then release each instance with `dispose()`.

The manifest lists these as serializable transformer estimators. Its `state_format` is descriptive: most entries record width even for operations that are otherwise row-local. It does not mean that fitting used Y. Every row-level transform in this table has `y: optional` and no required Y, labels, sample weights, groups, feature groups, blocks, target domain, or fold IDs. Only Resampler declares a required axis fit input. For this X-only comparison, never pass Y.

The native generic role ABI uses typed parameter setters `n4m_params_set_int`, `n4m_params_set_double`, `n4m_params_set_bool`, `n4m_params_set_enum`, `n4m_params_set_int_array`, and `n4m_params_set_double_array`, followed by `n4m_params_validate`. Estimators use `n4m_estimator_create`, `n4m_estimator_fit`, `n4m_estimator_transform`, `n4m_estimator_export_size`/`n4m_estimator_export_to_buffer`, `n4m_estimator_import_from_buffer`, and `n4m_estimator_destroy`. State export is the portable N4ME format. The installed JS/WASM facade exposes the corresponding `NativeEstimator` lifecycle; its per-class contracts are the same manifest entries.

## Preprocessing classes

All defaults and IDs in this table were checked against the installed package’s `estimatorRolesGenerated.d.ts` and `manifest()` output. “State” is the published manifest state-format label. Width effects are numerical API contracts where cited, or the package’s transform role and output-width behavior; the F4.3 adapter must still preserve and record returned dimensions and axes.

| Family / question | Published class (`methodId`) | Parameters and defaults | Fit/state and axis contract | Width / qualification notes |
|---|---|---|---|---|
| Scatter scaling | `SNV` (`preprocessing.scatter.snv`) | `with_mean=true`, `with_std=true`, `ddof=0` | Fit is X-only; state label `width`; no axis input. | Row-wise SNV; same number of rows/features. Pinned scatter header documents zero-SD rows remain unscaled, and constant rows map to exact zeros when centering is enabled. |
| Robust scatter scaling | `RNV` (`preprocessing.scatter.robust_snv`) | `with_center=true`, `with_scale=true`, `k=1.4826` (`k >= 0`) | Fit is X-only; state `width`; no axis input. | Same shape. Published class name is `RNV` (robust SNV), not `RobustSNV`. |
| Multiplicative scatter correction | `MSC` (`preprocessing.scatter.msc`) | No parameters | State `reference`; fit learns the reference from X. No axis input. | Same shape. Pinned native header describes the reference as the fit-matrix column mean and each spectrum’s intercept/slope regression against that reference; fit requires at least one row and two columns. Fit train only, then reuse for test. |
| Polynomial detrending | `Detrend` (`preprocessing.baselines.detrend`) | `polyorder=1` (`polyorder >= 0`) | State `width`; no axis input. | Same shape. Default is linear detrending. With no physical axis accepted, do not label this as a wavelength-scaled physical operation. |
| Per-column centering | `BaselineCenter` (`preprocessing.scaling.baseline`) | No parameters | State `column_mean`; fit learns means from X. No axis input. | Same shape. The class name is historical: pinned scaling header defines it as per-column mean centering, equivalent to `StandardScaler(with_std=False)`, not polynomial/spectroscopic baseline removal. Fit train only. |
| Savitzky–Golay smoothing | `SavitzkyGolay` (`preprocessing.derivatives.savitzky_golay`) | `window_length=5`, `polyorder=2`, `deriv=0`, `delta=1`, `mode="mirror"`, `cval=0`; modes `mirror|constant|nearest|wrap|interp` | State `width`; no axis input. | Same width. Header requires odd `window_length >= 1`, `0 <= polyorder < window_length`, and nonzero `delta`; the edge mode affects boundaries. `deriv=0` is smoothing. |
| Savitzky–Golay derivative 1 or 2 | Same `SavitzkyGolay` class | Set `deriv=1` or `deriv=2`; other defaults as above. | Same lifecycle, X-only; no axis input. | Same width. `delta` is a scalar sample spacing, not an axis vector. Unless a uniform axis spacing is supplied as `delta`, describe outputs as index-domain derivatives rather than physical wavelength derivatives. |
| First derivative | `FirstDerivative` (`preprocessing.derivatives.first_derivative`) | `delta=1`, `edge_order=2` (`edge_order` 1 or 2) | State `width`; no axis input. | Pinned smoothing header defines `np.gradient(X, delta, axis=1, edge_order)` and confirms output shape matches input. `delta` is scalar; do not imply support for nonuniform wavelength intervals. |
| Second derivative | `SecondDerivative` (`preprocessing.derivatives.second_derivative`) | `delta=1`, `edge_order=2` (`edge_order` 1 or 2) | State `width`; no axis input. | Pinned header defines two passes of `np.gradient` and shape-preserving output. Treat `delta` as scalar spacing; F4.3 should preserve provider failures for too-short/invalid inputs. |
| Gaussian smoothing / filter derivative | `Gaussian` (`preprocessing.smoothing.gaussian`) | `sigma=1`, `order=0`, `mode="reflect"`, `cval=0`, `truncate=4`; modes `reflect|constant|nearest|mirror|wrap` | State `width`; no axis input. | Same shape. Header requires `sigma > 0`, `order >= 0`, `truncate >= 0`. The API has no wavelength-axis input, so sigma is in feature-index units unless an upstream caller has verified regular spacing and documented it. |
| Normalize, default mode | `Normalize` (`preprocessing.scaling.normalize`) | `feature_min=-1`, `feature_max=1` | State `column_stats`; fit learns per-column L2 norms from X. No axis input. | A synthetic runtime probe confirmed the default pair divides each feature column by its norm over the fit rows, then reuses those norms on held-out rows. It preserves shape. |
| Normalize, custom range | Same `Normalize` class | Any custom `feature_min`/`feature_max` pair selects range-scaling mode. | State `column_stats`; fit learns column scaling from X. No axis input. | Synthetic probe with `(0,1)` confirmed fit-based per-column min/max scaling. Fit train only and reuse that state. Do not confuse this mode with the default fitted per-column L2 normalization. |
| Area normalization | `AreaNormalization` (`preprocessing.scatter.area_normalization`) | `method="sum"`; choices `sum|abs_sum|trapz` | State `width`; no axis input. | Same shape. The published API supplies no physical axis; `trapz` therefore has no route for a nonuniform axis in this class. Treat feature spacing and denominator edge cases as provider-defined until separately qualified. |
| Standard scaling | `StandardScale` (`preprocessing.scaling.standard_scale`) | `with_mean=true`, `with_std=true` | State `components`; fit learns feature statistics from X. No axis input. | Same shape. Pinned JS owner test uses population variance, includes a constant feature and large-offset case, transforms held-out rows, and checks state export/import replay. Fit train only. |
| Crop | `CropTransformer` (`preprocessing.resampling.crop`) | Required integer `start`, `end`; manifest permits `start >= 0`, `end >= -1` | State `width`; no axis input. | A synthetic runtime probe verified the interval is half-open `[start,end)`: `(1,3)` keeps input columns 1 and 2. Apply the same interval to the corresponding axis; report the cropped axis and new width. The manifest allows `end=-1`; its special meaning was not separately probed here. |
| Axis-aware resampling | `Resampler` (`preprocessing.resampling.resampler`) | Defaults: `target_wavelengths=[]`, `method="linear"` (`linear|nearest|cubic`), `crop_min=0`, `crop_max=0`, `use_crop=false`, `fill_value=0`, `bounds_error=false`, `extrapolate=false`, `tgt_min=0`, `tgt_step=1`, `tgt_n=0` | State `source_axis`; axis is required at fit and is the source axis. No Y input. | Output follows target wavelengths/grid, so feature count and axis can change. Record actual source/target axes, units, and output width. To claim wavelength resampling, provide the actual wavelength axis; positional grids are not evidence of physical wavelengths. Configuration requires an explicit, admissible target definition; do not silently infer one. |

### Similar names with different width contracts

The generated class `Derivate` (`preprocessing.smoothing.derivate`) is distinct from `FirstDerivative` and `SecondDerivative`. Its parameters are `order` and `delta`; the pinned header defines it as repeated finite differences with output width `input_cols - order`, requires fit to record the input width, and returns not-fitted/shape-mismatch errors when appropriate. It is not the requested same-width gradient derivative class. The `ResampleTransformer` (`preprocessing.resampling.resample_transformer`) is also separate from axis-aware `Resampler`: it takes a required `num_samples`, has no physical axis input, and changes the number of columns to that requested sample count. These are available APIs, but should not be conflated with wavelength-aware operations.

## Structure-comparison APIs actually present

Runtime export inspection and the installed `index.d.ts` found these Methods helpers:

| Export | What it computes | F4.3 boundary |
|---|---|---|
| `preflightAdjustedRandIndex(a, b)` | Adjusted Rand index for two aligned label arrays. Native function: `n4m_preflight_adjusted_rand_index(ctx, labels_a, labels_b, n, ari)`. | The Methods contract treats every label, including `-1`, as a regular class. If noise is excluded, apply one shared aligned non-noise mask before the call and report excluded counts. Provider documents NaN for `n < 2` and identical trivial partitions; preserve unavailable values rather than substituting a number. |
| `clusterJaccardMatrix(labelsA, labelsB, nClustersA, nClustersB)` | Row-major cluster-pair Jaccard matrix plus exact intersections and cluster sizes. Native function: `n4m_cluster_jaccard_matrix(...)`. | Negative labels are unassigned and belong to no cluster. Empty/empty cluster-pair Jaccard is NaN. This is a matrix, not a single global partition score; preserve cluster counts, unassigned/noise counts, and matching population. |
| `preflightNearestNeighbors(query, reference, k, queryGroups?, referenceGroups?)` | Per-query ranked neighbor indices and distances. | No Methods neighbor-overlap/retention score was found. A protocol may compute elementary set overlap from these returned index sets, but it must state the formula, common query rows, same exclusion rules, fixed k, and identity alignment in advance. Distances from different representations are not directly comparable. |
| `preflightPca(...)` | PCA diagnostics are available, but no paired-PCA subspace similarity function was found among published exports. | Do not claim coordinatewise PC agreement, PC1 correlation, or a Methods-provided subspace-invariance score. Compare only with a separately specified and qualified metric; otherwise show the separate PCA results without a direct stability score. |

No exported function matching PCA-subspace comparison or neighbor-overlap scoring was found in the installed runtime. `statsPcaMonitor` is a monitoring operation with a centroid-to-reference-subspace distance field; that field is not a paired-PCA comparison metric. It must not be repurposed as one.

## API versus qualification status

The APIs above are present in the pinned/published Methods surface. That alone does not qualify every requested configuration for F4.3. In particular, the installed owner test `bindings/js/test/run_estimator_roles.mjs` analytically exercises StandardScale fit/held-out transform/state replay, while `run_native_preprocessing_pipeline.mjs` tests a distinct, narrower `NativePreprocessingPipeline` API and its SNV→MSC held-out oracle. These upstream tests do not constitute F4.3’s complete per-class native/WASM parity or protocol qualification.

F4.3 should version a fixed panel and parameter set before inspecting comparative results; fit every learned transform on train only; carry original row identities and the corresponding output axis; preserve provider errors and undefined outputs; and record exact Methods version, ABI, parameters, fit population, output dimensions, and state fingerprint/provenance. A missing or unqualified method stays unavailable rather than being replaced with a hand-coded kernel. No preprocessing family should be selected because it gives a more favorable separation, cluster count, association, or test result.

## Evidence references

Installed published package, from the active F4.3 worktree:

- `bindings/wasm/node_modules/@nirs4all/methods/package.json` — npm package version and exports.
- `bindings/wasm/node_modules/@nirs4all/methods/dist/estimatorRoles.d.ts` — `NativeEstimator`, fit inputs, lifecycle, serialization, disposal.
- `bindings/wasm/node_modules/@nirs4all/methods/dist/estimatorRolesGenerated.d.ts` — class names, `methodId`s, parameters, defaults, fit-input notes.
- `bindings/wasm/node_modules/@nirs4all/methods/dist/index.d.ts` and `preflightDiagnostics.d.ts` — exported diagnostic functions/types.
- `bindings/wasm/node_modules/@nirs4all/methods/dist/index.js` and `.wasm` — runtime package loaded for version, ABI, class/function exports, and the noted synthetic probes.

Pinned upstream source at `fa8ff57603ec23bce95f73d52170285e8f3e2861`:

- `cpp/include/n4m/estimator.h` — typed parameter setters, generic fit/transform lifecycle, fit-input contract, N4ME state import/export.
- `cpp/include/n4m/transform/scatter.h` — SNV, RNV, MSC and area-normalization native contracts.
- `cpp/include/n4m/transform/baseline.h` — detrending parameter requirements.
- `cpp/include/n4m/transform/scaling.h` — Normalize modes and BaselineCenter fit semantics.
- `cpp/include/n4m/transform/smoothing.h` — finite difference, Savitzky–Golay and same-width gradient derivative contracts.
- `cpp/include/n4m/transform/resampling.h` — resampler, crop, and fixed-sample resampling lifecycles.
- `cpp/include/n4m/metrics.h` — PCA and comparison-kernel descriptions and exact ARI/Jaccard signatures.
- `bindings/js/test/run_estimator_roles.mjs` — StandardScale analytic and serialization test evidence.
- `bindings/js/test/run_native_preprocessing_pipeline.mjs` — scope and evidence for the separate narrow N4MP pipeline API.
