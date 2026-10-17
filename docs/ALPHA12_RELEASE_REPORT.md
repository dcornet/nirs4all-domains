# Alpha.12 — robust unsupervised structural characterization

Baseline `e8385bf4aa3125d6f6ffadd5e63d080d14a02b44`, 173 tests and 224 previously
protected artifacts. Alpha.12 keeps all previous results and extends the local
preservation map to 371. This release investigates observable structure in X;
target association and demonstrated predictive dependence remain separate.

## A — Public coverage

All 42 pinned public entries remain in the [matrix](benchmarks/alpha12/structural-matrix.json).
Thirty-nine have complete-population raw/SNV profiles (78 fits), 37 have variable
declared metadata factors, and seven have actual conditional resampling.
Two public EcoSIS rights endpoints were resolved; two malaria entries remain
unavailable and one simulated molecular entry is ineligible. Four historical
physical-ownership admissions and two directly rechecked original-key namespaces
do not establish an independent-study count. The hierarchy preserves unknowns.

## B — Geometrical characterization

Raw/SNV median first-PC fractions are .6821/.7410; median retained fractions
are .999662/.998666, with minima .902412/.860757. Exact participation-ratio
dimension is available for 12 sources each, median 1.7535/1.8066; 27 each remain
unavailable. Primary cluster counts range 0–32/0–37 with median two. These are
parameter-specific fragments, not verified populations. Full-axis density and
multi-scale proximity supplement PCA/clustering without forcing discrete labels.
See [comparative results](ALPHA12_CROSS_DATASET_RESULTS.md) for distributions,
denominators and continuous-geometry interpretation limits.

## C — Representation sensitivity

On identical populations, median raw/SNV primary ARI is .2390 (37 nontrivial
comparisons; two unavailable) and median mean k=8 overlap .3305 (39 sources).
Noise/group/variance changes are retained per setting. No nuisance-removal,
chemical-identification or predictive benefit follows from these changes.
The [standalone figure](benchmarks/alpha12/figures/representation-sensitivity.svg)
uses only dimensionless/source-scoped descriptors and identifies sampled queries.

## D — Neighborhood evidence

There are 22 exact complete-source censuses, up from 12 in alpha.11, plus 17
prespecified query-subset descriptions. Each query sees every reference row and
band. Total exact work is bounded at 750 million products, 250 million per call;
batching reduces transport memory without removing all-pairs complexity.
Distances are normalized within source/representation by sqrt(full trace).
Seven radii and k=1/4/8 are fixed. Partial-query bootstrap describes query-sample
sensitivity, not biological uncertainty or exact unobserved-tail precision.
[Detailed modes, limits and upstream proposals](ALPHA12_NEIGHBORHOOD_COVERAGE.md).

## E — Structural stability

Seven prespecified views complete 560 PCA refits and 1,120 HDBSCAN attempts.
Among 56 combinations there are four operationally robust, two fragile and 50
insufficient-information outcomes. No source meets every combination. Forty-eight
combinations lack pair support; quality and eligible-ARI failures overlap.
Twenty .6 draws provide limited joint exposure even for stable pairs, so no
blanket instability conclusion is warranted. Thresholds were not relaxed.
Cartilage samples complete location blocks; other sources use observation-level
algorithmic subsampling. None gives biological sampling uncertainty.
[Full stability findings and design-power limitation](ALPHA12_STRUCTURAL_STABILITY.md).

## F — Cross-dataset synthesis

The bank has 38 vegetation views and one qualified Cartilage view. Related
preparations/revisions and 70 cited-reference groups are not independent studies;
study-level prevalence remains not identifiable. Source-family and verified-key
namespace strata preserve this imbalance rather than pooling raw distances.
Original litter views match 321 objects by ID from parents 322/321, with one
intact-only object preserved. Raw/SNV primary cross-view ARIs are .09585/−.01407,
neighbor overlaps .13980/.24494: same-object preparation effects, not generalization.
Metadata have missingness/cardinality/semantics/weighting caveats and corroborate
X geometry without supplying target labels. [Machine-readable findings](benchmarks/alpha12/findings.json).

## G — Future supervised hypotheses

[H1–H5](ALPHA12_HYPOTHESIS_REGISTER.md) freeze separation, proximity,
representation sensitivity, continuous support and identity uncertainty predictors.
[Future outcomes](ALPHA12_FUTURE_OUTCOME_CONTRACT.md) define paired RMSE/skill
changes and estimator interactions, controlling training size, group support,
target range, study, preprocessing and model family. EcoSIS, Perten and litter
are exploratory. Untouched confirmation needs original-study/population separation
and locked definitions before responses; retain contrary cases as falsification.

## H — Remaining source limitations

Official public Belgian dunes ODbL and Alberta CC BY-SA metadata are matched to
original package IDs and authors; no spectra were acquired or redistributed.
Their admission is separate from the initial read-only re-audit. Malaria custom
terms remain inaccessible. ChEMBL Raman part1 v3 CC BY 4.0 is verified, but other
scope, simulated MIR/Raman modality and full-population cost prevent admission.
Drydown's prior PDDL correction is preserved. Physical/biological/assay closure,
uniform original intensity units, full moments and calibrated continuum semantics
remain limited. CORN stays pending its previously missing authorization.

## I — Resources and preservation

Real X-only work uses 642 PCA fits and 1,284 HDBSCAN attempts: 78 reference,
560 resampling and four paired-view PCA fits. The separate 16-mechanism,
18-case control suite uses 57 PCA and 114 clustering fits including its .8
positive control. Test-provider calls are separate. **Zero new real supervised
model fits, zero TabPFN fits/weights downloads.** Full-source matrices stay in
existing authorized caches; compact stages retain no source X, loadings or scores.

Primary callback time sums 299.62 s; measured main profile phase wall time is
685.21 s, excluding separately completed sentinel reference work. Remaining
400-draw phase wall time is 837.62 s. Sentinel 160-draw callbacks sum 244.06 s,
with 1,095.69 s observed first-to-last admission span, not full launch time.
Paired phase wall time is 37.17 s; its actual Python-worker peak is 279,900,160
bytes, excluding Rust. Primary/rest-stability original counters measured the
venv launcher; explicit corrections leave actual worker peaks unavailable.
Separate Rust peaks remain unmeasured; <1.5 GiB is an estimate, not a quota.

The owner approved workspace ceiling 13,873,678,017 bytes. Serial 512 MiB campaign,
256 MiB/task, 4 MiB evidence/task and 2 GiB free reserves remain unchanged.
No deletion/migration/upstream modification occurred. Exact providers, executed
source hashes/contracts, byte measurements and corrected counter scopes are
published with the storage/validation audits. Reconstruction requires exact
caches; portable integrity checks do not claim a full raw-source archive.

## J — Validation and bounded next phase

Local checks and package/source parity are recorded in
[validation proof](audit/alpha12-validation.json); actual hosted execution is
recorded separately after push. The suite retains all 173 baseline tests and adds
52 Python tests, for **225 passing tests (35 Rust + 190 Python)**. A first full
Python attempt exposed an unsuitable rank-one batching fixture; its corrected
analytic fixture and rerun are preserved in the execution log. No real science
or thresholds changed. CI configuration alone is not execution proof.

All 18 local release checks pass, and the 97,049-byte wheel matches every packaged
source/schema and imports in isolation. The local snapshot is 13,675,921,814
workspace bytes under 13,873,678,017; cumulative reservations are 427,393,916
bytes under 536,870,912. Maximum new-task essential evidence is 2,047,799 bytes
under 4,194,304. All 371 protected files verify. Public manifest and executed-source
checks are additional final gates. Hosted CI and commit identity are recorded
after actual push/completion.

Twenty-eight older audit JSON files have existing CRLF working-copy/LF Git-blob
variants. The local preservation map remains frozen; an additive baseline
encoding proof confirms the sole newline difference for portable validation.
Historical files and repository content are unchanged.

Alpha.13 should first calibrate pair-panel exposure on controlled X and resolve
study/biological closure. Then propose a small separately admitted confirmatory
supervised campaign under H1–H5, with untouched study units and explicit power,
split, size/range and estimator controls. Further TabPFN work remains deferred.
