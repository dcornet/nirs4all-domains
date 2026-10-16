# NIRS domains audit

Dataset: synthetic-qualified_technical_repeats · source: nir · target: concentration · split: explicit-v1

Status: **partial** · protocol: `domains.canonical.v0.2` · origin: synthetic

Test target accessed: **false**

## Dimensions

- coverage: computed, exploratory
- generalization: spectral comparison computed; predictive risk unvalidated
- integrity: computed (Preflight exploratory alpha)
- measurement: see Preflight availability per metric
- structure: unavailable
- xy_relationship: train target description in Preflight; predictability unavailable

## Declared units and representation

| Count | Train | Test |
|---|---:|---:|
| acquisitions | 10 | 8 |
| samples | 8 | 8 |
| physical_samples | 8 | 8 |
| known_references | 8 | 8 |
| missing_reference_acquisitions | 0 | 0 |
| repeat_groups | 2 | 0 |
| declared_independence_groups | 8 | 8 |
| validation_groups | 8 | 8 |
| missing_instrument_or_campaign_acquisitions | 0 | 0 |

Representation: "technical_mean". X-Y blocked by reference audit: false. Known references are counted by supplied ID; missing IDs remain unknown. Validation groups are declared dependency components, not verified independent laboratory units.

## Observations and actions

- **10 exact spectral pairs span development and retained test in nir** → confidence: unknown → Review measurement integrity and independence before calibration. → Review physical identities and partition assignment before fitting

## Metrics

| Metric | Status | Value | Unit / reason |
|---|---|---|---|
| reference.xy_eligibility | Computed | {"reference_identity_complete":true,"status":"descriptive_only"} |  |
| structure.clustering | Unavailable | null | CLUSTER_PROTOCOL_DEFERRED |
| xy.nested_probe | Unavailable | null | NESTED_GROUP_VALIDATION_DEFERRED |
| explainability.conditional_effects | Unavailable | null | CONDITIONAL_FACTOR_PROTOCOL_DEFERRED |
| coverage.effective_dimension | Computed | 1.0 | dimensions |
| domain.centroid_distance | Computed | 0.0 | absorbance |
| domain.dispersion_ratio | Computed | 1.0 | variance ratio |
| coverage.test_outside_fraction | Computed | 0.0 | fraction |
| coverage.train_neighbor_distances | Computed | [2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178,2.449489742783178] | absorbance |
| coverage.test_neighbor_distances | Computed | [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0] | absorbance |
| coverage.train_reconstruction_squared | Computed | [1.1832913578315177e-30,1.1832913578315177e-30,0.0,0.0,0.0,0.0,1.1832913578315177e-30,1.1832913578315177e-30] | signal squared |
| coverage.test_reconstruction_squared | Computed | [1.1832913578315177e-30,1.1832913578315177e-30,0.0,0.0,0.0,0.0,1.1832913578315177e-30,1.1832913578315177e-30] | signal squared |
| target.test_shift | Unavailable | null | Y_TEST_FORBIDDEN_PRE_TRAINING |

## Limits

- Exploratory descriptive audit; no calibrated statistical test or prediction-performance claim.
- Coverage thresholds use train-only Tukey fences; these are heuristics, not failure probabilities.
- No clustering, confounding inference, nested PLS/PCR probe, AOM, MMD, energy or C2ST protocol is implemented.
- Technical means require declared homogeneous contexts; ambiguous and cross-context units are explicitly excluded from pooled geometry.
- Counts of physical samples and groups are not an estimator of effective sample size.
- Physical, group and reference IDs are supplied by the host; structural checks do not independently verify real-world identities or laboratory provenance.

The adjacent JSON preserves the fitted state, observation IDs, distributions, parameters, engine versions and the full Preflight report.
