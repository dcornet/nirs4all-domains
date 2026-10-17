# Future outcomes — domains.alpha12.future_outcomes.v0.1

Additive operational specification of the hypothesis register, before any new
supervised response is generated. Alpha.12 does not evaluate these outcomes.

For the same target/unit and matched evaluation IDs, define degradation as
`D_RMSE = RMSE_stress - RMSE_reference`. Define null-relative skill as
`S = 1 - RMSE / RMSE_null`, with the null fitted from the corresponding training
reference values only. `D_skill = S_stress - S_reference`; negative values
denote deterioration. A zero/undefined null denominator makes skill unavailable.
For two prespecified estimators, the interaction is
`D_RMSE_estimator1 - D_RMSE_estimator2` on the same matched evaluation population.
Do not pool raw RMSE across different target units.

Control exact training size and declared dependency support, original source and
study relationships, target-range extrapolation, model family and preprocessing.
Size matching uses whole admissible components, never rowwise thinning of known
repeats. All preprocessing and tuning belong inside the training scope. Retained
test outcomes cannot choose structural descriptors, splits or hyperparameters.
An X-aware structural split is explicitly transductive and cannot masquerade as
prospective validation. No held-out HDBSCAN assignment is assumed available.

Freeze descriptor extraction from the alpha.12 matrix identity, outcome
definitions, statistical analysis, study-level discovery/confirmation membership
and stopping rules before examining confirmatory responses. Repeated designs
are sensitivity measurements within a task; they are not independent study
replications. EcoSIS/CA2023, Perten and litter remain exploratory because their
responses have already informed interpretation. Unknown study overlap and
biological closure prevent a current independent-study power claim.

Retain stable-structure/good-generalization and weak-structure/poor-generalization
cases as potential falsification. A useful structural predictor need not identify
a causal shortcut. TabPFN and additional estimator studies remain separate later
campaigns with their own source, checkpoint, rights, split and resource admission.
