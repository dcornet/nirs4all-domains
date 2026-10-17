# Alpha.7 split stress and negative interventions

Protocol `domains.split_stress.v0.1`, frozen before alpha.7 model execution on
2026-10-17. This programme was not executed in alpha.6. Retain EcoSIS's frozen
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

## Alpha.7 implementation decisions frozen before numerical experiments

The identity/metadata audit found genus closure feasible, but some reference
inner-training scopes have only 29% or 40% of targets in swappable, complete
same-genus-composition blocks. This is metadata evidence, not a model result.
Intervention eligibility requires at least six swappable components and 50% of
training outcomes in such blocks **in every inner and outer training scope**.
Missing-factor blocks are not exchangeable within a factor. Record exact
signature strata, factorial assignment counts, immovable blocks and assumptions.
After drawing, actual source-ID movement and changed-Y fractions are separate.
Changed-Y fraction below 50% is limited evidence, never evidence of independence
or retained group mediation. All scheduled attempts remain recorded, with no
redraw. A constant-within-factor control can execute an identity permutation
but cannot establish perturbation of a nonexistent within-group target signal.

Reference folds retain `group_folds` exactly. Its identity-hash allocation is
already a dependency-safe random-like allocation; add one explicitly seeded
shuffle allocation through that same helper, not a separate split library.
Factor holdout unions components connected by any observed factor level.
Missing-only components remain separate unknown units, never an invented genus.
Use min(5, closure-unit count) outer folds, require at least two outer folds and
three original components in every outer train for nested selection.
Each inner training population must also have at least grid_max+2 samples;
otherwise native PLS selection is explicitly unavailable for that design.
Factor levels must be disjoint across every actual train/validation pair. Outer and
inner folds depend only on IDs/metadata. Inner CV keeps original components
whole; true factor holdout is the outer experimental intervention.

Training-size comparison cannot use the same full validation block and restore
its withheld genera: its complement already excludes them. Instead intersect
each factor-holdout validation block H with each original reference validation
block R. Evaluate that H∩R cell using whole-component subsamples of R's train,
targeting the sample count of H's train. Reference train may legitimately contain
other held-out-genus members outside H∩R; no evaluated component can enter it.
Three deterministic component orders, seeded from H/R/draw identities, greedily
retain components without exceeding the target. Gap <=2 samples is a declared
granularity tolerance and yields limited evidence; exact matches are primary.
If the reference pool is smaller than the requested target, that cell is
unavailable rather than augmented or reused. Each draw combines disjoint cells
so evaluated IDs occur once. Publish full protocol outcomes and matched-ID
conditional comparisons separately. Never call the partial matched subset a
paired all-development experiment.

Bounded real schedule: reuse alpha.6 seed-17 genus predictions (verify IDs,
folds, provider versions and input fingerprint), five extra reference seeds,
one shuffle seed 17, genus holdout and secondary date holdout. Species epithet
receives a feasibility audit only. Size controls apply to primary genus holdout.
Interventions apply only to original reference seed 17 and genus: 19 global and
19 within-factor scheduled attempts, with 500 paired whole-component frozen-OOF
bootstrap draws. No seed × factor × intervention Cartesian campaign. Audit
every inner scope before real intervention execution. Failed/low-power designs
remain explicit. Source area codes are used only to describe date/geography
confounding, not to invent coordinate groups or change the predictor.

Native callback extension: transform original Y only after selecting the exact
native FIT_CV/REFIT training IDs. Independently recreate a training-only target
map for each inner scope; native SELECT scores original inner-validation Y.
REFIT recreates the outer-train map. The same scope/attempt yields the same map
for all candidates and both spectral models. Original outer-validation truth is
used only after prediction. Rank pairing inside compatible vectors is declared
as (factor level, physical ID) for within-factor and physical ID for global;
the resulting destination/source-ID map is explicit, never an input-row join.

An initial native qualification exposed a real technical constraint: the
six-feature analytical fixture loses rank when a factor level is removed or
training is reduced. Requesting six PLS components returned native "Y score
vanished" / "X weights vanished" at component 5; DAG-ML aborts that campaign
rather than selecting around a failed candidate. The standalone stress-control
configuration therefore fixes grid 1–3 before its next execution. Full-rank
analytical intervention gates retain grid 1–6 and their 1e-9 prediction checks.
This is a fixed control-design change, not a per-fold performance-driven cap;
EcoSIS remains on its original grid 1–5. Native failures remain errors, never
silently refitted with a smaller grid.

Analytical tests use 1e-9 absolute prediction tolerance and 1e-10 relative mean/
distribution checks. Native candidate artifact hashes and target maps must be
exactly invariant to forbidden labels; row order and retained-label mutations
must give byte-identical development reports. Mixed/trait controls must lose
fine-grained spectral gain under effective within-factor permutation; pure
group offsets retain between-group signal. Size-only and extrapolation-only
controls demonstrate alternative explanations without a shortcut conclusion.
