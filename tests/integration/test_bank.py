"""Alpha.8 adversarial storage, identity, restart and native consolidation gates."""
import copy
import gzip
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nirs4all_domains.bank import bounded_qualify, schema_check
from nirs4all_domains.registry import (TASK_FIELDS, compact_stress, compressed_archive, evidence,
    execution_contract, freeze_suite, select, task_identity, verify_evidence, verify_storage)
from nirs4all_domains.storage import (StageStore, atomic_json, cleanup_plan, digest, encoded, estimate,
                                    fingerprint, safe_path, serial_lease, tree_bytes)

ROOT = Path(__file__).resolve().parents[2]


def policy():
    return dict(per_task_bytes=256*2**20, campaign_bytes=512*2**20, evidence_bytes=4*2**20,
                workspace_max_bytes=1024*2**20, reserve_free_bytes=0, max_concurrency=1)


def identity():
    return task_identity({k:k+"-v1" for k in TASK_FIELDS})


def contract():
    from nirs4all_domains.registry import EXECUTION_FIELDS
    return execution_contract(identity(), {k:"a"*64 if k.endswith("sha256") else {"setting":1} for k in EXECUTION_FIELDS})


def record():
    return evidence(identity(), contract(), {"oof":[]},
        {"identity":{"status":"unavailable", "reason":"UNQUALIFIED", "value":None}},
        ["insufficient_evidence"], ["Synthetic contract fixture"], "synthetic")


class StorageTests(unittest.TestCase):
    def test_per_task_budget_and_persistent_cap_apply_across_stages(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);pol=policy();pol.update(per_task_bytes=150,evidence_bytes=100)
            store=StageStore(root/"state",root/"scratch",root/"evidence",root,pol)
            plan=dict(inputs=[],scratch_bytes=50,evidence_bytes=50,expected_fits=0,expected_permutations=0,uncertainty="bounded")
            self.assertEqual(store.run(contract(),"P1",plan,lambda path:{"v":1})[0]["status"],"computed")
            rejected,_=store.run(contract(),"P2",plan,lambda path:self.fail("cumulative task cap bypassed"))
            self.assertIn("CUMULATIVE_TASK_DISK",rejected["reason"])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);pol=policy();pol["evidence_bytes"]=20
            store=StageStore(root/"state",root/"scratch",root/"evidence",root,pol)
            plan=dict(inputs=[],scratch_bytes=0,evidence_bytes=16,expected_fits=0,expected_permutations=0,uncertainty="bounded")
            self.assertEqual(store.run(contract(),"P1",plan,lambda path:{"v":1})[0]["status"],"computed")
            rejected,_=store.run(contract(),"P2",plan,lambda path:self.fail("cumulative evidence cap bypassed"))
            self.assertIn("CUMULATIVE_TASK_EVIDENCE",rejected["reason"])
    def test_read_only_audit_and_link_accounting(self):
        spec = importlib.util.spec_from_file_location("storage_audit", ROOT/"scripts/audit_storage.py")
        module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix="bank spaces ") as temp:
            root = Path(temp); (root/"a").write_bytes(b"data")
            os.link(root/"a", root/"b")
            before = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in root.iterdir()}
            result = module.scan([("test",root),("overlap",root)], hash_duplicates=False)
            self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in root.iterdir()})
            self.assertEqual(result["totals"]["test"]["bytes"],8)
            self.assertEqual(sum(x["unique"] for x in result["files"]),1)
            self.assertEqual(tree_bytes([root,root]),4)

    def test_estimate_counts_shared_verified_content_once_and_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); p=root/"input";p.write_bytes(b"abc")
            entry={"path":str(p),"sha256":digest(p),"bytes":3}
            plan=dict(inputs=[entry,entry],scratch_bytes=20,evidence_bytes=10,expected_fits=6,expected_permutations=1,uncertainty="bounded")
            result=estimate(plan,policy(),root,root/"scratch",root/"evidence")
            self.assertEqual((result["input_bytes"],result["new_input_bytes"],result["peak_incremental_bytes"]),(3,0,30))
            self.assertEqual(list(root.iterdir()),[p])
            p.write_bytes(b"bad")
            with self.assertRaisesRegex(ValueError,"MISMATCH"):estimate(plan,policy(),root,root,root)

    def test_external_cache_bytes_are_accounted_without_overlap_or_new_acquisition(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);workspace=root/"workspace";workspace.mkdir()
            (workspace/"local").write_bytes(b"abc")
            cached=root/"provider-cache";cached.write_bytes(b"1234")
            entry={"path":str(cached),"sha256":digest(cached),"bytes":4}
            plan=dict(inputs=[entry,entry],scratch_bytes=0,evidence_bytes=0,expected_fits=0,expected_permutations=0,uncertainty="measured")
            result=estimate(plan,policy(),workspace,workspace/"scratch",workspace/"evidence")
            self.assertEqual(result["measured_existing_bytes"],7)
            self.assertEqual(result["existing_verified_input_bytes"],4)
            self.assertEqual(result["new_input_bytes"],0)

    def test_budget_and_available_volume_refuse_before_callback(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); plan=dict(inputs=[],scratch_bytes=100,evidence_bytes=10,expected_fits=6,expected_permutations=0,uncertainty="bounded")
            pol=policy();pol["per_task_bytes"]=10
            store=StageStore(root/"state",root/"scratch",root/"evidence",root,pol)
            called=[];status,value=store.run(contract(),"P3",plan,lambda path:called.append(path))
            self.assertEqual(status["status"],"budget_exceeded");self.assertIsNone(value);self.assertEqual(called,[])
            with patch("nirs4all_domains.storage.shutil.disk_usage",return_value=type("Usage",(),{"free":0})()):
                result=estimate(plan,policy(),root,root,root)
            self.assertEqual(result["status"],"insufficient_storage")

    def test_atomic_restart_after_crash_and_verified_cache_hit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);store=StageStore(root/"state",root/"scratch",root/"evidence",root,policy())
            plan=dict(inputs=[],scratch_bytes=4096,evidence_bytes=4096,expected_fits=0,expected_permutations=0,uncertainty="bounded")
            def crash(path):
                (path/"half.part").write_bytes(b"partial")
                raise KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):store.run(contract(),"P2",plan,crash)
            first=json.loads((root/"state/journal.json").read_text());self.assertEqual(next(iter(first["runs"].values()))["status"],"running")
            receipt,value=store.run(contract(),"P2",plan,lambda path:{"answer":42})
            self.assertEqual((receipt["status"],receipt["attempt"],receipt["previous_status"]),("computed",2,"running"))
            self.assertTrue(list((root/"scratch").rglob("half.part")))
            hit,again=store.run(contract(),"P2",plan,lambda path:self.fail("unexpected replay"))
            self.assertTrue(hit["cache_hit"]);self.assertEqual(again,value)
            safe_path(root/"evidence",receipt["artifact"]).write_text("{}")
            with self.assertRaisesRegex(ValueError,"CORRUPT"):store.run(contract(),"P2",plan,lambda path:{})

    def test_failed_task_isolated_and_estimate_underrun_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);store=StageStore(root/"state",root/"scratch",root/"evidence",root,policy())
            plan=dict(inputs=[],scratch_bytes=0,evidence_bytes=4096,expected_fits=0,expected_permutations=0,uncertainty="deliberately too small")
            def callback(path):
                (path/"extra").write_bytes(b"overflow")
                return {"valid":True}
            status,value=store.run(contract(),"P2",plan,callback)
            self.assertEqual(status["status"],"failed");self.assertIn("ESTIMATE_UNDERRUN",status["reason"]);self.assertIsNone(value)
            other=contract();other["execution"]["input_sha256"]="b"*64
            ok,value=store.run(other,"P2",plan,lambda path:{"good":True})
            self.assertEqual(ok["status"],"computed")

    def test_campaign_reservations_partial_runs_and_serial_lease(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);pol=policy();pol["campaign_bytes"]=8192
            store=StageStore(root/"state",root/"scratch",root/"evidence",root,pol)
            plan=dict(inputs=[],scratch_bytes=4096,evidence_bytes=4096,expected_fits=0,expected_permutations=0,uncertainty="bounded")
            store.run(contract(),"P1",plan,lambda path:{"v":1})
            status,_=store.run(contract(),"P2",plan,lambda path:self.fail("budget not enforced"))
            self.assertIn("CAMPAIGN",status["reason"])
            with serial_lease(root/"lease"):
                with self.assertRaisesRegex(RuntimeError,"BUSY"):
                    with serial_lease(root/"lease"):pass

    def test_cleanup_plan_protects_frozen_shared_running_unknown_and_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ("frozen","referenced","running","owned","unknown"):(root/name).write_text(name)
            owned=[{"path":n,"sha256":digest(root/n),"retention":"scratch","validated":True} for n in ("frozen","referenced","running","owned")]
            result=cleanup_plan(root,owned,[{"local_root":str(root),"artifacts":[{"path":"referenced"}]}],[root/"frozen"],[root/"running"])
            self.assertEqual([e["path"] for e in result["eligible"]],["owned"])
            self.assertEqual(result["bytes_removed"],0);self.assertTrue((root/"unknown").exists())
            cache_result=cleanup_plan(root,[owned[-1]],[],shared_caches=[root])
            self.assertEqual(cache_result["eligible"],[])
            os.link(root/"owned",root/"hardlink")
            self.assertEqual(cleanup_plan(root,[owned[-1]],[])["eligible"],[])

    def test_portable_paths_reject_escapes_windows_drives_and_spaces_work(self):
        with tempfile.TemporaryDirectory(prefix="Windows path spaces ") as temp:
            root=Path(temp)
            for path in ("../bad","C:/private","D:\\secret","/absolute","a/../../b"):
                with self.assertRaises(ValueError):safe_path(root,path)
            # Hosted Windows TEMP can use an NTFS 8.3 alias (RUNNER~1).
            # The public result is canonical, including existing ancestors.
            self.assertEqual(safe_path(root,"one space/evidence.json"),(root/"one space/evidence.json").resolve())


class RegistryTests(unittest.TestCase):
    def test_restricted_missing_source_inventory_is_metadata_only(self):
        from nirs4all_domains.inventory import catalog_inventory
        import yaml
        descriptor={"schema_version":"2.0","id":"restricted_fixture","name":"Restricted fixture", "description":"Metadata only",
            "tier":"private", "sources":[{"source_id":"X","axis_unit":"nm"}],
            "variables":[{"name":"Y","role":"target","type":"numeric"}],
            "provenance":{"contributor":"fixture"},"governance":{"license":"LicenseRef-not-cleared"}}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/"catalog/datasets";folder.mkdir(parents=True)
            (folder/"restricted_fixture.yaml").write_text(yaml.safe_dump(descriptor))
            fake=type("Revision",(),{"stdout":"a"*40})()
            with patch("nirs4all_domains.inventory.subprocess.run",return_value=fake),patch("nirs4all_datasets.get",side_effect=AssertionError("No matrix acquisition")),patch("nirs4all_datasets.retrieve",side_effect=AssertionError("No source download")):
                result=catalog_inventory(root)
            self.assertEqual(result["counts"]["datasets"],1)
            self.assertIn("RESTRICTED_TIER_NO_ACQUISITION_AUTHORIZATION",result["datasets"][0]["blockers"])
            self.assertNotIn(str(root),encoded(result).decode())

    def test_unavailable_evidence_has_explicit_reason_and_revision_selection(self):
        r=record()
        unavailable=evidence(r["task"],r["contract"],{},r["qualifications"],r["purposes"],r["limitations"],"real","unavailable","AUTHORIZED_SOURCE_MISSING")
        verify_evidence(unavailable);schema_check(unavailable,"qualification-evidence")
        with self.assertRaisesRegex(ValueError,"STATUS_REASON"):
            evidence(r["task"],r["contract"],{},r["qualifications"],r["purposes"],r["limitations"],"real","unavailable")
        real=evidence(r["task"],r["contract"],{},r["qualifications"],r["purposes"],r["limitations"],"real")
        with self.assertRaisesRegex(ValueError,"AMBIGUOUS"):
            select([real,unavailable],"insufficient_evidence")
    def test_every_reuse_dependency_changes_execution_identity(self):
        original=contract();base=fingerprint(original)
        for field in original["execution"]:
            changed=copy.deepcopy(original);changed["execution"][field]="changed"
            self.assertNotEqual(fingerprint(changed),base,field)
        for field in TASK_FIELDS:
            spec={k:identity()[k] for k in TASK_FIELDS};spec[field]="changed"
            self.assertNotEqual(task_identity(spec)["task_id"],identity()["task_id"],field)

    def test_evidence_status_schema_digest_and_no_heavy_arrays(self):
        r=record();schema_check(r,"qualification-evidence");verify_evidence(r)
        bad=copy.deepcopy(r);bad["scientific"]["x"]=[[1,2]]
        with self.assertRaises(ValueError):evidence(identity(),contract(),bad["scientific"],r["qualifications"],r["purposes"],r["limitations"])
        bad=copy.deepcopy(r);bad["qualifications"]["identity"]["value"]=True
        with self.assertRaises(Exception):schema_check(bad,"qualification-evidence")
        bad=copy.deepcopy(r);bad["scientific"]["metric"]=123
        with self.assertRaises(ValueError):verify_evidence(bad)

    def test_absent_metadata_powerless_and_independent_y_never_certify_low_dependence(self):
        for reason in ("NO_METADATA","NO_EFFECTIVE_WITHIN_INTERVENTION","NO_MEANINGFUL_XY_SIGNAL","UNQUALIFIED_IDENTITY"):
            with self.assertRaisesRegex(ValueError,"INSUFFICIENT_EVIDENCE"):
                evidence(identity(),contract(),{}, {"structural_stress":{"status":"unavailable","reason":reason,"value":None}},
                         ["candidate_low_structural_dependence"],[reason])

    def test_suite_excludes_synthetic_and_does_not_accept_new_estimator_scores(self):
        r=record();self.assertEqual(freeze_suite([r],"insufficient_evidence",{"metric":"rmse"})["tasks"],[])
        real=evidence(r["task"],r["contract"],{},r["qualifications"],r["purposes"],r["limitations"],"real")
        a=freeze_suite([real],"insufficient_evidence",{"metric":"RMSE in task units"})
        self.assertEqual(a,freeze_suite([real],"insufficient_evidence",{"metric":"RMSE in task units"}));schema_check(a,"benchmark-suite")
        self.assertEqual(len(select([real],"insufficient_evidence")),1)

    def test_manifest_and_deterministic_compression_verify_actual_bytes(self):
        data=b"repeatable evidence"*100
        zipped,receipt=compressed_archive(data);self.assertEqual(zipped,compressed_archive(data)[0]);self.assertEqual(gzip.decompress(zipped),data)
        self.assertEqual(receipt["mtime"],0)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/"artifact.json").write_bytes(data)
            manifest={"schema_version":1,"artifacts":[{"path":"artifact.json","bytes":len(data),"sha256":digest(root/"artifact.json")}]}
            self.assertTrue(verify_storage(manifest,root));(root/"artifact.json").write_bytes(b"changed")
            with self.assertRaises(ValueError):verify_storage(manifest,root)

    def test_additive_packaged_schemas_match_and_reject_nonportable_refs(self):
        for name in ("benchmark-task","qualification-evidence","storage-manifest","benchmark-suite","datasets-sidecar"):
            package=ROOT/"bridges/python/nirs4all_domains"/(name+".v1.schema.json")
            self.assertEqual(package.read_bytes(),(ROOT/"schemas"/package.name).read_bytes())
        schema_check(identity(),"benchmark-task")

    def test_paired_sources_join_by_declared_identity_not_position(self):
        from nirs4all_domains.dataset import task_from_dataset
        from types import SimpleNamespace
        import numpy as np
        import pandas as pd
        class Paired:
            id="paired-control"
            descriptor=SimpleNamespace(versions=SimpleNamespace(content="1.0.0"),
                sources=[SimpleNamespace(source_id=s,axis_unit="nm") for s in ("A","B")])
            def sources(self):return ["A","B"]
            def sample_ids(self,s):return np.array(["p1","p2"] if s=="A" else ["p2","p1"])
            def observation_ids(self,s):return np.array([s+v for v in self.sample_ids(s)])
            def x(self,s):return np.array([[1.,2.],[3.,4.]] if s=="A" else [[30.,40.],[10.,20.]])
            def wavelengths(self,s):return np.array([1100.,1200.])
            def metadata(self):return pd.DataFrame({"sample_id":["p2","p1"],"factor":["F2","F1"]})
            def y(self,target):return pd.DataFrame({"sample_id":["p2","p1"],"y":[999.,1.]})
            def split(self,name):return pd.DataFrame({"sample_id":["p1","p2"],"partition":["train","test"]})
        config={"source_id":"A","target_id":"y","content_version":"1.0.0","split_id":"fixed",
                "partition_labels":{"train":"train","test":"test"},"sample_identity_confirmed":True,"signal_unit":"supplied"}
        left=task_from_dataset(Paired(),config);right=task_from_dataset(Paired(),dict(config,source_id="B"))
        pairs={r["physical_sample_id"]:r for r in right["observations"]}
        first=left["observations"][0];self.assertEqual(first["x"],[1.,2.])
        self.assertEqual(pairs[first["physical_sample_id"]]["x"],[10.,20.])
        self.assertEqual(pairs[first["physical_sample_id"]]["y"],first["y"])
        self.assertEqual(len(pairs),2)  # two objects, not four source rows
        with self.assertRaisesRegex(ValueError,"Physical identities"):
            task_from_dataset(Paired(),dict(config,sample_identity_confirmed=False))


class NativeBankTests(unittest.TestCase):
    def test_real_work_requires_frozen_admission_before_native_fit(self):
        source=ROOT/"tests/fixtures/dependence/mixed.json";data=json.loads(source.read_text())
        spec={k:k+"-v1" for k in TASK_FIELDS}
        spec.update({k:data["context"][k] for k in ("dataset_id","content_version","source_id","target_id")})
        with self.assertRaisesRegex(ValueError,"ADMISSION_REQUIRED"):
            bounded_qualify(source,spec,{},policy(),workspace=ROOT,state=ROOT,scratch=ROOT,output=ROOT,binary="missing",library="missing",domain="real")

    def test_bounded_native_pipeline_compact_evidence_and_checkpoint_reuse(self):
        source=ROOT/"tests/fixtures/dependence/mixed.json";data=json.loads(source.read_text())
        spec={k:k+"-v1" for k in TASK_FIELDS};spec.update({k:data["context"][k] for k in ("dataset_id","content_version","source_id","target_id")})
        config=json.loads((ROOT/"configs/pilots/split-stress-controls-v1.json").read_text())
        spec.update(representation="technical_mean",qualification_protocol="domains.split_stress.v0.1")
        config.update(holdout_factors=[],shuffle_reference=False,size_draws=0,intervention_attempts=1)
        with tempfile.TemporaryDirectory(prefix="bank native space ") as temp:
            root=Path(temp)
            args=dict(workspace=root,state=root/"state",scratch=root/"scratch",output=root/"evidence",binary=os.environ["N4DOMAINS_BIN"],library=os.environ["N4DOMAINS_METHODS_LIBRARY"])
            receipts,final=bounded_qualify(source,spec,config,policy(),**args)
            self.assertEqual([r["status"] for r in receipts],["computed"]*4,receipts[-1])
            verify_evidence(final);schema_check(final,"qualification-evidence")
            self.assertLess(len(encoded(final)),4*2**20)
            self.assertFalse(final["scientific"]["deep"]["test_target_accessed"])
            again,replayed=bounded_qualify(source,spec,config,policy(),**args)
            self.assertEqual(replayed,final);self.assertTrue(all(r["cache_hit"] for r in again))
            for p in (root/"evidence").rglob("*.json"):
                self.assertNotIn('"x":',p.read_text())


if __name__=="__main__":unittest.main()
