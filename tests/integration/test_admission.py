"""Alpha.9 gates fixed before real fitting; native execution is required."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from nirs4all_domains.admission import DIMENSIONS, freeze_admission, verify_admission, paired_keys, target_semantics
from nirs4all_domains.bank import schema_check
from nirs4all_domains.comparison import ridge_on_frozen_folds
from nirs4all_domains.dependence import development_rows
from nirs4all_domains.predictive import _inner_fit, group_folds
from nirs4all_domains.storage import fingerprint

ROOT = Path(__file__).resolve().parents[2]


def specification():
    return dict(dataset_id="real", catalog_revision="revision", content_version="1", source_hashes={"original":"a"*64},
        scientific_reference=["original source"], permissions={k:{"status":"allowed","evidence":["source permission"]} for k in DIMENSIONS},
        source_id="X", target=dict(name="Moisture",semantic_role="quantitative_measurement",meaning="Oven moisture",unit="%",evidence=["original"]),
        identities={k:{"status":"verified","evidence":["original keys"]} for k in ("original_sample_keys","source_reference_alignment")},
        dependencies={"policy":"whole specimens"},factors={},representation="singleton",split={"policy":"identity only"},independent_units=20,
        missing_fields=["assay precision"],budget={"bytes":100},review_evidence=["source to reference audit"])


def pairs():
    a = [{"sample_key":str(i),"physical_id":"physical:"+str(i),"reference_key":"assay:"+str(i),"reference_unit":"%"} for i in range(12)]
    return {"m5":a,"mp5":copy.deepcopy(a)}, {"m5":[1100,1102],"mp5":[1100,1102]}


class AdmissionTests(unittest.TestCase):
    def test_changed_origin_after_admission_blocks_before_canonical_write(self):
        import importlib.util
        from types import SimpleNamespace
        from unittest.mock import patch
        from nirs4all_domains.storage import atomic_json,digest
        module=importlib.util.spec_from_file_location("alpha9_pilot",ROOT/"scripts/run_alpha9_pilot.py")
        runner=importlib.util.module_from_spec(module);module.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);leaf=root/"leaf";(leaf/"raw").mkdir(parents=True)
            archive=leaf/"raw/sensAIfood_Perten.zip";archive.write_bytes(b"admitted origin")
            for name in ("X.csv","Y.csv","M.csv"):(leaf/name).write_text("unchanged keyed input")
            s=specification();s["source_hashes"]={"archive":digest(archive),**{k:digest(leaf/k) for k in ("X.csv","Y.csv","M.csv")}}
            out=root/"out";atomic_json(out/"perten-admission.json",freeze_admission(s))
            archive.write_bytes(b"changed after admission, source tables unchanged")
            with patch("nirs4all_datasets.canonical.build_canonical",side_effect=AssertionError("provider must not write")):
                with self.assertRaisesRegex(ValueError,"ADMITTED_INPUT_CHANGED"):
                    runner.prepare(SimpleNamespace(leaf=leaf,out=out))

    def test_source_adapter_uses_original_reference_keys_ignoring_unkeyed_y(self):
        import importlib.util
        import pandas as pd
        module = importlib.util.spec_from_file_location("alpha9_pilot",ROOT/"scripts/run_alpha9_pilot.py")
        runner = importlib.util.module_from_spec(module); module.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/"raw").mkdir()
            pd.DataFrame([dict(sample_id="b",observation_id="ob",instrument="m",country="c",year="2000"),
                          dict(sample_id="a",observation_id="oa",instrument="m",country="c",year="2000")]).to_csv(root/"M.csv",sep=";",index=False)
            (root/"Y.csv").write_text("Moisture\n999\n888\n")
            waves=list(map(str,range(950,1651,5)))
            source=pd.DataFrame([dict(ID="a",Moisture=1,**{k:10 for k in waves}),dict(ID="b",Moisture=2,**{k:20 for k in waves})]).to_csv(index=False)
            with zipfile.ZipFile(root/"raw/sensAIfood_Perten.zip","w") as archive:archive.writestr("original.csv",source)
            runner.keyed_source_tables(root,root/"keyed")
            got=pd.read_csv(root/"keyed/Y.csv",sep=";").set_index("observation_id")
            self.assertEqual(got.at["oa","Moisture"],1);self.assertEqual(got.at["ob","Moisture"],2)

    def test_public_access_does_not_grant_other_permissions(self):
        s=specification(); s["permissions"]["publish_statistics"]={"status":"unknown","evidence":[]}
        self.assertIn("PUBLISH_STATISTICS_UNKNOWN",freeze_admission(s)["reasons"])

    def test_analysis_distinct_from_raw_redistribution(self):
        s=specification();s["permissions"]["redistribute_raw"]={"status":"denied","evidence":["no raw redistribution"]}
        record=freeze_admission(s);self.assertEqual(record["status"],"admitted")
        schema_check(record,"task-admission");verify_admission(record)

    def test_private_tier_is_not_an_analysis_denial(self):
        s=specification();s["permissions"]["access"]["evidence"]=["Authorized local private source"]
        self.assertEqual(freeze_admission(s)["status"],"admitted")

    def test_access_denial_blocks_even_if_analysis_allowed(self):
        s=specification();s["permissions"]["access"]={"status":"denied","evidence":["restriction"]}
        self.assertEqual(freeze_admission(s)["status"],"pending")

    def test_permission_without_evidence_rejected(self):
        s=specification();s["permissions"]["access"]["evidence"]=[]
        with self.assertRaisesRegex(ValueError,"EXPLICIT_EVIDENCE"):freeze_admission(s)

    def test_numeric_identifiers_are_not_regression_targets(self):
        for name in ("sample_number","Individual","genotype","sample_id","x"):
            with self.subTest(name=name):
                t=specification()["target"];t["name"]=name
                self.assertEqual(target_semantics(t),"NUMERIC_IDENTIFIER_OR_UNQUALIFIED_TARGET_SEMANTICS")

    def test_missing_semantics_and_units_not_inferred(self):
        t=specification()["target"];t["unit"]=None
        self.assertIn("MISSING_TARGET",target_semantics(t))

    def test_original_identity_and_reference_evidence_required(self):
        for field in ("original_sample_keys","source_reference_alignment"):
            s=specification();s["identities"][field]={"status":"unverified","evidence":[]}
            self.assertNotEqual(freeze_admission(s)["status"],"admitted")

    def test_local_repeated_row_labels_do_not_establish_physical_identity(self):
        s=specification();s["identities"]["original_sample_keys"]={"status":"row_counter","evidence":["1..150 repeated three times"]}
        self.assertIn("UNVERIFIED_ORIGINAL_SAMPLE_KEYS",freeze_admission(s)["reasons"])

    def test_admission_deterministic_and_cannot_consume_predictor_scores(self):
        s=specification();self.assertEqual(freeze_admission(s),freeze_admission(copy.deepcopy(s)))
        s["r2"]=.9
        with self.assertRaisesRegex(ValueError,"PRE_PERFORMANCE"):freeze_admission(s)

    def test_admission_invalidation_on_permissions_source_or_protocol(self):
        record=freeze_admission(specification())
        for field in ("content_version","source_hashes","split","permissions"):
            changed=copy.deepcopy(record);changed["specification"][field]="changed"
            with self.assertRaises((ValueError,TypeError,AttributeError)):verify_admission(changed)

    def test_paired_instruments_are_one_physical_population(self):
        s,a=pairs();self.assertEqual(paired_keys(s,a,["original source labels"])["n_physical_samples"],12)

    def test_cross_source_reordering_is_keyed(self):
        s,a=pairs();expected=paired_keys(s,a,["original"]);s["mp5"].reverse()
        self.assertEqual(paired_keys(s,a,["original"]),expected)

    def test_unmatched_keys_fail_without_row_position_fallback(self):
        s,a=pairs();s["mp5"][0]["sample_key"]="different"
        with self.assertRaisesRegex(ValueError,"UNMATCHED"):paired_keys(s,a,["original"])

    def test_pairing_requires_actual_original_key_and_evidence(self):
        s,a=pairs();s["mp5"][0]["reference_key"]=""
        with self.assertRaisesRegex(ValueError,"MISSING_ORIGINAL"):paired_keys(s,a,["original"])

    def test_reference_contradiction_and_shared_assay_refused(self):
        s,a=pairs();s["mp5"][0]["reference_value"]=1;s["m5"][0]["reference_value"]=2
        with self.assertRaisesRegex(ValueError,"CONTRADICTORY_REFERENCE"):paired_keys(s,a,["original"])
        s,a=pairs()
        for rows in s.values():rows[0]["reference_key"]=rows[1]["reference_key"]
        with self.assertRaisesRegex(ValueError,"SHARED_ASSAY"):paired_keys(s,a,["original"])

    def test_different_axes_preserved_with_direct_transfer_unavailable(self):
        s,a=pairs();a["mp5"]=[1101,1103,1105]
        record=paired_keys(s,a,["original"])
        self.assertEqual(record["direct_transfer"]["status"],"unavailable")
        self.assertIsNone(record["direct_transfer"]["value"])
        self.assertNotEqual(record["axes_sha256"]["m5"],record["axes_sha256"]["mp5"])


class NativeSecondaryFamilyTests(unittest.TestCase):
    def test_native_ridge_analytical_centered_penalty(self):
        from n4m.roles import Ridge
        model=Ridge(alpha=1.0,center_x=True,center_y=True,scale_x=False)
        model.fit([[-1.0],[0.0],[1.0]],[[1.0],[4.0],[7.0]])
        predicted=model.predict([[-2.0],[2.0]]).reshape(-1).tolist()
        # Centered X'X=2, X'Y=6; slope=6/(2+1)=2, intercept=4.
        self.assertAlmostEqual(predicted[0],0.0,delta=1e-10)
        self.assertAlmostEqual(predicted[1],8.0,delta=1e-10)

    def test_native_rank_failure_is_explicit_and_never_silently_retried(self):
        from nirs4all_domains.split_stress import run_design
        task=self.task();rows=development_rows(task)
        for i,r in enumerate(rows):r["x"]=[float((i+1)*(j+1)) for j in range(6)];r["y"]=float(i+1)
        folds=group_folds(rows,4,17,"outer")
        cfg=json.loads((ROOT/"configs/pilots/split-stress-controls-v1.json").read_text());cfg["max_components"]=6
        with self.assertRaisesRegex(RuntimeError,"(?i)(vanished|native|Methods|component)"):
            run_design(rows,folds,os.environ["N4DOMAINS_METHODS_LIBRARY"],cfg)

    def task(self):
        task=json.loads((ROOT/"tests/fixtures/dependence/mixed.json").read_text())
        task.setdefault("provenance",{})["reference_xy_blocked"]="false"
        for r in task["observations"]:r["metadata"]["validation_component_id"]=r["independence_group"]
        return task

    def test_native_ridge_frozen_folds_and_retained_instrument_isolation(self):
        task=self.task();rows=development_rows(task);folds=group_folds(rows,4,17,"outer")
        suite={"tasks":[{"task_id":"controlled"}],"selection_basis":"qualification evidence fixed before evaluation of a new estimator",
               "metric_contract":{"evaluation":{"context":task["context"],"development_input_sha256":fingerprint(rows),"outer_fold_set_sha256":fingerprint(folds)}}}
        suite["suite_id"]=fingerprint(suite)
        cfg=dict(seed=17,inner_folds=3,max_components=3)
        first=ridge_on_frozen_folds(task,folds,os.environ["N4DOMAINS_METHODS_LIBRARY"],cfg,suite)
        self.assertEqual(first["status"],"computed",first)
        changed=copy.deepcopy(task)
        for r in changed["observations"]:
            if r["partition"]=="test":r["x"]=[1e10]*len(r["x"]);r["y"]=-1e15;r["metadata"]["instrument"]="heldout-different"
        self.assertEqual(first,ridge_on_frozen_folds(changed,folds,os.environ["N4DOMAINS_METHODS_LIBRARY"],cfg,suite))
        self.assertTrue(all(r["native_fit_lineage_verified"] for r in first["value"]["lineage"]))
        changed=copy.deepcopy(task);changed["observations"][0]["x"][0]+=1
        with self.assertRaisesRegex(ValueError,"CONTENT_OR_FOLDS_MISMATCH"):
            ridge_on_frozen_folds(changed,folds,os.environ["N4DOMAINS_METHODS_LIBRARY"],cfg,suite)

    def test_secondary_family_requires_prior_suite_freeze(self):
        with self.assertRaisesRegex(ValueError,"SUITE_MUST_BE_FROZEN"):
            ridge_on_frozen_folds({}, {}, "missing", {}, {})

    def test_unqualified_family_transform_combination_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNQUALIFIED_ESTIMATOR"):
            _inner_fit([],"missing",17,3,3,"scope",family="ridge",residual_factor="factor")


if __name__=="__main__":unittest.main()
