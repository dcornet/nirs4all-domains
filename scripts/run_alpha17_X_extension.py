"""Execute only the approved eight-view freeze with existing native X APIs."""
from collections import Counter
import copy
import json
import os
from pathlib import Path
import subprocess
import threading
import time

from alpha17_common import Context, read
from measure_alpha12_phase import windows_peak
from run_alpha10_multifamily import peak_memory
from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.dependence import state
from nirs4all_domains.native_profile_stream import NativeProfileStream
from nirs4all_domains.storage import atomic_json, digest, fingerprint
from nirs4all_domains.synthesis import describe, validate_states
from nirs4all_domains.unsupervised import (compact_profile, compare_partition,
    neighborhood_agreement, query_design, represent)


def main():
    c=Context();proposal=c.load('NEXT_X_CAMPAIGN_PLAN_v3.json')
    assert proposal['plan_id']==c.extension['X_plan_id'] and proposal['revision']==3
    assert len(proposal['sources'])==8 and all(s['previous_execution_status']=='not_executed' for s in proposal['sources'])
    paths=[s['matrix'] for s in proposal['sources']]
    c.guard(paths=paths)
    c.save('candidate-inputs.json',sorted(set(c.load('candidate-inputs.json'))|set(paths)))
    from n4m._ffi import library_path
    import n4m
    binary=Path('.audit/alpha13/executed-alpha13-cli.exe');library=Path(library_path()).resolve()
    # Same dependency directory as the installed wheel's delvewheel patch.
    # This affects this controller/its children only, never the global PATH.
    dependencies=Path(n4m.__file__).parent.parent/'nirs4all_methods.libs'
    os.environ['PATH']=str(dependencies)+os.pathsep+os.environ['PATH']
    startup=subprocess.run([str(binary),'x-profile-stream','--methods-library',str(library)],
        input='',capture_output=True,text=True,timeout=30)
    assert startup.returncode==0, 'NATIVE_STARTUP_PREFLIGHT_FAILED_BEFORE_RESERVATION'
    assert digest(binary)=='0edf388a0e7facfad2d19a426938b56b2675a5c1b2bb822b8570fe48cba2e3c2'
    assert digest(library)=='096bae41ffc5e4f6ec8d73b0ca43f0cec83f66dda806b2d43b2d893ba07db164'
    frozen_name='approved-X-execution-freeze.json'
    if (c.root/frozen_name).exists():
        freeze=c.load(frozen_name)
        assert freeze['controller_sha256']==digest('.audit/alpha17/X-controller-first.py'), 'INITIAL_CONTROLLER_ARCHIVE_CHANGED'
    else:
        sources=copy.deepcopy(proposal['sources'])
        for s in sources:
            path=Path(s['matrix'])
            assert (path.stat().st_size,path.stat().st_mtime_ns)==(s['matrix_bytes'],s['mtime_ns']), 'SOURCE_CHANGED_SINCE_APPROVED_PLAN'
            s['sha256']=digest(path)
        freeze={'plan_id':proposal['plan_id'],'sources':sources,'controller_sha256':digest(__file__),
            'binary_sha256':digest(binary),'library_sha256':digest(library),
            'baseline_combined_bytes':c.guard()['combined_bytes'],
            'bridge_sha256':{n:digest(Path('bridges/python/nirs4all_domains')/n) for n in
                ['adaptive.py','native_profile_stream.py','unsupervised.py','synthesis.py']},
            'target_accessed':False,'supervised_fits':0}
        freeze['freeze_id']=fingerprint(freeze);c.save(frozen_name,freeze)
    assert all(digest(Path('bridges/python/nirs4all_domains')/n)==sha for n,sha in freeze['bridge_sha256'].items())
    continuation={'original_freeze_id':freeze['freeze_id'],'controller_sha256':digest(__file__),
        'dependency_sha256':{p.name:digest(p) for p in dependencies.glob('*.dll')},
        'cause':'Missing repaired-wheel DLL search directory in the CLI child environment.',
        'completed_attempts_not_retried':True,'numerical_protocol_changed':False}
    continuation_name='X-transport-continuation-freeze.json'
    if (c.root/continuation_name).exists():assert c.load(continuation_name)==continuation
    else:c.save(continuation_name,continuation)
    reports=c.load('X-extension-progress.json') if (c.root/'X-extension-progress.json').exists() else []
    previous={r['view_id']:r for r in reports}
    previous_seconds=sum(read(r['artifact_path'])['wall_seconds'] for r in reports)
    started=time.monotonic();deadline=started+max(0,7200-previous_seconds)
    for s in freeze['sources']:
        if s['view_id'] in previous:
            assert digest(previous[s['view_id']]['artifact_path'])==previous[s['view_id']]['artifact_sha256']
            continue
        assert digest(s['matrix'])==s['sha256'], 'FROZEN_SOURCE_CHANGED'
        c.guard(2097152)
        assert c.guard()['combined_bytes']+2097152<=freeze['baseline_combined_bytes']+134217728
        contract={'task':{'task_id':c.store.authenticate(['alpha17-X-v3',s['view_id']])},
            'protocol':'domains.unsupervised.v0.1','visibility':'local_private',
            'frozen_source_receipt':c.store.authenticate([s,freeze['freeze_id']]),
            'transport_continuation_receipt':c.store.authenticate(continuation)}
        old=read(c.scheduler.root/'journal.json')['runs'].get(fingerprint(contract)+':P2')
        assert not old or old['status']=='computed', 'FAILED_OR_PARTIAL_STAGE_REQUIRES_SEPARATE_RETRY_APPROVAL'
        plan={'inputs':[],'scratch_bytes':1048576,'evidence_bytes':1048576,
            'expected_fits':6,'expected_permutations':0,
            'uncertainty':'Two PCA requests, at most four HDBSCAN attempts; original native query policy. No Y.'}
        def compute(folder):
            task_started=time.monotonic()
            profiles={};requests=0;resource_fault=[];peaks={'python':peak_memory(),'native':0}
            stream=None;done=threading.Event()
            def limits():
                peaks['python']=max(peaks['python'],peak_memory())
                if peaks['python']+peaks['native']>1073741824:raise RuntimeError('RAM_STOP')
                if time.monotonic()>deadline:raise RuntimeError('CAMPAIGN_WALL_STOP')
            try:
                limits();raw=spectral_request(s['matrix'],s['view_id'].split('/')[-1])
                raw['axis_unit']=s['axis_unit']
                assert (len(raw['observation_ids']),len(raw['axis']))==(s['n_observations'],s['n_bands']), 'FULL_SOURCE_SHAPE_MISMATCH'
                design=query_design(raw['observation_ids'],len(raw['axis']))
                assert design['n_query']==s['planned_queries']
                limits()
                with NativeProfileStream(binary,library) as stream:
                    def watch():
                        while not done.wait(.1):
                            peaks['native']=max(peaks['native'],windows_peak(stream.process))
                            if peaks['python']+peaks['native']>1073741824 or time.monotonic()>deadline:
                                resource_fault.append('RAM_OR_CAMPAIGN_WALL_STOP');stream.process.kill();return
                    monitor=threading.Thread(target=watch,daemon=True);monitor.start()
                    try:
                        for rep in ['raw','snv']:
                            limits();represented=represent(raw,rep);limits();requests+=1
                            profiles[rep]=compact_profile(stream.profile(represented,rep,design=design),design)
                            del represented
                            peaks['native']=max(peaks['native'],windows_peak(stream.process));limits()
                    finally:
                        done.set();monitor.join(timeout=2)
                assert not resource_fault
                ids=raw['observation_ids'];parts=[]
                for i in range(2):
                    a,b=[profiles[r]['cluster_settings'][i] for r in ['raw','snv']]
                    parts.append(compare_partition(ids,a['value']['labels'],ids,b['value']['labels'])
                        if a['status']==b['status']=='computed' else state(reason='PARTITION_UNAVAILABLE'))
                agreement=state({'partitions':parts,'full_axis_neighbors':neighborhood_agreement(
                    profiles['raw']['neighborhoods']['value']['full_axis'],profiles['snv']['neighborhoods']['value']['full_axis'])})
                rows=[describe(s['view_id'],rep,profiles[rep],agreement,family=s['family'],modality='NIR') for rep in ['raw','snv']]
                result={'result':state(rows),'observation_ids':ids,'query_design':design,
                    'profile_fingerprints':{rep:fingerprint(p) for rep,p in profiles.items()},
                    'native_cluster_states':{rep:[{'status':v['status'],'reason':v['reason']} for v in p['cluster_settings']] for rep,p in profiles.items()}}
            except Exception as error:
                # Detailed original exception stays local; failed views are not substituted.
                result={'result':state(reason=type(error).__name__+':'+str(error),status='failed'),
                    'partial_rows':[describe(s['view_id'],rep,p,state(reason='PAIRED_REPRESENTATION_INCOMPLETE'),family=s['family'],modality='NIR') for rep,p in profiles.items()]}
            result.update(view_id=s['view_id'],native_PCA_requests=requests,
                completed_PCA_profiles=len(profiles),conditional_HDBSCAN_attempt_upper=requests*2,
                target_accessed=False,supervised_fits=0,B60_refits=0,
                peak_bytes=peaks,resource_fault=resource_fault,wall_seconds=time.monotonic()-task_started,
                scope='All source observations/axes retained; observation-conditional, not biological independence.')
            c.guard();return result
        receipt,value=c.scheduler.run(contract,'P2',plan,compute)
        assert value is not None, 'STAGE_NOT_COMPUTED_NO_AUTOMATIC_RETRY'
        artifact=c.scheduler.evidence/receipt['artifact']
        reports.append({'view_id':s['view_id'],'artifact_path':str(artifact),'artifact_sha256':digest(artifact),'receipt':receipt})
        c.save('X-extension-progress.json',reports)
        print(json.dumps({'view_id':s['view_id'],'result':value['result']['status'],
            'completed_PCA_profiles':value['completed_PCA_profiles'],'peak_MiB':round(sum(value['peak_bytes'].values())/1048576,2)}),flush=True)
        if value['resource_fault'] or any(v in (value['result'].get('reason') or '') for v in ['RAM_STOP','WALL_STOP']):break
    c.save('X-extension-results.json',{'freeze_id':freeze['freeze_id'],'reports':reports,
        'wall_seconds':previous_seconds+time.monotonic()-started,'expected_views':8})
    c.preservation()
    print('ALPHA17_APPROVED_X_EXTENSION_FINISHED; NO_Y_OR_SUPERVISED_FITS')


if __name__=='__main__':
    try:main()
    except Exception as error:
        try:Context().save('X-extension-controller-failure.json',{'type':type(error).__name__,'detail':str(error)})
        except Exception:pass
        print('ALPHA17_X_EXTENSION_STOPPED; DETAILS_REMAIN_LOCAL');raise SystemExit(2) from None
