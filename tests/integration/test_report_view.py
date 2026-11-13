"""Standalone consumer: immutable sources, exact owner checks and safe rendering."""

import json
import re
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from nirs4all_domains import report_view as view
from nirs4all_domains import structural_warnings as d1
from nirs4all_domains import validation_intent as d2
from nirs4all_domains.storage import encoded, fingerprint

ROOT = Path(__file__).resolve().parents[2]


def public_case():
    folder = ROOT / "docs/examples/structural-warnings"
    return {
        "case_id": "tablet",
        "report": json.loads((folder / "tablet.report.json").read_text()),
        "d1": json.loads((folder / "tablet.annotation.json").read_text()),
    }


def synthetic(kind):
    source = {
        "dataset_id": "synthetic-d4-rendering",
        "source_id": "X",
        "content_version": "schema-fixture-v1",
        "population_id": "synthetic-population",
        "scope_kind": "synthetic",
        "representation": "raw",
        "n_observations": 4,
        "identity_scope": "unknown",
        "references": [
            "Explicit synthetic interpretation fixture; no fit or empirical measurement"
        ],
        "original_source_identifiers": [],
        "provenance_group": None,
        "original_study_family": None,
        "study_reference": None,
    }
    value = (
        {"all_noise_settings": 1, "cluster_counts": [0], "trivial_partition": True}
        if kind == "all-noise"
        else {"full_x_overlap": 1.0, "partition_ari": 1.0}
        if kind == "contradicted"
        else {
            "partition_ari": {
                "status": "unavailable",
                "reason": "NATIVE_REFUSAL_FIXTURE",
                "value": None,
            },
            "trivial_partition": True,
        }
    )
    report = {
        "fixture": "Synthetic schema fixture, not a scientific calculation",
        "evidence": value,
    }
    request = {
        "source": source,
        "evidence": [
            {
                "kind": "representation",
                "root": "/evidence",
                "scope": {k: source[k] for k in d1.IDENTITY},
                "method": {
                    "owner": "source_documentation",
                    "name": "Schema fixture",
                    "version": "1",
                    "settings": {"new_fits": 0},
                    "reference": "Explicit synthetic values",
                },
                "metrics": {k: "/evidence/" + k for k in value},
                "qualifications": {
                    "admissible": True,
                    "matched_queries": True,
                    "matched_observations": True,
                    "representations": ["raw", "declared alternative"],
                },
            }
        ],
    }
    return {"case_id": kind, "report": report, "d1": d1.interpret(report, request)}


class StandaloneReport(unittest.TestCase):
    def test_public_report_exact_annotations_and_numerics_unchanged(self):
        c = public_case()
        before = deepcopy(c)
        result = view.render_report([c])
        self.assertEqual(c, before)
        row = result["view"]["cases"][0]
        self.assertEqual(row["companions"]["d1"]["value"], c["d1"])
        self.assertEqual(
            row["source_reports"]["reference"]["sha256"], fingerprint(c["report"])
        )
        for phrase in (
            "What was observed?",
            "Conditional methodological hypothesis",
            "What should be checked next?",
            "Required data:",
            "Stronger claims not established",
        ):
            self.assertIn(phrase, result["html"])
        self.assertEqual(
            result["view"]["coverage"]["original_database_count"], "unknown"
        )

    def test_source_and_stale_annotation_hash_fail(self):
        c = public_case()
        c["report"]["changed_after_annotation"] = True
        with self.assertRaises(ValueError):
            view.render_report([c])
        c = public_case()
        c["d1"]["source_report"]["sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            view.render_report([c])

    def test_population_view_source_and_intent_tampering_fail(self):
        for key in ("population_id", "representation", "source_id", "dataset_id"):
            c = public_case()
            c["d1"]["request"]["source"][key] = "wrong"
            with self.assertRaises(ValueError):
                view.render_report([c])
        c = public_case()
        c["d1"]["request"]["validation_intent"]["intended_use"] = "proof_of_concept"
        with self.assertRaises(ValueError):
            view.render_report([c])

    def test_unsupported_claims_and_separate_d2_intent_are_rejected(self):
        c = public_case()
        c["d1"]["warnings"][0]["risk_hypothesis"] = "Clusters prove physical leakage."
        with self.assertRaises(ValueError):
            view.render_report([c])
        c = public_case()
        c["d2"] = d2.interpret(c["report"], {"intended_use": "proof_of_concept"})
        with self.assertRaisesRegex(ValueError, "D1_D2_INTENT_MISMATCH"):
            view.render_report([c])

    def test_missing_companions_and_native_preflight_are_not_invented_warnings(self):
        native = {
            "schema_version": 1,
            "engine_version": "fixture",
            "protocol_bundle_version": "fixture",
            "validation": {},
            "capabilities": [],
            "metrics": [
                {
                    "metric_id": "native.zero",
                    "status": "computed",
                    "value": 0,
                    "reason_code": None,
                },
                {
                    "metric_id": "native.unavailable",
                    "status": "unsupported",
                    "value": None,
                    "reason_code": "UNSUPPORTED",
                },
            ],
            "findings": [],
            "limitations": [],
        }
        original = deepcopy(native)
        result = view.render_report([{"case_id": "native", "report": native}])
        row = result["view"]["cases"][0]
        self.assertEqual(row["companions"]["d1"]["status"], "unavailable")
        self.assertEqual(sum(row["warning_counts"].values()), 0)
        self.assertEqual(
            row["native_preflight"]["value"]["metrics"][0]["displayed_scalar"], 0
        )
        self.assertEqual(
            row["native_preflight"]["value"]["metrics"][1]["reason_code"], "UNSUPPORTED"
        )
        self.assertEqual(native, original)

    def test_all_noise_contradicted_unavailable_and_no_physical_proof_remain_distinct(
        self,
    ):
        result = view.render_report(
            [synthetic(k) for k in ("all-noise", "contradicted", "unavailable")]
        )
        rows = result["view"]["cases"]
        values = [
            next(
                w
                for w in c["companions"]["d1"]["value"]["warnings"]
                if w["warning_id"] == "preprocessing_dependent_organization"
            )
            for c in rows
        ]
        self.assertEqual(
            [w["value"] for w in values], ["observed", "contradicted", None]
        )
        self.assertEqual(values[-1]["status"], "unavailable")
        self.assertTrue(
            all(
                next(
                    w
                    for w in c["companions"]["d1"]["value"]["warnings"]
                    if w["warning_id"] == "physical_unit_dependence"
                )["status"]
                == "unavailable"
                for c in rows
            )
        )
        self.assertEqual(result["view"]["coverage"]["n_synthetic_dataset_ids"], 1)
        self.assertEqual(result["view"]["coverage"]["n_canonical_dataset_ids"], 0)

    def test_existing_public_d3_and_noncomparable_result(self):
        report = json.loads(
            (ROOT / "docs/benchmarks/alpha17/tablet-pilot-summary.json").read_text()
        )
        a3 = json.loads(
            (ROOT / "docs/examples/comparison/tablet.annotation.json").read_text()
        )
        c = {
            "case_id": "comparison",
            "report": report,
            "comparison_report": report,
            "d3": a3,
        }
        result = view.render_report([c])
        self.assertEqual(result["view"]["cases"][0]["companions"]["d3"]["value"], a3)
        self.assertIn("Exact comparison conditions", result["html"])
        from nirs4all_domains import comparison_interpretation as comparison

        first = {"target": "same", "units": "A", "rmse": 1.0}
        second = {"target": "same", "units": "B", "rmse": 2.0}
        request = {
            side: {
                "evaluation": "",
                "pointers": {"target": "/target", "units": "/units", "rmse": "/rmse"},
            }
            for side in ("reference", "stress")
        }
        ann = comparison.interpret(first, second, request)
        result = view.render_report(
            [
                {
                    "case_id": "incompatible",
                    "report": first,
                    "comparison_report": second,
                    "d3": ann,
                }
            ]
        )
        self.assertEqual(
            result["view"]["cases"][0]["companions"]["d3"]["value"][
                "direct_comparison"
            ],
            "incompatible",
        )

    def test_mixed_x_and_prediction_scope_requires_a_qualified_crosswalk(self):
        c = public_case()
        c["d3"] = {}
        c["comparison_report"] = c["report"]
        with self.assertRaisesRegex(ValueError, "SCOPE_CROSSWALK_REQUIRED"):
            view.render_report([c])

    def test_free_text_html_markdown_and_fence_injection_are_escaped(self):
        c = synthetic("all-noise")
        attack = "<script>window.D4_INJECTION=1</script><img src=x onerror=alert(1)> [bad](javascript:alert(1))\n```\n# injected"
        c["label"] = attack
        c["d1"]["request"]["source"]["references"] = [attack]
        c["d1"] = d1.interpret(c["report"], c["d1"]["request"])
        result = view.render_report([c], attack)
        self.assertNotIn("<script>", result["html"])
        self.assertNotIn("<img src=x", result["html"])
        # Literal source strings inside fenced JSON are provenance, not active
        # Markdown. Check both the exposed prose and that every fence is JSON.
        blocks = re.findall(r"```json\n([\s\S]*?)\n```", result["markdown"])
        for block in blocks:
            json.loads(block)
        prose = re.sub(r"```json\n[\s\S]*?\n```", "", result["markdown"])
        self.assertNotIn("[bad](javascript:", prose)
        self.assertIn("&lt;script&gt;", result["html"])
        self.assertIn("Content-Security-Policy", result["html"])
        self.assertEqual(
            result["view"]["cases"][0]["companions"]["d1"]["value"], c["d1"]
        )

    def test_no_overwrite_and_source_bytes_preserved(self):
        c = public_case()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            original = p / "source.json"
            original.write_bytes(encoded(c["report"]))
            before = original.read_bytes()
            with self.assertRaises(ValueError):
                view.export_report([c], p / "source", [original])
            outputs = view.export_report([c], p / "view", [original])
            self.assertEqual(set(outputs), {"html", "md", "json"})
            self.assertEqual(original.read_bytes(), before)
            with self.assertRaises(ValueError):
                view.export_report([c], p / "view")

    def test_schema_finite_values_and_dataset_denominators(self):
        self.assertEqual(
            view.SCHEMA_PATH.read_bytes(),
            (ROOT / "schemas/standalone-report.v1.schema.json").read_bytes(),
        )
        c = public_case()
        second = deepcopy(c)
        second["case_id"] = "same-dataset-other-panel"
        result = view.build_report([c, second])
        self.assertEqual(result["coverage"]["n_cases"], 2)
        self.assertEqual(result["coverage"]["n_canonical_dataset_ids"], 1)
        self.assertEqual(len(result["coverage"]["canonical_X_views"]), 1)
        c["report"]["nonfinite"] = float("nan")
        with self.assertRaises(ValueError):
            view.render_report([c])
