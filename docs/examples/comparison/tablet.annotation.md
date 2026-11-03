## Predictive comparison interpretation

Protocol: `domains.comparison_interpretation.v1`.

Direct numerical comparison: compatible. Evaluation matching: unmatched_ids.
Null scope: separate_definitions. Reference baseline: better_than_stated_null.

### Reference evidence

Report SHA-256: `0ea810ced51d38877a21d548798418b8361d9682d6b11ccef04d7be44dfeb247`. Evaluation pointer: `/contexts/1`.

- rmse: 0.8239002838589775 (stored value).
- skill: 0.20670341910133327 (stored value).
- null_rmse: 1.038577883350565 (stored value).

- source: `["ucph_tablet_nir", "1.0.0", "X"]`.
- target: `"Active substance mass fraction"`.
- units: `"percent mass/mass"`.
- population: `"C"`.
- model: `"models.pls.pls_regression"`.
- pipeline: `{"engine": "methods", "grid": {"n_components": [1, 2, 3]}, "id": "raw_pls", "method": "models.pls.pls_regression", "preprocessing": "raw"}`.
- training_population: `null`.
- n_train: `230`.
- n_evaluation: `80`.
- null_population: `"C"`.
- evaluation_ids_sha256: `null`.

Evidence pointers: `{"model": "/anchors/0/method", "n_evaluation": "/contexts/1/n_evaluation", "n_train": "/contexts/1/n_train", "null_population": "/contexts/1/source_type", "null_rmse": "/contexts/1/models/raw_pls/null/value/rmse", "pipeline": "/anchors/0", "population": "/contexts/1/source_type", "rmse": "/contexts/1/models/raw_pls/scores/value/rmse", "skill": "/contexts/1/models/raw_pls/S", "source": ["/dataset_id", "/content_version", "/source_id"], "target": "/target/meaning", "units": "/target/unit"}`.

### Stress evidence

Report SHA-256: `0ea810ced51d38877a21d548798418b8361d9682d6b11ccef04d7be44dfeb247`. Evaluation pointer: `/contexts/0`.

- rmse: 1.104234884393284 (stored value).
- skill: 0.5941486363884666 (stored value).
- null_rmse: 2.720786434144444 (stored value).

- source: `["ucph_tablet_nir", "1.0.0", "X"]`.
- target: `"Active substance mass fraction"`.
- units: `"percent mass/mass"`.
- population: `"A"`.
- model: `"models.pls.pls_regression"`.
- pipeline: `{"engine": "methods", "grid": {"n_components": [1, 2, 3]}, "id": "raw_pls", "method": "models.pls.pls_regression", "preprocessing": "raw"}`.
- training_population: `null`.
- n_train: `240`.
- n_evaluation: `70`.
- null_population: `"A"`.
- evaluation_ids_sha256: `null`.

Evidence pointers: `{"model": "/anchors/0/method", "n_evaluation": "/contexts/0/n_evaluation", "n_train": "/contexts/0/n_train", "null_population": "/contexts/0/source_type", "null_rmse": "/contexts/0/models/raw_pls/null/value/rmse", "pipeline": "/anchors/0", "population": "/contexts/0/source_type", "rmse": "/contexts/0/models/raw_pls/scores/value/rmse", "skill": "/contexts/0/models/raw_pls/S", "source": ["/dataset_id", "/content_version", "/source_id"], "target": "/target/meaning", "units": "/target/unit"}`.

### Descriptive contrast

- rmse_difference: 0.2803346005343066 (stress minus reference; relative change is a fraction).
- relative_rmse_deterioration: 0.34025306948709577 (stress minus reference; relative change is a fraction).

Compatibility: `{"model": "same", "n_evaluation": "different", "n_train": "different", "pipeline": "same", "population": "different", "source": "same", "target": "same", "training_population": "unknown", "units": "same"}`.

### Supported

- Target semantics and units match exactly as referenced; existing absolute RMSE values are numerically comparable in those units.
- The RMSE contrast is descriptive sensitivity under the two declared evaluation conditions.
- Evaluation identities are unmatched or unknown; this contrast must not be described as paired.

### Not established

- A causal shortcut, failure probability, universal model/validation ranking or composite risk score.
- Independent specimen, assay or database generalization from matched row IDs or aggregate performance alone.
- Physical factor identity from X-derived clusters, or external transfer beyond the actual tested context.
- Statistical significance from a numerical gap, or robust prediction from a small gap with a poor baseline.

### Missing information

- reference: evaluation_ids is not referenced or unavailable.
- reference: training_population is not referenced or unavailable.
- reference: Referenced spectral support is unavailable at /contexts/1/continuous_support. Status: unavailable; reason: QUALIFIED_CONTINUOUS_SUPPORT_NOT_IMPLEMENTED_FOR_THIS_TASK.
- stress: evaluation_ids is not referenced or unavailable.
- stress: training_population is not referenced or unavailable.
- stress: Referenced spectral support is unavailable at /contexts/0/continuous_support. Status: unavailable; reason: QUALIFIED_CONTINUOUS_SUPPORT_NOT_IMPLEMENTED_FOR_THIS_TASK.

### Limitations

- Keep the two skill definitions and null populations separate; no common-null effect is established.
- Reference skill improves on its stated null: deterioration can describe loss from that baseline advantage. Practical usefulness still needs a task-specific error tolerance and leakage controls.
- population is different across evaluations; an isolated split effect is not established.
- training_population is unknown across evaluations; an isolated split effect is not established.
- n_train is different across evaluations; an isolated split effect is not established.
- n_evaluation is different across evaluations; an isolated split effect is not established.
- Reference and stress name the caller's contrast; they do not rank validation families. Different novelty types and crossed factors retain their separate intent descriptions.
- Source/content/population identities, semantic equivalence and evidence quality are caller assertions, not automatic provenance certification.
- Only stored aggregate metrics are read. No predictions, nulls, intervals, significance tests, causal mechanisms or independent-database counts are estimated.

### Reference deployment scope

#### Deployment-aware validation interpretation

Protocol: `domains.validation_intent.v1`. Report SHA-256: `0ea810ced51d38877a21d548798418b8361d9682d6b11ccef04d7be44dfeb247`.

Intended use: outside_context. Population: Observed held-out original Type C in this tablet experiment
Prediction unit: new_context. Split family: context_holdout.
Split description: Leave original Type C out; nested PLS selection on the other Types. Reference/stress name this retrospective contrast only; no controlled split manipulation.
X-derived groups: False. Group basis/construction: declared_context / declared.
Transductive: False (declared/inferred from construction).

##### Dependency units and evidence

- 31 declared blocks (other): declared evidence; separated: yes. Reference: Public report /declared_blocks_preserved and /evaluation_scope; physical specimen/assay independence unknown..

##### Factor/context exclusions (relationships retained)

- original Type C (other): excluded: yes; relevant to intent: yes; declared evidence. Reference: Public report /contexts/1/source_type and /evaluation_scope. Relationship: Original formulation/context Type; not an instrument, genotype or whole independent experiment.

##### Referenced prediction metrics

- rmse: `/contexts/1/models/raw_pls/scores/value/rmse` in the original report (unchanged).

##### Spectral-support evidence

- Two train-fitted PC summaries only; evaluation projected without refit. Representation: raw/train-only PCA. Reference population: Other Types used to train the Type C holdout. Evidence: `/contexts/1/train_fitted_PC1_PC2_summaries`. Limits: Partial projection summaries are not full spectral support; context-specific PCA coordinates differ.
- Qualified continuous support unavailable. Representation: raw. Reference population: Type C training population. Evidence: `/contexts/1/continuous_support`. Limits: No low-risk interpretation from missing support.

##### outside_context

Conditions:

- If the objective is prediction outside the experimental context, match the tested novelty to that objective.

Supported:

- Existing prediction-error evidence describes the context holdout evaluation, conditional on the declared protocol.
- Declared exclusion of original Type C (other, declared evidence) describes prediction for the observed held-out levels only; it does not certify independence.

Not established:

- Universal external-population transfer, causal shortcut attribution and deployment-risk probabilities.
- Independence of unrecorded physical specimens or shared assay references.
- Unseen-population transfer from random/representative CV or X-derived clusters alone.
- New-experiment generalization from genotype, block or instrument holdout alone; those novelty types are distinct.
- Generalization to future unseen levels beyond the tested exclusions without representative independent evidence.

##### Missing information

- Referenced spectral support is unavailable at /contexts/1/continuous_support. Status: unavailable; reason: QUALIFIED_CONTINUOUS_SUPPORT_NOT_IMPLEMENTED_FOR_THIS_TASK.

##### Limitations

- Physical and assay dependencies remain unknown. Type-specific target ranges and training populations differ. These two context results do not isolate a causal split effect. No repeated fit or independent-database evidence is added.
- Spectral support applies only to each stated representation and reference population; a projection/range summary is not full support or a risk probability.
- Facts and evidence quality are caller declarations with report references; their provenance is not automatically verified.
- A categorical factor alone does not establish the need for a group split; no validation family is universally preferred.
- Known dependencies need not be exhaustive. No causal shortcut or probability of deployment failure is inferred.

### Stress deployment scope

#### Deployment-aware validation interpretation

Protocol: `domains.validation_intent.v1`. Report SHA-256: `0ea810ced51d38877a21d548798418b8361d9682d6b11ccef04d7be44dfeb247`.

Intended use: outside_context. Population: Observed held-out original Type A in this tablet experiment
Prediction unit: new_context. Split family: context_holdout.
Split description: Leave original Type A out; nested PLS selection on the other Types. Reference/stress name this retrospective contrast only; no controlled split manipulation.
X-derived groups: False. Group basis/construction: declared_context / declared.
Transductive: False (declared/inferred from construction).

##### Dependency units and evidence

- 31 declared blocks (other): declared evidence; separated: yes. Reference: Public report /declared_blocks_preserved and /evaluation_scope; physical specimen/assay independence unknown..

##### Factor/context exclusions (relationships retained)

- original Type A (other): excluded: yes; relevant to intent: yes; declared evidence. Reference: Public report /contexts/0/source_type and /evaluation_scope. Relationship: Original formulation/context Type; not an instrument, genotype or whole independent experiment.

##### Referenced prediction metrics

- rmse: `/contexts/0/models/raw_pls/scores/value/rmse` in the original report (unchanged).

##### Spectral-support evidence

- Two train-fitted PC summaries only; evaluation projected without refit. Representation: raw/train-only PCA. Reference population: Other Types used to train the Type A holdout. Evidence: `/contexts/0/train_fitted_PC1_PC2_summaries`. Limits: Partial projection summaries are not full spectral support; context-specific PCA coordinates differ.
- Qualified continuous support unavailable. Representation: raw. Reference population: Type A training population. Evidence: `/contexts/0/continuous_support`. Limits: No low-risk interpretation from missing support.

##### outside_context

Conditions:

- If the objective is prediction outside the experimental context, match the tested novelty to that objective.

Supported:

- Existing prediction-error evidence describes the context holdout evaluation, conditional on the declared protocol.
- Declared exclusion of original Type A (other, declared evidence) describes prediction for the observed held-out levels only; it does not certify independence.

Not established:

- Universal external-population transfer, causal shortcut attribution and deployment-risk probabilities.
- Independence of unrecorded physical specimens or shared assay references.
- Unseen-population transfer from random/representative CV or X-derived clusters alone.
- New-experiment generalization from genotype, block or instrument holdout alone; those novelty types are distinct.
- Generalization to future unseen levels beyond the tested exclusions without representative independent evidence.

##### Missing information

- Referenced spectral support is unavailable at /contexts/0/continuous_support. Status: unavailable; reason: QUALIFIED_CONTINUOUS_SUPPORT_NOT_IMPLEMENTED_FOR_THIS_TASK.

##### Limitations

- Physical and assay dependencies remain unknown. Type-specific target ranges and training populations differ. These two context results do not isolate a causal split effect. No repeated fit or independent-database evidence is added.
- Spectral support applies only to each stated representation and reference population; a projection/range summary is not full support or a risk probability.
- Facts and evidence quality are caller declarations with report references; their provenance is not automatically verified.
- A categorical factor alone does not establish the need for a group split; no validation family is universally preferred.
- Known dependencies need not be exhaustive. No causal shortcut or probability of deployment failure is inferred.
