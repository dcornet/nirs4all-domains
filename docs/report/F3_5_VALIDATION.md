# F3.5 qualification record

Base: F3 `80a5c19704c2f9015735d2a56952c269c6a0ecae`; F2/F3 remain open.
The F3.5 PR records final SHA, actual Windows/Ubuntu runs, reviewed artifacts,
resource closure and justified readiness. Configuration or a baseline pass alone
does not qualify the candidate. Expectations/budget were frozen in the contract.

Initial local checks: **101 frontend tests**, retaining all 85 F1–F3 tests and
adding 16 cases for none/all/figures/tables/provenance, availability/readiness,
1D/2D/missing PCA, all-noise/contradiction, stable IDs/scope refusal, language,
old readings, hostile CommonMark, full JSON, no display-X and long text/650 fields.
Local installed dependencies are the existing cohort; clean candidate installation
and native checks run hosted. Numerical fixtures/tolerances remain unchanged.

Browser hooks consume existing live/saved results. Export choices create no
workers; explicit intent changes use only the existing interpretation operation,
retaining exact metrics/evidence hashes. Saved choices and the long documentary
copy create no numerical worker. Tests cover core/figures/all, saved core/some/all,
language/intention preservation, dataset reset, mobile FR, offline links/CSP and
print. The original frozen fixtures/files are not rewritten.

Eight cases produce actual A4 and Letter PDFs (16 files) in hosted artifacts.
The long case is an explicitly unauthenticated synthetic documentary copy of the
public saved aggregate: existing numerical values are unchanged, with long text
and 650 string fields added solely to exercise pagination. All PDFs are checked
for source-end markers, machine selection, dimensions, blank pages and visible
text bounds. Representative real PDF pages are rasterized for visual inspection;
no maximum page count applies. The long reading is checked with and without
machine printing so a complete JSON appendix cannot hide a truncated readable table.

Initial browser head `04dc294` passed core/figure/all live and saved selections,
language/intention and dataset-reset checks, then failed exact source equality in
the long imported-saved case. The existing adapter aliased `source.limitations`;
an import-specific UI authenticity notice therefore mutated the scientific source.
The adapter now copies that array. A targeted test reproduced the mutation before
the fix; all original evidence equality checks remain strict. An added core-print
test also removes duplicate header JSON from custom readings. Final-head gates
remain required after these corrections; preliminary failures are not called green.

Head `d9a2c78` then passed all eight export cases and generated 16 PDFs before
the mobile stress check exposed an unbroken saved-PCA unavailability reason.
Development-only reproduction (existing installed cohort, strict 960 MiB Windows
process-tree guard) measured 622-pixel document width at a 390-pixel viewport.
Inherited `overflow-wrap:anywhere` on the workspace content reduced it to 390,
with no text clipping or hidden overflow; unrelated title/grid changes were not
needed. The candidate must still pass this unchanged assertion in hosted CI.

Implementation head `330fd9a627f46137797f4998b38567e8097a803b` passed both
Windows/Ubuntu jobs in [browser run 43962110777](https://github.com/dcornet/nirs4all-domains/actions/runs/43962110777),
[scientific gates 43962110850](https://github.com/dcornet/nirs4all-domains/actions/runs/43962110850)
and [report contracts 43962110650](https://github.com/dcornet/nirs4all-domains/actions/runs/43962110650).
That browser run records 57 checks per platform, Chromium 159.0.8154.6 / bounded
Firefox 159.0, and zero ordinary console/page/upload/off-origin violations.

The Ubuntu PDF reader processed all 16 PDFs: core live 25/27 pages, selected
figures 28/30, full live 137/145, core saved 38/39, selected saved 52/55, full
saved 258/273, long reading 153/161, long machine 452/477 (A4/Letter). All source
end markers, paper dimensions, blank-page and text-bound checks passed. These are
actual implementation-head measurements, not page budgets or final-head counts.
Proof ZIP SHA-256 was verified before inspecting its pages/captures in memory.

Manual raster review then identified dense structured JSON cells in the readable
tables. A regression reproduced this presentation defect. Custom tables now use
the existing F1 renderer with recursive lists/definition fields, retaining every
value; complete JSON stays in the technical space. Legacy rendering is unchanged.
Final review also samples actual figure/readiness/last-long-row pages, including
Letter. All 102 current frontend tests pass locally after these changes. The
final delivered SHA still requires its own complete Windows/Ubuntu qualification.

Candidate `824b37c01f004fd0a4d7507be6027cf137114c2e` also passed both platforms in
[browser run 43965205356](https://github.com/dcornet/nirs4all-domains/actions/runs/43965205356),
[scientific gates 43965205296](https://github.com/dcornet/nirs4all-domains/actions/runs/43965205296)
and [report contracts 43965205381](https://github.com/dcornet/nirs4all-domains/actions/runs/43965205381).
Its 16 PDFs passed automated inspection; the long readings reached 180/191 pages
and the explicitly selected machine appendices 479/507 pages (A4/Letter).
Manual review of the figure, saved readiness and last long-table pages found a
PCA axis-label/tick overlap and remaining serialized scope strings. The final
presentation correction widens the axis gutter, bounds tick notation (the exact
values remain in evidence), and renders every carried JSON-object scope as
readable fields. Ordinary source prose is retained literally; full source identity
is in the mandatory context. Source objects and numerical fixtures stay unchanged.
The 102 frontend tests pass locally, including the scope regression.

The isolated mobile component capture originally contained an overlaid sticky
navigation bar. The capture helper now hides navigation only while taking that
component image. An additional unmodified viewport image and the post-capture
width assertion record the actual UI; the receipt states this capture scope.
Hosted print checks also test axis-label/tick intersections. These last changes
require another exact-head run before the PR is ready; earlier green runs are
evidence for their own commits only.

PDF inspection uses test-only **PyMuPDF 1.28.2**, canonical hash-locked wheels,
no dependencies, in hosted CI. It is AGPL-3.0 / commercially licensed and is not
bundled with the application. The larger 2.x layout/model dependency cohort is
not used. OSV returned no known advisory for 1.28.2 at the 2026-11-16 review;
this is not a security certification. APIs follow official
[text extraction](https://pymupdf.readthedocs.io/en/latest/recipes-text.html) and
[page rasterization](https://pymupdf.readthedocs.io/en/latest/recipes-images.html)
documentation. No OCR, model or scientific processing is added.

All scientific/native/ignored/bridge/schema/history, actual WASM, frontend,
security/offline/browser, F3 performance, licence and no-diff gates remain.
No new real-source experiment, owner edit, version bump, release, automatic merge
or branch Pages publication. Actual final outcomes belong in the matching PR.
