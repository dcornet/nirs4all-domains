# F4.3 comparability rules

F4.3 reports representation-conditional observations from a prospectively
declared fixed panel. Every comparison is between the same ordered reference
population and declared exclusion policy unless the result explicitly marks an
entry unavailable. No comparison chooses a winning transform.

## Structure

When selected, each derived source independently reuses the fixed structure
bundle: Methods PCA (up to 20 resolved components), exact nearest neighbors with
`k=min(8,n-1)`, and HDBSCAN on the PCA scores with min cluster size 8, min
samples 4, EOM selection, and no single-cluster allowance. The settings are not
retuned by representation. Small-population, constant-input, domain and owner
failures remain representation-local.

PCA coordinates are not compared component by component. Sign, rotation, rank
and retained subspaces can differ, and no paired-subspace comparison API is
qualified. Show separate PCA results and their original source/axis. Do not
compare absolute distances across differently scaled representations.

## Neighbor identity retention

Compare the owner-returned neighbor identity sets for each shared reference row
under the same order and exclusions. For row `i`, report the intersection
count and both returned counts. The defined row fraction is
`|N_raw(i) ∩ N_rep(i)| / |N_raw(i)|`; when the raw neighborhood is empty, the
fraction is unavailable with an explicit reason. Summaries retain the number of
available and unavailable rows and the denominator. This is protocol assembly
over returned neighbor IDs, not a new neighbor search or owner-provided
similarity score.

## Cluster partition agreement

Adjusted Rand index uses only observations assigned in both partitions. Keep
the joint assigned count and counts for noise and assignment transitions;
owner-undefined or trivial values remain unavailable. Cluster Jaccard uses the
original complete label vectors, ignores negative/unassigned labels, and
retains pairwise intersections and cluster sizes. Do not choose a favorable
cluster matching or replace all-noise/trivial cases with perfect agreement.
These are descriptive partition comparisons, not physical population
validation or resampling stability.

## Factors and support

Up to two prospectively selected eligible train metadata factors are associated
with each representation's own recorded PCA scores through the existing F4.1
Methods/Preflight path. Preserve missingness, counts, dependency descriptions,
and factor provenance. Component-wise eta-squared is not a fraction of total
spectral variance. A changing PCA basis and repeated examination of factors do
not establish independent confirmation. Factor/color export permission remains
separate.

The optional F4.2 monitor/support bundle keeps its original indexed-fold,
training-fit, and dependence qualifications. Its results remain specific to
each derived source. Neither monitor thresholds nor distances can be compared
as though they shared one fitted geometry.

## Reading changes

Persistence means that a named observation is present across the declared
representations and diagnostic outputs. A difference is conditional on this
panel, population, parameterization, owner version and diagnostic. Persistence
does not prove a real chemical mechanism; disappearance does not prove noise.
No aggregate robustness score, causal shortcut percentage, predictive/leakage
probability, or representation recommendation is defined.

These are protocol rules, not a claim that all comparisons have passed native,
WASM or browser qualification. Actual results and tolerances belong in the
F4.3 validation record.
