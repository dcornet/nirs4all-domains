# F4.0 metadata protocol and report boundary

This note records the F4.0 browser protocol contract and report projection. It
does not qualify the browser execution path or extend the scientific meaning of
any provider result. The governing access rules are in
[`F4_0_DATA_ACCESS_POLICY.md`](F4_0_DATA_ACCESS_POLICY.md).

## Inventory and evidence

Import retains X, Y, metadata, missingness, original identities and partition
membership. The report inventory exposes dataset/source/content declarations,
counts, missing counts, field names, declared role/type/origin, target-derived
flag and evidence state. It never returns raw X, Y, or metadata values. A field
whose role, type, origin or target derivation is unknown remains marked unknown;
the UI does not infer a scientific meaning from its name or value shape.
Metadata values are aligned to imported `rowManifest` order. A display color join
is valid only when the field has one value for every manifest row and every
plotted technical key exists uniquely in that manifest.

Every scoped operation is represented by its own evidence item and receipt:
operation and diagnostic, status/reason, fit/reference/query populations,
partitions and fields accessed, provider, value, supported claims, limitations
and next action. A refusal is local to that operation and is not reported as a
negative scientific finding. Imported population counts remain distinct from
the analyzed subset counts. The report must state the access and analysis scope,
including whether test X was accessed and that Y was not accessed.

The exact Preflight metric name `cross_partition_exact_duplicate_pairs` is
retained. Its result excludes pairs with equal declared physical IDs; overlap
under the declared physical identity is documented separately. An exact spectral
match is not a physical-identity claim, and absence of detected matches does not
establish independence.

## Metadata use and display

Metadata factor and cross-partition metadata audits are documentary counts,
missingness, cardinalities, level counts and literal set intersections. They do
not implement association tests. X–M association and train-fitted PCA projection
remain unavailable in this browser protocol until the exact operation is bound
to a qualified public owner API and browser execution is qualified. Public
Methods flexible PCA fit/transform and factor-association APIs exist; this
statement describes the current browser integration seam, not an absent owner
API.

An optional PCA display color field is presentation-only. It is eligible only
when it is explicitly selected, not marked target-derived, and can be joined to
every plotted point by the technical row key. Explicit target derivation blocks
coloring; unknown derivation remains labeled unknown in report provenance. The
operation does not change PCA coordinates, scientific evidence, neighbor
exclusion, or any calculation. Missing field values receive an explicit missing
category. If exact manifest alignment is unavailable or incomplete, the display
explains that coloring is unavailable. Imported declarations may be unverified
and retain that evidence state.

Y values are never used for X-only interpretation, selection, fitting or
coloring. A target-derived metadata field is not eligible for primary X-only
interpretation or coloring. No predictive model, target-driven choice, automatic
tuning, causal conclusion or risk score is produced.

## Export

Existing F1/F2/F3.5 report renderers carry the safe inventory and scoped receipts
as documentary evidence. Raw X/Y matrices and unrestricted metadata values are
not included. Operation values are restricted to provider evidence and receipts;
the machine appendix must not serialize imported payloads. Existing saved report
and legacy live report paths keep their prior contracts and annotations.

Implementation and qualification are pending. The policy document defines
expected behavior; it is not evidence that every operation or browser provider
path has passed its gates.
