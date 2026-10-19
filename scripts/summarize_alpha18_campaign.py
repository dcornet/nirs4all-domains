"""Shared full-bank matrices and native cross-view descriptive confrontation."""
from collections import Counter,defaultdict
import copy
import json
from pathlib import Path
import re

import jsonschema
from alpha18_common import Context,read
from nirs4all_domains.dependence import state
from nirs4all_domains.predictive import native_summary
from nirs4all_domains.storage import atomic_json,digest,fingerprint
from nirs4all_domains.synthesis import validate_states,threshold_association,compare

OUT=Path('docs/campaign')


def reason(value):
    # Native diagnostics can quote an offending private cell: retain those
    # diagnostics locally, expose only a stable operational category.
    if value and 'Insufficient independent groups for the prespecified CV' in value:return 'FEWER_THAN_THREE_DECLARED_COMPONENTS'
    if value and 'could not convert string to float' in value:return 'INVALID_NONMISSING_NUMERIC_TARGET_CELL'
    text=(value or 'NOT_ATTEMPTED').split(':')[-1]
    return text if re.fullmatch('[A-Z][A-Z0-9_]+',text) else 'NUMERIC_OR_TRANSPORT_FAILURE'


def artifacts(c,name):
    if not (c.root/name).exists():return {}
    result={}
    for ref in c.load(name):
        if ref.get('artifact_path'):
            assert digest(ref['artifact_path'])==ref['artifact_sha256']
            value=read(ref['artifact_path']);result[ref['task_id']]=value
        else:result[ref['task_id']]={'result':ref['result']}
    return result


def join_and_screen(experiments,descriptor_rows):
    byview=defaultdict(list)
    for t in experiments:
        if t['execution_state']=='computed' and t['aggregates']['status']=='computed' and t.get('valid_for_primary_quantitative_analysis'):byview[t['view_id']].append(t)
    joined=[];raw={r['view_id']:r for r in descriptor_rows if r['representation']=='raw'}
    for key,tt in sorted(byview.items()):
        if key not in raw:continue
        skills={}
        for family in ['pls','ridge']:
            vals=[t['aggregates']['value']['families'][family]['pooled']['value']['skill']['value'] for t in tt if t['aggregates']['value']['families'][family]['pooled']['status']=='computed' and t['aggregates']['value']['families'][family]['pooled']['value']['skill']['status']=='computed']
            skills[family]=state(native_summary(vals)) if vals else state(reason='NO_COMPLETE_ELIGIBLE_TARGETS')
        joined.append({'view_id':key,'dataset_id':key.rsplit('/',1)[0],'n_target_tasks':len(tt),
            'descriptors':raw[key]['metrics'],'skill_across_targets':skills,
            'evidence_role':'historical_discovery_related' if any(w in key for w in ['cabo_2018','perten_cereals','intact_and_ground_leaf_litter','ucph_tablet']) else 'new_exploratory_confrontation',
            'independent_study_verified':False})
    screens=[]
    for descriptor in ['pc1_fraction','effective_dimension','neighbor_cv','proximity_0.01','raw_snv_ari','raw_snv_overlap']:
        for family in ['pls','ridge']:
            sample=[r for r in joined if r['descriptors'][descriptor]['status']=='computed' and r['skill_across_targets'][family]['status']=='computed']
            screens.append({'descriptor':descriptor,'family':family,'outcome':'median within-view target CV skill',
                'result':threshold_association([r['descriptors'][descriptor]['value'] for r in sample],[r['skill_across_targets'][family]['value']['median'] for r in sample],[r['view_id'] for r in sample])})
    return joined,screens


def representation_interactions(raw,snv):
    rows=[]
    for key,a in raw.items():
        b=snv.get(key)
        if b is None:continue
        base={k:a[k] for k in ['task_id','view_id','target','unit']}
        if a['result']['status']!=b['result']['status'] or a['result']['status']!='computed':
            rows.append(base|{'result':state(reason='PAIRED_REPRESENTATION_STRESS_UNAVAILABLE')});continue
        assert a['population_fingerprints']==b['population_fingerprints'],'RAW_SNV_TRAIN_OR_EVALUATION_MEMBERSHIPS_DIFFER'
        aa=a['result']['value'];bb=b['result']['value'];pairs={}
        for family in ['pls','ridge']:
            da=aa['deterioration'][family];db=bb['deterioration'][family]
            if da['status']!=db['status'] or da['status']!='computed':pairs[family]=state(reason='PAIRED_MODEL_DETERIORATION_UNAVAILABLE');continue
            ma=aa['regimes']['size_control']['models'][family]['value']['common_null_scores']['null_rmse']['value']
            mb=bb['regimes']['size_control']['models'][family]['value']['common_null_scores']['null_rmse']['value']
            assert abs(ma-mb)<=1e-10,'REPRESENTATION_COMMON_NULL_DENOMINATOR_CHANGED'
            sa=da['value']['D_skill'];sb=db['value']['D_skill']
            pairs[family]=state({'I_RMSE':db['value']['D_RMSE']-da['value']['D_RMSE'],
                'I_skill':state(sb['value']-sa['value']) if sa['status']==sb['status']=='computed' else state(reason='COMMON_NULL_SKILL_UNDEFINED')})
        rows.append(base|{'result':state({'factor':aa['factor'],'matched_memberships_verified':True,'common_null_denominator_verified':True,'model_interactions':pairs})})
    return rows


def interaction_screens(interactions,descriptor_rows):
    descriptors={r['view_id']:r['metrics'] for r in descriptor_rows if r['representation']=='raw'};result=[]
    for metric in ['raw_snv_ari','raw_snv_overlap']:
        for family in ['pls','ridge']:
            sample=[]
            for r in interactions:
                if r['result']['status']!='computed' or r['view_id'] not in descriptors:continue
                d=descriptors[r['view_id']][metric];v=r['result']['value']['model_interactions'][family]
                if d['status']=='computed' and v['status']=='computed' and v['value']['I_skill']['status']=='computed':sample.append((r['view_id'],d['value'],abs(v['value']['I_skill']['value'])))
            result.append({'descriptor':metric,'family':family,'outcome':'absolute matched raw/SNV stress-skill interaction',
                'result':threshold_association([r[1] for r in sample],[r[2] for r in sample],[r[0] for r in sample])})
    return result


def main():
    c=Context();f=c.load('campaign-freeze.json');xf=c.load('X-descriptor-freeze.json')
    if (c.root/'X-available-descriptor-freeze.json').exists():xf=c.load('X-available-descriptor-freeze.json')
    x=artifacts(c,'X-progress.json');tasks=artifacts(c,'reference-progress.json');stress=artifacts(c,'stress-progress.json');snv_stress=artifacts(c,'SNV-stress-progress.json')
    nulls=artifacts(c,'null-progress.json')
    grouped=artifacts(c,'group-sensitivity-progress.json')
    semantics={r['task_id']:r for r in c.load('target-semantics-v2.json')['records']}
    rows=defaultdict(list)
    for r in xf['rows']:rows[r['view_id']].append(r)
    publicrows=[];sources=[];allowed={}
    for s in f['sources']:
        key=s['view_id'];allowed[key]=s['aggregate_permission'] in ['allowed','allowed_noncommercial']
        if len(rows[key])==2:status='computed';why=None
        elif rows[key]:status='partial';why='PAIRED_REPRESENTATION_INCOMPLETE'
        elif key in x:status=x[key]['result']['status'];why=reason(x[key]['result']['reason'])
        else:status=s['X_plan'];why={'resource_deferred':'INITIAL_MATRIX_COST_TIER_EXCEEDED','analysis_not_authorized':'ANALYSIS_NOT_AUTHORIZED','source_unavailable':'SOURCE_UNAVAILABLE'}.get(status,'NOT_ATTEMPTED')
        aggregate=state(rows[key]) if rows[key] and allowed[key] else state(reason='SOURCE_AGGREGATE_PUBLICATION_TERMS_UNRESOLVED' if rows[key] else why)
        sources.append({k:s.get(k) for k in ['view_id','dataset_id','source_id','content_version','family','modality','n_observations','n_bands','aggregate_permission','prior_execution_state']}|
            {'execution_state':status,'reason':why,'reused_exact_profile':s['reused_exact_profile'],
             'aggregates':aggregate,'original_study_independence':'not_verified'})
        if allowed[key]:publicrows.extend(rows[key])
    structural={'schema_version':1,'protocol':'domains.full_bank.structural_matrix.v0.1',
        'descriptor_freeze_id':xf['descriptor_freeze_id'],'sources':sources,
        'counts':dict(Counter(s['execution_state'] for s in sources)),
        'public_computed_views':sum(bool(rows[s['view_id']]) and allowed[s['view_id']] for s in sources),
        'target_used_for_descriptors':False}
    validate_states(structural);atomic_json(OUT/'structural-matrix.json',structural)
    experiments=[];local=[]
    qualifications={q['view_id']:q['result'] for q in f['qualification']}
    continuation=c.load('scope-marker-continuation.json');f['scopes'].update(continuation['scopes'])
    retained=c.load('historical-retained-continuation.json');f['scopes'].update(retained['scopes'])
    for key in retained['blocked_sources']:f['scopes'].pop(key,None)
    for t in f['tasks']:
        sem=semantics.get(t['task_id'],{});v=tasks.get(t['task_id'])
        base={k:t[k] for k in ['task_id','dataset_id','view_id','target','unit','metadata_eligible']}
        base.update(target_evidence=sem.get('target_evidence','not_qualified'),independent_generalization=False,
                    semantic_eligible=t['metadata_eligible'] and not sem.get('excluded',False),
                    valid_for_primary_quantitative_analysis=t['metadata_eligible'] and not sem.get('excluded',False) and sem.get('target_evidence')=='catalog_quantitative_outcome_assay_independence_unverified',
                    retained_target_decoded=False,alignment='owner_attested_same_export_order' if t['view_id'] in f['scopes'] else None)
        if not t['metadata_eligible']:st='ineligible';why=t['eligibility_reason']
        elif sem.get('excluded'):st='ineligible';why=sem['reason']
        elif t['view_id'] in retained['blocked_sources']:st='unavailable';why=retained['blocked_sources'][t['view_id']]
        elif v is not None:
            st='computed' if v['result']['status']=='computed' else 'failed';why=reason(v['result']['reason']) if st=='failed' else None
            if st=='computed' and not v['result']['value']['reference_complete']:st='partial';why='INCOMPLETE_OOF_FAMILY'
        elif t['view_id'] not in f['scopes']:st='unavailable';why=reason(qualifications.get(t['view_id'],{}).get('reason'))
        elif x.get(t['view_id'],{}).get('result',{}).get('reason')=='ValueError:NONFINITE_OR_EMPTY_X':st='unavailable';why='REQUIRED_X_NUMERIC_VALUES_INVALID'
        else:st='not_attempted';why='TASK_NOT_EXECUTED_WITHIN_CURRENT_PASS'
        base.update(execution_state=st,reason=why,model_fit_attempts=v.get('model_fit_attempts',0) if v else 0,
                    model_fit_successes=v.get('model_fit_successes',0) if v else 0)
        base['task_artifact_exists']=v is not None
        base['model_fitting_attempted']=base['model_fit_attempts']>0
        metrics={}
        if v and 'families' in v:
            metrics={k:v[k] for k in ['n_development','n_evaluated','n_groups','group_columns','evaluation_scope','n_retained_excluded','n_purged_retained_component','target_summary','components','n_missing_target','n_available_components_with_missing_members']}
            metrics['null_baseline']=v['null_baseline']
            metrics['families']={name:{'pooled':fam['pooled'],'folds':[{k:r[k] for k in r if k!='fold_id'} for r in fam['folds']]} for name,fam in v['families'].items()}
        population=v.get('target_population',state(reason='TARGET_NOT_DECODED')) if v else state(reason='TARGET_NOT_DECODED')
        baseline=nulls.get(t['task_id'],{}).get('result',v.get('null_baseline',state(reason='NULL_EVALUATION_UNAVAILABLE')) if v else state(reason='NULL_EVALUATION_UNAVAILABLE'))
        if baseline['status']=='computed' and 'scores' not in baseline['value']:
            baseline=state({'scores':baseline['value'],'n_evaluated':v['n_evaluated'],'fold_fingerprint':v['fold_fingerprint']})
        local.append(base|{'target_population':population,'feature_free_null':baseline,'aggregates':state(metrics) if metrics else state(reason=why or 'NO_COMPLETED_MODEL_METRICS')})
        numerical_publication=allowed[t['view_id']] and base['semantic_eligible']
        withheld='NUMERIC_IDENTIFIER_OR_CATEGORY_HAS_NO_REGRESSION_INTERPRETATION' if not base['semantic_eligible'] else 'SOURCE_AGGREGATE_PUBLICATION_TERMS_UNRESOLVED'
        experiments.append(base|{'target_population':population if numerical_publication else state(reason=withheld),
            'feature_free_null':baseline if numerical_publication else state(reason=withheld),
            'aggregates':state(metrics) if metrics and numerical_publication else state(reason=withheld if metrics else why or 'NO_COMPLETED_MODEL_METRICS')})
    experiment={'schema_version':1,'protocol':'domains.bank_reference.v0.1','campaign_freeze_id':f['freeze_id'],
        'descriptor_freeze_id':xf['descriptor_freeze_id'],'tasks':experiments,
        'counts':dict(Counter(t['execution_state'] for t in experiments)),
        'model_fit_attempts':sum(t['model_fit_attempts'] for t in experiments),
        'model_fit_successes':sum(t['model_fit_successes'] for t in experiments),
        'primary_quantitative_fit_successes':sum(t['model_fit_successes'] for t in experiments if t['valid_for_primary_quantitative_analysis']),
        'completed_primary_quantitative_tasks':sum(t['execution_state']=='computed' and t['valid_for_primary_quantitative_analysis'] for t in experiments),
        'excluded_identifier_diagnostic_fit_successes':sum(t['model_fit_successes'] for t in experiments if not t['semantic_eligible']),
        'attempt_count_scope':'Pipeline model attempts; mathematical pre-fit guards can refuse before a native fit call.',
        'success_count_scope':'Finite native fit/predict completions; subsequent scoring failures remain separate.',
        'independent_generalization_validated':False}
    validate_states(experiment);atomic_json(OUT/'experiment-matrix.json',experiment)
    c.save('local-experiment-matrix.json',experiment|{'tasks':local})
    # Public scientific synthesis never imports unknown-publication metrics.
    public_comparison=compare(publicrows,'alpha18-source-permitted-full-bank')
    atomic_json(OUT/'descriptor-distributions.json',public_comparison)
    joined,screens=join_and_screen(experiments,publicrows)
    local_joined,local_screens=join_and_screen(local,xf['rows'])
    c.save('local-descriptor-distributions.json',compare(xf['rows'],'alpha18-all-authorized-source-views'))
    c.save('local-confrontation.json',{'joined_source_views':local_joined,'native_absolute_correlation_screens':local_screens,
        'stress_tasks':list(stress.values()),'SNV_stress_tasks':list(snv_stress.values()),
        'representation_interactions':representation_interactions(stress,snv_stress),
        'interaction_descriptor_screens':interaction_screens(representation_interactions(stress,snv_stress),xf['rows']),
        'declared_plot_sensitivity':list(grouped.values()),
        'independent_confirmation':False})
    stressrows=[]
    for v in stress.values():
        r=copy.deepcopy(v)
        if not allowed.get(r['view_id']):r={'view_id':r['view_id'],'task_id':r['task_id'],'result':state(reason='SOURCE_AGGREGATE_PUBLICATION_TERMS_UNRESOLVED'),'execution_state':v['result']['status']}
        else:
            for k in ['training_indices','evaluation_indices','OOF','observation_ids','population_fingerprints']:r.pop(k,None)
        stressrows.append(r)
    snvrows=[]
    for v in snv_stress.values():
        r=copy.deepcopy(v)
        if not allowed.get(r['view_id']):r={'view_id':r['view_id'],'task_id':r['task_id'],'result':state(reason='SOURCE_AGGREGATE_PUBLICATION_TERMS_UNRESOLVED'),'execution_state':v['result']['status']}
        else:r.pop('population_fingerprints',None)
        snvrows.append(r)
    interactions=[]
    for r in representation_interactions(stress,snv_stress):
        if not allowed.get(r['view_id']):r={k:r[k] for k in ['view_id','task_id','target','unit']}|{'result':state(reason='SOURCE_AGGREGATE_PUBLICATION_TERMS_UNRESOLVED')}
        interactions.append(r)
    grouped_rows=[]
    for v in grouped.values():
        r=copy.deepcopy(v)
        if not allowed.get(r['view_id']):r={k:r[k] for k in ['view_id','task_id','target','unit']}|{'result':state(reason='SOURCE_AGGREGATE_PUBLICATION_TERMS_UNRESOLVED'),'execution_state':v['result']['status']}
        elif r['result']['status']=='computed':
            for fam in r['result']['value']['grouped_reference']['families'].values():fam.pop('oof',None)
        grouped_rows.append(r)
    confrontation={'schema_version':1,'protocol':'domains.full_bank.confrontation.v0.1',
        'joined_source_views':joined,'native_absolute_correlation_screens':screens,'stress_tasks':stressrows,
        'SNV_stress_tasks':snvrows,'representation_interactions':interactions,
        'interaction_descriptor_screens':interaction_screens(interactions,publicrows),
        'declared_plot_sensitivity':grouped_rows,
        'additional_model_fit_successes':sum(v.get('model_fit_successes',0) for v in [*stress.values(),*snv_stress.values(),*grouped.values()]),
        'additional_model_fit_attempts':sum(v.get('model_fit_attempts',0) for v in [*stress.values(),*snv_stress.values(),*grouped.values()]),
        'n_source_views':len(joined),'n_catalog_entries':len({r['dataset_id'] for r in joined}),
        'n_independently_confirmed_studies':0,'independent_confirmation':False,
        'model_comparison_population':'Primary quantitative targets with complete pooled OOF for BOTH fixed families; partial/failed cases remain in the experiment matrix.',
        'limitations':['Source views, multiple targets and folds are not independent studies.',
            'Median CV skill depends on the target mixture and is not a deterioration estimand.',
            'Full-source X descriptors and development available-case outcomes can describe different populations; missingness and sealed exclusions can change composition.',
            'Source-declared predicted traits and spectral indices are retained in the experiment matrix but excluded from the primary skill screens.',
            'Unknown physical/assay overlap and observation CV can inflate performance.',
            'Raw unscaled X and fixed Ridge alpha=1 imply different effective regularization across intensity units; these are pipeline results, not optimized estimator potential.',
            'Absolute correlation filters expose thresholds, not coefficient signs or p-values.']}
    validate_states(confrontation);atomic_json(OUT/'confrontation.json',confrontation)
    # Optional external study audit joins without rewriting frozen descriptors.
    study=read('configs/bank/study-evidence.json');jsonschema.validate(study,read('schemas/study-evidence.v1.schema.json'))
    identities={(s['dataset_id'],s['content_version'],s['source_id']) for s in f['sources']}
    assert all((r['dataset_id'],r['content_version'],r['source_id']) in identities for r in study['records'])
    status={'protocol':'domains.scientific_status.v1','catalog_entries':164,'declared_source_views':171,
        'computed_source_views':structural['counts'].get('computed',0),'partial_source_views':structural['counts'].get('partial',0),
        'publishable_source_views':structural['public_computed_views'],'failed_source_views':structural['counts'].get('failed',0),
        'resource_deferred_views':structural['counts'].get('resource_deferred',0),
        'analysis_not_authorized_views':structural['counts'].get('analysis_not_authorized',0),
        'source_execution_counts':structural['counts'],'declared_target_tasks':2054,
        'reference_task_counts':experiment['counts'],'model_fit_attempts':experiment['model_fit_attempts'],
        'model_fit_successes':experiment['model_fit_successes'],'public_joined_source_views':len(joined),
        'primary_quantitative_fit_successes':experiment['primary_quantitative_fit_successes'],
        'completed_primary_quantitative_tasks':experiment['completed_primary_quantitative_tasks'],
        'all_authorized_joined_source_views':len(local_joined),
        'independent_cross_study_descriptor_validation':False,'frozen_hypotheses':['H1','H2','H3','H4','H5'],
        'campaign_phase':'Executed exploratory full-bank characterization/reference/stress; independent confirmation pending',
        'evidence':['structural-matrix.json','experiment-matrix.json','confrontation.json']}
    atomic_json(OUT/'status.json',status)
    md=['# Full-bank structural coverage','', 'All 171 source views; published numbers require actual source permission. All columns and rows remain in source characterization.','',
        '| Source view | State | n x p | Raw PC1 | SNV PC1 |','|---|---|---:|---:|---:|']
    for s in sources:
        rr={r['representation']:r for r in s['aggregates']['value']} if s['aggregates']['status']=='computed' else {}
        vals=[]
        for rep in ['raw','snv']:
            m=rr.get(rep,{}).get('metrics',{}).get('pc1_fraction',{})
            vals.append(f"{m['value']:.4f}" if m.get('status')=='computed' else 'unavailable')
        md.append(f"| {s['view_id']} | {s['execution_state']} | {s['n_observations']} x {s['n_bands']} | {' | '.join(vals)} |")
    (OUT/'source-matrix.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    c.save('summary-receipt.json',{'public_files':{p.name:digest(p) for p in OUT.glob('*.json')},'measurement':c.guard()})
    print('COVERAGE',status);print('STRESS',len(stressrows));print(c.guard())

if __name__=='__main__':main()
