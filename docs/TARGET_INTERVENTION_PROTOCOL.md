# Training-target interventions — alpha.7

Protocol `domains.split_stress.v0.1`; the frozen computational design, tolerances
and eligibility thresholds are in SPLIT_STRESS_ALPHA7_PROTOCOL.md. Methods
1.3.6 / DAG-ML 0.3.41 remain the numerical engines. No regression, metric or
generic optimizer is reimplemented.

An intervention exchanges complete target vectors between declared dependency
components, with explicit destination/source physical IDs. Global strata have
equal cardinality and compatible reference status/unit patterns.
Reference patterns follow the declared vector alignment; matching unordered
status counts alone cannot authorize exchanging incompatible positions.
Within-factor strata additionally have identical factor-level composition, exclude missing
factor blocks and align the declared within-vector order by factor then ID.
Reference IDs travel in target-map provenance; dataset reference declarations
are not rewritten or claimed to be new measured outcomes. The counterfactual
training targets are never written back to the source dataset.
This bounded workflow requires complete finite development-component target
vectors; missing development Y is rejected before fitting, rather than silently
permuting partial components. Pure-X workflows remain separate and available.

Exchangeability of plot target vectors within these restrictions is an explicit
exploratory assumption, not established biological/assay independence. The
eligibility report retains block memberships, cardinalities, compositions,
swappable and singleton blocks, exact factorial upper bound on assignments,
movable target fraction, and scope-specific reasons. Duplicate numerical Y
values reduce distinct outcome assignments; do not equate identity permutations
with distinct numerical outcomes. If exact numerical multiplicities are
enumerable, report the reduced number as well.

Each inner FIT_CV uses original rows restricted to its training IDs before any
permutation, mean, residualization or Methods fit. Its validation targets remain
original and enter selection scoring only. Outer REFIT independently applies
the same frozen rule to outer train, never deriving inner targets from an outer
permutation whose sources might lie in inner validation. Native data-view
lineage, target maps, training hashes and N4ME hashes witness these boundaries.
The null and group-only baselines use the same outer intervened training targets.

Compare null, group-only, spectral PLS and group+residual predictions to original
outer-validation Y on the original IDs. Positive degradation is
RMSE(intervened)−RMSE(original); positive gain is RMSE(null)−RMSE(model).
Paired 500-draw component bootstrap conditions on frozen OOF fits, excluding
refit uncertainty. Repeated-CV variability is reported separately. Nineteen
scheduled attempts give at best .05 Monte Carlo resolution but no confirmatory
p-value is produced. Failed and weak attempts are retained without redraw;
unavailable attempts contribute neither zero nor a favorable metric.

Performance surviving an effective within-factor intervention is compatible
with group-associated prediction. Lost performance supports useful finer X–Y
correspondence under the exchangeability assumption. Neither result identifies
a causal chemical percentage. A weak or inadmissible intervention identifies
neither conclusion. Original alpha.4 permuted-outcome experiments retain their
historical meaning and are not reused as training-intervention evidence.
