"""Freeze and execute the separate complete-population exact-size control."""
import argparse
import copy
import json
from pathlib import Path

from nirs4all_domains.dependence import development_rows, score_oof, state
from nirs4all_domains.multifamily import inner_fit, paired_contrast
from nirs4all_domains.predictive import group_folds
from nirs4all_domains.size_match import exact_training_subset
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint
from run_alpha10_multifamily import inputs, immutable


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run"))
    args = parser.parse_args()
    old, input_path, task = inputs()
    rows = development_rows(task)
    by_id = {r["physical_sample_id"]: r for r in rows}
    public, root = Path("docs/benchmarks/alpha10"), Path("results/alpha10-multifamily")
    parent = json.loads((public/"perten-evaluation.json").read_text())
    freeze_path = public/"size-control-evaluation.json"
    if args.command == "freeze":
        cells = []
        for stress in parent["outer_designs"]["holdout:cereal_type"]["folds"]:
            for ref in parent["outer_designs"]["reference:17"]["folds"]:
                scope = "size:"+stress["fold_id"]+":"+ref["fold_id"]
                selected = exact_training_subset(rows, ref["train_sample_ids"], len(stress["train_sample_ids"]), scope=scope)
                if selected is None: raise ValueError("EXACT_COMPONENT_SIZE_MATCH_UNAVAILABLE")
                valid = sorted(set(stress["validation_sample_ids"]) & set(ref["validation_sample_ids"]))
                if set(selected) & set(valid): raise ValueError("SIZE_MATCH_LEAKAGE")
                train = [by_id[s] for s in selected]
                cells.append({"cell_id": scope, "reference_fold_id": ref["fold_id"], "stress_fold_id": stress["fold_id"],
                              "train_sample_ids": selected, "validation_sample_ids": valid,
                              "inner_fold_set": group_folds(train, 3, 17, scope+":inner"),
                              "n_training_contexts": len({r["independence_group"] for r in train})})
        evaluated = [s for c in cells for s in c["validation_sample_ids"]]
        if sorted(evaluated) != sorted(by_id): raise ValueError("COMPLETE_ORIGINAL_POPULATION_REQUIRED")
        specs = copy.deepcopy(parent["specifications"])
        specs.extend([{"id": "pls_alpha9", "engine": "methods", "method": "models.pls.pls_regression", "preprocessing": "raw", "grid": {"n_components": [1, 2, 3]}},
                      {"id": "ridge_fixed_alpha9", "engine": "methods", "method": "models.regularized.ridge", "preprocessing": "raw", "grid": {"alpha": [1.]}}])
        frozen = {"protocol_version": "domains.size_match.v0.1", "parent_evaluation_id": parent["evaluation_id"],
                  "development_input_sha256": fingerprint(rows), "cells": cells, "specifications": specs,
                  "expected_behavior_sha256": digest("docs/ALPHA10_SIZE_CONTROL_PROTOCOL.md"), "test_target_accessed": False}
        frozen["evaluation_id"] = fingerprint(frozen)
        immutable(freeze_path, frozen)
        print(json.dumps({"frozen": frozen["evaluation_id"], "cells": len(cells), "evaluation_ids": len(evaluated)}))
        return
    from n4m._ffi import library_path
    from threadpoolctl import threadpool_limits
    frozen = json.loads(freeze_path.read_text())
    if frozen["development_input_sha256"] != fingerprint(rows) or frozen["evaluation_id"] != fingerprint({k: v for k, v in frozen.items() if k != "evaluation_id"}):
        raise ValueError("FROZEN_SIZE_CONTROL_CONTENT_CHANGED")
    budget_id = json.loads((public/"ridge_tuned_v1.json").read_text())["task_id"]
    contract = {"task": {"task_id": budget_id}, "execution": {"protocol": "domains.size_match.v0.1", "evaluation_id": frozen["evaluation_id"],
        "runner_sha256": digest(__file__), "subset_adapter_sha256": digest("bridges/python/nirs4all_domains/size_match.py"),
        "controller_sha256": digest("bridges/python/nirs4all_domains/multifamily.py"), "library_sha256": digest(library_path())}}
    store = StageStore("results/alpha9-perten-keyed/state", root/"scratch", root/"evidence", Path.cwd(), json.loads(Path("configs/bank/storage-policy-alpha10.json").read_text()))
    plan = {"inputs": [{"path": str(input_path.resolve()), "sha256": digest(input_path), "bytes": input_path.stat().st_size}],
            "scratch_bytes": 65536, "evidence_bytes": 800000, "expected_fits": 324, "expected_permutations": 0,
            "uncertainty": "Six frozen intersections, all six unchanged families; 359 matched IDs; no disk matrix/model copies."}
    def run(folder):
        results = {}
        for spec in frozen["specifications"]:
            oof, lineage = [], []
            for cell in frozen["cells"]:
                train = [by_id[s] for s in cell["train_sample_ids"]]
                valid = [by_id[s] for s in cell["validation_sample_ids"]]
                print(spec["id"]+" / "+cell["cell_id"], flush=True)
                fitted, trace = inner_fit(train, cell["inner_fold_set"], spec, str(library_path()))
                pred = fitted.predict([r["x"] for r in valid]).reshape(-1).tolist()
                oof.extend({"physical_sample_id": r["physical_sample_id"], "component_id": r["independence_group"], "y": r["y"], "prediction": p} for r, p in zip(valid, pred, strict=True))
                lineage.append({"cell_id": cell["cell_id"], "selected": trace["selected"], "artifact_sha256": trace["artifact_sha256"],
                                "full_trace_sha256": fingerprint(trace), "native_fit_lineage_verified": trace["native_fit_lineage_verified"],
                                "fit_and_selection_seconds": trace["fit_and_selection_seconds"]})
                del fitted
            oof.sort(key=lambda r: r["physical_sample_id"])
            if spec["id"].endswith("alpha9"):
                if spec["id"] == "pls_alpha9":
                    stress = next(d["value"]["oof"] for d in old["scientific"]["deep"]["experiments"] if d["design_id"] == "holdout:cereal_type")
                    stress = [{**r, "prediction": r["spectral"]} for r in stress]
                else:
                    stress = json.loads(Path("docs/benchmarks/alpha9/perten-family-comparison.json").read_text())["designs"]["holdout:cereal_type"]["result"]["value"]["oof"]
                    stress = [{**r, "prediction": r["ridge"]} for r in stress]
            else:
                stress = json.loads((public/(spec["id"]+".json")).read_text())["designs"]["holdout:cereal_type"]["value"]["oof"]
            results[spec["id"]] = {"scores": score_oof(oof, "prediction"), "oof": oof, "lineage": lineage,
                "stress_minus_size_control": paired_contrast([stress, oof], [1, -1])}
        return {"protocol_version": "domains.size_match.v0.1", "evaluation_id": frozen["evaluation_id"], "expected_fit_count": 324,
                "n_evaluated": 359, "n_contexts": 17, "models": results,
                "limitation": "Exact sample counts; cereal/context composition and target/spectral support remain unequal. Not causal attribution.", "test_target_accessed": False}
    with threadpool_limits(limits=1):
        receipt, value = store.run(contract, "P3", plan, run)
    atomic_json(root/"size-control-receipt.json", receipt)
    if value is None: raise RuntimeError(receipt)
    destination = public/"size-control-results.json"
    if not destination.exists(): destination.hardlink_to((root/"evidence"/receipt["artifact"]).resolve())
    if digest(destination) != receipt["sha256"]: raise ValueError("SIZE_CONTROL_EXPORT_CHANGED")
    print(json.dumps({"status": receipt["status"], "cache_hit": receipt["cache_hit"], "bytes": receipt["measured_evidence_bytes"]}))


if __name__ == "__main__": main()
