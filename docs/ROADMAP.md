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

**Alpha.4 delivered:** EcoSIS freeze-dried X/LMA, verified 82 samples / 492 spectra,
six documented spectral replicates each, full 2151-band grid, conservative plot
splits (seeds 17/31/47), native and evidence-backed descriptive means. Public
FlexiblePCA retains the 390 primary train acquisitions; only native exact
effective dimension is unavailable for its full-moment budget. Held-out plot
bootstrap (500 draws) and paired train-PCA/fence refits (100 draws, all successful)
separate uncertainty sources. A bounded DAG-ML/Methods nested group PLS check
uses development means only and beats its fold-local null (RMSE 110.87 vs 146.99
g/m²). This is conditional, exploratory evidence, not production calibrability.
See REPEATED_DATA_PILOT.md and PREDICTIVE_SANITY_CHECK.md. Original biological and
laboratory identity limits remain explicit; no upstream repository was changed.

**Next concrete scientific lot: PCA–HDBSCAN stability.** Before tests, freeze
controlled separated groups, varying-density groups, continuum, all-noise and
small-N expectations; calibrate decision tolerances on those controls. Adapt the
existing public Methods ABI 2.19 HDBSCAN and ARI kernels without copying them.
Start with eligible train physical means, canonical identity order and an explicit
small parameter set. Refit train-only PCA and HDBSCAN in 100 deterministic 80%
whole-component subsamples without replacement. Compare partitions on common
physical IDs with native ARI, both including and excluding noise, plus noise
agreement and cluster membership support. Neighbor-density variation alone is
not evidence of clusters.

Return one explicit classification: robust structure when calibrated agreement
and support gates hold; fragile structure when fitted partitions change under
the frozen sensitivity design; continuum when qualified controls support absence
of discrete structure at the examined scales; insufficient information when
effective groups, common members or solver results cannot support that decision.
All-noise output alone cannot distinguish continuum from insufficient power.
Do not pick the most attractive cluster count after inspecting held-out data.

Compare native/mean partitions only after mapping to common physical identities
with an explicit acquisition-consensus/noise rule. Held-out X can be described in
the frozen train PCA space; HDBSCAN prediction or membership confidence requires
a separately verified public assignment API and qualification. Re-running
HDBSCAN on train+test is not held-out prediction. Keep those test assignments
unavailable if that API is absent. Paired multi-instrument analysis, conditional
confounding, AOM and spectral networks remain later lots.

The owner authorized repository creation and commit/push on 2026-10-16. This
continuation uses that authorization for the Domains repository only.
