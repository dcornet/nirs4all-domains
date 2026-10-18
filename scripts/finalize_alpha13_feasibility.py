"""Source-level feasibility, never a score-based model admission."""
import json
from pathlib import Path
from alpha13_common import PUBLIC
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import atomic_json,digest,fingerprint


def main():
    contract=json.loads((PUBLIC/'falsification-contract.json').read_text())
    sources=json.loads((PUBLIC/'source-admissions.json').read_text());inputs=json.loads((PUBLIC/'real-input-freeze.json').read_text())
    assert len(sources['admissions'])==2 and contract['study_roles']['independent_confirmation_studies']==0
    blockers={
        'ucph_tablet_nir':['Original batch/assay dependency ownership is not verified.','An exact source observation-key audit, even when successful, does not establish tablet/reference independence.','No exact target/reference task and independent outer/inner folds admitted; targets remain unopened.'],
        'ohpl_soil_nir':['36 original plots are documented but their exact canonical sample membership is not verified.','No original source-reference/assay key closure; equal counts cannot assign triples to plots.','No qualified target-free field projection of the original MATLAB object; full-object load was rejected and not retried.'],
        'cartilage_spectroscopy_scientificdata_nir':['Physical locations and five joints are verified, but donor and assay closure remain unresolved.','Prior alpha.10/11 supervised nonadmission is preserved.'],
        'ohpl_beer_nir':['Original specimen/reference correspondence and selective X field IO remain unqualified.','Not acquired or scored; package documentation alone does not admit a supervised task.'],
        'ohpl_wheat_nir':['Original physical/reference ownership and source-study overlap remain unresolved.','Not acquired or scored; a different target does not create another study.']}
    rows=[]
    for name,reasons in blockers.items():
        entry=next((e for e in inputs['entries'] if e['dataset_id']==name),None)
        rows.append({'dataset_id':name,'x_only_admitted':any(a['specification']['dataset_id']==name for a in sources['admissions']) or name.startswith('cartilage'),
            'source_study_reference':entry.get('original_study_reference') if entry else None,
            'model_admission':state(reason='; '.join(reasons)),'blockers':reasons,'target_accessed':False})
    value={'protocol_version':'domains.alpha13.validation_feasibility.v0.1','falsification_contract_id':contract['contract_id'],
        'hypothesis_register_sha256':contract['hypothesis_register_ref']['sha256'],'source_admissions_sha256':digest(PUBLIC/'source-admissions.json'),
        'historical_discovery_cases':['EcoSIS/CA2023','Perten','Litter'],'historical_cases_reclassified_as_confirmation':0,
        'new_source_study_candidates':2,'independent_confirmation_studies':0,'admitted_supervised_tasks':0,'admitted_group_holdouts':0,
        'sources':rows,'cohort_roles':contract['study_roles'],'new_candidates_reserved_for_later_review':['ucph_tablet_nir','ohpl_soil_nir'],
        'descriptor_variation':state({'scope':'Two additional material-family source views; variation is descriptive and not independent-study power.'}),
        'confirmatory_power':state(reason='NO_ADMITTED_INDEPENDENT_CONFIRMATION_STUDIES_OR_REFERENCE_CLOSED_TASKS; OUTCOME_NOISE_AND_MATCHED_HOLDOUT_SUPPORT_UNKNOWN',status='insufficient_information'),
        'pilot':state(reason='NO_NEW_TASK_WITH_ORIGINAL_PHYSICAL_REFERENCE_CLOSURE_AND_FROZEN_GROUP_SAFE_EVALUATIONS'),
        'model_anchors':contract['model_anchors'],'response_definitions':contract['response_definitions'],
        'counterexample_policy':'Preserve every registered observation irrespective of direction; no new supervised observations exist in alpha.13. Synthetic falsification fixtures are not real-data confirmations.',
        'supervised_model_fits':0,'target_accessed':False,'model_performance_used':False,'hypotheses_confirmed':[],
        'hypotheses_contradicted_by_new_supervised_results':[],'universal_shortcut_score':None,
        'scope':'Feasibility, not a claim that any H1-H5 hypothesis is true or that future valid admission is impossible.'}
    literature=PUBLIC/'sources/tablet-literature-audit.json'
    if literature.exists():value['original_literature_review_ref']={'path':literature.as_posix(),'sha256':digest(literature)}
    value['record_id']=fingerprint(value);atomic_json(PUBLIC/'validation-feasibility.json',value)
    print(json.dumps({'confirmation_studies':0,'admitted_tasks':0,'model_fits':0,'pilot_reason':value['pilot']['reason']}))


if __name__=='__main__':main()
