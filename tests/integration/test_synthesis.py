"""Public/synthetic cohort and descriptor protocol adversaries, native statistics."""
import copy
import unittest

from nirs4all_domains.cohort import reconcile
from nirs4all_domains.dependence import state
from nirs4all_domains.synthesis import compare, describe, scalar, threshold_association, validate_states

SHA = 'a'*64


def corpus():
    entries = [{'catalog_id': 'controlled', 'local_analysis_allowed': True}]
    views = [{'view_id': v, 'catalog_id': 'controlled', 'content_sha256': SHA,
        'complete_X_available': True, 'family': 'controlled', 'modality': 'NIR',
        'study': {'id': 'study', 'verified': True, 'evidence_sha256': SHA},
        'population': {'id': 'population', 'verified': True, 'evidence_sha256': SHA}}
        for v in ['X-intact', 'X-ground']]
    executions = [{'execution_id': 'receipt-'+v['view_id'], 'view_id': v['view_id'],
        'content_sha256': SHA, 'status': 'computed', 'artifact_sha256': SHA, 'receipt_verified': True} for v in views]
    relations = [{'view_ids': [v['view_id'] for v in views], 'status': 'verified_shared', 'evidence_sha256': SHA}]
    return entries, views, executions, relations


class CohortAccounting(unittest.TestCase):
    def test_catalog_views_populations_studies_are_different_denominators(self):
        value = reconcile(*corpus())
        counts = value['denominators']
        self.assertEqual([counts[k] for k in ['catalog_entries', 'spectral_source_views', 'verified_physical_populations', 'verified_original_studies']], [1, 2, 1, 1])
        self.assertEqual(counts['calculated_X_views'], 2)

    def test_cards_without_executions_do_not_become_scientific_results(self):
        entries, views, _, relations = corpus()
        self.assertEqual(reconcile(entries, views, [], relations)['denominators']['calculated_X_views'], 0)

    def test_unknown_overlap_is_not_proven_independence(self):
        entries, views, executions, _ = corpus()
        views[1]['population']['id'] = 'other'
        value = reconcile(entries, views, executions, [])
        self.assertEqual(value['independent_study_denominator']['status'], 'not_identifiable')
        self.assertEqual(value['unknown_or_unproven_disjoint_source_pairs'], 1)

    def test_bibliography_and_row_keys_do_not_verify_original_units(self):
        entries, views, executions, relations = corpus()
        for view in views:
            view['study'] = {'verified': False, 'citation': 'same package'}
            view['population'] = {'verified': False, 'row_keys_unique': True}
        value = reconcile(entries, views, executions, [])
        self.assertEqual(value['denominators']['verified_original_studies'], 0)
        self.assertIsNone(value['independent_study_denominator']['value'])

    def test_publication_denied_does_not_block_authorized_science(self):
        entries, views, executions, relations = corpus()
        for view in views:
            view.update(exact_publication_approved=False, public_visibility=False)
        counts = reconcile(entries, views, executions, relations)['denominators']
        self.assertEqual((counts['calculated_X_views'], counts['approved_public_disclosure_views']), (2, 0))

    def test_public_visibility_cannot_override_missing_analysis_rights(self):
        entries, views, executions, relations = corpus()
        entries[0]['local_analysis_allowed'] = False
        views[0]['public_visibility'] = True
        with self.assertRaisesRegex(ValueError, 'ANALYSIS_AUTHORIZATION'):
            reconcile(entries, views, executions, relations)

    def test_failures_and_partial_receipts_remain_in_the_denominator(self):
        entries, views, executions, relations = corpus()
        executions[0]['status'] = 'failed'
        executions[1]['status'] = 'partial'
        value = reconcile(entries, views, executions, relations)
        self.assertEqual(value['denominators']['incomplete_or_unexecuted_views'], 2)
        self.assertEqual(value['denominators']['partial_X_views'], 1)

    def test_content_and_receipt_mismatches_are_refused(self):
        for field, replacement in [('content_sha256', 'b'*64), ('receipt_verified', False)]:
            records = corpus(); records[2][0][field] = replacement
            with self.assertRaises(ValueError): reconcile(*records)

    def test_duplicate_source_and_contradictory_overlap_are_refused(self):
        records = corpus(); records[1].append(copy.deepcopy(records[1][0]))
        with self.assertRaises(ValueError): reconcile(*records)
        records = corpus(); records[3][0]['status'] = 'verified_disjoint'
        with self.assertRaisesRegex(ValueError, 'CONTRADICTORY'): reconcile(*records)

    def test_xy_without_assay_and_folds_remains_descriptive(self):
        records = corpus()
        records[1][0].update(xy_mapping_verified=True, target_unit_verified=True)
        counts = reconcile(*records)['denominators']
        self.assertEqual(counts['XY_descriptive_eligible_views'], 1)
        self.assertEqual(counts['leakage_safe_supervised_eligible_views'], 0)


class NativeDescriptorSynthesis(unittest.TestCase):
    def test_json_schema_privacy_and_recursive_result_state_invariants(self):
        import json
        from pathlib import Path
        import jsonschema
        path = Path(__file__).resolve().parents[2]/'schemas/cross-dataset-synthesis.v1.schema.json'
        schema = json.loads(path.read_text())
        value = compare([], 'controlled-empty-cohort')
        jsonschema.validate(value, schema)
        changed = copy.deepcopy(value); changed['visibility'] = 'public'
        with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(changed, schema)
        for cell in [{'status':'computed','reason':'bad','value':1},
                {'status':'unavailable','reason':'missing','value':0}, {'status':'unavailable','value':None},
                {'status':'computed','reason':None,'value':float('nan')},
                {'status':'invented','reason':'unknown','value':None}]:
            with self.assertRaises(ValueError): validate_states({'nested':[cell]})

    def test_native_positive_negative_and_orthogonal_threshold_screens(self):
        for a, b, expected in [([1,2,3,4],[2,4,6,8],True), ([1,2,3,4],[-1,-2,-3,-4],True),
                ([-1,-1,1,1],[-1,1,-1,1],False)]:
            result = threshold_association(a,b,['a','b','c','d'])
            self.assertEqual([s['exceeds'] for s in result['value']['screens']], [expected]*3)
            self.assertIsNone(result['value']['exact_coefficient']['value'])

    def test_native_screen_replay_and_joint_key_permutation_are_exact(self):
        a,b,ids = [1,2,3,4],[3,6,9,12],['a','b','c','d']
        first = threshold_association(a,b,ids)
        self.assertEqual(first, threshold_association(a,b,ids))
        self.assertEqual(first['value']['screens'], threshold_association(a[::-1],b[::-1],ids[::-1])['value']['screens'])

    def test_constant_and_insufficient_values_are_not_weak_association(self):
        for a,b,ids in [([1,1,1],[2,3,4],['a','b','c']),([1,2],[2,4],['a','b'])]:
            self.assertIsNone(threshold_association(a,b,ids)['value'])

    def test_unmatched_nonfinite_or_reused_keys_are_refused(self):
        for a,b,ids in [([1,2,3],[1,2],['a','b','c']),([1,2,float('nan')],[1,2,3],['a','b','c']),
                ([1,2,3],[1,2,3],['a','a','b'])]:
            with self.assertRaises(ValueError): threshold_association(a,b,ids)

    def test_missing_exact_moments_never_become_truncated_dimension(self):
        profile = {'n_observations': 20, 'n_bands': 30, 'pca': {'pc1_fraction': .8},
            'effective_dimension': state(reason='EXACT_MOMENTS_BUDGET_EXCEEDED')}
        row = describe('synthetic','raw',profile,{},family='controlled',modality='NIR')
        self.assertEqual(row['metrics']['pc1_fraction']['value'], .8)
        self.assertIsNone(row['metrics']['effective_dimension']['value'])

    def test_target_payload_cannot_enter_x_descriptor_assembly(self):
        profile = {'n_observations': 20, 'n_bands': 30, 'Y_test': [1,2]}
        with self.assertRaisesRegex(ValueError, 'OUTCOME_INPUT_FORBIDDEN'):
            describe('synthetic','raw',profile,{},family='controlled',modality='NIR')

    def test_no_arbitrary_scalar_for_undefined_values(self):
        for value in [None, True, float('inf'), state(reason='unsupported')]:
            self.assertIsNone(scalar(value)['value'])

    def test_paired_summary_does_not_pool_representations_as_studies(self):
        rows = [{'view_id': 'synthetic', 'representation': rep, 'family':'controlled', 'n_observations':20,
            'n_bands':30,'metrics': {'pc1_fraction': state(value)}} for rep,value in [('raw',.8),('snv',.3)]]
        result = compare(rows, 'synthetic-cohort')
        changes = result['paired_representation_changes'][0]
        self.assertEqual(len(changes['matched_views']), 1)
        self.assertAlmostEqual(changes['change_summary']['value']['mean'], -.5, delta=1e-10)
        self.assertIsNone(result['study_level_inference']['value'])
        with self.assertRaisesRegex(ValueError, 'DUPLICATE'): compare(rows+[rows[0]], 'synthetic-cohort')


if __name__ == '__main__': unittest.main()
