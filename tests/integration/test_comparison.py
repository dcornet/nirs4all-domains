"""D3 read-only adversaries. Synthetic/public metrics only; no numerical backend."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator, ValidationError

from nirs4all_domains.comparison_interpretation import interpret, markdown, validate_annotation, SCHEMA_PATH
from nirs4all_domains.storage import fingerprint

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "docs/examples/comparison"
PUBLIC = ROOT / "docs/benchmarks/alpha17/tablet-pilot-summary.json"


def metric(value):
    return {"status": "computed", "reason": None, "value": value}


def fixture():
    report = {"source": {"dataset": "synthetic", "content": "1", "view": "X"},
              "target": "mass fraction of A", "unit": "%w/w", "model": "PLS", "pipeline": "raw, fixed grid",
              "e": {"population": "original experiment A", "ids": ["1", "2", "3"], "n": 3,
                    "training": "original training pool", "n_train": 20,
                    "rmse": metric(1.0), "skill": metric(0.5), "null": metric(2.0),
                    "null_population": "original experiment A"},
              "predictions": [0.5, 2.5, 3.0]}
    side = {"evaluation": "/e", "pointers": {
        "source": ["/source"], "target": "/target", "units": "/unit", "population": "/e/population",
        "evaluation_ids": "/e/ids", "n_evaluation": "/e/n", "training_population": "/e/training",
        "n_train": "/e/n_train", "model": "/model", "pipeline": "/pipeline",
        "rmse": "/e/rmse", "skill": "/e/skill", "null_rmse": "/e/null", "null_population": "/e/null_population"},
        "null_definition": "Training-only mean, RMSE on the evaluation population",
        "skill_definition": "one_minus_rmse_over_null_rmse",
        "intent": {"intended_use": "known_context", "prediction_unit": "new_specimens",
                   "prediction_population": "original experiment A", "split": {"family": "random_kfold"},
                   "groups": {"basis": "none"}, "transductive": False}}
    stress = deepcopy(report)
    stress["e"]["rmse"] = metric(1.5)
    stress["e"]["skill"] = metric(0.25)
    return report, stress, {"reference": side, "stress": deepcopy(side)}


class Comparison(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.request = fixture()

    def run_case(self):
        return interpret(self.a, self.b, self.request)

    def test_matched_ids_and_exact_numeric_preservation(self):
        original = deepcopy((self.a, self.b, self.request))
        result = self.run_case()
        self.assertEqual(result["evaluation_matching"], "matched_ids")
        self.assertEqual(result["compatibility"]["source"], "same")
        self.assertEqual(result["rmse_difference"]["value"], 0.5)
        self.assertEqual(result["relative_rmse_deterioration"]["value"], 0.5)
        self.assertEqual(result["performance"]["reference"]["rmse"], self.a["e"]["rmse"])
        self.assertEqual((self.a, self.b, self.request), original)
        validate_annotation(self.a, self.b, result)
        self.assertEqual(fingerprint(result), fingerprint(self.run_case()))
        result["context"]["reference"]["source"][0]["dataset"] = "annotation consumer edit"
        self.assertEqual((self.a, self.b, self.request), original)

    def test_reordered_ids_are_matched_as_sets_without_reordering_predictions(self):
        self.b["e"]["ids"].reverse()
        self.assertEqual(self.run_case()["evaluation_matching"], "matched_ids")
        self.assertEqual(self.b["predictions"], [0.5, 2.5, 3.0])

    def test_equal_counts_and_partial_overlap_are_not_paired(self):
        self.b["e"]["ids"] = ["1", "2", "4"]
        result = self.run_case()
        self.assertEqual(result["evaluation_matching"], "unmatched_ids")
        self.assertIn("must not be described as paired", " ".join(result["supported_claims"]))

    def test_same_ids_different_source_content_or_population_do_not_match(self):
        for field in ("source", "population"):
            with self.subTest(field=field):
                self.setUp()
                if field == "source": self.b["source"]["content"] = "2"
                else: self.b["e"]["population"] = "other experiment"
                self.assertNotEqual(self.run_case()["evaluation_matching"], "matched_ids")

    def test_missing_ids_never_inferred_from_equal_sample_counts(self):
        self.request["stress"]["pointers"].pop("evaluation_ids")
        self.assertEqual(self.run_case()["evaluation_matching"], "unknown")

    def test_equal_unavailable_identity_states_never_prove_matching(self):
        for report in (self.a, self.b):
            report["e"]["population"] = {"status": "unavailable", "reason": "UNKNOWN_POPULATION", "value": None}
        result = self.run_case()
        self.assertEqual(result["compatibility"]["population"], "unknown")
        self.assertEqual(result["evaluation_matching"], "unknown")

    def test_unavailable_units_prevent_direct_comparison(self):
        self.b["unit"] = {"status": "unavailable", "reason": "UNITS_UNKNOWN", "value": None}
        self.assertEqual(self.run_case()["direct_comparison"], "unknown")

    def test_different_sample_counts(self):
        self.b["e"]["ids"].append("4")
        self.b["e"]["n"] = 4
        result = self.run_case()
        self.assertEqual(result["compatibility"]["n_evaluation"], "different")
        self.assertEqual(result["evaluation_matching"], "unmatched_ids")
        self.assertIn("n_evaluation is different", " ".join(result["limitations"]))

    def test_duplicate_empty_or_count_inconsistent_ids_rejected(self):
        for ids in (["1", "1", "3"], ["1", "", "3"], ["1"], []):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.b["e"]["ids"] = ids
                self.run_case()

    def test_target_or_unit_mismatch_rejects_direct_contrast(self):
        for field in ("target", "unit"):
            with self.subTest(field=field):
                self.setUp()
                self.b[field] = "incompatible"
                result = self.run_case()
                self.assertEqual(result["direct_comparison"], "incompatible")
                for name in ("rmse_difference", "relative_rmse_deterioration"):
                    self.assertEqual(result[name]["reason"], "INCOMPATIBLE_TARGET_OR_UNITS")
                    self.assertIsNone(result[name]["value"])
                self.assertIn("Direct comparison rejected", " ".join(result["limitations"]))

    def test_missing_target_or_units_is_unknown(self):
        self.request["stress"]["pointers"].pop("units")
        self.assertEqual(self.run_case()["direct_comparison"], "unknown")
        self.assertIsNone(self.run_case()["rmse_difference"]["value"])

    def test_x_only_reports_remain_available_without_target_or_estimator(self):
        report = {"x_summary": {"status": "computed", "reason": None, "value": {"n": 12}}}
        side = {"evaluation": "", "pointers": {}}
        result = interpret(report, report, {"reference": side, "stress": side})
        self.assertEqual(result["direct_comparison"], "unknown")
        self.assertEqual(result["evaluation_matching"], "unknown")
        self.assertIsNone(result["rmse_difference"]["value"])
        self.assertEqual(len(result["validation_intent"]["reference"]["interpretations"]), 3)
        self.assertIn("predictive performance is not established", markdown(result))

    def test_no_unsupported_causal_or_independence_claim_is_established(self):
        result = self.run_case()
        claims = " ".join(result["supported_claims"])
        for forbidden in ("causal shortcut", "independent database", "universally preferred", "physical factor"):
            self.assertNotIn(forbidden, claims)
        self.assertIn("without a significance test", claims)
        self.assertIn("universal model/validation ranking", " ".join(result["stronger_claims_not_established"]))

    def test_different_null_population_or_definition_keeps_skills_separate(self):
        for change in ("population", "definition"):
            with self.subTest(change=change):
                self.setUp()
                if change == "population": self.b["e"]["null_population"] = "other pool"
                else: self.request["stress"]["null_definition"] = "population oracle mean"
                result = self.run_case()
                self.assertEqual(result["null_comparison"], "separate_definitions")
                self.assertIn("no common-null effect", " ".join(result["limitations"]))
                self.assertNotIn("skill_difference", result)

    def test_missing_null_limits_baseline_claim(self):
        self.request["reference"]["pointers"].pop("null_rmse")
        self.assertEqual(self.run_case()["baseline_context"], "unknown")

    def test_negative_skill_baseline_changes_meaning_of_same_relative_gap(self):
        positive = self.run_case()
        self.a["e"]["null"] = metric(0.5)
        self.a["e"]["skill"] = metric(-1.0)
        negative = self.run_case()
        self.assertEqual(positive["relative_rmse_deterioration"], negative["relative_rmse_deterioration"])
        self.assertEqual(positive["baseline_context"], "better_than_stated_null")
        self.assertEqual(negative["baseline_context"], "no_improvement_over_stated_null")
        self.assertIn("no improvement", " ".join(negative["limitations"]))
        self.assertIn("Practical usefulness still needs", " ".join(positive["limitations"]))

    def test_zero_skill_is_not_useful_prediction_claim(self):
        self.a["e"]["skill"] = metric(0.0)
        self.a["e"]["null"] = metric(1.0)
        self.assertEqual(self.run_case()["baseline_context"], "no_improvement_over_stated_null")

    def test_unknown_skill_definition_cannot_imply_usefulness(self):
        self.request["reference"].pop("skill_definition")
        self.assertEqual(self.run_case()["baseline_context"], "unknown")

    def test_zero_rmse_keeps_absolute_difference_and_unavailable_ratio(self):
        self.a["e"]["rmse"] = metric(0.0)
        self.a["e"]["skill"] = metric(1.0)
        result = self.run_case()
        self.assertEqual(result["rmse_difference"]["value"], 1.5)
        self.assertEqual(result["relative_rmse_deterioration"], {"status": "unavailable", "reason": "ZERO_REFERENCE_RMSE", "value": None})

    def test_unavailable_rmse_preserves_reason_and_null_contrast(self):
        self.a["e"]["rmse"] = {"status": "insufficient_data", "reason": "NO_EVAL_ROWS", "value": None}
        result = self.run_case()
        self.assertEqual(result["performance"]["reference"]["rmse"]["reason"], "NO_EVAL_ROWS")
        self.assertEqual(result["rmse_difference"]["reason"], "RMSE_UNAVAILABLE")

    def test_bad_numeric_states_rejected(self):
        for value in (-1.0, True, float("nan"), float("inf"), {"status": "computed", "reason": "bad", "value": 1},
                      {"status": "unavailable", "reason": None, "value": None},
                      {"status": "unavailable", "reason": "X", "value": 1},
                      {"status": 17, "reason": "X", "value": None}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.a["e"]["rmse"] = value
                self.run_case()

    def test_arithmetic_overflow_is_explicitly_unavailable(self):
        self.a["e"]["rmse"] = metric(1e-300)
        self.b["e"]["rmse"] = metric(1e300)
        for side in ("reference", "stress"):
            self.request[side].pop("skill_definition")
        result = self.run_case()
        self.assertEqual(result["relative_rmse_deterioration"]["reason"], "ARITHMETIC_OVERFLOW")
        self.assertIsNone(result["relative_rmse_deterioration"]["value"])

    def test_different_models_pipelines_and_training_sizes_are_visible(self):
        self.b["model"] = "Ridge"
        self.b["pipeline"] = "SNV"
        self.b["e"]["training"] = "smaller training pool"
        self.b["e"]["n_train"] = 10
        result = self.run_case()
        for key in ("model", "pipeline", "training_population", "n_train"):
            self.assertEqual(result["compatibility"][key], "different")
        self.assertIn("n_train: `10`", markdown(result))
        self.assertIn("isolated split effect is not established", markdown(result))

    def test_unknown_independence_and_unknown_intent_remain_conditional(self):
        self.request["reference"].pop("intent")
        result = self.run_case()
        readings = result["validation_intent"]["reference"]["interpretations"]
        self.assertEqual(len(readings), 3)
        self.assertTrue(all(r["conditional"] for r in readings))
        self.assertIn("dependencies are unknown", " ".join(result["missing_information"]))
        self.assertIn("Independent specimen", " ".join(result["stronger_claims_not_established"]))

    def test_x_derived_groups_never_become_documented_context(self):
        self.request["stress"]["intent"] = {"intended_use": "outside_context", "split": {"family": "loco_x"},
                                             "groups": {"basis": "physical", "construction": "complete_x"}, "transductive": False}
        result = self.run_case()
        intent = result["validation_intent"]["stress"]
        self.assertTrue(intent["uses_x_derived_groups"])
        self.assertTrue(intent["transductive"]["value"])
        self.assertIn("do not establish physical", markdown(result))
        self.assertNotIn("Declared exclusion", " ".join(intent["interpretations"][0]["supported_claims"]))

    def test_documented_genotype_and_experiment_holdouts_keep_scope(self):
        for kind in ("genotype", "experiment"):
            self.request["stress"]["intent"] = {"intended_use": "outside_context", "split": {"family": "context_holdout"},
                "groups": {"basis": "declared_context"}, "factors": [{"name": kind, "kind": kind,
                "excluded": True, "relevant_to_intent": True, "evidence": "declared", "reference": "synthetic roster", "relationship": "crossed with treatment"}]}
            result = self.run_case()
            text = markdown(result)
            self.assertIn(f"exclusion of {kind}", text)
            self.assertIn("crossed with treatment", text)

    def test_stale_binding_and_tampered_claims_rejected(self):
        result = self.run_case()
        for change in ("prediction", "metric", "identity", "claim"):
            with self.subTest(change=change):
                a, b, annotation = deepcopy((self.a, self.b, result))
                if change == "prediction": a["predictions"][0] = 99
                elif change == "metric": b["e"]["rmse"]["value"] = 99
                elif change == "identity": b["source"]["content"] = "2"
                else: annotation["supported_claims"].append("Universal transfer established")
                with self.assertRaises(ValueError): validate_annotation(a, b, annotation)

    def test_strict_schema_and_pointer_scope(self):
        for change in ("key", "pointer", "scope"):
            self.setUp()
            if change == "key": self.request["reference"]["surprise"] = True
            elif change == "pointer": self.request["reference"]["pointers"]["rmse"] = "not-a-pointer"
            else: self.request["reference"]["pointers"]["rmse"] = "/predictions/0"
            with self.assertRaises((ValueError, ValidationError)): self.run_case()

    def test_intent_metric_cannot_reference_another_evaluation(self):
        self.a["other"] = {"rmse": metric(0.01)}
        self.request["reference"]["intent"]["prediction_metrics"] = [{"name": "rmse", "pointer": "/other/rmse"}]
        with self.assertRaises(ValueError): self.run_case()

    def test_missing_pointer_is_not_silently_treated_as_missing_evidence(self):
        self.request["reference"]["pointers"]["n_train"] = "/e/typo"
        with self.assertRaises(ValueError): self.run_case()

    def test_same_null_scope_is_not_a_common_null_effect(self):
        result = self.run_case()
        self.assertEqual(result["null_comparison"], "same_definition_and_population")
        self.assertIn("no skill difference or common-null effect", " ".join(result["limitations"]))

    def test_contradictory_defined_skill_is_rejected(self):
        self.a["e"]["skill"] = metric(-1.0)
        with self.assertRaises(ValueError): self.run_case()

    def test_scalar_metrics_and_escaped_identity_pointers(self):
        self.a["e"]["rmse"] = 1.0
        self.b["e"]["rmse"] = 1.5
        for report, side in ((self.a, "reference"), (self.b, "stress")):
            report["target~/name"] = report["target"]
            self.request[side]["pointers"]["target"] = "/target~0~1name"
        self.assertEqual(self.run_case()["rmse_difference"]["value"], 0.5)

    def test_packaged_schema_matches_generated_contract(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import generate_comparison_schema
            schema = generate_comparison_schema.schema()
        finally: sys.path.pop(0)
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema, json.loads(SCHEMA_PATH.read_text()))
        self.assertEqual(schema, json.loads((ROOT / "schemas/comparison-interpretation.v1.schema.json").read_text()))

    def test_public_historical_example_reproduces_without_source_change(self):
        source_bytes = PUBLIC.read_bytes()
        report = json.loads(source_bytes)
        request = json.loads((EXAMPLE / "tablet.request.json").read_text())
        result = interpret(report, report, request)
        validate_annotation(report, report, result)
        self.assertEqual(result, json.loads((EXAMPLE / "tablet.annotation.json").read_text()))
        self.assertEqual(markdown(result), (EXAMPLE / "tablet.annotation.md").read_text(encoding="utf-8"))
        self.assertEqual(result["evaluation_matching"], "unmatched_ids")
        self.assertEqual(result["null_comparison"], "separate_definitions")
        self.assertEqual(PUBLIC.read_bytes(), source_bytes)

    def test_cli_no_provider_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory)/name for name in ("a.json", "b.json", "request.json", "out.json")]
            for path, obj in zip(paths, (self.a, self.b, self.request)):
                path.write_text(json.dumps(obj), encoding="utf-8")
            command = [sys.executable, "-m", "nirs4all_domains.comparison_interpretation", str(paths[0]), str(paths[1]),
                       "--request", str(paths[2]), "--out", str(paths[3])]
            subprocess.run(command, check=True, capture_output=True)
            self.assertTrue(paths[3].with_suffix(".md").exists())
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            command[-1] = str(paths[0])
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        code = "import sys; import nirs4all_domains.comparison_interpretation; assert not any(k in sys.modules for k in ('numpy','n4m','sklearn','nirs4all'))"
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
