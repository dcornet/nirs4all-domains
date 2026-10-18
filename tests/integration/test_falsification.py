import copy
import unittest
from nirs4all_domains.falsification import freeze_roles,response,retain_evidence,require_pre_outcome


def record(source='a',study='study:new',role='potential_confirmation',population='material:new'):
    return {'source_id':source,'original_study_id':study,'role':role,'population_namespace':population,
        'original_study_verified':True,'physical_reference_closure_verified':False,'untouched_outcomes':True,'exact_task_and_splits_frozen':False}


class FalsificationControls(unittest.TestCase):
    def test_original_study_views_cannot_cross_discovery_confirmation(self):
        with self.assertRaisesRegex(ValueError,'STUDY_SPLIT'):freeze_roles([record(role='discovery'),record('b',role='potential_confirmation',population='another')],[])

    def test_shared_population_cannot_cross_different_study_names(self):
        with self.assertRaisesRegex(ValueError,'SHARED_POPULATION'):freeze_roles([record(role='discovery'),record('b','study:another')],[])

    def test_unknown_overlap_is_conservatively_kept_out_of_confirmation(self):
        a=record(role='discovery');b=record('b','study:other',population='material:other')
        with self.assertRaisesRegex(ValueError,'OVERLAP'):freeze_roles([a,b],[{'source_ids':['a','b'],'overlap':'unknown_possible'}])

    def test_historical_cases_do_not_reset_after_new_models(self):
        for study in ['study:ecosis-ca2023','study:perten','study:litter-2024']:
            with self.assertRaisesRegex(ValueError,'HISTORICAL'):freeze_roles([record(study=study)],[])

    def test_candidate_is_not_an_admitted_confirmation_study(self):
        r=record();self.assertEqual(freeze_roles([r],[])['independent_confirmation_studies'],0)
        r['role']='confirmation'
        with self.assertRaisesRegex(ValueError,'ADMISSION'):freeze_roles([r],[])

    def test_scores_or_retained_y_cannot_change_preregistration(self):
        for field in ['future_scores','Y_test','rmse','predictions']:
            r=record();r[field]=[999.,-999.]
            with self.assertRaisesRegex(ValueError,'OUTCOME_INPUT'):freeze_roles([r],[])

    def test_multiple_folds_or_targets_do_not_inflate_study_support(self):
        records=[record(str(i),role='discovery') for i in range(12)]
        self.assertEqual(freeze_roles(records,[])['independent_confirmation_studies'],0)

    def test_disjointness_needs_evidence(self):
        with self.assertRaisesRegex(ValueError,'DISJOINTNESS'):freeze_roles([record(),record('b','other',population='other')],[{'source_ids':['a','b'],'overlap':'verified_disjoint'}])

    def test_cross_role_disjointness_cannot_be_assumed_from_study_names(self):
        rows=[record(role='discovery'),record('b','study:other',population='material:other')]
        with self.assertRaisesRegex(ValueError,'OVERLAP'):freeze_roles(rows,[])
        relation={'source_ids':['b','a'],'overlap':'verified_disjoint','evidence_sha256':'f'*64}
        self.assertEqual(freeze_roles(rows,[relation])['independent_confirmation_studies'],0)

    def test_shared_or_unknown_populations_cannot_inflate_confirmation_studies(self):
        rows=[record(role='confirmation'),record('b','study:other','confirmation','material:other')]
        for r in rows:r.update(physical_reference_closure_verified=True,exact_task_and_splits_frozen=True)
        for overlap in ['verified_shared','unknown_possible']:
            with self.assertRaisesRegex(ValueError,'OVERLAP'):freeze_roles(rows,[{'source_ids':['a','b'],'overlap':overlap}])
        relation={'source_ids':['a','b'],'overlap':'verified_disjoint','evidence_sha256':'f'*64}
        self.assertEqual(freeze_roles(rows,[relation])['independent_confirmation_studies'],2)

    def test_admission_rejects_truthy_nonbooleans(self):
        r=record(role='confirmation');r.update(physical_reference_closure_verified=True,exact_task_and_splits_frozen=True)
        for value in ['true',1]:
            bad=copy.deepcopy(r);bad['untouched_outcomes']=value
            with self.assertRaisesRegex(ValueError,'ADMISSION'):freeze_roles([bad],[])

    def test_invalid_relations_and_empty_study_ids_fail_closed(self):
        rows=[record(),record('b','other',population='other')]
        for relation in [{'source_ids':['a','b'],'overlap':'not_a_known_state'},
                         {'source_ids':['a','b'],'overlap':'verified_disjoint','evidence_sha256':'not-a-digest'},
                         {'source_ids':['a','foreign'],'overlap':'unknown_possible'}]:
            with self.assertRaises(ValueError):freeze_roles(rows,[relation])
        relation={'source_ids':['a','b'],'overlap':'unknown_possible'}
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):freeze_roles(rows,[relation,relation])
        bad=record(study='')
        with self.assertRaisesRegex(ValueError,'NONEMPTY'):freeze_roles([bad],[])

    def metrics(self,rmse=1.,null=2.,ids=None):
        return {'rmse':rmse,'null_rmse':null,'target_definition':'example:concentration','target_unit':'percent',
            'evaluation_ids':ids or ['x','y'],'metrics_from_native_provider':True,'null_fitted_on_training_only':True}

    def test_frozen_outcome_sign_and_zero_null(self):
        r=response(self.metrics(),self.metrics(3.))['value'];self.assertEqual(r['d_rmse'],2.);self.assertEqual(r['d_skill']['value'],-1.)
        self.assertEqual(response(self.metrics(null=0),self.metrics())['value']['d_skill']['status'],'unavailable')

    def test_unmatched_populations_are_not_a_structural_effect(self):
        self.assertEqual(response(self.metrics(),self.metrics(ids=['different']))['status'],'inconclusive')

    def test_target_units_and_null_scope_are_enforced(self):
        bad=self.metrics();bad['target_unit']='mg/kg'
        with self.assertRaisesRegex(ValueError,'TARGET_DEFINITION'):response(self.metrics(),bad)
        bad=self.metrics();bad['null_fitted_on_training_only']=False
        with self.assertRaisesRegex(ValueError,'TRAINING_ONLY_NULL'):response(self.metrics(),bad)

    def test_empty_evaluation_sets_cannot_produce_paired_responses(self):
        bad=self.metrics();bad['evaluation_ids']=[]
        with self.assertRaisesRegex(ValueError,'NONEMPTY'):response(bad,bad)
        a=self.metrics();b=self.metrics(ids=['y','x'])
        self.assertEqual(response(a,b)['status'],'computed')

    def test_finite_metrics_do_not_authorize_nonfinite_skill(self):
        bad=self.metrics(rmse=1e308,null=1e-308)
        r=response(bad,self.metrics())
        self.assertEqual(r['value']['reference_skill']['status'],'unavailable')
        self.assertEqual(r['value']['d_skill']['status'],'unavailable')
        import json
        json.dumps(r,allow_nan=False)

    def test_all_scheduled_outcomes_including_failures_must_be_retained(self):
        cohort=freeze_roles([record()],[])
        outcomes=[{'source_id':'a','observation_id':'task:good','status':'potential_counterexample'},
                  {'source_id':'a','observation_id':'task:failed','status':'unavailable','reason':'REFERENCE_UNRESOLVED'}]
        roster=['task:good','task:failed']
        with self.assertRaisesRegex(ValueError,'ROSTER'):retain_evidence(cohort,outcomes[:1],roster)
        r=retain_evidence(cohort,outcomes,roster)
        self.assertEqual(r['observations'],outcomes)
        self.assertEqual(r['scheduled_completeness']['status'],'computed')
        self.assertEqual(retain_evidence(cohort,outcomes)['scheduled_completeness']['status'],'unavailable')

    def test_h1_to_h5_potential_counterexamples_are_preserved(self):
        cohort=freeze_roles([record()],[])
        observations=[{'source_id':'a','observation_id':'H'+str(i),'status':'potential_counterexample','description':description}
            for i,description in enumerate(['Stable X with good transfer','High overlap without advantage',
                'Representation change without interaction','Support shift without deterioration',
                'Initially uncertain close objects verified independent without validity change'],1)]
        result=retain_evidence(cohort,observations);self.assertEqual(result['observations'],observations)
        self.assertEqual(response(self.metrics(),self.metrics())['value']['study_level_hypothesis_verdict']['status'],'insufficient_information')


if __name__=='__main__':unittest.main()
