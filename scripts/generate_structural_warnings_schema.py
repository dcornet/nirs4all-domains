"""Generate the optional D1 sidecar; existing owner schemas stay unchanged."""

import json
from copy import deepcopy
from pathlib import Path


def record(properties, required=None):
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties) if required is None else required,
    }


def schema():
    text = {"type": "string", "minLength": 1}
    nullable = {"anyOf": [text, {"type": "null"}]}
    texts = {"type": "array", "items": text, "uniqueItems": True}
    count = {"type": "integer", "minimum": 0}
    pointer = {"type": "string", "pattern": r"^(?:/(?:[^~/]|~[01])*)*$"}
    identity = {
        k: deepcopy(text)
        for k in ("dataset_id", "source_id", "population_id", "representation")
    }
    identity.update(
        {
            "content_version": nullable,
            "scope_kind": {
                "enum": [
                    "full_source",
                    "historical_bank_full_source",
                    "historical_full_source",
                    "reference_training",
                    "synthetic",
                    "other",
                ]
            },
            "n_observations": {"type": ["integer", "null"], "minimum": 1},
        }
    )
    source = record(
        {
            **identity,
            "identity_scope": {
                "enum": ["current_canonical_id", "historical", "unknown"]
            },
            "references": texts,
            "original_source_identifiers": texts,
            "provenance_group": nullable,
            "original_study_family": nullable,
            "study_reference": nullable,
        }
    )
    method = record(
        {
            "owner": {
                "enum": ["Methods", "Preflight", "source_documentation", "Domains"]
            },
            "name": text,
            "version": text,
            "settings": {"type": "object"},
            "reference": text,
            "binary_sha256": {
                "anyOf": [
                    {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    {"type": "null"},
                ]
            },
        },
        ["owner", "name", "version", "settings", "reference"],
    )
    boolean = {"type": "boolean"}
    qualifiers = record(
        {
            "dependency_basis": {
                "enum": [
                    "declared_technical_repetitions",
                    "shared_specimen",
                    "shared_reference",
                    "qualified_preflight",
                    "x_derived",
                    "unknown",
                ]
            },
            "evidence_quality": {"enum": ["declared", "verified", "unknown"]},
            "unit_memberships_available": boolean,
            "preflight_finding_scope": {
                "enum": [
                    "declared_identity_overlap",
                    "shared_reference_overlap",
                    "spectral_duplicates",
                    "other",
                    "unknown",
                ]
            },
            "factor_memberships_available": boolean,
            "factor": text,
            "role": {"enum": ["metadata", "target", "unknown"]},
            "role_reference": nullable,
            "duplicated_from_target": boolean,
            "admissible": boolean,
            "matched_observations": boolean,
            "matched_queries": boolean,
            "representations": texts,
            "comparison_kind": {
                "enum": [
                    "representation",
                    "density_parameter",
                    "single_partition",
                    "unknown",
                ]
            },
            "fit_scope": {"enum": ["training_only", "full_x", "unknown"]},
            "evaluation_X_observed": boolean,
            "reference_population_id": nullable,
            "evaluation_population_id": nullable,
        },
        [],
    )
    metric_names = (
        "has_shared_units",
        "n_overlapping_units",
        "qualified_preflight_finding",
        "eta_squared",
        "partition_ari",
        "partition_ari_range",
        "n_levels",
        "n_missing",
        "n_repeated_acquisitions",
        "full_x_overlap",
        "pca_overlap",
        "parameter_ari_min",
        "pc1_before",
        "pc1_after",
        "cluster_counts",
        "noise_fractions",
        "all_noise_settings",
        "trivial_partition",
        "native_refusals",
        "n_exceedances",
        "n_evaluation",
        "physical_units_known",
        "acquisition_context_known",
        "reference_units_known",
    )
    metrics = record({k: pointer for k in metric_names}, [])
    binding = record(
        {
            "kind": {
                "enum": [
                    "physical_units",
                    "factor_geometry",
                    "representation",
                    "spectral_support",
                    "context",
                ]
            },
            "root": pointer,
            "scope": record(identity),
            "method": method,
            "metrics": metrics,
            "qualifications": qualifiers,
        }
    )
    d2 = json.loads(
        Path("schemas/validation-intent.v1.schema.json").read_text(encoding="utf-8")
    )
    request = record(
        {
            "source": source,
            "evidence": {"type": "array", "items": binding},
            "validation_intent": deepcopy(d2["$defs"]["request"]),
        },
        ["source", "evidence"],
    )
    unavailable = record(
        {"status": {"const": "unavailable"}, "reason": text, "value": {"type": "null"}}
    )

    def state(value):
        return {
            "oneOf": [
                record(
                    {
                        "status": {"const": "computed"},
                        "reason": {"type": "null"},
                        "value": value,
                    }
                ),
                unavailable,
            ]
        }

    coverage = record(
        {
            "canonical_dataset_ids": texts,
            "historical_or_unknown_dataset_ids": texts,
            "dataset_identities": texts,
            "n_dataset_identities": count,
            "x_views": {
                "type": "array",
                "items": record({"dataset_id": text, "source_id": text}),
                "uniqueItems": True,
            },
            "n_x_views": count,
            "eligible_cases": count,
            "computed_cases": count,
            "unavailable_cases": count,
            "original_source_identifiers": texts,
            "documented_references": texts,
            "database_count": state(count),
            "declared_provenance_groups": texts,
            "documented_provenance_group_count": state(count),
            "original_study_families": texts,
            "original_study_family_count": state(count),
            "observation_evidence_level": {"const": "descriptive"},
            "risk_evidence_level": {"const": "hypothesis"},
            "externally_validated_warning": {"const": False},
        }
    )
    check = record(
        {
            "check_id": text,
            "description": text,
            "applies_when": texts,
            "required_information": texts,
            "testability": {"enum": ["available", "requires_information"]},
        }
    )
    observation = record(
        {
            "description": text,
            "measurements": {
                "type": "array",
                "items": record(
                    {
                        "kind": text,
                        "root": pointer,
                        "pointers": metrics,
                        "values": {"type": "object"},
                        "method": method,
                        "qualifications": qualifiers,
                    }
                ),
            },
        }
    )
    warning = record(
        {
            "warning_id": {
                "enum": [
                    "physical_unit_dependence",
                    "experimental_factor_structure",
                    "preprocessing_dependent_organization",
                    "spectral_support_mismatch",
                    "insufficient_experimental_context",
                ]
            },
            "definition_version": {"const": 1},
            "status": {"enum": ["computed", "unavailable"]},
            "reason": nullable,
            "value": {"enum": ["observed", "conditional", "contradicted", None]},
            "observation": state(observation),
            "risk_hypothesis": text,
            "conditions": {"type": "array", "items": text},
            "alternative_explanations": texts,
            "recommended_checks": {"type": "array", "items": check, "minItems": 1},
            "required_information": texts,
            "evidence_scope": record(identity),
            "scientific_basis": coverage,
            "limitations": texts,
        }
    )
    warning["allOf"] = [
        {
            "if": {"properties": {"status": {"const": "computed"}}},
            "then": {
                "properties": {
                    "reason": {"type": "null"},
                    "value": {"enum": ["observed", "conditional", "contradicted"]},
                }
            },
            "else": {"properties": {"reason": text, "value": {"type": "null"}}},
        }
    ]
    root = record(
        {
            "protocol_version": {"const": "domains.structural_warnings.v1"},
            "source_report": record(
                {
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "hash_scope": {"const": "canonical_json_with_newline"},
                }
            ),
            "request": {"$ref": "#/$defs/request"},
            "validation_intent": {"type": "object"},
            "warnings": {
                "type": "array",
                "items": warning,
                "minItems": 5,
                "maxItems": 5,
            },
            "limitations": texts,
        }
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://nirs4all.org/domains/structural-warnings.v1.schema.json",
        "$defs": {"request": request},
        **root,
    }


if __name__ == "__main__":
    data = json.dumps(schema(), indent=2, ensure_ascii=False) + "\n"
    for folder in ("schemas", "bridges/python/nirs4all_domains"):
        (Path(folder) / "structural-warnings.v1.schema.json").write_text(
            data, encoding="utf-8"
        )
