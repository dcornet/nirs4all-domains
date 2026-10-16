# Method reuse matrix

Snapshot audited on 2026-10-16. Commits: Methods
`131a15a6bbf73a8ab941c7b3fb81b21f6b71b059`, Preflight
`2f0574af0d04a9dbb0f64a978e9f2995ccf1a05d`, Datasets
`e68d1befb6cb8245799e83d4b4e4c41e66287689`.
See [machine-readable evidence](audit/upstreams.json).

**Correction to the initial availability map:** Methods GitHub release v1.3.6
was published on 2026-10-13. The Windows PyPI wheel 1.3.6 loads and reports
`1.3.6+abi.2.19.0`. Its new symbols are exported. `docs/dev/hdbscan.md` still says
unreleased; `CHANGELOG.md` has both the released heading and a stale prepared-1.3.5
sentence. Publication does not imply that Preflight's Rust provider exposes the
new functions or that Domains has qualified their protocols.

Common evidence paths below are relative to the named upstream repository. Native
test references were inspected; upstream test suites were **not rerun**. Local
execution refers only to tests described in VALIDATION.md.

| Need | Code and public interface verified | Minimum / publication / binding | Scientific evidence inspected; local qualification | Decision |
|---|---|---|---|---|
| Integrity and identities | Preflight `crates/nirs4all-preflight-core/src/lib.rs::validate_input`, facade `analyze` | Rust crate =0.1.0-alpha.1 published | Linked physical/individual components and reference-group checks; local adversarial policy tests | reuse |
| Exact train/test spectral duplicates | Preflight facade `src/lib.rs`, `integrity.cross_partition_exact_duplicate_pairs` | Same alpha; no Methods needed | Exact bit normalization, counts across declared physical identities; local 8-pair analytical fixture | reuse |
| Technical repeats / ICC(1,1) | Methods `cpp/include/n4m/metrics.h::n4m_preflight_repeatability_compute`; Preflight provider | ABI >=2.18, introduced 1.3.5 npm; present 1.3.6 native wheel; Rust provider available | Native acquisitions retained; alpha.3 exercises pooled SD through Preflight; no full ICC parity rerun | reuse |
| Homogeneous comparison representation | Preflight facade private physical/instrument/campaign averaging inspected; public Methods `SummaryRequest` mean | Published facade does not export its matrix/membership; existing mean primitive sufficient | Alpha.3 known/mixed/unknown/biological/context/partition/reference guards, analytical means and physical-sample weights | new Domains task policy; public Preflight representation seam proposed |
| Centered PCA and full moments | `n4m_preflight_pca_compute`; Preflight `PcaRequest/PcaDiagnostics` | ABI >=2.18; wheel 1.3.6; Rust provider loses loadings | Upstream hand-computed/truncated/strided tests; local rank-one trace=36, effective dimension=1, projection and no-refit tests | reuse |
| Train PCA transform of test | C ABI retains k x p loadings; no loadings in Rust `PcaDiagnostics` | Same ABI; local owning adapter calls public ABI | Local orthogonal shift catches residual outside retained subspace | new local protocol; upstream extension for retaining fitted state |
| Y summaries / quartiles | `n4m_preflight_summary_compute`; Rust `SummaryRequest` | ABI >=2.18; available through provider | Upstream type-7 and extreme finite tests; local target access/shift tests | reuse |
| Independent spectral neighbors | `n4m_preflight_nearest_neighbors`; Rust provider | ABI >=2.18, public and runtime exported | Upstream group exclusion/ties/extremes; local train-only threshold and grouped admissibility guards | reuse |
| Local descriptive X-Y contrast | `n4m_preflight_local_contrast`; Preflight `local.descriptive` | ABI >=2.18, Rust provider available | Upstream continuous/categorical tests; no calibrated inference or local predictability claim | reuse |
| HDBSCAN | `catalog/methods/diagnostics.hdbscan.yaml`, `n4m_cluster_hdbscan` | ABI >=2.19; wheel 1.3.6 symbol verified; Python raw declarations + JS wrapper; no Preflight Rust provider method | `docs/dev/hdbscan.md`, `cpp/tests/test_hdbscan.cpp`, `parity/fixtures/hdbscan_v1.json`; tie/order-sensitive stable-MST reference; not locally qualified | deferred; reuse kernel later |
| ARI | `n4m_preflight_adjusted_rand_index` | ABI >=2.19; native symbol + Python raw declaration + JS wrapper; absent Rust provider | Same frozen cluster reference gate; no Domains stability protocol yet | deferred; reuse |
| SG noise proxy | `n4m_preflight_noise_proxy_compute` | ABI >=2.19; native symbol + Python raw declaration + JS wrapper; absent Rust provider | Upstream masked/interior residual-gain tests; not SNR; not locally qualified | deferred; reuse |
| Near duplicates | `n4m_preflight_pairs_within_tolerance` | ABI >=2.19; native symbol + raw declarations/JS; absent Rust provider | RMS feature tolerance, bounded pair list and exact totals; upstream tests, no local tolerance calibration | deferred; reuse |
| Factor-target association / Holm | `n4m_preflight_factor_association`, `n4m_preflight_holm_adjust` | ABI >=2.19; native symbols + Python raw declarations + JS; absent Rust provider | Eta-squared/Cramer's V and unrestricted exchangeable-unit permutations; NumPy/SciPy goldens inspected; no conditional effect or restricted permutation support | deferred; reuse marginal kernels |
| SNV / MSC / SG / derivatives | `cpp/include/n4m/transform/`, catalog preprocessing entries | Catalog historical since_abi 1.0.0 for SNV/MSC/SG; current ABI 2 symbols; 1.3.6 published; Python typed transformers | Native/binding parity suites exist; no sensitivity chain qualified locally | reuse later; canonical MVP only centers |
| PLS / PCR / Ridge | `cpp/include/n4m/`, catalog `models.*`, typed estimator bindings | Catalog since_abi PLSRegression 2.13.0 (role surface), PCR 1.21.0, Ridge 1.16.0 (historical); current ABI 2.19 wheel published | Alpha.4 executes PLS through DAG-ML inner CV/select/refit and Methods artifact replay; synthetic signal/null and nested lineage gates, real development OOF | reuse PLS; PCR/Ridge protocols deferred |
| AOM-PLS | AOM public C ABI/catalog; target-dependent selection | Catalog historical since_abi 1.0.0; current ABI 2 names, 1.3.6 published; per-operator minima not fully audited | Existing model/selection parity paths; leakage-safe full protocol not locally qualified | deferred |
| Ward / GMM / Hopkins | No matching declared method/API found in audited catalog and C headers | Availability not confirmed; no binding claim | No local qualification | upstream extension (Methods), only after broader audit |
| Cluster stability and test membership | HDBSCAN + ARI kernels available; no complete task protocol | Rust adaptation missing; prediction of held-out HDBSCAN membership not assumed | Must refit train subsamples, compare common identities/noise, canonical order | new local protocol, deferred |
| X coverage, center and dispersion | Methods PCA, summary, neighbors | ABI >=2.18; local Rust protocol | Analytical centroid/variance ratios and orthogonal residual tests; heuristic coverage only | new local protocol, implemented |
| Y coverage and test shift | Preflight train distributions; optional Methods test summary | ABI >=2.18 for numeric summary | Pre-training forbids Y_test; post access declared; no calibrated target-shift test | reuse + new local protocol |
| MMD / energy / C2ST | No matching generic public APIs confirmed in catalog/C headers | Not declared available | Kernel bandwidth/permutation and grouped classifier validation unqualified | upstream extension (Methods kernels), Domains protocol deferred |
| PERMANOVA / PERMDISP / partitioning | No matching public API confirmed | Not declared available | Confounded design rank and exchangeability protocols missing | upstream extension (Methods), intrinsic Preflight protocol + domain interpretation |
| Detailed local contradictions | Existing neighbor/local-contrast primitives | Partial only; reference precision protocol missing | Must separate spectral similarity, lab uncertainty and non-identifiability | upstream extension (Preflight); Domains compares domains |
| Spectral graph metrics / Y mixtures | No complete public protocol confirmed | No binding/publication claim | Sensitivity to sample count, spectral redundancy and thresholds unresolved | deferred; generic kernels in Methods |

Audit also read Preflight README, SPECIFICATION, ROADMAP, REUSE_METHODS and facade
source; Datasets README, ONBOARDING, schema, catalog/cards, dataset.py and access.py.
Related IO/Formats/Core/DAG-ML README seams were inspected, not their full numerical
or execution APIs. Future nested-validation integration requires a focused public
DAG API audit rather than assuming its README guarantees are already integrated.

Alpha.3 also inspected Datasets `qualify/metrics.py`: `spectral_profile`,
`pca_outlier_metrics`, `repeatability_metrics`, RMS/SAM, noise and artifact
heuristics. None were copied. Local DLL lookup again succeeds for PCA, summary,
neighbors, repeatability, HDBSCAN, noise proxy and tolerance pairs. The native
suite executes the first four; symbol lookup alone does not qualify the others.
No new generic numerical primitive is required by this sprint.

## Alpha.4 executable additions

| Need | Public surface / exact version | Actual local evidence | Decision |
|---|---|---|---|
| Large complete-axis PCA | `n4m_decomposition_flexible_pca_{create,fit,transform,output_cols,destroy}` in `cpp/include/n4m/decomposition.h`; Methods 1.3.6 / ABI 2.19 | Small analytical projection; 390×2151 controlled coverage with moments unavailable; full real native/mean train/test and 100 refits each | Reuse fitted state; independent optional full moments |
| Within-ID dispersion | Preflight `MethodsProvider::repeatability` / existing ABI | Real train native acquisitions retained under both views; 2151 pooled SDs | Reuse; subtype remains unspecified |
| Nested PLS sanity | DAG-ML 0.3.41 `crates/dag-ml-py/src/lib.rs` public native `run_cv_refit_methods_in_process`; public export manifest and official tests inspected | Five outer scopes / three inner folds, native lineage checked, 19 whole-group permutations; no upstream suite rerun | Bounded optional integration, separate report |
| Selected native prediction / scores | Methods `NativeEstimator.from_n4me`, `.predict`, `n4m.metrics.scoring` and public summary ABI | Native OOF RMSE/MAE/R² and fold-local null; retained X/Y mutation invariance | Reuse; no sklearn numerical backend |

DAG-ML audited commit: `c6b52979745397ae4e8662580df79341f0378d28`.
Its older README version is not the installed wheel version. Source/binding and
actual execution evidence supersede the earlier README-only audit for this
bounded PLS workflow. HDBSCAN/ARI remain available kernels, not qualified local
clustering protocols. The large exact rank-one FlexiblePCA failure and getter
requests are recorded in UPSTREAM_DEPENDENCIES.md.
