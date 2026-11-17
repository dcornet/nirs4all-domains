# F4.0 partition audit and operation scopes

This is a protocol and report contract, not a claim that browser execution is
qualified. Import, operation authorization, provider execution and report
presentation are separate stages. IO/Formats own decoding, role declarations,
keyed joins and partition assembly. The browser report records what was loaded
separately from what each operation analyzed.

## Populations

Each imported row retains a technical unique key, optional declared observation
identity, current partition role and original partition declaration. Technical
keys support exact joins and receipts; they do not assert physical identity.
Repeated declared identities remain repeated and are not silently rewritten.
Prediction partitions remain in the loaded inventory but are excluded from
train/test operations.

`train` is the only population allowed to fit train structure. Test observations
can be query rows for the train-reference/test-query operation, but test X
access is recorded. Y is forbidden for every F4.0 operation, including
Y_train. No test fit, predictive fit, target-driven selection, automatic tuning
or choice of split occurs.

The global descriptive/transductive operation requires its own explicit user
selection and consent. It has a separate receipt and is never inferred from a
missing partition, absent split, or generic analyze action. An unpartitioned
source continues to use the existing descriptive full-source route. This does
not establish that its observations are independent.

## Operation-specific scope

| Operation | Data access and population | Interpretation boundary |
| --- | --- | --- |
| `integrity_audit / exact_spectra` | X for train and test; no Y; only documented identity metadata when required | Exact spectral duplicate evidence, not physical identity or independence |
| `integrity_audit / declared_identities` | Selected declared identity/group/reference metadata for train and test; no X or Y | Declaration consistency and overlap; declarations are not verified physical truth |
| `metadata_factor_audit` | Selected train metadata columns only; no X or Y | Documentary counts, missingness and levels; not an association test |
| `cross_partition_metadata_audit` | Selected train and test metadata columns; no X or Y | Documentary counts and literal intersections; not a leakage rate or risk score |
| `train_structure` | Train X only; optionally explicit train group exclusions; no Y | Existing fixed PCA/HDBSCAN evidence on train; descriptive structure only |
| `train_reference_test_query` | Train X reference and test X query; only declared exclusion groups as authorized; no Y | Existing raw-space neighbor evidence; query/reference scopes stay distinct |
| `global_descriptive_transductive` | Explicitly selected train plus test X; declared groups only; no Y | Full selected population descriptive evidence, explicitly transductive |
| `interpret_existing_evidence` | No new values; no X, M or Y access | Recontextualizes existing evidence only |

The exact Preflight `cross_partition_exact_duplicate_pairs` metric excludes
pairs with equal declared physical IDs. Same-physical identity overlap is
reported separately. Exact spectral duplicates and same-physical overlap are
distinct observations. A negative audit never certifies independence.

## Refusals and report rules

Each operation has independent validation and a local status/reason. A refusal
does not erase imported data or another operation's result. Reports show loaded
counts separately from operation-specific fit/reference/query counts, preserve
the exact access declaration and provider receipt, and include supported claims
and limitations. They do not substitute a global score or a new scientific
conclusion.

Raw X/Y arrays are not exported. The safe inventory exposes counts and field
declarations only. The F1/F2/F3.5 renderers remain the presentation surface;
existing saved evidence and legacy behavior remain separate and unchanged.

Provider qualification, WASM integration, leakage/adversarial checks and export
checks remain pending until their execution receipts are recorded. This page
documents expected protocol behavior and does not treat CI configuration as
execution proof.
