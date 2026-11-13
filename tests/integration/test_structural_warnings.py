"""D1 counterexamples: scientific interpretation, conditional actions and compatibility."""

import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import ValidationError
from nirs4all_domains import structural_warnings as d1
from nirs4all_domains.storage import fingerprint

ROOT = Path(__file__).resolve().parents[2]
IDENTITY = d1.IDENTITY


def source(dataset="synthetic", rep="raw"):
    return {
        "dataset_id": dataset,
        "source_id": "X",
        "content_version": "1",
        "population_id": "original-frozen-population",
        "scope_kind": "synthetic",
        "representation": rep,
        "n_observations": 12,
        "identity_scope": "unknown",
        "references": ["synthetic fixture"],
        "original_source_identifiers": [],
        "provenance_group": None,
        "original_study_family": None,
        "study_reference": None,
    }


def binding(s, kind, root, metrics, **q):
    return {
        "kind": kind,
        "root": root,
        "scope": {k: s[k] for k in IDENTITY},
        "method": {
            "owner": "Methods",
            "name": "stored native diagnostic",
            "version": "fixture1",
            "settings": {"fixed": True},
            "reference": "synthetic/public receipt",
        },
        "metrics": {k: root + "/" + value for k, value in metrics.items()},
        "qualifications": q,
    }


def fixture(kind, values, **q):
    s = source()
    report = {"e": values, "predictions": [1.0, 2.0], "rmse": 0.5}
    request = {
        "source": s,
        "evidence": [binding(s, kind, "/e", {k: k for k in values}, **q)],
    }
    return report, request


def warning(result, name):
    return next(w for w in result["warnings"] if w["warning_id"] == name)


class StructuralWarnings(unittest.TestCase):
    def test_preflight_spectral_duplicates_do_not_establish_physical_units(self):
        a, b = fixture(
            "physical_units",
            {"qualified_preflight_finding": True},
            dependency_basis="qualified_preflight",
            evidence_quality="verified",
            preflight_finding_scope="spectral_duplicates",
        )
        b["evidence"][0]["method"]["owner"] = "Preflight"
        self.assertEqual(
            warning(d1.interpret(a, b), "physical_unit_dependence")["status"],
            "unavailable",
        )
        b["evidence"][0]["qualifications"]["preflight_finding_scope"] = (
            "declared_identity_overlap"
        )
        self.assertEqual(
            warning(d1.interpret(a, b), "physical_unit_dependence")["value"],
            "conditional",
        )

    def test_raw_self_comparison_is_not_representation_replication(self):
        a, b = fixture(
            "representation",
            {"full_x_overlap": 1.0, "partition_ari": 1.0},
            admissible=True,
            matched_queries=True,
            matched_observations=True,
            representations=["raw"],
        )
        self.assertEqual(
            warning(d1.interpret(a, b), "preprocessing_dependent_organization")[
                "status"
            ],
            "unavailable",
        )

    def test_five_qualified_public_snapshots_and_unchanged_evidence(self):
        folder = ROOT / "docs/examples/structural-warnings"
        cases = json.loads(
            (folder / "scientific-cases.json").read_text(encoding="utf-8")
        )["cases"]
        self.assertEqual(len({c["dataset_id"] for c in cases}), 5)
        for case in cases:
            report, request = case["source_report"], case["request"]
            original = deepcopy((report, request))
            r = d1.interpret(report, request)
            w = warning(r, "experimental_factor_structure")
            self.assertEqual(w["value"], "conditional", case["dataset_id"])
            self.assertEqual(w["scientific_basis"]["n_dataset_identities"], 1)
            self.assertIn("Weak/negative cluster ARI", " ".join(w["limitations"]))
            self.assertEqual((report, request), original)
            d1.validate_annotation(report, r)
        report = json.loads((folder / "tablet.report.json").read_text())
        request = json.loads((folder / "tablet.request.json").read_text())
        annotation = json.loads((folder / "tablet.annotation.json").read_text())
        self.assertEqual(d1.interpret(report, request), annotation)

    def test_strong_continuous_tablet_batch_and_weak_cluster_agreement(self):
        a, b = fixture(
            "factor_geometry",
            {
                "eta_squared": [0.9793056177015933],
                "partition_ari": 0.038110815186653484,
                "n_levels": 31,
                "n_missing": 0,
            },
            factor="batch",
            role="metadata",
            role_reference="original keyed M",
            duplicated_from_target=False,
        )
        r = warning(d1.interpret(a, b), "experimental_factor_structure")
        self.assertEqual(r["value"], "conditional")
        self.assertIn(
            "independently of flat-cluster", r["observation"]["value"]["description"]
        )
        self.assertIn("cardinality", " ".join(r["required_information"]).lower())
        self.assertIn("causation", " ".join(r["limitations"]))
        self.assertIn("First establish", r["recommended_checks"][0]["description"])

    def test_animal_geometry_is_not_erased_by_nearly_zero_ari(self):
        a, b = fixture(
            "factor_geometry",
            {
                "eta_squared": [0.6002231023962316],
                "partition_ari_range": [-0.001, 0.003],
                "n_levels": 41,
            },
            factor="Cow_ID",
            role="metadata",
            role_reference="owner original_M",
            duplicated_from_target=False,
        )
        b["validation_intent"] = {
            "intended_use": "outside_context",
            "prediction_unit": "new_context",
            "factors": [
                {
                    "name": "Cow_ID",
                    "kind": "other",
                    "relevant_to_intent": True,
                    "excluded": False,
                    "evidence": "declared",
                    "reference": "owner M",
                    "relationship": "repeated acquisitions per cow",
                }
            ],
        }
        r = warning(d1.interpret(a, b), "experimental_factor_structure")
        self.assertEqual(r["value"], "conditional")
        self.assertIn("Cow_ID", r["recommended_checks"][0]["description"])
        self.assertIn("repeated", json.dumps(r).lower())
        self.assertNotIn("probability", r["observation"]["value"]["description"])

    def test_cartilage_neighbors_and_partition_changes_are_separate(self):
        a, b = fixture(
            "representation",
            {
                "full_x_overlap": 0.951171875,
                "pca_overlap": 0.94921875,
                "partition_ari": 0.178408,
                "cluster_counts": [2, 10],
            },
            admissible=True,
            matched_observations=True,
            matched_queries=True,
            representations=["raw", "smooth"],
            comparison_kind="representation",
        )
        r = warning(d1.interpret(a, b), "preprocessing_dependent_organization")
        self.assertEqual(r["value"], "observed")
        self.assertEqual(
            r["observation"]["value"]["measurements"][0]["values"]["cluster_counts"],
            [2, 10],
        )
        self.assertIn(
            "full-X neighbors separately", r["recommended_checks"][0]["description"]
        )
        self.assertIn("No family is selected", " ".join(r["limitations"]))

    def test_all_noise_is_computed_not_absence_of_continuous_structure(self):
        a, b = fixture(
            "representation",
            {
                "cluster_counts": [0],
                "noise_fractions": [1.0],
                "all_noise_settings": 1,
                "trivial_partition": True,
            },
            admissible=True,
            matched_observations=True,
            matched_queries=True,
            representations=["raw"],
            comparison_kind="single_partition",
        )
        r = warning(d1.interpret(a, b), "preprocessing_dependent_organization")
        self.assertEqual((r["status"], r["value"]), ("computed", "observed"))
        self.assertIn(
            "continuous structure is not ruled out",
            r["observation"]["value"]["description"],
        )
        a["e"] = {"trivial_partition": True}
        b["evidence"][0]["metrics"] = {"trivial_partition": "/e/trivial_partition"}
        r = warning(d1.interpret(a, b), "preprocessing_dependent_organization")
        self.assertEqual(r["status"], "unavailable")

    def test_missing_physical_metadata_is_unavailable_not_leakage(self):
        r = d1.interpret({}, {"source": source(), "evidence": []})
        self.assertEqual(
            warning(r, "physical_unit_dependence")["status"], "unavailable"
        )
        e = warning(r, "insufficient_experimental_context")
        self.assertEqual(e["value"], "observed")
        self.assertTrue(any("specimen" in t for t in e["required_information"]))
        self.assertIn("not evidence of a dangerous dataset", e["risk_hypothesis"])
        self.assertEqual(len(r["validation_intent"]["interpretations"]), 3)

    def test_declared_overlap_requires_new_unit_conditional_validation(self):
        a, b = fixture(
            "physical_units",
            {"n_overlapping_units": 2},
            dependency_basis="shared_specimen",
            evidence_quality="verified",
            unit_memberships_available=True,
        )
        b["validation_intent"] = {
            "intended_use": "known_context",
            "prediction_unit": "new_specimens",
            "split": {"family": "random_kfold"},
        }
        r = warning(d1.interpret(a, b), "physical_unit_dependence")
        self.assertEqual(r["value"], "observed")
        self.assertIn("whole-unit contrast", r["recommended_checks"][0]["description"])
        self.assertIn("new specimens", r["conditions"][0])
        b["evidence"][0]["qualifications"]["dependency_basis"] = "x_derived"
        self.assertEqual(
            warning(d1.interpret(a, b), "physical_unit_dependence")["status"],
            "unavailable",
        )

    def test_high_pc1_alone_never_infers_shortcut(self):
        a = {"pca": {"pc1_fraction": 0.99999}}
        r = d1.interpret(a, {"source": source(), "evidence": []})
        self.assertTrue(all(w["status"] == "unavailable" for w in r["warnings"][:4]))
        self.assertNotIn("leakage exists", json.dumps(r))

    def test_train_scoped_support_exceedance_is_evaluation_x_aware(self):
        a, b = fixture(
            "spectral_support",
            {"n_exceedances": 2, "n_evaluation": 10},
            fit_scope="training_only",
            evaluation_X_observed=True,
            reference_population_id="original-frozen-population",
            evaluation_population_id="observed-test-X",
        )
        r = warning(d1.interpret(a, b), "spectral_support_mismatch")
        self.assertEqual(r["value"], "conditional")
        self.assertIn("evaluation-X-aware", " ".join(r["limitations"]))
        a["e"]["n_exceedances"] = 0
        r = warning(d1.interpret(a, b), "spectral_support_mismatch")
        self.assertEqual(r["value"], "contradicted")
        self.assertIn("zero exceedance is not full", " ".join(r["limitations"]))
        b["evidence"][0]["qualifications"]["fit_scope"] = "full_x"
        self.assertEqual(
            warning(d1.interpret(a, b), "spectral_support_mismatch")["status"],
            "unavailable",
        )

    def test_negative_or_stable_evidence_does_not_force_warning(self):
        a, b = fixture(
            "representation",
            {"full_x_overlap": 1.0, "pca_overlap": 1.0, "partition_ari": 1.0},
            admissible=True,
            matched_observations=True,
            matched_queries=True,
            representations=["raw", "snv"],
            comparison_kind="representation",
        )
        self.assertEqual(
            warning(d1.interpret(a, b), "preprocessing_dependent_organization")[
                "value"
            ],
            "contradicted",
        )
        a, b = fixture(
            "factor_geometry",
            {"eta_squared": [0.0, 0.0], "n_levels": 2},
            factor="negative-control",
            role="metadata",
            role_reference="native fixture",
            duplicated_from_target=False,
        )
        self.assertEqual(
            warning(d1.interpret(a, b), "experimental_factor_structure")["value"],
            "contradicted",
        )

    def test_target_duplicated_in_metadata_is_excluded(self):
        a, b = fixture(
            "factor_geometry",
            {"eta_squared": [0.999], "n_levels": 2},
            factor="polymer_name",
            role="target",
            role_reference="owner Y mapping",
            duplicated_from_target=True,
        )
        r = warning(d1.interpret(a, b), "experimental_factor_structure")
        self.assertEqual(r["reason"], "TARGET_DERIVED_METADATA_EXCLUDED")
        self.assertIsNone(r["observation"]["value"])
        b["evidence"][0]["qualifications"].update(
            role="metadata", duplicated_from_target=False
        )
        a["e"]["primary_X_only_eligible"] = False
        with self.assertRaises(ValueError):
            d1.interpret(a, b)

    def test_source_query_admissibility_states_and_count_adversaries(self):
        a, b = fixture(
            "representation",
            {"full_x_overlap": 0.1},
            admissible=True,
            matched_queries=False,
            matched_observations=True,
            representations=["raw", "snv"],
        )
        self.assertEqual(
            warning(d1.interpret(a, b), "preprocessing_dependent_organization")[
                "status"
            ],
            "unavailable",
        )
        b["evidence"][0]["scope"]["population_id"] = "same-sized-other-population"
        with self.assertRaises(ValueError):
            d1.interpret(a, b)
        a, b = fixture("spectral_support", {"n_exceedances": 11, "n_evaluation": 10})
        with self.assertRaises(ValueError):
            d1.interpret(a, b)
        a, b = fixture("factor_geometry", {"eta_squared": float("nan")})
        with self.assertRaises(ValueError):
            d1.interpret(a, b)

    def test_schema_and_exact_report_compatibility_tampering(self):
        a, b = fixture("context", {"physical_units_known": False})
        original = deepcopy((a, b))
        r = d1.interpret(a, b)
        self.assertEqual((a, b), original)
        self.assertEqual(fingerprint(r), fingerprint(d1.interpret(a, b)))
        d1.validate_annotation(a, r)
        r["warnings"][0]["risk_hypothesis"] = "Leakage is proven."
        with self.assertRaises(ValueError):
            d1.validate_annotation(a, r)
        r = d1.interpret(a, b)
        r["warnings"][0]["severity"] = 0.9
        with self.assertRaises(ValidationError):
            d1.validate_annotation(a, r)
        self.assertEqual(
            (ROOT / "schemas/structural-warnings.v1.schema.json").read_bytes(),
            d1.SCHEMA_PATH.read_bytes(),
        )

    def test_cli_and_no_provider_import_or_new_fit_required(self):
        a, b = fixture("context", {"physical_units_known": False})
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "report.json").write_text(json.dumps(a))
            (p / "request.json").write_text(json.dumps(b))
            code = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "nirs4all_domains.structural_warnings",
                    str(p / "report.json"),
                    "--request",
                    str(p / "request.json"),
                    "--out",
                    str(p / "warning.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(code.returncode, 0, code.stderr)
            self.assertIn(
                "What should be checked next?",
                (p / "warning.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(json.loads((p / "report.json").read_text()), a)
            code = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    "from nirs4all_domains import structural_warnings; import sys; assert 'n4m' not in sys.modules and 'numpy' not in sys.modules",
                ],
                check=False,
            )
            self.assertEqual(code.returncode, 0)

    def test_native_synthetic_factor_fixture_without_any_pca_or_model_fit(self):
        from nirs4all_domains.unsupervised import factor_profile

        p = factor_profile(
            [-1] * 4,
            [[0.0], [0.0], [1.0], [1.0]],
            {"a": "A", "b": "A", "c": "B", "d": "B"},
            ["a", "b", "c", "d"],
            "native synthetic fixture",
        )
        self.assertEqual(p["status"], "computed")
        eta = p["value"]["pc_associations"][0]["value"]["eta_squared"]
        self.assertAlmostEqual(eta, 1.0, places=12)
        a, b = fixture(
            "factor_geometry",
            {"eta_squared": [eta], "n_levels": 2},
            factor="native-group",
            role="metadata",
            role_reference="native synthetic fixture",
            duplicated_from_target=False,
        )
        self.assertEqual(
            warning(d1.interpret(a, b), "experimental_factor_structure")["value"],
            "conditional",
        )


if __name__ == "__main__":
    unittest.main()
