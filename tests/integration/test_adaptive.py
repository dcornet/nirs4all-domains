"""Native evidence-level controls frozen before the public campaign."""
import copy
import json
import math
import os
from pathlib import Path
import unittest

from nirs4all_domains.adaptive import (association, coverage_record, partition_agreement,
                                       scientific_relation, x_characterization)
from nirs4all_domains.dependence import state


class AdaptiveControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = Path(os.environ.get("N4DOMAINS_BIN", "target/debug/n4domains" + (".exe" if os.name == "nt" else ""))).resolve()
        from n4m._ffi import library_path
        cls.library = Path(library_path()).resolve()

    def request(self, kind="gradient"):
        spectra = [[(i/12 if j == 0 else math.sin(i*(j+1)*.49)*.03) + (8*(i//24) if kind=="separated" and j==0 else 0)
                    for j in range(6)] for i in range(48)]
        if kind=="duplicates":
            spectra = [spectra[i//3] for i in range(48)]
        return {"source_id":"controlled", "observation_ids":[f"o:{i}" for i in range(48)],
                "identity_evidence":"observation_identity_only", "axis":list(range(1000,1006)),
                "axis_unit":"nm", "spectra":spectra}

    def test_missing_metadata_and_targets_allow_native_geometry(self):
        r=x_characterization(self.request(),self.binary,self.library)
        self.assertEqual(r["x_structure"]["status"],"computed")
        self.assertEqual(r["target_structure_association"]["status"],"unavailable")
        self.assertEqual(r["predictive_structural_dependence"]["status"],"unavailable")
        self.assertEqual(r["identity_evidence"],"observation_identity_only")

    def test_separation_and_continuum_remain_descriptive(self):
        a=x_characterization(self.request("separated"),self.binary,self.library)
        b=x_characterization(self.request(),self.binary,self.library)
        self.assertGreater(a["x_structure"]["value"]["full_trace"],b["x_structure"]["value"]["full_trace"])
        self.assertNotIn("low_risk", json.dumps(b))
        self.assertEqual(a["structural_stability"]["status"],"unavailable")

    def test_unknown_identity_duplicates_do_not_become_physical_repeats(self):
        r=x_characterization(self.request("duplicates"),self.binary,self.library)
        counts=r["near_duplicate_proximity"]["value"]["tolerance_sensitivity"]
        self.assertEqual(counts[0]["n_observations_with_close_neighbor"],48)
        self.assertEqual(r["identity_evidence"],"observation_identity_only")

    def test_independent_coincident_spectra_preserve_identity_state(self):
        q=self.request("duplicates");q["identity_evidence"]="verified_physical_identity"
        r=x_characterization(q,self.binary,self.library)
        self.assertEqual(r["identity_evidence"],"verified_physical_identity")
        self.assertEqual(r["predictive_structural_dependence"]["status"],"unavailable")

    def test_no_target_can_enter_native_x_contract(self):
        q=self.request();q["y_test"]=[999]*48
        with self.assertRaisesRegex(RuntimeError,"unknown field"):
            x_characterization(q,self.binary,self.library)

    def test_full_population_budget_failure_never_downsamples(self):
        q=self.request();q['spectra']=[[float(i),0.,1.,2.,3.,4.] for i in range(10000)]
        q['observation_ids']=[str(i) for i in range(10000)]
        with self.assertRaisesRegex(RuntimeError,'FULL_POPULATION_GEOMETRY_BUDGET_EXCEEDED'):
            x_characterization(q,self.binary,self.library)

    def test_duplicate_observation_keys_are_not_merged(self):
        q=self.request();q['observation_ids'][1]=q['observation_ids'][0]
        with self.assertRaisesRegex(RuntimeError,'INVALID_SCOPED'):
            x_characterization(q,self.binary,self.library)

    def test_additive_packaged_schemas_and_status_invariants(self):
        import jsonschema
        import nirs4all_domains
        root=Path(nirs4all_domains.__file__).parent
        for name in ['adaptive-coverage','repeated-design-result']:
            self.assertEqual(json.loads((root/(name+'.v1.schema.json')).read_text()),
                             json.loads((Path('schemas')/(name+'.v1.schema.json')).read_text()))
        levels={k:state(reason='UNKNOWN') for k in ['X0','X1','XY','XYM','MODEL']}
        r=coverage_record('d','X','observation_identity_only',levels)
        schema=json.loads((root/'adaptive-coverage.v1.schema.json').read_text());jsonschema.validate(r,schema)
        r['levels']['MODEL']={'status':'computed','value':None,'reason':None}
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(r,schema)

    def test_invalid_axis_and_missing_values_are_not_imputed(self):
        for change in (lambda q:q["axis"].reverse(),lambda q:q["spectra"][0].pop()):
            q=self.request();change(q)
            with self.assertRaisesRegex(RuntimeError,"INVALID_SCOPED"):
                x_characterization(q,self.binary,self.library)

    def test_exact_native_replay_and_imbalance(self):
        q=self.request("separated");q["spectra"][-4:]=[[v+80 for v in row] for row in q["spectra"][-4:]]
        a=x_characterization(q,self.binary,self.library);b=x_characterization(q,self.binary,self.library)
        self.assertEqual(a,b)
        self.assertTrue(all(math.isfinite(v) for v in a["x_structure"]["value"]["eigenvalues"]))

    def test_native_association_distinguishes_group_only_and_independent(self):
        group=["a"]*12+["b"]*12
        pure=association(group,[0.]*12+[10.]*12)
        independent=association(group,list(range(12))*2)
        self.assertAlmostEqual(pure["value"]["eta_squared"],1.,places=10)
        self.assertAlmostEqual(independent["value"]["eta_squared"],0.,places=10)
        self.assertEqual(association(["a"]*24,list(range(24)))["status"],"unavailable")

    def test_native_partition_agreement(self):
        self.assertAlmostEqual(partition_agreement([0,0,1,1],[9,9,4,4])["value"],1.,places=10)

    def test_shared_specimens_and_representations_are_not_new_populations(self):
        a={"study_id":"s1","population_id":"p1","physical_keys_verified":True,"physical_keys":["s:x"]}
        self.assertEqual(scientific_relation(a,{**a,"representation":"ground"}),"same_declared_population")
        self.assertEqual(scientific_relation(a,{**a,"population_id":"p2"}),"shared_study_independence_unverified")
        self.assertEqual(scientific_relation(a,{**a,"study_id":"s2","population_id":"p2"}),"shared_physical_specimens")
        self.assertEqual(scientific_relation(a,{**a,"study_id":"s2","population_id":"p2","physical_keys":["s2:z"]}),"distinct_provenance_overlap_unverified")

    def test_missing_independence_blocks_models_not_x0(self):
        levels={k:state(reason="UNKNOWN_DONOR_AND_ASSAY") for k in ["X0","X1","XY","XYM","MODEL"]}
        levels["X0"]=state({"measured":True})
        r=coverage_record("d","X","observation_identity_only",levels)
        self.assertEqual(r["levels"]["X0"]["status"],"computed")
        self.assertIsNone(r["universal_shortcut_score"])
        bad=copy.deepcopy(levels);bad["MODEL"]=state()
        with self.assertRaises(ValueError):coverage_record("d","X","observation_identity_only",bad)


if __name__=="__main__":unittest.main()
