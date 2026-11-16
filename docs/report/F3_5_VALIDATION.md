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
