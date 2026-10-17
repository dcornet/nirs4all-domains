"""Bounded scientific qualification and frozen EcoSIS execution; no old pilot reruns."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from check_split_stress_report import check
from nirs4all_domains.dependence import development_rows, score_oof, state
from nirs4all_domains.interventions import components, exchangeability, intervene
from nirs4all_domains.predictive import fingerprint
from nirs4all_domains.split_stress import (fit_outer, summarize, size_match_rows, paired_comparison, run_design)


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
def compact(v):
    if isinstance(v,list):return [compact(x) for x in v]
    if isinstance(v,dict):return {k:compact(x) for k,x in v.items() if k not in ("lineage","target_map","blocks","outer_fold_set","intervention_scopes") and not(k=="draws" and isinstance(x,list))}
    return v


def scientific_summary(report):
    result={"n_samples":report["n_samples"],"n_components":report["n_components"],"experiments":[],"interventions":[]}
    for e in report["experiments"]:
        entry={k:v for k,v in e.items() if k not in ("value","size_controls")}
        if e["value"]:
            v=e["value"];entry["value"]={k:v[k] for k in ("n_samples","n_components","scores","y_range")}
            entry["training_counts"]=[{"fold_id":s["fold_id"],"n_train":s["n_train_samples"],"components":s["n_train_components"],
                "n_valid":s["n_validation_samples"],"fallback":len(s["factor_overlap"]["fallback_ids"])} for s in v["lineage"]]
        else:entry["value"]=None
        if "size_controls" in e:
            entry["size_controls"]=[]
            for draw in e["size_controls"]["draws"]:
                entry["size_controls"].append({"draw":draw["draw"],"status":draw["status"],"reason":draw["reason"],
                    "n_samples":draw["value"]["n_samples"] if draw["value"] else None,
                    "computed_cells":sum(c["status"]=="computed" for c in draw["cells"]),
                    "failed_cells":[{k:c[k] for k in ("scope_id","status","reason","target_samples","pool_samples") if k in c} for c in draw["cells"] if c["status"]!="computed"],
                    "sample_gaps":[c["sample_gap"] for c in draw["cells"] if c["status"]=="computed"],
                    "versus_factor_holdout":draw.get("versus_factor_holdout"),"versus_original_reference":draw.get("versus_original_reference")})
        result["experiments"].append(compact(entry))
    for family in report["interventions"]:
        attempts=[]
        for a in family["attempts"]:
            entry={k:v for k,v in a.items() if k!="value"}
            entry["value"]={"scores":a["value"]["scores"],"y_range":a["value"]["y_range"]} if a["value"] else None
            attempts.append(compact(entry))
        result["interventions"].append({**{k:v for k,v in family.items() if k!="attempts"},"attempts":attempts})
    return result


def execute(task,config,out,reference=None):
    command=[os.environ["N4DOMAINS_BIN"],"split-stress",str(task),"--config",str(config),"--out",str(out),
        "--python",sys.executable,"--methods-library",os.environ["N4DOMAINS_METHODS_LIBRARY"]]
    if reference:command.extend(["--reference-report",str(reference)])
    subprocess.run(command,check=True)
    report=read(out/"report.json");check(report)
    return report


def run(out,task,reference,config):
    out.mkdir(parents=True,exist_ok=False)
    paths={Path(p) for p in read("docs/audit/alpha6-frozen-output-hashes.json")}
    paths.update(p for p in Path("results/dependence-alpha6-final").rglob("*") if p.is_file())
    paths.update(p for p in Path("schemas").glob("*.json") if not p.name.startswith("split-stress"))
    before={p.as_posix():sha(p) for p in sorted(paths)};write(out/"frozen-baselines-before.json",before)
    cfg=read("configs/pilots/split-stress-controls-v1.json")
    cfg["intervention_attempts"]=19
    controls_config=out/"controlled-config.json";write(controls_config,cfg)
    controls=[]
    for kind in ("group_only","trait_only","mixed","independent_y"):
        result=execute(Path("tests/fixtures/dependence")/(kind+".json"),controls_config,out/("control-"+kind))
        controls.append({"case":kind,"report_sha256":sha(out/("control-"+kind)/"report.json"),**scientific_summary(result)})
        write(out/"controlled-summary-checkpoint.json",controls)
    # Explicit failed-power control, with all 19 scheduled attempts retained.
    weak={**cfg,"holdout_factors":[],"shuffle_reference":False,"size_draws":0,"interventions":["within_factor"]}
    weak_config=out/"weak-config.json";write(weak_config,weak)
    weak_result=execute(Path("tests/fixtures/split_stress/power_failure.json"),weak_config,out/"control-power-failure")
    controls.append({"case":"power_failure",**scientific_summary(weak_result)})
    from nirs4all_domains.dependence import audit_representation
    from nirs4all_domains.predictive import group_folds
    extra={}
    for kind in ("size_only","extrapolation","mixed_composition"):
        folder=out/("extra-"+kind);folder.mkdir()
        data=audit_representation(read(Path("tests/fixtures/split_stress")/(kind+".json")),os.environ["N4DOMAINS_BIN"],os.environ["N4DOMAINS_METHODS_LIBRARY"],folder)
        rows=development_rows(data)
        if kind=="size_only":
            fold=group_folds(rows,4,17,"outer")["folds"][0];by={r["physical_sample_id"]:r for r in rows}
            train,valid=([by[s] for s in fold[k]] for k in ("train_sample_ids","validation_sample_ids"))
            pred,trace=fit_outer(train,valid,os.environ["N4DOMAINS_METHODS_LIBRARY"],cfg,"size-full")
            matched=size_match_rows(train,24,17,0)
            reduced,reduced_trace=fit_outer(matched["value"],valid,os.environ["N4DOMAINS_METHODS_LIBRARY"],cfg,"size-reduced")
            a,b=summarize(pred,[trace]),summarize(reduced,[reduced_trace])
            extra[kind]={"full":a,"reduced":b,"comparison":paired_comparison(a,b,500,17),
                "interpretation":"Same generating relation/evaluation IDs; training size is an alternative explanation, not a shortcut finding"}
        elif kind=="extrapolation":
            pred,trace=fit_outer(rows[:72],rows[72:],os.environ["N4DOMAINS_METHODS_LIBRARY"],cfg,"extrapolation")
            extra[kind]={**summarize(pred,[trace]),"generating_relation":"Y=t^2+2t; continuous X coordinate t; no generating group offset",
                "split_rule":"prespecified physical IDs p000..p071 train, p072..p095 development validation; not selected by model performance"}
        else:
            _,receipt=intervene(rows,kind="within_factor",factor="factor",seed=17,attempt=0)
            extra[kind]={"audit":exchangeability(rows,"within_factor","factor"),"receipt":receipt,
                "interpretation":"Complete mixed-level component vectors exchanged only within identical compositions"}
    write(out/"additional-controls.json",extra)
    # The real workflow is started only after all controlled/native/scope checks.
    real=execute(task,config,out/"ecosis",reference)
    rows=development_rows(read(out/"ecosis/mean-task.json"));by={r["physical_sample_id"]:r for r in rows};real_config=read(config)
    actual=next(e["value"] for e in real["experiments"] if e["design_id"]=="holdout:"+real_config["factor"] and e["status"]=="computed")
    replay=run_design(rows,actual["outer_fold_set"],os.environ["N4DOMAINS_METHODS_LIBRARY"],real_config)
    assert actual==replay,"Real factor-holdout replay changed"
    original_global=next(f for f in real["interventions"] if f["kind"]=="global")["attempts"][0]
    transformation=lambda train:intervene(train,kind="global",factor=real_config["factor"],seed=17,attempt=0,
        min_fraction=real_config["min_swappable_fraction"],min_components=real_config["min_swappable_components"],min_changed_fraction=real_config["min_changed_target_fraction"])
    repeated=run_design(rows,real["audit"]["reference_fold_set"],os.environ["N4DOMAINS_METHODS_LIBRARY"],real_config,transformation)
    assert repeated==original_global["value"],"Real global-intervention replay changed"
    size=next(e for e in real["experiments"] if e["design_id"]=="holdout:"+real_config["factor"])["size_controls"]
    size_replay=False
    for draw in size["draws"]:
        if draw["status"]!="computed":continue
        cell=next(c for c in draw["cells"] if c["status"]=="computed")
        pred,trace=fit_outer([by[s] for s in cell["training_ids"]],[by[s] for s in cell["validation_ids"]],
            os.environ["N4DOMAINS_METHODS_LIBRARY"],real_config,cell["scope_id"])
        assert trace==next(s for s in draw["value"]["lineage"] if s["fold_id"]==cell["scope_id"])
        assert pred==[r for r in draw["value"]["oof"] if r["fold_id"]==cell["scope_id"]]
        size_replay=True;break
    after={p:sha(p) for p in before};assert before==after,"Previous artifacts or schemas changed"
    proof={"protocol_version":"domains.split_stress.v0.1","execution_date":"2026-10-17","results_directory":out.as_posix(),
        "methods_binary_sha256":sha(os.environ["N4DOMAINS_METHODS_LIBRARY"]),"domains_binary_sha256":sha(os.environ["N4DOMAINS_BIN"]),
        "config_sha256":sha(config),"frozen_reference_sha256":sha(reference),"frozen_files_unchanged":len(before),
        "controlled":controls,"additional_controls":compact(extra),"real":scientific_summary(real),"real_report_sha256":sha(out/"ecosis/report.json"),
        "replay":{"real_genus_holdout_full_identical":True,"real_global_attempt_0_full_identical":True,"size_matched_cell_identical":size_replay,
            "scope":"Real selected protocols replayed, not the whole 19-attempt real campaign; full controlled CLI byte replay is a test gate"}}
    write(out/"qualification.json",proof)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);p.add_argument("--task",type=Path,required=True)
    p.add_argument("--reference-report",type=Path,required=True);p.add_argument("--config",type=Path,default=Path("configs/pilots/split-stress-v1.json"))
    a=p.parse_args();run(a.out,a.task,a.reference_report,a.config)
