"""Validate all public saved variants, original bindings and Python boundary oracle."""

import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator

from nirs4all_domains import structural_warnings as d1
from nirs4all_domains import validation_intent as d2
from nirs4all_domains import verification_readiness as d6
from nirs4all_domains.report_view import build_report
from nirs4all_domains.storage import fingerprint

from prepare_demo_examples import INTENTS, intent_request

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "demo/public/examples"


def checked(record):
    data = (FOLDER / record["file"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == record["sha256"]
    return json.loads(data)


def main():
    manifest = json.loads((FOLDER / "manifest.json").read_bytes())
    schema = json.loads(
        (ROOT / "schemas/standalone-report.v1.schema.json").read_bytes()
    )
    source = json.loads(
        (ROOT / "docs/examples/structural-warnings/tablet.report.json").read_bytes()
    )
    request = json.loads(
        (ROOT / "docs/examples/structural-warnings/tablet.request.json").read_bytes()
    )
    original_hash = fingerprint(source)
    oracle = checked(manifest["scientific_boundary_oracle"])
    assert oracle["source_report_sha256"] == original_hash
    assert oracle["new_scientific_fits"] == 0
    assert set(oracle["variants"]) == set(INTENTS)
    count = 0
    for example in manifest["examples"]:
        default = checked(example)
        assert set(example["variants"]) == set(INTENTS)
        assert default == checked(example["variants"][example["default_intent"]])
        assert example["new_scientific_fits"] == 0
        assert example["original_independent_study_count"] is None
        assert example["d3"]["status"] == "unavailable"
        for original in example["source_files"]:
            assert (
                hashlib.sha256((ROOT / original["path"]).read_bytes()).hexdigest()
                == original["sha256"]
            )
        for name, record in example["variants"].items():
            saved = checked(record)
            Draft202012Validator(schema).validate(saved)
            assert saved["protocol_version"] == "domains.standalone_report.v1"
            assert record["source_report_sha256"] == original_hash
            assert record["user_declaration_only"] is True
            case = saved["cases"][0]
            parent = case["companions"]["d1"]["value"]
            intent = case["companions"]["d2"]["value"]
            readiness = case["companions"]["readiness"]["value"]
            d1.validate_annotation(source, parent)
            d2.validate_annotation(source, intent)
            d6.validate_annotation(source, parent, readiness)
            assert fingerprint(parent) == record["d1_annotation_sha256"]
            assert fingerprint(parent["request"]) == record["d1_request_sha256"]
            assert parent["request"] == intent_request(request, name)
            assert fingerprint(intent) == fingerprint(parent["validation_intent"])
            assert parent["source_report"]["sha256"] == original_hash
            assert case["companions"]["d3"]["status"] == "unavailable"
            assert "decision_summary" in case
            assert all(
                row["execution"]["value"] == "not_executed"
                for row in readiness["records"]
            )
            replay = build_report(
                [
                    {
                        "case_id": "public-tablet",
                        "report": source,
                        "d1": parent,
                        "d2": intent,
                        "readiness": readiness,
                        "decision_summary": True,
                    }
                ],
                title=saved["title"],
            )
            assert fingerprint(replay) == fingerprint(saved)
            boundary = oracle["variants"][name]
            assert boundary["interpretations"] == intent["interpretations"]
            assert boundary["facts"]["dependencies"] == []
            assert boundary["facts"]["prediction_metrics"] == []
            assert boundary["required_browser_boundaries"] == {
                "physical_independence_verified": False,
                "predictive_performance_established": False,
                "universally_preferred_split": None,
                "authorization_granted": False,
                "new_execution": False,
            }
            for reading in boundary["interpretations"]:
                assert any(
                    "predictive performance is not established" in claim
                    for claim in reading["supported_claims"]
                )
                assert any(
                    "Independence of unrecorded physical specimens" in claim
                    for claim in reading["stronger_claims_not_established"]
                )
            assert any(
                "no validation family is universally preferred" in limit
                for limit in boundary["limitations"]
            )
            count += 1
    assert fingerprint(source) == original_hash
    print(
        json.dumps(
            {
                "examples_verified": len(manifest["examples"]),
                "intent_variants_verified": count,
                "schema_and_owner_replays": True,
                "python_boundary_oracle": True,
                "full_python_rust_parity_claimed": False,
                "raw_data_copied": False,
                "new_fits": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
