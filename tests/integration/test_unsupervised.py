"""Frozen alpha.12 expectations using the public native numerical providers."""
import copy
import json
import math
import os
from pathlib import Path
import unittest

from nirs4all_domains.unsupervised import (compact_profile, component_draw,
    compare_partition, factor_profile, native_profile, neighborhood_agreement,
    pair_panel, query_design, represent, stability_summary)
from scripts.generate_unsupervised_fixtures import MECHANISMS, scenario


class UnsupervisedControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = Path(os.environ.get('N4DOMAINS_BIN','target/debug/n4domains'+('.exe' if os.name=='nt' else ''))).resolve()
        from n4m._ffi import library_path
        cls.library = Path(library_path()).resolve()

    def profile(self, spectral, representation='raw', design=None):
        q = represent(spectral,representation)
        return native_profile(q,representation,self.binary,self.library,
            design or query_design(q['observation_ids'],len(q['axis'])))

    def test_snv_row_isolation_and_affine_invariance(self):
        q = scenario('scatter')['spectral']
        a = represent(q,'snv')
        changed = copy.deepcopy(q)
        changed['spectra'][0] = [v*3+123 for v in q['spectra'][0]]
        b = represent(changed,'snv')
        self.assertEqual(a['spectra'][1:],b['spectra'][1:])
        for x,y in zip(a['spectra'][0],b['spectra'][0],strict=True):
            self.assertTrue(math.isclose(x,y,abs_tol=1e-10,rel_tol=1e-10))
        self.assertEqual(q['axis'],a['axis'])
        self.assertEqual(q['observation_ids'],a['observation_ids'])

    def test_constant_spectrum_unavailable_without_deletion(self):
        q = scenario('separated')['spectral']; q['spectra'][0]=[1.]*len(q['axis'])
        before = copy.deepcopy(q)
        with self.assertRaisesRegex(ValueError,'CONSTANT_SPECTRUM'):
            represent(q,'snv')
        self.assertEqual(q,before)

    def test_query_design_is_not_reference_truncation(self):
        ids = [str(i) for i in range(2605)]
        a = query_design(ids,812)
        self.assertEqual(a,query_design(ids,812))
        self.assertEqual((a['n_source'],a['n_query'],a['mode']),(2605,128,'query_subset'))
        self.assertEqual(set(a['ids']),set(query_design(list(reversed(ids)),812)['ids']))

    def test_source_budget_failure_before_selection(self):
        with self.assertRaisesRegex(ValueError,'WORK_BUDGET'):
            query_design([str(i) for i in range(10000)],100000)

    def test_known_repeats_are_whole_components(self):
        fixture = scenario('known_acquisitions')
        ids = fixture['spectral']['observation_ids']; units = fixture['components']
        d = component_draw(ids,units,.6,0)
        selected = set(d['observation_ids'])
        for unit in set(units.values()):
            members = {s for s in ids if units[s]==unit}
            self.assertIn(len(members & selected),(0,len(members)))
        self.assertEqual(d,component_draw(ids,units,.6,0))

    def test_component_map_cannot_silently_drop_rows(self):
        fixture = scenario('known_acquisitions'); fixture['components'].pop('o:0')
        with self.assertRaisesRegex(ValueError,'COMPLETE_DECLARED'):
            component_draw(fixture['spectral']['observation_ids'],fixture['components'],.8,1)

    def test_native_full_and_partial_queries_are_exactly_consistent(self):
        q = scenario('gradient',n=48)['spectral']
        full = self.profile(q)
        design = {'ids':q['observation_ids'][::2], 'mode':'query_subset','n_source':48,'n_query':24,'seed':None}
        part = self.profile(q,design=design)
        for space in ('full_axis','pca'):
            a,b = (r['neighborhoods']['value'][space] for r in (full,part))
            self.assertEqual(b['n_reference'],48)
            self.assertEqual(b['reference_indices'],a['reference_indices'][::2])
            self.assertEqual(b['distances'],a['distances'][::2])
            self.assertFalse(b['approximate'])

    def test_complete_source_exact_neighbors_cross_public_call_budget(self):
        q={'source_id':'analytical-batched','observation_ids':[str(i) for i in range(512)],
           'identity_evidence':'observation_identity_only','axis':list(range(1000,2024)),
           'axis_unit':'nm','spectra':[[float(i)/512.+float(j==i) for j in range(1024)] for i in range(512)]}
        r=self.profile(q)['neighborhoods']['value']['full_axis']
        self.assertEqual(r['mode'],'complete_source')
        self.assertEqual(r['n_query'],512)
        self.assertGreater(r['native_calls'],1)
        self.assertEqual(r['distance_products'],512*512*1024)
        # Adjacent rows: the two +/-1 impulses have cancelling cross terms
        # with the common 1/512 offset across 1024 bands.
        self.assertTrue(all(math.isclose(v[0],math.sqrt(2.+1./256.),abs_tol=1e-10) for v in r['distances']))

    def test_native_total_budget_rejects_without_source_truncation(self):
        q={'source_id':'over-total-bound','observation_ids':[str(i) for i in range(2048)],
           'identity_evidence':'observation_identity_only','axis':list(range(1000,1256)),
           'axis_unit':'nm','spectra':[[float(i)]*256 for i in range(2048)]}
        with self.assertRaisesRegex(RuntimeError,'TOTAL_NEIGHBOR_PRODUCT_BUDGET'):
            self.profile(q,design={'ids':q['observation_ids']})
        self.assertEqual(len(q['spectra']),2048)

    def test_native_no_y_input(self):
        q = scenario('separated')['spectral'];q['Y_test']=[999.]*len(q['spectra'])
        with self.assertRaisesRegex(RuntimeError,'unknown field'):
            self.profile(q)

    def test_no_model_performance_input(self):
        q = scenario('gradient')['spectral'];q['rmse']=.01
        with self.assertRaisesRegex(RuntimeError,'unknown field'):
            self.profile(q)

    def test_exact_replay(self):
        q = scenario('separated')['spectral']
        self.assertEqual(self.profile(q),self.profile(q))

    def test_shared_partition_support_and_noise_are_separate(self):
        ids = [str(i) for i in range(48)]
        labels = [0]*24+[1]*24
        r = compare_partition(ids,labels,ids[::2],labels[::2])
        self.assertEqual(r['ari_including_noise']['value'],1.)
        r = compare_partition(ids,[-1]*48,ids[::2],[-1]*24)
        self.assertEqual(r['ari_including_noise']['status'],'unavailable')
        self.assertEqual(r['noise_status_agreement'],1.)

    def test_partial_support_not_favorable_zero(self):
        ids = [str(i) for i in range(48)]
        r = compare_partition(ids,[0]*24+[1]*24,ids[:4],[0]*4)
        self.assertIsNone(r['ari_including_noise']['value'])
        self.assertEqual(r['n_common'],4)

    def test_pair_panel_bounded_and_noise_excluded(self):
        labels = [-1]*12+[0]*24+[1]*24
        p = pair_panel(labels)
        self.assertEqual(p,pair_panel(labels))
        for key in ('within','between'):
            self.assertLessEqual(len(p[key]),128)
            self.assertTrue(all(labels[i]>=0 and labels[j]>=0 for i,j in p[key]))

    def test_high_cardinality_metadata_and_missingness(self):
        ids = [str(i) for i in range(48)]
        r = factor_profile([0]*24+[1]*24,[[float(i)] for i in range(48)],
            {s:'level:'+s for s in ids[1:]},ids,'simulated declared factor')
        self.assertEqual(r['value']['missing'],1)
        self.assertTrue(r['value']['high_cardinality'])
        self.assertEqual(r['value']['pc_associations'][0]['status'],'unavailable')

    def test_missing_metadata_does_not_create_factor(self):
        r = factor_profile([0]*48,[[float(i)] for i in range(48)],{},[str(i) for i in range(48)],'missing')
        self.assertEqual(r['status'],'unavailable')

    def test_neighborhood_support_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'MATCHED_NEIGHBOR'):
            neighborhood_agreement({'query_ids':['a'],'n_reference':3,'k':1},
                                   {'query_ids':['b'],'n_reference':3,'k':1})

    def test_no_scores_persist_in_compact_evidence(self):
        q = scenario('gradient',n=48)['spectral'];d=query_design(q['observation_ids'],len(q['axis']))
        r = compact_profile(self.profile(q),d)
        self.assertNotIn('transport_only_scores',r)
        self.assertIsNone(r['predictive_dependence']['value'])
        self.assertNotIn('low_risk',json.dumps(r))

    def test_native_resampling_support_is_conditional_and_reproducible(self):
        q = scenario('separated')['spectral'];ids=q['observation_ids']
        reference=self.profile(q);draws=[]
        for number in range(20):
            draw=component_draw(ids,{s:s for s in ids},.8,number)
            selected={**q,'observation_ids':draw['observation_ids'],
                      'spectra':[q['spectra'][i] for i in draw['indices']]}
            value=native_profile(selected,'raw',self.binary,self.library)
            draws.append({'draw':number,'status':'computed','reason':None,'value':value,
                          'selected_indices':draw['indices'],'n_selected_units':len(draw['selected_units'])})
        result=stability_summary(reference,draws,ids,len(ids),'Observation algorithmic stability only')
        for setting in result['settings']:
            self.assertEqual(setting['value']['successful_draws'],20)
            self.assertEqual(setting['value']['classification'],'robust_structure')
            self.assertFalse(setting['value']['biological_sampling_uncertainty'])
        self.assertEqual(result['biologically_independent_unit_count']['status'],'unavailable')


def mechanism_test(name):
    def check(self):
        fixture = scenario(name);q=fixture['spectral'];a=self.profile(q)
        self.assertEqual(a['n_observations'],len(q['spectra']))
        self.assertEqual(a['n_bands'],len(q['axis']))
        self.assertFalse(a['test_target_accessed'])
        self.assertTrue(all(math.isfinite(v) for v in a['pca']['eigenvalues']))
        if name == 'separated':
            self.assertGreaterEqual(a['cluster_settings'][0]['value']['n_clusters'],2)
        if name in ('exact_repeats_unknown','known_acquisitions'):
            self.assertTrue(all(row[0] == 0 for row in a['neighborhoods']['value']['full_axis']['distances']))
        if name == 'close_independent':
            self.assertEqual(q['identity_evidence'],'verified_physical_identity')
            self.assertEqual(len(set(fixture['components'].values())),len(q['spectra']))
        if name == 'high_dimensional_noise':
            self.assertLess(a['pca']['retained_variance_fraction'],.9)
        if name == 'wavelength_scaling':
            self.assertGreater(a['pca']['eigenvalues'][0]/a['pca']['full_trace'],.99)
        if name == 'fragmentation':
            for n in (48,240):
                b=self.profile(scenario(name,n=n)['spectral'])
                self.assertEqual(b['n_observations'],n)
        if name in ('scatter','snv_erased','snv_enhanced'):
            b=self.profile(q,'snv')
            self.assertEqual(b['n_observations'],a['n_observations'])
            self.assertNotEqual(a['input_sha256'],b['input_sha256'])
    return check


for _name in MECHANISMS:
    setattr(UnsupervisedControls,'test_mechanism_'+_name,mechanism_test(_name))


if __name__=='__main__':
    unittest.main()
