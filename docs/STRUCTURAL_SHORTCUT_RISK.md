# Structural shortcut risk research programme

Alpha.8 packages task-specific evidence for estimator-independent benchmark
selection. Missing clusters/metadata, successful PLS or powerless permutations
cannot certify low structural dependence. EcoSIS is a structure-sensitive
challenge with unresolved within-genus intervention power; the low-dependence
candidate suite is empty. Rights/identities block new real contrasts. Registry
purpose is separate from computed/exploratory/unavailable evidence status; later
multi-estimator validation remains necessary. See BENCHMARK_QUALIFICATION_MODEL.md.

Alpha.7 executes experiments 4–5 through `domains.split_stress.v0.1` while
preserving alpha.6 evidence. True genus holdout, conditional size matching and
global training interventions are computed on EcoSIS; within-genus intervention
remains unavailable under the frozen exchangeability/power gates. Synthetic
cases qualify scope-local interventions and their generating-mechanism response.
See SPLIT_STRESS_REAL_DATA_PILOT.md. Evidence is compatible with structural
sensitivity, with sample-size/range/composition alternatives explicitly retained;
no causal chemical fraction or global shortcut score follows.

Alpha.6 now implements experiments 1–3 for documented metadata in separate
`domains.structural_dependence.v0.1` reports. See
GROUP_TARGET_ASSOCIATION_PROTOCOL.md, STRUCTURAL_PREDICTIVE_BASELINES.md and
STRUCTURAL_DEPENDENCE_REAL_DATA_PILOT.md for qualified scopes and actual results.
This historical alpha.5 plan continues to specify experiments 4–5; alpha.7's
bounded design is in SPLIT_STRESS_ALPHA7_PROTOCOL.md. No causal risk estimator
or cluster-derived held-out predictor is implemented.

Specification `domains.structural_dependence.plan.v0.1`, alpha.5. This is a
research protocol, not an implemented risk estimator. It asks how predictive
gain changes when recognizable groups, neighborhoods and split-specific
associations are controlled or withheld. Group information can carry genuine
chemistry. Structural dependence is not proof of a spurious mechanism or cause.

## Availability and identities

Alpha.5 characterizes train X partitions and component-resampled stability with
native PCA–HDBSCAN–ARI. Y never selects clusters or parameters. The separate
alpha.4 grouped PLS workflow measures development OOF prediction. These results
together do not measure group-mediated prediction or within-group predictive
skill; `shortcut_risk_evidence` remains unavailable.

Distinguish indivisible physical/reference dependency components, documented
metadata factor levels, and spectrally discovered groups. Plots remain indivisible
even under a design called random sample split. Biological/assay independence
and reference precision may remain unknown.

| Experiment | Alpha.5 status | Numerical owner / prerequisite |
|---|---|---|
| Unsupervised structural stability | Implemented in separate report | Methods PCA/HDBSCAN/ARI; controlled gates |
| 1. Metadata group–Y decomposition | Specified, not executed | Methods factor association and summaries; reference guards |
| 2. Group-only prediction baseline | Planned | Fold-local native means and existing DAG-ML workflow |
| 3. Within-group predictive skill | Planned | Fold-local residualization and native OOF replay |
| 4. Split sensitivity | Planned | Comparable group-safe designs and nested selection |
| 5. Training-target interventions | Planned | Restricted reference-unit permutations and complete fold-local reruns |

The 19 historical alpha.4 permutations evaluate a permuted development-outcome
experiment. They are not relabeled as the original-outcome training interventions
below and do not supply a causal shortcut conclusion.

## Experiment 1 — between-group versus within-group Y variation

Use authorized development numeric Y, one eligible outcome per physical/reference
analysis unit, without independent duplicate votes for shared assays. Prespecify
factor source, units, conditioning population, group sizes, missing values and
reference exclusions. Report `SS_total = SS_between + SS_within` and
`eta_squared = SS_between / SS_total`.

Audited Methods 1.3.6 / ABI 2.19 `n4m_preflight_factor_association`, declared in
`metrics.h` and implemented in `c_api_preflight.cpp`, returns eta², ANOVA F,
degrees of freedom and undefined states. Its native permutations use a single
unrestricted exchangeable block, not a restricted plot/reference design. Use
zero permutations until that exchangeability is justified. Native summary
variance gives SS_total=(n−1)·variance; native eta² gives SS_between=eta²·SS_total
and SS_within by difference. This assembly does not copy the association kernel.

Report group means through native summaries. Constant Y, one factor level,
singleton saturation and absent residual degrees of freedom are explicitly
undefined/insufficient. Bootstrap whole verified dependency components, preserving
reference links; report its conditioning and uncertainty. Marginal association
does not imply conditional attribution or predictive reliance. EcoSIS has 45
development plot levels among 65 samples: high eta² for a near-saturated factor
would not establish transferable plot prediction.

## Experiment 2 — group-only baseline

Reuse the existing native nested predictive infrastructure and identical outer
OOF populations for the fold-local global mean, group-only mean and spectral
PLS/PCR. Group means use only that fold's train outcomes. Unknown/unseen/missing
levels use its global training mean; report fallback IDs/counts. Any smoothing
or tuning belongs inside inner folds. Factors must be available at deployment.

Under plot holdout, a plot-ID-only baseline always falls back. Broader documented
factors need enough repeated levels within training scopes. Never treat full-data
discovered clusters as out-of-fold labels: rebuild PCA/HDBSCAN inside each fold
and use a separately qualified public held-out assignment API. No such HDBSCAN
API was found in the current Methods surface. A cluster-derived predictive
baseline remains unavailable; nearest-centroid labels are not HDBSCAN prediction.

## Experiment 3 — within-group predictive skill

Estimate group means inside each relevant training fold and learn deviations
using the existing native spectral model/selection. Seen validation levels use
training-estimated offsets; unseen levels use the frozen global fallback. Never
subtract a true held-out group mean from held-out Y. Evaluate on original held-out
outcomes against the matching group-only baseline. Paired OOF RMSE/MAE/R² and
residual-target skill require their own populations; original and residual R²
are not interchangeable. No causal chemical proportion follows.

## Experiment 4 — split sensitivity

Prespecify random dependency-component splits, factor-group holdout and feasible
leave-one-factor-group-out designs. Preserve physical, reference and plot links.
When components span factor levels, keep their connected union or report the
design infeasible. Compare the same development population/target and bounded
model grid where possible. Retain train/test sizes, Y ranges, unseen levels and
spectral extrapolation. Optional Y-range matching is declared development-only
design, never retained-test optimization. Worse group-holdout performance can
reflect smaller train size, extrapolation or biological shifts as well as group
reliance; it is not automatically leakage.

## Experiment 5 — two training-target negative controls

Within every outer and inner training scope, global permutation destroys overall
training X–Y correspondence where reference-unit exchangeability is justified.
Within-factor permutation preserves training group distributions while disrupting
fine within-group correspondence. Shared assays, singleton groups and restricted
blocks can make an intervention invalid or powerless; report admissible
permutations and explicit reasons rather than assuming exchangeability.

Rerun fold-local means, preprocessing, hyperparameter selection and refit for
every intervention. Evaluate each outer model on original, nonpermuted development
holdout outcomes. Those outcomes cannot enter training permutations, residualization
or inner selection. Inner validation labels cannot influence inner fits. Report
paired OOF gain/loss versus unchanged spectral, group-only and null baselines,
component-resampled uncertainty and attainable Monte Carlo resolution. Retained
gain is not a causal percentage of chemical information.

## Controlled gates and alpha.6 order

Start alpha.6 with experiment 1 on documented metadata: analytical SS identity,
eta²=0/1, constant Y, singleton groups, missing/shared/censored references,
whole-component uncertainty and inaccessible test Y. Then implement experiment 2
with exact fold-local seen/unseen means and native DAG-ML lineage. A synthetic
between-group-only relation should be captured by the group baseline; independent
Y should not improve reliably. Add experiment 3 using known within-group,
between-group-only and independent controls, with held-out mutation tests.

Only afterwards qualify split sensitivity and both interventions on known
nuisance-only, within-group and mixed mechanisms. Keep real retained labels
sealed. No new regression engine, universal shortcut probability, causal
confounding claim or calibrability ranking is an acceptance target. Alpha.5
preserves the qualified PLS workflow and implements none of these interventions.
