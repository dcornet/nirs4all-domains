# EcoSIS split stress and training-target interventions — alpha.7

Executed 2026-10-17 with Methods 1.3.6 / ABI 2.19 and DAG-ML 0.3.41. The frozen
task remains freeze-dried source X / LMA g/m², 65 physical means / 45 declared
plot components, all 2151 bands. Retained test labels remain sealed. Alpha.6
seed-17 genus OOF predictions/folds/lineage are reused exactly, not re-fitted.
All other results below are executed alpha.7 experiments, not proposed values.

## Design and intervention audit before model execution

Genus has 15 observed levels (four missing values), but closure gives **14
holdout units**, not 15 independent genera. The largest closure has 13 samples /
eight original components. Dates give nine closure units; source species
epithets give 28 but receive an audit only under the bounded schedule.
Every known held-out factor level is absent from its outer train, and every
plot/reference component remains indivisible. Missing-only blocks remain
unknown units rather than a fabricated genus.

The source guide defines plot greater-area codes. Dates July 1–5 contain only
SL in this development population, July 6–7 only YV, and July 8–9 only HH.
These codes describe confounding; no coordinates are binned and no new region
predictor is created. Date holdout is neither a clean geographic intervention
nor necessarily new-region transfer.

Global equal-cardinality/reference-pattern block exchange passes every inner
and outer scope. Within-genus exchange fails the frozen 50% movable-target gate
in `outer:0:inner:0` (9 swappable components, 29.03% targets) and
`outer:1:inner:1` (10, 40%). Other scopes cannot compensate for those failures.
All 19 scheduled real within-genus attempts are explicitly unavailable; none is
redrawn, assigned a zero score or interpreted as independence/mediation.
See [the pre-experiment audit](audit/alpha7-pre-experiment-design.json).

## Matched all-development split results

All rows below predict each of the same 65 outcomes once. The predictor factor
remains genus, including under date holdout; only the outer split changes.
Every model retains the same grid 1–5, fold-local centering and three inner
component folds. Seed variability is reported separately from fixed-OOF CIs.

| Design | Null RMSE | Genus-only RMSE | Spectral PLS RMSE | Genus + residual RMSE |
|---|---:|---:|---:|---:|
| Reference 17, frozen alpha.6 | 146.993310 | 114.780941 | 110.867765 | 101.346279 |
| Reference 31 | 145.282443 | 112.366671 | 106.180578 | 100.804850 |
| Reference 47 | 144.411311 | 115.844215 | 110.094508 | 99.374491 |
| Reference 61 | 144.119641 | 111.026851 | 85.752386 | 106.425633 |
| Reference 79 | 145.481446 | 117.962872 | 92.810657 | 104.663573 |
| Reference 97 | 144.632872 | 111.260137 | 115.038339 | 107.847299 |
| Seeded component shuffle 17 | 146.446030 | 111.792024 | 107.782376 | 105.346599 |
| True genus closure holdout | 160.995214 | 160.995214 | 142.722764 | 151.836499 |
| Date closure holdout | 150.380985 | 126.103776 | 95.355025 | 105.637156 |

Units are g/m². The five sensitivity seeds were prespecified; none replaces the
primary seed. Reference spectral RMSE varies from 85.75 to 115.04, and residual
models do not uniformly beat ordinary PLS across seeds. These are separate CV
experiments, not draws pooled into a single confidence interval.

Genus holdout trains on 57/44/59/41/59 samples and 37/32/41/29/41 components,
versus 50/54/53/53/50 samples and 36 components per reference fold. All 65 genus
baseline predictions fall back, including missing/unknown labels. Spectral
degradation versus reference is **31.8550**, paired 95% interval
[14.4468, 53.0670]; residual degradation **50.4902**, [25.9752, 76.8796]. Even
the null worsens by 14.0019, [6.7065, 21.0113], indicating changed target
composition. Date-holdout spectral change is −15.5127, interval
[−44.8331, 7.9096]; it does not demonstrate a reproducible degradation.

## Training-size controls and target-range alternatives

Each matching draw has ten computed H∩R validation cells and twelve unavailable
cells because the reference train pool is smaller than the requested holdout
train size. The three draws evaluate **45 samples / 29 components**, not all 65.
They target 41 or 44 training samples (29 or 32 original components); actual
subsample component counts range 27–33. Draw 0 has nine exact cells plus one
one-sample shortfall; draws 1/2 have ten exact cells. The declared tolerance is
two samples, not a hidden deletion or relaxed dependency rule.

| Matching draw | Size-control spectral RMSE | Genus-holdout RMSE on those same 45 IDs | Change control − holdout, 95% interval |
|---|---:|---:|---|
| 0 | 85.406657 | 144.051615 | −58.644958 [−75.846268, −40.523658] |
| 1 | 89.463646 | 144.051615 | −54.587969 [−72.206106, −35.538126] |
| 2 | 118.595480 | 144.051615 | −25.456135 [−46.148566, −4.937038] |

This conditional result is compatible with a group/distribution effect beyond
training sample count alone. It does not match independent-component counts,
target distributions or all development IDs. The reference size controls can
contain other examples of the evaluated genus outside their validation cells;
none contains an evaluated plot. Do not compare their 45-ID aggregate to the
all-65 holdout error as if paired.

After predictions, reference has **2/65** Y outside the relevant training range,
genus holdout **7/65**, date holdout **2/65**. Reference inside/outside spectral
RMSE is 108.697583 (63 samples) / 165.231081 (2); genus holdout 128.722612
(58) / 227.723059 (7). These within/outside sets differ between protocols, so
their aggregates are not paired range-controlled effects. No difficult outcome
is discarded from a primary metric; no Y-range subset selects a model or split.

## Global training-target intervention

All **19/19** attempts compute successfully and meet the 50% changed-target
gate in every actual inner/outer fit; the minimum observed fraction is 61.76%.
All models are scored against original outer Y, while inner selection scores
original inner-validation Y. Complete target vectors are exchanged only within
compatible strata; each model's target maps, source reference IDs, training
hashes, native data views and selected N4ME hashes remain in the full report.

| Model | Original RMSE | Intervened median RMSE | Intervened range |
|---|---:|---:|---|
| Null | 146.993310 | 146.993310 | unchanged within floating roundoff |
| Genus-only | 114.780941 | 158.047762 | [142.476859, 173.234814] |
| Spectral PLS | 110.867765 | 139.162873 | [129.146783, 162.323457] |
| Genus + residual | 101.346279 | 160.195181 | [133.773453, 179.501301] |

Each attempt has its own paired 500-draw frozen-OOF interval and gain change
relative to its own fold-local null. For attempt 0, spectral degradation has
interval [18.044308, 70.233818] and residual degradation
[52.542076, 99.879013] g/m². These example intervals are identified by scheduled
attempt, not selected as the most favorable. No Monte Carlo p-value or claim
of 5% significance is produced. Conditional block exchangeability remains an
assumption. Preserving whole vectors also preserves their internal ordering
and dependence; surviving performance is not a measured chemical fraction.

## Controlled scientific execution

All four generating-mechanism fixtures execute 19 global and 19 within-factor
attempts. Full-rank analytical tests use grid 1–6; the standalone stress pilot
uses the predeclared rank-safe 1–3 grid, which need not fit an exact linear
relation to machine precision.

| Control | Original spectral RMSE | Global median | Within-factor median | Within interpretation |
|---|---:|---:|---:|---|
| Group offsets only | .371742 | 6.865600 | .371742 | Y unchanged; all 19 explicitly low-power |
| Continuous trait | .024209 | 5.074763 | 4.863043 | Effective fine correspondence loss |
| Mixed offsets + trait | .356084 | 8.891459 | 5.398795 | Group-only signal preserved; incremental signal reduced |
| Independent Y | 1.029357 | 1.023253 | 1.025064 | No reliable gain over original null .999030 |

The pure-offset global control has 19 computed but only 12 fully effective
attempts; seven remain weak, without redraw. The separate unique-label control
records all 19 within-factor attempts unavailable. Mixed-composition vectors
preserve their factor composition and reference constraints. Shared references,
partial component targets and incompatible ordered reference patterns are
rejected/scoped by explicit gates.

In the size-only control, spectral RMSE changes .483408→.471720 while residual
RMSE changes .929544→1.047270 after reducing train from 72 to 24 samples on the
same 24 validation IDs. Fewer samples can affect models differently; no shortcut
finding follows. A continuous nonlinear `Y=t²+2t` extrapolation control has all
24 validation Y outside train range and spectral RMSE 5.020695 despite no
generating group offset. A decline alone cannot identify structural shortcuts.

## Evidence, reproducibility and boundaries

Observed degradation under true genus holdout, effective global interventions
and partial size controls supports sensitivity to training relationships and
known taxonomic structure. Remaining alternatives include Y extrapolation,
cohort composition, different independent-component counts, model instability
and genuine biological shifts. Real within-genus mediation is unidentified
under the strict exchangeability/power design. No causal attribution, shortcut
percentage or universal score is produced. Alpha.5 EcoSIS inconclusive and
Shootout fragile X clustering retain their original meanings.

The runner preserves **123 frozen files**, including alpha.4–alpha.6 reports,
lineage and previous schemas. It exactly replays the full real genus-holdout
result, real global attempt 0 and one size-matched cell. It does **not** claim a
second execution of the complete 19-attempt real campaign. Controlled CLI
reports additionally replay byte-identically in tests. Bootstrap intervals
condition on fixed OOF predictions, exclude refit uncertainty and are distinct
from the six reference-seed experiments.

Use `scripts/run_split_stress_pilot.py` with the frozen mean task and alpha.6
report. Full artifacts remain in ignored `results/split-stress-alpha7`; compact
execution evidence is [alpha7-qualification.json](audit/alpha7-qualification.json).
