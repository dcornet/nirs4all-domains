# F4.1 Methods API inventory

This is a read-only API inventory for the F4.1 design. The installed WASM
package is `@nirs4all/methods` 1.3.13; the owner source was checked at tag
[`v1.3.13`](https://github.com/GBeurier/nirs4all-methods/tree/v1.3.13), commit
[`fa8ff57603ec23bce95f73d52170285e8f3e2861`](https://github.com/GBeurier/nirs4all-methods/commit/fa8ff57603ec23bce95f73d52170285e8f3e2861).
The npm package exports all six JS functions in `dist/index.d.ts` and wraps
the public C ABI symbols. Source inspection and owner tests are evidence of
availability and intended behavior; they are not execution of this Domains
consumer.

## API matrix

| API and signature | Estimand and conventions | B=0 behavior | Native / WASM evidence | Owner tests and reference values | Remaining executable qualification |
|---|---|---|---|---|---|
| `preflightFactorAssociation(factorCodes, targets, categorical, nPermutations, seed)`; `readonly (number\|bigint)[]`, `Float64Array`, `boolean`, `number`, `number\|bigint` → `PreflightFactorAssociationResult` | With a continuous target: eta² = SSbetween/SStotal and one-way ANOVA F. With categorical targets: Cramér's V and Pearson chi-square without continuity correction. Result carries effect/statistic/df, factor and target level counts, log10 distinct-outcome upper bound, p, exceedance count, and executed count. Uses one unrestricted exchangeability block; Monte Carlo permutes target labels. | Computes descriptive eta² or V and the statistic; `pValue=NaN`, zero permutations executed. This is the categorical factor / continuous PCA score descriptive route when `categorical=false`. | Public ABI `n4m_preflight_factor_association` in `cpp/include/n4m/metrics.h:399-449`; JS/WASM wrapper `preflightFactorAssociation` in the pinned package `dist/preflightDiagnostics.js` and type in `dist/preflightDiagnostics.d.ts`. | `cpp/tests/test_preflight.cpp:637-653`: eta²=27/29, F=54, df=(1,4); B=0 retains eta² and returns NaN p, B=0. Categorical fixture at `654-659`: V=5/12, chi²=175/144. | Must verify Domains row correspondence and metadata before calling. Do not report a permutation p-value for B=0. For inference, exchangeability of the actual analysis units and an eligible unrestricted assignment design need separate qualification. |
| `statsCorrelationTest(x, y, method, nPermutations, seed)`; `Float64Array`, `Float64Array`, `"pearson"|"spearman"`, `number`, `number|bigint` → `StatsCorrelationTestResult` | Pearson r or Spearman rho between paired vectors. Spearman uses average ranks for ties. Result includes coefficient, distinct counts for x/y, log10 distinct-permutation upper bound, p, exceedance count and executed count. Monte Carlo test is two-sided and permutes y; compares `|r_perm| >= |r_observed| - sqrt(DBL_EPSILON)`. | Computes Pearson r or Spearman rho with no randomization; `pValue=NaN`, zero permutations executed. This is the descriptive correlation route. A constant vector gives an undefined coefficient and no permutations. | Public ABI `n4m_stats_correlation_test` in `metrics.h:461-488`; pinned JS/WASM wrapper and result type in package `dist/preflightDiagnostics.js` / `.d.ts`. | `test_preflight.cpp:702-719`: owner vectors `cx={1,2,3,4,5}`, `cy={2,4,5,4,5}`; Pearson `r=6/sqrt(60)`, Spearman `rho=7/sqrt(90)`, B=0 p is NaN. For B=999, seed 17, Pearson b=133 and p=134/1000; Spearman b=201. Constant-vector NaN behavior at `742-746`; tied-rank SciPy references at `720-728`. | Signed Pearson r depends on the chosen PC score sign/orientation. Freeze or record the PC basis orientation before comparing signed coefficients. Two-sided permutation evidence is sign invariant, but B=0 itself is descriptive only. Paired lengths do not prove matching row identities/order. |
| `statsFactorAssociationExact(factorCodes, targets, categorical, maxArrangements)`; factor codes, `Float64Array`, `boolean`, `number` → `StatsExactPermutationResult` | Exact distribution of eta² or Cramér's V² over distinct arrangements. Returns arrangement count N, observed-tail exact p, minimum attainable p, and maximum statistic. Each distinct multiset arrangement is equally weighted; the side with fewer arrangements is enumerated. | Not a B=0 route: enumerates a bounded exact null distribution and returns inferential quantities. | Public ABI `n4m_stats_factor_association_exact` in `metrics.h:490-509`; pinned JS/WASM wrapper and shared result type in package dist. | `test_preflight.cpp:770-786`: exact categorical 4+4 fixture N=70, p=min p=1/35, max=1; continuous n=6 fixture N=20, p=min p=.1, max eta²=27/29; one-factor-level fixture N=1 with undefined p/max. There is no explicit owner 2+2 continuous exact golden in this test file; the aligned `{a,a,b,b}` two-level case has N=6 and tail 2/6 by the documented arrangement definition, but treat it as a derived value rather than a pinned owner golden. | Only use if an exchangeability design is independently justified and the arrangement/work cap is met. It is not needed for descriptive eta². The exact API does not establish validity of exchangeability. |
| `statsCorrelationExact(x, y, method, maxArrangements)`; `Float64Array`, `Float64Array`, Pearson/Spearman method, `number` → `StatsExactPermutationResult` | Exact distribution of `|r|` over distinct arrangements; returns N, exact p, minimum attainable p, and maximum `|r|`. Tied values reduce the number of distinct arrangements. | Enumerates a bounded exact null; not descriptive-only. | Public ABI `n4m_stats_correlation_exact` in `metrics.h:490-512`; pinned JS/WASM wrapper and shared result type in package dist. | `test_preflight.cpp:783-788`: n=5 Pearson N=30, p=2/15, minimum p=1/15, max |r|≈0.9036961; Spearman p=.2, minimum p=1/15, max≈0.9486833. No n=4 perfect-correlation ± pair reference is explicitly pinned there; for four unique values, the two perfect arrangements among 24 imply 2/24 under the documented rule, but that is a derived value, not an owner fixture. | Requires justified exchangeability and bounded enumeration; it does not supply a qualified general-purpose p-value without that design. |
| `preflightHolmAdjust(pValues)`; `Float64Array` → `Float64Array` | Holm step-down adjusted p-values for one prespecified hypothesis family; stable ascending order, cumulative maximum, cap at 1. Inputs in [0,1]. | Not applicable. | Public ABI `n4m_preflight_holm_adjust` in `metrics.h:451-457`; pinned JS/WASM export and wrapper in package dist. | `test_preflight.cpp:685-698`: R `p.adjust("holm")` reference for `[.01,.04,.03,.005]` is `[.03,.06,.06,.02]`; tied and capped fixtures also covered. | Define the hypothesis family before examining results. The adjustment does not make unqualified component tests or post-hoc selection valid. |
| `statsBhAdjust(pValues)`; `Float64Array` → `Float64Array` | Benjamini–Hochberg step-up adjusted p-values for one family: reverse cumulative minimum of `m*p_(j)/j`, capped at 1. Source documents FDR control under independence or positive regression dependence. | Not applicable. | Public ABI `n4m_stats_bh_adjust` in `metrics.h:514-522`; pinned JS/WASM export and wrapper in package dist. | `test_preflight.cpp:986 onward`: statsmodels/SciPy reference `[.02,.04,.04,.02]` for `[.01,.04,.03,.005]`, with tied/capped and scaled-normal-p cases. | Inventoried, but not qualified for this protocol: the dependence assumptions and prespecified family are not established. Use neither as a default nor as a substitute for the selected multiplicity policy. |

### Shared input and numerical constraints

The association and correlation kernels require finite inputs, at least two
rows, `nPermutations` in `[0, 1,000,000]`, and a work estimate no larger than
250 million operations. Their data domain D requires each nonzero absolute
value in `[2^-256, 2^256]` and within-array max/min nonzero magnitude at most
`2^32`; exact zeros are permitted. Categorical target values for factor
association are integer labels exactly representable as doubles (`|code| <=
2^53-1`) and are not checked against the continuous-value domain. Exact
enumeration accepts a maximum arrangement budget from 1 through 10,000,000
and refuses larger arrangement/work requirements with `N4M_ERR_UNSUPPORTED`.
Holm and BH require a nonempty family and p-values in `[0,1]`; nonzero
subnormal p-values below `2^-1022` are unsupported.

Factor codes are arbitrary integer labels; their numeric order has no
interpretation. A singleton per factor level is not an unavailable effect:
with at least two levels and distinct continuous targets, eta² is saturated
at 1, while F is undefined when `n == levels`. The owner test's
`flat_level={5,5,7}` over two levels checks eta²=1 and F=NaN
(`test_preflight.cpp:934-937`). F is also NaN when all within-level variance
is zero. Eta² is undefined when there are fewer than two factor levels or
fewer than two target values; the one-level owner fixtures check NaN effect
and zero permutations (`666-672`). Correlation is undefined when either
vector is constant. These are distinct from provider errors.

For PCA scores, changing a PC sign flips signed Pearson r; preserve and record
the component orientation if reporting signed values. Eta² and the two-sided
`|r|` tests are sign invariant. Spearman ties use average ranks, and exact
enumeration counts unique arrangements rather than duplicate permutations.
All APIs accept paired vectors only; they receive no row identities, axes,
groups or split metadata. Domains must establish the content-bound pairing and
the scientific exchangeability unit separately.

## Executable qualification status

The inventory itself was read-only. The subsequent Domains integration executes
the following public owners through actual native/WASM paths; the content-bound
receipts, exact commits and platform results are in
[F4_1_VALIDATION.md](F4_1_VALIDATION.md). Native transport is isolated in
`crates/nirs4all-domains/src/factor_methods.rs`; the historical `methods.rs`
transport is unchanged. Availability alone is still not qualification.

| Domains operation | Public Methods JS API | Public native symbol | Executed scope |
| --- | --- | --- | --- |
| Categorical descriptor | `preflightFactorAssociation` | `n4m_preflight_factor_association` | continuous PC target, B=0, seed=0 |
| Continuous descriptor | `statsCorrelationTest` | `n4m_stats_correlation_test` | explicit Pearson/Spearman, B=0, seed=0 |
| Exact categorical | `statsFactorAssociationExact` | `n4m_stats_factor_association_exact` | conditional eligible synthetic units/family |
| Exact continuous | `statsCorrelationExact` | `n4m_stats_correlation_exact` | conditional eligible synthetic units/family |
| Complete-family adjustment | `preflightHolmAdjust` | `n4m_preflight_holm_adjust` | prospectively declared factor × resolved-PC family |
| Continuous M range | `preflightSummary` | `n4m_preflight_summary_compute` | same admitted nonmissing M population |

`statsBhAdjust` remains inventoried only: it is not executed or qualified by
F4.1. No Cramér-V target analysis or Monte Carlo/constrained permutations are
silently substituted. Successful synthetic qualification does not validate a
real dataset's exchangeability, physical identity, causal mechanism or calibration.

For display-only target ranges, the existing `preflightSummary` public API is
also available: `n4m_preflight_summary_compute(ctx, values, valid_mask, n,
out_eight)` returns `[count,min,max,mean,sample SD,q25,median,q75]`.
The pinned header defines this order in `cpp/include/n4m/metrics.h:124-136`;
owner test `cpp/tests/test_preflight.cpp:590-593` checks count 4 and summary
values including quartiles. This is the existing summary kernel, not a new
range calculation in Domains.
