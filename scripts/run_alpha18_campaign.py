"""Serial, resumable X/reference workers over the frozen full-bank inventory."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from alpha18_common import Context,read
from measure_alpha12_phase import windows_peak
from run_alpha10_multifamily import peak_memory
from nirs4all_domains.dependence import state
from nirs4all_domains.full_bank import matrix_request,target_values,reference_task,folds_for,scores
from nirs4all_domains.native_profile_stream import NativeProfileStream
from nirs4all_domains.storage import digest,fingerprint
from nirs4all_domains.synthesis import describe,validate_states
from nirs4all_domains.unsupervised import compact_profile,query_design,represent,compare_partition,neighborhood_agreement


def runtime():
    import n4m
    from n4m._ffi import library_path
    os.environ['PATH']=str(Path(n4m.__file__).parent.parent/'nirs4all_methods.libs')+os.pathsep+os.environ['PATH']
    return Path('.audit/alpha13/executed-alpha13-cli.exe').resolve(),Path(library_path()).resolve()


def worker(c,freeze,source,phase):
    key=source['view_id'];binary,library=runtime();entry=next(e for e in freeze['entries'] if e['dataset_id']==source['dataset_id'])
    assert digest(source['matrix'])==source['input_sha256'],'FROZEN_X_CHANGED'
    if phase=='reference':
        for kind in ['metadata','target']:
            assert digest(entry[kind+'_path'])==entry[kind+'_sha256'],'FROZEN_Y_OR_M_CHANGED'
    x=None
    def execute(task,callback,phase_name,reserve):
        contract={'task':{'task_id':task},'protocol':'domains.bank_'+phase+'.v0.1',
                  'freeze_id':freeze['freeze_id'],'source_sha256':source['input_sha256']}
        stage='P2' if phase=='X' else 'P3';old=read(c.scheduler.root/'journal.json')['runs'].get(fingerprint(contract)+':'+stage)
        if old and old['status']!='computed':return {'task_id':task,'result':state(reason='PREVIOUS_FAILED_ATTEMPT_NOT_RETRIED',status='failed')}
        plan={'inputs':[],'scratch_bytes':reserve//2,'evidence_bytes':reserve//2,
              'expected_fits':6,'expected_permutations':0,'uncertainty':phase_name}
        receipt,value=c.scheduler.run(contract,stage,plan,callback)
        if value is None:return {'task_id':task,'result':state(reason=receipt['reason'],status='failed')}
        path=c.scheduler.evidence/receipt['artifact']
        return {'task_id':task,'artifact_path':str(path),'artifact_sha256':digest(path),'result':value['result'] if phase=='X' else state({'model_fit_attempts':value.get('model_fit_attempts',0)})}
    if phase=='X':
        c.guard(2097152)
        def compute(folder):
            begin=time.monotonic();profiles={};peaks={'python':peak_memory(),'native':0};attempts=0;axis=None;done=threading.Event()
            try:
                raw,axis=matrix_request(source);design=query_design(raw['observation_ids'],len(raw['axis']))
                assert (len(raw['spectra']),len(raw['axis']))==(source['n_observations'],source['n_bands'])
                with NativeProfileStream(binary,library) as stream:
                    def monitor():
                        while not done.wait(.1):
                            peaks['python']=max(peaks['python'],peak_memory());peaks['native']=max(peaks['native'],windows_peak(stream.process))
                            if sum(peaks.values())>2147483648 or time.monotonic()-begin>600:stream.process.kill();return
                    watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
                    try:
                        for rep in ['raw','snv']:
                            attempts+=1;profiles[rep]=compact_profile(stream.profile(represent(raw,rep),rep,design=design),design)
                    finally:done.set();watcher.join(2)
                ids=raw['observation_ids'];parts=[]
                for i in range(2):
                    a,b=[profiles[r]['cluster_settings'][i] for r in ['raw','snv']]
                    parts.append(compare_partition(ids,a['value']['labels'],ids,b['value']['labels']) if a['status']==b['status']=='computed' else state(reason='PARTITION_UNAVAILABLE'))
                agreement=state({'partitions':parts,'full_axis_neighbors':neighborhood_agreement(profiles['raw']['neighborhoods']['value']['full_axis'],profiles['snv']['neighborhoods']['value']['full_axis'])})
                result=state([describe(key,r,profiles[r],agreement,family=source['family'],modality=source['modality']) for r in ['raw','snv']])
            except Exception as error:result=state(reason=type(error).__name__+':'+str(error),status='failed')
            partial_rows=[describe(key,r,p,state(reason='PAIRED_REPRESENTATION_INCOMPLETE'),family=source['family'],modality=source['modality']) for r,p in profiles.items()] if result['status']!='computed' else []
            return {'view_id':key,'result':result,'partial_rows':partial_rows,
                    'profile_fingerprints':{r:fingerprint(p) for r,p in profiles.items()},'axis_contract':axis,
                    'PCA_requests':attempts,'wall_seconds':time.monotonic()-begin,'peak_bytes':peaks,
                    'target_accessed':False,'all_rows_and_columns_retained':True}
        progress=c.load('X-progress.json') if (c.root/'X-progress.json').exists() else []
        if any(p['task_id']==key for p in progress):return
        ref=execute(key,compute,'raw/SNV all rows and bands, old native query protocol',2097152)
        progress.append(ref);c.save('X-progress.json',progress)
        print(json.dumps({'phase':'X','view_id':key,'state':ref['result']['status'],'reason':ref['result']['reason']}),flush=True)
        return
    # The descriptor matrix is frozen before any task target decoding.
    assert (c.root/'X-descriptor-freeze.json').exists()
    scope=freeze['scopes'][key]
    try:
        raw,axis=matrix_request(source);x=raw['spectra']
    except Exception:
        x=None
    progress=c.load('reference-progress.json') if (c.root/'reference-progress.json').exists() else []
    previous={r['task_id'] for r in progress}
    semantics_name='target-semantics-v2.json' if (c.root/'target-semantics-v2.json').exists() else 'target-semantics.json'
    semantics={r['task_id']:r for r in c.load(semantics_name)['records']}
    tasks=[t for t in freeze['tasks'] if t['view_id']==key and t['metadata_eligible'] and not semantics[t['task_id']]['excluded']]
    forbidden={'class_index','class_label','raw_label','species','year','latitude','longitude','lat','lon','replicate','spectralrep','idvar','dimensions','feature_count_per_dimension'}
    for task in tasks:
        if task['task_id'] in previous:continue
        begin=time.monotonic()
        def compute(folder):
            population=state(reason='TARGET_NOT_DECODED')
            try:
                if task['target'].lower() in forbidden:raise ValueError('IDENTIFIER_CATEGORY_OR_EXPERIMENTAL_COUNTER')
                y,missing=target_values(entry,task['target'],scope)
                from nirs4all_domains.predictive import native_summary
                population=state({'n_development':len(scope['development_indices']), 'n_available_target':len(y),
                    'n_missing_target':missing,'n_retained_excluded':scope['n_retained'],
                    'summary':state(native_summary(y.values())) if y else state(reason='NO_AVAILABLE_DEVELOPMENT_TARGET_VALUES')})
                if x is None:raise ValueError('REQUIRED_X_NUMERIC_VALUES_INVALID')
                result=reference_task(x,y,scope,task)
                # The null remains a scientific result even when a model fold
                # fails; compute it independently after model attempts.
                null_y=[];null_p=[];id_index={v:i for i,v in enumerate(scope['observation_ids'])}
                for fold in folds_for(sorted(y),scope,task['task_id'])['folds']:
                    train=[id_index[s] for s in fold['train_sample_ids']]
                    evaluation=[id_index[s] for s in fold['validation_sample_ids']]
                    mean=native_summary([y[i] for i in train])['mean']
                    null_y.extend(y[i] for i in evaluation);null_p.extend([mean]*len(evaluation))
                result['null_baseline']=state(scores(null_y,null_p,null_p))
                # Keep compact keyed OOF without repeated null constants or Y.
                for family in result['families'].values():family['oof']=[[i,p] for i,p,_ in family['oof']]
                result.update(result=state({'reference_complete':all(f['pooled']['status']=='computed' for f in result['families'].values())}),
                              n_missing_target=missing,n_available_components_with_missing_members=len({scope['groups'][i] for i in scope['development_indices'] if i not in y}&{scope['groups'][i] for i in y}))
            except Exception as error:result={'result':state(reason=type(error).__name__+':'+str(error),status='failed'),'model_fit_attempts':0,'model_fit_successes':0}
            result.update(task_id=task['task_id'],view_id=key,target=task['target'],unit=task['unit'],
                wall_seconds=time.monotonic()-begin,peak_resident_bytes=peak_memory(),alignment=scope['alignment'],
                biological_independence_verified=False,retained_target_decoded=False,target_population=population)
            validate_states(result);return result
        if len(progress)%32==0:c.guard(32*524288)
        ref=execute(task['task_id'],compute,'Three folds, two fixed native families, no target selection',524288)
        progress.append(ref);c.save('reference-progress.json',progress)
        print(json.dumps({'phase':'reference','view_id':key,'target':task['target'],'state':ref['result']['status']}),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['X','reference']);p.add_argument('--view');p.add_argument('--smoke-only',action='store_true');a=p.parse_args()
    c=Context();freeze=c.load('campaign-freeze.json')
    if a.phase=='reference':
        freeze['scopes'].update(c.load('scope-marker-continuation.json')['scopes'])
        retained=c.load('historical-retained-continuation.json')
        freeze['scopes'].update(retained['scopes'])
        for key in retained['blocked_sources']:freeze['scopes'].pop(key,None)
    assert all(digest(k)==v for k,v in freeze['controller_sha256'].items()),'FROZEN_PROTOCOL_OR_ADAPTER_CHANGED'
    if a.view:
        worker(c,freeze,next(s for s in freeze['sources'] if s['view_id']==a.view),a.phase);return
    runtime();c.guard();proofname=a.phase+'-execution-controller.json'
    binding={'controller_sha256':digest(__file__),'freeze_id':freeze['freeze_id'],'phase':a.phase}
    if (c.root/proofname).exists():
        original=c.load(proofname)
        if original!=binding:
            continuation=c.load('reference-semantics-continuation.json')
            assert a.phase=='reference' and original['controller_sha256']==continuation['original_controller_sha256'] and binding['controller_sha256']==continuation['current_controller_sha256']
    else:c.save(proofname,binding)
    sources=[s for s in freeze['sources'] if s['X_plan']=='compute'] if a.phase=='X' else [s for s in freeze['sources'] if s['view_id'] in freeze['scopes']]
    if a.phase=='reference':
        # Diverse cheap smoke sources first, frozen before decoding the first Y.
        preferred=['ohpl_beer_nir','ohpl_soil_nir','ucph_tablet_nir','manure21_nir_all_y','ossl_jovic_visnir_soil_all_y']
        sources.sort(key=lambda s:(preferred.index(s['dataset_id']) if s['dataset_id'] in preferred else len(preferred),s['view_id']))
        if a.smoke_only:sources=sources[:5]
    runs=c.load(a.phase+'-worker-observations.json') if (c.root/(a.phase+'-worker-observations.json')).exists() else []
    previous={r['view_id'] for r in runs};wall=sum(r['wall_seconds'] for r in runs)
    other='X' if a.phase=='reference' else 'reference'
    if (c.root/(other+'-worker-observations.json')).exists():wall+=sum(r['wall_seconds'] for r in c.load(other+'-worker-observations.json'))
    for source in sources:
        if source['view_id'] in previous:continue
        if wall>=28800:break
        c.guard(2097152 if a.phase=='X' else 32*524288)
        start=time.monotonic();peak=0;fault=None
        log=c.root/(a.phase+'-'+fingerprint(source['view_id'])[:16]+'.log')
        env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        with log.open('w',encoding='utf-8') as out:
            command=[sys.executable,str(Path(__file__).resolve()),a.phase,'--view',source['view_id']]
            if a.phase=='reference':command=[sys.executable,'scripts/alpha18_worker_entry.py',*command[1:]]
            child=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            max_seconds=620 if a.phase=='X' else 180*sum(t['metadata_eligible'] and t['view_id']==source['view_id'] for t in freeze['tasks'])+120
            while child.poll() is None:
                peak=max(peak,windows_peak(child))
                if peak>2147483648 or time.monotonic()-start>min(max_seconds,28800-wall):fault='RAM_OR_WALL_LIMIT';child.kill();break
                time.sleep(.25)
            child.wait()
        elapsed=time.monotonic()-start;wall+=elapsed
        runs.append({'view_id':source['view_id'],'exit_code':child.returncode,'resource_fault':fault,'wall_seconds':elapsed,'observed_launcher_peak_bytes':peak,'log_sha256':digest(log)})
        c.save(a.phase+'-worker-observations.json',runs)
        print(json.dumps({k:runs[-1][k] for k in ['view_id','exit_code','resource_fault','wall_seconds']}),flush=True)
    if a.phase=='X':
        rows=[]
        for s in freeze['sources']:
            if s['reused_exact_profile']:rows.extend(s['rows'])
        for ref in c.load('X-progress.json'):
            if ref.get('artifact_path'):
                value=read(ref['artifact_path'])
                if value['result']['status']=='computed':rows.extend(value['result']['value'])
        matrix={'freeze_id':freeze['freeze_id'],'rows':rows,'row_fingerprints':{r['view_id']+':'+r['representation']:fingerprint(r) for r in rows},'target_accessed':False}
        matrix['descriptor_freeze_id']=fingerprint(matrix)
        if (c.root/'X-descriptor-freeze.json').exists():assert c.load('X-descriptor-freeze.json')==matrix
        else:c.save('X-descriptor-freeze.json',matrix)
    print(c.guard())

if __name__=='__main__':main()
