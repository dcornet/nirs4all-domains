## Conditional structural warnings

Protocol: `domains.structural_warnings.v1`; source report SHA256 `2360b7092e0b32c49e1ec10604d5433287349c72aa77e48f0537366a2f44e1f1`.

Dataset `ucph_tablet_nir`, view `X`, population `saved-population:7fab9c8f7422a1cf4f827843d1775e8d6836c136bf41b4bcd1564c2572a2a858`, representation `raw`.

These findings guide verification; they are not a global dataset-risk grade.

### physical_unit_dependence

Assessment: PHYSICAL_UNIT_EVIDENCE_UNAVAILABLE.

What was observed?

PHYSICAL_UNIT_EVIDENCE_UNAVAILABLE

Why might it matter?

Observation-level partitioning could be optimistic for prediction of new units when shared specimens, technical repetitions or references cross the split.

What should be checked next?

- Use the declared identity/reference mapping and existing Preflight integrity controls to inspect overlap; evaluate a whole-unit contrast matching deployment. Conditions: The objective is prediction of new specimens or independent reference units; the declared dependency applies to that objective. Prerequisites: Original specimen/reference membership; Actual split membership; Intended prediction unit. Testability: requires_information.

What remains unknown?

- Physical and assay identities may be incomplete.
- This is conditional methodological caution, not a probability, severity grade or prediction of calibration failure.
- Declared provenance is retained, not independently authenticated by this interpreter.
- Clusters, factor cardinality and variance concentration do not establish physical identities, causation or leakage.
- Dataset identities, X views, profile rows and provenance components are not independent experiments.
- Validation and preprocessing choices depend on the intended deployment; none is universally best.
- X-derived groups and repeated sample-key counts alone are not accepted physical-unit evidence; this layer does not duplicate Preflight's detector.

Evidence scope and coverage:

```json
{
  "scope": {
    "dataset_id": "ucph_tablet_nir",
    "source_id": "X",
    "content_version": "1.1.0",
    "population_id": "saved-population:7fab9c8f7422a1cf4f827843d1775e8d6836c136bf41b4bcd1564c2572a2a858",
    "scope_kind": "full_source",
    "representation": "raw",
    "n_observations": 310
  },
  "coverage": {
    "canonical_dataset_ids": [
      "ucph_tablet_nir"
    ],
    "historical_or_unknown_dataset_ids": [],
    "dataset_identities": [
      "ucph_tablet_nir"
    ],
    "n_dataset_identities": 1,
    "x_views": [
      {
        "dataset_id": "ucph_tablet_nir",
        "source_id": "X"
      }
    ],
    "n_x_views": 1,
    "eligible_cases": 1,
    "computed_cases": 0,
    "unavailable_cases": 1,
    "original_source_identifiers": [
      "source-url:ucphchemometrics.com/tablet"
    ],
    "documented_references": [
      "https://ucphchemometrics.com/tablet/",
      "https://ucphchemometrics.com/datasets/"
    ],
    "database_count": {
      "status": "unavailable",
      "reason": "AUTHORITATIVE_DATABASE_GROUPING_NOT_SUPPLIED",
      "value": null
    },
    "declared_provenance_groups": [
      "provenance:08babb771919a7e25a3d5a87"
    ],
    "documented_provenance_group_count": {
      "status": "computed",
      "reason": null,
      "value": 1
    },
    "original_study_families": [],
    "original_study_family_count": {
      "status": "unavailable",
      "reason": "ORIGINAL_STUDY_GROUPING_NOT_ESTABLISHED",
      "value": null
    },
    "observation_evidence_level": "descriptive",
    "risk_evidence_level": "hypothesis",
    "externally_validated_warning": false
  }
}
```

### experimental_factor_structure

Assessment: conditional.

What was observed?

Nonzero descriptive factor-PC correspondence is observed independently of flat-cluster agreement.

Why might it matter?

A factor associated with X may affect the applicability of a validation result when that factor changes in intended deployment.

What should be checked next?

- Examine the declared 'batch' contrast with indivisible units and crossed factors preserved. Conditions: If the intended deployment changes or excludes documented factor 'batch'; its relevance must be established. Prerequisites: Original factor memberships; Physical/reference dependencies; Crossed-factor coverage and deployment objective. Testability: requires_information.
- First establish whether 'scale' changes in deployment; a categorical column alone does not require GroupKFold/LOGO. Conditions: If the intended deployment changes or excludes documented factor 'scale'; its relevance must be established. Prerequisites: Original factor memberships; Physical/reference dependencies; Crossed-factor coverage and deployment objective. Testability: requires_information.

What remains unknown?

- Cardinality, missing levels, acquisition weighting, repeat counts and confounding remain relevant.
- This is conditional methodological caution, not a probability, severity grade or prediction of calibration failure.
- Declared provenance is retained, not independently authenticated by this interpreter.
- Clusters, factor cardinality and variance concentration do not establish physical identities, causation or leakage.
- Dataset identities, X views, profile rows and provenance components are not independent experiments.
- Validation and preprocessing choices depend on the intended deployment; none is universally best.
- Nonzero eta-squared is not significance, causation, leakage or predicted failure; no severity threshold is used.
- Weak/negative cluster ARI does not negate continuous geometry. Y-derived metadata are excluded from primary evidence.
- Repeated acquisitions are not automatically independent specimen or reference units.
- Marginal associations do not separate crossed or confounded factors.

Evidence scope and coverage:

```json
{
  "scope": {
    "dataset_id": "ucph_tablet_nir",
    "source_id": "X",
    "content_version": "1.1.0",
    "population_id": "saved-population:7fab9c8f7422a1cf4f827843d1775e8d6836c136bf41b4bcd1564c2572a2a858",
    "scope_kind": "full_source",
    "representation": "raw",
    "n_observations": 310
  },
  "coverage": {
    "canonical_dataset_ids": [
      "ucph_tablet_nir"
    ],
    "historical_or_unknown_dataset_ids": [],
    "dataset_identities": [
      "ucph_tablet_nir"
    ],
    "n_dataset_identities": 1,
    "x_views": [
      {
        "dataset_id": "ucph_tablet_nir",
        "source_id": "X"
      }
    ],
    "n_x_views": 1,
    "eligible_cases": 1,
    "computed_cases": 1,
    "unavailable_cases": 0,
    "original_source_identifiers": [
      "source-url:ucphchemometrics.com/tablet"
    ],
    "documented_references": [
      "https://ucphchemometrics.com/tablet/",
      "https://ucphchemometrics.com/datasets/"
    ],
    "database_count": {
      "status": "unavailable",
      "reason": "AUTHORITATIVE_DATABASE_GROUPING_NOT_SUPPLIED",
      "value": null
    },
    "declared_provenance_groups": [
      "provenance:08babb771919a7e25a3d5a87"
    ],
    "documented_provenance_group_count": {
      "status": "computed",
      "reason": null,
      "value": 1
    },
    "original_study_families": [],
    "original_study_family_count": {
      "status": "unavailable",
      "reason": "ORIGINAL_STUDY_GROUPING_NOT_ESTABLISHED",
      "value": null
    },
    "observation_evidence_level": "descriptive",
    "risk_evidence_level": "hypothesis",
    "externally_validated_warning": false
  }
}
```

### preprocessing_dependent_organization

Assessment: observed.

What was observed?

Recorded representations/settings change at least one measured aspect of organization.

Why might it matter?

A conclusion based on one representation or density setting may be specific to that assumption.

What should be checked next?

- Check whether the scientific conclusion persists across predefined physically admissible representations and density settings; inspect full-X neighbors separately from PCA geometry and partitions. Conditions: The intended validation/preprocessing rationale relies on the observed organization. Prerequisites: Admissible representation definitions; Matched populations/query references; Original native settings. Testability: available.

What remains unknown?

- Unavailable representations and resampling robustness remain separate evidence.
- This is conditional methodological caution, not a probability, severity grade or prediction of calibration failure.
- Declared provenance is retained, not independently authenticated by this interpreter.
- Clusters, factor cardinality and variance concentration do not establish physical identities, causation or leakage.
- Dataset identities, X views, profile rows and provenance components are not independent experiments.
- Validation and preprocessing choices depend on the intended deployment; none is universally best.
- No family is selected as a winner. Cluster counts are not physical populations.
- All-noise is computed, a trivial partition has no informative ARI, and native refusal is unavailable; none establishes absence of continuous structure.

Evidence scope and coverage:

```json
{
  "scope": {
    "dataset_id": "ucph_tablet_nir",
    "source_id": "X",
    "content_version": "1.1.0",
    "population_id": "saved-population:7fab9c8f7422a1cf4f827843d1775e8d6836c136bf41b4bcd1564c2572a2a858",
    "scope_kind": "full_source",
    "representation": "raw",
    "n_observations": 310
  },
  "coverage": {
    "canonical_dataset_ids": [
      "ucph_tablet_nir"
    ],
    "historical_or_unknown_dataset_ids": [],
    "dataset_identities": [
      "ucph_tablet_nir"
    ],
    "n_dataset_identities": 1,
    "x_views": [
      {
        "dataset_id": "ucph_tablet_nir",
        "source_id": "X"
      }
    ],
    "n_x_views": 1,
    "eligible_cases": 1,
    "computed_cases": 1,
    "unavailable_cases": 0,
    "original_source_identifiers": [
      "source-url:ucphchemometrics.com/tablet"
    ],
    "documented_references": [
      "https://ucphchemometrics.com/tablet/",
      "https://ucphchemometrics.com/datasets/"
    ],
    "database_count": {
      "status": "unavailable",
      "reason": "AUTHORITATIVE_DATABASE_GROUPING_NOT_SUPPLIED",
      "value": null
    },
    "declared_provenance_groups": [
      "provenance:08babb771919a7e25a3d5a87"
    ],
    "documented_provenance_group_count": {
      "status": "computed",
      "reason": null,
      "value": 1
    },
    "original_study_families": [],
    "original_study_family_count": {
      "status": "unavailable",
      "reason": "ORIGINAL_STUDY_GROUPING_NOT_ESTABLISHED",
      "value": null
    },
    "observation_evidence_level": "descriptive",
    "risk_evidence_level": "hypothesis",
    "externally_validated_warning": false
  }
}
```

### spectral_support_mismatch

Assessment: TRAIN_FITTED_EVALUATION_X_SUPPORT_UNAVAILABLE.

What was observed?

TRAIN_FITTED_EVALUATION_X_SUPPORT_UNAVAILABLE

Why might it matter?

Observed deployment/evaluation spectra may require extrapolation beyond the recorded training support.

What should be checked next?

- Examine extrapolation and domain overlap using train-fitted diagnostics and a validation contrast matching the intended deployment. Conditions: The observed evaluation X represents the intended application population. Prerequisites: Training/evaluation population identities; Additional multivariate support evidence. Testability: requires_information.

What remains unknown?

- Entirely unseen future X cannot be assessed by this observed-evaluation diagnostic.
- This is conditional methodological caution, not a probability, severity grade or prediction of calibration failure.
- Declared provenance is retained, not independently authenticated by this interpreter.
- Clusters, factor cardinality and variance concentration do not establish physical identities, causation or leakage.
- Dataset identities, X views, profile rows and provenance components are not independent experiments.
- Validation and preprocessing choices depend on the intended deployment; none is universally best.
- This warning is evaluation-X-aware. One-PC exceedance is not predicted failure; zero exceedance is not full multivariate support.

Evidence scope and coverage:

```json
{
  "scope": {
    "dataset_id": "ucph_tablet_nir",
    "source_id": "X",
    "content_version": "1.1.0",
    "population_id": "saved-population:7fab9c8f7422a1cf4f827843d1775e8d6836c136bf41b4bcd1564c2572a2a858",
    "scope_kind": "full_source",
    "representation": "raw",
    "n_observations": 310
  },
  "coverage": {
    "canonical_dataset_ids": [
      "ucph_tablet_nir"
    ],
    "historical_or_unknown_dataset_ids": [],
    "dataset_identities": [
      "ucph_tablet_nir"
    ],
    "n_dataset_identities": 1,
    "x_views": [
      {
        "dataset_id": "ucph_tablet_nir",
        "source_id": "X"
      }
    ],
    "n_x_views": 1,
    "eligible_cases": 1,
    "computed_cases": 0,
    "unavailable_cases": 1,
    "original_source_identifiers": [
      "source-url:ucphchemometrics.com/tablet"
    ],
    "documented_references": [
      "https://ucphchemometrics.com/tablet/",
      "https://ucphchemometrics.com/datasets/"
    ],
    "database_count": {
      "status": "unavailable",
      "reason": "AUTHORITATIVE_DATABASE_GROUPING_NOT_SUPPLIED",
      "value": null
    },
    "declared_provenance_groups": [
      "provenance:08babb771919a7e25a3d5a87"
    ],
    "documented_provenance_group_count": {
      "status": "computed",
      "reason": null,
      "value": 1
    },
    "original_study_families": [],
    "original_study_family_count": {
      "status": "unavailable",
      "reason": "ORIGINAL_STUDY_GROUPING_NOT_ESTABLISHED",
      "value": null
    },
    "observation_evidence_level": "descriptive",
    "risk_evidence_level": "hypothesis",
    "externally_validated_warning": false
  }
}
```

### insufficient_experimental_context

Assessment: observed.

What was observed?

The report leaves specific experimental/deployment questions unanswered.

Why might it matter?

Missing context limits the validation/dependency questions that can be answered; unknown structure is not evidence of a dangerous dataset.

What should be checked next?

- Obtain the original identity/context/reference mappings. Until then, report the limitations and use explicitly exploratory representation/support sensitivity without reconstructing physical groups. Conditions: The unanswered questions affect the intended deployment claim. Prerequisites: Which observations share a physical specimen or technical acquisition unit?; Which instrument, session, date, site or experimental conditions apply?; Which observations share an assay/reference measurement?. Testability: requires_information.

What remains unknown?

- Which observations share a physical specimen or technical acquisition unit?
- Which instrument, session, date, site or experimental conditions apply?
- Which observations share an assay/reference measurement?
- This is conditional methodological caution, not a probability, severity grade or prediction of calibration failure.
- Declared provenance is retained, not independently authenticated by this interpreter.
- Clusters, factor cardinality and variance concentration do not establish physical identities, causation or leakage.
- Dataset identities, X views, profile rows and provenance components are not independent experiments.
- Validation and preprocessing choices depend on the intended deployment; none is universally best.

Evidence scope and coverage:

```json
{
  "scope": {
    "dataset_id": "ucph_tablet_nir",
    "source_id": "X",
    "content_version": "1.1.0",
    "population_id": "saved-population:7fab9c8f7422a1cf4f827843d1775e8d6836c136bf41b4bcd1564c2572a2a858",
    "scope_kind": "full_source",
    "representation": "raw",
    "n_observations": 310
  },
  "coverage": {
    "canonical_dataset_ids": [
      "ucph_tablet_nir"
    ],
    "historical_or_unknown_dataset_ids": [],
    "dataset_identities": [
      "ucph_tablet_nir"
    ],
    "n_dataset_identities": 1,
    "x_views": [
      {
        "dataset_id": "ucph_tablet_nir",
        "source_id": "X"
      }
    ],
    "n_x_views": 1,
    "eligible_cases": 1,
    "computed_cases": 1,
    "unavailable_cases": 0,
    "original_source_identifiers": [
      "source-url:ucphchemometrics.com/tablet"
    ],
    "documented_references": [
      "https://ucphchemometrics.com/tablet/",
      "https://ucphchemometrics.com/datasets/"
    ],
    "database_count": {
      "status": "unavailable",
      "reason": "AUTHORITATIVE_DATABASE_GROUPING_NOT_SUPPLIED",
      "value": null
    },
    "declared_provenance_groups": [
      "provenance:08babb771919a7e25a3d5a87"
    ],
    "documented_provenance_group_count": {
      "status": "computed",
      "reason": null,
      "value": 1
    },
    "original_study_families": [],
    "original_study_family_count": {
      "status": "unavailable",
      "reason": "ORIGINAL_STUDY_GROUPING_NOT_ESTABLISHED",
      "value": null
    },
    "observation_evidence_level": "descriptive",
    "risk_evidence_level": "hypothesis",
    "externally_validated_warning": false
  }
}
```

## Deployment-aware validation interpretation

Protocol: `domains.validation_intent.v1`. Report SHA-256: `2360b7092e0b32c49e1ec10604d5433287349c72aa77e48f0537366a2f44e1f1`.

Intended use: outside_context. Population: Future production batches on the documented tablet process
Prediction unit: new_context. Split family: unknown.
Split description: unspecified
X-derived groups: False. Group basis/construction: unknown / unknown.
Transductive: None (TRANSDUCTIVE_STATUS_UNKNOWN).

### Dependency units and evidence

- Unspecified / not referenced.

### Factor/context exclusions (relationships retained)

- batch (block): excluded: unknown; relevant to intent: yes; declared evidence. Reference: Qualified original batch metadata in the referenced evidence. Relationship: Batch/acquisition and assay confounding must be checked; no physical independence claimed.

### Referenced prediction metrics

- Unspecified / not referenced.

### Spectral-support evidence

- Unspecified / not referenced.

### outside_context

Conditions:

- If the objective is prediction outside the experimental context, match the tested novelty to that objective.
- No evidenced deployment-relevant physical/context exclusion is established by the supplied evaluation facts.

Supported:

- Only the referenced X/structural evidence is described; predictive performance is not established.

Not established:

- Universal external-population transfer, causal shortcut attribution and deployment-risk probabilities.
- Independence of unrecorded physical specimens or shared assay references.
- Unseen-population transfer from random/representative CV or X-derived clusters alone.
- New-experiment generalization from genotype, block or instrument holdout alone; those novelty types are distinct.
- Generalization to future unseen levels beyond the tested exclusions without representative independent evidence.

### Missing information

- Actual evaluation split family is unspecified.
- Physical specimen, shared reference and acquisition dependencies are unknown.
- Evaluation group basis is unknown.
- Transductive use of evaluation X is unspecified.
- No spectral-support evidence is referenced.
- No computed prediction-error evidence is referenced; target and estimator may be absent.
- Exclusion/evidence is incomplete for relevant factor batch.

### Limitations

- Facts and evidence quality are caller declarations with report references; their provenance is not automatically verified.
- A categorical factor alone does not establish the need for a group split; no validation family is universally preferred.
- Known dependencies need not be exhaustive. No causal shortcut or probability of deployment failure is inferred.
