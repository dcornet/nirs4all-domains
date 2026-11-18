# Import a dataset in the browser

The Domains demo accepts supported dataset files or a folder from the landing
page. Use **Load my dataset** (French: **Charger mon dataset**) and drop/select
the files in one action. Directories are read with their relative paths. A
`.nirs4all.json` configuration can be included with its referenced files.
Standalone `.json` files are saved Domains reports, not generic data tables.

## What happens after selection

The browser reads the files locally and asks the published Formats and IO
packages to identify sources, parse supported formats, validate declarations,
and assemble the dataset. A preliminary IO preview is prepared as part of this
process. The normal path then completes final assembly automatically; there is
no required review or confirmation step. Import does not fit a model or run a
scientific analysis.

When loading completes, the workspace shows a data summary and available
operations. Choose an operation separately. Existing F4 operation-specific
rules still determine which observations may be used. Y values are kept for
inventory and masking but are not sent to scientific requests or report export.

## Optional settings and unresolved sources

The landing page offers **Open advanced settings after IO identifies the
sources** (French: **Ouvrir les paramètres avancés après l’identification des
sources par IO**). This is optional. It opens the shared source/column editor
after inference and preview, before final loading. You can also open **Data
settings** in the loaded workspace. Applying an edit asks IO to validate and
assemble the edited declarations again. A successful replacement gets updated
provenance and invalidates dependent analysis results.

If X is valid but an auxiliary Y or M attachment cannot be resolved, X may
still load. The unresolved source remains separately identified, and operations
that depend on it stay restricted until the specific issue is resolved. A
blocking ambiguity asks for the necessary role, key, partition, or parser
choice. The importer does not guess joins from row counts or order, combine
separate X sources, or silently convert Y into metadata.

## What the import preserves

The session retains the original selected files, relative paths, source
declarations, original axes, declared partitions, and missingness. Missing
values and all-missing declared variables are not grounds for global row or
column removal. CSV parsing, missing-token interpretation, identities and joins
remain under the IO/Formats owner APIs; Domains does not add a JavaScript CSV
parser or reinterpret `NA` strings. IO validation-fold declarations remain in
the in-memory session but are excluded from import execution; no split or fit
is created from them. Folder names are not used to flatten or infer a split.

The import session lives in browser memory for the current page session. It does
not persist raw datasets to IndexedDB or a server. The published IO package
returns spectral values as float32; widening those values for the browser
transport does not restore decimal precision beyond the source representation.
See the [import architecture](F4_0_IMPORT_ARCHITECTURE.md),
[data access policy](F4_0_DATA_ACCESS_POLICY.md), and
[one-shot implementation plan](ONE_SHOT_IMPORT_PLAN.md) for technical detail.
