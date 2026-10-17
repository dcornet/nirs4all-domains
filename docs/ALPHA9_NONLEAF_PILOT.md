# Perten cereals: a new non-leaf real task

One new task is admitted: **Perten X / oven Moisture**, distinct from EcoSIS.
The [frozen admission](benchmarks/alpha9/perten-admission.json) precedes prediction.
Source: sensAIfood/Perten, curated by Dario Passos, Zenodo version 1,
[DOI 10.5281/zenodo.15838136](https://doi.org/10.5281/zenodo.15838136), CC-BY-4.0.
The private catalog tier and LicenseRef declaration were stale relative to the
official API. This is an evidence-backed local task decision; upstream is unchanged.

All **450 specimens / 141 channels** remain: 359 development specimens in 17
context blocks, 91 sealed retained specimens in five blocks. The whole
instrument-model/country/year tuple defines a conservative experimental block,
not a verified original batch. The original 450 CSV IDs are unique. The repeated
1–150 row counters across cereals are not physical identities. Source XLSX notes
report no duplicates. The local standardized Y lacks observation keys, so it is
ignored. A tested adapter joins original CSV ID → original specimen → observation
key before Datasets canonicalization. No positional X/Y join is used.

Original laboratory assay event IDs, reference precision, farm/harvest links and
instrument serial numbers remain unknown. Moisture units are source percent;
the spreadsheet's wet/dry-basis wording is ambiguous. No basis conversion is
applied. Country may denote growing or measurement location. Missing instrument
model has an explicit unknown-model stratum. Source descriptors are declarations,
not proof of independent farms or independent assays.

Native Preflight reports valid input, zero missing spectral cells, ascending
axis, zero cross-physical and cross-partition exact spectral duplicate pairs.
There is one supplied spectrum per specimen, so repeatability is not applicable.
Train-fitted Methods FlexiblePCA retains **two PCs / 99.4187%** of full variance;
exact effective dimension is **1.16423**. The train-only coverage heuristic flags
**19/91** retained X rows. Retained Y is never used. These flags do not predict
calibration failure. See [intrinsic/geometry evidence](benchmarks/alpha9/perten-intrinsic-and-geometry.json).

Descriptive native physical-unit association (359 complete development records):

| Factor | Eta-squared | 95% whole-context interval |
|---|---:|---|
| Cereal | 0.04537 | [0.00231, 0.25689] |
| Country | 0.34455 | [0.15843, 0.63707] |
| Instrument-model stratum | 0.11695 | [0.01021, 0.38778] |

There are 100 successful component draws per association. Marginal association
is not predictive reliance or causal attribution. Country ambiguity and sparse
instrument strata constrain interpretation. The frozen PCA–HDBSCAN stability
workflow returns `insufficient_data`: it requires 30 physical samples **and 20
components**, while this development population has 17 components. No cluster
fits or 500 successful resamples are claimed. The threshold is preserved.

Development-only native DAG-ML nested grouped CV, three outer / three inner
folds, PLS components 1–3, fold-local centered X/Y without scaling:

| Evaluation | Null RMSE | Cereal-only RMSE | Spectral PLS RMSE | Cereal + residual PLS RMSE |
|---|---:|---:|---:|---:|
| Context-safe reference | 3.35315 | 3.96845 | **2.38729** | 2.83506 |
| Cereal closure holdout | 3.43017 | 3.43017 | **5.08562** | 5.37679 |
| Instrument-model closure holdout | 3.46085 | 4.02011 | **3.49175** | 3.98283 |

All RMSEs are in source moisture percentage points, on the same 359 physical IDs.
Reference spectral R² is **0.48376**. Spectral-over-null paired RMSE gain is
0.96586, with 95% context-block interval **[0.13430, 1.76582]**. Cereal-only
prediction is worse than the null; descriptive cereal association does not imply
a useful cereal predictor under this split. Residual-over-group gain has interval
[0.26132, 1.74753], but residual prediction remains worse than spectral PLS.

PLS degradation relative to reference is **2.69833 [1.73698, 3.75934]** for cereal
holdout and **1.10446 [0.30939, 1.81983]** for instrument-model holdout. Cereal
closure leaves only **two** units because some conservative contexts link cereal
levels. Instrument closure has six strata including unknown model. The intervals
resample the original 17 context blocks, condition on frozen OOF predictions,
and exclude refit and population-of-unseen-cereals uncertainty.

Target extrapolation, evaluated after prediction, affects 14/359 reference,
18/359 cereal-holdout and 21/359 instrument-holdout outcomes. The size control
has six cells: five unavailable due to whole-block granularity and one exact
209-training-sample match. Its evaluation intersection contains only **38
specimens / two blocks**: size-controlled RMSE 2.91704, original reference 3.21646,
cereal holdout 7.22153 on those same IDs. Its uncertainty interval is unavailable
for fewer than ten components. This partial intersection cannot separate the
all-359 deterioration from training-size, composition and extrapolation effects.

Three global and three within-cereal interventions are retained as unavailable.
Eleven of 12 required scopes fail global exchangeability/power gates; all 12 fail
within-cereal gates. Some scopes have zero movable targets; the largest
within-cereal swappable support is two components. Unequal complete-vector sizes
prevent the required >=50% movable fraction and >=6 compatible components.
There are **zero effective attempts**, not evidence of independence or zero effect.

Purpose: **structure_sensitive_challenge**, with a subsequently frozen secondary
family comparison. This is exploratory qualification within explicit identity
assumptions, not production calibration or a low-dependence certificate.
The [compact record](benchmarks/alpha9/perten-evidence.json) preserves OOF,
denominators, statuses, scoped digests, associations and uncertainty without X,
PCA score matrices or model payloads. One 103-prediction outer fold replays
exactly; this does not claim a second complete campaign.
