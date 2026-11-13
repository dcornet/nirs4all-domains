"""Decision consistency, not a user-effectiveness or numerical efficacy test."""

import unittest
from copy import deepcopy

from nirs4all_domains import report_view as view
from nirs4all_domains import structural_warnings as d1
from nirs4all_domains.storage import fingerprint
from test_report_view import public_case, synthetic


def tablet(intent, relevant):
    case = public_case()
    request = deepcopy(case["d1"]["request"])
    request["validation_intent"] = {
        "intended_use": intent,
        "prediction_population": "Simulated qualification objective: "
        + ("future batches" if relevant else "the observed experiment"),
        "prediction_unit": "new_context" if relevant else "new_acquisitions",
        "factors": [
            {
                "name": "batch",
                "kind": "other",
                "relevant_to_intent": relevant,
                "excluded": None,
                "evidence": "declared",
                "reference": "Synthetic deployment objective; no experimental exclusion claimed",
                "relationship": "Batch is not an entire independent experiment",
            }
        ],
        "limitations": ["Qualification scenario, not an actual user declaration"],
    }
    case["d1"] = d1.interpret(case["report"], request)
    return case


def warning(case, name):
    return next(w for w in case["d1"]["warnings"] if w["warning_id"] == name)


class WarningUtility(unittest.TestCase):
    def test_same_observations_have_context_specific_conditional_checks(self):
        poc = tablet("proof_of_concept", False)
        future = tablet("outside_context", True)
        self.assertEqual(fingerprint(poc["report"]), fingerprint(future["report"]))
        a = warning(poc, "experimental_factor_structure")
        b = warning(future, "experimental_factor_structure")
        self.assertEqual(a["observation"], b["observation"])
        first = next(
            c
            for c in a["recommended_checks"]
            if c["check_id"] == "factor_contrast:batch"
        )
        second = next(
            c
            for c in b["recommended_checks"]
            if c["check_id"] == "factor_contrast:batch"
        )
        self.assertIn("First establish whether", first["description"])
        self.assertIn("Examine the declared", second["description"])
        self.assertEqual(second["testability"], "requires_information")
        self.assertIn("categorical column alone", first["description"])

    def test_declared_objective_and_actual_split_visible_before_findings(self):
        rendered = view.render_report([tablet("outside_context", True)])
        text = rendered["html"]
        self.assertLess(
            text.index("Declared prediction objective"),
            text.index("What was observed?"),
        )
        self.assertIn("Simulated qualification objective: future batches", text)
        self.assertIn("Actual evaluation split", text)
        self.assertIn("Intended prediction unit", rendered["markdown"])

    def test_unavailable_physical_check_is_readable_without_json_disclosure(self):
        rendered = view.render_report([public_case()])
        row = rendered["view"]["cases"][0]
        sections = list(view._sections(row))
        checks = [c for _, values, kind in sections if kind == "checks" for c in values]
        check = next(
            c for c in checks if c["check_id"] == "audit_declared_unit_overlap"
        )
        self.assertEqual(check["testability"], "requires_information")
        self.assertTrue(
            any(
                "Original specimen/reference membership" in c["required_information"]
                for c in checks
            )
        )
        self.assertIn("PHYSICAL_UNIT_EVIDENCE_UNAVAILABLE", rendered["html"])
        self.assertIn("PHYSICAL\\_UNIT\\_EVIDENCE\\_UNAVAILABLE", rendered["markdown"])

    def test_prerequisite_availability_is_not_permission_or_completed_analysis(self):
        result = view.render_report([synthetic("all-noise")])
        self.assertIn(
            "does not mean that a new analysis is authorized or has been executed",
            result["html"],
        )
        self.assertIn("new fits require a separate protocol", result["markdown"])

    def test_all_noise_contradiction_and_missing_evidence_remain_distinct(self):
        for kind, assessment in [
            ("all-noise", "observed"),
            ("contradicted", "contradicted"),
            ("unavailable", None),
        ]:
            case = synthetic(kind)
            before = deepcopy(case)
            rendered = view.render_report([case])
            record = warning(case, "preprocessing_dependent_organization")
            self.assertEqual(record["value"], assessment)
            self.assertEqual(case, before)
            self.assertIn(
                "not probabilities", " ".join(rendered["view"]["limitations"])
            )
            self.assertIn("representation_sensitivity", str(rendered["view"]))
            if kind == "all-noise":
                self.assertIn(
                    "continuous structure is not ruled out", rendered["markdown"]
                )
            elif kind == "unavailable":
                self.assertIn(
                    "NO_ADMISSIBLE_MATCHED_REPRESENTATION_EVIDENCE",
                    rendered["html"],
                )

    def test_unknown_use_preserves_three_readings_and_no_physical_certification(self):
        case = public_case()
        request = deepcopy(case["d1"]["request"])
        request.pop("validation_intent", None)
        case["d1"] = d1.interpret(case["report"], request)
        rendered = view.render_report([case])
        intent = rendered["view"]["cases"][0]["companions"]["d2"]["value"]
        self.assertEqual(
            {x["intended_use"] for x in intent["interpretations"]},
            {"proof_of_concept", "known_context", "outside_context"},
        )
        self.assertIsNone(warning(case, "physical_unit_dependence")["value"])
        self.assertEqual(intent["facts"]["prediction_metrics"], [])


if __name__ == "__main__":
    unittest.main()
