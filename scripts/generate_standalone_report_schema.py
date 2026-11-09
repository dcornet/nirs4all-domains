"""Generate the optional standalone presentation schema, not source report schemas."""

import json
from pathlib import Path


def schema():
    def obj(properties):
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }

    text = {"type": "string"}
    integer = {"type": "integer", "minimum": 0}
    state = obj(
        {
            "status": {"enum": ["computed", "unavailable"]},
            "reason": {"type": ["string", "null"]},
            "value": {"type": ["object", "null"]},
        }
    )
    slot = obj(
        {
            **state["properties"],
            "sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
            "protocol_version": {"type": ["string", "null"]},
        }
    )
    for record in (state, slot):
        record["allOf"] = [
            {
                "if": {"properties": {"status": {"const": "computed"}}},
                "then": {
                    "properties": {
                        "reason": {"type": "null"},
                        "value": {"type": "object"},
                    }
                },
                "else": {
                    "properties": {
                        "reason": {"type": "string", "minLength": 1},
                        "value": {"type": "null"},
                    }
                },
            }
        ]
    slot["allOf"].append(
        {
            "if": {"properties": {"status": {"const": "computed"}}},
            "then": {
                "properties": {
                    "sha256": {"type": "string"},
                    "protocol_version": {"type": "string"},
                }
            },
            "else": {
                "properties": {
                    "sha256": {"type": "null"},
                    "protocol_version": {"type": "null"},
                }
            },
        }
    )
    counts = obj(
        {k: integer for k in ("observed", "conditional", "contradicted", "unavailable")}
    )
    case = obj(
        {
            "case_id": {"type": "string", "minLength": 1},
            "label": text,
            "source_ref": {"type": ["string", "null"]},
            "source_reports": {
                "type": "object",
                "minProperties": 1,
                "additionalProperties": obj(
                    {
                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "hash_scope": {"const": "canonical_json_with_newline"},
                    }
                ),
            },
            "identity": state,
            "companions": obj({k: slot for k in ("d1", "d2", "d3")}),
            "warning_counts": counts,
            "native_preflight": state,
        }
    )
    value = obj(
        {
            "protocol_version": {"const": "domains.standalone_report.v1"},
            "title": text,
            "coverage": {"type": "object"},
            "cases": {"type": "array", "minItems": 1, "maxItems": 128, "items": case},
            "limitations": {"type": "array", "items": text},
        }
    )
    value.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://nirs4all.org/domains/standalone-report.v1.schema.json",
        }
    )
    return value


if __name__ == "__main__":
    data = json.dumps(schema(), indent=2) + "\n"
    for folder in ("schemas", "bridges/python/nirs4all_domains"):
        (Path(folder) / "standalone-report.v1.schema.json").write_text(
            data, encoding="utf-8", newline="\n"
        )
