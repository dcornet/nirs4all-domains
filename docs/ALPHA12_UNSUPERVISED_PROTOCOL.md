# Alpha.12 — domains.unsupervised.v0.1

Frozen before new representation, neighborhood or stability experiments. The
read-only retrospective audit uses alpha.11 scientific values and native Methods
summaries, with zero PCA, clustering or predictive fits. Its entry-level source
hashes and 371-file historical preservation map are separate artifacts.

## Information and populations

The pinned catalog contains 42 entries, 37 with computed X-only evidence.
Selection and definitions use only X, original source descriptors, observation
identities and the retrospective X-only audit. No target table, model error,
target association or fitted predictor enters selection or threshold tuning.
Historical Level B/C reports remain unchanged and are not confirmatory evidence.

Pre-execution source amendment: the two previously unavailable EcoSIS package
endpoints now return HTTP 200 with matching original package IDs, ODbL and
CC BY-SA declarations. Their existing local matrices can enter the new
rights/axis/dimension audit without acquisition. Thus the initial upper bound
is 39 sources / 78 representation PCA fits / 156 reference HDBSCAN fits,
conditional on those checks. The seven-case stability selection is unchanged.
The 37-case retrospective denominator is not rewritten. Official metadata
responses and dates are pinned in source-reaudit.json; no restriction is bypassed.

Full-source characterization is descriptive, including all observations and
original wavelengths. It does not supply a prospective train-fitted reference.
Documented historical split support is reused with its original fit population.
No held-out HDBSCAN membership is invented. Equal row counts never establish a
cross-source join. Original IDs establish paired preparations where verified.

## Two representations

Use raw X and public Methods 1.3.6 SNV(with_mean=true,with_std=true,ddof=0).
SNV is per spectrum; its fitted width is not a population statistic. Qualify
row-wise isolation, positive affine invariance and zero-variance behavior before
real use. Constant spectra make the full SNV representation unavailable rather
than causing deletion or arbitrary replacement. Negative intensities alone do
not invalidate a numerical SNV contrast, but no chemical or nuisance-removal
interpretation follows. No derivative or preprocessing search is introduced.

Methods FlexiblePCA centers each complete representation and requests all
min(20,p,n-1) components, without whitening or autoscaling. Retained fractions
use independently calculated full covariance trace. Exact full moments are
optional; unavailable moments never become truncated effective dimension.
Keep original trace/units and dimensionless within-source descriptors separate.

HDBSCAN settings remain (min_cluster_size=8,min_samples=4,EOM) and (12,4,EOM),
allow_single_cluster=false. All returned PCA components are used. A change in
PCA solver route or variance retention is reported, not interpreted as chemistry.

## Native neighborhoods and limits

The public Preflight/Methods nearest-neighbor API supports arbitrary queries,
k and group exclusion. Its source scans every reference row and keeps k
candidates; it does not allocate an n-by-n distance matrix. Runtime remains
O(n_query*n_reference*(p+k)); blockwise transport does not change that bound.
No approximate neighbor API is substituted and no generic kNN engine is copied.
Preflight's Rust provider adds a 250,000,000-product limit per call. For the new
750,000,000 total bound, partition only query rows into deterministic calls below
that existing per-call limit, each against the identical full reference. This
is public-provider transport, not a replacement distance/search implementation.

Prespecify k=min(8,n-1), summarized at ranks 1,4,8 where available. Same-source
queries exclude their own observation, not an inferred physical duplicate.
Full-axis complete-source mode permits n*n*p <= 750,000,000, an explicit new
compute limit; source-specific costs show eligibility rises from 12 to 22 of
the 37 existing profiles. This is not yet execution coverage.

Other sources retain the entire reference population and all wavelengths.
Use a seeded simple random sample without replacement of min(128,n) query IDs,
reduced only if q*n*p would exceed 750,000,000; q<32 is unavailable. Query
membership is selected once from IDs, independent of spectra/representation,
with seed 12017, and exactly shared across raw/SNV and PCA/full-axis comparisons.
Those records are query-subset descriptions, never complete-source neighbors.

The complete-source result and the matched query subset are distinct supports.
Distance quantiles, rank-specific neighborhoods and gaps are measured by native
kernels. Normalize distances by sqrt(full trace) within each representation.
Report fractions with nearest normalized distance <= [1e-6,.001,.01,.05,.1,.25,.5].
These scales are descriptive radii, not laboratory duplicate thresholds.
For partial queries, 100 seeded query-bootstrap draws describe sensitivity of
the observed query sample's proximity fractions. They do not identify exact
finite-population coverage, biological uncertainty or unobserved tails. Quantile
sampling intervals remain unavailable without a separately qualified protocol.

Compare nearest-neighbor identities, set overlap at k=4/8 and exact rank
persistence on the same query IDs. Also compare full-axis versus PCA neighbors.
These are identity/rank comparisons, not a newly implemented correlation kernel.
Distance-gap ratios with zero denominators remain unavailable; count zeros.
No physical object is merged because a distance is small.

## Prespecified stability subset and stages

Choose seven catalog views from X-only evidence, before new fits:

| Source suffix (all EcoSIS except Cartilage) | Reason from alpha.11 X only |
|---|---|
| 2008_university_of_wisconsin_biotron_fresh_leaf_spectra_reflectance_nirs | 87 observations, two groups, parameter ARI 1 |
| ngee_arctic_2017_canopy_spectral_reflectance_seward_pen_reflectance_nirs | 511 observations; only .9024 retained variance |
| seasonal_measurements_of_photosynthesis_and_leaf_traits_reflectance_nirs | 48 observations; all-noise, no continuum assumption |
| tabletop_leaf_drydowns_to_relate_leaf_spectra_and_leaf_reflectance_nirs | 962 observations; 32 primary groups; PDDL correction retained |
| ground_leaf_cabo_spectra_from_herbarium_project_reflectance_nirs | 607 observations; six groups and .409 noise |
| fresh_leaf_cabo_spectra_from_herbarium_project_reflectance_nirs | Related preparation, 609 observations; three groups |
| cartilage_spectroscopy_scientificdata_nir | 2605 scans; verified 869 repeated physical locations; weak parameter agreement |

Stage the small Biotron case and large Cartilage case first; measure costs before
executing the five already selected remaining cases. Do not add sources based
on favorable stability. Two fractions (.6,.8), 20 draws each, seed 12031; same
selected units for both representations/settings. At most 560 resampled PCA
fits and 1120 HDBSCAN fits, plus 74 complete representation reference PCA fits
and 148 HDBSCAN fits; additional controlled fixtures are counted separately.
SNV is stateless and is not a supervised fit. Models/target interventions: zero.

Refit PCA on every selected complete-unit draw, then fit both HDBSCAN settings
on that identical score matrix. Failed/degenerate draws remain attempted;
never redraw. Known physical repeat identities must be transported from verified
source correspondence. If a reliable physical map cannot be supplied, that
source's stability is unavailable; never downgrade known repeats to independent
rows. Other cases use observation-level subsampling explicitly labeled
descriptive algorithmic stability, not biological sampling uncertainty.

Compare reference and each draw on exact shared observation IDs: ARI including
noise, ARI excluding jointly noisy observations, noise agreement, per-cluster
support and membership-strength summaries. ARI requires >=20 shared rows,
>=50% reference support, at least two classes and a nonsingleton in each
partition. Report support/failures even when ARI is not identifiable.

Bound co-membership evidence using a prespecified seeded panel of at most 128
within-reference-cluster pairs and 128 between-cluster pairs, with exact pair
IDs/exposures. Compute successful same-nonnoise-cluster counts only over draws
containing both members. Never report this sampled pair panel as all-pair
co-membership. Zero exposures are unavailable, not agreement zero or one.

Operational reproducible-group support requires >=30 observations, >=20
declared resampling units, >=90% successful draws, >=90% eligible ARIs,
median ARI>=.9, lower nearest-rank p10>=.8, noise agreement p10>=.9,
reference noise<=.4, >=2 reference groups, and median within-group pair-panel
support>=.8 with >=10 exposed pairs. Evaluate each representation, fraction
and setting separately. Overall support requires every eligible combination
and parameter ARI>=.8. These are exploratory reproducibility gates, not a
calibrated biological taxonomy. Failed gates with adequate support mean fragile
partition evidence; missing support means insufficient information. All-noise
does not establish continuum or low susceptibility. Continuum compatibility
requires the separately frozen alpha.5 regular-one-dimensional diagnostic;
otherwise leave its classification unavailable.

## Controlled expectations before numerical qualification

Generate no Y. Sixteen named mechanisms cover isotropic separated groups,
continuous gradient, overlapping populations, severe density imbalance, small
satellites, exact repeated spectra, close independent objects, known repeated
acquisition components, additive/multiplicative effects, continuous chemical
variation, thin manifold, high-dimensional noise, unequal wavelength scaling,
SNV-erased differences, SNV-enhanced shape differences and N-dependent
fragmentation. Qualify 16 mechanisms, including several prespecified sizes for
fragmentation, without tuning real-bank thresholds to their outcomes.

Expected: separated clouds can yield reproducible groups; gradients/manifolds
and noise need not form stable groups. HDBSCAN need not recover every small
satellite or overlapping population. Positive affine effects disappear under
SNV within abs/rel 1e-10; shape differences may persist. Physical identity,
not numerical coincidence, determines component membership. Full-source row
counts/axes/IDs survive every representation. A failed full representation
never becomes a favorable zero metric. Exact analytical native distances use
abs 1e-10; same-input replay and ID/hash joins are exact. Approximate kNN is
unavailable until an upstream implementation and quality study are qualified.

## Resource admission and preservation

Use the existing cumulative alpha.9 StageStore journal, serial execution and
approved campaign/task/evidence/free-volume limits. No new source matrix is
acquired by default. Stream matrices through stdin; retain compact summaries,
labels/identity panels, draws and hashes, without per-fold/source copies of X.
Native peak memory is estimated below 1.5 GiB at existing dimension limits;
measure process peaks where supported and distinguish estimates from quotas.
Preserve all historical files and do not clean caches/builds. Workspace ceiling
increases require the owner's explicit answer to the pending resource review.

The main output is a 42-entry representation-aware evidence matrix. Missing
rights, metadata, physical overlap, exact moments, stability and neighborhoods
have individual status/reason/value states. Cross-source aggregation uses
dimensionless descriptors, with view/entry counts and verified population
relations separate. Unknown population overlap never becomes independence.
