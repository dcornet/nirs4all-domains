# Group–target association — frozen alpha.6 design

Protocol `domains.structural_dependence.v0.1`, frozen 2026-10-17 before new
association or prediction execution. Canonical and structural v1 contracts stay
unchanged. All findings are exploratory and conditional on declared identities.

The unit is one admissible physical mean exported by Rust `represent`. Its
reference audit must permit X–Y. Known shared, contradictory, censored or
composite references block these experiments, while pure-X work remains valid.
Missing targets are excluded with IDs; no target imputation. Missing factors are
excluded from association but use the global training mean in prediction.
Technical acquisitions never contribute extra target votes. Dependency
components, explanatory metadata and discovered spectral clusters are distinct.

Before outcomes are inspected, audit each candidate's source column/hash, keyed
join, missingness, levels, samples and independent components per level, rare
levels, components spanning levels, prediction-time availability and outer-fold
overlap. EcoSIS candidates are original plot, sampling date, genus and species;
coordinates are audited only, with no coordinate bins. Genus/species may be
transported from the documented source by exact sample IDs if missing from the
old export; X, Y, sample order and folds must remain identical.
Source taxonomy receives only leading/trailing whitespace trimming; blanks stay
missing and no taxonomic synonym/epithet merge is inferred. This rule is fixed
before any association or prediction outcome. Factors with at least two levels
supported by three components each and at least 20 seen-level
OOF samples across 10 components qualify for conditional predictive evidence.
Others can be diagnostic baselines, with explicit limited support. Plot under
plot holdout is a deliberately nontransferable diagnostic. Factor selection uses
metadata support, never association or model performance. Full-data HDBSCAN
labels cannot enter any baseline without qualified fold-local assignment.

Methods 1.3.6 ABI 2.19 `n4m_preflight_factor_association` supplies continuous
eta-squared, F, degrees of freedom and level counts. Native unrestricted
permutations are disabled (B=0). Methods summaries supply group/overall means
and sample variance. SS_total=(n−1)sd²; SS_between=eta² SS_total;
SS_within=SS_total−SS_between. This scalar assembly does not reimplement ANOVA.
Native undefined F and eta² become null with reasons, never infinite JSON.
Constant Y, one level, fewer than two valid rows and missing factor are explicit
insufficient states. Saturated and nearly saturated factors (levels/n >= .8),
singleton levels, sparse component support and unknown assay precision warn
against inferential interpretation even when descriptive eta² is computable.

Bootstrap: 200 draws, seed 17, whole declared components sampled with
replacement, preserving all rows and multiplicity, no redraw. Record every draw
and its component IDs, value or failure reason. Nearest-rank 2.5%/97.5% endpoints
require 100 successful draws and 10 original components. They condition on the
observed design and do not establish population independence.

Expected controls, fixed before tests: analytical eta²=0, 1 and .8; unbalanced
groups obey the SS identity; constant/one-level/saturated inputs preserve native
undefined fields. Reordering and identical repeat duplication cannot alter the
physical-level result. Shared references block X–Y. Numeric comparisons use
absolute tolerance 1e-10 for analytical association and SS identities relative
to 1+SS_total. Prediction expectations are frozen in the companion protocol.
