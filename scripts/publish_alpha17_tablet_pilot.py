"""Publish only permitted aggregate outcomes from the frozen exploratory pilot."""
from pathlib import Path

from alpha17_common import Context,read
from nirs4all_domains.dependence import score_oof,state
from nirs4all_domains.storage import atomic_json,digest
from nirs4all_domains.synthesis import describe,validate_states


def main():
    c=Context();p=c.load('ORIGINAL_KEYED_TABLET_PILOT_FREEZE.json')
    pointer=c.load('tablet-pilot-results.json');assert digest(pointer['artifact_path'])==pointer['artifact_sha256']
    result=read(pointer['artifact_path']);assert result['plan_id']==p['plan_id']
    audit=c.auth(c.store.root/'screening-rights-reviewed.json','audit')
    entry=next(r for r in audit['entries'] if r['dataset_id']==p['dataset_id'])
    permission=entry['permissions']['publish_aggregates']
    assert permission['status']=='allowed' and permission['evidence_receipts']
    assert result['native_model_fits']==104 and result['PCA_fits']==4 and result['retained_target_accessed'] is False
    original=p['frozen_X_descriptors'];descriptors=[]
    for rep,ref in original['profiles'].items():
        assert digest(ref['path'])==ref['sha256']
        profile=read(ref['path']);profile=profile['value'] if 'status' in profile else profile
        descriptors.append(describe(p['dataset_id']+'/X',rep,profile,state(original['representation_agreement']),family=entry['family'],modality='NIR'))
    by_id={r['observation_id']:r for r in p['identities']['records']}
    contexts=[]
    for f,diagnostic in zip(p['identities']['outer_folds']['folds'],result['diagnostics'],strict=True):
        assert f['fold_id']==diagnostic['fold_id']
        levels={by_id[k]['source_type'] for k in f['validation_sample_ids']};assert len(levels)==1
        contexts.append({'source_type':next(iter(levels)),'n_train':len(f['train_sample_ids']),'n_evaluation':len(f['validation_sample_ids']),
            'target_below_training_min':diagnostic['eval_below_training_target_min'],
            'target_above_training_max':diagnostic['eval_above_training_target_max'],
            'training_target_summary':diagnostic['training_only_target_summary'],
            'train_fitted_PC1_PC2_summaries':diagnostic['PC1_PC2'],
            'continuous_support':diagnostic['continuous_support'],'exact_full_moments':diagnostic['exact_full_moments'],
            'models':{}})
        for anchor,values in result['outcomes'].items():
            blocks=[r for r in values['OOF'] if r['observation_id'] in f['validation_sample_ids']]
            assert len(blocks)==len(f['validation_sample_ids'])
            scores=next(r['scores'] for r in values['per_context'] if r['fold_id']==f['fold_id'])
            null=score_oof(blocks,'null_prediction',target='reference_value')
            rm=scores['value']['rmse'];rn=null['value']['rmse']
            skill=state(1-rm['value']/rn['value']) if rm['status']==rn['status']=='computed' and rn['value']>0 else state(reason='ZERO_OR_UNDEFINED_TRAINING_NULL_RMSE')
            trace=next(r for r in result['lineage'] if r['fold_id']==f['fold_id'] and r['anchor']==anchor)['lineage']
            assert trace['native_fit_lineage_verified'] is True
            contexts[-1]['models'][anchor]={'scores':scores,'null':null,'S':skill,'selected_parameters':trace['selected'],
                'native_inner_training_lineage_verified':True,'candidate_count':trace['candidate_count']}
    public={'protocol':p['protocol'],'dataset_id':p['dataset_id'],'source_id':'X','content_version':'1.0.0',
        'source_url':p['source_url'],'target':{'meaning':p['target']['meaning'],'unit':p['target']['unit']},
        'evaluation_scope':'Exploratory leave-one-original-Type-out nested CV; known declared blocks preserved, unknown physical/assay dependencies.',
        'n_observations':310,'n_bands':404,'original_contexts':4,'declared_blocks_preserved':31,
        'numeric_target_values_qualified':True,'retained_target_accessed':False,'independent_generalization':False,
        'anchors':p['anchors'],'native_model_fits':104,'train_only_PCA_fits':4,
        'pooled_outcomes':{k:{field:v[field] for field in ['model','null','S']} for k,v in result['outcomes'].items()},
        'contexts':contexts,'frozen_full_source_X_descriptors':descriptors,
        'hypothesis_scope':{'H1_H5_changed':False,'descriptor_selection_uses_outcomes':False,
            'D_RMSE':state(reason='NO_MATCHED_REFERENCE_STRESS_CONTRAST'),
            'D_skill':state(reason='NO_MATCHED_REFERENCE_STRESS_CONTRAST'),
            'independent_confirmation':state(reason='ONE_EXPLORATORY_POPULATION_WITH_UNKNOWN_PHYSICAL_ASSAY_DEPENDENCIES')},
        'observed_resources':{'native_worker_wall_seconds':result['wall_seconds'],'worker_lifetime_peak_resident_bytes':result['observed_peak_bytes'],
            'reservation_bytes':8388608,'campaign_reserved_bytes':c.guard()['campaign_reserved_bytes']},
        'findings':[
            {'observation':'Both pooled models improve on the training-only null, while a whole held-out context has negative R2 and all its outcomes below training target support.',
             'confidence':'Exact keyed development OOF aggregation under the frozen four-context design; uncertainty beyond this source is not quantified.',
             'consequence':'Pooled fit quality can hide poor context transfer and target-range extrapolation.',
             'action':'Retain pooled/per-context scores and frozen descriptors; require matched stress/control designs before testing degradation hypotheses.'},
            {'observation':'Ridge has lower pooled RMSE but higher RMSE than PLS in the fully target-extrapolating context.',
             'confidence':'Descriptive same-evaluation-identity comparison; no independent-study significance claim.',
             'consequence':'One pooled estimator ranking does not establish universal context robustness.',
             'action':'Keep both prespecified families and every context; do not select a single favorable model or retune H1–H5.'}],
        'limitations':['Type and canonical block membership do not verify physical specimen, assay-event or study independence.',
            'Full-source X-only profiles and train-fitted PCA diagnostics have different reference scopes.',
            'No random-CV reference, matched-size stress control, causal shortcut fraction or study-level confidence interval is estimated.',
            'Target extrapolation, training population composition and spectral support are not experimentally isolated.',
            'Continuous support and exact train full moments remain explicitly unavailable; PCA scores do not supply complete covariance moments.'],
        'publication':'Ordinary aggregate statistics under existing UCPH public-use permission. Raw X/Y, source keys, fold rosters, models and OOF vectors remain local.'}
    validate_states(public)
    import jsonschema
    jsonschema.validate(public,read('schemas/exploratory-pilot-summary.v1.schema.json'))
    path=Path('docs/benchmarks/alpha17/tablet-pilot-summary.json');atomic_json(path,public)
    c.save('tablet-pilot-publication-receipt.json',{'path':str(path),'sha256':digest(path),'source_permission_evidence':permission,'plan_id':p['plan_id']})
    c.preservation();print('ALPHA17_EXPLORATORY_TABLET_AGGREGATES_PUBLISHED; NO_REFIT')


if __name__=='__main__':
    try:main()
    except Exception as error:
        try:Context().save('tablet-publication-failure.json',{'type':type(error).__name__,'detail':str(error)})
        except Exception:pass
        print('ALPHA17_TABLET_PUBLICATION_REFUSED; DETAILS_REMAIN_LOCAL');raise SystemExit(2) from None
