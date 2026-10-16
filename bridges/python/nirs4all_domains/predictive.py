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


def _inner_fit(rows, library, seed, inner_folds, max_components, scope):
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
