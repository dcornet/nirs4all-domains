"""Verify alpha.10 public evidence with native metrics; no real-data acquisition."""
from collections import Counter
import json
import math
from pathlib import Path

from nirs4all_domains.bank import schema_check
from nirs4all_domains.dependence import score_oof
from nirs4all_domains.multifamily import paired_contrast
from nirs4all_domains.registry import reject_heavy_payload, verify_evidence, verify_storage
from nirs4all_domains.storage import digest, fingerprint


def main():
    root = Path("docs/benchmarks/alpha10")
    read = lambda p: json.loads(Path(p).read_text(encoding="utf-8"), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    record = read(root/"perten-evidence.json")
    schema_check(record, "qualification-evidence"); verify_evidence(record)
    manifest = read(root/"storage.json")
    schema_check(manifest, "storage-manifest"); verify_storage(manifest, root)
    frozen = read(root/"perten-evaluation.json")
    assert frozen["evaluation_id"] == fingerprint({k: v for k, v in frozen.items() if k != "evaluation_id"})
    assert frozen["config_sha256"] == digest("configs/pilots/multifamily-alpha10-v1.json")
    assert frozen["expected_behavior_sha256"] == digest("docs/ALPHA10_MULTIFAMILY_PROTOCOL.md")
    old = read("docs/benchmarks/alpha9/perten-evidence.json")
    old_designs = {d["design_id"]: d["value"] for d in old["scientific"]["deep"]["experiments"] if d["status"] == "computed"}
    model_records = [read(p) for p in root.glob("*_v1.json")]
    assert len(model_records) == 4
    summary = read(root/"perten-summary.json")
    for model in model_records:
        schema_check(model, "multifamily-result")
        assert model["evaluation_id"] == frozen["evaluation_id"]
        assert model["specification"] in frozen["specifications"]
        for design, result in model["designs"].items():
            assert result["status"] == "computed", result["reason"]
            value = result["value"]; oof = value["oof"]
            assert len(oof) == 359 and len({r["physical_sample_id"] for r in oof}) == 359
            original = {r["physical_sample_id"]: r for r in old_designs[design]["oof"]}
            assert set(original) == {r["physical_sample_id"] for r in oof}
            assert all((r["y"], r["component_id"], r["fold_id"]) == (original[r["physical_sample_id"]]["y"], original[r["physical_sample_id"]]["component_id"], original[r["physical_sample_id"]]["fold_id"]) for r in oof)
            actual = score_oof(oof, "prediction")
            for metric, number in actual["value"].items():
                assert math.isclose(number["value"], value["scores"]["value"][metric]["value"], abs_tol=1e-10, rel_tol=1e-10)
            for trace in value["lineage"]:
                inner = frozen["inner_designs"][design][trace["fold_id"]]
                assert trace["inner_fold_set_sha256"] == fingerprint(inner)
                assert trace["native_fit_lineage_verified"]
        data = model["designs"]
        contrast = paired_contrast([data["holdout:cereal_type"]["value"]["oof"], data["reference:17"]["value"]["oof"]], [1, -1])
        expected = summary["degradations"][model["specification"]["id"]]["holdout:cereal_type"]
        assert contrast["paired_draw_membership_sha256"] == expected["paired_draw_membership_sha256"]
        assert math.isclose(contrast["estimate"]["value"], expected["estimate"]["value"], abs_tol=1e-10, rel_tol=1e-10)
    size = read(root/"size-control-evaluation.json")
    assert size["evaluation_id"] == fingerprint({k: v for k, v in size.items() if k != "evaluation_id"})
    assert size["expected_behavior_sha256"] == digest("docs/ALPHA10_SIZE_CONTROL_PROTOCOL.md")
    eval_ids = [s for c in size["cells"] for s in c["validation_sample_ids"]]
    assert len(eval_ids) == len(set(eval_ids)) == 359
    for cell in size["cells"]:
        stress, = [f for f in frozen["outer_designs"]["holdout:cereal_type"]["folds"] if f["fold_id"] == cell["stress_fold_id"]]
        ref, = [f for f in frozen["outer_designs"]["reference:17"]["folds"] if f["fold_id"] == cell["reference_fold_id"]]
        assert len(cell["train_sample_ids"]) == len(stress["train_sample_ids"])
        assert set(cell["train_sample_ids"]) <= set(ref["train_sample_ids"])
        assert not set(cell["train_sample_ids"]) & set(cell["validation_sample_ids"])
    size_results = read(root/"size-control-results.json")
    assert len(size_results["models"]) == 6
    for result in size_results["models"].values():
        assert len(result["oof"]) == 359
        for metric, number in score_oof(result["oof"], "prediction")["value"].items():
            assert math.isclose(number["value"], result["scores"]["value"][metric]["value"], abs_tol=1e-10, rel_tol=1e-10)
    cartilage = read(root/"cartilage-admission.json")
    ids = cartilage["original_identity_evidence"]["value"]
    assert (ids["locations"], ids["acquisitions"], len(ids["joint_counts"]), len(ids["region_counts"])) == (869, 2605, 5, 44)
    assert cartilage["predictive_qualification"]["status"] == "not_identifiable" and cartilage["no_predictive_fit"]
    assert read(root/"paired-admission.json")["admitted_tasks"] == 0
    records = {r["task_id"]: r for r in (record, read("docs/benchmarks/alpha8/ecosis-evidence.json"))}
    for path in root.glob("*suite.json"):
        suite = read(path); schema_check(suite, "benchmark-suite")
        assert suite["suite_id"] == fingerprint({k: v for k, v in suite.items() if k != "suite_id"})
        for member in suite["tasks"]:
            assert member["evidence_sha256"] == fingerprint(records[member["task_id"]])
        if suite["purpose"] in ("candidate_low_structural_dependence", "transfer_challenge"): assert not suite["tasks"]
    def inspect(value):
        if isinstance(value, dict):
            if "test_target_accessed" in value: assert value["test_target_accessed"] is False
            if set(value) >= {"status", "reason", "value"}:
                if value["status"] == "computed": assert value["reason"] is None and value["value"] is not None
                else: assert value["reason"] and value["value"] is None
            for child in value.values(): inspect(child)
        elif isinstance(value, list):
            for child in value: inspect(child)
    for path in root.glob("*.json"):
        value = read(path); reject_heavy_payload(value); inspect(value)
    protected = read("docs/audit/alpha10-frozen-output-hashes.json")
    # Real pilot files are local-only; every portable baseline is checked in CI.
    checked = 0
    for path, expected in protected.items():
        if Path(path).exists(): assert digest(path) == expected; checked += 1
    print(f"alpha.10: four new pipelines, matched native metrics, exact-size 359-ID controls, source admission, suites, finite states; {checked} protected artifacts verified")


if __name__ == "__main__": main()
