"""Execute frozen, rights-admitted private raw/SNV profiles locally. No upload."""
import hmac
import json
from pathlib import Path
import time

from nirs4all_domains.privacy import PrivateStore,PrivacyError,fail
from nirs4all_domains.private_batch import PrivateBatch
from nirs4all_domains.storage import atomic_json,digest


def main():
    config=json.loads(Path('.audit/alpha14/private-root.json').read_text());store=PrivateStore(config['root'],Path.cwd())
    envelope=json.loads((store.root/'execution-freeze.json').read_text());freeze=envelope['freeze']
    if not hmac.compare_digest(envelope['authentication'],store.authenticate(freeze)):fail('PRIVATE_FREEZE_AUTHENTICATION_FAILED')
    from n4m._ffi import library_path
    binary=Path('.audit/alpha13/executed-alpha13-cli.exe').resolve();library=Path(library_path()).resolve()
    if digest(binary)!='0edf388a0e7facfad2d19a426938b56b2675a5c1b2bb822b8570fe48cba2e3c2':fail('QUALIFIED_NATIVE_BINARY_CHANGED')
    if digest(library)!='096bae41ffc5e4f6ec8d73b0ca43f0cec83f66dda806b2d43b2d893ba07db164':fail('QUALIFIED_NATIVE_PROVIDER_CHANGED')
    batch=PrivateBatch(store,state_root=Path('results/alpha9-perten-keyed/state'),workspace=Path.cwd(),
        policy=json.loads(Path('configs/bank/storage-policy-alpha14.json').read_text()),
        approval=json.loads(Path('.audit/alpha14/budget-approval.json').read_text()),binary=binary,library=library,
        controller_sha256=digest(__file__))
    manifest=store.root/'profile-execution.json';records=json.loads(manifest.read_text())['records'] if manifest.exists() else []
    old={r['source_receipt_id']:r for r in records};start=time.perf_counter()
    for source in freeze['sources']:
        if source['source_receipt_id'] in old:
            # Exact source/runtime/contract checks still run; cache hits never fit.
            if old[source['source_receipt_id']]['status']!='computed':continue
        try:
            result=batch.profile(source)
            record={'source_receipt_id':source['source_receipt_id'],'status':'computed','reason':None,**result}
        except PrivacyError as exc:
            record={'source_receipt_id':source['source_receipt_id'],'status':'failed','reason':str(exc),'visibility':'local_private'}
        old[source['source_receipt_id']]=record
        records=[old[s['source_receipt_id']] for s in freeze['sources'] if s['source_receipt_id'] in old]
        atomic_json(manifest,{'visibility':'local_private','input_freeze_receipt':freeze['receipt_id'],'records':records,
            'runtime':batch.runtime,'runner_sha256':digest(__file__),'wall_seconds_this_invocation':time.perf_counter()-start,
            'target_accessed':False,'public_export_created':False})
    print(json.dumps({'status':'private_screening_execution_finished','details':'protected local evidence root','public_export_created':False}))


if __name__=='__main__':
    try:main()
    except Exception:
        print(json.dumps({'status':'refused','reason':'PRIVATE_CAMPAIGN_OPERATION_FAILED'}));raise SystemExit(2)
