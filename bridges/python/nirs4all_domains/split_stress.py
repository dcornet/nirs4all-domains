"""Bounded alpha.7 split/target experiments over the qualified native bridge."""
from collections import Counter, defaultdict
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import random

from .dependence import development_rows, state, validate_folds, score_oof
from .interventions import components, exchangeability, intervene
from .predictive import fingerprint, group_folds, group_means, group_prediction, native_summary, _inner_fit

PROTOCOL = "domains.split_stress.v0.1"
MODELS = ("null", "group_only", "spectral", "group_plus_residual")


def stress_rows(task):
    # A partial target vector cannot stand in for a complete dependency block.
    missing=[r["physical_sample_id"] for r in task["observations"] if r["partition"]=="train" and r.get("y") is None]
    if missing:raise ValueError("ALPHA7_REQUIRES_COMPLETE_DEVELOPMENT_COMPONENT_TARGET_VECTORS:"+",".join(sorted(missing)))
    return development_rows(task)


def factor_holdout(rows, factor, outer_folds=5, inner_folds=3, seed=17):
    """Transitive component closure over observed metadata levels, never Y."""
    blocks = components(rows)
    parent = {g:g for g in blocks}
    def find(g):
        while parent[g]!=g:
            parent[g]=parent[parent[g]];g=parent[g]
        return g
    levels = {}
    for group, members in blocks.items():
        for row in members:
            level = row["metadata"].get(factor)
            if level:
                if level in levels:
                    a,b=find(group),find(levels[level]);parent[max(a,b)]=min(a,b)
                else:levels[level]=group
    closures = defaultdict(list)
    for group in blocks:closures[find(group)].append(group)
    aliases = {group:"closure:"+fingerprint(sorted(members)) for members in closures.values() for group in members}
    inventory = [{"closure_id":aliases[groups[0]],"components":groups,
                  "physical_ids":sorted(r["physical_sample_id"] for g in groups for r in blocks[g]),
                  "factor_levels":sorted({r["metadata"].get(factor) for g in groups for r in blocks[g]}-{None,""})}
                 for _,groups in sorted(closures.items())]
    result = {"factor":factor,"n_original_components":len(blocks),"n_closure_units":len(closures),"closures":inventory,
              "effective_outer_folds":min(outer_folds,len(closures))}
    if len(levels)<2:
        return {**result,**state(reason="FEWER_THAN_TWO_OBSERVED_FACTOR_LEVELS")}
    if len(closures)<2:
        return {**result,**state(reason="FACTOR_CLOSURE_LEAVES_FEWER_THAN_TWO_OUTER_UNITS")}
    renamed = [{**r,"independence_group":aliases[r["independence_group"]]} for r in rows]
    folds = group_folds(renamed,min(outer_folds,len(closures)),seed,"holdout:"+factor)
    validate_folds(rows,folds)
    by_id={r["physical_sample_id"]:r for r in rows}
    for fold in folds["folds"]:
        train,valid=([by_id[s] for s in fold[key]] for key in ("train_sample_ids","validation_sample_ids"))
        if len(components(train))<inner_folds:
            return {**result,**state(reason="FACTOR_HOLDOUT_HAS_INSUFFICIENT_INNER_COMPONENTS")}
        a={r["metadata"].get(factor) for r in train}-{None,""}
        b={r["metadata"].get(factor) for r in valid}-{None,""}
        if a&b:raise ValueError("Actual factor levels cross holdout")
    return {**result,**state(folds)}


def intervention_audit(rows, folds, config, kind):
    """Eligibility for every scheduled outer REFIT and inner FIT_CV scope."""
    by_id={r["physical_sample_id"]:r for r in rows}
    scopes=[]
    for outer in folds["folds"]:
        train=[by_id[s] for s in outer["train_sample_ids"]]
        inner=group_folds(train,config["inner_folds"],config["seed"],outer["fold_id"]+":inner")
        for scope,ids in [(outer["fold_id"]+":refit",outer["train_sample_ids"])]+[(f["fold_id"],f["train_sample_ids"]) for f in inner["folds"]]:
            audit=exchangeability([by_id[s] for s in ids],kind,config["factor"],config["min_swappable_fraction"],config["min_swappable_components"])
            scopes.append({"scope_id":scope,"training_ids":ids,**audit})
    failures=[s["scope_id"] for s in scopes if not s["eligible"]]
    return {"kind":kind,"factor":config["factor"],"scopes":scopes,"failed_scopes":failures,
            "eligible":not failures,"reason":None if not failures else "INTERVENTION_INADMISSIBLE_OR_LOW_POWER_IN_REQUIRED_TRAINING_SCOPE"}


def overlap(train, valid, factor):
    levels={r["metadata"].get(factor) for r in train}-{None,""}
    seen=[r["physical_sample_id"] for r in valid if r["metadata"].get(factor) in levels]
    return {"training_levels":sorted(levels),"validation_levels":sorted({r["metadata"].get(factor) for r in valid}-{None,""}),
            "training_level_support":[{"level":level,"n_samples":sum(r["metadata"].get(factor)==level for r in train),
                "n_components":len({r["independence_group"] for r in train if r["metadata"].get(factor)==level})} for level in sorted(levels)],
            "seen_ids":seen,"fallback_ids":[r["physical_sample_id"] for r in valid if r["physical_sample_id"] not in seen]}


def fit_outer(train, valid, library, config, scope, intervention=None):
    """Reuse native inner SELECT/REFIT; validation targets enter only after prediction."""
    factor=config["factor"]
    inner=group_folds(train,config["inner_folds"],config["seed"],scope+":inner")
    if any(len(f["train_sample_ids"])<config["max_components"]+2 for f in inner["folds"]):
        raise ValueError("INNER_TRAIN_TOO_SMALL_FOR_FROZEN_COMPONENT_GRID")
    fitted,receipt=intervention(train) if intervention else (train,None)
    baseline=group_means(fitted,factor)
    spectral,spectral_lineage=_inner_fit(train,library,config["seed"],config["inner_folds"],config["max_components"],scope+":inner",training_intervention=intervention)
    residual,residual_lineage=_inner_fit(train,library,config["seed"],config["inner_folds"],config["max_components"],scope+":inner",residual_factor=factor,training_intervention=intervention)
    if residual_lineage["outer_training_baseline"]!=baseline:
        raise ValueError("Outer REFIT target baseline differs across models")
    if intervention:
        expected=fingerprint(receipt)
        if spectral_lineage["outer_intervention_sha256"]!=expected or residual_lineage["outer_intervention_sha256"]!=expected:
            raise ValueError("Models did not use the same training-only target map")
    x=[r["x"] for r in valid]
    sp=spectral.predict(x).reshape(-1).tolist()
    corrections=residual.predict(x).reshape(-1).tolist()
    # Original validation targets are first used here, after native prediction.
    rows=[]
    for row,p,c in zip(valid,sp,corrections,strict=True):
        group,source=group_prediction(row,baseline,factor)
        rows.append({"physical_sample_id":row["physical_sample_id"],"component_id":row["independence_group"],
            "fold_id":scope,"y":row["y"],"null":baseline["global"],"group_only":group,
            "spectral":p,"group_plus_residual":group+c,"baseline_source":source})
    lineage={"fold_id":scope,"train_sample_ids":[r["physical_sample_id"] for r in train],
        "validation_sample_ids":[r["physical_sample_id"] for r in valid],"n_train_samples":len(train),
        "n_train_components":len(components(train)),"n_validation_samples":len(valid),
        "n_validation_components":len(components(valid)),"factor_overlap":overlap(train,valid,factor),
        "spectral":spectral_lineage,"residual":residual_lineage,
        "original_training_target_summary":native_summary(r["y"] for r in train),
        "validation_target_summary_post_evaluation":native_summary(r["y"] for r in valid)}
    return rows,lineage


def y_range_diagnostics(oof, lineage):
    by_fold={s["fold_id"]:s for s in lineage}
    inside,outside=[],[]
    for row in oof:
        summary=by_fold[row["fold_id"]]["original_training_target_summary"]
        (inside if summary["min"]<=row["y"]<=summary["max"] else outside).append(row)
    population=lambda rr:{"ids":[r["physical_sample_id"] for r in rr],"n_samples":len(rr),
        "n_components":len({r["component_id"] for r in rr}),"scores":{k:score_oof(rr,k) for k in MODELS}}
    return {"selection":"post-evaluation original development Y only; no split/model selection; all primary outcomes retained",
        "outside_training_range_fraction":len(outside)/len(oof),"within_range":population(inside),"outside_range":population(outside)}


def summarize(oof, lineage, folds=None):
    oof=sorted(oof,key=lambda r:r["physical_sample_id"])
    if len({r["physical_sample_id"] for r in oof})!=len(oof):raise ValueError("Duplicate OOF identities")
    return {"oof":oof,"n_samples":len(oof),"n_components":len({r["component_id"] for r in oof}),
        "scores":{k:score_oof(oof,k) for k in MODELS},"lineage":lineage,"outer_fold_set":folds,
        "y_range":y_range_diagnostics(oof,lineage)}


def run_design(rows, folds, library, config, intervention=None):
    validate_folds(rows,folds)
    by_id={r["physical_sample_id"]:r for r in rows}
    oof,lineage=[],[]
    for fold in folds["folds"]:
        train,valid=([by_id[s] for s in fold[key]] for key in ("train_sample_ids","validation_sample_ids"))
        try:
            predicted,evidence=fit_outer(train,valid,library,config,fold["fold_id"],intervention)
        except Exception as error:
            raise RuntimeError(f"{fold['fold_id']}:{type(error).__name__}:{error}") from error
        oof.extend(predicted);lineage.append(evidence)
    return summarize(oof,lineage,folds)


def paired_comparison(reference, candidate, draws=500, seed=17):
    """Identity-matched metrics and component bootstrap of frozen predictions."""
    from n4m.metrics.scoring import rmse
    a={r["physical_sample_id"]:r for r in reference["oof"]}
    b={r["physical_sample_id"]:r for r in candidate["oof"]}
    ids=sorted(a.keys()&b.keys())
    if len(ids)<2:return state(reason="FEWER_THAN_TWO_MATCHED_EVALUATION_IDS")
    if any(a[s]["y"]!=b[s]["y"] or a[s]["component_id"]!=b[s]["component_id"] for s in ids):
        raise ValueError("Paired OOF identity/truth mismatch")
    metric=lambda src,k,selected:float(rmse([a[s]["y"] for s in selected],[src[s][k] for s in selected]))
    point={k:metric(b,k,ids)-metric(a,k,ids) for k in MODELS}
    gain=lambda src,k,selected:metric(src,"null",selected)-metric(src,k,selected)
    gain_change={k:gain(b,k,ids)-gain(a,k,ids) for k in MODELS}
    groups=defaultdict(list)
    for sid in ids:groups[a[sid]["component_id"]].append(sid)
    keys=sorted(groups);rng=random.Random(seed);replicas=[];valid=[];valid_gain=[]
    for draw in range(draws):
        sampled=[rng.choice(keys) for _ in keys]
        selected=[sid for g in sampled for sid in groups[g]]
        try:
            value={k:metric(b,k,selected)-metric(a,k,selected) for k in MODELS}
            gain_value={k:gain(b,k,selected)-gain(a,k,selected) for k in MODELS}
            if not all(map(math.isfinite,value.values())):raise ValueError("NONFINITE_NATIVE_COMPARISON")
            valid.append(value);valid_gain.append(gain_value);replicas.append({"draw":draw,"components":sampled,**state(value),"gain_change":gain_value})
        except (ValueError,RuntimeError) as error:replicas.append({"draw":draw,"components":sampled,**state(reason=str(error),status="error")})
    intervals={k:[sorted(v[k] for v in valid)[math.ceil(q*len(valid))-1] for q in (.025,.975)] for k in MODELS} if len(valid)>=100 and len(keys)>=10 else None
    gain_intervals={k:[sorted(v[k] for v in valid_gain)[math.ceil(q*len(valid_gain))-1] for q in (.025,.975)] for k in MODELS} if len(valid_gain)>=100 and len(keys)>=10 else None
    return state({"matched_ids":ids,"n_samples":len(ids),"n_components":len(keys),"reference_only_ids":sorted(a.keys()-b.keys()),
        "candidate_only_ids":sorted(b.keys()-a.keys()),"paired_all_development":set(a)==set(b),
        "reference_scores":{k:score_oof([a[s] for s in ids],k) for k in MODELS},
        "candidate_scores":{k:score_oof([b[s] for s in ids],k) for k in MODELS},
        "rmse_change_candidate_minus_reference":point,"gain_change_relative_to_own_null":gain_change,
        "uncertainty":{"seed":seed,"requested":draws,"successful":len(valid),"failed":draws-len(valid),
            "interval_95":state(intervals) if intervals else state(reason="REQUIRES_100_SUCCESSFUL_DRAWS_AND_10_COMPONENTS"),
            "gain_change_interval_95":state(gain_intervals) if gain_intervals else state(reason="REQUIRES_100_SUCCESSFUL_DRAWS_AND_10_COMPONENTS"),
            "conditioning":"paired frozen OOF; declared whole components with replacement; excludes refit uncertainty","draws":replicas}})


def size_match_rows(pool, target, seed, draw, max_gap=2):
    blocks=components(pool);order=sorted(blocks)
    random.Random(int(fingerprint([seed,draw,order,target]),16)).shuffle(order)
    if len(pool)<target:return {**state(reason="REFERENCE_TRAIN_POOL_SMALLER_THAN_FACTOR_HOLDOUT_TRAIN"),"target_samples":target,"pool_samples":len(pool)}
    chosen=[];count=0
    for key in order:
        if count+len(blocks[key])<=target:chosen.append(key);count+=len(blocks[key])
    selected=[r for r in pool if r["independence_group"] in chosen]
    if target-count>max_gap:return {**state(reason="WHOLE_COMPONENT_GRANULARITY_EXCEEDS_MATCH_TOLERANCE"),"target_samples":target,"matched_samples":count}
    return {**state(selected),"target_samples":target,"pool_samples":len(pool),"matched_samples":count,
            "matched_components":len(chosen),"sample_gap":target-count,"exact_match":target==count,"chosen_components":chosen}


def run_size_controls(rows, reference_folds, holdout, holdout_result, reference_result, library, config):
    by_id={r["physical_sample_id"]:r for r in rows}
    draws=[]
    for draw in range(config["size_draws"]):
        predictions,lineage,cells=[],[],[]
        for h in holdout["folds"]:
            for r in reference_folds["folds"]:
                valid_ids=sorted(set(h["validation_sample_ids"])&set(r["validation_sample_ids"]))
                if not valid_ids:continue
                pool=[by_id[s] for s in r["train_sample_ids"]]
                scope=f"size:{draw}:{h['fold_id']}:{r['fold_id']}"
                matched=size_match_rows(pool,len(h["train_sample_ids"]),int(fingerprint([config["seed"],scope]),16),draw,config["size_max_gap"])
                record={k:v for k,v in matched.items() if k!="value"}
                record["value"]=None
                record.update(scope_id=scope,validation_ids=valid_ids,reference_fold=r["fold_id"],factor_holdout_fold=h["fold_id"])
                record.update(pool_components=len(components(pool)),target_components=len({by_id[s]["independence_group"] for s in h["train_sample_ids"]}),
                    matching_seed_sha256=fingerprint([config["seed"],scope]))
                if matched["status"]=="computed":
                    try:
                        pred,evidence=fit_outer(matched["value"],[by_id[s] for s in valid_ids],library,config,scope)
                        predictions.extend(pred);lineage.append(evidence)
                        record["training_ids"]=[x["physical_sample_id"] for x in matched["value"]]
                        record["value"]={"training_ids":record["training_ids"]}
                    except Exception as error:
                        record.update(status="error",reason=f"{type(error).__name__}:{error}",value=None)
                cells.append(record)
        if predictions:
            result=summarize(predictions,lineage)
            draws.append({"draw":draw,"cells":cells,**state(result),
                "versus_factor_holdout":paired_comparison(holdout_result,result,config["bootstrap_draws"],config["seed"]),
                "versus_original_reference":paired_comparison(reference_result,result,config["bootstrap_draws"],config["seed"])})
        else:draws.append({"draw":draw,"cells":cells,**state(reason="NO_ELIGIBLE_SIZE_MATCHED_EVALUATION_CELLS")})
    return {"matching_rule":"reference R train subsample targeting H train count; evaluate H-validation intersect R-validation; whole components only",
            "max_sample_gap":config["size_max_gap"],"requested_draws":config["size_draws"],"draws":draws}


def frozen_reference(rows, config, report):
    if report["development_input_sha256"]!=fingerprint(rows):raise ValueError("Frozen alpha.6 development input differs")
    if report["engine_versions"]["dag-ml"]!=version("dag-ml") or report["engine_versions"]["nirs4all-methods"]!=version("nirs4all-methods"):
        raise ValueError("Frozen reference native provider versions differ")
    if any(report["config"][key]!=config[key] for key in ("seed","outer_folds","inner_folds","max_components")):
        raise ValueError("Frozen reference model/split parameters differ")
    original=next(f for f in report["factors"] if f["factor"]==config["factor"])
    folds=group_folds(rows,config["outer_folds"],config["seed"],"outer")
    if original["outer_fold_set"]!=folds:raise ValueError("Frozen alpha.6 outer folds differ")
    validate_folds(rows,folds)
    by_id={r["physical_sample_id"]:r for r in rows};lineage=[]
    for outer in folds["folds"]:
        train,valid=([by_id[s] for s in outer[k]] for k in ("train_sample_ids","validation_sample_ids"))
        lineage.append({**outer,"n_train_samples":len(train),"n_train_components":len(components(train)),
            "n_validation_samples":len(valid),"n_validation_components":len(components(valid)),
            "factor_overlap":overlap(train,valid,config["factor"]),
            "original_training_target_summary":native_summary(r["y"] for r in train),
            "validation_target_summary_post_evaluation":native_summary(r["y"] for r in valid),
            "frozen_alpha6_residual_lineage":next(s for s in original["lineage"] if s["fold_id"]==outer["fold_id"]),
            "frozen_alpha6_spectral_lineage":next(s for s in original["spectral_lineage"] if s["fold_id"]==outer["fold_id"])})
    result=summarize([{k:r[k] for k in ("physical_sample_id","component_id","fold_id","y",*MODELS,"baseline_source")} for r in original["oof"]],lineage,folds)
    if result["scores"]!=original["scores"]:raise ValueError("Frozen original metrics changed")
    result["reuse"]="exact frozen alpha.6 OOF, folds and lineage; no model rerun"
    return result


def design_audit(rows, config):
    reference=group_folds(rows,config["outer_folds"],config["seed"],"outer")
    factors={factor:factor_holdout(rows,factor,config["outer_folds"],config["inner_folds"],config["seed"]) for factor in config["audit_factors"]}
    interventions={kind:intervention_audit(rows,reference,config,kind) for kind in config["interventions"]}
    date_area=Counter((r["metadata"].get("sampling_date"),r["metadata"].get("plot_name","").split("_")[0]) for r in rows if r["metadata"].get("sampling_date"))
    return {"protocol_version":PROTOCOL,"test_target_accessed":False,"n_samples":len(rows),"n_components":len(components(rows)),
        "reference_fold_set":reference,"reference_folds_sha256":fingerprint(reference),"factor_holdouts":factors,"interventions":interventions,
        "date_area_audit":{"source":"EcoSIS original guide defines plot_name greater-area codes; no coordinate bins or new predictor",
            "counts":[{"sampling_date":d,"source_area_code":a,"n":n} for (d,a),n in sorted(date_area.items())]},
        "scheduled_holdout_factors":config["holdout_factors"],"audit_only_factors":sorted(set(config["audit_factors"])-set(config["holdout_factors"]))}


def run_experiments(task, library, config, audit, reference_report=None, progress=None):
    rows=stress_rows(task)
    if version("dag-ml")!="0.3.41" or version("nirs4all-methods")!="1.3.6":raise ValueError("Qualified native versions required")
    from n4m._ffi import library_path
    if Path(library).resolve()!=Path(library_path()).resolve():raise ValueError("DAG and artifact replay library mismatch")
    if fingerprint(audit)!=fingerprint(design_audit(rows,config)):raise ValueError("Pre-experiment audit differs from current design")
    reference=frozen_reference(rows,config,reference_report) if reference_report else run_design(rows,audit["reference_fold_set"],library,config)
    experiments=[{"design_id":"reference:17","kind":"reference","seed":config["seed"],**state(reference)}]
    def done(label):
        if progress:progress(label)
    done("reference")
    for seed in config["sensitivity_seeds"]:
        folds=group_folds(rows,config["outer_folds"],seed,"outer")
        try:
            result=run_design(rows,folds,library,{**config,"seed":seed})
            experiments.append({"design_id":f"reference:{seed}","kind":"reference_sensitivity","seed":seed,**state(result),
                "comparison":paired_comparison(reference,result,config["bootstrap_draws"],config["seed"])})
        except Exception as error:experiments.append({"design_id":f"reference:{seed}","kind":"reference_sensitivity","seed":seed,**state(reason=f"{type(error).__name__}:{error}",status="error"),"outer_fold_set":folds})
        done(f"reference seed {seed}")
    if config["shuffle_reference"]:
        folds=group_folds(rows,config["outer_folds"],config["seed"],"shuffle",allocation="shuffle")
        try:
            result=run_design(rows,folds,library,config)
            experiments.append({"design_id":"shuffle:17","kind":"component_shuffle","seed":config["seed"],**state(result),"comparison":paired_comparison(reference,result,config["bootstrap_draws"],config["seed"])})
        except Exception as error:experiments.append({"design_id":"shuffle:17","kind":"component_shuffle","seed":config["seed"],**state(reason=f"{type(error).__name__}:{error}",status="error")})
        done("component shuffle")
    for factor in config["holdout_factors"]:
        candidate=audit["factor_holdouts"][factor]
        record={"design_id":"holdout:"+factor,"kind":"factor_holdout","factor":factor,"seed":config["seed"]}
        if candidate["status"]!="computed":record.update(state(reason=candidate["reason"]))
        else:
            try:
                result=run_design(rows,candidate["value"],library,config)
                record.update(state(result),comparison=paired_comparison(reference,result,config["bootstrap_draws"],config["seed"]))
                if factor==config["factor"] and config["size_draws"]:
                    record["size_controls"]=run_size_controls(rows,audit["reference_fold_set"],candidate["value"],result,reference,library,config)
            except Exception as error:record.update(state(reason=f"{type(error).__name__}:{error}",status="error"))
        experiments.append(record);done("holdout "+factor)
    interventions=[]
    for kind in config["interventions"]:
        eligibility=audit["interventions"][kind]
        attempts=[]
        for attempt in range(config["intervention_attempts"]):
            record={"attempt":attempt,"kind":kind}
            if not eligibility["eligible"]:
                record.update(state(reason=eligibility["reason"]))
            else:
                def transformation(train, attempt=attempt, kind=kind):
                    return intervene(train,kind=kind,factor=config["factor"],seed=config["seed"],attempt=attempt,
                        min_fraction=config["min_swappable_fraction"],min_components=config["min_swappable_components"],min_changed_fraction=config["min_changed_target_fraction"])
                try:
                    result=run_design(rows,audit["reference_fold_set"],library,config,transformation)
                    receipts=[receipt for scope in result["lineage"] for model in ("spectral","residual") for receipt in scope[model]["intervention_scopes"].values()]
                    effective=all(r["effective"] for r in receipts)
                    record.update(state(result),effective=effective,power_reason=None if effective else "LOW_ACTUAL_TARGET_PERTURBATION_IN_AT_LEAST_ONE_FIT_SCOPE",
                        evidence_status="computed" if effective else "limited_evidence",
                        minimum_changed_target_fraction=min(r["changed_target_fraction"] for r in receipts),
                        comparison=paired_comparison(reference,result,config["bootstrap_draws"],config["seed"]))
                except Exception as error:record.update(state(reason=f"{type(error).__name__}:{error}",status="error"))
            attempts.append(record);done(f"{kind} attempt {attempt+1}/{config['intervention_attempts']}")
        interventions.append({"kind":kind,"requested":config["intervention_attempts"],"successful":sum(a["status"]=="computed" for a in attempts),
            "failed_or_unavailable":sum(a["status"]!="computed" for a in attempts),"effective_attempts":sum(a.get("effective",False) for a in attempts),"attempts":attempts})
    return {"protocol_version":PROTOCOL,"test_target_accessed":False,"context":task["context"],"target_unit":task.get("target_unit"),
        "input_provenance":{k:v for k,v in task.get("provenance",{}).items() if k!="representation_membership"},
        "development_input_sha256":fingerprint(rows),"n_samples":len(rows),"n_components":len(components(rows)),"config":config,
        "engine_versions":{n:version(n) for n in ("dag-ml","nirs4all-methods","nirs4all-domains-bridge")},"audit":audit,
        "experiments":experiments,"interventions":interventions,
        "findings":[{"observation":"Report matched evaluation IDs, size controls, target extrapolation and effective training perturbation separately.",
            "confidence":"exploratory","consequence":"No causal shortcut percentage is identified; weak or inadmissible interventions establish neither independence nor mediation.",
            "action":"Use conditional matched comparisons and report exchangeability/refit limitations before broader datasets."}],
        "cluster_derived_prediction":state(reason="NO_QUALIFIED_PUBLIC_FOLD_LOCAL_HDBSCAN_ASSIGNMENT_API")}


def main():
    import argparse,os
    from .dependence import audit_representation
    import jsonschema
    parser=argparse.ArgumentParser()
    parser.add_argument("task",type=Path);parser.add_argument("--config",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True);parser.add_argument("--methods-library",type=Path,required=True)
    parser.add_argument("--reference-report",type=Path);parser.add_argument("--audit-only",action="store_true")
    args=parser.parse_args();config=json.loads(args.config.read_text())
    jsonschema.validate(config,json.loads(Path(__file__).with_name("split-stress-config.v1.schema.json").read_text()))
    if not set(config["holdout_factors"])<=set(config["audit_factors"]) or config["factor"] not in config["audit_factors"]:
        raise ValueError("Predictor and holdout factors must be audited")
    args.out.mkdir(parents=True,exist_ok=False)
    task=audit_representation(json.loads(args.task.read_text()),os.environ.get("N4DOMAINS_BIN","n4domains"),args.methods_library,args.out)
    rows=stress_rows(task);audit=design_audit(rows,config)
    if len(rows)>500 or len(rows)*len(rows[0]["x"])>1_500_000:raise ValueError("Bounded split-stress population budget exceeded")
    write=lambda name,value:(args.out/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    write("design-audit.json",audit)
    if args.audit_only:return
    reference=json.loads(args.reference_report.read_text()) if args.reference_report else None
    report=run_experiments(task,args.methods_library,config,audit,reference_report=reference,progress=lambda s:print(s,flush=True))
    if args.reference_report:report["frozen_reference_file_sha256"]=hashlib.sha256(args.reference_report.read_bytes()).hexdigest()
    write("report.json",report)
    lines=["# Split stress and training-target interventions","",f"Protocol: `{PROTOCOL}`. Original development outcomes only; retained targets accessed: false.","",
        "| Design | Status | Samples | Spectral RMSE | Residual RMSE |","|---|---|---:|---:|---:|"]
    for e in report["experiments"]:
        if e["status"]=="computed":
            v=e["value"];scores=v["scores"]
            lines.append(f"| {e['design_id']} | computed | {v['n_samples']} | {scores['spectral']['value']['rmse']['value']:.6f} | {scores['group_plus_residual']['value']['rmse']['value']:.6f} |")
        else:lines.append(f"| {e['design_id']} | {e['status']}: {e['reason']} | — | — | — |")
    for intervention in report["interventions"]:lines.extend(["",f"{intervention['kind']}: {intervention['successful']}/{intervention['requested']} computed; {intervention['effective_attempts']} meet every fit scope's perturbation threshold."])
    lines.extend(["","Inspect JSON for closure, matched populations, size gaps, post-evaluation Y-range diagnostics, every target map/native fit scope and paired frozen-OOF uncertainty. A performance decline alone does not prove shortcut learning."])
    (args.out/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":main()
