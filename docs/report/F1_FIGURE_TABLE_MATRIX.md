# Figure/table and evidence matrix

All browser and standalone scientific contracts are unchanged. F1's additive
`domains.report_presentation.v1` is a display projection, not a scientific report
replacement. `scientific_report` retains the original object and references.

| Presentation | Exact source | Population / units | Screen | HTML / Markdown / JSON |
|---|---|---|---|---|
| Spectral curves | Local import X and unchanged axis | Every acquisition; axis unit from IO, signal unit/type unknown | Existing shared SpectraExplorer; selection and index zoom | Text-only disclosure boundary / text / no raw X |
| Score map | `metrics.pca.value.scores` and original observation IDs | Complete imported X; score units unqualified if signal unit absent | Shared ScoreMap; optional declared-group colors | Graduated static SVG / axis and reading descriptions / same points |
| 1D PCA rail | Same source, one resolved component | PC1 only; rail is not PC2 | Static accessible SVG, no second axis | Same SVG / explicit PC2 limitation / same PC1 |
| Scree | Resolved eigenvalues and full covariance trace | Same centered-X fit; eigenvalue units not supplied | Shared EigenvalueScree in eigenvalue mode | Eigenvalue SVG / explanatory values and full-trace note / exact eigenvalues |
| Raw neighbors | `metrics.raw_neighbors` | Original raw space; recorded query/reference counts and exclusion rule | Scalar table + original object | Same table / table / original slot |
| PCA neighbors | `metrics.projected_neighbors` | Resolved PCA space; same exclusions | Separate table | Separate table / table / original slot |
| Density and sizes | `metrics.density` and label counts | PCA scope; acquisitions, negative labels are noise | Parameters/counts/provider summary + cluster-size table | Same; no stability/independence inference |
| Factor correspondence | Original D6.1 `factor_questions[].values` | Original source/population/representation; eta² and ARI kept separate | Dedicated table, original membership flag | Same table / table / original values |
| Sensitivity mechanisms | Original D6.1 `mechanisms[].kind/values/description` | Source-matched as declared, never inferred | Mechanism table and individual measurement tables | Same; representation and density parameter kinds remain distinct |
| D1 measured observations | Original warning's `observation` | Original warning `evidence_scope` | Readable findings and exact observation anchors | Same anchors / textual references / original warning preserved |
| D2 conditional reading | Original `d2.value.interpretations` | Original declared objective and actual split | Separate supported/stronger-claim table | Same; unknown intent keeps alternatives |
| D3 | Original companion if carried | Actual original predictive comparison only | Scalar overview or unavailable slot | Same; public tablet has no D3 prediction |
| D6 readiness | Original records and optional D6.1 selected checks | Exact original action/scope | Observation/input/protocol/authority/execution table | Same; no execution caused by rendering |
| D6.1 decision reading | Original optional decision object | Original source and limitations | Factor/mechanism/readiness tables + original prose | Same object and tables; no new summary scientist |
| Missing/contradictory/error states | Original status/reason/value | No fabricated counts/values | Localized labels and original reasons | Preserved in all formats |

PCA axis percentages use `100 * eigenvalue / full_covariance_trace`; the
retained sum is never a denominator. Axis ticks/percent labels use six significant
digits for legibility; tables use up to 17 digits and scientific notation for
extremes, and original JSON retains every supplied number. No new metric or
uncertainty estimate is computed. Counts are literal label frequencies, not
certified units. At most six declared group colors are carried into static
exports; larger group dictionaries remain neutral and retain their labels in
the original points. Declared groups never become HDBSCAN labels or physical units.

Generic tables expose at most 160 simple fields. Skipped coordinate/label/large
array payloads remain in their full original object; no sampled statistic is
substituted. Specialized factor/readiness tables use only actually carried
records. An unresolved evidence ID produces an explicit explanation, never a
link to a different metric. All new source strings are escaped before HTML or
CommonMark serialization. Exported spectral polylines and opt-in raw-X export
remain outside F1.
