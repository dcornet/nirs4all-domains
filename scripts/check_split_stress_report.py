"""Scientific scope/population checks in addition to the separate JSON Schema."""
from collections import Counter
import json
import math
from pathlib import Path
import sys

import jsonschema


def check(report):
    root=Path(__file__).resolve().parents[1]
    jsonschema.validate(report,json.loads((root/"schemas/split-stress-report.v1.schema.json").read_text()))
    jsonschema.validate(report["config"],json.loads((root/"schemas/split-stress-config.v1.schema.json").read_text()))
    def walk(v):
        if isinstance(v,float):assert math.isfinite(v)
        elif isinstance(v,list):
            for x in v:walk(x)
        elif isinstance(v,dict):
            if {"status","reason","value"}<=v.keys():
                if v["status"]=="computed":assert v["reason"] is None and v["value"] is not None
                else:assert v["value"] is None and v["reason"]
            for x in v.values():walk(x)
    walk(report)
    original=report["experiments"][0]["value"]
    truth={r["physical_sample_id"]:r for r in original["oof"]}
    assert len(truth)==report["n_samples"]
    factor_levels={}
    for closure in report["audit"]["factor_holdouts"][report["config"]["factor"]]["closures"]:
        for sid in closure["physical_ids"]:factor_levels[sid]=closure["factor_levels"]
    def result(v):
        rows=v["oof"];by={r["physical_sample_id"]:r for r in rows}
        assert len(rows)==len(by)==v["n_samples"]
        assert len({r["component_id"] for r in rows})==v["n_components"]
        assert all(r["y"]==truth[s]["y"] and r["component_id"]==truth[s]["component_id"] for s,r in by.items())
        predicted=[]
        for scope in v["lineage"]:
            tr=set(scope["train_sample_ids"]);va=set(scope["validation_sample_ids"])
            assert not tr&va
            assert not {truth[s]["component_id"] for s in tr}&{truth[s]["component_id"] for s in va}
            predicted.extend(va)
            for mode in ("spectral","residual"):
                if mode not in scope:continue # frozen alpha.6 witness has explicit original lineage
                evidence=scope[mode]
                assert evidence["native_fit_lineage_verified"]
                inner={f["fold_id"]:f for f in evidence["inner_fold_set"]["folds"]}
                for f in inner.values():
                    it,iv=set(f["train_sample_ids"]),set(f["validation_sample_ids"])
                    assert it|iv==tr and not it&iv
                    assert not {truth[s]["component_id"] for s in it}&{truth[s]["component_id"] for s in iv}
                for event in evidence.get("residual_fit_events",[]):
                    expected=tr if event["phase"]=="REFIT" else set(inner[event["fold_id"]]["train_sample_ids"])
                    fitted=set(event["baseline"]["training_ids"])
                    assert fitted==expected and not fitted&va
                    if "intervention_sha256" in event:
                        receipt=evidence["intervention_scopes"][event["intervention_sha256"]]
                        assert set(receipt["training_ids"])==expected
                        assert {e["source_id"] for e in receipt["target_map"]}==expected
                        assert {e["destination_id"] for e in receipt["target_map"]}==expected
                        destination_components={}
                        for entry in receipt["target_map"]:
                            assert entry["training_y"]==truth[entry["source_id"]]["y"]
                            assert entry["original_y"]==truth[entry["destination_id"]]["y"]
                            destination_components.setdefault(entry["destination_component"],set()).add(entry["source_component"])
                            if receipt["kind"]=="within_factor":assert entry["destination_factor"]==entry["source_factor"]
                        assert all(len(s)==1 for s in destination_components.values())
        assert Counter(predicted)==Counter(by.keys())
        assert v["y_range"]["within_range"]["n_samples"]+v["y_range"]["outside_range"]["n_samples"]==len(by)
    for e in report["experiments"]:
        if e["status"]=="computed":
            result(e["value"])
            assert set(r["physical_sample_id"] for r in e["value"]["oof"])==set(truth)
            if e["kind"]=="factor_holdout":
                closure=report["audit"]["factor_holdouts"][e["factor"]]
                for fold in e["value"]["outer_fold_set"]["folds"]:
                    tr=set(fold["train_sample_ids"]);va=set(fold["validation_sample_ids"])
                    assert not any(set(c["physical_ids"])&tr and set(c["physical_ids"])&va for c in closure["closures"])
            if "size_controls" in e:
                for draw in e["size_controls"]["draws"]:
                    if draw["status"]=="computed":result(draw["value"])
                    for cell in draw["cells"]:
                        if cell["status"]=="computed":
                            assert cell["matched_samples"]<=cell["target_samples"]<=cell["pool_samples"]
                            assert cell["sample_gap"]<=e["size_controls"]["max_sample_gap"]
                            assert len(cell["training_ids"])==cell["matched_samples"]
                            assert not set(cell["training_ids"])&set(cell["validation_ids"])
    for family in report["interventions"]:
        assert family["requested"]==len(family["attempts"])==family["successful"]+family["failed_or_unavailable"]
        assert [a["attempt"] for a in family["attempts"]]==list(range(family["requested"]))
        for attempt in family["attempts"]:
            if attempt["status"]=="computed":
                result(attempt["value"])
                assert set(r["physical_sample_id"] for r in attempt["value"]["oof"])==set(truth)
                if not attempt["effective"]:assert attempt["evidence_status"]=="limited_evidence" and attempt["power_reason"]
    return True


if __name__=="__main__":
    check(json.loads(Path(sys.argv[1]).read_text()));print("Split stress schema and scientific scope invariants valid")
