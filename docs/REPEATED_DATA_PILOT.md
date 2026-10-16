# EcoSIS repeated-data qualification — alpha.4

Executed on 2026-10-16. The frozen design is in
[REPEATED_PILOT_PROTOCOL.md](REPEATED_PILOT_PROTOCOL.md), its parameters in
[the pilot config](../configs/pilots/ecosis_freeze_dried.yaml), and numerical
evidence in [audit/ecosis-repeat-qualification.json](audit/ecosis-repeat-qualification.json).
Full reports, identity mappings, fitted states, OOF predictions and bootstrap
draws remain under ignored `results/ecosis-alpha4-release/`. Previous outputs,
including alpha.3, are preserved. This is a descriptive qualification, not a
production calibration or an estimate of prediction failure from coverage.

## Source and identities

The [official EcoSIS record](https://data.ecosis.org/dataset/freeze-dried-leaf-spectra-and-measured-traits-from-the-sierra-nevada--ca--in-july-2023)
and [original guide](https://data.ecosis.org/dataset/cd421eda-ed75-409a-99ae-a2385515c2ed/resource/f0418260-c9f1-48f3-bef0-b8af248d8bc7/download/readme.md)
describe individual CA2023 samples and six spectral replicate codes. Held CSV
bytes match the current official downloads by SHA-256. The record declares ODbL.
The original acquisition IDs and sample-keyed trait records are unique; X/Y are
joined by those keys, never by position. The legacy standardized Y table lacks
acquisition keys and was not used for a positional repair.

| Verified inventory | Freeze dried | Oven dried | Fresh |
|---|---:|---:|---:|
| Physical sample codes | 82 | 83 | 35 |
| Spectra | 492 | 498 | 363 |
| Acquisitions per sample | 6 | 6 | 9–16 |
| Wavelengths / axis | 2151 / 350–2500 nm | same | same |
| Role in this lot | Primary X/LMA qualification | Identity audit only | Identity audit only |

Freeze dried contains 81 numeric LMA records among the 82 measured samples;
`CA2023_019` is missing LMA. Supplemental record `CA2023_083` has no freeze-dried
spectra. All 1,058,292 canonical spectral cells are finite. The guide and keyed
sampling date, plot, coordinates and sample number corroborate 82 shared origin
records between dried datasets, and 35 with fresh. LMA records also agree on the
overlap. This establishes shared origin records, not interchangeable material
preparations. Drying treatments and fresh-leaf foreoptics are never averaged or
treated as independent evaluations of the same objects.

Freeze-dried metadata declares an ASD FieldSpec 3, serial 16122, laboratory
contact probe and lamp. The guide establishes spectral replicates, but does not
resolve rescan, repositioning or preparation subtypes. `technical_unspecified`
therefore requires the source evidence URI and homogeneous sample/context. Its
mean is a conditional descriptive representation; within-ID variation cannot be
called pure instrument noise. The campaign field denotes the source bundle;
separate measurement sessions are not established.

The official signal unit is `%`, while supplied values range approximately
0.03930–0.96333. Values remain `reflectance_as_supplied`, without rescaling.
The source declares prior interpolation; Domains preserves the supplied 1 nm
grid. LMA units are g/m². Independent assay event IDs, reference precision and
censoring metadata are unavailable. `CA2023:LMA:<sample>` denotes the original
logical trait record, with unknown laboratory status, not a verified independent
laboratory measurement. No repeated numeric LMA across different samples or
conflicting keyed LMA records was found; numeric equality alone would not prove
a shared assay.

There are 57 documented plots: 34 contain one sample, 21 contain two, and two
contain three. Plots form the conservative available validation blocks. Plant
identity is unknown. Independence between plots is conditional within the three
sampled geographical areas; this design does not validate transfer to a new
region or separate species/location effects.

Datasets 0.3.11 writes fresh canonical Parquet from already tabular, keyed source
CSV. A local derived descriptor explicitly declares the original plot/campaign
metadata; the upstream descriptor is unchanged. Values match originals by
acquisition ID after Datasets' float32 storage conversion; target values match by
sample ID. This is not a claim of numerical parity with unavailable historical
registry arrays. Source, descriptor and canonical hashes are retained.

## Frozen splits and comparison

Plots are ordered by SHA-256(seed, plot), with ceil(20% × 57) = 12 plots retained.
Neither X nor Y participates in assignment. Exact sample IDs for all three
splits are in [audit/ecosis-plot-splits.json](audit/ecosis-plot-splits.json).
Seed 17 is primary: 45 train / 12 test plots, 65 / 17 samples and 390 / 102
acquisitions. Its development LMA values are complete; missing LMA sample 019
stays in the X-only held-out population. No acquisition is deleted to meet a
numerical budget. Both representations use all 2151 wavelengths.

| Dataset | Target | N samples | N spectra | N train | N test | Policy | Coverage warnings | Predictive sanity check | Limitations |
|---|---|---:|---:|---|---|---|---|---|---|
| Freeze dried, seed 17 | LMA g/m² | 82 | 492 | 65 samples / 390 rows | 17 samples / 102 rows | grouped_native | 16/102 = 15.69% | Not run on acquisition rows | Conditional plot independence; exact effective dimension unavailable |
| Freeze dried, seed 17 | LMA g/m² | 82 | 492 | 65 samples / 65 rows | 17 samples / 17 rows | technical_mean | 4/17 = 23.53% | Development nested OOF RMSE 110.87 vs null 146.99 | Replicate subtype and assay precision unknown |
| Freeze dried, seed 31 | LMA g/m² | 82 | 492 | 66 samples / 396 rows | 16 samples / 96 rows | grouped_native | 18/96 = 18.75% | Prespecified coverage sensitivity only | Same identity limits |
| Freeze dried, seed 31 | LMA g/m² | 82 | 492 | 66 samples / 66 rows | 16 samples / 16 rows | technical_mean | 3/16 = 18.75% | Prespecified coverage sensitivity only | Same identity limits |
| Freeze dried, seed 47 | LMA g/m² | 82 | 492 | 65 samples / 390 rows | 17 samples / 102 rows | grouped_native | 4/102 = 3.92% | Prespecified coverage sensitivity only | Same identity limits |
| Freeze dried, seed 47 | LMA g/m² | 82 | 492 | 65 samples / 65 rows | 17 samples / 17 rows | technical_mean | 1/17 = 5.88% | Prespecified coverage sensitivity only | Same identity limits |

Each representation fits public Methods FlexiblePCA on train once and uses its
retained native `transform()` for test. Four components reach 97.3043% (native)
and 97.3475% (mean) of full covariance trace. Trace comes from Methods feature
variances. Native full squared covariance trace exceeds the existing public
kernel's 250-million-product budget: effective dimension is explicitly
unavailable, while scores, neighbors, residuals and coverage remain computed.
The mean-view full moments are available, giving effective dimension 2.48153.
No truncated eigenvalue sum is substituted for a full moment. The public affine
transform is queried on zero and coordinate vectors to obtain reconstruction
loadings; opaque native state is not inspected.

Primary nearest-neighbor fences are 1.15908 / 1.42634 and squared reconstruction
fences 0.248062 / 0.237749, native / mean. They are fitted separately on train,
excluding entire dependency components from admissible neighbors. Median
train pooled within-ID SD over wavelengths is 0.00636138 supplied reflectance
units, through the public Preflight/Methods repeatability kernel. It is identical
between policies because this diagnostic always uses original acquisitions.

The same four physical samples are flagged in both primary views: 019, 024, 048,
052. Native flagged acquisitions per sample are respectively 6, 2, 6, 2; each
mean contributes one flag. Thus 15.69% versus 23.53% does not show four additional
poorly supported samples. Different denominators and separately fitted
geometries explain the change. Coverage remains a heuristic, not a performance
loss probability; averaging can reduce within-ID dispersion without validating
independence or improving prediction.

## Uncertainty and stability

Held-out bootstrap draws whole plots, retaining all their physical samples and
acquisitions. Each sample contributes its mean acquisition flag. With 500 draws,
the nearest-rank 95% intervals for seeds 17 / 31 / 47 are:

| Representation | Seed 17 | Seed 31 | Seed 47 |
|---|---|---|---|
| grouped_native | [1.85%, 33.33%] | [0%, 35.29%] | [0%, 13.33%] |
| technical_mean | [5.00%, 50.00%] | [0%, 35.29%] | [0%, 20.00%] |

These intervals condition on the frozen train PCA and fences. Separately, 100
paired resamples of whole train plots refit PCA and both fences with held-out X
fixed. Both policies complete 100/100 fits without redrawing; the component-draw
hash is identical. Four PCs are retained in 94 draws and three in six, for both
views. Coverage refit intervals are [11.76%, 34.31%] native and [11.76%, 35.29%]
mean. Native NN/Q fence intervals are [0.991925, 1.72712] / [0.173419, 0.641498];
mean intervals are [1.06855, 2.03555] / [0.161216, 0.585693]. These are separate
conditional sensitivity analyses, not a combined uncertainty interval or a
calibrated population risk. The substantial seed sensitivity forbids treating
one held-out fraction as a universal dataset property.

The Preflight local descriptive contrast on exported development mean rows is
0.485117 (k=8); it is not predictive validation. The separate
[nested PLS sanity check](PREDICTIVE_SANITY_CHECK.md) supplies actual OOF evidence.
The canonical Rust report explicitly leaves its own nested-probe slot unavailable
because that optional workflow emits a separate report.

## Reproduce

Install `bridges/python[test,datasets,predictive]` and Methods 1.3.6. Supply the
original three EcoSIS resource folders and the audited Datasets descriptor:

```powershell
. .\scripts\dev-env.ps1
cargo build --workspace --locked
.venv\Scripts\python.exe scripts/run_repeated_pilot.py `
  --raw-root $rawResources --descriptor $freezeDescriptor `
  --binary target/debug/n4domains.exe `
  --methods-library $env:N4DOMAINS_METHODS_LIBRARY --out results/ecosis-new-run
```

`$rawResources` and `$freezeDescriptor` are explicit local inputs; the script
refuses an existing output directory. It rechecks official primary resource
hashes, canonical keyed parity, each coverage report twice, split safety, and
absence of test targets. Two complete full-grid executions also produced
byte-identical scientific coverage and predictive outputs. The provisional 2 nm
run is preserved for audit and superseded by the complete-axis qualification.

Shootout remains the separate historical-split reference (155 train, 460 test,
40 validation exclusions, 73/460 flags). Its four scalar metrics are unchanged
under alpha.4. Scores between these datasets are not directly comparable.
