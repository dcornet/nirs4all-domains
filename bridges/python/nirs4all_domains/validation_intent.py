"""Read-only deployment interpretation. No fitting or numerical provider imports.

An annotation is an optional, content-bound companion to any existing JSON report.
Declarations remain declarations: the interpreter does not certify their provenance.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from .storage import atomic_json, fingerprint

PROTOCOL = "domains.validation_intent.v1"
SCHEMA_PATH = Path(__file__).with_name("validation-intent.v1.schema.json")
INTENTS = ("proof_of_concept", "known_context", "outside_context")
DEFAULTS = {
    "intended_use": "unknown", "prediction_population": None,
    "prediction_unit": "unknown",
    "split": {"family": "unknown", "description": None},
    "dependencies": [], "factors": [],
    "groups": {"basis": "unknown", "construction": "unknown"},
    "transductive": None, "prediction_metrics": [], "spectral_support": [],
    "limitations": [],
}


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _pointer(report, pointer):
    """Resolve an RFC 6901 JSON pointer without evaluating code or loading files."""
    value = report
    if pointer:
        for token in pointer[1:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            try:
                if isinstance(value, list):
                    if not token.isdecimal() or (len(token) > 1 and token[0] == "0"):
                        raise ValueError("Noncanonical array index")
                    value = value[int(token)]
                else:
                    value = value[token]
            except (KeyError, IndexError, TypeError) as exc:
                raise ValueError(f"Missing report evidence: {pointer}") from exc
    return value


def _state(value, reason):
    return {"status": "unavailable" if value is None else "declared",
            "reason": reason if value is None else None, "value": value}


def interpret(report, request=None):
    """Return a deterministic annotation; never mutate or recompute the report.

    ``request`` follows ``$defs/request`` in validation-intent.v1.schema.json.
    Prediction metric pointers must reference existing computed scalar states.
    Evidence quality and split semantics are supplied by the caller, not inferred
    from metric magnitude, category labels or X-derived cluster membership.
    """
    if not isinstance(report, dict):
        raise ValueError("A JSON report object is required")
    # Canonical serialization also rejects NaN/Infinity anywhere in the report.
    report_hash = fingerprint(report)
    schema = _schema()
    request = {} if request is None else deepcopy(request)
    Draft202012Validator({"$ref": "#/$defs/request", "$defs": schema["$defs"]}).validate(request)
    facts = deepcopy(DEFAULTS)
    facts.update(request)
    for key in ("split", "groups"):
        facts[key] = {**DEFAULTS[key], **request.get(key, {})}

    # Validate references without reprinting or recalculating numerical evidence.
    for metric in facts["prediction_metrics"]:
        state = _pointer(report, metric["pointer"])
        if (not isinstance(state, dict) or state.get("status") != "computed"
                or state.get("reason") is not None or isinstance(state.get("value"), bool)
                or not isinstance(state.get("value"), (int, float))):
            raise ValueError("Prediction evidence must reference a computed numeric state")
        if metric["name"] != "r2" and state["value"] < 0:
            raise ValueError("Error metric must be nonnegative")
    for support in facts["spectral_support"]:
        _pointer(report, support["pointer"])

    full_x = facts["groups"]["construction"] == "complete_x"
    x_groups = (full_x or facts["groups"]["basis"] in ("x_derived", "mixed")
                or facts["split"]["family"] == "loco_x")
    transductive = facts["transductive"]
    missing, limitations = [], list(facts["limitations"])
    if full_x:
        if facts["groups"]["basis"] not in ("x_derived", "mixed"):
            limitations.append("Complete-X group construction is treated as X-derived regardless of an unknown or conflicting group-basis declaration.")
        if transductive is False:
            limitations.append("The supplied non-transductive declaration conflicts with complete-X group construction; interpretation is transductive.")
        transductive = True
    if facts["split"]["family"] == "loco_x" and facts["groups"]["basis"] == "physical":
        limitations.append("LOCO-X is geometric even when the supplied group basis says physical; physical separation is not established by these clusters.")
    if facts["prediction_population"] is None:
        missing.append("Intended prediction population is unspecified.")
    if facts["prediction_unit"] == "unknown":
        missing.append("New specimens versus new acquisitions or new contexts is unspecified.")
    if facts["split"]["family"] == "unknown":
        missing.append("Actual evaluation split family is unspecified.")
    if not facts["dependencies"]:
        missing.append("Physical specimen, shared reference and acquisition dependencies are unknown.")
    for dependency in facts["dependencies"]:
        if dependency["evidence"] == "unknown" or dependency["separated"] is None:
            missing.append(f"Dependency separation/evidence is incomplete for {dependency['unit']}.")
    if facts["groups"]["basis"] == "unknown":
        missing.append("Evaluation group basis is unknown.")
    if transductive is None:
        missing.append("Transductive use of evaluation X is unspecified.")
    if not facts["spectral_support"]:
        missing.append("No spectral-support evidence is referenced.")
    for support in facts["spectral_support"]:
        value = _pointer(report, support["pointer"])
        if value is None or (isinstance(value, dict) and value.get("status") == "unavailable"):
            missing.append(f"Referenced spectral support is unavailable at {support['pointer']}.")
    if not facts["prediction_metrics"]:
        missing.append("No computed prediction-error evidence is referenced; target and estimator may be absent.")
    relevant = [f for f in facts["factors"] if f["relevant_to_intent"]]
    if not relevant:
        missing.append("No deployment-relevant factor exclusion is documented.")
    for factor in relevant:
        if factor["excluded"] is None or factor["evidence"] == "unknown":
            missing.append(f"Exclusion/evidence is incomplete for relevant factor {factor['name']}.")
    if transductive:
        limitations.append("Evaluation X participates in the declared protocol; this is not an untouched prospective-X evaluation.")
    if x_groups:
        limitations.append("X-derived groups describe spectral geometry; they do not establish physical, assay or experimental independence.")
    if any(f["excluded"] is True for f in relevant) and facts["split"]["family"] in ("random_kfold", "representative", "unknown"):
        limitations.append("A factor exclusion declaration is not sufficient to interpret a random, representative or unspecified split as a context holdout; clarify the actual split.")
    if facts["spectral_support"]:
        limitations.append("Spectral support applies only to each stated representation and reference population; a projection/range summary is not full support or a risk probability.")
    limitations.extend([
        "Facts and evidence quality are caller declarations with report references; their provenance is not automatically verified.",
        "A categorical factor alone does not establish the need for a group split; no validation family is universally preferred.",
        "Known dependencies need not be exhaustive. No causal shortcut or probability of deployment failure is inferred.",
    ])
    selected = INTENTS if facts["intended_use"] == "unknown" else (facts["intended_use"],)
    readings = [_reading(intent, facts, x_groups, transductive, relevant) for intent in selected]
    annotation = {
        "protocol_version": PROTOCOL,
        "source_report": {"sha256": report_hash, "hash_scope": "canonical_json_with_newline"},
        "facts": facts,
        "uses_x_derived_groups": x_groups,
        "transductive": _state(transductive, "TRANSDUCTIVE_STATUS_UNKNOWN"),
        "interpretations": readings,
        "missing_information": missing, "limitations": limitations,
    }
    Draft202012Validator(schema).validate(annotation)
    return annotation


def _reading(intent, facts, x_groups, transductive, relevant):
    predictive = bool(facts["prediction_metrics"])
    family = facts["split"]["family"]
    scope = "reported evaluation" if family == "unknown" else family.replace("_", " ") + " evaluation"
    supported = [f"Existing prediction-error evidence describes the {scope}, conditional on the declared protocol."] if predictive else [
        "Only the referenced X/structural evidence is described; predictive performance is not established."]
    unsupported = [
        "Universal external-population transfer, causal shortcut attribution and deployment-risk probabilities.",
        "Independence of unrecorded physical specimens or shared assay references.",
    ]
    conditions = []
    if intent == "proof_of_concept":
        conditions.append("If the objective is proof of concept within the observed experiment/population.")
        if predictive:
            supported.append("The reported errors provide a within-evaluation proof-of-concept reference; useful X–Y information requires a suitable null comparison and leakage controls.")
        unsupported.append("Transfer to new experiments, instruments or populations from this proof of concept alone.")
    elif intent == "known_context":
        conditions.append("If prediction stays in the stated operational population and context.")
        separated = [d for d in facts["dependencies"] if d["kind"] == "specimen" and d["evidence"] == "verified" and d["separated"] is True]
        crossing = any(d["separated"] is False for d in facts["dependencies"])
        if facts["prediction_unit"] == "new_acquisitions":
            if predictive:
                supported.append("The declared question concerns new acquisitions of known specimens; performance remains conditional on the evaluated acquisition conditions.")
            unsupported.append("Performance on genuinely new specimens from repeated-acquisition evaluation alone.")
        elif (facts["prediction_unit"] == "new_specimens" and separated and not crossing
              and not x_groups and transductive is False and family != "unknown"):
            if predictive:
                supported.append("The declared verified specimen separation supports interpretation for new specimens within the tested known context, subject to other dependencies and sampling limits.")
        else:
            conditions.append("For new-specimen interpretation, document specimen/reference separation and its evidence; the current facts do not establish it.")
            unsupported.append("New-specimen operational generalization without verified relevant dependency separation.")
        unsupported.append("Transfer to an untested instrument, campaign or entire experiment.")
    else:
        conditions.append("If the objective is prediction outside the experimental context, match the tested novelty to that objective.")
        excluded = [f for f in relevant if f["excluded"] is True and f["evidence"] != "unknown"]
        for factor in excluded:
            if predictive and not x_groups and family in ("group_kfold", "logo", "context_holdout", "external_holdout", "temporal_holdout"):
                supported.append(f"Declared exclusion of {factor['name']} ({factor['kind']}, {factor['evidence']} evidence) describes prediction for the observed held-out levels only; it does not certify independence.")
        if not excluded or x_groups or family in ("random_kfold", "representative", "unknown", "other"):
            conditions.append("No evidenced deployment-relevant physical/context exclusion is established by the supplied evaluation facts.")
        unsupported.append("Unseen-population transfer from random/representative CV or X-derived clusters alone.")
        unsupported.append("New-experiment generalization from genotype, block or instrument holdout alone; those novelty types are distinct.")
        unsupported.append("Generalization to future unseen levels beyond the tested exclusions without representative independent evidence.")
    if x_groups:
        supported.append("The evaluation can describe an X-derived geometric partition, subject to its construction and support scope.")
    return {"intended_use": intent, "conditional": facts["intended_use"] == "unknown",
            "conditions": conditions, "supported_claims": supported,
            "stronger_claims_not_established": unsupported}


def validate_annotation(report, annotation):
    """Reject stale or edited annotations by reinterpreting their recorded facts."""
    Draft202012Validator(_schema()).validate(annotation)
    if interpret(report, annotation["facts"]) != annotation:
        raise ValueError("Annotation does not match this report and deterministic interpretation")


def markdown(annotation):
    """Render the optional human-readable section, including all declared facts."""
    Draft202012Validator(_schema()).validate(annotation)
    facts = annotation["facts"]
    lines = ["## Deployment-aware validation interpretation", "",
             f"Protocol: `{PROTOCOL}`. Report SHA-256: `{annotation['source_report']['sha256']}`.", "",
             f"Intended use: {facts['intended_use']}. Population: {facts['prediction_population'] or 'unspecified'}",
             f"Prediction unit: {facts['prediction_unit']}. Split family: {facts['split']['family']}.",
             f"Split description: {facts['split']['description'] or 'unspecified'}",
             f"X-derived groups: {annotation['uses_x_derived_groups']}. Group basis/construction: {facts['groups']['basis']} / {facts['groups']['construction']}.",
             f"Transductive: {annotation['transductive']['value']} ({annotation['transductive']['reason'] or 'declared/inferred from construction'}).", ""]
    def truth(value):
        return "unknown" if value is None else "yes" if value else "no"

    sections = [
        ("Dependency units and evidence", [
            f"{d['unit']} ({d['kind']}): {d['evidence']} evidence; separated: {truth(d['separated'])}. Reference: {d['reference'] or 'unspecified'}."
            for d in facts["dependencies"]]),
        ("Factor/context exclusions (relationships retained)", [
            f"{f['name']} ({f['kind']}): excluded: {truth(f['excluded'])}; relevant to intent: {truth(f['relevant_to_intent'])}; {f['evidence']} evidence. Reference: {f['reference'] or 'unspecified'}. Relationship: {f['relationship'] or 'unspecified'}"
            for f in facts["factors"]]),
        ("Referenced prediction metrics", [f"{m['name']}: `{m['pointer']}` in the original report (unchanged)." for m in facts["prediction_metrics"]]),
        ("Spectral-support evidence", [
            f"{s['description']} Representation: {s['representation']}. Reference population: {s['reference_population']}. Evidence: `{s['pointer']}`. Limits: {'; '.join(s['limitations']) or 'none supplied'}"
            for s in facts["spectral_support"]]),
    ]
    for label, items in sections:
        lines.extend([f"### {label}", "", *(["- " + item for item in items] or ["- Unspecified / not referenced."]), ""])
    for reading in annotation["interpretations"]:
        lines.extend([f"### {'Conditional: ' if reading['conditional'] else ''}{reading['intended_use']}", ""])
        for title, key in (("Conditions", "conditions"), ("Supported", "supported_claims"), ("Not established", "stronger_claims_not_established")):
            lines.extend([f"{title}:", "", *["- " + claim for claim in reading[key]], ""])
    for title, key in (("Missing information", "missing_information"), ("Limitations", "limitations")):
        lines.extend([f"### {title}", "", *(["- " + item for item in annotation[key]] or ["- None recorded."]), ""])
    return "\n".join(lines)


def _read(path):
    def reject(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Existing JSON report (read only)")
    parser.add_argument("--intent", help="Optional request JSON; omitted means unknown intended use")
    parser.add_argument("--out", required=True, help="New annotation JSON path; Markdown uses the same stem")
    args = parser.parse_args(argv)
    output = Path(args.out)
    rendered = output.with_suffix(".md")
    protected = {Path(args.report).resolve()}
    if args.intent:
        protected.add(Path(args.intent).resolve())
    if output.resolve() in protected or rendered.resolve() in protected or output.resolve() == rendered.resolve():
        parser.error("Annotation outputs must be distinct from report and request")
    if output.exists() or rendered.exists():
        parser.error("Annotation outputs already exist; choose a new output path")
    annotation = interpret(_read(args.report), _read(args.intent) if args.intent else None)
    atomic_json(output, annotation)
    rendered.write_text(markdown(annotation), encoding="utf-8")
    print(f"Annotation: {output}\nInterpretation: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
