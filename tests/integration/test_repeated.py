import copy
import json
import math
from pathlib import Path
import unittest

from nirs4all_domains.repeated import freeze, run_design, summarize_designs


def task():
    value=json.loads(Path('tests/fixtures/dependence/mixed.json').read_text())
    value.setdefault('provenance',{})['reference_xy_blocked']='false'
    for i,r in enumerate(value['observations']):
        r['metadata']['validation_component_id']=r['independence_group']
        r['x']=[math.sin(i*.7+j*.13)+.03*j*i+math.cos(i*.3-j*.7) for j in range(12)]
    return value


SPEC={'id':'ridge_control','engine':'methods','method':'models.regularized.ridge','preprocessing':'raw','grid':{'alpha':[.01,1.]}}


class RepeatedTests(unittest.TestCase):
    def test_few_groups_do_not_identify_new_group_distribution(self):
        t=task()
        for i,r in enumerate(t['observations']):r['metadata']['validation_component_id']=str(i%2)
        with self.assertRaisesRegex(ValueError,'TEN_DOCUMENTED'):freeze(t,[SPEC])

    def test_retained_labels_and_spectra_cannot_change_frozen_designs(self):
        t=task();a=freeze(t,[SPEC]);changed=copy.deepcopy(t)
        for r in changed['observations']:
            if r['partition']=='test':r['x']=[9999]*12;r['y']=-9999
        self.assertEqual(a,freeze(changed,[SPEC]))

    def test_native_grouped_refits_do_not_triple_independent_sample_count(self):
        from n4m._ffi import library_path
        t=task();f=freeze(t,[SPEC])
        results=[run_design(t,f,s,SPEC,library_path()) for s in [17,31,47]]
        self.assertTrue(all(r['status']=='computed' for r in results),results)
        summary=summarize_designs(results)['value']
        n=len(results[0]['value']['oof'])
        self.assertEqual(summary['n_unique_physical_units'],n)
        self.assertEqual(summary['not_independent_observation_count'],3*n)
        self.assertEqual(summary['conditional_bootstrap']['status'],'unavailable')
        self.assertEqual(summary['new_source_population_uncertainty']['status'],'unavailable')
        self.assertTrue(all(l['native_fit_lineage_verified'] for r in results for l in r['value']['lineage']))
        bad=copy.deepcopy(results);bad[1]['value']['oof'][0]['physical_sample_id']='changed'
        with self.assertRaisesRegex(ValueError,'POPULATIONS_DIFFER'):summarize_designs(bad)

    def test_frozen_source_and_transfer_mismatch_fail_before_fit(self):
        from n4m._ffi import library_path
        t=task();f=freeze(t,[SPEC]);changed=copy.deepcopy(t)
        row=next(r for r in changed['observations'] if r['partition']=='train');row['y']+=1
        with self.assertRaisesRegex(ValueError,'CONTENT_OR_ESTIMATOR'):run_design(changed,f,17,SPEC,library_path())
        with self.assertRaisesRegex(ValueError,'TRANSFER_CONTENT'):run_design(t,f,17,SPEC,library_path(),{})


if __name__=='__main__':unittest.main()
