"""Generate an additive declaration companion; no change to D1/D2/D3 schemas."""

import json
from pathlib import Path


def schema():
    text = {"type": "string", "minLength": 1}
    nullable = {"anyOf": [text, {"type": "null"}]}
    sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}

    def obj(properties):
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }

    def state(values, extra=None):
        return obj(
            {
                "status": {"enum": ["computed", "unavailable"]},
                "reason": nullable,
                "value": {"enum": [*values, None]},
                **(extra or {}),
            }
        ) | {
            "allOf": [
                {
                    "if": {"properties": {"status": {"const": "computed"}}},
                    "then": {
                        "properties": {
                            "reason": {"type": "null"},
                            "value": {"enum": values},
                        }
                    },
                    "else": {"properties": {"reason": text, "value": {"type": "null"}}},
                }
            ]
        }

    root = Path(__file__).resolve().parents[1]
    original = json.loads(
        (root / "schemas/structural-warnings.v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    scope = original["$defs"]["request"]["properties"]["evidence"]["items"][
        "properties"
    ]["scope"]
    requirement = obj(
        {
            "name": text,
            "accessible": {"type": ["boolean", "null"]},
            "reference": nullable,
        }
    )
    detail = obj(
        {
            k: nullable
            for k in (
                "intended_use",
                "units",
                "split_scope",
                "transformations",
                "evaluation_population",
            )
        }
    )
    receipt = obj(
        {
            "key": text,
            "sha256": sha,
            "pointers": obj(
                {
                    k: {"type": "string", "pattern": "^(/.*)?$"}
                    for k in (
                        "source_report_sha256",
                        "parent_annotation_sha256",
                        "scope",
                        "action",
                        "executed",
                    )
                }
            ),
        }
    )
    record = obj(
        {
            "record_id": text,
            "warning_id": text,
            "check_id": text,
            "scope": scope,
            "action_kind": {"enum": ["new_analysis", "review_saved_evidence"]},
            "action": text,
            "applicability": state(
                ["applicable", "inapplicable"],
                {"reference": nullable, "rationale": text},
            ),
            "inputs": state(
                ["documented_accessible", "requires_data"],
                {"requirements": {"type": "array", "items": requirement}},
            ),
            "protocol": state(
                ["qualified", "not_qualified"],
                {
                    "reference": nullable,
                    "details": {"anyOf": [detail, {"type": "null"}]},
                },
            ),
            "authorization": state(
                ["authorized", "not_authorized"],
                {
                    "reference": nullable,
                    "source_rights_reference": nullable,
                    "resource_limits_reference": nullable,
                },
            ),
            "execution": state(
                ["executed", "not_executed"],
                {"receipt": {"anyOf": [receipt, {"type": "null"}]}},
            ),
        }
    )
    request = obj(
        {
            "source_report_sha256": sha,
            "parent_annotation_sha256": sha,
            "checks": {
                "type": "array",
                "minItems": 1,
                "maxItems": 128,
                "items": record,
            },
        }
    )
    result_record = obj(
        {
            **record["properties"],
            "observation_evidence": obj(
                {
                    "finding": state(["observed", "conditional", "contradicted"]),
                    "measurement": {"type": "object"},
                }
            ),
            "legacy_testability": {"enum": ["available", "requires_information"]},
            "synthetic_fixture": {"type": "boolean"},
            "next_steps": {"type": "array", "items": text},
            "execution_receipt_evidence": {
                "anyOf": [
                    obj(
                        {
                            "receipt_sha256": sha,
                            "executed_action": text,
                            "source_report_sha256": sha,
                            "parent_annotation_sha256": sha,
                            "scope": scope,
                        }
                    ),
                    {"type": "null"},
                ]
            },
        }
    )
    return obj(
        {
            "protocol_version": {"const": "domains.verification_readiness.v1"},
            "source_report": obj(
                {"sha256": sha, "hash_scope": {"const": "canonical_json_with_newline"}}
            ),
            "parent_annotation": obj(
                {
                    "sha256": sha,
                    "protocol_version": {"const": "domains.structural_warnings.v1"},
                }
            ),
            "request": {"$ref": "#/$defs/request"},
            "records": {
                "type": "array",
                "minItems": 1,
                "maxItems": 128,
                "items": result_record,
            },
            "limitations": {"type": "array", "items": text},
        }
    ) | {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://nirs4all.org/domains/verification-readiness.v1.schema.json",
        "$defs": {"request": request},
    }


if __name__ == "__main__":
    data = json.dumps(schema(), indent=2) + "\n"
    for folder in ("schemas", "bridges/python/nirs4all_domains"):
        (Path(folder) / "verification-readiness.v1.schema.json").write_text(
            data, encoding="utf-8", newline="\n"
        )
