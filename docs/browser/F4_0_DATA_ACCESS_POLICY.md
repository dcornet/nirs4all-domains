# F4.0 scoped browser policy — pre-implementation expectations

Base: F3.5 `f918da7d01e917936985e382b937acef221d2e89`. Only Domains changes;
Preflight =0.1.6 and Methods 1.3.13 / ABI 2.20 remain fixed. This document freezes
expected behavior before new implementation/tests. Old browser_x.v1 fixtures,
results and tolerances remain unchanged. New access/execution contracts are v1.

Import and execution are separate. IO/Formats own decoding, roles, keyed joins
and partition assembly; UI's published DatasetBuilder reviews declarations.
The local imported dataset retains X/Y/M, missingness, axes, original identities
and partitions. A technical unique row key is distinct from a declared source
identity; repeated source/specimen IDs are preserved, not silently renamed.
Ambiguous joins, source fusion, imputation and silent row deletion are refused.

## Operation permissions

| Operation | X values | M values | Y values | Fit |
|---|---|---|---|---|
| integrity_audit / exact spectra | train + test | documented identities only if required by owner | none | none; public Preflight only |
| integrity_audit / declared identities | none | selected identity/group/reference columns, train + test | none | none |
| metadata_factor_audit | none | selected train columns | none | none; documentary counts |
| cross_partition_metadata_audit | none | selected train + test columns | none | none; documentary counts/intersections |
| train_structure | train only | train grouping exclusions if explicitly declared | none | existing fixed PCA/HDBSCAN on train |
| train_reference_test_query | train reference + test query | declared exclusion groups only | none | none; existing raw-space neighbors |
| global_descriptive_transductive | explicitly selected train + test | declared groups only | none | full selected population; explicit consent |
| interpret_existing_evidence | no new values | no new values | none | none |

Prediction rows are retained at import and excluded from the train/test operations.
Unpartitioned sources retain the existing descriptive full-source route. No Y
value, including Y_train, is admitted to an F4.0 scientific request. A declared
Y-derived M column is ineligible for primary X-only interpretation/coloring.
No predictive fitting, target-driven choice, automatic tuning or causal/risk score.

Each operation request has a dataset/source/content/version binding, manifest of
technical row keys and declared partition roles, exact reference/query row keys,
X and M field grants, fit type, representation, frozen parameters and context of
use (before-selection audit or post-evaluation explanation). Payload values are
projected before worker posting. Rust validates grants, actual values/keys,
partitions, shapes, unique technical identities and budgets before owner calls.
Unknown/extra Y fields and train-fit test rows are refused. An operation refusal
does not erase the imported dataset or another successful operation.

The manifest is a declaration, not cryptographic isolation or proof of physical
identity. Provider spies must verify actual PCA/HDBSCAN input populations, distinct
neighbor query/reference matrices and zero forbidden Y/provider calls. Changing
Y_test or intended-use prose cannot change numerical evidence or trigger a fit.

Metadata counts, missing counts, cardinalities, categorical level counts and
literal set intersections are documentary presentation operations, not association
tests. No local eta-squared/correlation/test implementation. X–M associations,
quasi-duplicates and train-fitted PCA projection stay unavailable unless the pinned
public owner contract and actual execution can qualify them. Close spectra are not
physical duplicates; negative audits never certify independence. Inspecting X_test
can influence decisions even without Y_test; record access and prohibit automatic
selection/refit in response.

New operation receipts retain actual provider/status/reason/value, input/receipt
hashes, reference/query/fit populations, partitions and types/fields read, parameters,
test-X access and no-Y access, plus supported claims and limitations. Reports use
the existing F1/F2/F3.5 renderers, preserve original evidence and exclude raw X/Y
arrays. Global analysis requires a separate explicit action and separate receipt.

## Adversaries and numerical tolerances

Reordered keyed Y/M, ambiguous/missing/duplicate join keys, cross-partition source
IDs, missing metadata/targets, categorical and multiple targets, declared Y-derived
M, forbidden Y fields, wrong grants, mismatched manifests, hidden test fit rows,
explicit vs missing transductive consent, provider failure and stale population
results must be tested. No new tolerance relaxes historical numerical gates.
Exact counts/identities/access/JSON contracts and same-input repeats compare exactly;
cross-native/WASM numerical comparisons retain each existing owner tolerance.

## Frozen resource stages

Actual combined baseline: 20,821,363,073 / 20,826,468,033 bytes; 5,104,960 bytes
remain. Stage at most 3 MiB engineering (including Git/caches) and 512 KiB essential
receipts/images locally, within that unchanged ceiling. Campaign reservations stay
2,015,788,498 / 2,023,410,176 bytes; zero new scientific reservations. Preserve
2 GiB free per volume, all histories/journals and all source restrictions. No local
package install/native rebuild or large PDF/archive copy. Native/WASM builds and
clean candidate/browser/PDF tests run in existing hosted Windows/Ubuntu workflows;
inspect artifacts in memory and retain only small receipts. Stop for a measured
bound, without raising a ceiling or deleting historical evidence.
