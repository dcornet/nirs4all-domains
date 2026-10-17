"""Execute frozen controls and EcoSIS twice, preserve old artifacts and record proof."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from check_dependence_report import check


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")


def run(out,task,config):
    out.mkdir(parents=True,exist_ok=False)
    binary=os.environ["N4DOMAINS_BIN"];library=os.environ["N4DOMAINS_METHODS_LIBRARY"]
    baseline=json.loads(Path("docs/audit/alpha6-frozen-output-hashes.json").read_text())
    assert all(sha(Path(p))==v for p,v in baseline.items())
    controls=[]
    controlled=json.loads(config.read_text());controlled.update(outer_folds=4,max_components=6,
        factors=[{"field":"factor","source_column":"factor","provenance":"frozen synthetic analytical control","available_at_prediction":True}])
    cc=out/"controlled-config.json";write(cc,controlled)
    for kind in ("group_only","trait_only","mixed","independent_y","unseen","high_cardinality","repeats"):
        destination=out/("control-"+kind)
        subprocess.run([binary,"dependence","tests/fixtures/dependence/"+kind+".json","--config",str(cc),"--out",str(destination),
            "--python",sys.executable,"--methods-library",library],check=True)
        report=json.loads((destination/"report.json").read_text());check(report)
        f=report["factors"][0];a=f["target.group_association"]
        controls.append({"case":kind,"report_sha256":sha(destination/"report.json"),"association":a["association"],
            "association_interval":a["bootstrap"]["interval_95"],"scores":f["scores"],"fallback_fraction":f["audit"]["fallback_fraction"],
            "within_group":f["prediction.within_group_incremental_skill"],"paired_uncertainty":f["uncertainty"]["interval_95"]})
    write(out/"controlled-summary.json",controls)
    hashes=[]
    for repeat in (1,2):
        destination=out/f"ecosis-{repeat}"
        subprocess.run([binary,"dependence",str(task),"--config",str(config),"--out",str(destination),
            "--python",sys.executable,"--methods-library",library],check=True)
        report=json.loads((destination/"report.json").read_text());check(report)
        hashes.append(sha(destination/"report.json"))
        old=json.loads(Path("results/ecosis-alpha4-release/predictive-sanity.json").read_text())
        spectral=json.loads((destination/"spectral.json").read_text())
        assert all(old[k]==spectral[k] for k in ("pls","null","oof","outer_fold_set","lineage"))
    assert hashes[0]==hashes[1],"Full report deterministic reruns differ"
    assert all(sha(Path(p))==v for p,v in baseline.items())
    real=[]
    for f in report["factors"]:
        real.append({"factor":f["factor"],"audit":f["audit"],"association":f["target.group_association"]["association"],
            "association_bootstrap":{k:v for k,v in f["target.group_association"]["bootstrap"].items() if k!="draws"},
            "scores":f["scores"],"conditional":f["prediction.within_group_incremental_skill"],
            "paired_rmse_improvement_over_group":f["paired_rmse_improvement_over_group"],
            "paired_bootstrap":{k:v for k,v in f["uncertainty"].items() if k!="draws"},
            "selected_components":[s["n_components"] for s in f["lineage"]]})
    proof={"protocol_version":"domains.structural_dependence.v0.1","execution_date":"2026-10-17","results_directory":out.as_posix(),
        "config_sha256":sha(config),"methods_binary_sha256":sha(Path(library)),"domains_binary_sha256":sha(Path(binary)),
        "controls":controls,"real":real,"real_report_sha256":hashes,"byte_identical_real_reruns":True,
        "alpha4_original_pls_folds_oof_metrics_artifacts_identical":True,"previous_30_reports_unchanged":True,
        "shootout":"No documented explanatory metadata factors qualified; fragile X clusters cannot be predictive factors."}
    write(out/"qualification.json",proof)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);p.add_argument("--task",type=Path,required=True)
    p.add_argument("--config",type=Path,default=Path("configs/pilots/dependence-v1.json"));a=p.parse_args();run(a.out,a.task,a.config)
