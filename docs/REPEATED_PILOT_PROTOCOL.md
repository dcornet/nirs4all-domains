# Frozen alpha.4 pilot protocol

Declared before pilot splitting, coverage or predictive results. Primary case:
EcoSIS Freeze Dried, X, LMA_value_g/m2; no dataset/target search. Seeds 17
(primary), 31 and 47 (coverage sensitivity only). Hold out ceil(20% of the
observed plots) by SHA-256(seed, plot) ordering, without X or Y. All acquisitions
and samples of a plot remain together. Plots are the most detailed documented
shared location; their independence is conditional within the three sampled
geographical areas. Plant identity is not independently established. No claim
of transfer to a new region follows from this design.

Original guides declare six spectral replicates per dried sample. The exact
rescan/repositioning/preparation subtype is unspecified. A new explicit
`technical_unspecified` declaration requires a source evidence URI and shared
sample/context; it permits a descriptive sample mean, not a pure instrument-noise
interpretation. Different drying methods or foreoptics are never pooled. Native
grouped spectra and physical-sample means are compared with separately fitted
train-only PCA and Tukey fences. Legacy `native` behavior remains available;
`grouped_native` explicitly requests acquisition-level descriptive geometry.

The initial 390 x 2151 preflight PCA returned Methods UNSUPPORTED because full
covariance moments exceed 250 million products. A provisional common 2 nm view
was executed and preserved. The owner's subsequent instruction selects the
public FlexiblePCA fit/transform API. Final qualification retains all 2151 bands
and all 390 primary training acquisitions. Both final views explicitly use
FlexiblePCA; Methods scores fit train only and transform test without refit.
Exact covariance trace comes from Methods feature variances. Full squared
covariance trace is computed separately through the existing kernel only when
within budget. Missing full moments make effective dimension unavailable, while
PCA scores and coverage remain computed. No truncated spectrum is represented
as an exact full covariance moment. The affine projection is recovered with
public transforms of zero/coordinate queries for reconstruction diagnostics;
the opaque fitted native state remains alive and supplies actual train/test
transforms. Source values are never interpolated or rescaled.

Coverage uncertainty uses 500 cluster-bootstrap draws of held-out plots, retaining
all their samples and acquisitions. The statistic is the physical-sample mean of
acquisition flags; a mean-spectrum row has one flag. A nearest-rank 95% percentile
interval describes held-out plot variability conditional on the fixed train fit.
It does not estimate PCA/threshold refit stability or population-independent risk.
The three prespecified splits show split sensitivity without choosing a winner.

The primary split additionally uses 100 paired bootstrap draws of whole train
components, refitting PCA and both train fences in every draw. The held-out X
population stays fixed. Repeated draws retain multiplicity as bootstrap weights.
All unsuccessful fits are reported, without redrawing. The two representations
share the same component draws; this checks PCA/threshold/coverage refit stability
separately from held-out-population uncertainty. No Y is used in this calculation.

Predictive sanity uses the primary development partition only, one complete mean
spectrum and one LMA per sample. Retained test target values never enter its
input. Five outer group folds; three inner group folds; centered, unscaled native
Methods PLS, components 1..5. DAG-ML executes inner CV, selection and REFIT.
The exported selected N4ME predicts only the corresponding outer holdout through
the public Methods estimator API. The null predicts that outer training set's
Methods mean. Metrics RMSE/MAE/R2 come from Methods, on joined outer OOF IDs.
Inner selection scores are not reported as independent predictive evidence.

Nineteen exploratory permutations exchange whole plot target vectors between
plots of equal sample cardinality, with deterministic sample order within blocks.
Each permutation reruns the complete nested probe. Exchangeability of plots is
an assumption; the coarse Monte Carlo result is not a confirmatory test. No
retained test score, AOM search or alternative dataset ranking is performed.

Controlled expectations fixed before tests: six known replicates become one
analytical mean and one sample vote; partition-spanning repeats fail; group
bootstrap preserves whole plot membership and is invariant to duplicated identical
acquisitions within a sample; test X/Y cannot change train fitted states; a strong
synthetic X-Y relation beats the fold-local null, while an independent synthetic
target does not show stable improvement. Every probe fit is confined to its
declared inner/outer train IDs. All raw/result directories must be new, and previous
alpha.3 evidence remains intact.
