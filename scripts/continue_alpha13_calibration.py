"""Exact scientific lineage across a qualified execution-transport change."""
import json
from pathlib import Path
from alpha13_common import ROOT,PUBLIC,STATE,policy,run as current_run
import run_alpha13_calibration as controller
from nirs4all_domains.native_profile_stream import NativeProfileStream
from nirs4all_domains.storage import StageStore,atomic_json,digest,fingerprint


def main():
    proof=json.loads((PUBLIC/'native-stream-parity.json').read_text());assert proof['all_exact']
    old=Path('target/debug/n4domains.exe').resolve();new=Path('target/qualification/n4domains.exe').resolve()
    from n4m._ffi import library_path
    library=Path(library_path()).resolve();p=proof['contract']
    assert digest(old)==p['old_binary_sha256'] and digest(new)==p['new_binary_sha256'] and digest(library)==p['library_sha256']
    assert digest('crates/nirs4all-domains/src/unsupervised.rs')==p['native_characterization_source_sha256']
    assert digest('crates/nirs4all-domains/src/methods.rs')==p['native_adapter_source_sha256']
    assert digest('bridges/python/nirs4all_domains/native_profile_stream.py')==p['stream_bridge_sha256']
    stop=json.loads((ROOT/'transport-boundary-stop.json').read_text());assert not stop['native_fit_canceled'] and not stop['active_native_children'] and not stop['running_scientific_stages']
    extra={'execution_transport':'domains.native_profile_stream.v0.1','stream_bridge_sha256':p['stream_bridge_sha256'],
        'continuation_wrapper_sha256':digest(__file__),'qualified_transport_parity_sha256':digest(PUBLIC/'native-stream-parity.json')}
    legacy=[];journal=json.loads((STATE/'journal.json').read_text())
    for record in journal['runs'].values():
        c=record['contract']
        if c.get('freeze_id')==stop['freeze_id'] and c.get('binary_sha256')==p['old_binary_sha256'] and record['status']=='computed':
            assert c['runner_sha256']==digest('scripts/run_alpha13_calibration.py')
            legacy.append(record)
    reused=[]
    def runtime():
        _,_,base=original_runtime();return new,library,{**base,'binary_sha256':digest(new),**extra}
    def compatible_run(contract,stage,plan,callback):
        historical={k:v for k,v in contract.items() if k not in extra}
        if 'binary_sha256' in historical:historical['binary_sha256']=p['old_binary_sha256']
        candidates=[r for r in legacy if r['stage']==stage and r['contract']==historical]
        if candidates:
            assert len(candidates)==1;r=candidates[0]
            store=StageStore(STATE,ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy());artifact=store.evidence/r['artifact']
            assert digest(artifact)==r['sha256'];value=json.loads(artifact.read_text())
            reused.append({'execution_id':r['execution_id'],'stage':stage,'sha256':r['sha256'],'old_binary_sha256':p['old_binary_sha256'],
                'new_execution_contract_sha256':fingerprint(contract),'basis':'Exact scientific contract plus qualified numeric transport parity; original artifact remains attributed to original binary.'})
            return store,{**r,'cache_hit':True},value
        return current_run(contract,stage,plan,callback)
    original_runtime=controller.native_runtime;controller.native_runtime=runtime;controller.run=compatible_run
    with NativeProfileStream(new,library) as stream:
        controller.native_profile=stream.profile;controller.main()
    atomic_json(ROOT/'calibration-transport-reuse.json',{'qualified_parity_sha256':digest(PUBLIC/'native-stream-parity.json'),
        'reused_exact_parent_stages':reused,'remaining_execution_transport':extra,'native_fit_canceled':False})
    print(json.dumps({'exact_parent_stages_reused':len(reused),'remaining_calibration_completed':True}))


if __name__=='__main__':main()
