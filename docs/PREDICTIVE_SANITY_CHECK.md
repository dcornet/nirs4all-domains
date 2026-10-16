# Development-only nested PLS sanity check

Protocol `domains.predictive_sanity.v0.1`, executed on EcoSIS freeze-dried X and
LMA g/m² on 2026-10-16. Expectations and parameters were fixed in
[REPEATED_PILOT_PROTOCOL.md](REPEATED_PILOT_PROTOCOL.md). This is an exploratory
check of a spectral association, with no production model or retained-test score.

## Execution and ownership

The Rust `represent` command exports the admissible technical means and the
audited dependency-component IDs. The optional Python workflow removes test
rows before target-cell access, input fingerprints, folds or fitting. It refuses
reference-blocked inputs and duplicate physical samples. The primary development
population is 65 complete samples from 45 plots; retained X/Y cannot enter it.

Methods 1.3.6 provides PLSRegression, centering, artifact replay, summaries and
RMSE/MAE/R². DAG-ML 0.3.41 executes the inner CV, SELECT and REFIT using its
published native `run_cv_refit_methods_in_process` binding. The high-level strict
terminal-predict façade does not accept this grouped workflow; the audited native
binding is in its public export manifest and exercised in upstream tests. It is
pinned and invoked through a bounded adapter, without changes to DAG-ML.

Five identity-only outer group scopes are assembled in Python. In each scope,
DAG-ML receives only outer-train rows and three explicit inner group folds.
Native PLS centering of X/Y is fitted inside each fold, without autoscaling or
other spectral preprocessing. Components 1–5 are selected by inner RMSE; DAG-ML
refits the selected model on that outer-train scope. Its N4ME artifact is restored
through public `NativeEstimator.from_n4me()` and predicts only that outer
holdout. Inner selection scores are not independent predictive evidence.

The null predicts each outer training population's native Methods target mean.
Joined sample-keyed outer OOF predictions yield the reported native metrics.
Actual inner FIT_CV train-prediction lineage is checked against the declared
training IDs; outer/inner fold membership and artifact hashes are retained.
Scikit-learn 1.7.2 is installed solely for the Methods estimator façade's base
classes; no sklearn fitting, preprocessing, selection or scoring is used.
Python performs identity assembly and control flow, not chemometric algorithms.

## Actual results

| Model | OOF RMSE (g/m²) | OOF MAE (g/m²) | OOF R² |
|---|---:|---:|---:|
| Native Methods PLS, nested group selection | 110.867765 | 76.875527 | 0.396921 |
| Fold-local training mean | 146.993310 | 124.067333 | -0.060129 |

Selected component counts in outer-fold order are 5, 4, 3, 4, 5. The RMSE
improvement is 36.125545 g/m². This supports a moderate development-population
spectral association under the supplied plot identity assumptions. It does not
establish production calibrability, independent assay accuracy, causal spectral
effects, cross-region transfer or a guarantee for the retained test samples.
No alternative dataset, target or split was chosen to maximize performance.

Nineteen deterministic exploratory permutations exchange whole plot target
vectors between plots of equal sample cardinality; sample order within vectors
is explicit. Every permutation repeats the full nested workflow. Permuted RMSE
improvements range from -21.497167 to 6.330597 g/m²; none reaches 36.125545.
The Monte Carlo value is (1+0)/(19+1)=0.05, the smallest possible value with this
budget. Plot exchangeability within cardinality strata is assumed, and region/
species effects are not conditioned away. This coarse result is not a
confirmatory significance claim. Predictions, permutation results and lineage
remain in `results/ecosis-alpha4-release/predictive-sanity.json`; aggregate
hashes and results are committed in the qualification record.

## Controlled gates and limits

The real native adapter is exercised on a strong synthetic relation (RMSE below
1e-10, R² approximately 1) and on a deterministic independent target (PLS RMSE
1.0735 versus null 1.0316, R² approximately -0.145). The latter demonstrates no
improvement in that controlled case, not a universal guarantee over random
targets. Tests also check inner fit lineage, whole-group folds/permutations,
blocked references, and byte-identical probe results after changing all retained
X/Y. Synthetic values are test generation, not a fallback numerical backend.

The optional bridge emits a separate development probe; the canonical report's
`xy.nested_probe` remains unavailable with an explicit separate-workflow reason.
The full Preflight report is retained unchanged. Its local contrast is descriptive
and may have different eligibility from the exported mean-row probe. Missing
training targets would be excluded explicitly rather than imputed. Further
qualification should vary group folds on development only, improve biological/
reference metadata and quantify uncertainty before any performance commitment.
