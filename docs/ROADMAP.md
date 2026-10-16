# Roadmap and acceptance gates

| Phase / WP | Scope | Acceptance |
|---|---|---|
| 0 / WP0 | Audit, ownership, ABI and result contracts | Pinned source evidence, registry/runtime distinction, explicit absence states; delivered in this slice |
| 1 / WP0+8 | Workspace, CLI, synthetic train/test, JSON/Markdown, batch isolation | Native Methods execution, analytical values, deterministic artifacts, no test fit or pre-training Y_test dependency; evidence in VALIDATION.md |
| 2 / WP2+3 | Repetition aggregation, measured coverage and real dataset adapter | Equal physical-sample weighting in homogeneous acquisition contexts; no partition crossing; real canonical dataset/identity/split checks and retained exclusions |
| 3 / WP6 | Broader domain comparisons | Explicit paired/unpaired/instrument/campaign mode, compatible axes, reference-fitted geometry, uncertainty; MMD/energy only after upstream kernel/API audit |
| 4 / WP3 | PCA-HDBSCAN stability | Public Rust adapter to existing ABI 2.19; frozen ties/canonical order; subsampled units, ARI/noise agreement, held-out assignment with honest limitations |
| 5 / WP4+5 | Confounding and X-Y readiness | Conditional identifiability and restricted exchangeability; nested group OOF through audited DAG-ML public APIs; train-fold baseline and retained predictions |
| 6 / WP1 | AOM sensitivity | Train/development-only nested selection; canonical and aom:<target> views remain separate; cluster stability/noise/ARI comparison only |
| 7 / WP8+9 | Broader qualification campaign | Three contrastive real cases acquired legally via Datasets, exact versions/identities/splits/seeds retained, errors per task, evidence-derived scientific recommendations |
| Extension / WP7 | Spectral graphs and advanced Y mixtures | Generic kernels upstream, threshold/bootstrap sensitivity, no universal score |

WP9 is a gate in every phase. A passing test for an unavailable future module is
not a scientific qualification of that module.

**First real task delivered:** Shootout X1/assay, native calibration/test mapping,
155 train and 460 test observations, 40 validation observations explicitly excluded.
The local raw reproduction runs through public Datasets getters and yields
identical reports on repeated execution. Target units, source hashes, engine
versions, identity assumptions and remaining pilot blockers are preserved. See
[qualification and limits](REAL_DATA_PILOT.md). Historical registry canonical
byte/numerical parity remains unverified; original laboratory reference IDs are
not available.

**Next concrete gate:** qualify technical-repeat aggregation on homogeneous
source/instrument/campaign contexts through Preflight's public protocols. Inspect
the existing averaging seam first; do not copy intrinsic aggregation into Domains.
Acceptance: unchanged weight when a technical repeat is duplicated, no averaging
across partitions or heterogeneous contexts, explicit exclusions and reference
identity transport that does not need Y_test. A grouped real task can only be
enabled after its physical/reference identities and split policy are documented.

Remote publication is a separate user-confirmed action. The initial request
explicitly requires confirmation before repository creation or first push.
