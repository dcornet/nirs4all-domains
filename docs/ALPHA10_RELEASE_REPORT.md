# Alpha.10 — estimator-dependent structural sensitivity

## A — Multi-family implementation

Domains retains its two Rust crates, Methods 1.3.6/ABI 2.19 and DAG-ML 0.3.41.
Classical calibration/scoring/SNV remain native. The requested optional upstream
candidate is **nirs4all 1.4.10 FastAOMPLSRidge**, audited at
`1aefd473a0ebeef28adc0d808c4a4b0c9c45fa9f`: both `hard_aom_chain` and
`sparse_mkr` execute. Its public constructor accepts `FastAOMConfig`; its NumPy/
SciPy implementation owns bases, SVD, operators and final prediction. Domains
copies no numerical algorithm. PCR is deferred to prioritize this amendment.

The published wheel's 19 audited Python source files match that revision.
An isolated wheel plus the tested public-entry import closure is used; ten
unneeded full-application base requirements remain absent. This qualifies the
specific estimator entry, not the whole nirs4all application. Exact requirements,
source/wheel hashes, serialization, rank and feature limits are in
[provider evidence](audit/alpha10-fastaom-provider.json). The same bounded import
contract is exercised in hosted CI. No package/provider is blindly upgraded.

Native Methods `FastAOMPLSRegressor`/`FastAOMRidgeRegressor` are separate strict10
branch-CV protocols with explicit fold IDs. Their installed bindings/symbols
are inspected; they are not executed or substituted for the requested model.
Source/ABI/binding/publication evidence alone is not scientific qualification.

## B — Perten results and selection

All 359 original development IDs, 17 context blocks, target units and three
alpha.9 outer designs remain fixed; 91 retained outcomes are sealed. Existing
PLS 1–3 and fixed alpha-1 Ridge are preserved and completely replayed exactly.
New Ridge uses alpha .0001/.01/1/100/10000; SNV/PLS uses components 1–3. Hard
FastAOM uses components 1–3, fixed lambda .01; sparse MKR has one fixed lambda-1
configuration and at most three active chains. Nine depth-one compact chains,
two raw/SNV bases, 18 screened pairs, eight finalists and rank cap 32 bound work.

| Pipeline | Reference RMSE | Cereal RMSE | Instrument RMSE |
|---|---:|---:|---:|
| Frozen PLS | 2.3873 | 5.0856 | 3.4918 |
| Frozen fixed Ridge | 2.6166 | 2.8468 | 3.4336 |
| Nested-selected Ridge | 1.8781 | 2.9542 | 3.0356 |
| Native SNV/PLS | 1.8221 | 3.0650 | 2.4471 |
| FastAOM hard chain | 2.0079 | 1.5000 | 2.0174 |
| FastAOM sparse MKR | 2.5337 | 2.5958 | 2.0207 |

Units are source moisture percentage points. Hard FastAOM's cereal change is
−.5079 [−.9064, .1582]; PLS's is +2.6983 [1.7370, 3.7593]. Their matched
interaction is **3.2063 [1.8164, 4.1940]**. Tuning Ridge improves its reference
skill while increasing its cereal deterioration relative to the fixed control.
Actual selected settings, MAE/R², null gains, all pair interactions, chains/bases,
lineage and failures are in [results](ALPHA10_MULTIFAMILY_RESULTS.md) and linked JSON.

Fresh estimators fit in every native group-safe inner-training scope. No outer
validation enters base fitting, screening, basis/latent selection or refit.
Shuffled internal KFold is disabled. Singleton lambdas disable row-LOOCV/GCV
hyperparameter selection; its internal diagnostics are not validation evidence.
Candidate errors fail their declared experiment rather than silently shrinking
the grid. Controlled validation-X/Y and retained-X/Y adversaries pass.

## C — Remaining confounding and interpretation

There are two cereal closure units: barley/wheat 209 specimens/11 contexts and
corn 150/six. Paired bootstrap draws resample the original 17 contexts and
condition on fitted OOF predictions. Unseen-category and model-refit uncertainty
remain unavailable. A pooled 359-ID metric is not 359 group-transfer experiments.

A separately frozen exact whole-component size control covers all 359 IDs,
preserving the earlier 38-ID result. With equal training counts, PLS's cereal gap
is +2.7221 [1.7108, 3.8369], tuned Ridge +.9192 [.1975, 1.6083], and hard
FastAOM −.2182 [−.5087, .0663]. Pure sample count does not explain every observed
gap. Cereal composition, context diversity, target/spectral extrapolation and
unknown assay/farm dependencies remain. Original target-range counts are
14/18/21 of 359, evaluated after prediction. No causal shortcut fraction is identified.

Observation: responses differ by estimator, tuning and preprocessing under the
same frozen structural tests. Confidence: exploratory and specimen-context
conditional. Consequence: favorable adaptive performance does not certify lower
structural dependence. Action: preserve these contrastive benchmark purposes and
seek more independent category/source support.

## D — Cartilage original-source qualification

The CC0 revised Figshare v2 MAT is verified, with 869 original keyed locations,
2,605 spectra, 812 bands, 44 regions and five joints. Every original location's
spectral multiset matches the derived X after float32 transport, using explicit
sample keys. Derived Y remains unkeyed; original MAT reference ownership supplies
a separate keyed adapter. Full-precision original axes are preserved.

Donor-to-joint relationships and assay-event dependencies remain unidentified.
No real predictive fit is run. The full-population resource estimate preserves
869 locations: 5.65 MB float64 means, 16.92 MB acquisitions, 50 model fits for a
5×3×3 design. A native synthetic 869×812 gate executes without truncation; it
does not qualify a real grouped workflow or remove the 500-row CLI guard.
Weak prediction remains an unresolved observation, not proof of a data error.
See [original audit](ALPHA10_CARTILAGE_ADMISSION.md).

## E — Paired-source transfer and Perten reference provenance

No paired case is admitted. CORN stays pending by explicit owner decision and
missing original sample/reference keys. Shootout's original MAT itself totals
655 per instrument; all original row keys are empty, while its official page says
654. UCPH still lacks source-confirmed NIR/NIT/Raman specimen/assay correspondence.
Prepared requests distinguish same-object source transfer from new-object
generalization. [Blockers](ALPHA10_PAIRED_SOURCE_ADMISSION.md) are reproducible;
no restricted fit, upstream change or external message occurs.

No new source evidence resolves Perten wet/dry basis, oven protocol/precision,
assay events, farm/harvest links or country/model semantics. Frozen original
targets and alpha.9 interpretation remain unchanged.

## F — Benchmark suitability and registry

Perten belongs to within-population estimator comparison and structural challenge
purposes; EcoSIS remains in the separate challenge suite. Actual membership/IDs
were fixed by the pre-score evaluation manifest; final enriched evidence hashes
are necessarily produced after execution and frozen for future comparisons.
Low-dependence and real transfer suites remain empty. Evidence is multidimensional,
without universal probability or raw RMSE aggregation across targets/units.
The additive schema/purpose and Datasets sidecar preserve all historical records.

## G — Storage and measured computation

Datasets owns the original MAT cache; no matrix is copied into each fold/report.
All execution uses the cumulative alpha.9 campaign journal. Primary fitting uses
320 model fits; exact-size controls 324; complete anchor replay 112; scoped
adaptive/native replay 10/16. The original 256 MiB task / 4 MiB evidence / 512 MiB
campaign / serial / 2 GiB volume-reserve limits are retained. The owner approved
the initial 512 MiB workspace increase. New Rust build artifacts subsequently
crossed that ceiling by 27.84 MiB; the validation guard stopped there. The owner
approved another 256 MiB for validation/build tooling, setting the final workspace
ceiling to 12,799,936,193 bytes. No data, historical results or caches are deleted
or migrated. Final byte/approval evidence is recorded separately.

Hard/sparse FastAOM whole primary execution measures 7.49/8.81 seconds, versus
4.67 for tuned Ridge and 8.50 for SNV/PLS in this local serial environment.
Process peaks are 232/230 MiB versus 202/197 MiB, including imports. Hard FastAOM
screening totals .467 seconds. These are single environment-specific measurements;
different candidate counts and timing scopes preclude a blanket speed claim.
Detailed fit/prediction costs and actual selected complexity remain in evidence.

## H — Specific upstream needs

Prepared only: Cartilage joint-to-animal and assay-event map plus keyed target/
full-axis adapter; Perten oven/basis/assay/lot/country/serial definitions; CORN,
Shootout and UCPH physical/reference keys and permitted paired-publication scope.
For nirs4all, a grouped internal selection contract, documented minimal estimator
deployment, a stable model interchange format, and solver/rank-budget reporting
would improve integration. Methods' distinct native FastAOM would need its own
protocol qualification. No upstream repository or issue tracker is modified.

## I — Validation and publication

Baseline: 129 tests. Alpha.10 adds 23 controlled integration gates. The 177-file
preservation manifest extends the earlier 133 artifacts to alpha.9 compact and
local scientific outputs; portable hashes are also checked in CI. All 2,154
anchor predictions replay exactly; one tuned-Ridge and one hard-FastAOM outer
scope replay under their exact/tolerance contracts. Four primary checkpoints and
the complete-size checkpoint are resumable content-bound stages.

**152 tests pass locally: 35 Rust + 117 Python.** fmt, Clippy with denied warnings,
native ignored gates, schemas, reports and isolated wheel import pass. The
80,061-byte wheel matches the executed controllers; all 177 protected outputs
retain their hashes. Combined unique alpha.10 essential evidence is 2,815,216
bytes; cumulative campaign reservations are 196,676,888 bytes. Measured workspace
12,654,715,975 bytes is below the final owner-reviewed ceiling, with free-volume
reserves preserved. Exact receipts are in audit/alpha10-validation.json and
audit/alpha10-storage.json. Commit and actual Windows/Ubuntu CI are recorded in
[VALIDATION.md](VALIDATION.md) after hosted execution; configuration alone is not
execution proof.

## J — Bounded alpha.11 and deliberately separate TabPFN study

First obtain source identity/reference support for a non-cereal benchmark and
qualified real transfer case; retain difficult/negative cases without score-based
discard. Freeze a small, scientifically diverse task subset and exact group-safe
evaluations before any new model's scores. Extend independent group support,
repeated fitted-design uncertainty and target-reference provenance before
proposing low structural dependence.

A later TabPFNNIRSRegressor experiment would use that frozen subset: structural
challenge, a sufficiently supported limited-dependence candidate if one exists,
real transfer and controlled mechanisms. Audit exact model/weights/license,
GPU/RAM, feature limits, train-only preprocessing and resource budgets first.
Use identical group-safe outer evaluations and only compatible internal selection.
Compare matched deterioration to these anchors; stronger shortcut use is a
hypothesis to test. **No TabPFN package, weights or model is run in alpha.10.**
