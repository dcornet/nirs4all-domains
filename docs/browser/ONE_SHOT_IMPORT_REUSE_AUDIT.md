# One-shot import reuse audit

Read-only source audit for the one-shot import flow. No upstream changes are
proposed here. Project ownership remains as specified in
[architecture](../ARCHITECTURE.md), [method reuse](../METHOD_REUSE_MATRIX.md),
and [scientific protocols](../SCIENTIFIC_PROTOCOLS.md): IO/Formats own decoding,
identity, joins and assembly; Domains owns task admission and interpretation.

## Pinned evidence

The Preflight source reviewed is `GBeurier/nirs4all-preflight` commit
[`98af576f165abf54a6019e655a127438661a99ce`](https://github.com/GBeurier/nirs4all-preflight/tree/98af576f165abf54a6019e655a127438661a99ce).
Its `demo/src/dataset-io.ts` calls Formats `openWithSidecars`, IO
`inferDataset`, `validate`, and `assembleDataset`; it adapts the resulting
owner-assembled data in `dataset.ts`. `DatasetPicker.tsx` demonstrates a
single-submit handoff but persists the complete dataset in IndexedDB through
`dataset-store.ts` before opening it.

The shared UI evidence is the actually installed/public `nirs4all-ui` 0.2.5
package (manifest verified in the qualified checkout), pinned to tag commit
[`a79ed90df1371735539e55e6e5362ce41d588df3`](https://github.com/GBeurier/nirs4all-ui/tree/a79ed90df1371735539e55e6e5362ce41d588df3).
The separately published IO dependency in the qualified Domains demo is
`@nirs4all/io-wasm` 0.2.14 (package lock and package manifest). Its public
[`AssembledDataset` declaration](https://github.com/GBeurier/nirs4all-io/blob/v0.2.14/bindings/wasm/types/nirs4all-io.d.ts)
declares `name`, `blocks`, optional `folds`, and `warnings`; it does not declare
`assembled_schema_version` or `identity`.

This wire is not interchangeable with the Preflight checkout's own vendored IO
adapter: its `demo/src/dataset.ts` requires `assembled_schema_version === 3`
and reads `identity.provenance`. Do not copy the Preflight adapter or cast the
0.2.14 public result to its v3 shape. Bind to the published 0.2.14 declarations
and the actual wire, keep identity/version claims only where that wire supplies
them, and validate any richer sidecar contract explicitly.

## Reusable UI surface

`nirs4all-ui/components` exports `DatasetDropzone`, `DroppedFile`,
`pickedFiles`, and `droppedFiles`. `DatasetDropzone` accepts `onFiles` and
optional `onError`, labels/hints, `active`, `busy`, `accept`, and `folderLabel`.
With `folderLabel`, it provides a directory picker; dropped directories are
expanded recursively. Relative paths are retained and dotfiles are skipped.
The component passes selected files to the host and does no parsing or IO.

`nirs4all-ui/datasetBuilder` exports `DatasetBuilder`, `LiveValidationCard`,
the view-model types (`DatasetSource`, `DatasetColumn`,
`DatasetExportConfig`), and pure functions including `autoDetectSource`,
`deriveSchema`, `derivePartitionPreview`, `validateBuilder`, and
`buildExportConfig`. Controlled `sources`/`onChange` and `onExport` allow the
host to supply IO-derived descriptors, receive edits, and collect declarations.
`buildExportConfig` creates a UI config, not an IO `DatasetSpec`; host mapping
and IO revalidation remain necessary. UI role detection is heuristic and its
validation checks presence/consistency, not scientific qualification or actual
join correctness. Use it as optional editing/presentation, not as evidence of
identity or an independent assembly implementation.

Tests at the pinned UI commit cover the pure detector and builder config
(`detect.test.ts`, `engine.test.ts`). Preflight's
[`dataset.test.ts`](https://github.com/GBeurier/nirs4all-preflight/blob/98af576f165abf54a6019e655a127438661a99ce/demo/src/dataset.test.ts)
is useful precedent for keyed joins independent of row order, partition-scoped
joins, ambiguous/shared-ID rejection, sparse targets, repetition declarations,
and axis incompatibility. Its `dataset-store.test.ts` validates persistence,
which is outside this import flow.

## Current Domains integration

The production Chromium helper has passed 48 cases, including optional
pre-load settings. The final validation record and PR checks distinguish local
execution from Windows/Ubuntu CI; this count alone does not qualify that CI.

Domains uses the public dropzone for a single file/folder submission and the
public builder only as an optional editor. The normal user action runs a
preliminary IO inference/assembly preview and then final one-shot assembly in
two single-use workers; it does not ask for a mandatory confirmation. The
optional pre-load editor pauses after IO identifies sources and before final
dataset loading. Post-load Data settings use the same IO-backed rematerialize,
validate, and replacement path. Import itself never fits or analyzes data.

The `ImportOutcome` can be `loaded` with a dataset or `needs_input` with or
without one. In particular, independently validated X may load while unresolved
Y/M remains separate and dependent operations are restricted. Ambiguities that
prevent reliable loading require the relevant user choice. Domains does not
infer joins by matching counts/order. A successful parser edit is rematerialized
by IO and produces updated content provenance; no hand-written CSV parsing or
missing-token conversion is used. Session files/declarations remain in memory,
not IndexedDB. Validation-fold declarations remain in that session but are
excluded from the import execution spec; they create no split or fit, and folder
paths are not flattened based on a `fold` keyword.

The installed IO 0.2.14 public types document spectral values as float32. The
browser's wider numeric transport does not promise exact decimal precision past
that representation. Original source bytes and hashes remain provenance; they
do not make the parsed float32 values lossless.

## Reuse boundaries for Domains

The Preflight `prepareDataset` pattern is reusable: let native IO infer, parse,
and assemble; use Formats for supported spectral decoding; inspect native
identity ambiguity before treating a key as sample identity; set NA handling
to preserve missing cells; and revalidate edited declarations through IO.
Preflight's fallback checks a metadata/target table alone and keeps a candidate
key only when IO reports `identity.ambiguous === false`. Its test explicitly
rejects a dataset-level ID shared by rows. This is evidence for handling
ambiguity, not a license to infer a join from equal counts or order.

Do not reuse Preflight's full `importFiles` or `keep` flow unchanged:

- `dropEmptyBands` removes all-empty spectral columns and mutates the axis; its
  test expects that behavior. Domains' one-shot contract preserves every
  original axis and all-missing declared variables.
- `keep` writes full input and table metadata into persistent IndexedDB. The
  one-shot flow is session-only and must not add persistent raw data storage.
- Preflight's current wire adapter requires v3, while the pinned published IO
  0.2.14 public declaration does not specify that v3 identity/schema envelope.
- Existing conversion logic labels missing target values by omission and may
  filter targets with no values. Domains must retain the distinction between
  absent, all-missing, detached, and aligned Y/M sources in its own contract.

Recommended composition: public `DatasetDropzone` for file/folder handoff;
Formats and published IO 0.2.14 for supported decoding, inference, validation,
and assembly; a Domains-owned adapter that preserves source declarations,
original headers/axes, missingness, and attachment status; and the public UI
builder only when role/key/partition edits are needed. Keep data in memory for
the session, retain original file identities/hashes as provenance, and do not
run any fit as part of import.
