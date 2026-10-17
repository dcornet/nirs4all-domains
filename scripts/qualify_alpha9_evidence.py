"""Bounded supplementary native characterization, registry freeze, then Ridge.

Does not select datasets/models from scores. The PLS task was admitted before
fitting; the challenge suite is immutable before the secondary family executes.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess

from nirs4all_domains.bank import file_plan, read, schema_check
from nirs4all_domains.comparison import ridge_on_frozen_folds
from nirs4all_domains.dependence import development_rows, paired_bootstrap
from nirs4all_domains.registry import compact_tree, evidence, freeze_suite, verify_evidence
from nirs4all_domains.split_stress import design_audit, fit_outer
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint, encoded, tree_bytes


def immutable(path, value):
    path = Path(path)
    if path.exists():
        if read(path) != value: raise ValueError("FROZEN_OUTPUT_DIFFERS:"+path.name)
    else: atomic_json(path, value)


def structure_summary(report):
    result = {k:report[k] for k in ("protocol_version", "status", "reason", "configuration", "population", "classification",
        "classification_evidence", "held_out_assignment", "shortcut_risk_evidence", "test_target_accessed", "limitations")}
    result["settings"] = []
    for s in report["settings"]:
        r = s["reference"]
        result["settings"].append({"parameters":s["parameters"], "status":s["status"], "reason":s["reason"],
            "replicate_statuses":[{"draw":v["draw"], "status":v["status"], "reason":v["reason"]} for v in s["replicates"]],
            "reference":None if r is None else {"n_clusters":r["hdbscan"]["n_clusters"], "noise_fraction":r["noise_fraction"],
                "physical_ids":r["physical_sample_ids"], "labels":r["hdbscan"]["labels"],
                "pca":{k:v for k,v in r["pca"].items() if k != "fitted_state"}},
            "stability":{k:v for k,v in s["stability"].items() if k != "co_membership_pairs"},
            "comparison_to_primary":s["comparison_to_primary"]})
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("supplement", "freeze", "compare", "replay"))
    for k in ("root", "registry", "binary", "library", "policy"):
        p.add_argument("--"+k, type=Path, required=True)
    args = p.parse_args()
    args.binary=args.binary.resolve();args.library=args.library.resolve()
    receipts=read(args.root/"stage-receipts.json")
    original=read(args.root/"evidence"/receipts[-1]["artifact"])
    verify_evidence(original)
    p1=read(args.root/"evidence"/receipts[0]["artifact"])
    mean_path=args.root/"scratch"/p1["mean_task_ref"]
    if digest(mean_path)!=p1["mean_task_sha256"]:raise ValueError("MEAN_CACHE_CHANGED")
    task=read(mean_path);rows=development_rows(task);config=original["scientific"]["deep"]["config"]
    contract=copy.deepcopy(original["contract"])
    contract["execution"]["settings"]={"supplement":"domains.alpha9.real_evidence.v0.1", "config":config,
        "structure_config_sha256":digest("configs/pilots/structure-v1.json"), "base_evidence_id":original["evidence_id"],
        "runner_sha256":digest(__file__), "comparison_sha256":digest(Path(ridge_on_frozen_folds.__code__.co_filename))}
    store=StageStore(args.root/"state",args.root/"scratch",args.root/"evidence",Path.cwd(),read(args.policy))
    if args.command=="supplement":
        def calculate(folder):
            associations={}
            for factor in ("cereal_type","instrument","country"):
                out=folder/(factor+".json")
                subprocess.run([str(args.binary),"group-target",str(mean_path),"--factor",factor,"--draws","100","--seed","17",
                                "--out",str(out),"--methods-library",str(args.library)],check=True,capture_output=True)
                report=read(out)
                associations[factor]={**compact_tree(report),"full_report_sha256":digest(out)}
            destination=folder/"structure"
            subprocess.run([str(args.binary),"structure",str(mean_path),"--config","configs/pilots/structure-v1.json",
                            "--out",str(destination),"--methods-library",str(args.library)],check=True,capture_output=True)
            report=read(destination/"report.json")
            audit=design_audit(rows,config)
            power={kind:[{k:s[k] for k in ("scope_id","n_components","n_targets","movable_target_fraction","eligible","reason")} |
                         {"swappable_components":len(s["swappable_components"])} for s in a["scopes"]] for kind,a in audit["interventions"].items()}
            baseline=original["scientific"]["deep"]["experiments"][0]["value"]
            return {"associations":associations,"structure":structure_summary(report),"structure_full_report_sha256":digest(destination/"report.json"),
                    "reference_paired_uncertainty":compact_tree(paired_bootstrap(baseline["oof"],100,17)),
                    "intervention_power":power,"test_target_accessed":False}
        receipt,value=store.run(contract,"P2",file_plan(mean_path,128*2**20,256*1024,501),calculate)
        atomic_json(args.root/"supplement-receipt.json",receipt)
        print(json.dumps({"status":receipt["status"],"reason":receipt["reason"],"bytes":receipt.get("measured_evidence_bytes")}))
        if value is None:raise SystemExit(2)
    elif args.command=="freeze":
        receipt=read(args.root/"supplement-receipt.json")
        supplement=read(args.root/"evidence"/receipt["artifact"])
        if digest(args.root/"evidence"/receipt["artifact"])!=receipt["sha256"]:raise ValueError("SUPPLEMENT_CHANGED")
        scientific={**original["scientific"],"supplement":supplement,
            "admission":read(args.root/"perten-admission.json"), "original_bank_evidence_id":original["evidence_id"]}
        q={"identity":{"status":"computed","reason":None,"value":True},
           "xy_signal":{"status":"computed","reason":None,"value":True},
           "independent_support":{"status":"computed","reason":None,"value":{"declared_development_context_blocks":17,"original_assay_events_verified":False}},
           "structural_stress":{"status":"computed","reason":None,"value":"Cereal/instrument closure holdout sensitivity; size and target-range alternatives remain"}}
        record=evidence(original["task"],contract,scientific,q,["structure_sensitive_challenge"],original["limitations"]+[
            "Moisture unit is source percent; wet/dry basis is ambiguous, and no conversion is applied.",
            "Context blocks are conservative instrument-model/country/year tuples, not verified batches or independent farms.",
            "Two cereal closure units; 38-ID/2-block size-control intersection is partial and cannot isolate the all-359 effect.",
            "Global and within-cereal interventions unavailable; no low-dependence certification.",
            "Instrument metadata include an explicit unknown-model stratum; country can describe growing or measurement location."])
        schema_check(record,"qualification-evidence");verify_evidence(record)
        args.registry.mkdir(parents=True,exist_ok=True)
        immutable(args.registry/"perten-evidence.json",record)
        immutable(args.registry/"perten-task.json",record["task"])
        immutable(args.registry/"perten-admission.json",read(args.root/"perten-admission.json"))
        metric={"primary":"RMSE in source moisture percentage points; compare within task only", "target_unit":task["target_unit"],
                "uncertainty":"paired whole context blocks; fixed OOF, excludes model-refit uncertainty",
                "evaluation":{"context":task["context"],"development_input_sha256":fingerprint(rows),
                              "outer_fold_set_sha256":fingerprint(original["scientific"]["deep"]["experiments"][0]["value"]["outer_fold_set"])}}
        suite=freeze_suite([record],"structure_sensitive_challenge",metric)
        schema_check(suite,"benchmark-suite");immutable(args.registry/"perten-comparison-suite.json",suite)
        all_records=[record,read("docs/benchmarks/alpha8/ecosis-evidence.json")]
        immutable(args.registry/"structure-challenge-suite.json",freeze_suite(all_records,"structure_sensitive_challenge",
            {"primary":"task-wise RMSE, native target units", "aggregation":"No raw RMSE averaging across chemically different units"}))
        immutable(args.registry/"low-dependence-candidate-suite.json",freeze_suite(all_records,"candidate_low_structural_dependence",{}))
        print(json.dumps({"task_id":record["task_id"],"evidence_id":record["evidence_id"],"suite_id":suite["suite_id"],"bytes":len(encoded(record))}))
    elif args.command=="compare":
        suite=read(args.registry/"perten-comparison-suite.json")
        frozen=read(args.registry/"perten-evidence.json");verify_evidence(frozen)
        if suite["tasks"][0]["evidence_sha256"]!=fingerprint(frozen):raise ValueError("SUITE_EVIDENCE_CHANGED")
        contract["execution"]["settings"]["suite_id"]=suite["suite_id"]
        def calculate(folder):
            output={}
            for design in frozen["scientific"]["deep"]["experiments"]:
                if design["status"]!="computed":continue
                folds=design["value"]["outer_fold_set"]
                # Secondary holdouts are already declared in the frozen PLS
                # evidence. Pin each fold-set before its Ridge execution.
                evaluation=copy.deepcopy(suite)
                if design["kind"]!="reference":
                    evaluation["metric_contract"]["evaluation"]["outer_fold_set_sha256"]=fingerprint(folds)
                    evaluation["suite_id"]=fingerprint({k:v for k,v in evaluation.items() if k!="suite_id"})
                output[design["design_id"]]={"evaluation_manifest":evaluation,
                    "result":ridge_on_frozen_folds(task,folds,str(args.library),config,evaluation)}
            return {"protocol_version":"domains.alpha9.family_comparison.v0.1","frozen_primary_suite_id":suite["suite_id"],
                    "config":{"ridge_alpha":1.0,"center_x":True,"center_y":True,"scale_x":False},
                    "designs":output,"test_target_accessed":False}
        receipt,value=store.run(contract,"P3",file_plan(mean_path,65536,512*1024,12),calculate)
        atomic_json(args.root/"comparison-receipt.json",receipt)
        if value is None:print(receipt["reason"]);raise SystemExit(2)
        immutable(args.registry/"perten-family-comparison.json",value)
        print(json.dumps({k:v["result"]["status"] for k,v in value["designs"].items()}))
    else:
        reference=original["scientific"]["deep"]["experiments"][0]["value"]
        # Exact scoped replay, not another whole campaign.
        fold=reference["outer_fold_set"]["folds"][0];by_id={r["physical_sample_id"]:r for r in rows}
        def calculate(folder):
            actual,_=fit_outer([by_id[s] for s in fold["train_sample_ids"]],[by_id[s] for s in fold["validation_sample_ids"]],
                               str(args.library),config,fold["fold_id"])
            expected=[r for r in reference["oof"] if r["fold_id"]==fold["fold_id"]]
            actual.sort(key=lambda r:r["physical_sample_id"]);expected.sort(key=lambda r:r["physical_sample_id"])
            if actual!=expected:raise ValueError("EXACT_REAL_OOF_REPLAY_DIFFERS")
            return {"status":"computed","reason":None,"value":{"fold_id":fold["fold_id"],"n_predictions":len(actual),
                    "oof_sha256":fingerprint(actual),"exact_equality":True},"test_target_accessed":False}
        receipt,value=store.run(contract,"P1",file_plan(mean_path,65536,8192,20),calculate)
        atomic_json(args.root/"replay-receipt.json",receipt)
        if value is None:print(receipt["reason"]);raise SystemExit(2)
        immutable(args.registry/"perten-replay.json",value)
        print(json.dumps(value))


if __name__=="__main__":main()
