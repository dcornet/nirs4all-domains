"""Independent readiness dimensions and content binding; explicit synthetic fixtures."""

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import ValidationError
from nirs4all_domains import report_view
from nirs4all_domains import verification_readiness as readiness
from nirs4all_domains.storage import fingerprint
from test_report_view import synthetic


def state(value=None, **extra):
    return {
        "status": "computed" if value is not None else "unavailable",
        "reason": None if value is not None else "SYNTHETIC_UNKNOWN",
        "value": value,
        **extra,
    }


def fixture(kind="all-noise", index=2):
    case = synthetic(kind)
    parent = case["d1"]
    w = parent["warnings"][index]
    check = w["recommended_checks"][0]
    record = {
        "record_id": "synthetic-verification",
        "warning_id": w["warning_id"],
        "check_id": check["check_id"],
        "scope": deepcopy(w["evidence_scope"]),
        "action_kind": "new_analysis",
        "action": check["description"],
        "applicability": state(
            "applicable",
            reference="Synthetic objective declaration",
            rationale="Explicit synthetic test, not a real user objective",
        ),
        "inputs": state(
            "requires_data",
            requirements=[
                {
                    "name": name,
                    "accessible": False,
                    "reference": "Synthetic missing input",
                }
                for name in check["required_information"]
            ],
        ),
        "protocol": state(reference=None, details=None),
        "authorization": state(
            "not_authorized",
            reference="Synthetic explicit denial",
            source_rights_reference=None,
            resource_limits_reference=None,
        ),
        "execution": state("not_executed", receipt=None),
    }
    return case, {
        "source_report_sha256": fingerprint(case["report"]),
        "parent_annotation_sha256": fingerprint(parent),
        "checks": [record],
    }


def available(record):
    record["inputs"] = state(
        "documented_accessible",
        requirements=[
            r | {"accessible": True, "reference": "Synthetic accessible fixture"}
            for r in record["inputs"]["requirements"]
        ],
    )


def qualified(record):
    record["protocol"] = state(
        "qualified",
        reference="Synthetic qualified protocol fixture",
        details={
            k: "Synthetic explicit scope, no real analysis"
            for k in (
                "intended_use",
                "units",
                "split_scope",
                "transformations",
                "evaluation_population",
            )
        },
    )


def receipt(case, record):
    # A schema fixture only, not evidence that any real scientific analysis ran.
    payload = {
        "synthetic_fixture": True,
        "source": fingerprint(case["report"]),
        "parent": fingerprint(case["d1"]),
        "scope": record["scope"],
        "action": record["action"],
        "executed": True,
    }
    record["execution"] = state(
        "executed",
        receipt={
            "key": "synthetic",
            "sha256": fingerprint(payload),
            "pointers": {
                "source_report_sha256": "/source",
                "parent_annotation_sha256": "/parent",
                "scope": "/scope",
                "action": "/action",
                "executed": "/executed",
            },
        },
    )
    return {"synthetic": payload}


class VerificationReadiness(unittest.TestCase):
    def run_record(self, case, request, receipts=None):
        return readiness.interpret(case["report"], case["d1"], request, receipts)[
            "records"
        ][0]

    def test_five_families_keep_original_observations_and_prerequisite_meaning(self):
        for index in range(5):
            case, request = fixture(index=index)
            actual = self.run_record(case, request)
            original = case["d1"]["warnings"][index]
            self.assertEqual(
                actual["observation_evidence"]["measurement"], original["observation"]
            )
            self.assertEqual(
                actual["observation_evidence"]["finding"]["value"], original["value"]
            )
            self.assertEqual(
                actual["legacy_testability"],
                original["recommended_checks"][0]["testability"],
            )

    def test_available_observation_does_not_supply_verification_metadata(self):
        case, request = fixture()
        actual = self.run_record(case, request)
        self.assertEqual(
            actual["observation_evidence"]["measurement"]["status"], "computed"
        )
        self.assertEqual(actual["inputs"]["value"], "requires_data")
        self.assertIn("Document or obtain", " ".join(actual["next_steps"]))

    def test_accessible_inputs_do_not_qualify_protocol_or_grant_permission(self):
        case, request = fixture()
        available(request["checks"][0])
        actual = self.run_record(case, request)
        self.assertEqual(actual["protocol"]["status"], "unavailable")
        self.assertEqual(actual["authorization"]["value"], "not_authorized")
        self.assertEqual(actual["execution"]["value"], "not_executed")

    def test_qualified_protocol_is_independent_of_missing_authorization(self):
        case, request = fixture()
        available(request["checks"][0])
        qualified(request["checks"][0])
        actual = self.run_record(case, request)
        self.assertEqual(actual["protocol"]["value"], "qualified")
        self.assertEqual(
            actual["observation_evidence"]["measurement"]["status"], "computed"
        )
        self.assertIn("not a measurement failure", " ".join(actual["next_steps"]))

    def test_synthetic_authorized_check_is_still_not_executed(self):
        case, request = fixture()
        record = request["checks"][0]
        available(record)
        qualified(record)
        record["authorization"] = state(
            "authorized",
            reference="Synthetic grant, no real permission",
            source_rights_reference="Synthetic rights",
            resource_limits_reference="Synthetic limits",
        )
        actual = self.run_record(case, request)
        self.assertTrue(actual["synthetic_fixture"])
        self.assertEqual(actual["execution"]["value"], "not_executed")
        self.assertIsNone(actual["execution_receipt_evidence"])

    def test_executed_fixture_requires_exact_action_source_parent_and_scope(self):
        case, request = fixture()
        payloads = receipt(case, request["checks"][0])
        actual = self.run_record(case, request, payloads)
        self.assertEqual(
            actual["execution_receipt_evidence"]["executed_action"],
            request["checks"][0]["action"],
        )
        for field in ("source", "parent", "action", "scope", "executed"):
            changed = deepcopy(payloads)
            changed["synthetic"][field] = (
                False
                if field == "executed"
                else {}
                if field == "scope"
                else "different"
            )
            request2 = deepcopy(request)
            request2["checks"][0]["execution"]["receipt"]["sha256"] = fingerprint(
                changed["synthetic"]
            )
            with self.assertRaises(ValueError):
                self.run_record(case, request2, changed)

    def test_missing_and_stale_execution_receipt_are_refused(self):
        case, request = fixture()
        request["checks"][0]["execution"] = state("executed", receipt=None)
        with self.assertRaisesRegex(ValueError, "REQUIRES_RECEIPT"):
            self.run_record(case, request)
        payloads = receipt(case, request["checks"][0])
        payloads["synthetic"]["new_field"] = "changed"
        with self.assertRaisesRegex(ValueError, "STALE_EXECUTION_RECEIPT"):
            self.run_record(case, request, payloads)

    def test_saved_review_cannot_be_laundered_into_parent_scientific_analysis(self):
        case, request = fixture()
        record = request["checks"][0]
        original_action = record["action"]
        record.update(
            action_kind="review_saved_evidence",
            action="Inspect the saved synthetic observation only",
        )
        payloads = receipt(case, record)
        self.run_record(case, request, payloads)
        record.update(action_kind="new_analysis", action=original_action)
        with self.assertRaisesRegex(ValueError, "EXECUTED_ACTION_MISMATCH"):
            self.run_record(case, request, payloads)

    def test_stale_report_parent_or_population_representation_is_refused(self):
        case, request = fixture()
        for key in ("source_report_sha256", "parent_annotation_sha256"):
            changed = deepcopy(request)
            changed[key] = "0" * 64
            with self.assertRaises(ValueError):
                self.run_record(case, changed)
        for key in ("population_id", "representation", "dataset_id"):
            changed = deepcopy(request)
            changed["checks"][0]["scope"][key] = "different"
            with self.assertRaisesRegex(ValueError, "OBSERVATION_SCOPE_MISMATCH"):
                self.run_record(case, changed)

    def test_partial_unknown_requirements_do_not_become_complete_inputs(self):
        case, request = fixture()
        record = request["checks"][0]
        record["inputs"] = state(
            requirements=[
                {
                    "name": "Only some metadata",
                    "accessible": True,
                    "reference": "Synthetic partial evidence",
                }
            ]
        )
        self.assertIsNone(self.run_record(case, request)["inputs"]["value"])
        record["inputs"]["status"] = "computed"
        record["inputs"]["reason"] = None
        record["inputs"]["value"] = "documented_accessible"
        with self.assertRaisesRegex(ValueError, "REQUIREMENTS_INCOMPLETE"):
            self.run_record(case, request)

    def test_unknown_protocol_or_missing_grant_references_cannot_be_qualified(self):
        case, request = fixture()
        record = request["checks"][0]
        record["protocol"] = state(
            "qualified", reference="Synthetic partial protocol", details=None
        )
        with self.assertRaisesRegex(ValueError, "EXPLICIT_SCOPE"):
            self.run_record(case, request)
        qualified(record)
        record["authorization"] = state(
            "authorized",
            reference="Synthetic grant",
            source_rights_reference=None,
            resource_limits_reference=None,
        )
        with self.assertRaisesRegex(ValueError, "EXPLICIT_REFERENCES"):
            self.run_record(case, request)

    def test_partial_protocol_preserves_known_scope_without_becoming_qualified(self):
        case, request = fixture()
        record = request["checks"][0]
        record["protocol"] = state(
            reference="Partial synthetic documentary evidence",
            details={
                "intended_use": "known_context",
                "units": None,
                "split_scope": None,
                "transformations": "No fit performed",
                "evaluation_population": None,
            },
        )
        actual = self.run_record(case, request)
        self.assertIsNone(actual["protocol"]["value"])
        self.assertEqual(
            actual["protocol"]["details"]["transformations"], "No fit performed"
        )
        record["protocol"].update(status="computed", reason=None, value="qualified")
        with self.assertRaisesRegex(ValueError, "EXPLICIT_SCOPE"):
            self.run_record(case, request)

    def test_whitespace_is_not_a_qualified_protocol_or_authorization_reference(self):
        case, request = fixture()
        record = request["checks"][0]
        qualified(record)
        record["protocol"]["details"]["units"] = "   "
        with self.assertRaisesRegex(ValueError, "EXPLICIT_SCOPE"):
            self.run_record(case, request)
        qualified(record)
        record["authorization"] = state(
            "authorized",
            reference="   ",
            source_rights_reference="Synthetic rights",
            resource_limits_reference="Synthetic limits",
        )
        with self.assertRaisesRegex(ValueError, "EXPLICIT_REFERENCES"):
            self.run_record(case, request)

    def test_inapplicability_preserves_observation_without_prescribing_analysis(self):
        case, request = fixture()
        request["checks"][0]["applicability"] = state(
            "inapplicable",
            reference="Synthetic unrelated objective",
            rationale="No partition-dependent conclusion is intended",
        )
        actual = self.run_record(case, request)
        self.assertIn("Do not prescribe", actual["next_steps"][0])
        self.assertEqual(
            actual["observation_evidence"]["measurement"]["status"], "computed"
        )

    def test_all_noise_unavailable_and_contradicted_findings_remain_distinct(self):
        for kind, value, index in [
            ("all-noise", "observed", 2),
            ("contradicted", "contradicted", 2),
            ("unavailable", None, 0),
        ]:
            case, request = fixture(kind, index)
            actual = self.run_record(case, request)
            self.assertEqual(actual["observation_evidence"]["finding"]["value"], value)

    def test_source_and_records_unchanged_and_edited_conclusions_rejected(self):
        case, request = fixture()
        before = deepcopy((case, request))
        annotation = readiness.interpret(case["report"], case["d1"], request)
        self.assertEqual((case, request), before)
        annotation["records"][0]["next_steps"] = [
            "Leakage or predictive failure established"
        ]
        with self.assertRaises(ValueError):
            readiness.validate_annotation(case["report"], case["d1"], annotation)

    def test_unknown_state_invariants_and_nonfinite_values_rejected(self):
        case, request = fixture()
        request["checks"][0]["protocol"]["reason"] = None
        with self.assertRaises(ValidationError):
            self.run_record(case, request)
        case, request = fixture()
        request["checks"][0]["scope"]["n_observations"] = float("nan")
        with self.assertRaises(ValueError):
            self.run_record(case, request)

    def test_consumer_exports_independent_dimensions_without_mutating_old_annotations(
        self,
    ):
        case, request = fixture()
        annotation = readiness.interpret(case["report"], case["d1"], request)
        before = deepcopy(case)
        rendered = report_view.render_report([case | {"readiness": annotation}])
        self.assertEqual(case, before)
        self.assertEqual(
            rendered["view"]["cases"][0]["companions"]["d1"]["value"], case["d1"]
        )
        for label in (
            "A. Observation evidence",
            "B. Verification inputs",
            "C. Protocol readiness",
            "D. Execution authorization",
            "E. Execution result",
        ):
            self.assertIn(label, rendered["html"])
        self.assertIn("Independent readiness dimensions", rendered["markdown"])
        self.assertIn(
            "readiness", rendered["view"]["coverage"]["companion_slot_counts"]
        )

    def test_executed_consumer_needs_original_receipt_payload(self):
        case, request = fixture()
        payloads = receipt(case, request["checks"][0])
        annotation = readiness.interpret(case["report"], case["d1"], request, payloads)
        with self.assertRaises(ValueError):
            report_view.render_report([case | {"readiness": annotation}])
        report_view.render_report(
            [case | {"readiness": annotation, "readiness_receipts": payloads}]
        )
        with self.assertRaises(ValueError):
            report_view.render_report(
                [
                    {
                        k: v
                        for k, v in (case | {"readiness": annotation}).items()
                        if k != "d1"
                    }
                ]
            )

    def test_schema_mirrors_and_old_view_serialize_without_new_slot(self):
        root = Path(__file__).resolve().parents[2]
        self.assertEqual(
            (root / "schemas/verification-readiness.v1.schema.json").read_bytes(),
            readiness.SCHEMA_PATH.read_bytes(),
        )
        case, _ = fixture()
        view = report_view.build_report([case])
        self.assertNotIn("readiness", view["cases"][0]["companions"])
        self.assertNotIn("readiness", view["coverage"]["companion_slot_counts"])

    def test_cli_manifest_with_receipt_and_existing_output_protection(self):
        case, request = fixture()
        payloads = receipt(case, request["checks"][0])
        annotation = readiness.interpret(case["report"], case["d1"], request, payloads)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            for name, value in {
                "report": case["report"],
                "d1": case["d1"],
                "readiness": annotation,
                "receipt": payloads["synthetic"],
            }.items():
                (path / (name + ".json")).write_text(
                    json.dumps(value), encoding="utf-8"
                )
            manifest = {
                "cases": [
                    {
                        "case_id": "synthetic-cli",
                        "report": "report.json",
                        "d1": "d1.json",
                        "readiness": "readiness.json",
                        "readiness_receipts": {"synthetic": "receipt.json"},
                    }
                ]
            }
            (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            report_view.main(
                [
                    "--manifest",
                    str(path / "manifest.json"),
                    "--out",
                    str(path / "review"),
                ]
            )
            self.assertTrue((path / "review.html").exists())
            with self.assertRaises(ValueError):
                report_view.main(
                    [
                        "--manifest",
                        str(path / "manifest.json"),
                        "--out",
                        str(path / "receipt"),
                    ]
                )


if __name__ == "__main__":
    unittest.main()
