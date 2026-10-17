# Alpha.7 proposed split stress and negative interventions

Design only: this programme was not executed in alpha.6. Retain EcoSIS's frozen
65 means / 45 plot components, LMA g/m², 2151 bands and alpha.6 qualified factor
definitions. Retained test remains sealed. Keep null, group-only, original PLS
and group+residual predictions on matched development validation identities.
Methods/DAG-ML continue to own numerical fitting and inner selection.

1. Freeze identity-only reference group folds (alpha.4/6), five additional
   prespecified seeds (31, 47, 61, 79, 97), and true explanatory-factor holdout
   where feasible. Join whole components connected across factor levels before
   holdout; refuse designs whose resulting units leave fewer than three inner
   train components. Report unavailable factors rather than split physical or
   reference links. Do not call ordinary plot folds genus holdout.
2. Match training sizes: for each eligible true factor holdout, construct
   component-preserving subsamples of reference-fold train with matched sample
   counts where exact matching is feasible. Otherwise retain the size difference
   explicitly. Report train samples/components, unique levels, Y ranges and
   original-unit X coverage for each scope. A performance drop can reflect fewer
   training examples, unseen levels, Y extrapolation or a changed biological
   population. Keep those explanations distinct.
3. Prespecify development-only Y-range overlap sensitivity as a separate
   restricted-population experiment. Never tune splits on retained targets or
   silently delete extrapolating validation outcomes. Its denominator differs
   from the original all-development experiment.
4. For every outer/inner training scope, qualify two target interventions:
   global permutation of admissible reference-unit target blocks, and
   within-factor permutation of admissible blocks. Preserve shared references,
   cardinality and indivisible component constraints; quantify singleton and
   unswappable blocks. Do not treat individual acquisitions as independent
   outcomes. A restricted exchangeability rule must be defensible and frozen
   for each factor; otherwise that intervention is unavailable.
5. Recompute training group means, residualization, PLS centering, inner
   selection and outer refit for every intervention. Inner validation Y remains
   original for scoring, outer validation Y remains original for evaluation,
   and neither enters any training permutation or fitted statistic. Within-group
   intervention should preserve between-group Y structure while destroying
   fine within-group correspondence; global intervention destroys both where
   its exchangeability assumptions hold. These differ from alpha.4's experiment
   scoring permuted outcomes.
6. Use 19 prespecified intervention draws initially (minimum Monte Carlo
   resolution .05), separately labeled as a bounded sensitivity pilot. Retain
   every failed/non-admissible draw without replacement. Compare paired OOF
   changes to frozen alpha.6 baselines; 500 whole-component frozen-OOF bootstrap
   draws quantify conditional uncertainty only. Repeated nested CV across seeds
   is reported separately as refit/split sensitivity, never folded into that CI.

Before real runs, require controls with pure group offsets, independent
continuous trait, mixed signal, independent Y, unseen levels, size reduction
alone and Y extrapolation alone. Mutate outer/inner validation outcomes and
verify intervention membership, fitted target means and candidate artifacts
are unchanged within each corresponding fit scope. Require the correct response
to destruction of within-group information, rather than interpreting every
performance decline as shortcut learning. No causal chemical percentage or
universal risk score is authorized.
