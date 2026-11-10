"""Source-bound readiness declarations for an existing D1 check; never execution."""

import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from . import structural_warnings as d1
from .storage import fingerprint
from .validation_intent import _pointer

PROTOCOL = "domains.verification_readiness.v1"
SCHEMA_PATH = Path(__file__).with_name("verification-readiness.v1.schema.json")
LIMITATIONS = [
    "Readiness is a source-scoped declaration, not independent certification of scientific qualification, rights or permission.",
    "The original D1 testability flag describes recorded prerequisites and is not changed or used to infer these dimensions.",
    "Report and receipt hashes bind supplied content; they do not authenticate its author or establish physical/reference independence.",
    "No global availability, risk score, automatic execution or validation-workflow engine is provided.",
    "An executed saved-evidence review does not establish execution of its parent scientific analysis or future predictive performance.",
]


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _known(state, value):
    return state["status"] == "computed" and state["value"] == value


def _validate_declarations(record, check):
    inputs = record["inputs"]
    items = inputs["requirements"]
    names = [r["name"] for r in items]
    if len(set(names)) != len(names):
        raise ValueError("DUPLICATE_VERIFICATION_REQUIREMENT")
    if _known(inputs, "documented_accessible"):
        if not items or not all(
            r["accessible"] is True and r["reference"] for r in items
        ):
            raise ValueError("ACCESSIBLE_INPUTS_REQUIRE_DOCUMENTED_REQUIREMENTS")
        if record["action_kind"] == "new_analysis" and not set(
            check["required_information"]
        ) <= set(names):
            raise ValueError("VERIFICATION_REQUIREMENTS_INCOMPLETE")
    if _known(inputs, "requires_data") and not any(
        r["accessible"] is False for r in items
    ):
        raise ValueError("MISSING_INPUT_MUST_BE_IDENTIFIED")
    if _known(record["protocol"], "qualified"):
        details = record["protocol"]["details"]
        if (
            not (record["protocol"]["reference"] or "").strip()
            or details is None
            or any(
                not isinstance(v, str)
                or not v.strip()
                or v.strip().lower() in ("unknown", "unspecified")
                for v in details.values()
            )
        ):
            raise ValueError("QUALIFIED_PROTOCOL_REQUIRES_EXPLICIT_SCOPE")
    if _known(record["authorization"], "authorized") and not all(
        (record["authorization"][k] or "").strip()
        for k in ("reference", "source_rights_reference", "resource_limits_reference")
    ):
        raise ValueError("AUTHORIZATION_REQUIRES_EXPLICIT_REFERENCES")
    if (
        record["applicability"]["status"] == "computed"
        and not record["applicability"]["reference"]
    ):
        raise ValueError("APPLICABILITY_REQUIRES_REFERENCE")


def _receipt(record, receipts, source_hash, parent_hash):
    receipt = record["execution"]["receipt"]
    if not _known(record["execution"], "executed"):
        if receipt is not None:
            raise ValueError("RECEIPT_REQUIRES_EXECUTED_DECLARATION")
        return None
    if receipt is None:
        raise ValueError("EXECUTED_CHECK_REQUIRES_RECEIPT")
    payload = receipts.get(receipt["key"])
    if payload is None or fingerprint(payload) != receipt["sha256"]:
        raise ValueError("MISSING_OR_STALE_EXECUTION_RECEIPT")
    values = {k: _pointer(payload, p) for k, p in receipt["pointers"].items()}
    if values["executed"] is not True:
        raise ValueError("RECEIPT_DOES_NOT_RECORD_EXECUTION")
    if (
        values["source_report_sha256"] != source_hash
        or values["parent_annotation_sha256"] != parent_hash
    ):
        raise ValueError("EXECUTION_RECEIPT_SOURCE_MISMATCH")
    scope = values["scope"]
    if not isinstance(scope, dict) or any(
        scope.get(k) != v for k, v in record["scope"].items()
    ):
        raise ValueError("EXECUTION_RECEIPT_SCOPE_MISMATCH")
    if values["action"] != record["action"]:
        raise ValueError("EXECUTED_ACTION_MISMATCH")
    return {
        "receipt_sha256": receipt["sha256"],
        "executed_action": values["action"],
        "source_report_sha256": source_hash,
        "parent_annotation_sha256": parent_hash,
        "scope": deepcopy(record["scope"]),
    }


def _steps(record):
    if _known(record["applicability"], "inapplicable"):
        return [
            "Do not prescribe this verification for the declared objective. Preserve the original observation and the stated inapplicability rationale."
        ]
    steps = []
    if record["applicability"]["status"] == "unavailable":
        steps.append(
            "Establish whether this exact verification applies to the declared objective."
        )
    if not _known(record["inputs"], "documented_accessible"):
        steps.append(
            "Document or obtain the stated verification inputs; existing observation evidence alone does not supply them."
        )
    if not _known(record["protocol"], "qualified"):
        steps.append(
            "Qualify the protocol, including units, split scope, transformations and evaluation population, before a new verification."
        )
    if not _known(record["authorization"], "authorized"):
        steps.append(
            "Obtain or document explicit source- and resource-scoped authorization. Missing authorization is not a measurement failure."
        )
    if _known(record["execution"], "executed"):
        steps.append(
            "Inspect the actual linked receipt for this exact action only; no broader scientific verification is implied."
        )
    elif _known(record["execution"], "not_executed"):
        steps.append(
            "This action has not been executed. Readiness declarations do not run or schedule it."
        )
    else:
        steps.append(
            "Execution is unknown; do not present the recommendation as a completed analysis."
        )
    return steps


def interpret(report, parent, request, receipts=None):
    """Interpret independently documented dimensions; no fit or side effect."""
    d1.validate_annotation(report, parent)
    fingerprint(request)
    schema = _schema()
    Draft202012Validator(
        {"$ref": "#/$defs/request", "$defs": schema["$defs"]}
    ).validate(request)
    source_hash, parent_hash = fingerprint(report), fingerprint(parent)
    if request["source_report_sha256"] != source_hash:
        raise ValueError("READINESS_SOURCE_REPORT_MISMATCH")
    if request["parent_annotation_sha256"] != parent_hash:
        raise ValueError("READINESS_PARENT_ANNOTATION_MISMATCH")
    ids = [c["record_id"] for c in request["checks"]]
    if len(set(ids)) != len(ids):
        raise ValueError("DUPLICATE_READINESS_RECORD")
    warnings = {w["warning_id"]: w for w in parent["warnings"]}
    records = []
    for declaration in request["checks"]:
        record = deepcopy(declaration)
        warning = warnings.get(record["warning_id"])
        checks = (
            {c["check_id"]: c for c in warning["recommended_checks"]} if warning else {}
        )
        check = checks.get(record["check_id"])
        if check is None:
            raise ValueError("READINESS_CHECK_BINDING_UNKNOWN")
        if record["scope"] != warning["evidence_scope"]:
            raise ValueError("READINESS_OBSERVATION_SCOPE_MISMATCH")
        if (
            record["action_kind"] == "new_analysis"
            and record["action"] != check["description"]
        ):
            raise ValueError("NEW_ANALYSIS_ACTION_MUST_MATCH_PARENT_CHECK")
        _validate_declarations(record, check)
        records.append(
            {
                **record,
                "observation_evidence": {
                    "finding": {k: warning[k] for k in ("status", "reason", "value")},
                    "measurement": deepcopy(warning["observation"]),
                },
                "legacy_testability": check["testability"],
                "synthetic_fixture": record["scope"]["scope_kind"] == "synthetic",
                "execution_receipt_evidence": _receipt(
                    record, receipts or {}, source_hash, parent_hash
                ),
                "next_steps": _steps(record),
            }
        )
    result = {
        "protocol_version": PROTOCOL,
        "source_report": {
            "sha256": source_hash,
            "hash_scope": "canonical_json_with_newline",
        },
        "parent_annotation": {
            "sha256": parent_hash,
            "protocol_version": parent["protocol_version"],
        },
        "request": deepcopy(request),
        "records": records,
        "limitations": LIMITATIONS,
    }
    fingerprint(result)
    Draft202012Validator(schema).validate(result)
    return result


def validate_annotation(report, parent, annotation, receipts=None):
    Draft202012Validator(_schema()).validate(annotation)
    if fingerprint(
        interpret(report, parent, annotation["request"], receipts)
    ) != fingerprint(annotation):
        raise ValueError("STALE_OR_ALTERED_VERIFICATION_READINESS")
