# F4.0 browser import architecture

This note records the import and provider boundaries for the F4.0 Domains
browser work. It describes package declarations and source contracts inspected
locally; it is not evidence that a clean install, browser bundle, or runtime
execution succeeded. F4.0 access and operation expectations are frozen in
[F4.0 data access policy](F4_0_DATA_ACCESS_POLICY.md).

## Package evidence

The Domains demo manifest pins `@nirs4all/io-wasm` 0.2.14,
`@nirs4all/formats-wasm` 0.2.14, `nirs4all-ui` 0.2.5, and its local
`@nirs4all/domains` binding. The binding manifest pins `@nirs4all/methods`
1.3.13. The local installed Methods package under `bindings/wasm/node_modules`
also reports 1.3.13. These are version declarations, not runtime qualification.

The checked-in lock records UI 0.2.5, but the existing demo `node_modules`
contains UI 0.2.1. Therefore local UI inspection is not proof of the pinned
0.2.5 package's API or execution. The package manifest and lock remain the pin
evidence; a clean published 0.2.5 artifact check is separate. No dependency
upgrade or upstream change is part of this architecture note.

## IO and Formats responsibilities

Domains' F4.0 import path is `demo/src/engine/import-draft.ts`, dispatched by
`demo/src/engine/dataset-io.ts`:

- `prepareDataset` loads Formats `openWithSidecars` for non-tabular spectral
  files; tables remain raw inputs for IO's table reader. IO `inferDataset`
  provides a provisional plan and descriptors for the UI's explicit role,
  column, and join review.
- `builderSpec` translates reviewed source and column choices to an IO
  `DatasetSpec`; `assembleDatasetDraft` validates and assembles that spec
  through IO. Import dispatch requires a reviewed role configuration. IO's
  `proposeDataset` is available in the package declarations, but the current
  importer uses `inferDataset` and the shared builder review seam.
- IO's public WASM declarations in
  `@nirs4all/io-wasm/types/nirs4all-io.d.ts` expose `inferDataset`,
  `proposeDataset`, `assembleDataset`, and `validate`. `proposeDataset` exposes
  proposals and confirmed locks; Domains' virtual module seam currently
  declares inference, assembly, and validation.
- Formats owns supported spectral-file decoding and sidecars through
  `openWithSidecars`; IO owns tabular parsing, role assignment, joins, and
  partitions during assembly. Domains should preserve that boundary.

The direct `assembleDataset` full-value wire is assembled schema v2. Its blocks
carry row counts, ordered source IDs, X matrices, feature headers and units, Y,
categorical target descriptions, and metadata; identity declarations are
serialized under `identity.provenance`. The v2 constant and serialization are
in IO's `crates/nirs4all-io-core/src/materialize/assemble.rs`, and the WASM
smoke fixture asserts v2. IO's internal `DatasetPackage` is a distinct v3
typed package that can round-trip an assembled v2 dataset; it is not the direct
`assembleDataset` wire. Consumers must not treat these version numbers as
interchangeable.

The current F4.0 `adaptImported` path explicitly requires v2. It retains
declared train/test/predict or unpartitioned partitions, original headers,
metadata, targets, nullable X and explicit missingness masks. A generated
technical row key addresses each assembled row separately from declared
observation IDs. Import refuses implicit multi-X fusion and incompatible axes.
It creates no scientific request or fit; the least-access operation projector
later chooses the rows and fields for a requested operation. IO
`na: { policy: "ignore" }` is the assembly setting for preserving missing
cells; it does not authorize imputation or silently dropping rows. Whether a
requested operation can handle those missing values is a separate
validation/execution decision.

## Shared Dataset Builder seam

The Domains F4.0 import view composes the shared `DatasetBuilder` with parsed
`DatasetSource` descriptors, receives source edits through `onChange`, and
receives declarations through `onExport`. In the inspected local UI 0.2.1
artifact, the `nirs4all-ui/datasetBuilder` subpath exposes `DatasetBuilder`
alongside pure helpers including `autoDetectSource`, `validateBuilder`,
`deriveSchema`, and `buildExportConfig`. The manifest and lock pin 0.2.5, but
that installed 0.2.1 artifact is not evidence of 0.2.5 compatibility or
execution; verify the pinned published artifact separately.

The builder is a view and declaration editor. Its export config is not an IO
`DatasetSpec`; a host adapter must translate chosen roles and joins into an IO
spec, call IO `validate`, then use IO `assembleDataset`. The local Preflight
reference checkout's `demo/src/dataset-io.ts` shows this seam in
`prepareDataset`, `builderSpec`, and `assembleDraft`.
Domains can reuse the composition pattern while keeping its own allowed
operations and owner contracts. A builder validation status is not an
authorization to assemble or analyze; the host's explicit confirmation and
operation policy remain authoritative.

Join declarations must use explicit keys and the IO join contract. They must
not be inferred from coincident row counts or array positions. The assembled
technical row key used to carry rows through the browser is distinct from a
source-declared observation/sample ID, group ID, repetition ID, or reference ID.
It is an addressing device only: it must not replace, deduplicate, or upgrade
the scientific meaning of declared identities. Repeated declared IDs remain
repeated. Same-export positional correspondence can only be treated as
exploratory when content, counts, row order, exclusions, and the absence of
independent sorting/filtering are verified; it does not establish physical or
reference independence.

The local UI checkout/package state is behind the manifest pin, and its builder
validation is presentation-level. The host confirm/role-review flow is present
in Domains code; exact compatibility with the pinned 0.2.5 artifact and
end-to-end runtime success remain separate verification steps. No UI package
runtime-success claim is made here.

## Methods APIs inspected

The locally installed `@nirs4all/methods` 1.3.13 declarations are under
`bindings/wasm/node_modules/@nirs4all/methods/dist`:

- `preflightPca(X, k): PreflightPcaResult` returns scores, loadings,
  eigenvalues, full covariance moments, a resolution threshold, and unresolved
  component flags. It is a diagnostic call that computes one PCA result; its
  declaration provides no fitted object with a later `transform` method.
- `FlexiblePCA` is separately exported in `estimatorRolesGenerated.d.ts` as a
  `NativeEstimator` implementing `Transformer`. `NativeEstimator.fit(X, y?,
  inputs?)` and `FlexiblePCA.transform(X)` are declared in
  `estimatorRoles.d.ts` / `estimatorRolesGenerated.d.ts`. This is the public
  fit/transform estimator surface, distinct from `preflightPca`. Declaration
  presence alone does not qualify it for a particular F4.0 operation, ABI
  execution, or train/test population contract.
- `preflightFactorAssociation(factorCodes, targets, categorical,
  nPermutations, seed)` returns a factor-target effect/statistic and permutation
  summary. `statsFactorAssociationExact` offers exact factor-target
  permutations. Related `statsCorrelationTest` / `statsCorrelationExact`
  declarations cover two numeric vectors. These APIs do not themselves define
  Domains' metadata field grants, identity closure, valid exchangeability
  units, train-only scope, or missing-value policy. Domains must not create a
  local substitute statistic; qualification and the admissible request remain
  separate decisions.

Domains' current worker bridge invokes `preflightPca` for its existing PCA
operation. No new Methods owner changes, kernels, JS numerical routines, or
qualification claims are introduced by F4.0 import architecture.
