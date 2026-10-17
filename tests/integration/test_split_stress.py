"""Alpha.7 scientific controls and actual native DAG/Methods leakage adversaries."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from nirs4all_domains.dependence import development_rows
from nirs4all_domains.interventions import components, exchangeability, intervene
from nirs4all_domains.predictive import group_folds, _inner_fit, native_summary
from nirs4all_domains.split_stress import (factor_holdout, design_audit, run_design, run_experiments,
    size_match_rows, paired_comparison, fit_outer, summarize)

ROOT=Path(__file__).resolve().parents[2]
CONFIG=json.loads((ROOT/"configs/pilots/split-stress-controls-v1.json").read_text())


def task(kind="mixed"):
    from nirs4all_domains.dependence import audit_representation
    data=json.loads((ROOT/"tests/fixtures/dependence"/(kind+".json")).read_text())
    with tempfile.TemporaryDirectory() as folder:
        return audit_representation(data,os.environ["N4DOMAINS_BIN"],os.environ["N4DOMAINS_METHODS_LIBRARY"],Path(folder))


def transform(attempt=0,kind="within_factor"):
    return lambda rows:intervene(rows,kind=kind,factor="factor",seed=17,attempt=attempt)


class SplitIdentityTests(unittest.TestCase):
    def test_transitive_factor_closure_and_unknown_levels(self):
        rows=development_rows(task())
        for r in rows:r["metadata"]["factor"]=r["independence_group"]
        rows[0]["metadata"]["factor"]="A";rows[1]["metadata"]["factor"]="B"
        rows[2]["metadata"]["factor"]="B";rows[3]["metadata"]["factor"]="C"
        rows[4]["metadata"]["factor"]="C"
        result=factor_holdout(rows,"factor",4)
        linked=next(c for c in result["closures"] if rows[0]["physical_sample_id"] in c["physical_ids"])
        self.assertTrue({r["physical_sample_id"] for r in rows[:6]}<=set(linked["physical_ids"]))
        by={r["physical_sample_id"]:r for r in rows}
        for f in result["value"]["folds"]:
            tr={by[s]["metadata"]["factor"] for s in f["train_sample_ids"]}
            va={by[s]["metadata"]["factor"] for s in f["validation_sample_ids"]}
            self.assertFalse(tr&va)
        for r in rows:r["metadata"]["factor"]="one"
        self.assertEqual(factor_holdout(rows,"factor")["status"],"unavailable")
        for r in rows:r["metadata"].pop("factor")
        self.assertEqual(factor_holdout(rows,"factor")["reason"],"FEWER_THAN_TWO_OBSERVED_FACTOR_LEVELS")

    def test_reference_and_random_allocation_are_identity_only(self):
        rows=development_rows(task());a=group_folds(rows,4,17,"outer")
        b=group_folds(rows,4,17,"shuffle",allocation="shuffle")
        self.assertNotEqual(a,b)
        for r in rows:r["y"]*=1e6
        self.assertEqual(a,group_folds(rows,4,17,"outer"))
        self.assertEqual(b,group_folds(rows,4,17,"shuffle",allocation="shuffle"))
        for f in b["folds"]:
            tr={r["independence_group"] for r in rows if r["physical_sample_id"] in f["train_sample_ids"]}
            va={r["independence_group"] for r in rows if r["physical_sample_id"] in f["validation_sample_ids"]}
            self.assertFalse(tr&va)

    def test_whole_vector_maps_preserve_factor_and_reference_integrity(self):
        rows=development_rows(task())
        changed,receipt=intervene(rows,kind="within_factor",factor="factor",seed=17,attempt=0)
        before={r["physical_sample_id"]:r for r in rows}
        self.assertTrue(receipt["effective"])
        for entry in receipt["target_map"]:
            self.assertEqual(entry["destination_factor"],entry["source_factor"])
            self.assertEqual(entry["training_y"],before[entry["source_id"]]["y"])
            self.assertEqual(entry["source_reference_id"],before[entry["source_id"]]["reference_id"])
        for g,members in components(changed).items():
            sources={e["source_component"] for e in receipt["target_map"] if e["destination_component"]==g}
            self.assertEqual(len(sources),1)
            self.assertEqual(len(members),len(components(rows)[next(iter(sources))]))
        for level in {r["metadata"]["factor"] for r in rows}:
            self.assertEqual(sorted(r["y"] for r in rows if r["metadata"]["factor"]==level),
                             sorted(r["y"] for r in changed if r["metadata"]["factor"]==level))
        altered=copy.deepcopy(rows);altered.reverse()
        _,reordered=intervene(altered,kind="within_factor",factor="factor",seed=17,attempt=0)
        self.assertEqual(receipt,reordered)

    def test_mixed_compositions_missing_and_power_failure_are_explicit(self):
        rows=development_rows(task())
        for i,r in enumerate(rows):r["metadata"]["factor"]=str(i)
        a=exchangeability(rows,"within_factor","factor")
        self.assertFalse(a["eligible"]);self.assertEqual(a["movable_target_fraction"],0.)
        with self.assertRaisesRegex(ValueError,"INSUFFICIENT"):transform()(rows)
        rows[0]["metadata"].pop("factor")
        self.assertIn(rows[0]["independence_group"],exchangeability(rows,"within_factor","factor")["missing_factor_components"])
        pure=development_rows(task("group_only"))
        _,receipt=transform()(pure)
        self.assertGreater(receipt["moved_identity_fraction"],.5)
        self.assertEqual(receipt["changed_target_fraction"],0.)
        self.assertFalse(receipt["effective"])
        self.assertEqual(receipt["attainable_numerical_vector_assignments"],"1")

    def test_size_accounting_and_failed_matches_keep_whole_components(self):
        rows=development_rows(task())
        match=size_match_rows(rows,31,17,0)
        self.assertEqual(match["matched_samples"],30)
        self.assertEqual(match["sample_gap"],1);self.assertFalse(match["exact_match"])
        self.assertEqual(len(components(match["value"])),15)
        for members in components(match["value"]).values():self.assertEqual(len(members),2)
        self.assertEqual(size_match_rows(rows,97,17,0)["reason"],"REFERENCE_TRAIN_POOL_SMALLER_THAN_FACTOR_HOLDOUT_TRAIN")
        self.assertEqual(size_match_rows(rows,31,17,0,max_gap=0)["status"],"unavailable")

    def test_ordered_reference_patterns_cannot_exchange_incompatible_positions(self):
        rows=development_rows(task())
        for i,members in enumerate(components(rows).values()):
            members[0]["reference_status"]="exact" if i%2 else "unknown"
            members[1]["reference_status"]="unknown" if i%2 else "exact"
        _,receipt=intervene(rows,kind="global",factor="factor",seed=17,attempt=0)
        by={r["physical_sample_id"]:r for r in rows}
        for e in receipt["target_map"]:
            self.assertEqual(by[e["destination_id"]]["reference_status"],by[e["source_id"]]["reference_status"])

    def test_shared_reference_audit_and_repeat_transport(self):
        original=task();repeats=task("repeats")
        a=development_rows(original);b=development_rows(repeats)
        _,x=transform()(a);_,y=transform()(b)
        self.assertEqual(x["target_map"],y["target_map"])
        data=json.loads((ROOT/"tests/fixtures/dependence/mixed.json").read_text())
        data["observations"][1]["reference_id"]=data["observations"][0]["reference_id"]
        from nirs4all_domains.dependence import audit_representation
        with tempfile.TemporaryDirectory() as folder:
            audited=audit_representation(data,os.environ["N4DOMAINS_BIN"],os.environ["N4DOMAINS_METHODS_LIBRARY"],Path(folder))
        with self.assertRaisesRegex(ValueError,"reference audit"):development_rows(audited)
        from nirs4all_domains.split_stress import stress_rows
        original["observations"][0]["y"]=None
        with self.assertRaisesRegex(ValueError,"COMPLETE_DEVELOPMENT_COMPONENT_TARGET_VECTORS"):stress_rows(original)


class NativeStressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=os.environ["N4DOMAINS_METHODS_LIBRARY"]
        cls.results={}
        cfg={**CONFIG,"max_components":6,"shuffle_reference":False,"holdout_factors":[],"size_draws":0,"bootstrap_draws":100}
        for kind in ("group_only","trait_only","mixed","independent_y"):
            data=task(kind);rows=development_rows(data);audit=design_audit(rows,cfg)
            cls.results[kind]=run_experiments(data,cls.library,cfg,audit)

    def test_group_offsets_trait_mixed_and_independent_native_responses(self):
        metric=lambda v,m:v["scores"][m]["value"]["rmse"]["value"]
        for kind in ("group_only","trait_only","mixed"):
            report=self.results[kind];original=report["experiments"][0]["value"]
            self.assertLess(metric(original,"spectral"),1e-9)
            global_attempts=report["interventions"][0]["attempts"]
            self.assertTrue(all(a["status"]=="computed" for a in global_attempts))
            self.assertGreater(native_summary(metric(a["value"],"spectral") for a in global_attempts)["median"],2.)
            within=report["interventions"][1]["attempts"]
            self.assertTrue(all(a["status"]=="computed" for a in within))
            if kind=="group_only":
                for a in within:
                    self.assertLess(metric(a["value"],"spectral"),1e-9)
                    self.assertFalse(a["effective"]);self.assertEqual(a["evidence_status"],"limited_evidence")
            else:
                self.assertGreater(native_summary(metric(a["value"],"spectral") for a in within)["median"],2.)
                self.assertTrue(all(a["effective"] for a in within))
        independent=self.results["independent_y"]["experiments"][0]["value"]
        self.assertGreater(metric(independent,"spectral"),metric(independent,"null"))

    def test_every_inner_map_is_training_scoped_and_original_oof_truth_retained(self):
        original=development_rows(task());by={r["physical_sample_id"]:r for r in original}
        report=self.results["mixed"]
        for family in report["interventions"]:
            for attempt in family["attempts"]:
                for row in attempt["value"]["oof"]:self.assertEqual(row["y"],by[row["physical_sample_id"]]["y"])
                for outer in attempt["value"]["lineage"]:
                    train=set(outer["train_sample_ids"]);valid=set(outer["validation_sample_ids"])
                    for mode in ("spectral","residual"):
                        evidence=outer[mode]
                        for receipt in evidence["intervention_scopes"].values():
                            ids=set(receipt["training_ids"])
                            self.assertTrue(ids<=train);self.assertFalse(ids&valid)
                            self.assertEqual(ids,{e["destination_id"] for e in receipt["target_map"]})
                            self.assertEqual(ids,{e["source_id"] for e in receipt["target_map"]})
                        for event in evidence["residual_fit_events"]:
                            receipt=evidence["intervention_scopes"][event["intervention_sha256"]]
                            self.assertEqual(set(event["baseline"]["training_ids"]),set(receipt["training_ids"]))
                            self.assertFalse(set(event["validation_ids"])&set(receipt["training_ids"]))

    def test_inner_validation_mutation_preserves_common_candidate_maps_and_artifacts(self):
        rows=development_rows(task());folds=group_folds(rows,3,17,"challenge")
        mutate=set(folds["folds"][0]["validation_sample_ids"])
        changed=copy.deepcopy(rows)
        for r in changed:
            if r["physical_sample_id"] in mutate:r["y"]+=10000.
        for factor in (None,"factor"):
            _,a=_inner_fit(rows,self.library,17,3,3,"challenge",residual_factor=factor,training_intervention=transform(kind="global"))
            _,b=_inner_fit(changed,self.library,17,3,3,"challenge",residual_factor=factor,training_intervention=transform(kind="global"))
            event=lambda v:{e["n_components"]:e for e in v["residual_fit_events"] if e["fold_id"]==folds["folds"][0]["fold_id"]}
            self.assertEqual(event(a),event(b))
            for e in event(a).values():self.assertEqual(a["intervention_scopes"][e["intervention_sha256"]],b["intervention_scopes"][e["intervention_sha256"]])

    def test_outer_and_retained_labels_cannot_change_fits(self):
        data=task();rows=development_rows(data);fold=group_folds(rows,4,17,"outer")["folds"][0];by={r["physical_sample_id"]:r for r in rows}
        tr=[by[s] for s in fold["train_sample_ids"]];va=[by[s] for s in fold["validation_sample_ids"]]
        pred,evidence=fit_outer(tr,va,self.library,CONFIG,"outer:0",transform(kind="global"))
        changed=copy.deepcopy(va)
        for r in changed:r["y"]+=10000.
        after,lineage=fit_outer(tr,changed,self.library,CONFIG,"outer:0",transform(kind="global"))
        self.assertEqual(evidence["spectral"],lineage["spectral"])
        self.assertEqual(evidence["residual"],lineage["residual"])
        for a,b in zip(pred,after):
            for m in ("null","group_only","spectral","group_plus_residual"):self.assertEqual(a[m],b[m])
        for r in data["observations"]:
            if r["partition"]=="test":r["y"]=-1e30;r["x"]=[1e30]*6
        data["observations"].reverse()
        cfg={**CONFIG,"max_components":6,"shuffle_reference":False,"holdout_factors":[],"size_draws":0,"bootstrap_draws":100}
        rerun=run_experiments(data,self.library,cfg,design_audit(development_rows(data),cfg))
        self.assertEqual(self.results["mixed"],rerun)

    def test_true_factor_holdout_size_control_and_post_evaluation_ranges(self):
        rows=development_rows(task());hold=factor_holdout(rows,"factor",4)
        result=run_design(rows,hold["value"],self.library,CONFIG)
        for row in result["oof"]:self.assertEqual(row["baseline_source"],"global_training_fallback")
        self.assertIn("post-evaluation",result["y_range"]["selection"])
        self.assertEqual(result["n_samples"],96)
        a=self.results["mixed"]["experiments"][0]["value"]
        comparison=paired_comparison(a,result,100,17)
        self.assertEqual(comparison["value"]["n_samples"],96)
        self.assertTrue(comparison["value"]["paired_all_development"])

    def test_size_only_and_y_extrapolation_without_shortcut_assertion(self):
        from random import Random
        rows=development_rows(task("trait_only"));rng=Random(241)
        noisy=copy.deepcopy(rows)
        for r in noisy:r["y"]+=rng.gauss(0,.5)
        fold=group_folds(noisy,4,17,"outer")["folds"][0];by={r["physical_sample_id"]:r for r in noisy}
        tr=[by[s] for s in fold["train_sample_ids"]];va=[by[s] for s in fold["validation_sample_ids"]]
        full,le=fit_outer(tr,va,self.library,CONFIG,"size-full")
        small=size_match_rows(tr,24,17,0)["value"]
        reduced,se=fit_outer(small,va,self.library,CONFIG,"size-reduced")
        self.assertEqual(len(reduced),len(full));self.assertLess(se["n_train_components"],le["n_train_components"])
        # A continuous nonlinear generating relationship, no group offsets.
        data=copy.deepcopy(rows)
        for i,r in enumerate(data):
            t=i/20;r["x"][2]=t;r["y"]=t*t+2*t
        train=data[:72];valid=data[72:]
        pred,evidence=fit_outer(train,valid,self.library,CONFIG,"extrapolation")
        result=summarize(pred,[evidence])
        self.assertEqual(result["y_range"]["outside_training_range_fraction"],1.)
        self.assertGreater(result["scores"]["spectral"]["value"]["rmse"]["value"],.1)

    def test_inadmissible_attempts_remain_scheduled_without_redraw_or_score(self):
        data=task("high_cardinality")
        cfg={**CONFIG,"shuffle_reference":False,"holdout_factors":[],"size_draws":0,
             "interventions":["within_factor"],"intervention_attempts":3}
        r=run_experiments(data,self.library,cfg,design_audit(development_rows(data),cfg))
        family=r["interventions"][0]
        self.assertEqual(family["successful"],0);self.assertEqual(family["failed_or_unavailable"],3)
        self.assertEqual([a["attempt"] for a in family["attempts"]],[0,1,2])
        self.assertTrue(all(a["value"] is None and a["reason"] for a in family["attempts"]))

    def test_cli_schema_packaged_contract_determinism_and_directory_preservation(self):
        sys.path.insert(0,str(ROOT/"scripts"));from check_split_stress_report import check
        import nirs4all_domains.split_stress as module
        self.assertEqual(json.loads(Path(module.__file__).with_name("split-stress-config.v1.schema.json").read_text()),
            json.loads((ROOT/"schemas/split-stress-config.v1.schema.json").read_text()))
        cfg={**CONFIG,"intervention_attempts":1}
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);config=folder/"config.json";config.write_text(json.dumps(cfg))
            reports=[]
            for repeat in (1,2):
                out=folder/str(repeat)
                command=[os.environ["N4DOMAINS_BIN"],"split-stress",str(ROOT/"tests/fixtures/dependence/mixed.json"),
                    "--config",str(config),"--out",str(out),"--python",sys.executable,"--methods-library",self.library]
                subprocess.run(command,check=True,capture_output=True)
                report=json.loads((out/"report.json").read_text());check(report)
                self.assertTrue(all(e["status"]=="computed" for e in report["experiments"]))
                self.assertTrue(any(c["status"]=="computed" for e in report["experiments"] if "size_controls" in e for d in e["size_controls"]["draws"] for c in d["cells"]))
                before=(out/"report.json").read_bytes();reports.append(before)
                self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
                self.assertEqual(before,(out/"report.json").read_bytes())
            self.assertEqual(reports[0],reports[1])


if __name__=="__main__":unittest.main()
