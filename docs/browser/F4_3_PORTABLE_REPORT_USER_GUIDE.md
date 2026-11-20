# Practical PDF and complete companion results

The export section offers **PDF (A4)**, **PDF (Letter)**, **Detailed CSV** and
**Results archive**, alongside the existing HTML/Markdown/JSON actions.
The archive is the easiest way to keep relative links usable: extract it into
one folder and open either PDF. It contains `report-a4.pdf`, `report-letter.pdf`,
`results.csv`, `report.json`, `manifest.json` and the embedded font's license.
The visible filenames remain useful if a PDF viewer blocks local links.

The PDF keeps populations, stages, all requested representations and refusals,
parameters, recorded figures, compact tables, findings, limits and provenance.
Large details move to an explicitly identified complete CSV counterpart. It
does not print the full interactive DOM or an enormous hidden machine annex.
Selecting report sections grants no extra permission to export metadata colors,
raw spectra or Y. The original permission-filtered structured evidence remains
in the package. Existing full HTML/Markdown exports retain their original scope.

`results.csv` is UTF-8, RFC4180 long form, not one wide model matrix. Each
record has a stable section/result/representation ID, a JSON pointer into
`report.json`, a type and an exact JSON-literal value. Empty arrays/objects,
null values and section status/refusal reasons remain explicit. Zero-based
row/column indices and carried observation/axis keys accompany applicable values.
`unit_json` carries original axis units for axis cells; null means no unit was
carried for that scalar. Other explicit source unit fields remain ordinary CSV
records. Original strings/IDs are JSON-encoded, including spreadsheet-formula
characters; use a CSV parser and JSON-decode those cells to recover the originals.

The manifest documents columns, row counts, ordering, section scopes/providers,
JSON pointers and hashes of actual companion files. It does not invent absent
loadings or unavailable statistics. Scientific result digests remain integrity
and lineage references, not a cross-backend numerical equality requirement.

On screen, complete F4.3 tables load when their disclosure opens. Choose a
scientific table and use Previous/Next to inspect its 200-row pages. Closing
the disclosure releases its table DOM; all complete values remain available
in CSV/JSON. Representation availability and unfavorable/refused entries stay
visible even while details are closed.

The [v2 verification/presentation contract](F4_3_FINALIZATION_CONTRACT_V2.md)
defines admission and qualification. A working PDF or browser is not numerical
portability, predictive validation or a recommendation of preprocessing.
Methods 1.3.13 / ABI 2.20 remains pinned pending the externally delegated PCA
correction and a separate provider-admission stage. PR #16 remains a draft.
