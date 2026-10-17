# EcoSIS structural dependence — alpha.6

Executed 2026-10-17 on the frozen freeze-dried / `LMA_value_g/m2` development
population: 65 physical means, 45 declared plot components, all 2151 bands,
seed 17, five outer / three inner grouped folds, components 1–5. Retained test
labels never enter this workflow. Source, target, physical means and folds are
unchanged. The original PLS predictions, metrics, selected artifacts and lineage
are compared exactly to alpha.4. The previous 30 coverage/predictive/structural
reports are hash-checked before and after execution.

## Factor audit before outcome experiments

The alpha.4 metadata accessor/export contained plot, date and coordinates.
Genus/species were declared as categorical **targets** in the original descriptor,
so `metadata()` did not export them. Public Datasets 0.3.11 `y('genus')` and
`y('species')` retrieve their canonical columns; no LMA/test-target accessor is
called during this augmentation. Values are verified against the original
supplemental CSV by sample ID. Source blanks stay missing; leading/trailing
whitespace is trimmed by a rule frozen before outcomes. No taxonomy regrouping,
coordinate binning or cluster-derived factor is introduced. Source hashes,
counts, joins and per-fold level overlap are in
[the pre-experiment audit](audit/alpha6-factor-transport.json).

| Factor | Observed levels | Missing means | Seen-level OOF | Fallback | Conditional support |
|---|---:|---:|---:|---:|---|
| Plot | 45 | 0 | 0/65 | 100% | Unavailable: every plot held out |
| Sampling date | 9 | 0 | 65/65 | 0% | Eligible, each date spans 3–7 plots |
| Genus | 15 | 4 | 55/65 | 15.38% | Eligible subset; many rare genera |
| Species column | 23 | 11 | 37/65 | 43.08% | Eligible subset; many rare labels |

The species column contains source epithets, not independently qualified
taxonomic identities. Date means historical date overlap, not future-date
transfer. Botanical labels must actually be available for any deployment using
these baselines. Coordinates have no missing development values but are audited
only. Plot/plant/assay independence and laboratory precision remain unverified.
Eligibility was based on metadata support, never eventual performance.

## Descriptive association and matched prediction

Association excludes missing factor rows. **All predictive models use all 65
means on identical outer IDs**, with missing/unseen factor levels falling back
to the outer training global mean. The null RMSE is 146.993310 g/m²; the original
spectral PLS RMSE is 110.867765, MAE 76.875527 and R² 0.396921. It remains
numerically unchanged. No model uses a true validation-group target mean.

| Factor | Association n / components | Eta² | Group-only RMSE | Spectral RMSE | Group + residual RMSE | Residual gain over group |
|---|---|---:|---:|---:|---:|---:|
| Plot | 65 / 45 | 0.708937 | 146.993310 | 110.867765 | 142.041824 | 4.951486; conditional interpretation unavailable |
| Date | 65 / 45 | 0.366504 | 132.014416 | 110.867765 | 118.277172 | 13.737244 |
| Genus | 61 / 43 | 0.608047 | 114.780941 | 110.867765 | 101.346279 | 13.434662 |
| Species column | 54 / 37 | 0.680436 | 112.673515 | 110.867765 | 105.954082 | 6.719433 |

Positive gain means RMSE(group-only) minus RMSE(group+residual). Association
component counts are reported by the native-backed report; missing factors
change that descriptive denominator, so eta² values are not paired comparisons.

All 200 association and paired OOF component draws succeed for each factor.
Nearest-rank 95% association intervals are plot [.568901, .863811], date
[.252028, .639658], genus [.466612, .823925], species [.502816, .863306].
These condition on the observed design and assume declared components suffice.
Unrestricted native factor permutations are disabled.

| Factor | Group gain over null, 95% interval (g/m²) | Residual gain over group, 95% interval (g/m²) |
|---|---|---|
| Plot | [0, 0] | [-12.912700, 17.932245] |
| Date | [-3.220037, 34.111841] | [-2.942152, 28.056257] |
| Genus | [14.297613, 47.756673] | [0.598976, 26.083021] |
| Species column | [18.208400, 49.518840] | [-14.307176, 24.142208] |

These resample **frozen paired OOF predictions**, excluding model-refit
uncertainty. They are exploratory, with only 200 draws and no confirmatory
multiple-factor testing claim. The original spectral gain over null interval is
[2.476651, 68.439368] g/m² on the same population.

Seen-level conditional populations are date 65/45, genus 55/39, species 37/26
samples/components. Their group / group+residual RMSEs are respectively
132.014416 / 118.277172, 100.901136 / 85.923405, and 93.835123 / 87.582336.
Residual-target R² values are .197185, .274048 and .127201; these have a
different denominator from original-target R². Their own paired bootstrap
records accompany the JSON; the all-65 intervals above cannot substitute for
those conditional populations.
For the 55 seen-genus samples / 39 components, the residual gain interval is
[.203243, 26.736482] g/m². For the 37 seen-epithet samples / 26 components it is
[-10.842084, 17.872105] g/m². Neither interval includes model-refit uncertainty.

## Interpretation

Genus and source-species labels carry useful development prediction information
under plot holdout, despite sparse/unseen labels. Genus also shows an exploratory
positive paired residual correction on the full development population. Dates
and source-species residual gains have intervals crossing zero. Plot association
is high with 45 levels but its predictor always falls back: that failure says
nothing about whether spectra exploit plot or regional structure.

For example, plot eta²=.709 describes fitted group means on the observed Y,
while plot group-only OOF equals the null because every validation plot is new.
Original PLS R²=.397 instead measures predictions from spectra under plot
holdout. Genus group-only RMSE 114.78 shows that known botanical labels predict
much of this particular development variation; residual RMSE 101.35 provides
additional conditional evidence. None of these quantities is a percentage of
chemical signal, a proof of shortcut learning or a causal decomposition.
Correlated taxonomy, geography, sampling dates and genuine chemistry remain
unidentified jointly. Selection/refit variability, independent assay accuracy
and new-region performance remain unmeasured.
Residualizing Y does not remove group-related information from X or guarantee a
pure chemical within-group effect.

## Controlled scientific execution

All controls use 96 physical means / 48 components, four outer / three inner
folds, native summaries, PLS and scoring. Nondegenerate linear fixtures use
components 1–6 on six features. Actual results are:

| Control | Eta² | Null RMSE | Group RMSE | Spectral RMSE | Group + residual RMSE |
|---|---:|---:|---:|---:|---:|
| Pure group offsets | 1 | 6.623937 | 0 | <1e-9 | 0, exact-zero no-fit case |
| Continuous trait independent of factor | ~0 | 4.756250 | 5.417950 | <1e-9 | <1e-9 |
| Mixed group and trait | .667536 | 8.299096 | 5.417950 | <1e-9 | <1e-9 |
| Independent Y | .018281 | .999030 | 1.019795 | 1.056773 | 1.047103 |
| Unseen component labels | .996089 | 8.299096 | 8.299096 | <1e-9 | 8.244812 |
| Unique labels | 1 | 8.299096 | 8.299096 | <1e-9 | 8.299096, exact-zero no-fit case |

Independent-Y residual gain has paired interval [-.065058, .005240], with no
reliable gain in this frozen control. The unseen-label result is explicitly
ineligible for conditional group mediation despite a small residual correction.
Duplicated acquisitions reproduce the mixed-control physical-level evidence.
Separate analytical native fixtures verify eta²=0/1/.8 and undefined F; these
use stated floating tolerances, not rounded scientific thresholds. Adversarial
tests preserve candidate artifacts when their inner holdout Y changes, reject
identity remappings that split components, and retain failed bootstrap draws.

EcoSIS alpha.5 X clustering remains inconclusive. Shootout remains the second
preserved case with fragile X clustering, not confirmed predictive groups. No
documented explanatory factor was qualified for Shootout in this sprint; no
HDBSCAN labels were repurposed as instruments/batches/assays. Cluster-derived
prediction remains unavailable without qualified fold-local held-out assignment.

The reproducible runner is `scripts/run_dependence_pilot.py`; full artifacts stay
under ignored `results/dependence-alpha6-final`. Committed compact execution
evidence is [alpha6-dependence-qualification.json](audit/alpha6-dependence-qualification.json).
