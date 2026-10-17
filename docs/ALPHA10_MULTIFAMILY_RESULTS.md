# Estimator and pipeline sensitivity on the frozen Perten task

All six rows use the same 359 development specimens, 17 conservative context
blocks, moisture percentage-point unit, exact outer designs and group-safe
inner folds. The 91 retained outcomes remain sealed. Historical PLS/fixed Ridge
are preserved; all **2,154** historical anchor OOF predictions replay exactly.
Four prespecified new configurations execute without candidate failures.

| Pipeline | Reference RMSE | Cereal holdout | Instrument holdout | Cereal change from own reference |
|---|---:|---:|---:|---|
| Historical PLS, components 1–3 | 2.3873 | 5.0856 | 3.4918 | +2.6983 [1.7370, 3.7593] |
| Historical fixed Ridge, alpha 1 | 2.6166 | 2.8468 | 3.4336 | +0.2302 [−0.3408, 0.5521] |
| Nested-selected Ridge | 1.8781 | 2.9542 | 3.0356 | +1.0761 [0.3474, 1.5958] |
| Native SNV → nested PLS | 1.8221 | 3.0650 | 2.4471 | +1.2429 [0.4800, 2.2534] |
| nirs4all FastAOM hard chain | 2.0079 | 1.5000 | 2.0174 | −0.5079 [−0.9064, 0.1582] |
| nirs4all FastAOM sparse MKR | 2.5337 | 2.5958 | 2.0207 | +0.0620 [−0.2118, 0.3997] |

Intervals resample the same original context blocks for every prediction vector,
with 100 successful draws. They condition on these fitted OOF predictions. The
cereal closures are **209 barley/wheat specimens in 11 contexts**, versus **150
corn specimens in six contexts**. There are two transfer directions, not 359
independent unseen-category experiments. Uncertainty over hypothetical new
cereals and fitted-model/repeated-design variation remains unavailable.

The cereal interaction `(PLS stress − PLS reference) − (hard FastAOM stress −
hard FastAOM reference)` is **3.2063 [1.8164, 4.1940]** percentage points.
The instrument interaction is 1.0950 [−0.4534, 2.1955]. All 15 family-pair
interactions, both stress designs, matched null gains, MAE/R² and component-draw
digests are in [perten-summary.json](benchmarks/alpha10/perten-summary.json).
No favorable subset or model is selected for reporting.

Ridge selects alpha .01 in all three reference folds, .0001/.01 in cereal
folds, and .01/.0001/.0001 in instrument folds. Boundary selections are reported;
the grid is not expanded after seeing them. Fixed alpha 1 and this five-candidate
selection are different experiments, with substantially different reference
skill and stress deterioration. Hard FastAOM selects component caps 2/1/2,
3/2 and 3/3/3 respectively. Native SNV/PLS selects 3/3/3, 2/3 and 3/1/3.
Sparse MKR has a single external configuration and fixed lambda 1, with adaptive
training-only chain selection. Selected chains/bases/effective ranks are retained
for every adaptive fit; they are not interchangeable with selected PLS components.

## Complete-population training-size control

The alpha.9 greedy design's 38-ID/two-block result remains unchanged. A separate
[outcome-blind exact subset protocol](ALPHA10_SIZE_CONTROL_PROTOCOL.md) freezes
all six reference/cereal intersections before additional fitting. Whole context
components match the stress training count exactly at 150 or 209 specimens,
retain maximum available context diversity and cover **all 359 evaluation IDs**.
All six unchanged configurations execute; none drops a difficult cell.

| Pipeline | Exact-size reference RMSE | Cereal stress minus exact-size reference, 95% interval |
|---|---:|---|
| Historical PLS | 2.3635 | +2.7221 [1.7108, 3.8369] |
| Fixed Ridge | 2.7125 | +0.1343 [−0.3969, 0.4622] |
| Tuned Ridge | 2.0350 | +0.9192 [0.1975, 1.6083] |
| SNV/PLS | 2.3137 | +0.7513 [0.0827, 1.7101] |
| FastAOM hard chain | 1.7182 | −0.2182 [−0.5087, 0.0663] |
| FastAOM sparse MKR | 2.4182 | +0.1776 [−0.2312, 0.5103] |

Equal sample counts do not equalize cereal composition, context diversity,
target range, spectral support or unknown assay/farm dependencies. The additional
control limits a pure sample-count explanation; it does not identify a causal
shortcut effect. Original post-prediction target extrapolation counts remain
14/359 reference, 18/359 cereal and 21/359 instrument. No range-based selection
is performed. [Frozen IDs and results](benchmarks/alpha10/size-control-results.json)
remain separate from the original primary experiment.

## Measured computational cost

Single local Windows measurements, serial execution, BLAS thread limit one;
model fit counts include inner fits and selected refits. Native preprocessing
fits and adaptive internal base/chain operations are additional work.

| New pipeline / all three designs | Model fits | Whole execution seconds | Process peak resident MiB |
|---|---:|---:|---:|
| Tuned Ridge | 128 | 4.67 | 201.9 |
| SNV/PLS | 80 | 8.50 | 197.2 |
| Hard FastAOM | 80 | 7.49 | 232.0 |
| Sparse FastAOM | 32 | 8.81 | 230.0 |

Whole execution includes imports, orchestration, selection and prediction;
individual fit/prediction timings are stored separately. Process peaks include
imports and the lifetime high-water resident set, rather than incremental native
allocation. Hard FastAOM spends 0.467 s screening and 2.034 s fitting low-rank
bases across its 80 fits. Each fit enumerates nine compact depth-one chains,
screens 18 raw/SNV pairs and retains eight. The requested rank cap is 32; the
upstream code computes a full thin SVD before truncation.

The complete anchor replay measures 1.730 s PLS and .859 s fixed Ridge for
fit/selection, plus .0035/.0032 s prediction. Those subtotals exclude other
execution overhead and must not be compared directly to whole-execution times.
The additional exact-size experiment uses 324 model fits. Scoped tuned-Ridge/
hard-FastAOM replay adds 16/10 fits; complete anchor replay adds 112, beyond the
320 primary fits. No speed advantage over an exhaustive search is claimed:
no such search was run. Timing is one environment-specific observation.

Observation: estimator configuration and adaptive preprocessing change the
response to these same structural stresses. Confidence: exploratory, conditional
on the observed contexts and finite search budgets. Consequence: task structure
alone cannot predict every estimator's error response; favorable FastAOM scores
do not prove lower structural dependence or chemical causality. Action: retain
Perten in within-population comparison and structural-challenge suites, keep the
low-dependence suite empty, and obtain broader independent source support.
