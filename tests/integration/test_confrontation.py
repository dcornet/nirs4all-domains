"""Synthetic original-ownership gates and actual grouped Methods/DAG anchors."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nirs4all_domains.confrontation import admit, dependency_map, freeze, execute
from nirs4all_domains.dependence import development_rows
from nirs4all_domains.predictive import group_folds
from test_multifamily import task

SHA = 'a'*64


def source_evidence():
    value = {key: True for key in ['analysis_authorized', 'complete_X_qualified', 'original_keyed_XY_verified',
        'target_meaning_units_verified', 'development_scope_frozen_before_target_decode', 'original_study_verified',
        'physical_specimen_ownership_verified', 'reference_assay_ownership_verified', 'dependency_map_verified',
        'component_safe_split_feasible']}
    value.update({key: SHA for key in ['original_source_sha256', 'canonical_X_sha256', 'canonical_Y_sha256', 'closure_evidence_sha256']})
    value['publication_allowed'] = False
    return value


def freeze_control(value=None):
    value = value or task()
    links = [{'observation_id': r['observation_id'], 'physical_id': r['physical_sample_id'],
        'reference_id': 'reference:'+r['physical_sample_id'], 'assay_event_id': 'assay:'+r['physical_sample_id'],
        'component_id': r['independence_group'], 'partition': r['partition']} for r in value['observations']]
    rows = development_rows(value)
    designs = {key: group_folds(rows, 2, seed, key) for key,seed in [('reference',17),('stress',23),('size_control',17)]}
    return value, freeze(value, source_evidence(), links, designs, {'path': 'synthetic-H1-H5', 'sha256': SHA}), links, designs


class SourceClosureControls(unittest.TestCase):
    def test_missing_assay_ownership_retains_only_xy_description(self):
        evidence = source_evidence(); evidence['reference_assay_ownership_verified'] = False
        result = admit(evidence)
        self.assertEqual(result['tier'], 'XY_descriptive_qualified')
        self.assertIn('REFERENCE_ASSAY_OWNERSHIP_VERIFIED_REQUIRED', result['blockers'])

    def test_missing_original_xy_mapping_retains_x_only(self):
        evidence = source_evidence(); evidence['original_keyed_XY_verified'] = False
        self.assertEqual(admit(evidence)['tier'], 'X_only_qualified')

    def test_publication_status_does_not_qualify_or_block_science(self):
        evidence = source_evidence()
        self.assertEqual(admit(evidence)['tier'], 'exploratory_supervised_qualified')
        evidence['analysis_authorized'] = False; evidence['publication_allowed'] = True
        self.assertEqual(admit(evidence)['tier'], 'not_admitted')

    def test_no_target_or_model_scores_in_scientific_candidate_admission(self):
        evidence = source_evidence(); evidence['rmse'] = .001
        with self.assertRaisesRegex(ValueError, 'OUTCOME_INPUT_FORBIDDEN'): admit(evidence)

    def test_shared_assay_cannot_be_split_into_independent_components(self):
        links = [{'observation_id': key,'physical_id': key,'reference_id':'r'+key,
            'assay_event_id':'shared','component_id':'c'+key,'partition':'train'} for key in ['a','b']]
        with self.assertRaisesRegex(ValueError, 'INDIVISIBLE'): dependency_map(links)
        for row in links: row['component_id'] = 'one'
        self.assertEqual(len(dependency_map(links)['rows']), 2)
        links[1]['partition'] = 'test'
        with self.assertRaisesRegex(ValueError, 'INDIVISIBLE'): dependency_map(links)

    def test_unique_observation_ids_do_not_supply_assay_or_specimen_ownership(self):
        with self.assertRaisesRegex(ValueError, 'OWNERSHIP_REQUIRED'):
            dependency_map([{'observation_id':'a'}])

    def test_exact_frozen_anchors_fit_count_and_study_scope(self):
        _, frozen, _, _ = freeze_control()
        self.assertEqual(frozen['prospective_model_fits'], 3*2*(3*8+2))
        self.assertEqual(frozen['anchors'][0]['grid'], {'n_components':[1,2,3]})
        self.assertEqual(frozen['anchors'][1]['grid'], {'alpha':[.01,.1,1.,10.,100.]})
        self.assertFalse(frozen['study_level_confirmation'])
        self.assertIsNone(frozen['real_execution']['value'])

    def test_retained_y_cannot_change_preregistration_or_descriptor_bindings(self):
        value, first, links, designs = freeze_control()
        for row in value['observations']:
            if row['partition'] == 'test': row['y'] = 1e19; row['x'] = []; row['metadata'] = {}
        second = freeze(value, source_evidence(), links, designs, {'path':'synthetic-H1-H5','sha256':SHA})
        self.assertEqual(first, second)
        self.assertEqual(first['hypothesis_ref']['sha256'], SHA)

    def test_separate_budget_gate_precedes_every_native_model_call(self):
        value, frozen, _, _ = freeze_control()
        with patch('nirs4all_domains.confrontation.compare_design') as native:
            with self.assertRaisesRegex(ValueError, 'SEPARATE_EXACT_PILOT_RESOURCE_APPROVAL'):
                execute(value, frozen, {'owner_approved':True,'pilot_id':'different'}, 'unused')
            native.assert_not_called()

    def test_frozen_mutation_and_arbitrary_component_thinning_are_refused(self):
        value, frozen, links, designs = freeze_control()
        frozen['anchors'][1]['grid']['alpha'] = [2.]
        with self.assertRaisesRegex(ValueError, 'DIGEST_MISMATCH'): execute(value,frozen,{},'unused')
        with self.assertRaisesRegex(ValueError, 'MEMBERSHIP_REQUIRED'):
            freeze(value,source_evidence(),links[:-1],designs,{'path':'synthetic','sha256':SHA})
        train = next(r for r in value['observations'] if r['partition']=='train')
        train['metadata']['validation_component_id'] = 'invented-singleton'
        with self.assertRaisesRegex(ValueError, 'VALIDATION_COMPONENT_MAPPING_CHANGED'):
            freeze(value,source_evidence(),links,designs,{'path':'synthetic','sha256':SHA})


class NativeExploratoryAnchors(unittest.TestCase):
    def test_real_native_pls_ridge_null_and_retained_target_mutation(self):
        value, frozen, _, _ = freeze_control()
        approval = {'owner_approved':True,'pilot_id':frozen['pilot_id'],
            'model_fit_upper_bound':frozen['prospective_model_fits'],'storage_admitted':True,
            'scope':'public synthetic fixture only; no real source admission'}
        from nirs4all_domains.storage import StageStore
        with tempfile.TemporaryDirectory(prefix='domains-public-synthetic-pilot-') as temp:
            root = Path(temp)
            policy = {'campaign_bytes':64*1024*1024,'per_task_bytes':32*1024*1024,
                'evidence_bytes':4*1024*1024,'workspace_max_bytes':128*1024*1024,
                'reserve_free_bytes':1024,'max_concurrency':1}
            scheduler = StageStore(root/'state',root/'scratch',root/'evidence',root,policy)
            def checkpoint(contract,compute):
                grid_size = len(next(iter(contract['specification']['grid'].values())))
                count = sum(len(f['folds'])*grid_size+1 for f in frozen['evaluation']['inner_designs'][contract['design']].values())
                receipt,result = scheduler.run(contract,'P3',{'inputs':[], 'scratch_bytes':65536,
                    'evidence_bytes':512*1024,'expected_fits':count,'expected_permutations':0,
                    'uncertainty':'Synthetic grouped anchor selection/refits; no real source data.'},lambda folder:compute())
                self.assertEqual(receipt['status'],'computed')
                return result
            first = execute(value,frozen,approval,os.environ['N4DOMAINS_METHODS_LIBRARY'],checkpoint)
            for row in value['observations']:
                if row['partition']=='test': row['y'] = -1e17; row['x'] = [1e25]*32
            with patch('nirs4all_domains.confrontation.compare_design') as native:
                second = execute(value,frozen,approval,os.environ['N4DOMAINS_METHODS_LIBRARY'],checkpoint)
                native.assert_not_called()
        for design in first['outcomes']:
            for model,result in first['outcomes'][design].items():
                self.assertEqual(result['status'],'computed',result)
                a,b = result['value'],second['outcomes'][design][model]['value']
                self.assertEqual(a['oof'],b['oof'])
                self.assertEqual(a['null_scores'],b['null_scores'])
                self.assertTrue(a['null_fitted_on_training_only'])
                self.assertTrue(all(r['native_fit_lineage_verified'] for r in a['lineage']))
        self.assertEqual(first['matched_contrasts'],second['matched_contrasts'])
        self.assertTrue(first['contrary_and_null_outcomes_retained'])
        self.assertEqual(set(first['matched_contrasts']), {'raw_pls','raw_ridge'})


if __name__ == '__main__': unittest.main()
