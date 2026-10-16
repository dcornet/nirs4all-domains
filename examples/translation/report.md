# NIRS domains audit

Dataset: synthetic-translation · source: nir · target: concentration · split: explicit-v1

Status: **partial** · protocol: `domains.canonical.v0.1` · origin: synthetic

Test target accessed: **false**

## Dimensions

- coverage: computed, exploratory
- generalization: spectral comparison computed; predictive risk unvalidated
- integrity: computed (Preflight exploratory alpha)
- measurement: see Preflight availability per metric
- structure: unavailable
- xy_relationship: train target description in Preflight; predictability unavailable

## Observations and actions

- **8 of 8 test observations exceed a train-only coverage heuristic.** → confidence: low → Possible spectral extrapolation; this does not establish a loss of predictive performance. → Inspect the listed observations and verify the intended application domain with independent evaluation.

## Metrics

| Metric | Status | Value | Unit / reason |
|---|---|---|---|
| structure.clustering | Unavailable | null | CLUSTER_PROTOCOL_DEFERRED |
| xy.nested_probe | Unavailable | null | NESTED_GROUP_VALIDATION_DEFERRED |
| explainability.conditional_effects | Unavailable | null | CONDITIONAL_FACTOR_PROTOCOL_DEFERRED |
| coverage.effective_dimension | Computed | 1.0 | dimensions |
| domain.centroid_distance | Computed | 24.494897427831777 | absorbance |
| domain.dispersion_ratio | Computed | 0.9999999999999996 | variance ratio |
| coverage.test_outside_fraction | Computed | 1.0 | fraction |
| coverage.train_neighbor_distances | Computed | [2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178] | absorbance |
| coverage.test_neighbor_distances | Computed | [7.348469228349531,9.79795897113271,12.247448713915889,14.696938456699067,17.146428199482244,19.595917942265423,22.045407685048602,24.49489742783178] | absorbance |
| coverage.train_reconstruction_squared | Computed | [1.1832913578315177e-30,1.1832913578315177e-30,0.0,0.0,0.0,0.0,1.1832913578315177e-30,1.1832913578315177e-30] | signal squared |
| coverage.test_reconstruction_squared | Computed | [4.733165431326071e-30,4.733165431326071e-30,0.0,0.0,0.0,0.0,1.8932661725304283e-29,0.0] | signal squared |
| target.test_shift | Unavailable | null | Y_TEST_FORBIDDEN_PRE_TRAINING |

## Limits

- Exploratory descriptive audit; no calibrated statistical test or prediction-performance claim.
- Coverage thresholds use train-only Tukey fences; these are heuristics, not failure probabilities.
- No clustering, confounding inference, nested PLS/PCR probe, AOM, MMD, energy or C2ST protocol is implemented.
- Repeated physical samples retain integrity/measurement diagnostics; geometric aggregation is deferred.
- Counts of physical samples and groups are not an estimator of effective sample size.

The adjacent JSON preserves the fitted state, observation IDs, distributions, parameters, engine versions and the full Preflight report.
