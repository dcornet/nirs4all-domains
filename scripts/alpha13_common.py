"""Existing serial StageStore with a bounded alpha.13 sub-envelope."""
import json
import os
from pathlib import Path
from nirs4all_domains.storage import StageStore,atomic_json,digest,fingerprint

ROOT=Path('.audit/alpha13');PUBLIC=Path('docs/benchmarks/alpha13')
STATE=Path('results/alpha9-perten-keyed/state')
INITIAL_RESERVED=427393916
NEW_RESERVATION_LIMIT=96*1024*1024


def policy():
    path=Path('configs/bank/storage-policy-alpha13.json')
    value=json.loads((path if path.exists() else Path('configs/bank/storage-policy-alpha12.json')).read_text())
    if value['workspace_max_bytes']>13873678017:
        approval=json.loads((ROOT/'budget-approval.json').read_text())
        assert approval['workspace_ceiling']==value['workspace_max_bytes']
    return value


def run(contract,stage,plan,callback):
    journal=json.loads((STATE/'journal.json').read_text())
    reserve=plan['scratch_bytes']+plan['evidence_bytes']+sum(i['bytes'] for i in plan['inputs'] if not i.get('path') or not Path(i['path']).exists())
    old=journal['runs'].get(fingerprint(contract)+':'+stage)
    if not (old and old['status']=='computed') and journal['reserved_campaign_bytes']-INITIAL_RESERVED+reserve>NEW_RESERVATION_LIMIT:
        raise ValueError('ALPHA13_ADDITIONAL_RESERVATION_ENVELOPE_EXCEEDED')
    store=StageStore(STATE,ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy())
    receipt,value=store.run(contract,stage,plan,callback)
    if value is None:raise RuntimeError(json.dumps(receipt))
    return store,receipt,value


def publish(store,receipt,name):
    origin=store.evidence/receipt['artifact'];destination=PUBLIC/name
    assert destination.resolve().is_relative_to(PUBLIC.resolve()) and digest(origin)==receipt['sha256']
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        if digest(destination)!=receipt['sha256']:raise ValueError('EXISTING_ALPHA13_EVIDENCE_CHANGED')
        return
    temporary=destination.with_name(destination.name+'.shared')
    if temporary.exists():
        if digest(temporary)!=receipt['sha256']:raise ValueError('INTERRUPTED_ALPHA13_EXPORT_CHANGED')
    else:os.link(origin,temporary)
    os.replace(temporary,destination)


def native_runtime():
    from n4m._ffi import library_path
    binary=Path('target/debug/n4domains.exe').resolve();library=Path(library_path()).resolve()
    return binary,library,{'binary_sha256':digest(binary),'library_sha256':digest(library),
        'geometry_bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py'),
        'power_bridge_sha256':digest('bridges/python/nirs4all_domains/stability_power.py')}
