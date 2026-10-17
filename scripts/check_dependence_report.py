"""Schema plus semantic identity/scope/status checks on an executed workflow."""
import json
import math
from pathlib import Path
import sys

import jsonschema


def check(report):
    root=Path(__file__).resolve().parents[1]
    jsonschema.validate(report,json.loads((root/"schemas/dependence-report.v1.schema.json").read_text()))
    jsonschema.validate(report["config"],json.loads((root/"schemas/dependence-config.v1.schema.json").read_text()))
    def finite(value):
        if isinstance(value,float):assert math.isfinite(value)
        elif isinstance(value,list):
            for v in value:finite(v)
        elif isinstance(value,dict):
            if {"status","reason","value"}<=value.keys():
                if value["status"]=="computed":assert value["value"] is not None and value["reason"] is None
                else:assert value["value"] is None and value["reason"]
            for v in value.values():finite(v)
    finite(report)
    reference_ids=None
    for factor in report["factors"]:
        rows=factor["oof"];by_id={r["physical_sample_id"]:r for r in rows}
        assert len(by_id)==len(rows)==report["n_samples"]
        assert len({r["component_id"] for r in rows})==report["n_components"]
        if reference_ids is None:reference_ids=set(by_id)
        assert set(by_id)==reference_ids
        outer=factor["outer_fold_set"]
        assert set(outer["sample_ids"])==set(by_id)
        seen=[]
        for fold in outer["folds"]:
            train=set(fold["train_sample_ids"]);valid=set(fold["validation_sample_ids"])
            assert not train&valid and train|valid==set(by_id)
            assert not {by_id[s]["component_id"] for s in train}&{by_id[s]["component_id"] for s in valid}
            seen.extend(valid)
        assert len(seen)==len(set(seen))==len(rows)
        for scope in factor["lineage"]:
            train=set(scope["train_sample_ids"]);holdout=set(scope["validation_sample_ids"])
            inner={f["fold_id"]:f for f in scope["inner_fold_set"]["folds"]}
            assert scope["native_fit_lineage_verified"]
            for event in scope["residual_fit_events"]:
                fitted=set(event["baseline"]["training_ids"])
                assert fitted<=train and not fitted&holdout
                expected=train if event["phase"]=="REFIT" else set(inner[event["fold_id"]]["train_sample_ids"])
                assert fitted==expected and not fitted&set(event["validation_ids"])
                assert event["fit_kind"] in ("native_methods_pls","exact_zero_training_residual_no_pls_fit")
        for row in rows:
            assert row["group_plus_residual"]==row["group_only"]+row["residual_correction"]
            assert row["residual_truth"]==row["y"]-row["group_only"]
            if row["baseline_source"]=="global_training_fallback":assert row["group_only"]==row["null"]
        a=factor["target.group_association"]["association"]
        if a["status"]=="computed":
            v=a["value"]
            assert abs(v["ss_total"]-v["ss_between"]-v["ss_within"])<=1e-10*(1+v["ss_total"])
            assert v["native_permutations"]==0
        b=factor["uncertainty"]
        assert b["successful"]+b["failed"]==b["requested"]==len(b["draws"])
    return True


if __name__=="__main__":
    check(json.loads(Path(sys.argv[1]).read_text()));print("Dependence schema and semantic invariants valid")
