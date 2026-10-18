# Disclosure policy — domains.disclosure.v0.1

Expected publication behavior, fixed before the adversarial tests:

Numerical success never causes publication. A local record has private taint and
an opaque random receipt. Exact source fingerprints, identities, dimensions,
paths, coordinates, per-observation values and free text are local by default.
Pseudonyms are not automatically public identifiers. A public candidate uses a
closed schema containing only policy-enumerated aggregate indicators, fixed
status/reason codes, and opaque audit/review receipt identifiers. Unknown and
nested fields fail closed. No general private-report-to-public-copy operation.

Aggregate rights, permission to disclose participation and confidentiality review
are separate requirements. Without all necessary approvals, use local_only or
blocked_pending_review and create no public numerical file. A local approval
binds exact candidate bytes, source permission receipts, policy version and all
previous release digests. Changing any binding invalidates approval. Multiple
exports must be reviewed jointly rather than each being treated as isolated.

Small-cell control is configurable and is not an anonymity guarantee. For an
approved partition count table, suppress positive cells below its reviewed
minimum. If a published total would reveal the sole suppressed cell, suppress
an additional nonempty cell, or suppress the total. Unreviewed overlapping
marginals and cross-table joins are blocked. Extreme values, distinctive source
sizes, rare combinations and scientific participation need separate review;
ordinary scalar aggregation does not discharge those requirements. No
differential privacy mechanism or general anonymity claim is made.

The export operation writes only an independently validated, specifically
approved candidate. It never uploads. Public validation checks schemas and
visibility/provenance as well as literal sensitive-byte canaries. Outgoing review
covers tracked and staged bytes, paths, Markdown/JSON/CSV, figures and metadata,
logs and traces, package members, fixtures, models and build manifests. Newly
generated alpha.14 public scientific artifacts require approved receipt-bound
provenance; unknown formats are denied. Synthetic/public fixtures alone run in
CI. Historical publishable artifacts retain their baseline hashes.

On failure emit a fixed code, never the offending value, and leave local
scientific evidence untouched. Private mappings and secrets stay outside Git;
`.gitignore` is only one additional defense. These are tested application
boundaries, not a guarantee against deliberate bypass through external tools.
