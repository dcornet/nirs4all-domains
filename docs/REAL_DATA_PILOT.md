# First real-data qualification — Shootout X1

The alpha.2 execution below is retained as a baseline. Alpha.3 adds the explicit
representation comparison described at the end of this document.

Executed locally on 2026-10-16 with Domains **0.1.0-alpha.2**, Datasets 0.3.11,
Preflight 0.1.0-alpha.1 and Methods 1.3.6 / ABI 2.19.0. The first published commit's
[GitHub CI](https://github.com/dcornet/nirs4all-domains/actions/runs/38894601512)
passed on Windows and Ubuntu. That CI did not access these privately held data.

## Task and populations

Dataset `pharmaceutical_tablets_nir_shootout_eigenvector`, descriptor content
version 1.0.0, **X1 only**, target **assay (mg/tablet)**, native `original` split.
The source includes 655 rows per instrument: 155 calibration, 460 test and 40
validation. This differs from the archive landing page's historical count of 654;
the actual native partition counts are preserved and the discrepancy remains
documented rather than silently removing a row.

The [task configuration](../configs/pilot-shootout.yaml) explicitly maps
calibration → train, test → test, validation → exclude. The retained task has
615 observations. All 40 excluded observation IDs and native counts are retained
in provenance. The validation subset is never pooled into calibration or test.
The canonical geometry uses train centering and adaptive PCA (95%, maximum 20),
without autoscaling, supervised preprocessing or model fitting on test.

The primary practical analysis by A.M.C. Davies identifies the target as assay
in mg/tablet and the 155/460 native subsets. It uses a different demonstration
training assignment; this pilot preserves the original calibration/test labels.
See [Spectroscopy Europe 18(6), 2006, p. 28](https://www.spectroscopyeurope.com/system/files/pdf/TD_18_6.pdf#page=1).
The spectral log(1/T) representation is documented in
[Eigenvector's preprocessing course](https://www.eigenvector.com/Docs/EigenU_Europe_17/5b_AdvancedPrepro.pdf).
No absorbance/reflectance conversion is performed here.

## Data handoff and reuse

The existing local standardized export had removed observation IDs from Y.csv,
while its older datapackage still declared them. Passing it directly to Datasets
would skip the target table. Domains now rejects a requested target absent from
canonical data rather than quietly treating that as a qualified regression task.

The audited existing `convert_eigenvector_1d_datasets.py::convert_shootout` was
reused from the separate data preparation project, with its output root redirected
into a fresh workspace staging tree and downloads disabled in favor of the already
held official ZIP. It regenerates keyed X1/X2/Y/M exports; the script is not copied
or modified. No row-position join between instrumental sources is added to Domains.
`nirs4all_datasets.canonical.build_canonical` then materializes canonical Parquet,
and all analysis input is read through public `get()/sources()/x()/y()/metadata()/split()`
and identity/axis accessors. The converter SHA is pinned in configuration.

This is a **local raw-data reproduction**, not a verified download of the registry's
canonical bytes. The registry manifest was produced with converter 0.2.0a1;
this materialization uses 0.3.11 and its Parquet hashes differ. The task records the
descriptor's content version, raw ZIP SHA, converter/descriptor SHA and newly
materialized canonical hashes. `registry_byte_identity_verified=false` is explicit;
numerical equivalence with the unavailable historical canonical arrays is not claimed.

Source partition/index aliases identify rows. One acquisition per tablet on X1
is an explicit source-based assumption, not independently discovered physical
identity. Original laboratory reference IDs are unavailable. Checks demonstrate
structural partition separation, not universal biological/reference independence.
No grouped CV or prediction-performance claim follows from this pilot.

## Results and acceptance evidence

| Descriptive output | Result |
|---|---:|
| Independent-unit count under the stated assumption | 155 train / 460 test |
| Effective spectral dimension from full moments | 1.642155 |
| Centroid distance in the train-fitted retained space | 0.350485 log(1/T) |
| Retained-score dispersion ratio, test/train | 0.967042 |
| Test observations exceeding either coverage heuristic | 73 / 460 (15.8696%) |

Both executions produce byte-identical JSON. The fit contains precisely 155 train
observation IDs; the report declares no Y_test access. Preflight emits no integrity
finding on this source under the declared identities. The report and availability
invariants pass JSON Schema validation. The batch retains this computed partial
report plus explicit unavailability for CORN's missing split and UCPH's unresolved
repeat/group plan. Remaining unavailable modules keep the report **partial**.

The 15.9% fraction is a train-only Tukey-fence diagnostic, **not** an error rate,
a predictive failure probability or proof of performance degradation. The
thresholds, observation IDs and distributions remain in the local JSON report.

## Reproduce locally

Supply the existing converter and raw archive; source repositories remain read-only:

```powershell
. .\scripts\dev-env.ps1
.venv\Scripts\python.exe scripts/run_local_pilot.py `
  --converter $sourceConverter `
  --raw-zip $sourceArchive `
  --descriptor .audit/datasets/catalog/datasets/pharmaceutical_tablets_nir_shootout_eigenvector.yaml `
  --registry-manifest .audit/datasets/datasets/pharmaceutical_tablets_nir_shootout_eigenvector/manifest.json `
  --binary target/debug/n4domains.exe `
  --methods-library $env:N4DOMAINS_METHODS_LIBRARY `
  --baseline-report results/shootout/first/report.json `
  --out results/shootout-alpha3-final
```

The converter must match the configured SHA. Fresh staging directories prevent
replacement of prior or upstream data. Raw files, canonical bytes, full reports
and per-observation outputs remain under ignored `results/`; only aggregate
evidence is committed. No new permission to redistribute data is assumed.

For the ordinary dataset batch, use the `catalog_root` written in the local
`qualification.json`:

```powershell
$pilot = Get-Content results/shootout/qualification.json -Raw | ConvertFrom-Json
target\debug\n4domains.exe batch --catalog-config configs/pilot.yaml `
  --catalog-root $pilot.catalog_root --out results/pilot --python .venv/Scripts/python.exe
```

## Alpha.3 representation comparison

The raw reproduction was rerun in a fresh output directory, leaving alpha.2
results intact. Each policy was executed twice with byte-identical results within
that policy. JSON and Markdown reports now expose the native acquisitions,
sample-context records, linked dependency components, reference completeness,
exclusions and exact train/test coverage population. The local full reports are
`results/shootout-alpha3-final/native/report.json` and
`results/shootout-alpha3-final/technical_mean/report.json`; their comparison is
`representation-comparison.json` / `.md` in the same directory.

| Count / result | Native | Technical mean |
|---|---:|---:|
| Train acquisitions / declared physical samples | 155 / 155 | 155 / 155 |
| Test acquisitions / declared physical samples | 460 / 460 | 460 / 460 |
| Declared independence groups, train / test | 155 / 460 | 155 / 460 |
| Dependency validation groups, train / test | 155 / 460 | 155 / 460 |
| Known laboratory reference IDs, train / test | 0 / 0; identities unavailable | 0 / 0; identities unavailable |
| Declared repeat groups, train / test | 0 / 0 | 0 / 0 |
| Native validation acquisitions excluded | 40 | 40 |
| Additional representation exclusions | 0 | 0 |
| Coverage numerator / exact denominator | 73 / 460 | 73 / 460 |

All four scalar metrics have exactly zero delta between policies and versus the
retained local alpha.2 report; train fitted states are identical between policies.
The technical-mean operation is a singleton identity operation under the supplied
row aliases. This real case checks preservation, populations and reproducibility;
nontrivial repeat averaging is qualified on controlled data, not demonstrated on
Shootout. Instrument/campaign metadata and original reference precision/status
are unavailable. Optional missing context does not block singleton rows; it
would block certification of a repeated-group mean.

Zero known reference IDs is not a claim that there were zero laboratory
measurements. The actual number of independent references remains unknown.
Physical and validation-unit counts remain conditional on the stated source-row
identity assumption. Historical registry canonical numerical equivalence remains
unverified. The 15.9% coverage fraction remains exploratory and does not estimate
prediction error. Aggregate hashes, counts and deltas are committed in
[the alpha.3 record](audit/shootout-representation-qualification.json); full arrays
and per-observation outputs remain local.

## Alpha.4 complementary repeated pilot

The grouped real-data lot is now executed on EcoSIS freeze-dried X/LMA. Its source
audit, full-axis FlexiblePCA, conditional plot splits, native/mean coverage and
two uncertainty scopes are in [REPEATED_DATA_PILOT.md](REPEATED_DATA_PILOT.md).
The [separate nested PLS check](PREDICTIVE_SANITY_CHECK.md) uses only EcoSIS
development means; it does not select a Shootout instrument-transfer strategy.

Shootout remains the historical split and prospective instrument-transfer case.
Fresh alpha.4 outputs preserve 155 train, 460 test and 40 validation exclusions,
with 73/460 outside flags under both singleton representations and exactly zero
delta in all four scalar metrics versus alpha.3. No existing pilot outputs were
overwritten. Dataset scores are not directly compared across these objectives.
Historical registry parity and original laboratory identities remain unverified.
