# First exploratory original-keyed pilot — approved and executed 2026-10-19

The frozen local packet is `alpha17/ORIGINAL_KEYED_TABLET_PILOT_FREEZE.json`.
The owner explicitly approved this exact packet on 2026-10-19. The run is complete;
[results](ALPHA17_TABLET_PILOT_RESULTS.md) record every context and both anchors.
The protocol below was frozen before numerical target decode and fitting. The
controller requires the signed task-specific decision and reuses Methods/DAG.

The task is **UCPH tablet NIR, X, content 1.0.0**, active substance **% mass/mass**.
Keep all **310 development observations and 404 spectral bands**. The
[original source page](https://ucphchemometrics.com/tablet/) calls the download
development data and identifies Dyrby et al. (2002). The existing alpha.13 audit
verified exact float32 X/axis parity through explicit original record keys.
Join canonical `observation_id` through M's `source_sample_id` to the original
record key; read its co-located `active (%w/w)` field only after approval.
The unkeyed canonical Y table is unused. Cached content proof does not establish
original assay/specimen independence.

Metadata-only verification finds four original Type contexts (70/80/80/80 rows)
and 31 declared canonical blocks, all nested within Type. Preserve every block.
Freeze four outer leave-one-Type-out folds, each with three inner
leave-one-remaining-Type-out folds. Exact identity rosters and validated FoldSets
stay local. `by_batch_grouping_documented_not_applied` is a grouping recommendation,
not a list of retained test members; no existing retained partition is repurposed.
Scale metadata agrees by key. Type/Scale are source categories, without a claim
that all hidden dependencies have been identified.

Raw PLS components **1,2,3** and raw Ridge alphas **.01,.1,1,10,100** remain fixed.
Fit centering, model selection and refit within each native training scope.
The actual FoldSets imply **4 × (3 × 8 + 2) = 104 model fits**. Separately allow
four Methods FlexiblePCA fits with 20 components, fitted on each outer training
set and used to transform its evaluation X without refitting. PC1/2 summaries
are descriptive; continuous-support scores and exact full moments are unavailable
for this task. No truncated-PCA moment substitute is allowed.

Report pooled and per-context RMSE/MAE/R², training-only null error and
`S = 1 − RMSE/RMSE_null`, target-range extrapolation, selected parameters,
lineage and failures. Keep frozen raw/SNV X descriptors as prospective comparators;
do not choose descriptors from outcomes. H1–H5 remain unchanged. This single
exploratory reference design has no matched stress/control contrast: `D_RMSE`
and `D_skill` remain unavailable. Four contexts do not provide independent-study
uncertainty, a causal shortcut fraction or independently validated generalization.

Proposed additional cost: **8 MiB cumulative reservation** (4 MiB scratch,
4 MiB essential evidence) and **64 MiB maximum additional combined footprint**,
inside the existing alpha.17 envelope and unchanged global ceilings. After the
approved eight-view X allocation, campaign reservations are 796,261,842 bytes;
the pilot would reach **804,650,450**, leaving **655,918 bytes**. Execute one task
at a time, preserve 2 GiB free on participating volumes, and stop at **1 hour or
1 GiB process RAM**. These are prospective operating limits; real source-specific
runtime and native memory peaks have not been measured. The feature-array payload
alone is about 1 MiB and is not an estimate of total process memory.

Before fitting, verify whole-file, source-proof, controller, provider and bridge
hashes. Refuse changed keys/scopes or any nonfinite/missing X/Y; retain all rows
or fail the task. Preserve partial evidence and reservations. No automatic
retry/refit, source substitution, performance-based stopping, SNV model, B60,
TabPFN, acquisition, cleanup, migration or ceiling increase. Ordinary permitted
aggregates may be public; raw X/Y, record keys, folds and OOF vectors stay local.
