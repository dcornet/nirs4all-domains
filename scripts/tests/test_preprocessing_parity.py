"""Small adversaries for qualification rules; no real artifacts or provider fitting."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_preprocessing_parity as parity


def unavailable(reason="NOT_REQUESTED"):
    return {"status": "unavailable", "reason": reason, "value": None}


def computed(value):
    return {"status": "computed", "reason": None, "value": value}


def binding_case():
    dataset = {"dataset_id": "synthetic", "source_id": "public", "content_version": "1", "content_sha256": "a"*64}
    keys = ["a", "b", "c"]
    matrix, axis = [[1., 2.], [3., 4.], [5., 6.]], [1000., 1100.]
    factor = {"name": "instrument", "role": "instrument", "kind": "categorical", "unit": None, "origin": "M", "derived_from_target": False, "evidence": "declared", "row_keys": keys, "values": ["one", "one", "two"]}
    plan = {"bank_id": "test-v1", "representations": [{"id": "raw", "family": "raw", "steps": []}]}
    request = {"schema_version": 1, "protocol_version": "domains.browser_preprocessing_sensitivity.v1", "dataset": dataset, "manifest": [{"key": key, "partition": "train"} for key in keys], "plan": plan, "population": "train", "stage": "reference_only", "reference_keys": keys, "query_keys": [], "x": {"row_keys": keys, "matrix": matrix, "axis": axis, "axis_unit": "nm"}, "factors": [factor], "dependencies": [], "frozen_reference": None}
    plan_hash = parity.fingerprint(plan)
    reference = {"dataset": dataset, "manifest": request["manifest"], "reference_keys": keys, "axis": axis, "axis_unit": "nm", "matrix": matrix, "factors": [factor], "dependencies": []}
    reference_hash = parity.fingerprint(reference)
    suffix = "::f43::"+plan_hash+"::raw"
    source = {"dataset_id": "synthetic"+suffix, "source_id": "public"+suffix, "content_version": "derived-reference-v1", "content_sha256": parity.fingerprint({"parent": dataset["content_sha256"], "reference_matrix": matrix, "axis": axis, "plan": plan_hash})}
    result = {"schema_version": 1, "protocol_version": "domains.browser_preprocessing_sensitivity_result.v1", "status": "computed", "reason": None, "dataset": dataset, "plan": plan, "plan_sha256": plan_hash, "reference_input_sha256": reference_hash, "input_sha256": parity.fingerprint({"reference_input_sha256": reference_hash, "plan_sha256": plan_hash, "stage": "reference_only", "query_keys": [], "query_matrix": [], "dependencies": []}), "stage": "reference_only", "population": "train", "representations": [{"id": "raw", "family": "raw", "steps": [], "status": "computed", "reason": None, "value": {"source": source, "axis": axis, "original_axis_sha256": parity.fingerprint(axis), "reference_matrix_sha256": parity.fingerprint(matrix), "query_matrix_sha256": None, "transformations": [], "structure": unavailable(), "factors": [unavailable()], "support": unavailable()}}], "receipt": {"provider": parity.VERSION, "reference_keys": keys, "query_keys": [], "y_accessed": False, "x_predict_accessed": False, "test_x_accessed": False, "frozen_reference_sha256": None, "provider_calls": []}}
    result["evidence_sha256"] = parity.fingerprint(result)
    return {"id": "tiny", "request": request, "result": result}


def score_pair(flip=False, wrong_statistic=False):
    scores = [[-1., 0.], [0., 1.], [1., -1.]]
    estimate = -0.25 if flip else 0.25
    factor = computed({"factors": [{"factor_id": "temperature", "components": [{"component": 1, "n_used": 3, "descriptive": computed({"measure": "pearson_r", "estimate": 0.25, "owner_output": {"coefficient": 0.25, "p_value": None, "n_permutations_executed": 0, "n_at_least_observed": 0}})}]}]})
    rep = {"id": "raw", "status": "computed", "value": {"structure": computed({"report": {"metrics": {"pca": computed({"scores": scores, "eigenvalues": [1., 2.], "n_components_resolved": 2}), "density": unavailable()}}, "scoped": None}), "factors": [factor], "support": unavailable(), "comparisons": {"clusters": unavailable()}}}
    left = {"representations": [rep]}
    right = copy.deepcopy(left)
    if flip:
        for row in right["representations"][0]["value"]["structure"]["value"]["report"]["metrics"]["pca"]["value"]["scores"]:
            row[0] *= -1
    value = right["representations"][0]["value"]["factors"][0]["value"]["factors"][0]["components"][0]["descriptive"]["value"]
    value["estimate"] = value["owner_output"]["coefficient"] = estimate + (0.1 if wrong_statistic else 0)
    return left, right


class ParityAdversaries(unittest.TestCase):
    def test_gram_change_and_malformed_rank_are_refused(self):
        for left, right, energies in [([[1., 0.], [0., 1.]], [[2., 0.], [0., 1.]], [1., 1.]), ([[1., 0.]], [[1.]], [1., 1.]), ([], [], []), ([[1., 0.]], [[1., 0.]], [1.])]:
            with self.subTest(left=left), self.assertRaises(AssertionError):
                parity.geometry(left, right, energies, "adversary", {"numeric": 0})

    def test_signed_basis_flip_is_accepted_but_factor_alignment_is_strict(self):
        for wrong in (False, True):
            left, right = score_pair(flip=True, wrong_statistic=wrong)
            a, b = parity.prepare_pair(left, right, {"reference_keys": ["a", "b", "c"]}, "signed", {"numeric": 0}, [])
            if wrong:
                with self.assertRaises(AssertionError):
                    parity.compare(a, b, "signed", {"numeric": 0}, lambda *_: False)
            else:
                parity.compare(a, b, "signed", {"numeric": 0}, lambda *_: False)

    def test_status_and_owner_estimate_mismatches_remain_failures(self):
        left, right = score_pair(wrong_statistic=True)
        a, b = parity.prepare_pair(left, right, {"reference_keys": ["a", "b", "c"]}, "statistic", {"numeric": 0}, [])
        with self.assertRaises(AssertionError):
            parity.compare(a, b, "statistic", {"numeric": 0}, lambda *_: False)
        with self.assertRaises(AssertionError):
            parity.compare(unavailable("OWNER_UNDEFINED"), computed(0.), "status", {"numeric": 0}, lambda *_: False)

    def test_source_keys_metadata_and_protocol_mutations_are_rejected(self):
        case = binding_case()
        parity.verify_result(case, {}, "control")
        mutations = [lambda c: c["request"]["dataset"].update(content_sha256="b"*64), lambda c: c["request"].update(reference_keys=["c", "b", "a"]), lambda c: c["request"]["factors"][0]["values"].__setitem__(0, "changed"), lambda c: c["request"].update(protocol_version="wrong"), lambda c: c["result"].update(protocol_version="wrong")]
        for mutate in mutations:
            changed = copy.deepcopy(case)
            mutate(changed)
            # A self-consistent edited envelope must not bypass the original bindings.
            changed["result"].pop("evidence_sha256")
            changed["result"]["evidence_sha256"] = parity.fingerprint(changed["result"])
            with self.subTest(mutate=mutate), self.assertRaises(AssertionError):
                parity.verify_result(changed, {}, "tampered")

    def test_label_permutation_is_exact_identity_partition_equivalence_only(self):
        a = computed({"labels": [0, 0, 1, -1]})
        b = computed({"labels": [7, 7, 3, -1]})
        self.assertEqual(parity.align_density(a, b, ["a", "b", "c", "d"], "labels"), {7: 0, 3: 1})
        with self.assertRaises(AssertionError):
            parity.align_density(a, computed({"labels": [7, 3, 3, -1]}), ["a", "b", "c", "d"], "changed")


if __name__ == "__main__":
    unittest.main()
