"""Consolidate frozen real evidence and replay representative cells under quota.

No acquisition, cleanup, full old campaign rerun or upstream mutation.
"""
import argparse
import json
import os
from pathlib import Path

from nirs4all_domains.bank import bounded_qualify, file_plan, schema_check
from nirs4all_domains.dependence import development_rows
from nirs4all_domains.interventions import intervene
from nirs4all_domains.predictive import fingerprint as scientific_fingerprint
from nirs4all_domains.registry import (compact_stress, compact_tree, evidence, execution_contract, freeze_suite,
                                      task_identity, verify_evidence, verify_storage)
from nirs4all_domains.split_stress import fit_outer
from nirs4all_domains.storage import StageStore, atomic_json, digest, encoded, fingerprint, tree_bytes


def read(path):return json.loads(Path(path).read_text())


def run(out, binary, library):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    before=tree_bytes([Path.cwd()])
    audit=read(".audit/storage-alpha8/inventory-initial.json")
    policy=dict(per_task_bytes=256*2**20,campaign_bytes=512*2**20,evidence_bytes=4*2**20,
                workspace_max_bytes=audit["totals"]["workspace"]["bytes"]+512*2**20,
                reserve_free_bytes=2*2**30,max_concurrency=1)
    if (out/"policy.json").exists() and read(out/"policy.json")!=policy:raise ValueError("FROZEN_POLICY_CHANGED")
    atomic_json(out/"policy.json",policy)
    frozen=read("docs/audit/alpha7-frozen-output-hashes.json")
    assert len(frozen)==123 and all(digest(p)==sha for p,sha in frozen.items())
    full=Path("results/split-stress-alpha7/ecosis/report.json")
    assert digest(full)=="36204d732780f16ae5eb7e26dc97820d5a05276bda1a93b6994cd17f3315c591"
    original=read(full)
    association_path=Path("results/dependence-alpha6-final/ecosis-1/genus-association.json")
    dependence_path=Path("results/dependence-alpha6-final/ecosis-1/genus-report.json")
    coverage_path=Path("results/ecosis-alpha4-release/seed-17/technical_mean/report.json")
    association,dependence,coverage=map(read,(association_path,dependence_path,coverage_path))
    assert not association["test_target_accessed"] and not coverage["test_target_accessed"]
    task_path=Path("results/dependence-alpha6-final/ecosis-1/mean-task.json")
    task=read(task_path);rows=development_rows(task)
    assert scientific_fingerprint(rows)==original["development_input_sha256"]
    assert all(r.get("y") is None for r in task["observations"] if r["partition"]=="test")
    inventory=read("docs/audit/catalog-inventory-alpha8.json")
    catalog_entry=next(d for d in inventory["datasets"] if d["dataset_id"]==original["context"]["dataset_id"])
    identity=task_identity(dict(dataset_id=original["context"]["dataset_id"],content_version="1.0.0",
        dataset_revision=fingerprint({"catalog_revision":catalog_entry["dataset_revision"],"source_hashes":read("docs/audit/ecosis-repeat-qualification.json")["source_audit"]["freeze"]["source_hashes"]}),
        source_id="X",target_id="LMA_value_g/m2",representation="technical_mean; all 2151 bands",
        split_protocol="experimental_plot_sha256_v1; frozen grouped OOF and declared stress designs",
        independence_policy="whole plot/reference components; conditional between-plot independence",
        qualification_protocol="domains.bank.v0.1"))
    original_contract=execution_contract(identity,dict(input_sha256=digest(task_path),source_content_sha256=original["input_provenance"]["source_spectra_sha256"],
        split_folds_sha256=fingerprint(original["audit"]["reference_fold_set"]),dependency_policy=identity["independence_policy"],
        preprocessing="fold-local centering; no scaling; full axis",models="Methods PLS1..5, null, genus-only, genus+residual",
        protocol=original["protocol_version"],binaries={"methods_sha256":digest(library),"original_domains_transport_binary":"not separately recorded in alpha7 report; audited input frozen"},
        providers=original["engine_versions"],settings={"split_stress":original["config"],
            "supplemental_frozen_report_sha256":{p.name:digest(p) for p in (association_path,dependence_path,coverage_path)},
            "structural_record_sha256":digest("docs/audit/structure-alpha5-qualification.json"),
            "consolidation_controller_sha256":digest(__file__)},
        controller_sha256=fingerprint(read("docs/audit/alpha7-validation.json")["source_sha256_normalized_lf"])))
    store=StageStore(out/"state",out/"scratch",out/"evidence",Path.cwd(),policy)
    receipts=[]
    q={"identity":{"status":"exploratory","reason":None,"value":"Original sample keys/plots verified; assay events and plant independence conditional"},
       "xy_signal":{"status":"exploratory","reason":None,"value":{"null_rmse":146.99331012135553,"spectral_rmse":110.86776478755294}},
       "independent_support":{"status":"exploratory","reason":None,"value":{"samples":65,"plot_components":45}},
       "structural_stress":{"status":"exploratory","reason":None,"value":"Genus holdout degradation with partial size controls; effective global interventions"},
       "group_association":{"status":"exploratory","reason":None,"value":{"eta_squared":association["association"]["value"]["eta_squared"],"n_complete_factor_units":61,"n_components":43}},
       "within_group_skill":{"status":"exploratory","reason":None,"value":"Matched seen-level OOF residual skill; see retained eligibility/conditional intervals"},
       "within_group_intervention":{"status":"unavailable","reason":"TWO_REQUIRED_INNER_TRAINING_SCOPES_FAIL_MOVABLE_TARGET_POWER_GATE","value":None},
       "causal_attribution":{"status":"not_identifiable","reason":"BIOLOGICAL_COMPOSITION_AND_RANGE_ALTERNATIVES; NO_EFFECTIVE_WITHIN_GENUS_TEST","value":None}}
    def consolidate(_folder):
        scientific=compact_stress(original)
        scientific["group_target_association"]=compact_tree(association)
        scientific["within_group_evidence"]={k:compact_tree(dependence[k]) for k in
            ("prediction.within_group_incremental_skill","prediction.structural_dependence_evidence","audit","uncertainty")}
        ids={"coverage.effective_dimension","domain.centroid_distance","domain.dispersion_ratio","coverage.test_outside_fraction"}
        scientific["frozen_coverage"]={"report_sha256":digest(coverage_path),"context":coverage["context"],
            "metrics":[m for m in coverage["metrics"] if m["metric_id"] in ids],
            "fit_summary":{k:v for k,v in coverage["fit"].items() if isinstance(v,(str,int,float,bool)) or v is None}}
        scientific["unsupervised_structure"]={"status":"insufficient_information","reason":"FROZEN_ALPHA5_PRIMARY_ALL_NOISE_AND_WEAK_SENSITIVITY_SUPPORT",
            "value":None,"source_record_sha256":digest("docs/audit/structure-alpha5-qualification.json")}
        return evidence(identity,original_contract,scientific,q,["structure_sensitive_challenge"],
            ["Exploratory PLS-only development evidence; no low-dependence certification.",
             "Logical assay aliases do not establish independent laboratory event identities.",
             "Full target maps and model payloads require the frozen authorized local source/cache.",
             "Historical Domains transport binary is not separately recorded in the alpha7 report; do not promise full historical byte replay."])
    receipt,record=store.run(original_contract,"P4",file_plan(full,65536,4*2**20),consolidate,
                            lambda v:(verify_evidence(v),schema_check(v,"qualification-evidence")))
    receipts.append(receipt)
    if record is None:raise RuntimeError(receipt)
    registry=Path("docs/benchmarks/alpha8");registry.mkdir(parents=True,exist_ok=True)
    atomic_json(registry/"ecosis-evidence.json",record,4*2**20)
    atomic_json(registry/"ecosis-task.json",identity)
    by_id={r["physical_sample_id"]:r for r in rows}
    holdout=next(e for e in original["experiments"] if e["design_id"]=="holdout:genus")["value"]
    global0=original["interventions"][0]["attempts"][0]["value"]
    cells=[("genus_holdout_fold0",holdout["lineage"][0],holdout["oof"],None),
           ("global_attempt0_fold0",global0["lineage"][0],global0["oof"],lambda training:intervene(training,kind="global",factor="genus",seed=17,attempt=0))]
    replays={}
    for name,trace,oof,intervention in cells:
        training=[by_id[s] for s in trace["train_sample_ids"]]
        valid=[by_id[s] for s in trace["validation_sample_ids"]]
        scoped={"original":original_contract,"cell":name,"scope":trace["fold_id"],"domains_binary_sha256":digest(binary),
                "replay_controller_sha256":fingerprint({p:digest(p) for p in ("bridges/python/nirs4all_domains/split_stress.py","bridges/python/nirs4all_domains/predictive.py","bridges/python/nirs4all_domains/interventions.py")})}
        def replay(_folder,training=training,valid=valid,trace=trace,oof=oof,intervention=intervention):
            predictions,lineage=fit_outer(training,valid,library,original["config"],trace["fold_id"],intervention)
            expected=[r for r in oof if r["fold_id"]==trace["fold_id"]]
            assert sorted(predictions,key=lambda r:r["physical_sample_id"])==sorted(expected,key=lambda r:r["physical_sample_id"])
            assert lineage==trace
            return dict(exact_oof_equal=True,exact_full_lineage_equal=True,n_validation=len(valid),
                        lineage_sha256=fingerprint(lineage),predictions_sha256=fingerprint(sorted(predictions,key=lambda r:r["physical_sample_id"])),
                        scope=trace["fold_id"],test_target_accessed=False)
        receipt,value=store.run(scoped,"P3",file_plan(task_path,65536,65536,32,1 if intervention else 0),replay)
        receipts.append(receipt)
        if value is None:raise RuntimeError(receipt)
        replays[name]=value
    # New representative controlled execution; original four scientific controls
    # remain part of the baseline tests and retained alpha7 pilot evidence.
    source=Path("tests/fixtures/dependence/mixed.json");control=read(source)
    spec=dict(dataset_id=control["context"]["dataset_id"],content_version=control["context"]["content_version"],
        dataset_revision=digest(source),source_id="X",target_id="y",representation="technical_mean",split_protocol="component_hash17",
        independence_policy="declared complete fixture components",qualification_protocol="domains.split_stress.v0.1")
    config=read("configs/pilots/split-stress-controls-v1.json")
    config.update(holdout_factors=[],shuffle_reference=False,size_draws=0,intervention_attempts=1)
    stages,synthetic=bounded_qualify(source,spec,config,policy,workspace=Path.cwd(),state=out/"state",scratch=out/"scratch",output=out/"evidence",binary=binary,library=library)
    receipts.extend(stages)
    if synthetic is None:raise RuntimeError(stages[-1])
    atomic_json(registry/"mixed-control-evidence.json",synthetic,4*2**20)
    suite=freeze_suite([record,synthetic],"structure_sensitive_challenge",{
        "metric":"RMSE in each task's declared target unit; matched physical OOF IDs",
        "split":"Frozen reference and named structural stress contrasts; never choose using a new estimator",
        "target_access":"development outcomes only; retained Y_test sealed", "estimator_comparison_certified":False})
    schema_check(suite,"benchmark-suite");atomic_json(registry/"structure-challenge-suite.json",suite)
    empty=freeze_suite([record,synthetic],"candidate_low_structural_dependence",{"status":"No current task admitted; multi-estimator validation remains future"})
    atomic_json(registry/"low-dependence-candidate-suite.json",empty)
    artifacts=[]
    for p in sorted(registry.glob("*.json")):
        if p.name=="storage.json" or p.name=="datasets-sidecar.json":continue
        artifacts.append(dict(path=p.name,sha256=digest(p),bytes=p.stat().st_size,retention="essential_evidence"))
    manifest=dict(schema_version=1,protocol_version="domains.storage.v0.1",execution_id=record["execution_id"],artifacts=artifacts,
        cache_dependencies=[dict(content_sha256=digest(task_path),bytes=task_path.stat().st_size,provider="Datasets0.3.11 historical local canonical reproduction + audited mean export",access="public",local_locator_key="ecosis_alpha6_mean_task"),
                            dict(content_sha256=digest(full),bytes=full.stat().st_size,provider="Frozen Domains alpha7 report",access="requires_authorization",local_locator_key="ecosis_alpha7_full_report")],
        replay_grade="reconstructed_from_cache",measured_bytes=sum(a["bytes"] for a in artifacts),optional_archives=[],
        limitations=["Two representative cells exactly replayed; not all old attempts rerun.","Replay needs preserved local bytes plus matching Methods binary and controller; historical transport-binary identity is incomplete."])
    schema_check(manifest,"storage-manifest");verify_storage(manifest,registry);atomic_json(registry/"storage.json",manifest)
    sidecar=dict(schema_version=1,integration_protocol="domains.datasets_sidecar.v0.1",dataset_id=identity["dataset_id"],content_version="1.0.0",
        task_id=identity["task_id"],qualification_protocol=identity["qualification_protocol"],evidence_sha256=digest(registry/"ecosis-evidence.json"),
        evidence_ref="ecosis-evidence.json",purposes=record["purposes"])
    schema_check(sidecar,"datasets-sidecar");atomic_json(registry/"datasets-sidecar.json",sidecar)
    after=tree_bytes([Path.cwd()])
    qualification=dict(schema_version=1,version="0.1.0-alpha.8",frozen_files_unchanged=len(frozen),
        original_report_bytes=full.stat().st_size,compact_real_evidence_bytes=len(encoded(record)),compact_scientific_payload_bytes=len(encoded(record["scientific"])),
        registry_bytes=tree_bytes([registry]),policy=policy,real_cases={"A":"frozen EcoSIS reused; two representative cells replayed", "B":"ineligible; see frozen admission audit", "C":"ineligible; see frozen admission audit"},
        real_additional_tasks_executed=0,raw_bytes_downloaded=0,bytes_removed=0,bytes_migrated=0,replays=replays,
        stage_measurements=[{k:r.get(k) for k in ("stage","status","reason","cache_hit","duration_seconds","measured_scratch_bytes","measured_evidence_bytes","estimate")} for r in receipts],
        workspace_logical_before=before,workspace_logical_after=after,incremental_workspace_bytes=after-before,
        controlled_task_id=synthetic["task_id"],real_task_id=identity["task_id"],evidence_id=record["evidence_id"],suite_id=suite["suite_id"],
        replay_scope="Exact OOF and full lineage for one real genus holdout fold and one real global-attempt0 fold. No new real dataset or full old campaign executed.")
    atomic_json("docs/audit/alpha8-bank-qualification.json",qualification)
    assert all(digest(p)==sha for p,sha in frozen.items())
    print(json.dumps({k:qualification[k] for k in ("frozen_files_unchanged","compact_real_evidence_bytes","registry_bytes","incremental_workspace_bytes","replay_scope")},indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--binary",type=Path,required=True);parser.add_argument("--library",type=Path,required=True)
    args=parser.parse_args();run(args.out,args.binary.resolve(),args.library.resolve())
