"""Whole declared-plot CV and common-observation comparisons via native APIs."""
import os
import time
from alpha18_common import Context,read
from alpha18_memory import peak_memory
from nirs4all_domains.full_bank import matrix_request,target_values,reference_task,scores
from nirs4all_domains.predictive import group_folds,native_summary
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import digest,fingerprint
from nirs4all_domains.synthesis import validate_states


def main():
    c=Context();f=c.load('campaign-freeze.json');selection=c.load('group-sensitivity-freeze-v2.json')
    binding=c.load('group-explicit-fold-code-continuation.json')
    assert digest('bridges/python/nirs4all_domains/full_bank.py')==binding['current_core_sha256']
    execution={'selection_id':selection['freeze_id'],'code_continuation_id':binding['continuation_id'],
               'controller_sha256':digest(__file__),'plan_sha256':digest('docs/ALPHA18_GROUP_SENSITIVITY_PLAN.md')}
    name='group-sensitivity-execution-freeze.json'
    if (c.root/name).exists():assert c.load(name)==execution
    else:c.save(name,execution)
    refs={r['task_id']:r for r in c.load('reference-progress.json')}
    progress=c.load('group-sensitivity-progress.json') if (c.root/'group-sensitivity-progress.json').exists() else []
    done={r['task_id'] for r in progress}
    for p in selection['plans']:
        if p['task_id'] in done:continue
        c.guard(524288);task=next(t for t in f['tasks'] if t['task_id']==p['task_id']);scope=selection['scopes'][p['view_id']]
        entry=next(e for e in f['entries'] if e['dataset_id']==task['dataset_id']);source=next(s for s in f['sources'] if s['view_id']==p['view_id'])
        assert digest(source['matrix'])==source['input_sha256'] and digest(entry['target_path'])==entry['target_sha256'] and digest(entry['metadata_path'])==entry['metadata_sha256']
        contract={'task':{'task_id':task['task_id']},'protocol':selection['protocol'],'execution':execution}
        def compute(folder):
            start=time.monotonic()
            try:
                x=matrix_request(source)[0]['spectra'];y,missing=target_values(entry,task['target'],scope)
                ng=len({scope['groups'][i] for i in y})
                if ng<2:raise ValueError('FEWER_THAN_TWO_DECLARED_PLOT_COMPONENTS')
                foldrows=[{'physical_sample_id':scope['observation_ids'][i],'independence_group':scope['groups'][i]} for i in sorted(y)]
                folds=group_folds(foldrows,min(3,ng),18,'plot-sensitivity:'+task['task_id'])
                result=reference_task(x,y,scope,task,folds=folds)
                parent_ref=refs.get(task['task_id']);old=None
                if parent_ref and parent_ref.get('artifact_path'):
                    assert digest(parent_ref['artifact_path'])==parent_ref['artifact_sha256'];old=read(parent_ref['artifact_path'])
                comparisons={}
                for family,grouped in result['families'].items():
                    baseline=old.get('families',{}).get(family,{}) if old else {}
                    if grouped['pooled']['status']!='computed' or baseline.get('pooled',{}).get('status')!='computed':
                        comparisons[family]=state(reason='COMPLETE_PRIMARY_AND_GROUPED_OOF_PAIR_UNAVAILABLE');continue
                    prior={r[0]:r[1] for r in baseline['oof']};current={r[0]:r[1] for r in grouped['oof']}
                    common=sorted(set(prior)&set(current)&set(y))
                    if set(common)!=set(y):raise ValueError('GROUPED_COMPARISON_EVALUATION_COVERAGE_MISMATCH')
                    # The grouped null is a common denominator; raw RMSEs stay
                    # in the one target's units. Training sets are not size matched.
                    n_byid={v:i for i,v in enumerate(scope['observation_ids'])};null={}
                    for fold in folds['folds']:
                        mean=native_summary([y[n_byid[v]] for v in fold['train_sample_ids']])['mean']
                        for v in fold['validation_sample_ids']:null[n_byid[v]]=mean
                    yy=[y[i] for i in common];nn=[null[i] for i in common]
                    a=scores(yy,[prior[i] for i in common],nn);b=scores(yy,[current[i] for i in common],nn)
                    delta=b['rmse']['value']-a['rmse']['value'];den=b['null_rmse']['value']
                    comparisons[family]=state({'n_common_evaluation':len(common),'primary_within_context':a,'declared_plot_CV':b,
                        'D_RMSE':delta,'D_skill':state(delta/den) if den>0 else state(reason='ZERO_GROUPED_NULL_DENOMINATOR'),
                        'interpretation':'Common evaluation observations; different training composition/size and one fixed allocation. Not a pure grouping causal effect or biological independence.'})
                for model in result['families'].values():model['oof']=[[i,p] for i,p,_ in model['oof']]
                v={'result':state({'grouped_reference':result,'paired_comparison':comparisons,'n_outer_folds':len(folds['folds']),'n_missing_target':missing}),
                   'model_fit_attempts':result['model_fit_attempts'],'model_fit_successes':result['model_fit_successes']}
            except Exception as error:v={'result':state(reason=type(error).__name__+':'+str(error),status='failed'),'model_fit_attempts':0,'model_fit_successes':0}
            v.update(task_id=task['task_id'],view_id=p['view_id'],target=task['target'],unit=task['unit'],
                     wall_seconds=time.monotonic()-start,peak_resident_bytes=peak_memory(),retained_target_decoded=False,
                     biological_independence_verified=False,plot_fields=p['plot_fields'])
            validate_states(v);return v
        receipt,value=c.scheduler.run(contract,'P3',{'inputs':[],'scratch_bytes':262144,'evidence_bytes':262144,'expected_fits':6,'expected_permutations':0,'uncertainty':'Up to three folds; six fixed native fits and matched-evaluation OOF scoring.'},compute)
        assert value is not None
        path=c.scheduler.evidence/receipt['artifact'];progress.append({'task_id':task['task_id'],'artifact_path':str(path),'artifact_sha256':digest(path)});c.save('group-sensitivity-progress.json',progress)
        print(task['dataset_id'],value['result']['status'],flush=True)
    print(c.guard())

if __name__=='__main__':main()
