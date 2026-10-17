"""Compact, reproducible public evidence from full local alpha.7 reports."""
import argparse
import hashlib
import json
from pathlib import Path

from nirs4all_domains.predictive import native_summary


def scores(result):
    return {k:{m:v["value"][m]["value"] for m in ("rmse","mae","r2")} for k,v in result["scores"].items()}


def comparison(c):
    if not c or c["value"] is None:return c
    v=c["value"]
    return {"status":c["status"],"n_samples":v["n_samples"],"n_components":v["n_components"],
        "matched_ids":v["matched_ids"],"paired_all_development":v["paired_all_development"],
        "reference_rmse":{k:x["value"]["rmse"]["value"] for k,x in v["reference_scores"].items()},
        "candidate_rmse":{k:x["value"]["rmse"]["value"] for k,x in v["candidate_scores"].items()},
        "rmse_change_candidate_minus_reference":v["rmse_change_candidate_minus_reference"],
        "gain_change_relative_to_own_null":v["gain_change_relative_to_own_null"],
        "uncertainty":{k:x for k,x in v["uncertainty"].items() if k!="draws"}}


def summarize(report):
    cases=[]
    for e in report["experiments"]:
        entry={k:e[k] for k in ("design_id","kind","status","reason")}
        if e["value"]:
            v=e["value"];entry.update(scores=scores(v),n_samples=v["n_samples"],n_components=v["n_components"],
                outside_training_range_fraction=v["y_range"]["outside_training_range_fraction"],
                training_counts=[{"samples":s["n_train_samples"],"components":s["n_train_components"],
                    "validation_samples":s["n_validation_samples"],"fallback":len(s["factor_overlap"]["fallback_ids"])} for s in v["lineage"]])
            entry["range_sensitivity"]={k:{"n_samples":v["y_range"][k]["n_samples"],"n_components":v["y_range"][k]["n_components"],
                "rmse":{m:(a["value"]["rmse"]["value"] if a["value"] else None) for m,a in v["y_range"][k]["scores"].items()}} for k in ("within_range","outside_range")}
        if "comparison" in e:entry["comparison"]=comparison(e["comparison"])
        if "size_controls" in e:
            entry["size_controls"]=[]
            for d in e["size_controls"]["draws"]:
                cells=[c for c in d["cells"] if c["status"]=="computed"]
                entry["size_controls"].append({"draw":d["draw"],"status":d["status"],"reason":d["reason"],
                    "successful_cells":len(cells),"total_cells":len(d["cells"]),"exact_cells":sum(c["exact_match"] for c in cells),
                    "target_sample_counts":sorted({c["target_samples"] for c in cells}),"target_component_counts":sorted({c["target_components"] for c in cells}),
                    "actual_component_counts":sorted({c["matched_components"] for c in cells}),"sample_gaps":sorted({c["sample_gap"] for c in cells}),
                    "failure_reasons":[c["reason"] for c in d["cells"] if c["status"]!="computed"],
                    "scores":scores(d["value"]) if d["value"] else None,
                    "versus_factor_holdout":comparison(d.get("versus_factor_holdout")),"versus_reference":comparison(d.get("versus_original_reference"))})
        cases.append(entry)
    families=[]
    for f in report["interventions"]:
        computed=[a for a in f["attempts"] if a["value"]]
        entry={k:f[k] for k in ("kind","requested","successful","failed_or_unavailable","effective_attempts")}
        if computed:
            entry["metric_distributions"]={model:{m:native_summary(a["value"]["scores"][model]["value"][m]["value"] for a in computed)
                for m in ("rmse","mae","r2")} for model in computed[0]["value"]["scores"]}
        entry["evaluation_ids"]=computed[0]["comparison"]["value"]["matched_ids"] if computed else None
        attempts=[]
        for a in f["attempts"]:
            c=a.get("comparison",{}).get("value")
            small=None if c is None else {"n_samples":c["n_samples"],"n_components":c["n_components"],
                "rmse_change":c["rmse_change_candidate_minus_reference"],"gain_change":c["gain_change_relative_to_own_null"],
                "rmse_change_interval_95":c["uncertainty"]["interval_95"]["value"],"gain_change_interval_95":c["uncertainty"]["gain_change_interval_95"]["value"],
                "bootstrap_successful":c["uncertainty"]["successful"],"bootstrap_failed":c["uncertainty"]["failed"]}
            attempts.append({"attempt":a["attempt"],"status":a["status"],"reason":a["reason"],"effective":a.get("effective"),
                "minimum_changed_target_fraction":a.get("minimum_changed_target_fraction"),"power_reason":a.get("power_reason"),
                "scores":scores(a["value"]) if a["value"] else None,"comparison":small})
        entry["attempts"]=attempts
        families.append(entry)
    return {"experiments":cases,"interventions":families}


def run(directory,out):
    proof=json.loads((directory/"qualification.json").read_text())
    report=json.loads((directory/"ecosis/report.json").read_text())
    result={k:proof[k] for k in ("protocol_version","execution_date","results_directory","methods_binary_sha256","domains_binary_sha256",
        "config_sha256","frozen_reference_sha256","frozen_files_unchanged","real_report_sha256","replay")}
    result["full_qualification_sha256"]=hashlib.sha256((directory/"qualification.json").read_bytes()).hexdigest()
    result["real"]=summarize(report)
    result["controlled"]={}
    for folder in sorted(directory.glob("control-*")):
        p=folder/"report.json"
        if p.exists():result["controlled"][folder.name]={"report_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),**summarize(json.loads(p.read_text()))}
    extra=json.loads((directory/"additional-controls.json").read_text())
    result["additional_controls"]={"size_only":{"full_scores":scores(extra["size_only"]["full"]),"reduced_scores":scores(extra["size_only"]["reduced"]),
        "comparison":comparison(extra["size_only"]["comparison"])},"extrapolation":{"scores":scores(extra["extrapolation"]),
        "outside_training_range_fraction":extra["extrapolation"]["y_range"]["outside_training_range_fraction"]},
        "mixed_composition":{"eligible":extra["mixed_composition"]["audit"]["eligible"],"receipt_sha256":hashlib.sha256(json.dumps(extra["mixed_composition"]["receipt"],sort_keys=True).encode()).hexdigest()}}
    out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("directory",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();run(a.directory,a.out)
