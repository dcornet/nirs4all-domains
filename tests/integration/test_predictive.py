"""Scientific behavior of the real native DAG-ML/Methods sanity-check seam."""
import copy
import os
import random
import unittest

from nirs4all_domains.predictive import predictive_sanity, permute_group_targets


def task(dependent=True):
    rng=random.Random(103)
    rows=[{"physical_sample_id":f"s{i}","sample_id":f"s{i}","observation_id":f"o{i}",
           "independence_group":f"g{i//2}","metadata":{"validation_component_id":f"g{i//2}"},"partition":"train",
           "x":[i/10,(i%7)/10,(i%11)/10],"y":2*i/10+3 if dependent else rng.gauss(0,1)} for i in range(48)]
    rows.append({"partition":"test","y":1e30,"x":[999,999,999],"metadata":{},"physical_sample_id":"held"})
    return {"policy":{"representation":"technical_mean"},"context":{"target_id":"y"},
            "observations":rows,"provenance":{"reference_xy_blocked":"false"}}


class PredictiveTests(unittest.TestCase):
    def run_probe(self, data):
        return predictive_sanity(data,os.environ["N4DOMAINS_METHODS_LIBRARY"],outer_folds=4,inner_folds=3,max_components=3,permutations=0)

    def test_synthetic_signal_beats_fold_local_null_with_verified_native_lineage(self):
        result=self.run_probe(task())
        self.assertLess(result["pls"]["rmse"],1e-10)
        self.assertGreater(result["null"]["rmse"],2.)
        self.assertAlmostEqual(result["pls"]["r2"],1.)
        self.assertEqual(len(result["oof"]),48)
        for scope in result["lineage"]:
            train=set(scope["train_sample_ids"]);valid=set(scope["validation_sample_ids"])
            self.assertFalse(train&valid)
            self.assertTrue(scope["native_fit_lineage_verified"])
            for inner in scope["inner_fold_set"]["folds"]:
                self.assertTrue(set(inner["train_sample_ids"])<=train)
                self.assertTrue(set(inner["validation_sample_ids"])<=train)

    def test_independent_target_has_no_stable_improvement(self):
        result=self.run_probe(task(False))
        self.assertLess(result["pls"]["r2"],0.)
        self.assertGreater(result["pls"]["rmse"],result["null"]["rmse"])

    def test_retained_targets_and_spectra_cannot_affect_any_probe_fit(self):
        original=task();before=self.run_probe(original)
        changed=copy.deepcopy(original);changed["observations"][-1]["y"]=-1e30;changed["observations"][-1]["x"]=[-99,-99,-99]
        self.assertEqual(before,self.run_probe(changed))
        for row in original["observations"]:
            if row["partition"]=="train":row["reference_id"]="shared"
        original["provenance"]["reference_xy_blocked"]="true"
        with self.assertRaisesRegex(ValueError,"reference audit"):
            self.run_probe(original)

    def test_permutation_moves_whole_equal_size_group_vectors(self):
        rows=task()["observations"][:-1];shuffled=permute_group_targets(rows,991)
        original={tuple(r["y"] for r in rows if r["independence_group"]==g) for g in {r["independence_group"] for r in rows}}
        vectors={tuple(r["y"] for r in shuffled if r["independence_group"]==g) for g in {r["independence_group"] for r in shuffled}}
        self.assertEqual(original,vectors)
        self.assertNotEqual([r["y"] for r in rows],[r["y"] for r in shuffled])
        self.assertEqual(shuffled,permute_group_targets(rows,991))
