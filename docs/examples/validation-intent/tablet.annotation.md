## Deployment-aware validation interpretation

Protocol: `domains.validation_intent.v1`. Report SHA-256: `0ea810ced51d38877a21d548798418b8361d9682d6b11ccef04d7be44dfeb247`.

Intended use: outside_context. Population: Held-out Type contexts within UCPH tablet development data, active substance percent mass/mass, X content 1.0.0. Future contexts remain unvalidated.
Prediction unit: new_context. Split family: logo.
Split description: Four outer leave-one-original-Type-out folds, three inner remaining-Type folds; all 31 declared canonical blocks preserved. Not leave-one-experiment-out.
X-derived groups: False. Group basis/construction: declared_context / declared.
Transductive: False (declared/inferred from construction).

### Dependency units and evidence

- 31 declared canonical blocks (other): verified evidence; separated: yes. Reference: docs/ALPHA17_TABLET_PILOT_PLAN.md; tablet-pilot-summary.json declared_blocks_preserved.
- Physical specimen (specimen): unknown evidence; separated: unknown. Reference: unspecified.
- Original assay event/shared reference (assay_reference): unknown evidence; separated: unknown. Reference: unspecified.

### Factor/context exclusions (relationships retained)

- Type (other): excluded: yes; relevant to intent: yes; verified evidence. Reference: docs/ALPHA17_TABLET_PILOT_PLAN.md; tablet-pilot-summary.json original_contexts and contexts. Relationship: Canonical blocks nested within original Type; Type/Scale source categories do not establish physical or experiment identity.

### Referenced prediction metrics

- rmse: `/pooled_outcomes/raw_pls/model/value/rmse` in the original report (unchanged).
- rmse: `/pooled_outcomes/raw_ridge/model/value/rmse` in the original report (unchanged).

### Spectral-support evidence

- Existing train-fitted PC1/PC2 projection summaries for held-out Type A; no PCA is recomputed. Representation: Raw spectra; PCA centered/fitted on the corresponding training fold. Reference population: Type A fold training population, excluding Type A. Evidence: `/contexts/0/train_fitted_PC1_PC2_summaries`. Limits: Two projections do not establish full spectral support; other contexts have their own summaries.
- Qualified continuous support is explicitly unavailable in the source report. Representation: raw. Reference population: Type A fold training population. Evidence: `/contexts/0/continuous_support`. Limits: Do not substitute a truncated-PCA moment estimate or interpret support as a risk probability.

### outside_context

Conditions:

- If the objective is prediction outside the experimental context, match the tested novelty to that objective.

Supported:

- Existing prediction-error evidence describes the logo evaluation, conditional on the declared protocol.
- Declared exclusion of Type (other, verified evidence) describes prediction for the observed held-out levels only; it does not certify independence.

Not established:

- Universal external-population transfer, causal shortcut attribution and deployment-risk probabilities.
- Independence of unrecorded physical specimens or shared assay references.
- Unseen-population transfer from random/representative CV or X-derived clusters alone.
- New-experiment generalization from genotype, block or instrument holdout alone; those novelty types are distinct.
- Generalization to future unseen levels beyond the tested exclusions without representative independent evidence.

### Missing information

- Dependency separation/evidence is incomplete for Physical specimen.
- Dependency separation/evidence is incomplete for Original assay event/shared reference.
- Referenced spectral support is unavailable at /contexts/0/continuous_support.

### Limitations

- One exploratory development population; unknown physical/assay dependencies prevent independent-generalization claims.
- The existing pooled scores hide context variation; Type A has negative R2 and target-range extrapolation for both models.
- Full-source X descriptors elsewhere in the source report have a different scope from train-fitted diagnostics; they did not select these models.
- No matched random-CV contrast, stress/control design or test of frozen H1-H5 is supplied.
- Spectral support applies only to each stated representation and reference population; a projection/range summary is not full support or a risk probability.
- Facts and evidence quality are caller declarations with report references; their provenance is not automatically verified.
- A categorical factor alone does not establish the need for a group split; no validation family is universally preferred.
- Known dependencies need not be exhaustive. No causal shortcut or probability of deployment failure is inferred.
