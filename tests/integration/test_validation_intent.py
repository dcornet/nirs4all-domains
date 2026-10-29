"""D2 symbolic/adversarial fixtures. No datasets, fitting or numerical providers."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator, ValidationError

from nirs4all_domains.storage import fingerprint
from nirs4all_domains.validation_intent import interpret, markdown, validate_annotation

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "docs/benchmarks/alpha17/tablet-pilot-summary.json"
EXAMPLE = ROOT / "docs/examples/validation-intent"


def dependency(evidence="verified", separated=True, kind="specimen"):
    return {"unit": kind, "kind": kind, "evidence": evidence,
            "separated": separated, "reference": "synthetic fixture identity audit" if evidence != "unknown" else None}


def factor(kind, excluded=True, relevant=True):
    return {"name": kind, "kind": kind, "excluded": excluded,
            "relevant_to_intent": relevant, "evidence": "verified",
            "reference": "synthetic split roster", "relationship": None}


class ValidationIntent(unittest.TestCase):
    def setUp(self):
        self.report = {"context": {"dataset": "synthetic", "target": "y", "estimator": "fixture"},
                       "rmse": {"status": "computed", "reason": None, "value": 1.25},
                       "support": {"status": "unavailable", "reason": "NO_FULL_SUPPORT", "value": None},
                       "predictions": [1.0, 2.0, 3.0]}
        self.request = {"intended_use": "proof_of_concept", "prediction_population": "Observed experiment",
                        "prediction_unit": "new_specimens", "split": {"family": "random_kfold"},
                        "groups": {"basis": "none"}, "transductive": False,
                        "prediction_metrics": [{"name": "rmse", "pointer": "/rmse"}]}

    def reading(self, request=None, report=None):
        return interpret(self.report if report is None else report,
                         self.request if request is None else request)["interpretations"][0]

    def supported(self, request=None):
        return " ".join(self.reading(request)["supported_claims"])

    def test_proof_of_concept_does_not_establish_external_transfer(self):
        result = self.reading()
        self.assertIn("within-evaluation proof-of-concept", " ".join(result["supported_claims"]))
        self.assertIn("Transfer to new experiments", " ".join(result["stronger_claims_not_established"]))
        outside = {**self.request, "intended_use": "outside_context"}
        self.assertNotIn("Declared exclusion", self.supported(outside))
        self.assertIn("Unseen-population transfer", " ".join(self.reading(outside)["stronger_claims_not_established"]))

    def test_new_specimens_and_repeated_acquisitions_are_distinct(self):
        request = {**self.request, "intended_use": "known_context", "split": {"family": "group_kfold"},
                   "groups": {"basis": "physical"}, "dependencies": [dependency()]}
        self.assertIn("verified specimen separation", self.supported(request))
        # One independently evidenced specimen per observation can make ordinary
        # KFold a new-specimen evaluation too; do not impose a split-name ranking.
        random = {**request, "split": {"family": "random_kfold"}, "groups": {"basis": "none"}}
        self.assertIn("verified specimen separation", self.supported(random))
        acquisitions = {**request, "prediction_unit": "new_acquisitions", "dependencies": [dependency(separated=False)]}
        self.assertIn("new acquisitions of known specimens", self.supported(acquisitions))
        self.assertNotIn("verified specimen separation", self.supported(acquisitions))
        for dependencies in ([dependency("declared")], [dependency(separated=False)],
                             [dependency(), dependency(separated=False, kind="assay_reference")], []):
            with self.subTest(dependencies=dependencies):
                self.assertNotIn("verified specimen separation", self.supported({**request, "dependencies": dependencies}))

    def test_known_versus_excluded_instrument(self):
        request = {**self.request, "intended_use": "outside_context", "split": {"family": "context_holdout"}}
        known = {**request, "factors": [factor("instrument", False)]}
        unseen = {**request, "factors": [factor("instrument")]}
        self.assertNotIn("Declared exclusion", self.supported(known))
        self.assertIn("instrument (instrument, verified evidence)", self.supported(unseen))
        self.assertIn("observed held-out levels only", self.supported(unseen))

    def test_genotype_block_instrument_and_entire_experiment_keep_names(self):
        request = {**self.request, "intended_use": "outside_context", "split": {"family": "logo"}}
        for kind in ("genotype", "block", "instrument", "experiment"):
            with self.subTest(kind=kind):
                result = self.reading({**request, "factors": [factor(kind)]})
                self.assertIn(f"{kind} ({kind}, verified evidence)", " ".join(result["supported_claims"]))
                if kind != "experiment":
                    self.assertNotIn("exclusion of experiment", " ".join(result["supported_claims"]))
                self.assertIn("beyond the tested exclusions", " ".join(result["stronger_claims_not_established"]))

    def test_categorical_column_and_random_cv_cannot_become_logo(self):
        request = {**self.request, "intended_use": "outside_context", "factors": [factor("instrument")]}
        annotation = interpret(self.report, request)
        self.assertNotIn("Declared exclusion", self.supported(request))
        self.assertTrue(any("clarify the actual split" in item for item in annotation["limitations"]))
        request["factors"][0]["excluded"] = False
        self.assertTrue(any("categorical factor alone" in item for item in interpret(self.report, request)["limitations"]))

    def test_x_clusters_never_establish_physical_logo_even_with_conflicting_declaration(self):
        base = {**self.request, "intended_use": "outside_context", "split": {"family": "loco_x"},
                "factors": [factor("experiment")], "dependencies": [dependency()]}
        for basis in ("physical", "x_derived", "mixed"):
            with self.subTest(basis=basis):
                request = {**base, "groups": {"basis": basis, "construction": "complete_x"}, "transductive": False}
                annotation = interpret(self.report, request)
                self.assertTrue(annotation["uses_x_derived_groups"])
                self.assertEqual(annotation["transductive"], {"status": "declared", "reason": None, "value": True})
                self.assertNotIn("Declared exclusion", self.supported(request))
                self.assertTrue(any("conflicts" in s for s in annotation["limitations"]))
        geometric = {**base, "split": {"family": "group_kfold"}, "groups": {"basis": "x_derived", "construction": "train_only"}}
        self.assertFalse(interpret(self.report, geometric)["transductive"]["value"])
        self.assertNotIn("Declared exclusion", self.supported(geometric))
        # Calling the split LOGO cannot disguise complete-X cluster construction.
        complete = {**base, "split": {"family": "logo"},
                    "groups": {"basis": "physical", "construction": "complete_x"}}
        self.assertTrue(interpret(self.report, complete)["uses_x_derived_groups"])
        self.assertNotIn("Declared exclusion", self.supported(complete))

    def test_crossed_factors_stay_separate_without_a_tree_or_automatic_exclusions(self):
        genotype, treatment = factor("genotype"), factor("treatment", False)
        genotype["relationship"] = "crossed with treatment within block"
        treatment["relationship"] = "crossed with genotype within block"
        request = {**self.request, "intended_use": "outside_context", "split": {"family": "logo"},
                   "factors": [genotype, treatment, factor("block", False, False)]}
        result = interpret(self.report, request)
        self.assertEqual(result["facts"]["factors"], request["factors"])
        supported = self.supported(request)
        self.assertIn("exclusion of genotype", supported)
        self.assertNotIn("exclusion of treatment", supported)
        self.assertNotIn("exclusion of block", supported)
        self.assertIn("crossed with treatment", markdown(result))

    def test_unknown_intent_produces_three_conditional_readings(self):
        result = interpret(self.report)
        self.assertEqual([r["intended_use"] for r in result["interpretations"]],
                         ["proof_of_concept", "known_context", "outside_context"])
        self.assertTrue(all(r["conditional"] for r in result["interpretations"]))
        self.assertEqual(result["transductive"], {"status": "unavailable", "reason": "TRANSDUCTIVE_STATUS_UNKNOWN", "value": None})
        self.assertTrue(any("population is unspecified" in s for s in result["missing_information"]))
        validate_annotation(self.report, result)

    def test_x_only_without_target_or_estimator_has_no_predictive_claim(self):
        report = {"geometry": {"pc1": 0.95}}
        result = interpret(report, {"intended_use": "outside_context", "factors": [factor("instrument")],
                                    "split": {"family": "logo"}})
        self.assertIn("predictive performance is not established", " ".join(result["interpretations"][0]["supported_claims"]))
        self.assertNotIn("Declared exclusion", " ".join(result["interpretations"][0]["supported_claims"]))
        self.assertNotIn("target", result["facts"])
        with self.assertRaises(ValueError):
            interpret(report, {"prediction_metrics": [{"name": "rmse", "pointer": "/geometry/pc1"}]})

    def test_support_is_reference_specific_and_unavailable_is_reported(self):
        support = {"pointer": "/support", "description": "Continuous support", "representation": "raw",
                   "reference_population": "training", "limitations": ["No calibrated probability"]}
        result = interpret(self.report, {"spectral_support": [support]})
        self.assertTrue(any("support is unavailable" in s for s in result["missing_information"]))
        self.assertTrue(any("not full support or a risk probability" in s for s in result["limitations"]))
        self.assertIn("No calibrated probability", markdown(result))
        for status in ("error", "insufficient_data", "unavailable"):
            state = {"status": status, "reason": "SUPPORT_NOT_COMPUTED", "value": None}
            failed = interpret({**self.report, "support": state}, {"spectral_support": [support]})
            self.assertTrue(any(status in s and "SUPPORT_NOT_COMPUTED" in s for s in failed["missing_information"]))
        with self.assertRaises(ValueError):
            interpret(self.report, {"spectral_support": [{**support, "pointer": "/not-found"}]})

    def test_determinism_serialization_and_exact_numeric_invariance(self):
        report, request = deepcopy(self.report), deepcopy(self.request)
        before = fingerprint(report)
        first, second = interpret(report, request), interpret(report, request)
        self.assertEqual(first, second)
        self.assertEqual(first, json.loads(json.dumps(first, allow_nan=False)))
        self.assertEqual(report, self.report)
        self.assertEqual(request, self.request)
        self.assertEqual(fingerprint(report), before)
        self.assertEqual(first["source_report"]["sha256"], before)
        self.assertNotIn("predictions", first)
        validate_annotation(report, first)
        report["rmse"]["value"] = 1.2500000000000002
        with self.assertRaises(ValueError):
            validate_annotation(report, first)
        first["interpretations"][0]["supported_claims"] = ["Independently certified external transfer"]
        with self.assertRaises(ValueError):
            validate_annotation(self.report, first)

    def test_bad_evidence_and_nonfinite_json_rejected(self):
        for value in (None, True, [], "excellent"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                interpret({**self.report, "rmse": {"status": "computed", "reason": None, "value": value}}, self.request)
        for state in ({"status": "unavailable", "reason": "MISSING", "value": None},
                      {"status": "computed", "reason": "FAILED", "value": 1.0},
                      {"status": "computed", "reason": None, "value": -1.0}):
            with self.assertRaises(ValueError):
                interpret({**self.report, "rmse": state}, self.request)
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(ValueError):
                interpret({"unrelated_field": value})
        for bad in ({"intended_use": "best_split"}, {"transductive": "false"}, {"auto_logo": True},
                    {"factors": [{**factor("instrument"), "reference": None}]},
                    {"prediction_metrics": [{"name": "rmse", "pointer": "/bad~2escape"}]}):
            with self.assertRaises(ValidationError):
                interpret(self.report, bad)

    def test_finite_negative_r2_does_not_become_positive_scientific_claim(self):
        report = {"r2": {"status": "computed", "reason": None, "value": -12.0}}
        result = interpret(report, {"prediction_metrics": [{"name": "r2", "pointer": "/r2"}]})
        self.assertNotIn("accurate", markdown(result))
        self.assertNotIn("useful X–Y", " ".join(result["interpretations"][2]["supported_claims"]))

    def test_schema_is_packaged_and_generator_has_no_drift(self):
        schema_path = ROOT / "schemas/validation-intent.v1.schema.json"
        schema = json.loads(schema_path.read_text())
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema_path.read_bytes(), (ROOT / "bridges/python/nirs4all_domains" / schema_path.name).read_bytes())
        import importlib.util
        spec = importlib.util.spec_from_file_location("validation_schema", ROOT / "scripts/generate_validation_intent_schema.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(schema, module.schema())
        bad = interpret(self.report)
        bad["transductive"] = {"status": "unavailable", "reason": None, "value": False}
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(bad)

    def test_public_reports_and_closed_legacy_schema_stay_compatible(self):
        # No new field is injected into either open or closed historical reports.
        paths = [PUBLIC, ROOT / "docs/benchmarks/alpha13/profiles/ucph_tablet_nir.raw.json",
                 ROOT / "docs/benchmarks/alpha8/mixed-control-evidence.json"]
        for path in paths:
            with self.subTest(path=path.name):
                original = path.read_bytes()
                report = json.loads(original)
                annotation = interpret(report)
                validate_annotation(report, annotation)
                self.assertEqual(path.read_bytes(), original)
                self.assertNotIn("validation_intent", report)
                if path == PUBLIC or path.name == "mixed-control-evidence.json":
                    name = "exploratory-pilot-summary" if path == PUBLIC else "qualification-evidence"
                    closed = json.loads((ROOT / f"schemas/{name}.v1.schema.json").read_text())
                    self.assertFalse(closed["additionalProperties"])
                    Draft202012Validator(closed).validate(report)
                    # Closed consumers need never accept an extra report field.
                    with self.assertRaises(ValidationError):
                        Draft202012Validator(closed).validate({**report, "validation_intent": annotation})

    def test_worked_example_is_reproducible_against_existing_public_evidence(self):
        request = json.loads((EXAMPLE / "tablet.request.json").read_text())
        report = json.loads(PUBLIC.read_text())
        annotation = interpret(report, request)
        self.assertEqual(annotation, json.loads((EXAMPLE / "tablet.annotation.json").read_text()))
        self.assertEqual(markdown(annotation), (EXAMPLE / "tablet.annotation.md").read_text(encoding="utf-8"))
        validate_annotation(report, annotation)
        text = " ".join(annotation["interpretations"][0]["supported_claims"])
        self.assertIn("Type (other, verified evidence)", text)
        self.assertNotIn("exclusion of experiment", text)

    def test_cli_preserves_source_bytes_and_blocks_overwrites(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            source, request, output = path / "report.json", path / "request.json", path / "annotation.json"
            source.write_text(json.dumps(self.report), encoding="utf-8")
            request.write_text(json.dumps(self.request), encoding="utf-8")
            original = source.read_bytes()
            command = [sys.executable, "-m", "nirs4all_domains.validation_intent", str(source), "--intent", str(request), "--out"]
            subprocess.run([*command, str(output)], check=True, capture_output=True)
            self.assertEqual(source.read_bytes(), original)
            validate_annotation(self.report, json.loads(output.read_text()))
            self.assertTrue(output.with_suffix(".md").is_file())
            for protected in (output, source, request):
                self.assertNotEqual(subprocess.run([*command, str(protected)], capture_output=True).returncode, 0)
            self.assertEqual(source.read_bytes(), original)

    def test_no_numerical_provider_is_imported(self):
        code = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'n4m', 'numpy', 'sklearn', 'dagml', 'nirs4all', 'nirs4all_datasets'}:
            raise RuntimeError('Numerical provider imported: ' + fullname)
sys.meta_path.insert(0, Block())
from nirs4all_domains.validation_intent import interpret, markdown
assert 'predictive performance is not established' in markdown(interpret({'X_only': True}))
"""
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
