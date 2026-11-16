# F1 baseline audit

Source: remote main `457227a743f7f0655e8f858d029469bead8d94ec`, inspected before
implementation. Dedicated branch: `feat/domains-report-f1`. No source science,
provider, frozen annotation, package version or licence changes are authorized.
Both Domains checkouts lack an exact CodeGraph index; current AGENTS forbids
ancestor indexes/automatic indexing, so actual source and contracts were read.

| Evidence / original object | Mode / population / representation | Current screen | HTML / Markdown / JSON | Debt |
|---|---|---|---|---|
| Imported spectra / local X | Live, complete observations, original axis | Shared SpectraExplorer, selection/axis zoom | No raw X / no raw X / no raw X | P1: missing export explanation; saved has empty controls |
| PCA scores / metrics.pca | Live, complete X, centered raw PCA | Shared ScoreMap | Minimal ungraduated SVG / absent / original scores | P1: no common figure explanation; one PC uses zero display coordinate |
| Eigenvalues/full moments | Live, same PCA | Shared EigenvalueScree | Absent / absent / original values | P1: loss between formats |
| Raw neighbors | Live, complete raw reference; declared exclusions | Folded JSON | Folded JSON / JSON fence / original values | P1: no readable metric or distance definitions |
| Projected neighbors | Live, resolved PCA space; same exclusion rule | Folded JSON | Folded JSON / JSON fence / original values | P1: representation/units obscure |
| HDBSCAN labels/noise/persistence | Live, one fixed fit in resolved PCA | Folded JSON | Folded JSON / JSON fence / original values | P1: computed all-noise not explained; no cluster-size table |
| Factor association / D1 measurements | Saved, exact source scope, raw tablet | Nested JSON in d1 | JSON only | P1: factor/PC versus partition agreement inaccessible |
| Representation/density comparisons | Saved, matched scope as declared | D1 nested JSON | JSON only | P1: density-versus-representation distinction buried |
| D1 warnings | Saved, five original assessment states | Cards | Cards / prose / originals | P0: warning-ID links have no corresponding evidence row |
| Live findings and intent | Live X-only observations, no prediction | Cards | Cards / prose / originals | P0: report hash treated as a nonexistent metric anchor |
| D2 deployment reading | Saved original companion | Nested JSON | Nested JSON | P1: conditional alternatives and missing facts hard to read |
| D3 predictive comparison | Saved only if supplied; public tablet unavailable | Unavailable slot | JSON | Preserve refusal: no predictive result may be manufactured |
| D6 readiness | Saved exact action/scope | Nested JSON | JSON | P1: inputs/protocol/authority/execution not readable |
| D6.1 decision summary | Saved, original optional presentation | Summary partly flattened; provenance JSON | JSON | P1: mechanisms/factor questions/checks not exposed |
| Missing/contradictory/unsupported states | Both; original status/reason/value | Badges and original text | Uneven localisation, null/count formatting | P1: zero variables rendered via falsy fallback in exports; P2 print/details/localisation |

No model operation is needed to correct these defects. The F1 presentation must
reference original values and keep original source prose distinct from bilingual
pedagogy. Raw spectra stay screen-only. A saved example has no reconstructed
scores or spectra; categorical metadata never certifies physical units. Existing
CommonMark adversaries, frozen fixtures, native defaults and source hashes remain.

The public Preflight reference and installed shared UI are presentation references,
read-only. Their shared chart/brand APIs remain in use; no upstream component is copied.
