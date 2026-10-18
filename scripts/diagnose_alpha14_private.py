"""Diagnose failed admitted X transport without repeating PCA/HDBSCAN fits."""
import json
import math
from pathlib import Path

from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.privacy import PrivateStore,authorize,opaque_id
from nirs4all_domains.storage import atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import represent


def diagnose(store,freeze,execution):
    results=[]
    for record in execution['records']:
        if record['status']=='computed':continue
        source=next(s for s in freeze['sources'] if s['source_receipt_id']==record['source_receipt_id'])
        authorize(source['admission']);assert digest(source['matrix'])==source['source_sha256']
        outcome={'source_receipt_id':source['source_receipt_id'],'original_status':record['status'],
                 'original_safe_code':record['reason'],'repeated_pca_fits':0,'repeated_hdbscan_fits':0}
        try:
            raw=spectral_request(source['matrix'],source['source_id'],'observation_identity_only')
            if [len(raw['observation_ids']),len(raw['axis'])]!=source['shape']:
                outcome['diagnosis']='PINNED_COMPLETE_SOURCE_DIMENSIONS_MISMATCH'
            elif any(type(v) not in (int,float) for row in raw['spectra'] for v in row):
                outcome['diagnosis']='DECLARED_X_CONTAINS_NON_NUMERIC_CELLS'
            elif any(not math.isfinite(v) for row in raw['spectra'] for v in row):
                outcome['diagnosis']='FULL_SOURCE_CONTAINS_NONFINITE_VALUES_NO_ROW_THINNING_ALLOWED'
            else:
                try:represent(raw,'snv')
                except ValueError as exc:
                    outcome['diagnosis']='FULL_POPULATION_SNV_NOT_FEASIBLE' if str(exc)=='CONSTANT_SPECTRUM_PREVENTS_FULL_POPULATION_SNV' else 'NATIVE_SNV_NOT_QUALIFIED_FOR_COMPLETE_SOURCE'
                else:outcome['diagnosis']='TRANSPORT_AND_SNV_PASS_NATIVE_PROFILE_FAILURE_REQUIRES_SEPARATE_QUALIFICATION'
        except ValueError as exc:
            safe={'NUMERIC_SPECTRAL_AXIS_REQUIRED','FINITE_SPECTRAL_AXIS_REQUIRED','DECLARED_AXIS_NOT_STRICTLY_INCREASING','DUPLICATE_OBSERVATION_ID'}
            outcome['diagnosis']=str(exc) if str(exc) in safe else 'COMPLETE_DECLARED_X_TRANSPORT_NOT_QUALIFIED'
        except Exception:outcome['diagnosis']='COMPLETE_DECLARED_X_TRANSPORT_NOT_QUALIFIED'
        outcome['action']='Retain original failed attempt. Resolve source/format or native qualification under a new explicit contract; do not relabel axes, drop observations, invent values or repeat fits as a cache hit.'
        results.append(outcome)
    return results


def main():
    cfg=json.loads(Path('.audit/alpha14/private-root.json').read_text());store=PrivateStore(cfg['root'],Path.cwd())
    freeze=json.loads((store.root/'execution-freeze.json').read_text())['freeze']
    execution=json.loads((store.root/'profile-execution.json').read_text())
    assert len(execution['records'])==len(freeze['sources'])
    contract={'task':{'task_id':store.authenticate(['alpha14','failed-source-transport-diagnosis'])},
        'visibility':'local_private','protocol':'domains.alpha14.transport_diagnosis.v0.1','runner_sha256':digest(__file__),
        'input_freeze_receipt':freeze['receipt_id']}
    from nirs4all_domains.storage import StageStore
    policy=json.loads(Path('configs/bank/storage-policy-alpha14.json').read_text())
    scheduler=StageStore('results/alpha9-perten-keyed/state',store.root/'diagnostic-scratch',store.root/'diagnostic-evidence',Path.cwd(),policy)
    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':131072,'expected_fits':0,'expected_permutations':0,
          'uncertainty':'Admitted X transport and existing native SNV feasibility only. Zero PCA/HDBSCAN retries; no targets.'}
    receipt,value=scheduler.run(contract,'P0',plan,lambda folder:{'visibility':'local_private',
        'records':diagnose(store,freeze,execution),'target_accessed':False})
    assert value is not None
    atomic_json(store.root/'failed-source-diagnosis.json',{'diagnosis':value,'authentication':store.authenticate(value)})
    print(json.dumps({'status':'private_failure_diagnosis_retained','pca_hdbscan_refits':0,'public_export_created':False}))


if __name__=='__main__':
    try:main()
    except Exception:
        print(json.dumps({'status':'refused','reason':'PRIVATE_DIAGNOSIS_FAILED'}));raise SystemExit(2)
