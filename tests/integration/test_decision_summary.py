"""Distinct D6.1 counterexamples; no frozen expectations or observations rewritten."""

import html
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from nirs4all_domains import report_view as view
from nirs4all_domains import structural_warnings as d1
from nirs4all_domains import verification_readiness as readiness
from nirs4all_domains.storage import encoded
from test_report_view import public_case, synthetic
from test_verification_readiness import fixture, state
from test_warning_utility import tablet


def comparison(kind="density_parameter", rep="raw", counts=(5, 4), ari=0.986):
    case = synthetic("contradicted")
    request = deepcopy(case["d1"]["request"])
    request["source"].update(representation=rep, n_observations=32)
    ev = request["evidence"][0]
    ev["scope"].update(representation=rep, n_observations=32)
    values = {"cluster_counts": list(counts), "parameter_ari_min": ari}
    if kind == "representation":
        values.update(partition_ari=0.178, full_x_overlap=0.951, pca_overlap=0.949)
    case["report"]["evidence"] = values
    ev["metrics"] = {k: "/evidence/" + k for k in values}
    ev["qualifications"]["comparison_kind"] = kind
    ev["qualifications"]["representations"] = (
        ["raw", "smooth"] if kind == "representation" else [rep]
    )
    ev["method"]["settings"]["actual_native_configuration"] = {
        "HDBSCAN": [
            {
                "min_cluster_size": n,
                "min_samples": 4,
                "status": "computed",
                "reason": None,
            }
            for n in (8, 12)
        ],
        "PCA": {"retained_components": 20},
        "provider": {"version": "synthetic"},
    }
    ev["method"]["settings"]["query_support"] = {
        "scope": "Synthetic declared reference",
        "n_query": 32,
    }
    case["case_id"] = rep
    case["d1"] = d1.interpret(case["report"], request)
    return case


def summarize(case):
    return view.build_report([case | {"decision_summary": True}])["cases"][0][
        "decision_summary"
    ]


class DecisionSummary(unittest.TestCase):
    def test_unknown_method_scope_cannot_qualify_paired_counts(self):
        raw, smooth = (
            comparison(counts=(2, 6)),
            comparison("representation", "smooth", (10, 6)),
        )
        for case in (raw, smooth):
            request = deepcopy(case["d1"]["request"])
            request["evidence"][0]["method"]["settings"].pop("query_support")
            case["d1"] = d1.interpret(case["report"], request)
        smooth["decision_summary"] = True
        actual = view.build_report([raw, smooth])["cases"][1]["decision_summary"]
        self.assertEqual(actual["paired_representation_counts"], [])

    def test_optional_absence_preserves_exact_old_view(self):
        case = public_case()
        old = view.build_report([case])
        self.assertNotIn("decision_summary", old["cases"][0])
        self.assertEqual(
            encoded(old),
            encoded(view.build_report([case | {"decision_summary": False}])),
        )

    def test_summary_preserves_all_annotations_observations_and_counts(self):
        case = public_case()
        original = deepcopy(case)
        old = view.build_report([case])
        new = view.build_report([case | {"decision_summary": True}])
        self.assertEqual(old["coverage"], new["coverage"])
        row = deepcopy(new["cases"][0])
        row.pop("decision_summary")
        self.assertEqual(old["cases"][0], row)
        self.assertEqual(case, original)
        self.assertEqual(len(case["d1"]["warnings"]), 5)

    def test_density_does_not_become_preprocessing_effect(self):
        m = summarize(comparison())["mechanisms"]
        self.assertEqual({r["kind"] for r in m}, {"density_parameter"})
        self.assertEqual(m[0]["values"]["cluster_counts"], [5, 4])
        self.assertEqual(m[0]["values"]["parameter_ari_min"], 0.986)
        self.assertIn("not preprocessing effects", m[0]["description"])

    def test_representation_density_and_neighbors_are_separate(self):
        m = summarize(comparison("representation", "smooth", (10, 6)))["mechanisms"]
        self.assertEqual(
            {r["kind"] for r in m},
            {"representation", "density_parameter", "neighborhood"},
        )
        self.assertIn("mean neighbor intersection / k", m[-1]["description"])
        self.assertIn("not Jaccard", m[-1]["description"])

    def test_contradicted_comparison_has_no_active_sensitivity_caution(self):
        m = summarize(synthetic("contradicted"))["mechanisms"]
        self.assertTrue(
            all(
                r["finding"] == "contradicted" and not r["active_sensitivity_caution"]
                for r in m
            )
        )
        self.assertIn("does not establish universal stability", m[0]["description"])

    def test_all_noise_and_unavailability_do_not_imply_no_continuous_structure(self):
        for kind in ("all-noise", "unavailable"):
            m = summarize(synthetic(kind))["mechanisms"]
            self.assertFalse(any(r["active_sensitivity_caution"] for r in m))
            self.assertEqual(m[0]["kind"], "partition_noninformative_or_unavailable")
            self.assertIn("do not exclude continuous structure", m[0]["description"])

    def test_unknown_intent_first_clarifies_novelty(self):
        case = public_case()
        request = deepcopy(case["d1"]["request"])
        request.pop("validation_intent", None)
        case["d1"] = d1.interpret(case["report"], request)
        s = summarize(case)
        self.assertIn("First clarify", s["verify_now"][0])
        self.assertIn("Do not prescribe GroupKFold/LOGO", s["verify_now"][0])

    def test_same_tablet_measurement_has_conditional_context_questions(self):
        poc, future = tablet("proof_of_concept", False), tablet("outside_context", True)
        self.assertEqual(
            poc["d1"]["warnings"][1]["observation"],
            future["d1"]["warnings"][1]["observation"],
        )
        a, b = summarize(poc), summarize(future)
        self.assertTrue(
            any(
                "not automatically necessary" in f["question"]
                for f in a["factor_questions"]
            )
        )
        self.assertTrue(
            any("Only if these keys" in f["question"] for f in b["factor_questions"])
        )

    def test_unknown_inputs_and_inapplicability_do_not_become_imperatives(self):
        case, req = fixture()
        r = req["checks"][0]
        r["inputs"] = state(
            requirements=[{"name": "Partial", "accessible": None, "reference": None}]
        )
        case["readiness"] = readiness.interpret(case["report"], case["d1"], req)
        s = summarize(case)
        self.assertIn("completeness is unknown", " ".join(s["additional_requirements"]))
        r["applicability"] = state(
            "inapplicable",
            reference="Synthetic declaration",
            rationale="Unrelated purpose",
        )
        case["readiness"] = readiness.interpret(case["report"], case["d1"], req)
        self.assertIn(
            "do not prescribe", " ".join(summarize(case)["additional_requirements"])
        )

    def test_new_analysis_legacy_label_keeps_documentary_prerequisite_separate(self):
        case, req = fixture(index=4)
        case["readiness"] = readiness.interpret(case["report"], case["d1"], req)
        s = summarize(case)
        r = s["selected_readiness_checks"][0]
        self.assertEqual(r["legacy_action_kind"], "new_analysis")
        self.assertIn("documentary prerequisite", r["presentation"])
        self.assertEqual(r["execution"], "not_executed")
        self.assertIn("not an exhaustive", " ".join(s["additional_requirements"]))

    def test_pair_counts_require_exact_declared_population_and_density_settings(self):
        raw, smooth = (
            comparison(counts=(2, 6), ari=0.193),
            comparison("representation", "smooth", (10, 6)),
        )
        smooth["decision_summary"] = True
        s = view.build_report([raw, smooth])["cases"][1]["decision_summary"]
        self.assertEqual(
            [
                (x["reference_clusters"], x["clusters"])
                for x in s["paired_representation_counts"]
            ],
            [(2, 10), (6, 6)],
        )
        raw["d1"]["request"]["source"]["population_id"] = "other"
        raw["d1"]["request"]["evidence"][0]["scope"]["population_id"] = "other"
        raw["d1"] = d1.interpret(raw["report"], raw["d1"]["request"])
        self.assertEqual(
            view.build_report([raw, smooth])["cases"][1]["decision_summary"][
                "paired_representation_counts"
            ],
            [],
        )

    def test_missing_companion_keeps_refusals_without_inventing_crosswalk(self):
        case = {"case_id": "unknown", "report": {"rmse": 1}, "decision_summary": True}
        row = view.build_report([case])["cases"][0]
        self.assertEqual(row["companions"]["d1"]["status"], "unavailable")
        self.assertIn(
            "no additional D6 benefit", row["decision_summary"]["observed"][0]
        )
        self.assertEqual(row["decision_summary"]["selected_readiness_checks"], [])

    def test_same_semantic_sections_drive_all_formats_with_escaped_input(self):
        case = public_case()
        case["decision_summary"] = True
        result = view.render_report([case])
        summary = result["view"]["cases"][0]["decision_summary"]
        for text in summary["verify_now"]:
            self.assertIn(html.escape(text, quote=True), result["html"])
            self.assertIn(view._md(text), result["markdown"])
        self.assertLess(
            result["html"].index("What the analyst can verify now"),
            result["html"].index("Detailed scientific evidence"),
        )
        self.assertNotIn("<script", result["html"].lower())
        self.assertIn(
            "Absence from the original source has not been established", result["html"]
        )

    def test_summary_option_is_boolean_and_stale_source_remains_rejected(self):
        c = public_case()
        c["decision_summary"] = "true"
        with self.assertRaisesRegex(ValueError, "BOOLEAN_REQUIRED"):
            view.render_report([c])
        c["decision_summary"] = True
        c["report"]["changed"] = True
        with self.assertRaises(ValueError):
            view.render_report([c])

    def test_cli_manifest_and_flag_use_same_consumer_and_preserve_sources(self):
        case = public_case()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "source.json").write_bytes(encoded(case["report"]))
            (p / "d1.json").write_bytes(encoded(case["d1"]))
            manifest = {
                "cases": [
                    {
                        "case_id": "one",
                        "report": "source.json",
                        "d1": "d1.json",
                        "decision_summary": True,
                    }
                ]
            }
            (p / "manifest.json").write_text(json.dumps(manifest))
            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "nirs4all_domains.report_view",
                    "--manifest",
                    str(p / "manifest.json"),
                    "--out",
                    str(p / "out"),
                ],
                check=True,
                capture_output=True,
            )
            row = json.loads((p / "out.json").read_text())["cases"][0]
            self.assertIn("decision_summary", row)
            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "nirs4all_domains.report_view",
                    str(p / "source.json"),
                    "--d1",
                    str(p / "d1.json"),
                    "--decision-summary",
                    "--out",
                    str(p / "flag"),
                ],
                check=True,
                capture_output=True,
            )
            flag = json.loads((p / "flag.json").read_text())["cases"][0]
            self.assertEqual(flag["decision_summary"], row["decision_summary"])
            self.assertEqual((p / "source.json").read_bytes(), encoded(case["report"]))


if __name__ == "__main__":
    unittest.main()
