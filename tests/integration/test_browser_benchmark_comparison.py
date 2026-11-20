"""Engineering receipt adversaries. These objects are not scientific execution evidence."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("benchmark_comparison", Path(__file__).resolve().parents[2] / "scripts/compare_browser_benchmarks.py")
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def rank_receipt(scoped, *, automatic=False):
    files = [{"name": comparison.FIXTURE["name"], "sha256": hashlib.sha256(comparison.FIXTURE["contents"].encode()).hexdigest()}]
    reviewed = {"schema_version": 1, "name": "dataset", "sources": [{"id": "train_x", "input": "X.csv", "partition": "train", "role": "mixed", "columns": {"features": ["1000"]}}]}
    content = comparison.digest({"files": files, "reviewed_spec": reviewed}, canonical=True) if scoped else comparison.digest(files)
    ids = ['["train_x","train",0]', '["train_x","train",1]', '["train_x","train",2]']
    request = {"schema_version": 1, "dataset_id": "dataset", "source_id": "train_x", "content_sha256": content,
               "observation_ids": ids, "axis": [1000], "axis_unit": "unknown", "group_ids": None}
    scope = {"dataset_id": "dataset", "source_id": "train_x", "content_sha256": content, "axis_unit": "unknown",
             "n_observations": 3, "n_bands": 1, "axis_sha256": comparison.digest([1000.0]), "observation_ids_sha256": comparison.digest(ids)}
    metrics = {"pca": {"status": "computed", "value": {"eigenvalues": [1]}}, "documentary_count": 3}
    numerical_input = {"schema_version": 1, "dataset_id": "dataset", "source_id": "train_x", "content_sha256": content,
                       "observation_ids": ids, "axis": [1000.0], "axis_unit": "unknown", "spectra": [[1.0], [2.0], [3.0]],
                       "group_ids": None, "prediction_intent": "unknown"}
    provenance = {"protocol": "domains.import_xy_m.v1", "roles_reviewed": not automatic, "files": files,
                  "original_source_ids": ["train_x"], "identity_independence": "unknown",
                  "file_content_sha256": comparison.digest(files), "reviewed_spec_sha256": comparison.digest(reviewed, canonical=True)} if scoped else None
    return {"wrapper_protocol": comparison.SCOPED_WRAPPER if scoped else comparison.SCIENTIFIC_PROTOCOL,
            "protocol_version": comparison.SCIENTIFIC_PROTOCOL, "metrics": metrics, "scope": scope,
            "input_sha256": comparison.digest(numerical_input),
            "evidence_sha256": comparison.digest(comparison.evidence_tree({"scope": scope, "metrics": metrics}), canonical=True),
            "source_binding": {"kind": "file_bindings_reviewed_spec.v1" if scoped else "file_bindings.v1",
                               "fixture": comparison.FIXTURE, "input": request, "import_provenance": provenance,
                               "reviewed_spec": reviewed if scoped else None},
            "operation": "train_structure" if scoped else "analyze",
            "population_manifest": [{"key": key, "partition": "train"} for key in ids] if scoped else None}


def receipt(*, scoped=False, before=False, automatic=False):
    names = {"io": "nirs4all_io_wasm_bg-test.wasm", "formats": "nirs4all_formats_wasm_bg-test.wasm",
             "domains": "nirs4all_domains_bg-test.wasm", "methods": "nirs4all_methods-test.wasm"}
    modules = ["io", "io", "domains", "methods"] if scoped else ["io", *(["formats"] if before else []), "domains", "methods"]
    rank = rank_receipt(scoped, automatic=automatic)
    scientific = {"protocol_version": comparison.SCIENTIFIC_PROTOCOL, "input_sha256": "1" * 64,
                  "scope": {"source": "public synthetic"}, "metrics": {"count": 48}, "interpretation": {"declaration_only": True}}
    scientific["evidence_sha256"] = comparison.digest(comparison.evidence_tree({"scope": scientific["scope"], "metrics": scientific["metrics"]}), canonical=True)
    live = {"input_sha256": scientific["input_sha256"], "evidence_sha256": scientific["evidence_sha256"], "metrics": scientific["metrics"], "scientific_report": scientific}
    operations = ["prepare_import", "assemble_import", "scoped"] if scoped else ["import", "analyze"]
    workers = [{"operation": operation, "input_bytes": len(comparison.FIXTURE["contents"].encode()) if i == 0 else 0,
                "transferred_bytes": 0 if before or i else len(comparison.FIXTURE["contents"].encode()),
                "sender_detached": not before and i == 0, "terminated": 1, "messages": [{"final": True, "ok": True}]} for i, operation in enumerate(operations)]
    sample = {"rank_one": rank, "import_route": "one_shot" if automatic else "reviewed" if scoped else "automatic",
              "live": live, "network": [{"asset": names[module], "body_bytes": 123} for module in modules], "workers": workers}
    for key in ["landing_ms", "import_to_visible_ms", "declaration_edit_ms", "main_thread_script_delta_ms", "layout_delta_ms", "main_thread_heap_sample_bytes", "offline_render_ms"]:
        sample[key] = 1
    for key in ["json_export", "html_export", "markdown_export"]:
        sample[key] = {"ms": 1, "bytes": 123}
    return {"protocol": "domains.technical_benchmark.v2", "success": True, "browser": "same", "node": "same",
            "assets": [{"file": name, "bytes": 123, "sha256": "0" * 64} for name in names.values()],
            "samples": [deepcopy(sample) for _ in range(3)], "measurement_limits": ["Workflow latency is not throughput."]}


class BenchmarkComparisonTests(unittest.TestCase):
    def provider_transition_receipts(self):
        before, after = receipt(before=True), receipt(scoped=True)
        for old, sample in [(True, item) for item in before["samples"]] + [(False, item) for item in after["samples"]]:
            provider = comparison.BASELINE_PROVIDER if old else comparison.CANDIDATE_PROVIDER
            rank = sample["rank_one"]
            rank["metrics"]["pca"]["value"]["backend_version"] = provider
            rank["evidence_sha256"] = comparison.digest(comparison.evidence_tree({"scope": rank["scope"], "metrics": rank["metrics"]}), canonical=True)
            live = sample["live"]
            report = live["scientific_report"]
            report["metrics"]["provider"] = {"backend_version": provider, "numeric_value": 0.125}
            report["engine_version"] = "0.1.0-alpha.17" if old else "0.2.0"
            report["capabilities"] = [{"reason": provider + "; bounded browser protocol"}]
            evidence = comparison.digest(comparison.evidence_tree({"scope": report["scope"], "metrics": report["metrics"]}), canonical=True)
            live["evidence_sha256"] = report["evidence_sha256"] = evidence
            report["interpretation"]["evidence_sha256"] = evidence
        return before, after

    def test_declared_provider_labels_change_hashes_without_changing_scientific_values(self):
        before, after = self.provider_transition_receipts()
        result = comparison.compare(before, after)
        self.assertTrue(result["scientific_values_equal"])
        self.assertFalse(result["synthetic_report_exactly_equal"])
        self.assertFalse(result["same_protocol_hashes_equal"]["synthetic"])
        self.assertTrue(result["declared_provider_metadata_transition"]["evidence_hashes_recomputed_and_verified"])

    def test_provider_transition_does_not_allow_changed_numbers_with_recomputed_hashes(self):
        before, after = self.provider_transition_receipts()
        for sample in after["samples"]:
            live = sample["live"]
            report = live["scientific_report"]
            report["metrics"]["provider"]["numeric_value"] += 1e-15
            evidence = comparison.digest(comparison.evidence_tree({"scope": report["scope"], "metrics": report["metrics"]}), canonical=True)
            live["evidence_sha256"] = report["evidence_sha256"] = report["interpretation"]["evidence_sha256"] = evidence
        with self.assertRaisesRegex(AssertionError, "Matched synthetic report"):
            comparison.compare(before, after)

    def test_undeclared_provider_or_engine_transition_is_refused(self):
        for field in ("provider", "engine"):
            with self.subTest(field=field):
                before, after = self.provider_transition_receipts()
                if field == "provider":
                    rank = after["samples"][0]["rank_one"]
                    rank["metrics"]["pca"]["value"]["backend_version"] = "1.5.1+abi.2.24.0"
                    rank["evidence_sha256"] = comparison.digest(comparison.evidence_tree({"scope": rank["scope"], "metrics": rank["metrics"]}), canonical=True)
                else:
                    after["samples"][0]["live"]["scientific_report"]["engine_version"] = "0.2.1"
                with self.assertRaises(AssertionError):
                    comparison.compare(before, after)

    def test_automatic_binding_keeps_unreviewed_roles_explicit_without_changing_numeric_gates(self):
        result = comparison.compare(receipt(before=True), receipt(scoped=True, automatic=True))
        self.assertTrue(result["scientific_values_equal"])
        self.assertFalse(result["scientific_values_and_hashes_equal"])
        self.assertFalse(result["declared_verified_binding_transition"]["after"]["roles_reviewed"])
        self.assertEqual(result["declared_verified_binding_transition"]["after"]["import_route"], "one_shot")

    def test_unreviewed_roles_without_the_recorded_automatic_route_are_refused(self):
        after = receipt(scoped=True, automatic=True)
        for sample in after["samples"]:
            sample["import_route"] = "reviewed"
        with self.assertRaisesRegex(AssertionError, "explicit one-shot import route"):
            comparison.compare(receipt(before=True), after)

    def test_automatic_import_cannot_fabricate_user_review(self):
        after = receipt(scoped=True, automatic=True)
        after["samples"][0]["rank_one"]["source_binding"]["import_provenance"]["roles_reviewed"] = True
        with self.assertRaisesRegex(AssertionError, "must not claim a user role review"):
            comparison.compare(receipt(before=True), after)

    def test_automatic_source_and_independence_provenance_tampering_is_refused(self):
        for field, value, reason in [("original_source_ids", ["other-source"], "source identities changed"),
                                     ("identity_independence", "verified", "cannot qualify physical independence")]:
            with self.subTest(field=field):
                after = receipt(scoped=True, automatic=True)
                after["samples"][0]["rank_one"]["source_binding"]["import_provenance"][field] = value
                with self.assertRaisesRegex(AssertionError, reason):
                    comparison.compare(receipt(before=True), after)

    def test_automatic_file_bytes_and_scientific_scope_tampering_remain_refused(self):
        after = receipt(scoped=True, automatic=True)
        after["samples"][0]["rank_one"]["source_binding"]["fixture"]["contents"] += "4\n"
        with self.assertRaisesRegex(AssertionError, "filename and bytes"):
            comparison.compare(receipt(before=True), after)
        after = receipt(scoped=True, automatic=True)
        after["samples"][0]["rank_one"]["scope"]["source_id"] = "other-source"
        with self.assertRaisesRegex(AssertionError, "Scientific scope disagrees"):
            comparison.compare(receipt(before=True), after)

    def test_declared_binding_transition_preserves_values_without_claiming_hash_equality(self):
        result = comparison.compare(receipt(before=True), receipt(scoped=True))
        self.assertEqual(result["protocol"], "domains.technical_comparison.v2")
        self.assertTrue(result["scientific_values_equal"])
        self.assertEqual(result["same_protocol_hashes_equal"], {"synthetic": True, "rank_one": False})
        self.assertFalse(result["scientific_values_and_hashes_equal"])
        self.assertTrue(result["declared_verified_binding_transition"]["verified"])
        self.assertEqual(result["csv_loaded_wasm_modules"], {"before": 4, "after": 4})

    def test_legacy_same_binding_keeps_the_original_exact_hash_and_lazy_load_gate(self):
        result = comparison.compare(receipt(before=True), receipt())
        self.assertTrue(result["scientific_values_and_hashes_equal"])
        self.assertEqual(result["csv_loaded_wasm_modules"], {"before": 4, "after": 3})

    def test_changed_metrics_are_refused_even_with_self_consistent_new_evidence_hash(self):
        for automatic in (False, True):
            with self.subTest(automatic=automatic):
                after = receipt(scoped=True, automatic=automatic)
                for sample in after["samples"]:
                    rank = sample["rank_one"]
                    rank["metrics"]["documentary_count"] = 4
                    rank["evidence_sha256"] = comparison.digest(comparison.evidence_tree({"scope": rank["scope"], "metrics": rank["metrics"]}), canonical=True)
                with self.assertRaisesRegex(AssertionError, "CSV scientific values changed"):
                    comparison.compare(receipt(before=True), after)

    def test_unexpected_input_hash_is_refused(self):
        after = receipt(scoped=True)
        after["samples"][0]["rank_one"]["input_sha256"] = "f" * 64
        with self.assertRaisesRegex(AssertionError, "Scientific input hash"):
            comparison.compare(receipt(before=True), after)

    def test_changed_declaration_with_stale_binding_is_refused(self):
        after = receipt(scoped=True)
        after["samples"][0]["rank_one"]["source_binding"]["reviewed_spec"]["name"] = "different"
        with self.assertRaisesRegex(AssertionError, "specification fingerprint"):
            comparison.compare(receipt(before=True), after)

    def test_test_row_hidden_in_training_manifest_is_refused(self):
        after = receipt(scoped=True)
        after["samples"][0]["rank_one"]["population_manifest"][0]["partition"] = "test"
        with self.assertRaisesRegex(AssertionError, "three declared training rows"):
            comparison.compare(receipt(before=True), after)

    def test_synthetic_hash_or_report_change_is_not_part_of_the_migration(self):
        after = receipt(scoped=True)
        after["samples"][0]["live"]["input_sha256"] = "2" * 64
        with self.assertRaisesRegex(AssertionError, "Matched synthetic report"):
            comparison.compare(receipt(before=True), after)

    def test_eager_formats_load_in_csv_workflow_is_refused(self):
        after = receipt(scoped=True)
        after["samples"][0]["network"].append({"asset": "nirs4all_formats_wasm_bg-test.wasm", "body_bytes": 123})
        with self.assertRaisesRegex(AssertionError, "per-stage WASM loads"):
            comparison.compare(receipt(before=True), after)


if __name__ == "__main__":
    unittest.main()
