# Structural predictive baselines — frozen alpha.6 design

Protocol `domains.structural_dependence.v0.1`, frozen 2026-10-17 before new
prediction execution. Extend `predictive.py`; DAG-ML 0.3.41 owns inner CV,
selection and refit, Methods 1.3.6 owns PLS, summaries and scoring. No new
optimizer, regression, metric or fold engine is introduced.

Use the original identity-only outer group folds, seed 17, five outer / three
inner folds and PLS components 1–5 for EcoSIS: exactly 65 physical means / 45
plots, LMA g/m², 2151 unchanged bands. The alpha.4 original PLS experiment must
reproduce its folds, OOF predictions and metrics. Test rows are removed before
target inspection, fingerprints, association, folds or fitting. Caller-supplied
folds must cover every development ID exactly once and keep components whole.

Four predictions share the same outer validation IDs: outer-train global mean;
outer-train factor-level mean (missing/unseen levels fall back to that global
mean); original nested spectral PLS; group baseline plus residual-target PLS.
No shrinkage or baseline hyperparameter selection. Each record retains its
factor, seen/fallback source, fold, component, original Y and four predictions.
Methods RMSE/MAE/R² use the same sample weights (one physical vote). Improvement
is RMSE(reference) minus RMSE(candidate), positive means improvement.

Residual fitting must recompute group/global means in **each inner training
population**, subtract them from that training Y, and reconstruct original-unit
validation predictions with those same means. DAG-ML selects by original-unit
validation RMSE, then recomputes the baseline and residuals on outer train for
REFIT. The callback-capable public DAG scheduler is audited as a possible route;
the callback-free static input API cannot represent changing Y by fold. Only
native Methods PLS may execute in such a callback. Export/replay N4ME and retain
training IDs, baseline means, residual fingerprints, selected components and
artifact hashes. If this route fails leakage gates, experiment 3 stays explicitly
unavailable with the exact missing contract documented; no unsafe substitute.

The exact-zero training-residual case requires no correction fit. Methods
explicitly refuses constant residual Y; Domains retains zero correction, records
`exact_zero_training_residual_no_pls_fit`, zero components and a JSON lineage
artifact distinct from N4ME. This is a degenerate group baseline, not proof of a
PLS fit. Nonzero residual controls must execute native PLS and N4ME replay.
Controlled six-feature linear fixtures use the full component grid 1–6 so the
stated analytical 1e-9 tolerance applies; EcoSIS retains the alpha.4 grid 1–5.

Conditional seen-level metrics require >=20 samples / >=10 components and at
least two levels supported by three components each. Label their denominator
explicitly. Original-unit R² and residual-target R² have different denominators.
All-unseen prediction is a fallback diagnostic and cannot identify group
mediation. Neither residualization nor a gain proves chemistry or causality.

Paired OOF uncertainty: 200 whole-component replacement draws, seed 17,
nearest-rank 95% endpoints, >=100 successful / >=10 original components. Freeze
OOF rows before resampling, preserve paired predictions and multiplicity, retain
failures without redraw. This conditions on fitted CV; no model-refit uncertainty.

Controls before real interpretation: A group-only X/Y offsets (high association,
competitive group means, low extra spectral skill); B continuous trait independent
of factor (weak group skill, spectral/residual gains); C mixed offsets and trait
(distinct group and residual contributions); D structured X with independent Y
(no reproducible gains in the frozen control); E unseen levels (training-global
fallback only); F repeats/shared/contradictory references (physical weighting and
scoped blocks); G nearly unique levels (saturated association, unseen OOF,
nonidentifiability); H retained Y/X mutation, row reorder, permuted identity maps,
and illegal component-splitting folds. All computed development results must be
identical under retained-data mutation. Analytical perfect predictions use
RMSE tolerance 1e-9; arbitrary real differences are reported without an invented
significance threshold. Cluster-derived prediction remains unavailable.
