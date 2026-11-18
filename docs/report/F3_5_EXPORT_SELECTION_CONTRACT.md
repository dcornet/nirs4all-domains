# F3.5 export selection contract and staged expectations

Base: F3 `80a5c19704c2f9015735d2a56952c269c6a0ecae`; F2/F3 remain open, so
F3.5 targets `feat/domains-technical-f3`. Only Domains changes. Preflight 0.1.6,
Methods 1.3.13 / ABI 2.20, numerical sources, fixtures and dependencies stay fixed.

Before implementation/tests: `domains.report_export_selection.v1` is additive
presentation metadata. Mandatory identity/context, findings/checks, missing
information/limitations and evidence/status/value references cannot be disabled.
Every carried finding is mandatory regardless of status or numerical magnitude.
No new importance score or scientific threshold. Core recorded values remain
readable even when optional figures/tables are unchecked. No reconstructed saved
coordinates, invented execution, raw-X export, numerical refit or page cap.

Stable optional IDs describe actual carried figures, tables, methods, neighbors,
clustering, factors, sensitivity, readiness, extended provenance, glossary and
machine evidence. Missing sections remain disabled with an explicit source reason.
Requested unavailable sections are recorded/explained, never manufactured. Scope
and availability are checked against the current dataset/report. Choices live in
component memory, survive language/intention changes and reset with a new dataset.

Absent selection retains historical complete/F2 `reading_mode` serialization.
Custom selection controls readable/printed content independently of numerical
evidence. JSON remains complete; HTML retains the complete original model in a
named technical space; Markdown retains one safely fenced complete JSON object.
Machine payloads print only when explicitly requested, without a length cap.

Resource baseline: 20,807,240,959 / 20,826,468,033 bytes; 19,227,074 bytes available.
Campaign remains 2,015,788,498 / 2,023,410,176 bytes. Freeze additional local work
at 12 MiB engineering plus 2 MiB essential receipts, within the existing ceiling;
zero new scientific reservations, no ceiling increase, 2 GiB free-volume reserves.
Use existing installed tools for small checks; candidate installs/native builds,
screenshots and long A4/Letter PDFs run in hosted CI. No local package installs,
native rebuild, duplicated dataset, deleted history or Research write.

Required adversaries include missing/contradictory evidence, live/saved, 1D/2D/no
PCA, all-noise, scope mismatch, hostile CommonMark/HTML, unchanged source objects,
long tables/prose beyond historical display truncations, every section combination,
language/intention/dataset changes, offline links/CSP and actual A4/Letter print.
All F1–F3 gates and original tolerances remain required on the delivered SHA.

## Source-level frontend API

```ts
const selection = createSelection(view, ['pca_scores', 'readiness']);
const model = reportModel(view, originalScientificReport, 'unknown', 'en',
  declarations, 'complete', selection);
const html = serializeReport(model, 'html');
const integralJson = serializeReport(model, 'json');
```

Functions are exported from `demo/src/report/selection.ts`, `model.ts` and
`export.ts`; this extends the existing frontend, not the Rust/CLI numerical API.
The contract records immutable mandatory IDs, optional/available/requested/selected
IDs, unavailable reasons, exact evidence IDs/pointers, dataset/source/content/
protocol scope, live/saved mode and memory-only action provenance. Unknown IDs,
versions, changed mandatory lists, stale scope/availability or invalid provenance
are refused; JSON object-key order has no semantic significance.

Optional IDs: `pca_scores`, `pca_scree`, `detailed_tables`, `methods_parameters`,
`neighborhood`, `clustering`, `experimental_factors`, `representation_sensitivity`,
`readiness`, `extended_provenance`, `glossary`, `machine_evidence`. Availability
follows actual transported slots/coordinates/source references, never magnitude
or a favorable finding. Requested unavailable IDs remain explained in metadata
and reading, without a fabricated section. Core values/status/reason/scope,
definitions, limits and canonical evidence anchors remain unconditionally readable.
Custom scalar tables have no 160-field cap. Original transport/request/parent
objects remain in full machine evidence, not reclassified as new observations.

For F4.3, `representation_sensitivity` links to the exact carried
`domains.browser_preprocessing_sensitivity_result.v1` objects and derived-source
figures/tables. It is optional presentation content; omitting its figure/table
does not remove the scientific evidence object or alter its statuses, reasons,
parameters, hashes, lineage or limitations in complete HTML/JSON machine
evidence. It adds no cross-representation PCA metric or preprocessing ranking.
See the [F4.3 representation contract](../browser/F4_3_REPRESENTATION_CONTRACT.md).

Absent selection retains historical F1/F2 output. Custom choice sets the UI to
complete and disables legacy reading switches until reset; the selected reading
controls print. Reset removes custom metadata and restores complete defaults.
Language/intention changes preserve IDs; dataset loads reset choices. Nothing
is persisted to localStorage. Numerical evidence is never filtered or refitted.
