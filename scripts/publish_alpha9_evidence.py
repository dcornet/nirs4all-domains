"""Assemble portable evidence manifests and matched uncertainty, without fits."""
import argparse
import copy
import json
import os
from pathlib import Path

from nirs4all_domains.bank import read, schema_check
from nirs4all_domains.registry import verify_evidence, compact_tree, verify_storage
from nirs4all_domains.split_stress import paired_comparison
from nirs4all_domains.storage import atomic_json, digest, fingerprint, tree_bytes


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot",type=Path,required=True);p.add_argument("--registry",type=Path,required=True)
    p.add_argument("--cache",type=Path,required=True)
    args=p.parse_args();root=args.registry
    evidence=read(root/"perten-evidence.json");verify_evidence(evidence)
    comparison=read(root/"perten-family-comparison.json")
    designs={d["design_id"]:d["value"] for d in evidence["scientific"]["deep"]["experiments"] if d["status"]=="computed"}
    ridge_designs={}
    for key,record in comparison["designs"].items():
        if record["result"]["status"]!="computed":continue
        baseline=copy.deepcopy(designs[key]);predictions={r["physical_sample_id"]:r for r in record["result"]["value"]["oof"]}
        for row in baseline["oof"]:
            matched=predictions[row["physical_sample_id"]]
            if row["y"]!=matched["y"] or row["component_id"]!=matched["component_id"]:raise ValueError("MATCHED_RIDGE_IDENTITY_OR_TRUTH_DIFFERS")
            row["spectral"]=matched["ridge"]
        ridge_designs[key]=baseline
    output={}
    for key,design in ridge_designs.items():
        records={}
        for label,reference in (("ridge_minus_pls_same_design",designs[key]),("ridge_minus_ridge_reference",ridge_designs["reference:17"])):
            if key=="reference:17" and label=="ridge_minus_ridge_reference":continue
            result=paired_comparison(reference,design,100,17)["value"]
            interval=result["uncertainty"]["interval_95"]
            records[label]={"rmse_change":result["rmse_change_candidate_minus_reference"]["spectral"],
                "interval_95":interval["value"]["spectral"] if interval["status"]=="computed" else None,
                "interval_reason":interval["reason"],"n_samples":result["n_samples"],"n_components":result["n_components"],
                "requested_draws":100,"successful_draws":result["uncertainty"]["successful"],
                "conditioning":result["uncertainty"]["conditioning"]}
        output[key]=records
    uncertainty={"protocol_version":"domains.alpha9.family_comparison.v0.1", "input_comparison_sha256":digest(root/"perten-family-comparison.json"),
                 "frozen_suite_id":comparison["frozen_primary_suite_id"],"designs":output,"test_target_accessed":False,
                 "limitation":"Cereal holdout has only two closure units; context-block OOF intervals are not uncertainty over a population of unseen cereals."}
    atomic_json(root/"perten-comparison-uncertainty.json",uncertainty)
    sidecar=dict(schema_version=1,integration_protocol="domains.datasets_sidecar.v0.1",dataset_id=evidence["task"]["dataset_id"],
        content_version=evidence["task"]["content_version"],task_id=evidence["task_id"],qualification_protocol=evidence["protocol_version"],
        evidence_sha256=digest(root/"perten-evidence.json"),evidence_ref="perten-evidence.json",purposes=evidence["purposes"])
    schema_check(sidecar,"datasets-sidecar");atomic_json(root/"datasets-sidecar.json",sidecar)
    receipts=read(args.pilot/"stage-receipts.json")
    moderate=args.pilot/"scratch"/receipts[1]["execution_id"]/"P2"/str(receipts[1]["attempt"])/"coverage/report.json"
    canonical=read(moderate)
    qc={"canonical_report_sha256":digest(moderate),"preflight_validation":canonical["preflight"]["validation"],
        "intrinsic_metrics":[{k:v for k,v in m.items() if k!="provenance"} for m in canonical["preflight"]["metrics"] if m["metric_id"].startswith("integrity.")],
        "fit":{k:v for k,v in canonical["fit"].items() if not isinstance(v,(dict,list))},
        "findings":canonical["findings"],"test_target_accessed":canonical["test_target_accessed"]}
    atomic_json(root/"perten-intrinsic-and-geometry.json",qc)
    # New alpha.9 exports can share identical immutable local stage bytes. Verify
    # content and workspace boundaries before replacing an export directory entry.
    # No historical artifact, payload or source path is removed or migrated.
    sharing=[];workspace=Path.cwd().resolve()
    candidates={"perten-family-comparison.json":args.pilot/"evidence"/read(args.pilot/"comparison-receipt.json")["artifact"],
                "perten-replay.json":args.pilot/"evidence"/read(args.pilot/"replay-receipt.json")["artifact"],
                "perten-admission.json":args.pilot/"perten-admission.json","perten-task.json":args.pilot/"perten-identity.json"}
    for name,source in candidates.items():
        target=root/name;source=source.resolve();target=target.resolve()
        if not source.is_relative_to(workspace) or not target.is_relative_to(workspace) or digest(source)!=digest(target):
            raise ValueError("EXPORT_SHARING_REQUIRES_IDENTICAL_OWNED_WORKSPACE_FILES")
        if not os.path.samefile(source,target):
            temp=target.with_name(target.name+".link-part")
            os.link(source,temp);os.replace(temp,target)
        sharing.append({"export":name,"sha256":digest(target),"bytes":target.stat().st_size,"same_file_identity":os.path.samefile(source,target)})
    artifacts=[dict(path=f.name,sha256=digest(f),bytes=f.stat().st_size,retention="essential_evidence") for f in sorted(root.glob("*.json")) if f.name!="storage.json"]
    cache=read(args.pilot/"preparation.json")
    cached_dataset=args.cache/"datasets"/evidence["task"]["dataset_id"]
    deps=[{"content_sha256":cache_hash,"bytes":(cached_dataset/path).stat().st_size,"provider":"Datasets 0.3.11 local canonical reproduction",
            "access":"public","local_locator_key":"perten_canonical_"+path.replace('/','_').replace('.','_')} for path,cache_hash in cache["canonical_hashes"].items()]
    deps.extend([{"content_sha256":digest(args.pilot/"perten-task.json"),"bytes":(args.pilot/"perten-task.json").stat().st_size,
                  "provider":"Domains audited keyed scratch input","access":"public","local_locator_key":"perten_original_task"},
                 {"content_sha256":digest("docs/benchmarks/alpha8/ecosis-evidence.json"),"bytes":Path("docs/benchmarks/alpha8/ecosis-evidence.json").stat().st_size,
                  "provider":"Frozen repository alpha.8 evidence for the two-task suite","access":"public","local_locator_key":"frozen_ecosis_alpha8_evidence"}])
    manifest=dict(schema_version=1,protocol_version="domains.storage.v0.1",execution_id=evidence["execution_id"],artifacts=artifacts,cache_dependencies=deps,
        replay_grade="reconstructed_from_cache",measured_bytes=sum(a["bytes"] for a in artifacts),optional_archives=[],
        limitations=["Exact representative PLS fold replay; complete historical campaign replay is not claimed.",
                     "Authorized cache resolution and matching Domains/Methods/DAG/controller builds remain required.",
                     "CORN remains pending by the owner's explicit decision: no rights justification; original keys also absent."])
    schema_check(manifest,"storage-manifest");atomic_json(root/"storage.json",manifest);verify_storage(manifest,root)
    budget=read("configs/bank/storage-policy-alpha8.json")
    essential=tree_bytes([root,args.pilot/"evidence",args.pilot/"perten-fit-admission.json"])
    if essential>budget["evidence_bytes"]:raise ValueError("COMBINED_TASK_EVIDENCE_CAP_EXCEEDED:"+str(essential))
    summary={"task_id":evidence["task_id"],"portable_registry_logical_bytes":tree_bytes([root]),
             "combined_unique_task_evidence_bytes":essential,"evidence_cap_bytes":budget["evidence_bytes"],"identical_new_export_sharing":sharing,
             "pilot_total_bytes":tree_bytes([args.pilot]),"cache_bytes":tree_bytes([args.cache]),"native_retained_test_targets_accessed":False}
    atomic_json("docs/audit/alpha9-storage.json",summary)
    print(json.dumps({k:v for k,v in summary.items() if k!="identical_new_export_sharing"}))


if __name__=="__main__":main()
