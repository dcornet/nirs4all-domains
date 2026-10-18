# Alpha.13 unsupervised bank extension

Soil's canonical labels span 1100–2500 nm, whereas package documentation describes
400–2500 nm. Original-axis correspondence remains unavailable. The results below
describe the complete canonical array with its declared labels; wavelength-specific
original-source interpretation is not qualified.

Two independently sourced material-family candidates add full-population raw/SNV
evidence to the protected 39 alpha.12 public-catalog views. The bank now has
**41 characterized views**, comprising the unchanged 39/42 public cohort plus two
separately rights-admitted private-tier canonical views. This is not 41 independent
studies or 41/42 public coverage.

Both new sources use complete-source exact query/reference neighborhoods in full
axis and retained PCA coordinates. Native Methods/Preflight supply all PCA,
moments, distances, HDBSCAN, ARI, SNV and summaries. Four reference PCA fits and
eight clustering attempts are new; prior references are reused exactly.

| Source / representation | PC1 fraction | Effective dimension | Groups at 8 / 12 | Noise at 8 / 12 |
|---|---:|---:|---|---|
| Tablets raw | .99688 | 1.0063 | 5 / 4 | .058 / .042 |
| Tablets SNV | .64757 | 1.9997 | 9 / 5 | .219 / .100 |
| Soil raw | .86936 | 1.3060 | 3 / 2 | .648 / .741 |
| Soil SNV | .85689 | 1.3418 | 2 / 0 | .694 / 1.000 |

Dimensions use full native covariance moments where available, not a truncated
PCA surrogate. The tablet axis retains 404 wavenumbers in cm^-1; soil retains its
700 declared wavelengths in nm. Intensity conventions retain source limitations.
No interpolation, row thinning or target-based screening occurs.

Within-source normalized nearest-neighbor medians are .02362/.18199 for tablet
raw/SNV and .16606/.17944 for soil raw/SNV. At the frozen relative radius .01,
tablet raw has 10/310 queries with a neighbor and SNV 0/310; both soil views have
0/108. These fractions use the source's own covariance-trace normalization and
complete population. They are descriptive; raw distances/traces are not pooled
across unrelated units. Close spectra do not establish physical replication.

The same observations, full references and queries support every representation
comparison. Soil's all-noise SNV setting remains a valid missing partition result,
not a continuum or low-susceptibility certificate. Metadata agreement lacks a
separately qualified original-key factor join. Nothing in these X-only profiles
demonstrates target association, predictive dependence or causal shortcuts.

Tablets also enter the prospectively selected revised stability cohort. Soil
receives geometry without an unplanned fourth stability campaign. All contrary,
noisy and unavailable findings are retained.

See [extension JSON](benchmarks/alpha13/x-only-extension.json), individual
[profiles](benchmarks/alpha13/profiles), and
[stability results](ALPHA13_STABILITY_POWER_RESULTS.md).
