"""Interpret existing prediction comparisons without fitting or numerical providers."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

from . import validation_intent
from .storage import atomic_json, fingerprint

PROTOCOL = "domains.comparison_interpretation.v1"
SCHEMA_PATH = Path(__file__).with_name("comparison-interpretation.v1.schema.json")
SIDES = ("reference", "stress")
FIELDS = ("source", "target", "units", "population", "evaluation_ids", "n_evaluation",
          "model", "pipeline", "training_population", "n_train", "rmse", "skill",
          "null_rmse", "null_population")


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _state(value=None, reason="NOT_REFERENCED"):
    return {"status": "unavailable" if value is None else "computed",
            "reason": reason if value is None else None, "value": value}


def _metric(value, name):
    if value is None:
        return _state()
    if isinstance(value, dict):
        if not {"status", "reason", "value"} <= value.keys():
            raise ValueError(f"Malformed {name} state")
        if not isinstance(value["status"], str) or not value["status"]:
            raise ValueError(f"Invalid {name} status")
        if value["status"] != "computed":
            if value["value"] is not None or not isinstance(value["reason"], str) or not value["reason"]:
                raise ValueError(f"Invalid unavailable {name} state")
            return _state(reason=value["reason"])
        if value["reason"] is not None:
            raise ValueError(f"Computed {name} cannot have a reason")
        value = value["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Finite numeric {name} required")
    if name != "skill" and value < 0:
        raise ValueError(f"Nonnegative {name} required")
    return _state(value)


def _relation(a, b):
    if a is None or b is None:
        return "unknown"
    return "same" if fingerprint(a) == fingerprint(b) else "different"


def _identity(value):
    if isinstance(value, dict) and {"status", "reason", "value"} <= value.keys():
        if value["value"] is None:
            if value["status"] == "computed" or not isinstance(value["reason"], str) or not value["reason"]:
                raise ValueError("Invalid unavailable identity state")
            return None
        if value["status"] != "computed" or value["reason"] is not None:
            raise ValueError("Invalid computed identity state")
        return value["value"]
    return value


def _resolve(report, request):
    evaluation = validation_intent._pointer(report, request["evaluation"])
    if not isinstance(evaluation, dict):
        raise ValueError("Evaluation pointer must reference an object")
    pointers = request["pointers"]
    values = {}
    for key in FIELDS:
        pointer = pointers.get(key)
        if key == "source":
            value = [_identity(validation_intent._pointer(report, p)) for p in pointer] if pointer else None
            if value is not None and any(v is None or v == "" for v in value):
                value = None
        else:
            value = validation_intent._pointer(report, pointer) if pointer is not None else None
            if key not in ("rmse", "skill", "null_rmse"):
                value = _identity(value)
        if key in ("rmse", "skill", "null_rmse"):
            # Prevent accidental metric selection from a different evaluation.
            scope = request["evaluation"]
            if pointer is not None and scope and not pointer.startswith(scope + "/"):
                raise ValueError(f"{key} pointer is outside its evaluation")
            value = _metric(value, key)
        elif key in ("target", "units") and value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Nonempty {key} semantics required")
        elif key in ("n_train", "n_evaluation") and value is not None:
            if type(value) is not int or value < 1:
                raise ValueError(f"Positive integer {key} required")
        elif key == "evaluation_ids" and value is not None:
            if (not isinstance(value, list) or not value
                    or any(not isinstance(v, str) or not v for v in value)
                    or len(set(value)) != len(value)):
                raise ValueError("Evaluation IDs must be unique nonempty strings")
        values[key] = value
    if (values["evaluation_ids"] is not None and values["n_evaluation"] is not None
            and len(values["evaluation_ids"]) != values["n_evaluation"]):
        raise ValueError("Evaluation ID count disagrees with n_evaluation")
    return values


def interpret(reference, stress, request):
    """Content-bound companion using explicit pointers and caller intent facts.

    Scalars may be existing finite numbers or status/reason/value states. Only
    RMSE difference and fractional change are assembled, never predictions,
    skill, nulls, intervals or significance. Caller identities are not certified.
    """
    if not isinstance(reference, dict) or not isinstance(stress, dict):
        raise ValueError("Two JSON report objects are required")
    reports = dict(zip(SIDES, (reference, stress)))
    bindings = {key: {"sha256": fingerprint(report), "hash_scope": "canonical_json_with_newline"}
                for key, report in reports.items()}
    schema = _schema()
    request = deepcopy(request)
    fingerprint(request)  # finite JSON, including caller declarations
    Draft202012Validator({"$ref": "#/$defs/comparison_request", "$defs": schema["$defs"]}).validate(request)
    values = {key: _resolve(reports[key], request[key]) for key in SIDES}
    a, b = values["reference"], values["stress"]
    relations = {key: _relation(a[key], b[key]) for key in (
        "source", "target", "units", "population", "model", "pipeline", "training_population", "n_train", "n_evaluation")}
    compatibility = ("incompatible" if "different" in (relations["target"], relations["units"])
                     else "compatible" if relations["target"] == relations["units"] == "same" else "unknown")
    matching = "unknown"
    if a["evaluation_ids"] is not None and b["evaluation_ids"] is not None:
        if set(a["evaluation_ids"]) != set(b["evaluation_ids"]):
            matching = "unmatched_ids"
        elif relations["source"] == relations["population"] == "same" and compatibility == "compatible":
            matching = "matched_ids"
    if relations["n_evaluation"] == "different" or relations["population"] == "different":
        matching = "unmatched_ids"
    null_relation = "unknown"
    definitions = [request[key].get("null_definition") for key in SIDES]
    null_population = _relation(a["null_population"], b["null_population"])
    if null_population == "different" or _relation(*definitions) == "different" or relations["source"] == "different":
        null_relation = "separate_definitions"
    elif null_population == _relation(*definitions) == relations["source"] == "same":
        null_relation = "same_definition_and_population"

    difference = _state(reason="INCOMPATIBLE_TARGET_OR_UNITS" if compatibility == "incompatible" else "COMPATIBILITY_UNKNOWN")
    relative = deepcopy(difference)
    if compatibility == "compatible":
        av, bv = a["rmse"]["value"], b["rmse"]["value"]
        if av is None or bv is None:
            difference = relative = _state(reason="RMSE_UNAVAILABLE")
        else:
            delta = bv - av
            difference = _state(delta) if math.isfinite(delta) else _state(reason="ARITHMETIC_OVERFLOW")
            ratio = delta / av if av else None
            relative = (_state(reason="ZERO_REFERENCE_RMSE") if ratio is None else
                        _state(ratio) if math.isfinite(ratio) else _state(reason="ARITHMETIC_OVERFLOW"))
    baseline = "unknown"
    if (request["reference"].get("skill_definition") == "one_minus_rmse_over_null_rmse"
            and a["skill"]["value"] is not None and a["null_rmse"]["value"] is not None
            and a["null_rmse"]["value"] > 0 and relations["target"] == "same"
            and _relation(a["population"], a["null_population"]) == "same"
            and definitions[0] is not None):
        baseline = "better_than_stated_null" if a["skill"]["value"] > 0 else "no_improvement_over_stated_null"

    # A declared known-form skill cannot contradict the referenced error order.
    for side in SIDES:
        v = values[side]
        if (request[side].get("skill_definition") == "one_minus_rmse_over_null_rmse"
                and all(v[m]["value"] is not None for m in ("skill", "rmse", "null_rmse"))):
            sv, rv, nv = (v[m]["value"] for m in ("skill", "rmse", "null_rmse"))
            if nv <= 0 or (sv > 0) != (rv < nv) or (sv == 0) != (rv == nv):
                raise ValueError("Declared skill sign contradicts RMSE/null evidence")

    intents = {}
    for key in SIDES:
        facts = deepcopy(request[key].get("intent", {}))
        pointer = request[key]["pointers"].get("rmse")
        stored = validation_intent._pointer(reports[key], pointer) if pointer is not None else None
        if (not facts.get("prediction_metrics") and isinstance(stored, dict)
                and values[key]["rmse"]["status"] == "computed"):
            facts["prediction_metrics"] = [{"name": "rmse", "pointer": pointer}]
        for evidence in facts.get("prediction_metrics", []):
            scope = request[key]["evaluation"]
            if scope and not evidence["pointer"].startswith(scope + "/"):
                raise ValueError("Intent prediction metric is outside its evaluation")
        intents[key] = validation_intent.interpret(reports[key], facts)
    missing, limitations, supported = [], [], []
    for key in SIDES:
        for field in ("source", "target", "units", "population", "evaluation_ids", "n_evaluation", "model", "pipeline", "training_population", "n_train", "null_population"):
            if values[key][field] is None:
                missing.append(f"{key}: {field} is not referenced or unavailable.")
        for field in ("rmse", "skill", "null_rmse"):
            if values[key][field]["value"] is None:
                missing.append(f"{key}: {field} unavailable ({values[key][field]['reason']}).")
        if not request[key].get("null_definition"):
            missing.append(f"{key}: null definition is unspecified.")
        if not request[key].get("skill_definition"):
            missing.append(f"{key}: skill definition is unspecified; no sign interpretation.")
        missing.extend(f"{key}: {item}" for item in intents[key]["missing_information"])
    if compatibility == "compatible":
        supported.append("Target semantics and units match exactly as referenced; existing absolute RMSE values are numerically comparable in those units.")
        if difference["value"] is not None:
            supported.append("The RMSE contrast is descriptive sensitivity under the two declared evaluation conditions.")
    elif compatibility == "incompatible":
        limitations.append("Direct comparison rejected: target semantics or units differ. Absolute results remain separate; no conversion is attempted.")
    else:
        limitations.append("Direct RMSE contrast unavailable until target semantics and units are documented.")
    supported.append("Same explicit evaluation IDs within the referenced source/content and population; this is an ID-matched contrast, without a significance test." if matching == "matched_ids" else
                     "Evaluation identities are unmatched or unknown; this contrast must not be described as paired.")
    if null_relation != "same_definition_and_population":
        limitations.append("Keep the two skill definitions and null populations separate; no common-null effect is established.")
    else:
        limitations.append("Same declared null definition and population do not guarantee identical fold-specific null predictions; no skill difference or common-null effect is computed.")
    if baseline == "no_improvement_over_stated_null":
        limitations.append("Reference skill is zero or negative: relative deterioration starts from a baseline with no improvement over its stated null, not demonstrated useful prediction.")
    elif baseline == "better_than_stated_null":
        limitations.append("Reference skill improves on its stated null: deterioration can describe loss from that baseline advantage. Practical usefulness still needs a task-specific error tolerance and leakage controls.")
    else:
        limitations.append("Baseline usefulness is undetermined without a compatible, defined null/skill reference; a small gap alone does not demonstrate robust prediction.")
    for key in ("source", "population", "model", "pipeline", "training_population", "n_train", "n_evaluation"):
        if relations[key] != "same":
            limitations.append(f"{key} is {relations[key]} across evaluations; an isolated split effect is not established.")
    limitations.extend([
        "Reference and stress name the caller's contrast; they do not rank validation families. Different novelty types and crossed factors retain their separate intent descriptions.",
        "Source/content/population identities, semantic equivalence and evidence quality are caller assertions, not automatic provenance certification.",
        "Only stored aggregate metrics are read. No predictions, nulls, intervals, significance tests, causal mechanisms or independent-database counts are estimated.",
    ])
    unsupported = [
        "A causal shortcut, failure probability, universal model/validation ranking or composite risk score.",
        "Independent specimen, assay or database generalization from matched row IDs or aggregate performance alone.",
        "Physical factor identity from X-derived clusters, or external transfer beyond the actual tested context.",
        "Statistical significance from a numerical gap, or robust prediction from a small gap with a poor baseline.",
    ]
    result = {"protocol_version": PROTOCOL, "source_reports": bindings, "request": request,
              "compatibility": relations, "direct_comparison": compatibility,
              "evaluation_matching": matching, "null_comparison": null_relation,
              "performance": {key: {m: values[key][m] for m in ("rmse", "skill", "null_rmse")} for key in SIDES},
              "context": {key: {**{f: values[key][f] for f in ("source", "target", "units", "population", "model", "pipeline", "training_population", "n_train", "n_evaluation", "null_population")},
                                "evaluation_ids_sha256": fingerprint(sorted(values[key]["evaluation_ids"])) if values[key]["evaluation_ids"] is not None else None} for key in SIDES},
              "rmse_difference": difference, "relative_rmse_deterioration": relative,
              "baseline_context": baseline, "validation_intent": intents,
              "supported_claims": supported, "stronger_claims_not_established": unsupported,
              "missing_information": missing, "limitations": limitations}
    fingerprint(result)
    Draft202012Validator(schema).validate(result)
    return deepcopy(result)


def validate_annotation(reference, stress, annotation):
    """Reject stale bindings, invalid pointers, altered claims or metric copies."""
    Draft202012Validator(_schema()).validate(annotation)
    expected = interpret(reference, stress, annotation["request"])
    if fingerprint(expected) != fingerprint(annotation):
        raise ValueError("Stale report binding or inconsistent comparison annotation")


def markdown(annotation):
    """Render a consumer section; validate against reports before trusting it."""
    fingerprint(annotation)
    Draft202012Validator(_schema()).validate(annotation)
    lines = ["## Predictive comparison interpretation", "", f"Protocol: `{PROTOCOL}`.", "",
             f"Direct numerical comparison: {annotation['direct_comparison']}. Evaluation matching: {annotation['evaluation_matching']}.",
             f"Null scope: {annotation['null_comparison']}. Reference baseline: {annotation['baseline_context']}.", ""]
    for side in SIDES:
        lines.extend([f"### {side.capitalize()} evidence", "", f"Report SHA-256: `{annotation['source_reports'][side]['sha256']}`. Evaluation pointer: `{annotation['request'][side]['evaluation']}`.", ""])
        for name, state in annotation["performance"][side].items():
            lines.append(f"- {name}: {state['value']} ({state['reason'] or 'stored value'}).")
        lines.append("")
        for name, value in annotation["context"][side].items():
            lines.append(f"- {name}: `{json.dumps(value, sort_keys=True)}`.")
        lines.extend(["", "Evidence pointers: `" + json.dumps(annotation["request"][side]["pointers"], sort_keys=True) + "`.", ""])
    lines.extend(["### Descriptive contrast", ""])
    for key in ("rmse_difference", "relative_rmse_deterioration"):
        state = annotation[key]
        lines.append(f"- {key}: {state['value']} ({state['reason'] or 'stress minus reference; relative change is a fraction'}).")
    lines.extend(["", "Compatibility: `" + json.dumps(annotation["compatibility"], sort_keys=True) + "`.", ""])
    for title, key in (("Supported", "supported_claims"), ("Not established", "stronger_claims_not_established"),
                       ("Missing information", "missing_information"), ("Limitations", "limitations")):
        lines.extend([f"### {title}", "", *["- " + item for item in annotation[key]], ""])
    for side in SIDES:
        section = validation_intent.markdown(annotation["validation_intent"][side])
        nested = "\n".join("##" + line if line.startswith("#") else line for line in section.splitlines())
        lines.extend([f"### {side.capitalize()} deployment scope", "", nested, ""])
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference")
    parser.add_argument("stress")
    parser.add_argument("--request", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    output = Path(args.out)
    rendered = output.with_suffix(".md")
    protected = {Path(p).resolve() for p in (args.reference, args.stress, args.request)}
    if output.resolve() in protected or rendered.resolve() in protected or output.resolve() == rendered.resolve():
        parser.error("Outputs must be distinct from source reports and request")
    if output.exists() or rendered.exists():
        parser.error("Outputs already exist; choose new paths")
    annotation = interpret(validation_intent._read(args.reference), validation_intent._read(args.stress), validation_intent._read(args.request))
    atomic_json(output, annotation)
    rendered.write_text(markdown(annotation), encoding="utf-8", newline="\n")
    print(f"Annotation: {output}\nInterpretation: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
