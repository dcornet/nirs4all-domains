"""Matched grouped comparison; fitting/selection/scoring belong to upstream providers."""
from __future__ import annotations

import copy
import hashlib
from importlib.metadata import version
import json
import math
import pickle
import random
import time

from .dependence import development_rows, score_oof, state, validate_folds
from .predictive import group_folds
from .storage import fingerprint

PROTOCOL = "domains.multifamily.v0.1"


def validate_spec(spec):
    if spec["engine"] == "nirs4all":
        cfg = spec["config"]
        if (spec["model"] not in ("hard_aom_chain", "sparse_mkr") or cfg.get("cv_n_components", False)
                or len(cfg.get("lambdas", [])) != 1 or cfg["max_chain_depth"] != 1
                or cfg["primitive_bank"] != "compact" or cfg["rank"] > 32 or cfg["top_global"] > 8
                or set(spec["grid"]) - {"n_components"}):
            raise ValueError("UNQUALIFIED_FASTAOM_INTERNAL_SELECTION_OR_SEARCH_BUDGET")
    elif spec["engine"] == "methods":
        if spec["method"] not in ("models.regularized.ridge", "models.pls.pls_regression") or spec["preprocessing"] not in ("raw", "snv"):
            raise ValueError("UNQUALIFIED_NATIVE_PIPELINE")
    else:
        raise ValueError("UNQUALIFIED_ENGINE")
    if math.prod(len(v) for v in spec["grid"].values()) > 5:
        raise ValueError("CANDIDATE_BUDGET_EXCEEDED")


def _request(rows, folds, spec):
    import dag_ml
    relations = {"records": [{"observation_id": r["observation_id"], "sample_id": r["physical_sample_id"],
                               "group_id": r["independence_group"]} for r in rows]}
    envelope = {"schema_version": 1, "schema_fingerprint": fingerprint(["X", len(rows[0]["x"])]),
                "plan_fingerprint": fingerprint([PROTOCOL, folds, spec]),
                "relation_fingerprint": dag_ml.sample_relation_set_fingerprint_json(json.dumps(relations)),
                "coordinator_relations": relations,
                "data_content_fingerprint": fingerprint([[r["physical_sample_id"], r["x"]] for r in rows]),
                "target_content_fingerprint": fingerprint([[r["physical_sample_id"], r["y"]] for r in rows])}
    host = spec["engine"] == "nirs4all"
    method = "domains:fast_aom" if host else "n4m:" + spec["method"]
    params = {} if host else {"method_id": spec["method"], "center_x": True, "scale_x": False, "center_y": True}
    if not host and "pls" in spec["method"]:
        params["scale_y"] = False
    params.update({k: v[0] for k, v in spec["grid"].items()})
    model = {"model": method, "params": params}
    if spec["grid"]:
        model["generators"] = [{"kind": "grid", "params": spec["grid"]}]
    if host:
        model["metadata"] = {"controller_id": "controller:domains.fast_aom"}
    steps = [model]
    if spec.get("preprocessing") == "snv":
        steps.insert(0, {"ref": "n4m:preprocessing.scatter.snv", "params": {"method_id": "preprocessing.scatter.snv"}})
    first = "model:compat.0" if len(steps) == 1 else "transform:compat.0"
    dsl = {"id": "domains-multifamily", "pipeline": steps,
           "split_invocation": {"id": "split:inner", "controller_id": None,
                "params": {"kind": "group_kfold", "n_splits": len(folds["folds"])}, "fold_set": folds},
           "data_bindings": [{"node_id": first, "input_name": "x", "request_id": "domains-frozen-spectra",
                **{k: envelope[k] for k in ("schema_fingerprint", "plan_fingerprint", "relation_fingerprint")},
                "output_representation": "tabular_numeric", "feature_set_id": "x", "source_ids": ["X"], "require_relations": True}]}
    inputs = {first + ".x": {"sample_ids": [r["physical_sample_id"] for r in rows], "x": [r["x"] for r in rows],
                             "y": [[r["y"]] for r in rows], "target_names": ["y"]}}
    return dsl, envelope, inputs


class NativePipeline:
    def __init__(self, steps):
        self.steps = steps

    def predict(self, x):
        for step in self.steps[:-1]:
            x = step.transform(x)
        return self.steps[-1].predict(x)


def _native_inner(rows, folds, spec, library):
    from dag_ml import _dag_ml as native
    from n4m.roles import NativeEstimator
    dsl, envelope, inputs = _request(rows, folds, spec)
    started = time.perf_counter()
    raw, artifacts = native.run_cv_refit_methods_in_process(json.dumps(dsl), json.dumps(envelope),
                          json.dumps(inputs), str(library), "rmse", refit=True)
    payload = json.loads(raw)
    elapsed = time.perf_counter() - started
    expected = {f["fold_id"]: set(f["train_sample_ids"]) for f in folds["folds"]}
    observed = set()
    for frame in payload["node_results"]:
        for block in frame.get("predictions", []):
            if block["partition"] == "train":
                if set(block["sample_ids"]) != expected[block["fold_id"]]:
                    raise ValueError("NATIVE_TRAINING_LINEAGE_MISMATCH")
                observed.add(block["fold_id"])
    if observed != set(expected):
        raise ValueError("INCOMPLETE_NATIVE_TRAINING_LINEAGE")
    records = sorted(payload["refit_artifacts"], key=lambda a: int(a["node_id"].split(".")[-1]))
    steps, hashes = [], []
    for record in records:
        artifact = record["artifact"]
        data = bytes(artifacts[artifact["id"]])
        if hashlib.sha256(data).hexdigest() != artifact["content_fingerprint"]:
            raise ValueError("NATIVE_ARTIFACT_HASH_MISMATCH")
        steps.append(NativeEstimator.from_n4me(data))
        hashes.append(artifact["content_fingerprint"])
    if len(steps) != len(dsl["pipeline"]):
        raise ValueError("INCOMPLETE_SELECTED_PIPELINE")
    parameter = "alpha" if "ridge" in spec["method"] else "n_components"
    return NativePipeline(steps), {"selected": {parameter: getattr(steps[-1], parameter)},
        "artifact_sha256": hashes, "native_fit_lineage_verified": True,
        "selection_payload_sha256": fingerprint(payload), "candidate_count": len(payload["variant_catalog"]),
        "fit_and_selection_seconds": elapsed, "events": [], "failures": []}


def _fast_inner(rows, folds, spec):
    import dag_ml
    from dag_ml import _dag_ml as native
    import numpy as np
    from nirs4all.operators.models import FastAOMPLSRidge, FastAOMConfig
    if version("nirs4all") != "1.4.10":
        raise ValueError("QUALIFIED_NIRS4ALL_VERSION_REQUIRED")
    dsl, envelope, _ = _request(rows, folds, spec)
    node, = [n for n in dag_ml.compile_pipeline_dsl_artifact(dsl).graph.to_dict()["nodes"] if n["kind"] == "model"]
    controller = "controller:domains.fast_aom"
    manifest = {"controller_id": controller, "controller_version": "0.1.0-alpha.10", "operator_kind": "model", "priority": 0,
                "supported_phases": ["FIT_CV", "REFIT", "PREDICT"], "input_ports": node["ports"]["inputs"],
                "output_ports": node["ports"]["outputs"], "data_requirements": None,
                "capabilities": ["deterministic", "emits_predictions", "emits_artifacts", "stateful"],
                "fit_scope": "fold_train", "rng_policy": "uses_core_seed", "artifact_policy": "serializable"}
    by_id = {r["physical_sample_id"]: r for r in rows}
    scopes = {f["fold_id"]: f for f in folds["folds"]}
    events, refits, failures = [], [], []

    def callback(task):
        plan, phase = task["node_plan"], task["phase"]
        if phase not in ("FIT_CV", "REFIT"):
            raise ValueError("UNEXPECTED_FASTAOM_PHASE")
        scope = {"train_sample_ids": list(by_id), "validation_sample_ids": []} if phase == "REFIT" else scopes[task["fold_id"]]
        train_ids, valid_ids = scope["train_sample_ids"], scope["validation_sample_ids"]
        views = task["data_views"].values()
        native_train = [v["sample_ids"] for v in views if v["partition"] in ("fold_train", "full_train")]
        native_valid = [v["sample_ids"] for v in views if v["partition"] == "fold_validation"]
        if (set(train_ids) & set(valid_ids) or not native_train or (phase == "FIT_CV" and not native_valid)
                or any(set(v) != set(train_ids) for v in native_train) or any(set(v) != set(valid_ids) for v in native_valid)):
            raise ValueError("FASTAOM_NATIVE_DATA_VIEW_SCOPE_MISMATCH")
        train = [by_id[s] for s in train_ids]
        cfg = copy.deepcopy(spec["config"])
        params = plan.get("params", {})
        cfg.update(params)
        cfg.update(model=spec["model"], lambdas=tuple(cfg["lambdas"]))
        began = time.perf_counter()
        try:
            fitted = FastAOMPLSRidge(FastAOMConfig(**cfg))
            fitted.fit(np.asarray([r["x"] for r in train]), np.asarray([r["y"] for r in train]))
        except Exception as error:
            failures.append({"phase": phase, "fold_id": task["fold_id"], "params": params, "reason": str(error)})
            raise
        fit_seconds = time.perf_counter() - began
        diagnostic = copy.deepcopy(fitted.diagnostics_)
        # Timing is a measurement, excluded from the reproducible fitted-state
        # artifact. Only upstream diagnostic metadata is removed, never model state.
        fitted.diagnostics_.pop("timings_s", None)
        data = pickle.dumps(fitted, protocol=5)
        sha = hashlib.sha256(data).hexdigest()
        event = {"phase": phase, "fold_id": task["fold_id"], "params": params,
                 "train_ids_sha256": fingerprint(train_ids), "validation_ids_sha256": fingerprint(valid_ids),
                 "training_input_sha256": fingerprint([[r["physical_sample_id"], r["x"], r["y"]] for r in train]),
                 "artifact_sha256": sha, "artifact_bytes": len(data), "native_fit_lineage_verified": True,
                 "fit_seconds": fit_seconds, "diagnostics": diagnostic,
                 "actual_ranks": [lr.rank for lr in fitted.lowrank_bases_],
                 "actual_components": getattr(fitted.model_, "n_components_", len(fitted.model_.components_))}
        events.append(event)
        artifacts, handles = [], {}
        if phase == "REFIT":
            restored = pickle.loads(data)  # own in-memory artifact only
            x = np.asarray([r["x"] for r in train[:3]])
            if not np.allclose(restored.predict(x), fitted.predict(x), atol=1e-9, rtol=1e-9):
                raise ValueError("FASTAOM_SERIALIZATION_REPLAY_DIFFERS")
            refits.append((restored, event))
            artifacts = [{"id": "artifact:"+sha, "kind": "pickle", "controller_id": controller,
                          "content_fingerprint": sha, "size_bytes": len(data)}]
            handles = {"artifact:"+sha: {"handle": 80001, "kind": "model", "owner_controller": controller}}
        predictions, targets = [], []
        if valid_ids:
            valid = [by_id[s] for s in valid_ids]
            pred = fitted.predict(np.asarray([r["x"] for r in valid])).reshape(-1).tolist()
            if not all(map(math.isfinite, pred)):
                raise ValueError("NONFINITE_FASTAOM_PREDICTION")
            predictions = [{"producer_node": plan["node_id"], "producer_port": "oof", "partition": "validation",
                            "fold_id": task["fold_id"], "sample_ids": valid_ids, "values": [[p] for p in pred], "target_names": ["y"]}]
            targets = [{"level": "sample", "unit_ids": [{"level": "sample", "id": s} for s in valid_ids],
                        "values": [[r["y"]] for r in valid], "target_names": ["y"]}]
        return {"node_id": plan["node_id"], "outputs": {"oof": {"handle": 80002, "kind": "prediction", "owner_controller": controller}},
                "predictions": predictions, "regression_targets": targets, "artifacts": artifacts, "artifact_handles": handles,
                "lineage": {"record_id": "lineage:"+fingerprint([phase, task["fold_id"], task["variant_id"], sha]),
                            "run_id": task["run_id"], "node_id": plan["node_id"], "phase": phase,
                            "controller_id": controller, "controller_version": plan["controller_version"],
                            "variant_id": task["variant_id"], "fold_id": task["fold_id"], "branch_path": task["branch_path"],
                            "input_lineage": [], "artifact_refs": artifacts, "params_fingerprint": plan["params_fingerprint"],
                            "seed": task["seed"], "unsafe_flags": [], "metrics": {}}}

    began = time.perf_counter()
    payload = json.loads(native.run_cv_refit_in_process(json.dumps(dsl), json.dumps(envelope), json.dumps([manifest]), callback, "rmse", refit=True))
    if len(refits) != 1:
        raise ValueError("EXACTLY_ONE_DAG_SELECTED_FASTAOM_REFIT_REQUIRED")
    fitted, selected = refits[0]
    return fitted, {"selected": selected["params"], "artifact_sha256": selected["artifact_sha256"],
        "native_fit_lineage_verified": True, "candidate_count": len(payload["variant_catalog"]),
        "selection_payload_sha256": fingerprint(payload), "events": events, "failures": failures,
        "fit_and_selection_seconds": time.perf_counter()-began}


def inner_fit(rows, folds, spec, library):
    from pathlib import Path
    from n4m._ffi import library_path
    validate_spec(spec)
    validate_folds(rows, folds)
    if version("dag-ml") != "0.3.41" or version("nirs4all-methods") != "1.3.6":
        raise ValueError("QUALIFIED_NATIVE_PROVIDER_VERSIONS_REQUIRED")
    if Path(library).resolve() != Path(library_path()).resolve():
        raise ValueError("IDENTICAL_NATIVE_LIBRARY_REQUIRED_FOR_FITTING_AND_SCORING")
    return _fast_inner(rows, folds, spec) if spec["engine"] == "nirs4all" else _native_inner(rows, folds, spec, library)


def freeze_evaluation(task, designs, specs, parent_evidence_id):
    rows = development_rows(task)
    for folds in designs.values():
        validate_folds(rows, folds)
    for spec in specs:
        validate_spec(spec)
    manifest = {"protocol_version": PROTOCOL, "parent_evidence_id": parent_evidence_id,
        "selection_basis": "alpha.9 qualification evidence fixed before new estimator scores",
        "context": task["context"], "development_input_sha256": fingerprint(rows),
        "target_unit": task.get("target_unit"), "specifications": specs, "outer_designs": designs,
        "inner_designs": {key: {f["fold_id"]: group_folds([r for r in rows if r["physical_sample_id"] in set(f["train_sample_ids"])],
                   3, 17, f["fold_id"]+":inner") for f in folds["folds"]} for key, folds in designs.items()},
        "purposes": ["within_population_estimator_comparison", "structure_sensitive_challenge"],
        "low_dependence": state(reason="UNDERPOWERED_CEREAL_TRANSFER_AND_UNAVAILABLE_INTERVENTIONS"),
        "test_target_accessed": False}
    return {**manifest, "evaluation_id": fingerprint(manifest)}


def compare_design(task, frozen, design, spec, library):
    if frozen["evaluation_id"] != fingerprint({k: v for k, v in frozen.items() if k != "evaluation_id"}):
        raise ValueError("FROZEN_EVALUATION_DIGEST_MISMATCH")
    rows = development_rows(task)
    if frozen["development_input_sha256"] != fingerprint(rows) or frozen["context"] != task["context"] or spec not in frozen["specifications"]:
        raise ValueError("FROZEN_CONTENT_OR_SPECIFICATION_MISMATCH")
    folds = frozen["outer_designs"][design]
    validate_folds(rows, folds)
    by_id = {r["physical_sample_id"]: r for r in rows}
    oof, lineage = [], []
    for fold in folds["folds"]:
        train = [by_id[s] for s in fold["train_sample_ids"]]
        valid = [by_id[s] for s in fold["validation_sample_ids"]]
        inner = frozen["inner_designs"][design][fold["fold_id"]]
        try:
            fitted, trace = inner_fit(train, inner, spec, library)
            began = time.perf_counter()
            pred = fitted.predict([r["x"] for r in valid]).reshape(-1).tolist()
            prediction_seconds = time.perf_counter()-began
            if len(pred) != len(valid) or not all(map(math.isfinite, pred)):
                raise ValueError("NONFINITE_OR_INCOMPLETE_OUTER_PREDICTIONS")
            oof.extend({"physical_sample_id": r["physical_sample_id"], "component_id": r["independence_group"],
                "fold_id": fold["fold_id"], "y": r["y"], "prediction": p} for r, p in zip(valid, pred, strict=True))
            lineage.append({"fold_id": fold["fold_id"], "train_ids_sha256": fingerprint(fold["train_sample_ids"]),
                "inner_fold_set_sha256": fingerprint(inner), "prediction_seconds": prediction_seconds, **trace})
            del fitted
        except Exception as error:
            return {**state(reason=f"{type(error).__name__}:{error}", status="failed"),
                    "failed_fold_id": fold["fold_id"], "completed_folds": lineage, "partial_oof_count": len(oof)}
    oof.sort(key=lambda r: r["physical_sample_id"])
    return state({"specification": spec, "evaluation_id": frozen["evaluation_id"], "design_id": design,
        "oof": oof, "scores": score_oof(oof, "prediction"), "lineage": lineage,
        "test_target_accessed": False})


def paired_contrast(vectors, coefficients, *, draws=100, seed=17):
    """One component draw for every vector; all RMSE calculations use Methods."""
    from n4m.metrics.scoring import rmse
    if len(vectors) != len(coefficients) or not vectors:
        raise ValueError("CONTRAST_ARITY_MISMATCH")
    keyed = [{r["physical_sample_id"]: r for r in vector} for vector in vectors]
    if any(len(k) != len(v) for k, v in zip(keyed, vectors, strict=True)) or any(set(k) != set(keyed[0]) for k in keyed):
        raise ValueError("MATCHED_PHYSICAL_IDS_REQUIRED")
    for s in keyed[0]:
        if any((k[s]["component_id"], k[s]["y"]) != (keyed[0][s]["component_id"], keyed[0][s]["y"]) for k in keyed):
            raise ValueError("MATCHED_COMPONENT_AND_REFERENCE_IDENTITIES_REQUIRED")
    groups = {}
    for s, row in sorted(keyed[0].items()):
        groups.setdefault(row["component_id"], []).append(s)
    def evaluate(ids):
        y = [keyed[0][s]["y"] for s in ids]
        return sum(c*float(rmse(y, [k[s]["prediction"] for s in ids])) for c, k in zip(coefficients, keyed, strict=True))
    keys, rng, values, memberships, failures = sorted(groups), random.Random(seed), [], [], []
    for draw in range(draws):
        sample = [rng.choice(keys) for _ in keys]
        memberships.append(sample)
        try:
            value = evaluate([s for g in sample for s in groups[g]])
            if not math.isfinite(value):
                raise ValueError("NONFINITE_NATIVE_CONTRAST")
            values.append(value)
        except (ValueError, RuntimeError) as error:
            failures.append({"draw": draw, "reason": str(error)})
    ci = [sorted(values)[math.ceil(q*len(values))-1] for q in (.025, .975)] if len(values) >= 100 and len(keys) >= 10 else None
    return {"estimate": state(evaluate(sorted(keyed[0]))), "interval_95": state(ci) if ci else state(reason="REQUIRES_100_SUCCESSFUL_DRAWS_AND_10_COMPONENTS"),
        "requested": draws, "successful": len(values), "failures": failures, "seed": seed,
        "n_samples": len(keyed[0]), "n_components": len(keys), "component_membership_sha256": fingerprint(groups),
        "paired_draw_membership_sha256": fingerprint(memberships), "coefficients": coefficients,
        "conditioning": "Frozen OOF; observed context-block variation only; excludes refit and unseen-category uncertainty"}
