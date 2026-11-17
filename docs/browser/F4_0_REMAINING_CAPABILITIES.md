# F4.0 remaining capabilities and evidence boundaries

This matrix distinguishes implemented request paths from provider/API
availability and scientific qualification. It makes no hosted CI, clean-build,
or end-to-end runtime-success claim. The applicable contract is frozen in
[F4.0 data access policy](F4_0_DATA_ACCESS_POLICY.md); read alongside
[native/WASM compatibility](F4_0_NATIVE_WASM_COMPATIBILITY.md).

| Capability | Current scoped path or public API | Remaining boundary |
|---|---|---|
| Import review and X/Y/M retention | IO/Formats inference and assembly; shared UI `DatasetBuilder`; Domains adapter retains role-reviewed nullable X, Y and M | IO/UI declarations do not establish scientific identity. Current local UI installation is 0.2.1 while the manifest pins 0.2.5; verify the pinned artifact separately. |
| Exact spectra and declared-identity integrity | Scoped `integrity_audit` has distinct exact-spectra and declared-identity diagnostics; exact spectra delegates to Preflight 0.1.6 with numerical methods unavailable | No tolerance duplicate threshold is selected. Negative findings do not certify independence. Intrinsic alpha availability/execution does not establish qualification. |
| Train structure | Scoped `train_structure` passes the selected train rows to existing raw PCA/density support path | This is a descriptive X fit. Its utility and scientific scope remain separate from physical independence or predictive performance. |
| Raw train-reference/test-query support | Scoped query uses raw train reference and test query with public nearest-neighbor API | Train-fitted PCA projection, tolerance-based duplicates, and wider support claims remain unavailable or unqualified. Test-X access can affect decisions even though no Y is admitted. |
| Metadata factor counts | Scoped `metadata_factor_audit` reports row counts, missing counts, cardinality and level counts; cross-partition audit also reports literal shared nonmissing values | These are documentary descriptions, not association tests. Do not infer X-M association or causality from them. |
| Metadata association provider APIs | Methods 1.3.13 declares factor-target permutation and exact tests, plus numeric correlation tests | The scoped metadata-field protocol, exchangeability/dependency rules, field grants and adversarial association tests are not qualified. Availability is not evidence of scoped execution. |
| Train-fitted PCA query transform | Methods declares generic `FlexiblePCA.fit` and `.transform`; current browser diagnostic calls `preflightPca` for a single result | The fitted-state handoff, train-only fit population, query transform, receipt lineage and adversarial leakage checks are not qualified for this F4.0 path. |
| Global descriptive transductive structure | Scoped operation requires explicit transductive consent and labels the fit as transductive | It cannot support prospective train-only claims or automatic validation selection. |
| Y handling | Import may retain Y locally for inventory and masking; scoped requests require an empty `y_fields` grant and receipts state `y_accessed: false` | No Y values are passed to scoped operations. No predictive fitting, target-driven selection, or calibration score is added. |
| Repeatability and further inference | Public Methods declarations include other diagnostics and procedures | Scoped browser provider returns `NO_BROWSER_REPEATABILITY_PROTOCOL`; those other operations have no F4.0 scoped contract or qualification here. |

Operation receipts and unavailable reasons are evidence about the implemented
request path. They are not evidence that an operation is useful in a broader
population, that units are independent, or that a validation choice is
appropriate for every intended use. Hosted CI and native/browser execution
remain separate verification steps.
