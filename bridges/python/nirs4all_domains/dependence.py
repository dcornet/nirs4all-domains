"""Bounded structural-dependence workflow; numerical work stays in Methods/DAG-ML."""
from __future__ import annotations

import argparse
from collections import Counter
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import random
import subprocess

from .predictive import (fingerprint, group_folds, group_means, group_prediction,
                         native_summary, _nested, _inner_fit)

PROTOCOL = "domains.structural_dependence.v0.1"


def state(value=None, reason=None, status=None):
    return {"status": status or ("computed" if reason is None else "unavailable"),
            "reason": reason, "value": value if reason is None else None}


def development_rows(task):
    if task["policy"]["representation"] != "technical_mean" or task.get("provenance", {}).get("reference_xy_blocked") != "false":
        raise ValueError("Rust-exported technical_mean with an unblocked reference audit is required")
    # Partition filter precedes any target/metadata/X access.
    rows = [{**r, "independence_group": r["metadata"]["validation_component_id"]}
            for r in task["observations"] if r["partition"] == "train" and r.get("y") is not None]
    rows.sort(key=lambda r: r["physical_sample_id"])
    if not rows or len({r["physical_sample_id"] for r in rows}) != len(rows):
        raise ValueError("One complete physical mean per development ID required")
    if any(not math.isfinite(r["y"]) or not r["x"] or any(x is None or not math.isfinite(x) for x in r["x"]) for r in rows):
        raise ValueError("Finite complete development X/Y required")
    return rows


def validate_folds(rows, folds):
    import dag_ml
    dag_ml.validate_fold_set_json(json.dumps(folds))
    by_id = {r["physical_sample_id"]: r for r in rows}
    if set(folds["sample_ids"]) != set(by_id):
        raise ValueError("Fold population differs from development population")
    valid = []
    for fold in folds["folds"]:
        train_ids, valid_ids = fold["train_sample_ids"], fold["validation_sample_ids"]
        if set(train_ids) & set(valid_ids) or set(train_ids) | set(valid_ids) != set(by_id):
            raise ValueError("Invalid outer fold population")
        train_groups = {by_id[s]["independence_group"] for s in train_ids}
        valid_groups = {by_id[s]["independence_group"] for s in valid_ids}
        if train_groups & valid_groups:
            raise ValueError("Dependency component spans training and validation")
        valid.extend(valid_ids)
    if Counter(valid) != Counter(by_id.keys()):
        raise ValueError("Every physical ID must have exactly one OOF prediction")


def audit_factors(rows, factors, folds):
    """Metadata-only audit: this function never inspects a target value."""
    validate_folds(rows, folds)
    by_id = {r["physical_sample_id"]: r for r in rows}
    result = []
    for specification in factors:
        factor = specification["field"]
        levels, components = {}, {}
        for row in rows:
            level = row["metadata"].get(factor)
            components.setdefault(row["independence_group"], set()).add(level)
            if level:
                levels.setdefault(level, []).append(row)
        overlap = []
        seen_ids = []
        for fold in folds["folds"]:
            train_levels = {by_id[s]["metadata"].get(factor) for s in fold["train_sample_ids"]} - {None, ""}
            seen = [s for s in fold["validation_sample_ids"] if by_id[s]["metadata"].get(factor) in train_levels]
            seen_ids.extend(seen)
            overlap.append({"fold_id": fold["fold_id"], "training_levels": sorted(train_levels),
                            "validation_levels": sorted({by_id[s]["metadata"].get(factor) for s in fold["validation_sample_ids"]} - {None, ""}),
                            "seen_ids": seen, "fallback_ids": [s for s in fold["validation_sample_ids"] if s not in seen]})
        support = [{"level": k, "n_samples": len(v), "n_components": len({r["independence_group"] for r in v})}
                   for k,v in sorted(levels.items())]
        eligible = (sum(v["n_components"] >= 3 for v in support) >= 2 and len(seen_ids) >= 20
                    and len({by_id[s]["independence_group"] for s in seen_ids}) >= 10
                    and specification["available_at_prediction"])
        result.append({**specification, "n_levels": len(levels), "level_support": support,
                       "missing_ids": [r["physical_sample_id"] for r in rows if not r["metadata"].get(factor)],
                       "singleton_levels": [v["level"] for v in support if v["n_samples"] == 1],
                       "rare_levels": [v["level"] for v in support if v["n_components"] < 3],
                       "components_spanning_levels": sorted(k for k,v in components.items() if len(v)>1),
                       "outer_overlap": overlap, "seen_count": len(seen_ids),
                       "fallback_fraction": 1-len(seen_ids)/len(rows), "eligible_conditional_evidence": eligible,
                       "eligibility_reason": None if eligible else "INSUFFICIENT_SEEN_LEVEL_OR_INDEPENDENT_COMPONENT_SUPPORT",
                       "scope": "observed metadata levels under declared component holdout; no causal attribution"})
    return result


def score_oof(oof, prediction, target="y"):
    from n4m.metrics.scoring import rmse, mae, r2
    if len(oof)<2:
        return state(reason="FEWER_THAN_TWO_MATCHED_OOF_UNITS", status="insufficient_data")
    truth, pred = [r[target] for r in oof], [r[prediction] for r in oof]
    values = {k: float(fn(truth, pred)) for k,fn in (("rmse",rmse),("mae",mae),("r2",r2))}
    return state({k: state(v) if math.isfinite(v) else state(reason="NATIVE_UNDEFINED_CONSTANT_TARGET") for k,v in values.items()})


def paired_bootstrap(oof, draws, seed):
    from n4m.metrics.scoring import rmse
    groups = {}
    for row in oof:
        groups.setdefault(row["component_id"], []).append(row)
    keys = sorted(groups)
    rng = random.Random(seed)
    records, values = [], []
    for draw in range(draws):
        sampled = [rng.choice(keys) for _ in keys]
        sample = [r for k in sampled for r in groups[k]]
        try:
            y = [r["y"] for r in sample]
            errors = {k: float(rmse(y, [r[k] for r in sample])) for k in ("null", "group_only", "spectral", "group_plus_residual")}
            value = {"group_over_null": errors["null"]-errors["group_only"],
                     "spectral_over_null": errors["null"]-errors["spectral"],
                     "residual_over_group": errors["group_only"]-errors["group_plus_residual"]}
            if not all(map(math.isfinite, value.values())):
                raise ValueError("NONFINITE_NATIVE_METRIC")
            values.append(value)
            records.append({"draw": draw, "components": sampled, **state(value)})
        except (RuntimeError, ValueError) as error:
            records.append({"draw": draw, "components": sampled, **state(reason=str(error), status="error")})
    intervals = None
    if len(values)>=100 and len(keys)>=10:
        intervals = {k: [sorted(v[k] for v in values)[math.ceil(q*len(values))-1] for q in (.025,.975)] for k in values[0]}
    return {"seed": seed, "requested": draws, "successful": len(values), "failed": draws-len(values),
            "interval_95": state(intervals) if intervals is not None else state(reason="REQUIRES_100_SUCCESSFUL_DRAWS_AND_10_COMPONENTS"),
            "conditioning": "paired frozen OOF predictions; whole components with replacement; excludes model-refit uncertainty",
            "draws": records}


def predictive_dependence(task, library, factor_audit, *, seed=17, outer_folds=5, inner_folds=3, max_components=5, draws=200, spectral=None):
    from n4m._ffi import library_path
    if version("dag-ml")!="0.3.41" or version("nirs4all-methods")!="1.3.6" or Path(library).resolve()!=Path(library_path()).resolve():
        raise ValueError("Qualified Methods 1.3.6 / DAG-ML 0.3.41 and identical library required")
    rows = development_rows(task)
    if draws<0 or draws>1000 or len(rows)>10_000 or len(rows)*draws>2_000_000:
        raise ValueError("Dependence resampling budget exceeded")
    spectral = spectral or _nested(rows, library, seed, outer_folds, inner_folds, max_components)
    folds = spectral["outer_fold_set"]
    validate_folds(rows, folds)
    by_id = {r["physical_sample_id"]: r for r in rows}
    # Recompute the audit so callers cannot supply favorable or mismatched overlap.
    audit = audit_factors(rows, [factor_audit], folds)[0]
    factor = audit["field"]
    predictions, lineage = {}, []
    for fold in folds["folds"]:
        train, valid = ([by_id[s] for s in fold[key]] for key in ("train_sample_ids", "validation_sample_ids"))
        baseline = group_means(train, factor)
        model, evidence = _inner_fit(train, library, seed, inner_folds, max_components, fold["fold_id"]+":inner", residual_factor=factor)
        if baseline != evidence["outer_training_baseline"]:
            raise RuntimeError("Residual REFIT baseline must match the outer-train baseline")
        corrections = model.predict([r["x"] for r in valid]).reshape(-1).tolist()
        for row, correction in zip(valid, corrections, strict=True):
            g, source = group_prediction(row, baseline, factor)
            predictions[row["physical_sample_id"]] = {"fold_id": fold["fold_id"], "factor_level": row["metadata"].get(factor),
                "group_only": g, "null": baseline["global"], "group_plus_residual": g+correction,
                "residual_correction": correction, "residual_truth": row["y"]-g, "baseline_source": source}
        lineage.append({**fold, **evidence})
    old = {r["physical_sample_id"]: r for r in spectral["oof"]}
    if set(old)!=set(by_id) or set(predictions)!=set(by_id):
        raise ValueError("Matched OOF identities differ across models")
    oof = [{"physical_sample_id": s, "component_id": by_id[s]["independence_group"], "y": by_id[s]["y"],
            "spectral": old[s]["prediction"], **predictions[s]} for s in sorted(by_id)]
    if any(r["null"]!=old[r["physical_sample_id"]]["null_prediction"] or r["y"]!=old[r["physical_sample_id"]]["y"] for r in oof):
        raise ValueError("Original spectral experiment population or target differs")
    scores = {k: score_oof(oof,k) for k in ("null","group_only","spectral","group_plus_residual")}
    seen = [r for r in oof if r["baseline_source"]=="level_training_mean"]
    conditional = state({"n_samples":len(seen),"n_components":len({r["component_id"] for r in seen}),
                         "original_unit_metrics":{k:score_oof(seen,k) for k in ("group_only","group_plus_residual")},
                         "residual_target_metrics":score_oof(seen,"residual_correction","residual_truth"),
                         "paired_uncertainty":paired_bootstrap(seen,draws,seed),
                         "denominator":"seen-level OOF only; residual R2 uses Y minus the fold training baseline"}) if audit["eligible_conditional_evidence"] else state(reason=audit["eligibility_reason"])
    gain = scores["group_only"]["value"]["rmse"]["value"]-scores["group_plus_residual"]["value"]["rmse"]["value"]
    uncertainty=paired_bootstrap(oof,draws,seed)
    group_gain=scores["null"]["value"]["rmse"]["value"]-scores["group_only"]["value"]["rmse"]["value"]
    return {"factor":factor,"audit":audit,"scores":scores,"oof":oof,"outer_fold_set":folds,
            "lineage":lineage,"spectral_lineage":spectral["lineage"],
            "prediction.group_only":state(scores["group_only"]),"prediction.spectral":state(scores["spectral"]),
            "prediction.within_group_incremental_skill":conditional,
            "paired_rmse_improvement_over_group":gain,"uncertainty":uncertainty,
            "prediction.structural_dependence_evidence":state({"confidence":"exploratory",
                "observation": "All levels unseen: group-only is the global fallback; group mediation remains unidentified." if not seen else "Matched group and residual spectral OOF predictions quantify conditional development gains.",
                "group_over_null_rmse_improvement":group_gain,"residual_over_group_rmse_improvement":gain,
                "seen_samples":len(seen),"fallback_fraction":audit["fallback_fraction"],
                "conditional_support_eligible":audit["eligible_conditional_evidence"],
                "paired_frozen_oof_intervals":uncertainty["interval_95"],
                "consequence":"No fraction of performance attributable to chemistry or shortcut learning is identified.",
                "action":"Inspect factor overlap and independent support before split-stress experiments."}),
            "cluster_derived_prediction":state(reason="NO_QUALIFIED_PUBLIC_FOLD_LOCAL_HDBSCAN_ASSIGNMENT_API")}


def audit_representation(task, binary, library, output):
    """Shared Rust audit/mean transport, preserving original singleton floats."""
    import copy
    task=copy.deepcopy(task)
    for row in task["observations"]:
        if row["partition"]=="test":row["y"]=None;row["category"]=None
    task["policy"]["audit_mode"]="pre_training"
    input_path=output/"sanitized-task.json";represented=output/"mean-task.json"
    input_path.write_text(json.dumps(task,allow_nan=False))
    subprocess.run([str(binary),"represent",str(input_path),"--out",str(represented),"--methods-library",str(library)],check=True)
    audited=json.loads(represented.read_text())
    if len({r["physical_sample_id"] for r in task["observations"]})==len(task["observations"]):
        original={r["physical_sample_id"]:r for r in task["observations"]}
        if set(original)!={r["physical_sample_id"] for r in audited["observations"]}:
            raise ValueError("Rust audit excluded an input physical unit")
        for row in audited["observations"]:
            source=original[row["physical_sample_id"]]
            if row["observation_id"]!=source["observation_id"] or row["partition"]!=source["partition"]:
                raise ValueError("Rust audit changed singleton identities or partitions")
            row["x"]=source["x"];row["y"]=source.get("y")
    represented.write_text(json.dumps(audited,allow_nan=False),encoding="utf-8")
    return audited


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--methods-library", type=Path, required=True)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    import jsonschema
    config = json.loads(args.config.read_text())
    schema = Path(__file__).with_name("dependence-config.v1.schema.json")
    jsonschema.validate(config,json.loads(schema.read_text()))
    if len({f["field"] for f in config["factors"]})!=len(config["factors"]):
        raise ValueError("Duplicate factor fields")
    args.out.mkdir(parents=True,exist_ok=False)
    binary = os.environ.get("N4DOMAINS_BIN", "n4domains")
    represented=args.out/"mean-task.json"
    task=audit_representation(json.loads(args.task.read_text()),binary,args.methods_library,args.out)
    rows=development_rows(task)
    folds=group_folds(rows,config["outer_folds"],config["seed"],"outer")
    audit=audit_factors(rows,config["factors"],folds)
    write=lambda path,value:path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    write(args.out/"factor-audit.json",{"protocol_version":PROTOCOL,"context":task["context"],"test_target_accessed":False,
        "development_ids":[r["physical_sample_id"] for r in rows],"outer_fold_set":folds,"factors":audit})
    if args.audit_only:return
    spectral=_nested(rows,args.methods_library,config["seed"],config["outer_folds"],config["inner_folds"],config["max_components"])
    write(args.out/"spectral.json",spectral)
    results=[]
    for specification in audit:
        factor=specification["field"]
        association_path=args.out/(factor+"-association.json")
        subprocess.run([binary,"group-target",str(represented),"--factor",factor,"--out",str(association_path),
            "--draws",str(config["draws"]),"--seed",str(config["seed"]),"--methods-library",str(args.methods_library)],check=True)
        result=predictive_dependence(task,args.methods_library,specification,**{k:config[k] for k in ("seed","outer_folds","inner_folds","max_components","draws")},spectral=spectral)
        result["target.group_association"]=json.loads(association_path.read_text())
        write(args.out/(factor+"-report.json"),result)
        results.append(result)
        print(f"Completed {factor}",flush=True)
    report={"protocol_version":PROTOCOL,"test_target_accessed":False,"context":task["context"],"target_unit":task.get("target_unit"),
        "development_input_sha256":fingerprint(rows),"config":config,"n_samples":len(rows),"n_components":len({r["independence_group"] for r in rows}),
        "engine_versions":{n:version(n) for n in ("dag-ml","nirs4all-methods","nirs4all-domains-bridge")},"factors":results}
    write(args.out/"report.json",report)
    lines=["# Structural dependence experiment", "", f"Protocol: `{PROTOCOL}`. Development only; retained targets accessed: false.", "",
           f"Population: {report['n_samples']} physical means / {report['n_components']} declared components. Target unit: {report['target_unit']}.", "",
           "| Factor | Eta squared | Group RMSE | Spectral RMSE | Group + residual RMSE | Fallback fraction |", "|---|---:|---:|---:|---:|---:|"]
    for f in results:
        a=f["target.group_association"]["association"]["value"]
        eta=a["eta_squared"] if a else "unavailable"
        errors=[f["scores"][k]["value"]["rmse"]["value"] for k in ("group_only","spectral","group_plus_residual")]
        lines.append(f"| {f['factor']} | {eta} | {errors[0]:.6f} | {errors[1]:.6f} | {errors[2]:.6f} | {f['audit']['fallback_fraction']:.6f} |")
    lines.extend(["", "Association uses complete factor/target units; all four prediction models use the same development population. Inspect the JSON for excluded IDs, seen-level conditional metrics, paired component intervals and every native fit scope.", "", "These exploratory findings do not identify causal chemistry or a shortcut probability. Unseen levels use the training global mean. HDBSCAN-derived prediction is unavailable."])
    (args.out/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":main()
