"""Generate only the optional D2 annotation contract; no legacy schema changes."""
from copy import deepcopy
import json
from pathlib import Path


def record(properties, required=None):
    return {"type": "object", "additionalProperties": False,
            "properties": properties, "required": list(properties) if required is None else required}


def choice(*values):
    return {"enum": list(values)}


def array(items):
    return {"type": "array", "items": items, "uniqueItems": True}


def schema():
    text = {"type": "string", "minLength": 1}
    nullable_text = {"anyOf": [text, {"type": "null"}]}
    boolean = {"type": ["boolean", "null"]}
    evidence = choice("unknown", "declared", "verified")
    # Verified means the caller cites evidence, not that Domains authenticates it.
    reference_rule = {"if": {"properties": {"evidence": {"enum": ["declared", "verified"]}}},
                      "then": {"properties": {"reference": text}}}
    dependency = record({"unit": text,
                         "kind": choice("specimen", "assay_reference", "acquisition", "session", "other"),
                         "evidence": evidence, "separated": boolean, "reference": nullable_text})
    dependency["allOf"] = [reference_rule]
    factor = record({"name": text,
                     "kind": choice("genotype", "block", "instrument", "experiment", "site", "campaign", "session", "treatment", "time", "other"),
                     "relevant_to_intent": {"type": "boolean"}, "excluded": boolean,
                     "evidence": evidence, "reference": nullable_text,
                     "relationship": nullable_text})
    factor["allOf"] = [reference_rule]
    pointer = {"type": "string", "pattern": r"^(?:/(?:[^~/]|~[01])*)*$"}
    facts = record({
        "intended_use": choice("proof_of_concept", "known_context", "outside_context", "unknown"),
        "prediction_population": nullable_text,
        "prediction_unit": choice("new_specimens", "new_acquisitions", "new_context", "unknown"),
        "split": record({"family": choice("random_kfold", "representative", "group_kfold", "logo", "loco_x", "context_holdout", "external_holdout", "temporal_holdout", "other", "unknown"), "description": nullable_text}, []),
        "dependencies": array(dependency), "factors": array(factor),
        "groups": record({"basis": choice("physical", "declared_context", "x_derived", "mixed", "none", "unknown"),
                          "construction": choice("declared", "train_only", "complete_x", "unknown")}, []),
        "transductive": boolean,
        "prediction_metrics": array(record({"name": choice("rmse", "mae", "mse", "r2"), "pointer": pointer})),
        "spectral_support": array(record({"pointer": pointer, "description": text,
                                           "representation": text, "reference_population": text,
                                           "limitations": array(text)})),
        "limitations": array(text),
    })
    request = deepcopy(facts)
    request["required"] = []
    facts = {"allOf": [{"$ref": "#/$defs/request"}, {
        "required": list(facts["properties"]),
        "properties": {"split": {"required": ["family", "description"]},
                       "groups": {"required": ["basis", "construction"]}},
    }]}
    interpretation = record({"intended_use": choice("proof_of_concept", "known_context", "outside_context"),
                             "conditional": {"type": "boolean"},
                             "conditions": array(text), "supported_claims": array(text),
                             "stronger_claims_not_established": array(text)})
    state = {"oneOf": [record({"status": {"const": "declared"}, "reason": {"type": "null"}, "value": {"type": "boolean"}}),
                        record({"status": {"const": "unavailable"}, "reason": {"const": "TRANSDUCTIVE_STATUS_UNKNOWN"}, "value": {"type": "null"}})]}
    result = record({"protocol_version": {"const": "domains.validation_intent.v1"},
                     "source_report": record({"sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                              "hash_scope": {"const": "canonical_json_with_newline"}}),
                     "facts": {"$ref": "#/$defs/facts"},
                     "uses_x_derived_groups": {"type": "boolean"}, "transductive": state,
                     "interpretations": {"type": "array", "items": interpretation, "minItems": 1, "maxItems": 3},
                     "missing_information": array(text), "limitations": array(text)})
    result.update({"$schema": "https://json-schema.org/draft/2020-12/schema",
                   "$id": "https://nirs4all.org/domains/validation-intent.v1.schema.json",
                   "title": "Optional deployment-aware validation annotation v1",
                   "$defs": {"request": request, "facts": facts}})
    return result


if __name__ == "__main__":
    data = json.dumps(schema(), indent=2, ensure_ascii=False) + "\n"
    for path in (Path("schemas/validation-intent.v1.schema.json"),
                 Path("bridges/python/nirs4all_domains/validation-intent.v1.schema.json")):
        path.write_text(data, encoding="utf-8")
