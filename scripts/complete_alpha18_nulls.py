"""Complete the feature-free baseline where nonfinite X blocked both models."""
from alpha18_common import Context,read
from nirs4all_domains.full_bank import target_values,folds_for,scores
from nirs4all_domains.predictive import native_summary
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import digest,fingerprint


def main():
    c=Context();f=c.load('campaign-freeze.json');f['scopes'].update(c.load('scope-marker-continuation.json')['scopes'])
    history=c.load('historical-retained-continuation.json');f['scopes'].update(history['scopes'])
    tasks={t['task_id']:t for t in f['tasks']};entries={e['dataset_id']:e for e in f['entries']}
    candidates=[]
    for ref in c.load('reference-progress.json'):
        if not ref.get('artifact_path'):continue
        v=read(ref['artifact_path'])
        if v['result']['reason']=='ValueError:REQUIRED_X_NUMERIC_VALUES_INVALID':candidates.append(tasks[v['task_id']])
    # Bound this feature-free continuation inside the initial reference envelope.
    assert len(candidates)<=416
    value={'controller_sha256':digest(__file__),'parent_freeze_id':f['freeze_id'],
           'tasks':[t['task_id'] for t in candidates],'model_fits':0,'ceiling_increase':0,
           'reservation_upper_bytes':len(candidates)*131072,
           'scope':'Same original development identities, folds and training-mean rule. No X imputation/model or retained target access.'}
    name='target-only-null-freeze.json'
    if (c.root/name).exists():assert c.load(name)==value
    else:c.save(name,value)
    progress=c.load('null-progress.json') if (c.root/'null-progress.json').exists() else []
    previous={r['task_id'] for r in progress}
    for t in candidates:
        if t['task_id'] in previous:continue
        if len(progress)%32==0:c.guard(32*131072)
        assert t['view_id'] not in history['blocked_sources']
        entry=entries[t['dataset_id']];scope=f['scopes'][t['view_id']]
        assert digest(entry['target_path'])==entry['target_sha256']
        def compute(folder):
            try:
                y,missing=target_values(entry,t['target'],scope);folds=folds_for(sorted(y),scope,t['task_id'])
                index={s:i for i,s in enumerate(scope['observation_ids'])};yy=[];pred=[]
                for fold in folds['folds']:
                    train=[index[s] for s in fold['train_sample_ids']];ev=[index[s] for s in fold['validation_sample_ids']]
                    mean=native_summary([y[i] for i in train])['mean'];yy.extend(y[i] for i in ev);pred.extend([mean]*len(ev))
                result=state({'scores':scores(yy,pred,pred),'n_evaluated':len(yy),'n_missing_target':missing,
                              'fold_fingerprint':fingerprint(folds)})
            except Exception as error:result=state(reason=type(error).__name__+':'+str(error),status='failed')
            return {'task_id':t['task_id'],'view_id':t['view_id'],'result':result,'retained_target_decoded':False,'model_fits':0}
        contract={'task':{'task_id':t['task_id']},'protocol':'domains.bank_reference_null_completion.v0.1','freeze_id':fingerprint(value)}
        receipt,result=c.scheduler.run(contract,'P4',{'inputs':[],'scratch_bytes':65536,'evidence_bytes':65536,'expected_fits':0,'expected_permutations':0,'uncertainty':'Feature-free native training mean/metrics under unchanged folds.'},compute)
        assert result is not None
        path=c.scheduler.evidence/receipt['artifact'];progress.append({'task_id':t['task_id'],'artifact_path':str(path),'artifact_sha256':digest(path)})
        c.save('null-progress.json',progress)
    print('NULL_COMPLETION_TASKS',len(progress));print(c.guard())

if __name__=='__main__':main()
