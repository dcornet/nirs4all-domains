"""Real Methods and DAG scheduler scientific gates; no numerical mocks."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from nirs4all_domains.dependence import (audit_factors, development_rows, predictive_dependence,
                                        paired_bootstrap, validate_folds)
from nirs4all_domains.predictive import group_folds, group_means, group_prediction, _inner_fit

ROOT=Path(__file__).resolve().parents[2]
SPEC={"field":"factor","source_column":"factor","provenance":"frozen controlled input","available_at_prediction":True}


def represented(kind):
    with tempfile.TemporaryDirectory() as folder:
        out=Path(folder)/"task.json"
        subprocess.run([os.environ["N4DOMAINS_BIN"],"represent",str(ROOT/"tests/fixtures/dependence"/(kind+".json")),
            "--out",str(out),"--methods-library",os.environ["N4DOMAINS_METHODS_LIBRARY"]],check=True,capture_output=True)
        return json.loads(out.read_text())


class DependenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results={}
        for kind in ("group_only","trait_only","mixed","independent_y","unseen","high_cardinality"):
            cls.results[kind]=predictive_dependence(represented(kind),os.environ["N4DOMAINS_METHODS_LIBRARY"],SPEC,
                outer_folds=4,inner_folds=3,max_components=6,draws=200)

    def test_group_only_trait_only_mixed_and_independent_controls(self):
        def error(kind,model):return self.results[kind]["scores"][model]["value"]["rmse"]["value"]
        self.assertLess(error("group_only","group_only"),1e-9)
        self.assertLess(error("group_only","group_plus_residual"),1e-9)
        for kind in ("trait_only","mixed"):
            self.assertLess(error(kind,"spectral"),1e-9)
            self.assertLess(error(kind,"group_plus_residual"),1e-9)
            self.assertGreater(error(kind,"group_only"),1.)
        self.assertLess(error("mixed","group_only"),error("mixed","null"))
        independent=self.results["independent_y"]
        self.assertLess(independent["uncertainty"]["interval_95"]["value"]["residual_over_group"][0],0.)

    def test_unseen_and_high_cardinality_never_use_validation_means(self):
        for kind in ("unseen","high_cardinality"):
            r=self.results[kind]
            self.assertEqual(r["audit"]["fallback_fraction"],1.)
            self.assertEqual(r["prediction.within_group_incremental_skill"]["status"],"unavailable")
            for row in r["oof"]:
                self.assertEqual(row["group_only"],row["null"])
                self.assertEqual(row["baseline_source"],"global_training_fallback")
        train=[{"physical_sample_id":"a","metadata":{"factor":"seen"},"y":2.},
               {"physical_sample_id":"b","metadata":{"factor":"seen"},"y":4.}]
        baseline=group_means(train,"factor")
        self.assertEqual(group_prediction({"metadata":{"factor":"seen"}},baseline,"factor"),(3.,"level_training_mean"))
        self.assertEqual(group_prediction({"metadata":{}},baseline,"factor"),(3.,"global_training_fallback"))

    def test_actual_inner_and_outer_residualization_and_reconstruction(self):
        task=represented("mixed");rows=development_rows(task);by_id={r["physical_sample_id"]:r for r in rows}
        for outer in self.results["mixed"]["lineage"]:
            train=set(outer["train_sample_ids"]);valid=set(outer["validation_sample_ids"])
            for event in outer["residual_fit_events"]:
                ids=event["baseline"]["training_ids"]
                self.assertTrue(set(ids)<=train);self.assertFalse(set(ids)&valid)
                self.assertEqual(event["baseline"],group_means([by_id[s] for s in ids],"factor"))
                self.assertFalse(set(ids)&set(event["validation_ids"]))
            for row in self.results["mixed"]["oof"]:
                self.assertEqual(row["group_plus_residual"],row["group_only"]+row["residual_correction"])

    def test_inner_holdout_targets_do_not_change_fitted_means_or_artifacts(self):
        rows=development_rows(represented("mixed"));folds=group_folds(rows,3,17,"audit")
        _,before=_inner_fit(rows,os.environ["N4DOMAINS_METHODS_LIBRARY"],17,3,3,"audit",residual_factor="factor")
        changed=copy.deepcopy(rows);holdout=set(folds["folds"][0]["validation_sample_ids"])
        for row in changed:
            if row["physical_sample_id"] in holdout:row["y"]+=1000.
        _,after=_inner_fit(changed,os.environ["N4DOMAINS_METHODS_LIBRARY"],17,3,3,"audit",residual_factor="factor")
        # DAG may execute the selected candidate again. Selection can change
        # when validation Y changes; each common candidate's fitted state cannot.
        events=lambda r:{e["n_components"]:e for e in r["residual_fit_events"] if e["fold_id"]==folds["folds"][0]["fold_id"]}
        self.assertEqual(events(before),events(after))

    def test_retained_mutation_reorder_repeat_invariance_and_identity_join(self):
        task=represented("mixed")
        kwargs=dict(outer_folds=4,inner_folds=3,max_components=6,draws=200)
        changed=copy.deepcopy(task)
        for row in changed["observations"]:
            if row["partition"]=="test":row["y"]=-1e30;row["x"]=[1e30]*6
        changed["observations"].reverse()
        rerun=predictive_dependence(changed,os.environ["N4DOMAINS_METHODS_LIBRARY"],SPEC,**kwargs)
        self.assertEqual(self.results["mixed"],rerun)
        repeats=predictive_dependence(represented("repeats"),os.environ["N4DOMAINS_METHODS_LIBRARY"],SPEC,**kwargs)
        self.assertEqual(self.results["mixed"],repeats)
        rows=development_rows(task);folds=group_folds(rows,4,17,"outer")
        # Same-sized identity reassignment that separates a component must fail.
        bad=copy.deepcopy(folds)
        a,b=bad["folds"][0]["validation_sample_ids"][0],bad["folds"][1]["validation_sample_ids"][0]
        for fold in bad["folds"]:
            for key in ("train_sample_ids","validation_sample_ids"):
                fold[key]=[b if s==a else a if s==b else s for s in fold[key]]
        import dag_ml
        with self.assertRaises(dag_ml.DagMlError):validate_folds(rows,bad)

    def test_bootstrap_keeps_pairs_components_multiplicity_and_replays(self):
        oof=self.results["mixed"]["oof"]
        a=paired_bootstrap(oof,200,17)
        self.assertEqual(a,paired_bootstrap(oof,200,17))
        self.assertEqual(a["successful"],200);self.assertEqual(a["failed"],0)
        self.assertTrue(any(len(set(d["components"]))<len(d["components"]) for d in a["draws"]))
        self.assertIn("excludes model-refit uncertainty",a["conditioning"])

    def test_factor_audit_scope_missing_levels_and_reference_guard(self):
        task=represented("mixed");rows=development_rows(task);folds=group_folds(rows,4,17,"outer")
        rows[0]["metadata"].pop("factor")
        audit=audit_factors(rows,[SPEC],folds)[0]
        self.assertEqual(audit["missing_ids"],[rows[0]["physical_sample_id"]])
        task["provenance"]["reference_xy_blocked"]="true"
        with self.assertRaisesRegex(ValueError,"reference audit"):development_rows(task)

    def test_packaged_configuration_schema_matches_repository_contract(self):
        import nirs4all_domains.dependence as module
        self.assertEqual(json.loads((ROOT/"schemas/dependence-config.v1.schema.json").read_text()),
            json.loads(Path(module.__file__).with_name("dependence-config.v1.schema.json").read_text()))
        import jsonschema
        schema=json.loads((ROOT/"schemas/task.v1.schema.json").read_text())
        for path in (ROOT/"tests/fixtures/dependence").glob("*.json"):
            jsonschema.validate(json.loads(path.read_text()),schema)

    def test_cli_workflow_schema_determinism_and_output_preservation(self):
        import sys
        sys.path.insert(0,str(ROOT/"scripts"))
        from check_dependence_report import check
        config=json.loads((ROOT/"configs/pilots/dependence-v1.json").read_text())
        config.update(outer_folds=4,max_components=6,draws=200,factors=[SPEC])
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);cp=folder/"config.json";cp.write_text(json.dumps(config))
            reports=[]
            for repeat in (1,2):
                out=folder/str(repeat)
                command=[os.environ["N4DOMAINS_BIN"],"dependence",str(ROOT/"tests/fixtures/dependence/mixed.json"),
                    "--config",str(cp),"--out",str(out),"--methods-library",os.environ["N4DOMAINS_METHODS_LIBRARY"],"--python",sys.executable]
                subprocess.run(command,check=True,capture_output=True)
                report=json.loads((out/"report.json").read_text());check(report)
                reports.append((out/"report.json").read_bytes())
                original=(out/"report.json").read_bytes()
                self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
                self.assertEqual(original,(out/"report.json").read_bytes())
            self.assertEqual(reports[0],reports[1])


if __name__=="__main__":unittest.main()
