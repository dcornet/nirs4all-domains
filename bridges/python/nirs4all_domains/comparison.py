"""Fixed-family comparison on already frozen development folds; native kernels only."""
from .dependence import development_rows, validate_folds, score_oof, state
from .predictive import _inner_fit
from .storage import fingerprint


def ridge_on_frozen_folds(task, folds, library, config, frozen_suite):
    if (not frozen_suite.get("tasks") or frozen_suite.get("suite_id") != fingerprint({k:v for k,v in frozen_suite.items() if k != "suite_id"})
            or not frozen_suite.get("selection_basis", "").startswith("qualification evidence fixed")):
        raise ValueError("SUITE_MUST_BE_FROZEN_BEFORE_SECONDARY_ESTIMATOR_EVALUATION")
    rows = development_rows(task)
    contract = frozen_suite.get("metric_contract", {}).get("evaluation", {})
    if contract != {"context":task["context"], "development_input_sha256":fingerprint(rows), "outer_fold_set_sha256":fingerprint(folds)}:
        raise ValueError("FROZEN_EVALUATION_CONTENT_OR_FOLDS_MISMATCH")
    validate_folds(rows, folds)
    by_id = {r["physical_sample_id"]:r for r in rows}
    oof, lineage = [], []
    for fold in folds["folds"]:
        train = [by_id[s] for s in fold["train_sample_ids"]]
        valid = [by_id[s] for s in fold["validation_sample_ids"]]
        try:
            fitted, trace = _inner_fit(train, library, config["seed"], config["inner_folds"], config["max_components"],
                                       fold["fold_id"]+":inner", family="ridge")
            predicted = fitted.predict([r["x"] for r in valid]).reshape(-1).tolist()
            oof.extend({"physical_sample_id":r["physical_sample_id"], "component_id":r["independence_group"],
                        "fold_id":fold["fold_id"], "y":r["y"], "ridge":p} for r,p in zip(valid,predicted,strict=True))
            lineage.append({"fold_id":fold["fold_id"], "train_ids_sha256":fingerprint(fold["train_sample_ids"]),
                            "inner_folds_sha256":fingerprint(trace["inner_fold_set"]),
                            "native_fit_lineage_verified":trace["native_fit_lineage_verified"], "artifact_sha256":trace["artifact_sha256"]})
            del fitted
        except Exception as error:
            return state(reason=f"{type(error).__name__}:{error}", status="error")
    return state({"family":"Methods Ridge alpha=1.0, centered X/Y, no scaling", "selection_engine":"DAG-ML native CV/refit",
                  "suite_id_frozen_before_evaluation":frozen_suite["suite_id"], "test_target_accessed":False,
                  "oof":sorted(oof,key=lambda r:r["physical_sample_id"]), "scores":score_oof(oof,"ridge"), "lineage":lineage,
                  "limitation":"Two families on limited frozen designs do not certify estimator-independent low structural dependence."})
