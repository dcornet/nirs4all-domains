# Packaged alignment adapter contract

`domains.same_export.v0.2` requires an explicit export receipt for unkeyed Y:
owner attestation, identified export, dataset/content/source scope, preserved
order and X/Y/M SHA-256 bindings. Matching counts or X/M keys alone must refuse.
Explicit keyed Y joins still require the same declared dataset/content namespace.
If M has no observation key, its order also requires the content-bound export
receipt, even when Y is keyed. Declared X counts must match the actual keys.
The exact historical-no-split marker is a recommendation without memberships;
actual train/test columns still take precedence. The project's previously sealed
identities must additionally be carried forward by the campaign controller.

Expected adversarial behavior, stated before final tests: unrelated but equally
sized unkeyed Y refuses without the receipt; mismatched file bindings refuse;
conflicting X/M order refuses; keyed Y cannot authorize an unrelated unkeyed M;
retained component closure remains unchanged.
The existing focused fixture exercises refusal and the positive content-bound
receipt. It also verifies the documented no-membership marker.

Executed alpha.18 bank controllers already had the owner's explicit global
same-export attestation and frozen input identities. Their actual source is
archived. This delivery refinement makes that trust explicit for future callers
of the shared helper; it does not reinterpret or rerun those experiments.
Numerical fitting/scoring/fold functions remain byte-equivalent at AST level to
the qualified grouped-source version. No new secret, approval or privacy layer.

Pass `export_contract` to `metadata_scope` (or place it in
`entry["same_export_contract"]`). Required fields are `dataset_id`,
`content_version`, `source_id`, nonempty `export_id`, `owner_attested: true`,
`order_preserved: true`, and `sha256` with `X`, `Y`, `M` content digests for
participating files. One receipt covers all genuine targets in the export;
it is a data-binding contract, not a new publication approval transaction.
