"""Bounded identity orchestration over DAG-ML CV/SELECT/REFIT and native Methods.

No numerical fit, preprocessing, regression metric or mean is implemented here.
Retained-test rows are removed before constructing any native training request.
"""
from __future__ import annotations

import ctypes
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import random


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def native_summary(values):
    """Thin transport to the public eight-field summary ABI (same kernel as Rust)."""
    from n4m import Context
    from n4m._ffi import lib
    values = list(map(float, values))
    if not values or not all(map(math.isfinite, values)):
        raise ValueError("A nonempty finite summary population is required")
    data = (ctypes.c_double * len(values))(*values)
    out = (ctypes.c_double * 8)()
    with Context() as context:
        status = lib.n4m_preflight_summary_compute(context.handle, data, None, len(values), out)
        if status:
            raise RuntimeError(f"Methods summary failed: {status}")
    return dict(zip(("count", "min", "max", "mean", "sd", "q25", "median", "q75"),
                    (float(v) if math.isfinite(v) else None for v in out), strict=True))


def group_folds(rows, n_folds, seed, scope):
    """Declare identity-only folds; DAG-ML validates the complete FoldSet."""
    import dag_ml
    groups = sorted({r["independence_group"] for r in rows},
                    key=lambda g: fingerprint([seed, scope, g]))
    if len(groups) < n_folds:
        raise ValueError("Insufficient independent groups for the prespecified CV")
    assignment = {group: i % n_folds for i, group in enumerate(groups)}
    ids = [r["physical_sample_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("The predictive probe requires one mean spectrum per physical sample")
    folds = [{"fold_id": f"{scope}:{fold}",
              "train_sample_ids": [r["physical_sample_id"] for r in rows if assignment[r["independence_group"]] != fold],
              "validation_sample_ids": [r["physical_sample_id"] for r in rows if assignment[r["independence_group"]] == fold],
              "metadata": {}} for fold in range(n_folds)]
    result = {"id": scope, "sample_ids": ids, "folds": folds,
              "sample_groups": {r["physical_sample_id"]: r["independence_group"] for r in rows}}
    dag_ml.validate_fold_set_json(json.dumps(result))
    return result


def _inner_fit(rows, library, seed, inner_folds, max_components, scope, residual_factor=None):
    import dag_ml
    from dag_ml import _dag_ml as native
    from n4m.roles import NativeEstimator
    ids = [r["physical_sample_id"] for r in rows]
    relations = {"records": [{"observation_id": r["observation_id"], "sample_id": r["physical_sample_id"],
                              "group_id": r["independence_group"]} for r in rows]}
    inputs = {"model:compat.0.x": {"sample_ids": ids, "x": [r["x"] for r in rows],
                                  "y": [[r["y"]] for r in rows], "target_names": ["y"]}}
    envelope = {"schema_version": 1, "schema_fingerprint": fingerprint(["X", len(rows[0]["x"])]),
                "plan_fingerprint": fingerprint([scope, seed]),
                "relation_fingerprint": dag_ml.sample_relation_set_fingerprint_json(json.dumps(relations)),
                "coordinator_relations": relations,
                "data_content_fingerprint": fingerprint([[r["physical_sample_id"], r["x"]] for r in rows]),
                "target_content_fingerprint": fingerprint([[r["physical_sample_id"], r["y"]] for r in rows])}
    folds = group_folds(rows, inner_folds, seed, scope)
    dsl = {"id": "domains-sanity", "pipeline": [{"model": "n4m:models.pls.pls_regression",
        "params": {"method_id": "models.pls.pls_regression", "n_components": 1,
                   "center_x": True, "scale_x": False, "center_y": True, "scale_y": False},
        "generators": [{"kind": "range", "param": "n_components", "start": 1, "stop": max_components, "step": 1}]}],
        "split_invocation": {"id": "split:inner", "controller_id": None,
                             "params": {"kind": "group_kfold", "n_splits": inner_folds}, "fold_set": folds},
        "data_bindings": [{"node_id": "model:compat.0", "input_name": "x", "request_id": "domains-mean-spectra",
            **{k: envelope[k] for k in ("schema_fingerprint", "plan_fingerprint", "relation_fingerprint")},
            "output_representation": "tabular_numeric", "feature_set_id": "x", "source_ids": ["X"], "require_relations": True}]}
    if residual_factor is not None:
        return _residual_cv(rows, dsl, envelope, folds, residual_factor)
    payload_json, artifacts = native.run_cv_refit_methods_in_process(
        json.dumps(dsl), json.dumps(envelope), json.dumps(inputs), str(library), "rmse", refit=True)
    payload = json.loads(payload_json)
    records = [r for r in payload["refit_artifacts"] if r["node_id"] == "model:compat.0"]
    if len(records) != 1:
        raise RuntimeError("Exactly one selected native PLS artifact is required")
    artifact = records[0]["artifact"]
    model = NativeEstimator.from_n4me(bytes(artifacts[artifact["id"]]))
    # Assert that every inner FIT_CV frame's train population matches its declared scope.
    expected = {f["fold_id"]: set(f["train_sample_ids"]) for f in folds["folds"]}
    observed = []
    for frame in payload["node_results"]:
        for block in frame.get("predictions", []):
            if block["partition"] == "train":
                if set(block["sample_ids"]) != expected[block["fold_id"]]:
                    raise RuntimeError("Native fit lineage differs from the declared inner training IDs")
                observed.append(block["fold_id"])
    if set(observed) != set(expected):
        raise RuntimeError("Native inner FIT_CV lineage is incomplete")
    return model, {"inner_fold_set": folds, "n_components": int(model.n_components),
                   "artifact_sha256": artifact["content_fingerprint"],
                   "input_sha256": fingerprint(inputs), "native_fit_lineage_verified": True}


def _nested(rows, library, seed, outer_folds, inner_folds, max_components):
    from n4m.metrics.scoring import rmse, mae, r2
    folds = group_folds(rows, outer_folds, seed, "outer")
    by_id = {r["physical_sample_id"]: r for r in rows}
    predictions, null, lineage = {}, {}, []
    for fold in folds["folds"]:
        train = [by_id[s] for s in fold["train_sample_ids"]]
        valid = [by_id[s] for s in fold["validation_sample_ids"]]
        model, evidence = _inner_fit(train, library, seed, inner_folds, max_components, fold["fold_id"] + ":inner")
        values = model.predict([r["x"] for r in valid]).reshape(-1).tolist()
        mean = native_summary(r["y"] for r in train)["mean"]
        predictions.update(zip(fold["validation_sample_ids"], values, strict=True))
        null.update({sid: mean for sid in fold["validation_sample_ids"]})
        lineage.append({**fold, **evidence, "null_training_mean": mean})
        del model
    ids = sorted(by_id)
    if set(predictions) != set(ids):
        raise RuntimeError("Outer OOF predictions must cover the development samples exactly once")
    truth = [by_id[s]["y"] for s in ids]
    score = lambda pred: {"rmse": float(rmse(truth, pred)), "mae": float(mae(truth, pred)), "r2": float(r2(truth, pred))}
    return {"pls": score([predictions[s] for s in ids]), "null": score([null[s] for s in ids]),
            "oof": [{"physical_sample_id": s, "group": by_id[s]["independence_group"], "y": by_id[s]["y"], "prediction": predictions[s], "null_prediction": null[s]} for s in ids],
            "outer_fold_set": folds, "lineage": lineage}


def permute_group_targets(rows, seed):
    """Exchange whole target vectors among equal-cardinality groups; no acquisition shuffle."""
    groups = {}
    for row in rows:
        groups.setdefault(row["independence_group"], []).append(row)
    groups = {g: sorted(v, key=lambda r: r["physical_sample_id"]) for g, v in sorted(groups.items())}
    strata = {}
    for group, values in groups.items():
        strata.setdefault(len(values), []).append(group)
    rng = random.Random(seed)
    replacement = {}
    for keys in strata.values():
        sources = list(keys); rng.shuffle(sources)
        for dest, src in zip(keys, sources, strict=True):
            for a, b in zip(groups[dest], groups[src], strict=True):
                replacement[a["physical_sample_id"]] = b["y"]
    return [{**r, "y": replacement[r["physical_sample_id"]]} for r in rows]


def predictive_sanity(task, library, *, seed=17, outer_folds=5, inner_folds=3, max_components=5, permutations=19, progress=None):
    from n4m._ffi import library_path
    if version("dag-ml") != "0.3.41" or version("nirs4all-methods") != "1.3.6":
        raise ValueError("This probe is qualified only with dag-ml 0.3.41 and Methods 1.3.6")
    if Path(library).resolve() != Path(library_path()).resolve():
        raise ValueError("DAG-ML and Methods artifact replay must use the same explicit library")
    if task["policy"]["representation"] != "technical_mean":
        raise ValueError("The probe requires a Rust-exported technical_mean task")
    if task.get("provenance",{}).get("reference_xy_blocked") != "false":
        raise ValueError("The Rust reference audit must authorize descriptive X-Y analysis")
    # Do not inspect retained target fields, even to build a fingerprint.
    rows = [{**r,"independence_group":r["metadata"]["validation_component_id"]} for r in task["observations"] if r["partition"] == "train" and r.get("y") is not None]
    if not rows or any(not math.isfinite(r["y"]) or any(x is None or not math.isfinite(x) for x in r["x"]) for r in rows):
        raise ValueError("Complete finite development X/Y is required")
    result = _nested(rows, library, seed, outer_folds, inner_folds, max_components)
    observed = result["null"]["rmse"] - result["pls"]["rmse"]
    permuted = []
    for i in range(permutations):
        draw = _nested(permute_group_targets(rows, seed + 1000 + i), library, seed, outer_folds, inner_folds, max_components)
        permuted.append({"pls": draw["pls"], "null": draw["null"], "improvement_rmse": draw["null"]["rmse"] - draw["pls"]["rmse"]})
        if progress:
            progress(f"Permutation {i+1}/{permutations} completed")
    result.update(protocol_version="domains.predictive_sanity.v0.1", status="computed", target=task["context"]["target_id"],
        target_unit=task.get("target_unit"), seed=seed, test_target_accessed=False,
        n_samples=len(rows), n_groups=len({r["independence_group"] for r in rows}),
        development_input_sha256=fingerprint(rows), engine_versions={n:version(n) for n in ("dag-ml","nirs4all-methods")},
        parameters={"outer_folds":outer_folds,"inner_folds":inner_folds,"component_grid":list(range(1,max_components+1)),"preprocessing":"fold-local Methods centering, no autoscaling"},
        improvement_rmse=observed, permutation={"draws":permutations,"unit":"whole plot vectors, cardinality restricted",
            "p_exploratory": (1+sum(p["improvement_rmse"] >= observed for p in permuted))/(permutations+1) if permutations else None,
            "results":permuted,"exchangeability":"assumed for plots within cardinality strata; not a confirmatory test"},
        interpretation="Development-only nested group OOF sanity check; no retained-test performance or production calibration")
    return result


def group_means(rows, factor):
    """Fold-local native means. No validation target is accepted by this function."""
    levels = {}
    for row in rows:
        level = row["metadata"].get(factor)
        if level and level.strip():
            levels.setdefault(level, []).append(row["y"])
    return {"global": native_summary(r["y"] for r in rows)["mean"],
            "levels": {k: native_summary(v)["mean"] for k, v in sorted(levels.items())},
            "training_ids": [r["physical_sample_id"] for r in rows]}


def group_prediction(row, baseline, factor):
    level = row["metadata"].get(factor)
    return baseline["levels"].get(level, baseline["global"]), (
        "level_training_mean" if level in baseline["levels"] else "global_training_fallback")


class _ZeroResidual:
    """Exact degenerate target case, not a fitted alternative to PLS."""
    n_components = 0

    def predict(self, x):
        import numpy as np
        return np.zeros((len(x), 1))  # output buffer only; no numerical fit


def _residual_cv(rows, dsl, envelope, folds, factor):
    """DAG scheduler/SELECT/REFIT, with Methods fitting in a scope-bound callback.

    The callback-free API accepts one static Y buffer. Its public callback twin
    supplies the fold scope needed to fit a different target baseline per fold.
    """
    import dag_ml
    from dag_ml import _dag_ml as native
    from n4m.roles import PLSRegression, NativeEstimator
    import copy
    dsl = copy.deepcopy(dsl)
    controller = "controller:domains.residual_pls"
    dsl["pipeline"][0]["model"] = "domains:residual_pls"
    dsl["pipeline"][0]["metadata"] = {"controller_id": controller}
    graph = dag_ml.compile_pipeline_dsl_artifact(dsl).graph.to_dict()
    node = next(n for n in graph["nodes"] if n["kind"] == "model")
    manifest = {"controller_id": controller, "controller_version": "0.1.0-alpha.6",
                "operator_kind": "model", "priority": 0,
                "supported_phases": ["FIT_CV", "REFIT", "PREDICT"],
                "input_ports": node["ports"]["inputs"], "output_ports": node["ports"]["outputs"],
                "data_requirements": None,
                "capabilities": ["deterministic", "emits_predictions", "emits_artifacts", "stateful"],
                "fit_scope": "fold_train", "rng_policy": "uses_core_seed", "artifact_policy": "serializable"}
    by_id = {r["physical_sample_id"]: r for r in rows}
    fold_by_id = {f["fold_id"]: f for f in folds["folds"]}
    events, refits = [], {}

    def callback(task):
        plan = task["node_plan"]
        refit = task["phase"] == "REFIT"
        if task["phase"] not in ("FIT_CV", "REFIT"):
            raise ValueError("Unexpected residual callback phase")
        scope = {"train_sample_ids": list(by_id), "validation_sample_ids": []} if refit else fold_by_id[task["fold_id"]]
        train_ids, valid_ids = scope["train_sample_ids"], scope["validation_sample_ids"]
        if set(train_ids) & set(valid_ids):
            raise ValueError("Residual fit scope crosses validation")
        train, valid = [by_id[s] for s in train_ids], [by_id[s] for s in valid_ids]
        # Bind the numerical input to the actual native scheduler data-view IDs.
        views = task["data_views"]
        native_train = [v["sample_ids"] for v in views.values() if v["partition"] in ("fold_train", "full_train")]
        native_valid = [v["sample_ids"] for v in views.values() if v["partition"] == "fold_validation"]
        if not native_train or (not refit and not native_valid) or any(set(v) != set(train_ids) for v in native_train) or any(set(v) != set(valid_ids) for v in native_valid):
            raise ValueError("Native residual data views differ from declared fit scope: " + repr(views))
        baseline = group_means(train, factor)
        residual = [r["y"] - group_prediction(r, baseline, factor)[0] for r in train]
        zero_residual = native_summary(residual)["min"] == native_summary(residual)["max"] == 0.
        if zero_residual:
            # Methods refuses constant Y. There is exactly zero training residual
            # to learn; keep the group baseline and state the degenerate case.
            model = _ZeroResidual()
            artifact_bytes = json.dumps({"kind":"domains.exact_zero_residual.v1", "training_ids":train_ids}).encode()
        else:
            model = PLSRegression(n_components=int(plan["params"]["n_components"]),
                                  center_x=True, scale_x=False, center_y=True, scale_y=False)
            model.fit([r["x"] for r in train], [[y] for y in residual])
            artifact_bytes = model.to_n4me()
        digest = hashlib.sha256(artifact_bytes).hexdigest()
        event = {"phase": task["phase"], "fold_id": task["fold_id"],
                 "n_components": int(model.n_components), "baseline": baseline,
                 "validation_ids": valid_ids, "residual_target_sha256": fingerprint(list(zip(train_ids, residual))),
                 "artifact_sha256": digest, "native_fit_lineage_verified": True}
        event["fit_kind"] = "exact_zero_training_residual_no_pls_fit" if zero_residual else "native_methods_pls"
        events.append(event)
        artifacts, handles = [], {}
        if refit:
            aid = "artifact:domains.residual:" + digest
            artifacts = [{"id": aid, "kind": "exact_zero_residual" if zero_residual else "n4me", "controller_id": controller,
                          "content_fingerprint": digest, "size_bytes": len(artifact_bytes)}]
            handles = {aid: {"handle": 80001, "kind": "model", "owner_controller": controller}}
            refits[digest] = (artifact_bytes, event)
        predictions, targets = [], []
        if valid:
            correction = model.predict([r["x"] for r in valid]).reshape(-1).tolist()
            predictions = [{"producer_node": plan["node_id"], "producer_port": "oof",
                            "partition": "validation", "fold_id": task["fold_id"],
                            "sample_ids": valid_ids, "values": [[group_prediction(r, baseline, factor)[0]+p] for r,p in zip(valid, correction, strict=True)],
                            "target_names": ["y"]}]
            targets = [{"level": "sample", "unit_ids": [{"level": "sample", "id": s} for s in valid_ids],
                        "values": [[r["y"]] for r in valid], "target_names": ["y"]}]
        return {"node_id": plan["node_id"], "outputs": {"oof": {"handle": 80002, "kind": "prediction", "owner_controller": controller}},
                "predictions": predictions, "regression_targets": targets,
                "artifacts": artifacts, "artifact_handles": handles,
                "lineage": {"record_id": "lineage:"+fingerprint([task["phase"],task["fold_id"],task["variant_id"],digest]),
                            "run_id": task["run_id"], "node_id": plan["node_id"], "phase": task["phase"],
                            "controller_id": controller, "controller_version": plan["controller_version"],
                            "variant_id": task["variant_id"], "fold_id": task["fold_id"], "branch_path": task["branch_path"],
                            "input_lineage": [], "artifact_refs": artifacts, "params_fingerprint": plan["params_fingerprint"],
                            "seed": task["seed"], "unsafe_flags": [], "metrics": {}}}

    payload = json.loads(native.run_cv_refit_in_process(json.dumps(dsl), json.dumps(envelope),
        json.dumps([manifest]), callback, "rmse", refit=True))
    if len(refits) != 1:
        raise RuntimeError("Exactly one DAG-selected residual REFIT artifact required")
    artifact, refit = next(iter(refits.values()))
    model = _ZeroResidual() if refit["fit_kind"]=="exact_zero_training_residual_no_pls_fit" else NativeEstimator.from_n4me(artifact)
    return model, {"inner_fold_set": folds, "n_components": int(model.n_components),
                   "artifact_sha256": refit["artifact_sha256"], "native_fit_lineage_verified": True,
                   "residual_fit_events": sorted(events, key=lambda e:(e["phase"],e["fold_id"] or "",e["n_components"])),
                   "outer_training_baseline": refit["baseline"],
                   "selection_engine": "DAG-ML public run_cv_refit_in_process; original-unit validation RMSE",
                   "selection_payload_sha256": fingerprint(payload)}
