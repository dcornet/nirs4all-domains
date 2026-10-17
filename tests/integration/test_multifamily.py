"""Alpha.10 gates: upstream native/optional FastAOM fitting, identity transport."""
import copy
import json
import math
import os
from pathlib import Path
import unittest

from nirs4all_domains.dependence import development_rows
from nirs4all_domains.multifamily import freeze_evaluation, compare_design, inner_fit, paired_contrast, validate_spec
from nirs4all_domains.original_keys import cartilage_keys, dependency_closure, keyed_equivalence, full_population_cost
from nirs4all_domains.predictive import group_folds
from nirs4all_domains.storage import fingerprint

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT/"configs/pilots/multifamily-alpha10-v1.json").read_text())


def specimen(key="sample_01_a_01", joint=1, area="A", point=1, donor=None):
    return {"sample_id": key, "joint_id": joint, "area_of_interest_id": area, "measurement_point_id": point,
            "donor_id": donor, "reference_key": key+":thickness", "acquisition_keys": [key+":s1", key+":s2", key+":s3"]}


def task():
    value = json.loads((ROOT/"tests/fixtures/dependence/mixed.json").read_text())
    value.setdefault("provenance", {})["reference_xy_blocked"] = "false"
    for i, row in enumerate(value["observations"]):
        row["metadata"]["validation_component_id"] = row["independence_group"]
        row["x"] = [math.sin(i*.7+j*.13)+.03*j*i+math.cos(i*.3-j*.7) for j in range(32)]
    return value


class OriginalIdentityTests(unittest.TestCase):
    def test_exact_size_matching_preserves_components_without_outcomes_or_spectra(self):
        from nirs4all_domains.size_match import exact_training_subset
        rows = [{"physical_sample_id": str(i), "independence_group": str(i//2)} for i in range(12)]
        allowed = [r["physical_sample_id"] for r in rows]
        selected = exact_training_subset(rows, allowed, 6)
        self.assertEqual(len(selected), 6)
        self.assertTrue(all((str(i) in selected) == (str(i+1) in selected) for i in range(0, 12, 2)))
        self.assertIsNone(exact_training_subset(rows, allowed, 7))
        with self.assertRaisesRegex(ValueError, "SPLITS_DEPENDENCY"):
            exact_training_subset(rows, allowed[1:], 6)
    def test_cartilage_explicit_keys_and_three_spectra_one_location(self):
        rows = cartilage_keys([specimen()])
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]["acquisition_keys"]), 3)
        self.assertEqual(rows[0]["region_id"], "joint:1:AI:A")

    def test_missing_and_contradictory_original_keys(self):
        for change in ({"sample_id": ""}, {"joint_id": 2}, {"measurement_point_id": 2}):
            row = specimen(); row.update(change)
            with self.assertRaises(ValueError): cartilage_keys([row])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ORIGINAL_LOCATION"):
            cartilage_keys([specimen(), specimen()])

    def test_duplicate_acquisitions_do_not_create_physical_units(self):
        a, b = specimen(), specimen("sample_01_a_02", point=2)
        b["acquisition_keys"][0] = a["acquisition_keys"][0]
        with self.assertRaisesRegex(ValueError, "REUSED_ACROSS"):
            cartilage_keys([a, b])

    def test_region_joint_and_donor_transitive_closure(self):
        rows = cartilage_keys([specimen(donor="animal-A"), specimen("sample_01_b_02", area="B", point=2, donor="animal-A"),
                               specimen("sample_02_a_01", joint=2, donor="animal-A"), specimen("sample_03_a_01", joint=3, donor="animal-B")])
        result = dependency_closure(rows)
        self.assertEqual(sorted(map(len, result["declared_components"])), [1, 3])

    def test_shared_reference_links_distinct_joints(self):
        a, b = specimen(donor="A"), specimen("sample_02_a_01", joint=2, donor="B")
        b["reference_key"] = a["reference_key"]
        self.assertEqual(dependency_closure(cartilage_keys([a, b]))["n_declared_components"], 1)

    def test_missing_donor_does_not_certify_independence(self):
        result = dependency_closure(cartilage_keys([specimen(), specimen("sample_02_a_01", joint=2)]))
        self.assertEqual(result["n_declared_components"], 2)
        self.assertEqual(result["biological_independence"]["status"], "not_identifiable")
        self.assertIsNone(result["biological_independence"]["value"])

    def test_original_canonical_keyed_permutation_and_no_positional_join(self):
        a = [{"key": "a", "y": 2}, {"key": "b", "y": 5}]
        self.assertEqual(keyed_equivalence(a, a[::-1], key="key", columns=["y"])["n"], 2)
        with self.assertRaisesRegex(ValueError, "POSITIONAL_JOIN"):
            keyed_equivalence(a, [{"y": 2}, {"y": 5}], key="key", columns=["y"])
        with self.assertRaisesRegex(ValueError, "CONTRADICTION"):
            keyed_equivalence(a, [{"key": "a", "y": 5}, {"key": "b", "y": 2}], key="key", columns=["y"])

    def test_full_population_exceeds_old_guard_without_truncation(self):
        cost = full_population_cost(869, 2605, 812)
        self.assertEqual(cost["n_locations"], 869)
        self.assertEqual(cost["native_fit_count"], 50)
        self.assertEqual(cost["mean_f64_bytes"], 5645024)
        self.assertIsNone(cost["predictive_execution"]["value"])


class PairedContrastTests(unittest.TestCase):
    def test_compact_artifact_size_is_metadata_and_payload_is_rejected(self):
        from nirs4all_domains.registry import reject_heavy_payload
        reject_heavy_payload({"artifact_bytes": 1234})
        for value in ("serialized-model", [1, 2], -1, True):
            with self.assertRaises(ValueError): reject_heavy_payload({"artifact_bytes": value})
    def vectors(self, n=10):
        base = [{"physical_sample_id": str(i), "component_id": "g"+str(i), "y": float(i)} for i in range(n)]
        return [[{**r, "prediction": r["y"]+delta} for r in base] for delta in (3, 1, 2, 1)]

    def test_known_estimator_by_split_interaction_and_paired_draws(self):
        result = paired_contrast(self.vectors(), [1, -1, -1, 1])
        self.assertAlmostEqual(result["estimate"]["value"], 1, delta=1e-10)
        self.assertEqual(result["interval_95"]["value"], [1., 1.])
        reverse = [v[::-1] for v in self.vectors()]
        self.assertEqual(result, paired_contrast(reverse, [1, -1, -1, 1]))

    def test_few_components_have_no_precision_certificate(self):
        result = paired_contrast(self.vectors(2), [1, -1, -1, 1])
        self.assertIsNone(result["interval_95"]["value"])
        self.assertEqual(result["estimate"]["value"], 1)

    def test_matching_requires_reference_component_and_unique_physical_ids(self):
        for field, change in (("y", 999), ("component_id", "other"), ("physical_sample_id", "other")):
            values = self.vectors(); values[1][0][field] = change
            with self.assertRaises(ValueError): paired_contrast(values, [1, -1, -1, 1])
        values = self.vectors(); values[0].append(values[0][0])
        with self.assertRaises(ValueError): paired_contrast(values, [1, -1, -1, 1])


class NativeMultifamilyTests(unittest.TestCase):
    def setUp(self):
        from threadpoolctl import threadpool_limits
        self.threads = threadpool_limits(limits=1)
        self.addCleanup(self.threads.restore_original_limits)
        self.task = task(); self.rows = development_rows(self.task)
        self.folds = group_folds(self.rows, 4, 17, "outer")
        self.library = os.environ["N4DOMAINS_METHODS_LIBRARY"]

    def test_identical_folds_fixed_versus_tuned_ridge_distinction(self):
        tuned = CONFIG["models"][0]; fixed = copy.deepcopy(tuned)
        fixed["id"] = "ridge_fixed_control"; fixed["grid"] = {"alpha": [1.]}
        a = freeze_evaluation(self.task, {"reference": self.folds}, [tuned], "parent")
        b = freeze_evaluation(self.task, {"reference": self.folds}, [fixed], "parent")
        self.assertNotEqual(a["evaluation_id"], b["evaluation_id"])
        self.assertEqual(a["inner_designs"], b["inner_designs"])
        fit, trace = inner_fit(self.rows, group_folds(self.rows, 3, 17, "inner"), tuned, self.library)
        self.assertEqual(trace["candidate_count"], 5)
        self.assertIn(trace["selected"]["alpha"], tuned["grid"]["alpha"])

    def test_native_provider_full_869_by_812_without_software_truncation(self):
        from n4m.roles import Ridge
        # Dimension-matched controlled data only, never Cartilage references.
        # Equal columns make a hand-checkable centered Ridge penalty case.
        # Expected: all 869 predictions, finite, with the regularized slope.
        t = [(i-434)/100 for i in range(869)]
        x = [[v]*812 for v in t]
        y = [[4+3*v] for v in t]
        model = Ridge(alpha=1., center_x=True, center_y=True, scale_x=False)
        model.fit(x, y)
        prediction = model.predict(x).reshape(-1).tolist()
        self.assertEqual(len(prediction), 869)
        slope = 3*(812*sum(v*v for v in t))/(1+812*sum(v*v for v in t))
        for i in (0, 434, 868):
            self.assertAlmostEqual(prediction[i], 4+slope*t[i], delta=1e-8)

    def test_fold_local_native_snv_serialized_chain_prediction(self):
        import numpy as np
        spec = CONFIG["models"][1]
        fitted, trace = inner_fit(self.rows, group_folds(self.rows, 3, 17, "inner"), spec, self.library)
        self.assertEqual(len(trace["artifact_sha256"]), 2)
        first = fitted.predict([self.rows[0]["x"]]).reshape(-1)
        other = [self.rows[0]["x"], [1e8*x for x in self.rows[1]["x"]]]
        self.assertTrue(np.allclose(first, fitted.predict(other).reshape(-1)[:1], atol=1e-10, rtol=0))

    def test_no_retained_x_y_metadata_effect_and_frozen_content_guard(self):
        spec = CONFIG["models"][0]
        frozen = freeze_evaluation(self.task, {"reference": self.folds}, [spec], "parent")
        first = compare_design(self.task, frozen, "reference", spec, self.library)
        self.assertEqual(first["status"], "computed", first)
        changed = copy.deepcopy(self.task)
        for row in changed["observations"]:
            if row["partition"] == "test": row["x"] = [1e12]*32; row["y"] = 1e15; row["metadata"] = {}
        second = compare_design(changed, frozen, "reference", spec, self.library)
        self.assertEqual(first["value"]["oof"], second["value"]["oof"])
        changed = copy.deepcopy(self.task)
        next(r for r in changed["observations"] if r["partition"] == "train")["y"] += 1
        with self.assertRaisesRegex(ValueError, "CONTENT_OR_SPECIFICATION"):
            compare_design(changed, frozen, "reference", spec, self.library)
        frozen["protocol_version"] = "changed"
        with self.assertRaisesRegex(ValueError, "DIGEST_MISMATCH"):
            compare_design(self.task, frozen, "reference", spec, self.library)

    def test_failed_native_candidate_preserves_full_declared_grid(self):
        spec = copy.deepcopy(CONFIG["models"][1]); spec["grid"]["n_components"] = [1, 100]
        frozen = freeze_evaluation(self.task, {"reference": self.folds}, [spec], "parent")
        result = compare_design(self.task, frozen, "reference", spec, self.library)
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["value"])
        self.assertEqual(spec["grid"]["n_components"], [1, 100])
        import jsonschema
        schema = json.loads((ROOT/"schemas/multifamily-result.v1.schema.json").read_text())
        jsonschema.validate(result, schema["properties"]["designs"]["additionalProperties"])

    def test_suite_is_frozen_before_scores_and_cannot_certify_low_dependence(self):
        frozen = freeze_evaluation(self.task, {"reference": self.folds}, CONFIG["models"], "parent")
        self.assertNotIn("scores", frozen)
        self.assertIsNone(frozen["low_dependence"]["value"])
        changed = copy.deepcopy(CONFIG["models"][0]); changed["grid"]["alpha"] = [2.]
        with self.assertRaisesRegex(ValueError, "CONTENT_OR_SPECIFICATION"):
            compare_design(self.task, frozen, "reference", changed, self.library)

    def test_random_internal_cv_and_multi_lambda_are_rejected(self):
        for change in ({"cv_n_components": True}, {"lambdas": [.01, 1.]}, {"max_chain_depth": 4}):
            spec = copy.deepcopy(CONFIG["models"][2]); spec["config"].update(change)
            with self.assertRaisesRegex(ValueError, "INTERNAL_SELECTION"):
                validate_spec(spec)


class FastAOMTests(unittest.TestCase):
    setUp = NativeMultifamilyTests.setUp
    def test_upstream_adaptive_grouped_inner_fit_and_validation_label_adversary(self):
        import numpy as np
        spec = copy.deepcopy(CONFIG["models"][2]); spec["grid"] = {"n_components": [1]}
        folds = group_folds(self.rows, 3, 17, "inner")
        model, first = inner_fit(self.rows, folds, spec, self.library)
        changed = copy.deepcopy(self.rows)
        ids = set(folds["folds"][0]["validation_sample_ids"])
        for row in changed:
            if row["physical_sample_id"] in ids: row["y"] += 1e3
        _, second = inner_fit(changed, folds, spec, self.library)
        select = lambda trace: [e["artifact_sha256"] for e in trace["events"] if e["phase"] == "FIT_CV" and e["fold_id"] == folds["folds"][0]["fold_id"]]
        self.assertEqual(select(first), select(second))
        changed_x = copy.deepcopy(self.rows)
        for row in changed_x:
            if row["physical_sample_id"] in ids: row["x"] = [v*1e6 for v in row["x"]]
        _, third = inner_fit(changed_x, folds, spec, self.library)
        self.assertEqual(select(first), select(third))
        self.assertTrue(all(e["native_fit_lineage_verified"] for e in first["events"]))
        self.assertTrue(all(e["diagnostics"]["n_finalists"] <= 8 for e in first["events"]))
        x = [r["x"] for r in self.rows[:2]]
        a = model.predict(x[:1]); b = model.predict([x[0], [v*1e9 for v in x[1]]])[:1]
        self.assertTrue(np.allclose(a, b, atol=1e-9, rtol=1e-9))
        repeat, _ = inner_fit(self.rows, folds, spec, self.library)
        self.assertTrue(np.allclose(a, repeat.predict(x[:1]), atol=1e-9, rtol=1e-9))

    def test_retained_test_has_no_effect_on_adaptive_selection_or_predictions(self):
        spec = copy.deepcopy(CONFIG["models"][2]); spec["grid"] = {"n_components": [1]}
        frozen = freeze_evaluation(self.task, {"reference": self.folds}, [spec], "parent")
        first = compare_design(self.task, frozen, "reference", spec, self.library)
        changed = copy.deepcopy(self.task)
        for row in changed["observations"]:
            if row["partition"] == "test": row["x"] = None; row["y"] = "forbidden"; row["metadata"] = {}
        second = compare_design(changed, frozen, "reference", spec, self.library)
        self.assertEqual(first["status"], "computed", first)
        self.assertEqual(first["value"]["oof"], second["value"]["oof"])

    def test_upstream_sparse_mkr_group_safe_fit_and_replay(self):
        spec = CONFIG["models"][3]
        fitted, trace = inner_fit(self.rows, group_folds(self.rows, 3, 17, "inner"), spec, self.library)
        self.assertEqual(len(trace["events"]), 4)
        self.assertTrue(all(math.isfinite(float(x)) for x in fitted.predict([r["x"] for r in self.rows[:3]])))


if __name__ == "__main__": unittest.main()
