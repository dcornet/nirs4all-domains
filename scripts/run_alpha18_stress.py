"""Frozen matched-context task transport; all models/PCA/scores are native."""
import os
import argparse
from pathlib import Path
import time
import threading
import numpy as np
from alpha18_common import Context,read
from alpha18_memory import peak_memory
from nirs4all_domains.full_bank import matrix_request,target_values,fit_predict,scores
from nirs4all_domains.predictive import native_summary
from nirs4all_domains.dependence import state
from nirs4all_domains.size_match import exact_training_subset
from nirs4all_domains.storage import digest,fingerprint
from nirs4all_domains.synthesis import validate_states
from nirs4all_domains.unsupervised import represent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--representation',choices=['raw','snv'],default='raw');args=parser.parse_args()
    representation=args.representation
    os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
    c=Context();f=c.load('campaign-freeze.json');sf=c.load('stress-freeze-v3.json')
    f['scopes'].update(c.load('historical-retained-continuation.json')['scopes'])
    f['scopes'].update(c.load('group-sensitivity-freeze-v2.json')['scopes'])
    previous=sum(r['wall_seconds'] for name in ['X-worker-observations.json','reference-worker-observations.json'] if (c.root/name).exists() for r in c.load(name))
    for name in ['stress-progress.json','SNV-stress-progress.json']:
        if (c.root/name).exists():previous+=sum(read(r['artifact_path'])['wall_seconds'] for r in c.load(name))
    deadline=time.monotonic()+max(0,28800-previous)
    def watchdog():
        while True:
            if time.monotonic()>deadline or peak_memory()>2147483648:os._exit(86)
            time.sleep(.1)
    threading.Thread(target=watchdog,daemon=True).start()
    extension=c.load('SNV-stress-extension-freeze-v2.json')
    memory=c.load('memory-watchdog-continuation.json')
    assert digest(__file__)==memory['current_stress_controller_sha256'] and extension['controller_sha256']==memory['prior_stress_controller_sha256']
    execution={'selection_id':sf['freeze_id'],'controller_sha256':digest(__file__), 'representation':representation,
               'extension_id':extension['extension_id'],
               'memory_monitor_sha256':memory['memory_monitor_sha256'],
               'estimands_sha256':digest('docs/ALPHA18_STRESS_ESTIMANDS.md'),
               'descriptor_freeze_id':c.load('X-descriptor-freeze.json')['descriptor_freeze_id']}
    name='stress-execution-freeze.json' if representation=='raw' else 'SNV-stress-execution-freeze.json'
    if (c.root/name).exists():assert c.load(name)==execution
    else:c.save(name,execution)
    progress_name='stress-progress.json' if representation=='raw' else 'SNV-stress-progress.json'
    progress=c.load(progress_name) if (c.root/progress_name).exists() else []
    done={r['task_id'] for r in progress}
    for plan in sf['plans']:
        if plan['task_id'] in done:continue
        c.guard(1048576);task=next(t for t in f['tasks'] if t['task_id']==plan['task_id'])
        source=next(s for s in f['sources'] if s['view_id']==plan['view_id']);entry=next(e for e in f['entries'] if e['dataset_id']==task['dataset_id'])
        scope=f['scopes'][plan['view_id']]
        assert all(digest(path)==sha for path,sha in [(source['matrix'],source['input_sha256']),(entry['target_path'],entry['target_sha256']),(entry['metadata_path'],entry['metadata_sha256'])])
        contract={'task':{'task_id':task['task_id']+':matched-stress'},'protocol':'domains.bank_stress.v0.1' if representation=='raw' else 'domains.bank_stress_snv.v0.1',
                  'execution':execution,'selected_plan_id':fingerprint(plan)}
        old=read(c.scheduler.root/'journal.json')['runs'].get(fingerprint(contract)+':P3')
        assert not old or old['status']=='computed','NO_AUTOMATIC_RETRY'
        def compute(folder):
            start=time.monotonic();attempts=0;successes=0;pcas=0
            try:
                from n4m.roles import FlexiblePCA
                request,axis=matrix_request(source);request=represent(request,representation);x=request['spectra'];y,missing=target_values(entry,task['target'],scope)
                ev=[i for i in plan['evaluation_indices'] if i in y]
                full=[i for i in plan['full_training_indices'] if i in y]
                stress=[i for i in plan['stress_training_indices'] if i in y]
                if min(len(ev),len(stress))<6:raise ValueError('INSUFFICIENT_AVAILABLE_CASE_STRESS_SUPPORT')
                allrows=[{'physical_sample_id':scope['observation_ids'][i],'independence_group':scope['groups'][i]} for i in sorted(y)]
                chosen=exact_training_subset(allrows,[scope['observation_ids'][i] for i in full],len(stress),scope='alpha18:'+task['task_id'])
                if chosen is None:raise ValueError('WHOLE_COMPONENT_SIZE_CONTROL_UNAVAILABLE')
                index={v:i for i,v in enumerate(scope['observation_ids'])};control=[index[v] for v in chosen]
                if not set(control)-set(stress):raise ValueError('MATCHED_CONTROL_HAS_NO_EVALUATION_CONTEXT_SUPPORT')
                trainsets={'full_reference':full,'size_control':control,'context_excluded':stress}
                evalgroups={scope['groups'][i] for i in ev}
                if any(evalgroups & {scope['groups'][i] for i in ii} for ii in trainsets.values()):raise ValueError('STRESS_COMPONENT_CONTAMINATION')
                components=min(3,len(x[0]),min(map(len,trainsets.values()))-1)
                common_mean=native_summary([y[i] for i in control])['mean'];common_null=[common_mean]*len(ev)
                regimes={}
                for label,train in trainsets.items():
                    ts=native_summary([y[i] for i in train]);models={}
                    pca=FlexiblePCA(n_components=1);pca.fit(np.asarray([x[i] for i in train],dtype=np.float64));pcas+=1
                    pc_train=pca.transform(np.asarray([x[i] for i in train],dtype=np.float64))[:,0].tolist()
                    pc_eval=pca.transform(np.asarray([x[i] for i in ev],dtype=np.float64))[:,0].tolist()
                    ss=native_summary(pc_train)
                    for family in ['pls','ridge']:
                        attempts+=1
                        try:
                            pred=fit_predict(x,y,train,ev,family,components);successes+=1
                            models[family]=state({'own_null_scores':scores([y[i] for i in ev],pred,[ts['mean']]*len(ev)),
                                'common_null_scores':scores([y[i] for i in ev],pred,common_null)})
                        except Exception as error:models[family]=state(reason=type(error).__name__,status='failed')
                    regimes[label]={'n_train':len(train),'n_train_groups':len({scope['groups'][i] for i in train}),
                        'training_target_summary':ts,'target_outside_train_range':sum(y[i]<ts['min'] or y[i]>ts['max'] for i in ev),
                        'PC1_train_summary':ss,'PC1_evaluation_summary':native_summary(pc_eval),
                        'PC1_outside_train_range_fraction':sum(v<ss['min'] or v>ss['max'] for v in pc_eval)/len(ev),'models':models}
                deterioration={}
                for family in ['pls','ridge']:
                    a=regimes['size_control']['models'][family];b=regimes['context_excluded']['models'][family]
                    if a['status']==b['status']=='computed':
                        aa=a['value']['common_null_scores'];bb=b['value']['common_null_scores'];delta=bb['rmse']['value']-aa['rmse']['value'];null=aa['null_rmse']['value']
                        deterioration[family]=state({'D_RMSE':delta,'D_skill':state(delta/null) if null>0 else state(reason='ZERO_COMMON_NULL_RMSE')})
                    else:deterioration[family]=state(reason='MATCHED_MODEL_PAIR_INCOMPLETE')
                result=state({'factor':plan['factor'],'n_context_levels':plan['n_context_levels'],
                    'n_evaluation':len(ev),'n_evaluation_groups':len(evalgroups),'evaluation_target_summary':native_summary([y[i] for i in ev]),
                    'n_missing_target':missing,'matched_evaluation':True,'matched_training_size':len(control)==len(stress),
                    'regimes':regimes,'deterioration':deterioration,
                    'interpretation':'Declared-context exploratory stress with a matched-size control; not causal shortcut evidence or independent study confirmation.'})
            except Exception as error:result=state(reason=type(error).__name__+':'+str(error),status='failed')
            populations={k:fingerprint(v) for k,v in {'evaluation':ev,'full_training':full,'size_control_training':control,'stress_training':stress}.items()} if result['status']=='computed' else None
            v={'task_id':task['task_id'],'view_id':plan['view_id'],'target':task['target'],'unit':task['unit'],'result':result,
               'representation':representation,'population_fingerprints':populations,
               'model_fit_attempts':attempts,'model_fit_successes':successes,'train_only_PCA_fits':pcas,
               'retained_target_decoded':False,'independent_generalization':False,
               'wall_seconds':time.monotonic()-start,'peak_resident_bytes':peak_memory()}
            validate_states(v);return v
        receipt,value=c.scheduler.run(contract,'P3',{'inputs':[],'scratch_bytes':524288,'evidence_bytes':524288,'expected_fits':9,'expected_permutations':0,'uncertainty':'Six model fits, three train-only diagnostic PCAs, frozen paired evaluation.'},compute)
        assert value is not None
        artifact=c.scheduler.evidence/receipt['artifact'];progress.append({'task_id':task['task_id'],'artifact_path':str(artifact),'artifact_sha256':digest(artifact)})
        c.save(progress_name,progress);print(task['dataset_id'],representation,value['result']['status'],flush=True)
    print(c.guard())

if __name__=='__main__':main()
