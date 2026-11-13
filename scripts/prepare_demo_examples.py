"""Build public saved intent variants with qualified APIs; no fit or private data."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from nirs4all_domains import structural_warnings as d1
from nirs4all_domains import verification_readiness as d6
from nirs4all_domains.report_view import build_report
from nirs4all_domains.storage import fingerprint

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/examples/structural-warnings"
OUT = ROOT / "demo/public/examples"
INTENTS = {
    "study": ("proof_of_concept", "unknown", "Within the observed tablet experiment"),
    "known_acquisitions": (
        "known_context",
        "new_acquisitions",
        "New acquisitions within the documented tablet context",
    ),
    "new_specimens": (
        "known_context",
        "new_specimens",
        "New tablet specimens within the documented process",
    ),
    "new_groups": (
        "outside_context",
        "unknown",
        "Unseen declared groups; their physical and context meaning is unverified",
    ),
    "new_context": (
        "outside_context",
        "new_context",
        "A new production context, whose boundary still requires declaration",
    ),
    "unknown": ("unknown", "unknown", None),
}


def encoded(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def publish(name, value):
    payload = encoded(value)
    (OUT / name).write_bytes(payload)
    return {
        "file": name,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }


def intent_request(original, name):
    request = deepcopy(original)
    use, unit, population = INTENTS[name]
    request["validation_intent"].update(
        {
            "intended_use": use,
            "prediction_unit": unit,
            "prediction_population": population,
        }
    )
    request["validation_intent"]["limitations"] = [
        *request["validation_intent"].get("limitations", []),
        "Demo objective is a user declaration applied to saved evidence; it certifies no source, unit, split or independence.",
        "New groups is a declared objective only; a group label alone does not certify a new specimen or context.",
    ]
    return request


def readiness(report, parent):
    """Public unknown/not-executed model from run_verification_readiness_example.py."""
    warning = next(
        w
        for w in parent["warnings"]
        if w["warning_id"] == "experimental_factor_structure"
    )
    check = warning["recommended_checks"][0]

    def state(value=None, **extra):
        return {
            "status": "computed" if value else "unavailable",
            "reason": None if value else "NOT_QUALIFIED",
            "value": value,
            **extra,
        }

    request = {
        "source_report_sha256": fingerprint(report),
        "parent_annotation_sha256": fingerprint(parent),
        "checks": [
            {
                "record_id": "conditional-factor-contrast",
                "warning_id": warning["warning_id"],
                "check_id": check["check_id"],
                "scope": warning["evidence_scope"],
                "action_kind": "new_analysis",
                "action": check["description"],
                "applicability": state(
                    reference=None,
                    rationale="Deployment and original unit mappings remain unqualified",
                ),
                "inputs": state(
                    "requires_data",
                    requirements=[
                        {
                            "name": name,
                            "accessible": False,
                            "reference": "Memberships are not supplied by this saved aggregate report",
                        }
                        for name in check["required_information"]
                    ],
                ),
                "protocol": state(
                    "not_qualified",
                    reference="No new contrast protocol specified",
                    details=None,
                ),
                "authorization": state(
                    "not_authorized",
                    reference="Read-only demo; no new analysis authorized",
                    source_rights_reference=None,
                    resource_limits_reference=None,
                ),
                "execution": state("not_executed", receipt=None),
            }
        ],
    }
    return d6.interpret(report, parent, request)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = json.loads((SOURCE / "tablet.report.json").read_bytes())
    original_d1 = json.loads((SOURCE / "tablet.annotation.json").read_bytes())
    original_request = json.loads((SOURCE / "tablet.request.json").read_bytes())
    frozen = encoded([report, original_d1, original_request])
    d1.validate_annotation(report, original_d1)
    variants, oracle = {}, {}
    for intent in INTENTS:
        request = intent_request(original_request, intent)
        parent = d1.interpret(report, request)
        annotation = parent["validation_intent"]
        # Reuse exact D1 intent: separately defaulting D2 would mismatch its binding.
        saved = build_report(
            [
                {
                    "case_id": "public-tablet",
                    "report": report,
                    "d1": parent,
                    "d2": annotation,
                    "readiness": readiness(report, parent),
                    "decision_summary": True,
                }
            ],
            title="Public tablets: saved structural evidence",
        )
        variants[intent] = {
            **publish(f"tablet.{intent}.saved.json", saved),
            "user_declaration_only": True,
            "source_report_sha256": fingerprint(report),
            "d1_request_sha256": fingerprint(request),
            "d1_annotation_sha256": fingerprint(parent),
        }
        oracle[intent] = {
            "python_protocol": annotation["protocol_version"],
            "facts": {
                key: annotation["facts"][key]
                for key in (
                    "intended_use",
                    "prediction_unit",
                    "prediction_population",
                    "dependencies",
                    "split",
                    "groups",
                    "prediction_metrics",
                )
            },
            "interpretations": annotation["interpretations"],
            "missing_information": annotation["missing_information"],
            "limitations": annotation["limitations"],
            "required_browser_boundaries": {
                "physical_independence_verified": False,
                "predictive_performance_established": False,
                "universally_preferred_split": None,
                "authorization_granted": False,
                "new_execution": False,
            },
        }
        if intent == "unknown":
            default = publish("tablet.saved.json", saved)
    assert encoded([report, original_d1, original_request]) == frozen
    source_files = [
        {
            "path": "docs/examples/structural-warnings/" + name,
            "sha256": hashlib.sha256((SOURCE / name).read_bytes()).hexdigest(),
        }
        for name in (
            "tablet.report.json",
            "tablet.annotation.json",
            "tablet.request.json",
        )
    ]
    boundary = publish(
        "scientific-boundary-oracle.json",
        {
            "schema_version": 1,
            "protocol_version": "domains.demo_scientific_boundary_oracle.v1",
            "qualification": "Python companion boundary oracle only; not full Python/Rust companion parity",
            "source_report_sha256": fingerprint(report),
            "variants": oracle,
            "new_scientific_fits": 0,
        },
    )
    manifest = {
        "schema_version": 1,
        "examples": [
            {
                "id": "tablet-saved",
                **default,
                "default_intent": "unknown",
                "variants": variants,
                "mode": "saved_qualified_report",
                "dataset_id": "ucph_tablet_nir",
                "source_id": "X",
                "n_observations": 310,
                "source_files": source_files,
                "references": [
                    "https://ucphchemometrics.com/tablet/",
                    "https://ucphchemometrics.com/datasets/",
                ],
                "license_scope": "Already-published source-permitted aggregate report only; no raw X/Y redistribution. See docs/campaign/source-attribution.md.",
                "original_independent_study_count": None,
                "new_scientific_fits": 0,
                "d3": {
                    "status": "unavailable",
                    "reason": "NO_COMPATIBLE_COMPARISON_POPULATION_CROSSWALK",
                    "value": None,
                },
            }
        ],
        "scientific_boundary_oracle": boundary,
    }
    publish("manifest.json", manifest)
    print(
        json.dumps(
            {
                "saved_examples": 1,
                "intent_variants": len(variants),
                "new_fits": 0,
                "default_sha256": default["sha256"],
                "bytes": sum(v["bytes"] for v in variants.values())
                + default["bytes"]
                + boundary["bytes"],
            }
        )
    )


if __name__ == "__main__":
    main()
