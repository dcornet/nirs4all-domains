"""Generate the optional D3 companion only; historical contracts are untouched."""
import json
from pathlib import Path
from generate_validation_intent_schema import array, choice, record, schema as intent_schema


def schema():
    text = {"type": "string", "minLength": 1}
    pointer = {"type": "string", "pattern": r"^(?:/(?:[^~/]|~[01])*)*$"}
    nullable_pointer = {"anyOf": [pointer, {"type": "null"}]}
    fields = ("target", "units", "population", "evaluation_ids", "n_evaluation",
              "model", "pipeline", "training_population", "n_train", "rmse",
              "skill", "null_rmse", "null_population")
    pointers = record({"source": {"type": "array", "items": pointer, "minItems": 1, "uniqueItems": True},
                       **{key: nullable_pointer for key in fields}}, required=[])
    side = record({"evaluation": pointer, "pointers": pointers,
                   "null_definition": {"anyOf": [text, {"type": "null"}]},
                   "skill_definition": choice(None, "one_minus_rmse_over_null_rmse"),
                   "intent": {"$ref": "#/$defs/request"}},
                  required=["evaluation", "pointers"])
    request = record({"reference": side, "stress": side})
    numeric = {"type": "number"}
    state = {"oneOf": [record({"status": {"const": "computed"}, "reason": {"type": "null"}, "value": numeric}),
                        record({"status": {"const": "unavailable"}, "reason": text, "value": {"type": "null"}})]}
    metric_record = record({key: state for key in ("rmse", "skill", "null_rmse")})
    relation = choice("same", "different", "unknown")
    compatibility = record({key: relation for key in ("source", "target", "units", "population", "model", "pipeline", "training_population", "n_train", "n_evaluation")})
    result = record({
        "protocol_version": {"const": "domains.comparison_interpretation.v1"},
        "source_reports": record({key: record({"sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                             "hash_scope": {"const": "canonical_json_with_newline"}}) for key in ("reference", "stress")}),
        "request": {"$ref": "#/$defs/comparison_request"},
        "compatibility": compatibility,
        "direct_comparison": choice("compatible", "incompatible", "unknown"),
        "evaluation_matching": choice("matched_ids", "unmatched_ids", "unknown"),
        "null_comparison": choice("same_definition_and_population", "separate_definitions", "unknown"),
        "performance": record({key: metric_record for key in ("reference", "stress")}),
        "context": record({side: record({**{key: {} for key in ("source", "target", "units", "population", "model", "pipeline", "training_population", "n_train", "n_evaluation", "null_population")},
                                         "evaluation_ids_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"}}) for side in ("reference", "stress")}),
        "rmse_difference": state, "relative_rmse_deterioration": state,
        "baseline_context": choice("better_than_stated_null", "no_improvement_over_stated_null", "unknown"),
        "validation_intent": record({key: {"$ref": "#/$defs/validation_annotation"} for key in ("reference", "stress")}),
        "supported_claims": array(text), "stronger_claims_not_established": array(text),
        "missing_information": array(text), "limitations": array(text),
    })
    result.update({"$schema": "https://json-schema.org/draft/2020-12/schema",
                   "$id": "https://nirs4all.org/domains/comparison-interpretation.v1.schema.json",
                   "$defs": {**intent_schema()["$defs"], "comparison_request": request,
                             "validation_annotation": {k: v for k, v in intent_schema().items() if k not in ("$schema", "$id", "$defs")}},
                   "title": "Optional read-only predictive comparison interpretation v1"})
    return result


if __name__ == "__main__":
    data = json.dumps(schema(), indent=2, ensure_ascii=False) + "\n"
    for directory in (Path("schemas"), Path("bridges/python/nirs4all_domains")):
        (directory / "comparison-interpretation.v1.schema.json").write_text(data, encoding="utf-8", newline="\n")
