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

**Alpha.3 delivered:** dependency components, reference safety scoped to X-Y,
native/context-linked inventories, optional homogeneous technical means via
Methods summaries, one physical-sample vote, explicit exclusions/populations and
adversarial tests. Shootout native and technical_mean reports have identical
fits and four scalar metrics: there are no declared within-X1 repeats. Original
physical/reference independence remains unverified. The private Preflight
averaging seam was inspected; a public representation API is proposed in
UPSTREAM_DEPENDENCIES.md, without blocking the local task protocol.

**Next concrete scientific lot:** coverage on documented independent validation
units. Select one legally available grouped real task with physical/reference
IDs, context and a frozen group split; qualify transitive component exclusions
for neighbors and coverage denominators, compare native/context policies, and
define uncertainty resampling whole independent components. Do not infer those
identities from Shootout aliases. Paired multi-instrument coverage remains
unavailable until that design is specified. Only then proceed to PCA-HDBSCAN
stability; nested PLS/PCR, confounding, advanced shift and AOM stay deferred.

Remote publication is a separate user-confirmed action. The initial request
explicitly requires confirmation before repository creation or first push.
