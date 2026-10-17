"""Pre-performance rights/semantic/identity decisions; no acquisition or numerics."""
from __future__ import annotations

from .storage import fingerprint

PROTOCOL = "domains.admission.v0.1"
DIMENSIONS = ("access", "local_analysis", "publish_statistics", "redistribute_raw")


def target_semantics(target):
    """A numeric dtype is insufficient; require a documented measurement."""
    name = target["name"].lower()
    identifier = name in {"id", "x", "number", "individual", "genotype", "sample_number", "house_num"} or name.endswith("_id")
    if identifier or target.get("semantic_role") != "quantitative_measurement":
        return "NUMERIC_IDENTIFIER_OR_UNQUALIFIED_TARGET_SEMANTICS"
    if not target.get("meaning") or not target.get("unit") or not target.get("evidence"):
        return "MISSING_TARGET_MEANING_UNIT_OR_SOURCE_EVIDENCE"
    return None


def freeze_admission(specification):
    """Deliberately accepts no observed model scores or post-evaluation selection."""
    required = {"dataset_id", "catalog_revision", "content_version", "source_hashes", "scientific_reference",
                "permissions", "source_id", "target", "identities", "dependencies", "factors", "representation",
                "split", "independent_units", "missing_fields", "budget", "review_evidence"}
    if set(specification) != required:
        raise ValueError("COMPLETE_PRE_PERFORMANCE_ADMISSION_SPECIFICATION_REQUIRED")
    reasons = []
    permissions = specification["permissions"]
    if set(permissions) != set(DIMENSIONS):
        raise ValueError("FOUR_SEPARATE_PERMISSION_DIMENSIONS_REQUIRED")
    for dimension, decision in permissions.items():
        if set(decision) != {"status", "evidence"} or decision["status"] not in ("allowed", "denied", "unknown"):
            raise ValueError("INVALID_PERMISSION_EVIDENCE")
        if decision["status"] != "unknown" and not decision["evidence"]:
            raise ValueError("PERMISSION_REQUIRES_EXPLICIT_EVIDENCE")
        if dimension != "redistribute_raw" and decision["status"] != "allowed":
            reasons.append(dimension.upper()+"_"+decision["status"].upper())
    semantic = target_semantics(specification["target"])
    if semantic:
        reasons.append(semantic)
    identities = specification["identities"]
    for field in ("original_sample_keys", "source_reference_alignment"):
        if identities.get(field, {}).get("status") != "verified" or not identities[field].get("evidence"):
            reasons.append("UNVERIFIED_"+field.upper())
    if not specification["source_hashes"] or not specification["scientific_reference"] or not specification["review_evidence"]:
        reasons.append("MISSING_PINNED_SOURCE_OR_REVIEW_EVIDENCE")
    if not isinstance(specification["independent_units"], int) or isinstance(specification["independent_units"], bool) or specification["independent_units"] < 2:
        reasons.append("INSUFFICIENT_DECLARED_INDEPENDENT_UNITS")
    result = {"schema_version": 1, "protocol_version": PROTOCOL, "specification": specification,
              "status": "admitted" if not reasons else "pending", "reasons": sorted(reasons),
              "selection_basis": "source documentation, metadata identities and budget; no prediction scores"}
    return {**result, "admission_id": fingerprint(result)}


def verify_admission(record):
    if freeze_admission(record["specification"]) != record:
        raise ValueError("ADMISSION_CONTENT_OR_DECISION_MISMATCH")


def paired_keys(sources, axes, evidence):
    """Audit explicitly supplied original keys; no row-number pairing or axis fit.

    Shared assays across physical objects require the existing intrinsic/reference
    dependency audit before a paired evaluation; this small adapter refuses them.
    """
    if len(sources) < 2 or set(sources) != set(axes) or not evidence:
        raise ValueError("PAIRED_ORIGINAL_SOURCE_EVIDENCE_REQUIRED")
    indexes = {}
    for name, rows in sources.items():
        index = {}
        for row in rows:
            if any(not row.get(k) for k in ("sample_key", "physical_id", "reference_key", "reference_unit")):
                raise ValueError("MISSING_ORIGINAL_SAMPLE_OR_REFERENCE_KEY")
            key = row["sample_key"]
            if key in index:
                raise ValueError("AMBIGUOUS_SOURCE_SAMPLE_KEY")
            index[key] = row
        indexes[name] = index
    first = indexes[sorted(indexes)[0]]
    if not first or any(set(v) != set(first) for v in indexes.values()):
        raise ValueError("UNMATCHED_SOURCE_SAMPLE_KEYS")
    references = {}
    for key in sorted(first):
        expected = first[key]
        for index in indexes.values():
            row = index[key]
            if any(row[k] != expected[k] for k in ("physical_id", "reference_key", "reference_unit")):
                raise ValueError("CROSS_SOURCE_IDENTITY_OR_REFERENCE_CONTRADICTION")
            if "reference_value" in row and "reference_value" in expected and row["reference_value"] != expected["reference_value"]:
                raise ValueError("CONTRADICTORY_REFERENCE_VALUES")
        references.setdefault(expected["reference_key"], set()).add(expected["physical_id"])
    if any(len(v) > 1 for v in references.values()):
        raise ValueError("SHARED_ASSAY_REQUIRES_DEPENDENCY_COMPONENT_AUDIT")
    if len({r["physical_id"] for r in first.values()}) != len(first):
        raise ValueError("MULTIPLE_KEYS_FOR_ONE_PHYSICAL_SAMPLE_REQUIRE_REPEAT_AUDIT")
    equal_axes = all(axis == axes[sorted(axes)[0]] for axis in axes.values())
    return {"sample_keys": sorted(first), "n_physical_samples": len(first), "n_sources": len(sources),
            "paired_keys_sha256": fingerprint({k: {f: first[k][f] for f in ("physical_id", "reference_key", "reference_unit")} for k in sorted(first)}),
            "axes_sha256": {k: fingerprint(v) for k, v in sorted(axes.items())},
            "direct_transfer": {"status": "computed" if equal_axes else "unavailable",
                                "reason": None if equal_axes else "DIFFERENT_AXES_REQUIRE_A_PRESPECIFIED_QUALIFIED_TRANSFORMATION",
                                "value": True if equal_axes else None},
            "scope": "paired measurement contexts; does not establish new-physical-sample generalization"}
