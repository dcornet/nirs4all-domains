"""Task-specific gated original-keyed pilot; Methods/DAG owns all numerics."""
import json
import math
import os
from pathlib import Path
import threading
import time

from alpha17_common import Context, read
from run_alpha10_multifamily import peak_memory
from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.dependence import score_oof, state
from nirs4all_domains.multifamily import _native_inner
from nirs4all_domains.predictive import native_summary
from nirs4all_domains.storage import atomic_json, digest, fingerprint, tree_bytes


def main():
    c=Context();p=c.load('ORIGINAL_KEYED_TABLET_PILOT_FREEZE.json')
    grant_path=c.root/'owner-tablet-pilot-approval.json'
    # Presence of a proposal or X-only approval can never authorize real fits.
    assert grant_path.exists(), 'TASK_SPECIFIC_REAL_FIT_APPROVAL_REQUIRED'
    grant=c.load(grant_path.name)
    assert grant.get('owner_approved') is True and grant.get('plan_id')==p['plan_id']
    assert grant.get('new_reservation_bytes')==8388608 and grant.get('native_model_fit_upper')==104
    assert grant.get('train_only_PCA_fit_upper')==4
    assert digest(__file__)==p['controller_sha256']
    from n4m._ffi import library_path
    library=library_path();assert digest(library)==p['methods_library_sha256']
    for n,sha in p['bridge_sha256'].items():assert digest(Path('bridges/python/nirs4all_domains')/n)==sha
    for item in p['inputs']:assert digest(item['path'])==item['sha256']
    c.guard(8388608)
    contract={'task':{'task_id':c.store.authenticate(['alpha17-tablet',p['plan_id']])},
        'protocol':p['protocol'],'visibility':'local_private','freeze_receipt':c.store.authenticate(p)}
    prior=read(c.scheduler.root/'journal.json')['runs'].get(fingerprint(contract)+':P3')
    assert not prior or prior['status']=='computed', 'PARTIAL_STAGE_REQUIRES_SEPARATE_REVIEW_NO_AUTO_REFIT'
    plan={'inputs':[],'scratch_bytes':4194304,'evidence_bytes':4194304,
        'expected_fits':108,'expected_permutations':0,
        'uncertainty':'104 native PLS/Ridge fits and four training-only FlexiblePCA fits; source-specific time/RAM unmeasured.'}
    def compute(folder):
        import numpy as np
        import pandas as pd
        from n4m.roles import FlexiblePCA
        started=time.monotonic();done=threading.Event();peak=[peak_memory()]
        def monitor():
            while not done.wait(.1):
                peak[0]=max(peak[0],peak_memory())
                if peak[0]>1073741824 or time.monotonic()-started>3600:
                    c.save('tablet-resource-stop.json',{'fixed_reason':'PILOT_RAM_OR_WALL_STOP','observed_peak_bytes':peak[0]})
                    os._exit(75)  # Preserve reservation/partial evidence; never resume/refit silently.
        thread=threading.Thread(target=monitor,daemon=True);thread.start()
        try:
            # Scope/keys were frozen before this first quantitative decode.
            spectral=spectral_request(p['canonical_X'],'X')
            assert (len(spectral['observation_ids']),len(spectral['axis']))==(310,404)
            x={k:v for k,v in zip(spectral['observation_ids'],spectral['spectra'],strict=True)}
            table=pd.read_csv(p['original_source'],sep=';',usecols=['Unnamed: 0',p['target']['column']],dtype={'Unnamed: 0':str},keep_default_na=False)
            assert len(table)==310 and not table['Unnamed: 0'].duplicated().any()
            target={r['Unnamed: 0']:float(r[p['target']['column']]) for r in table.to_dict('records')}
            assert set(target)=={r['source_record_key'] for r in p['identities']['records']}
            records=p['identities']['records'];ids=p['identities']['development_observation_ids']
            assert not p['identities']['retained_observation_ids'] and set(ids)==set(x)
            rows={r['observation_id']:{'observation_id':r['observation_id'],
                'physical_sample_id':r['observation_id'],'independence_group':r['source_type'],
                'x':x[r['observation_id']],'y':target[r['source_record_key']]} for r in records}
            assert all(math.isfinite(r['y']) and all(map(math.isfinite,r['x'])) for r in rows.values()), 'COMPLETE_FINITE_X_Y_REQUIRED_NO_ROW_DROPPING'
            oof={a['id']:[] for a in p['anchors']};lineage=[];diagnostics=[];models=0;pca_count=0
            for f in p['identities']['outer_folds']['folds']:
                train=[rows[k] for k in f['train_sample_ids']];valid=[rows[k] for k in f['validation_sample_ids']]
                train_y=native_summary(r['y'] for r in train);null=train_y['mean']
                for anchor in p['anchors']:
                    fitted,trace=_native_inner(train,p['identities']['inner_folds'][f['fold_id']],anchor,library)
                    models+=len(p['identities']['inner_folds'][f['fold_id']]['folds'])*len(next(iter(anchor['grid'].values())))+1
                    predictions=fitted.predict([r['x'] for r in valid]).reshape(-1).tolist()
                    assert len(predictions)==len(valid) and all(map(math.isfinite,predictions))
                    block=[{'observation_id':r['observation_id'],'reference_value':r['y'],'prediction':v,'null_prediction':null} for r,v in zip(valid,predictions,strict=True)]
                    oof[anchor['id']]+=block
                    checkpoint={'fold_id':f['fold_id'],'anchor':anchor['id'],'OOF':block,'lineage':trace,
                        'training_only_target_summary':train_y,'train_count':len(train),'eval_count':len(valid)}
                    atomic_json(folder/(fingerprint([f['fold_id'],anchor['id']])+'.json'),checkpoint,max_bytes=524288)
                    lineage.append({k:v for k,v in checkpoint.items() if k!='OOF'});del fitted
                pca=FlexiblePCA(n_components=p['PCA_components']);pca.fit(np.asarray([r['x'] for r in train],dtype=np.float64));pca_count+=1
                training=pca.transform(np.asarray([r['x'] for r in train],dtype=np.float64))
                evaluation=pca.transform(np.asarray([r['x'] for r in valid],dtype=np.float64))
                diagnostics.append({'fold_id':f['fold_id'],'training_only_target_summary':train_y,
                    'eval_below_training_target_min':sum(r['y']<train_y['min'] for r in valid),
                    'eval_above_training_target_max':sum(r['y']>train_y['max'] for r in valid),
                    'PC1_PC2':{'training':[native_summary(training[:,j]) for j in range(2)],
                        'evaluation':[native_summary(evaluation[:,j]) for j in range(2)]},
                    'continuous_support':state(reason='QUALIFIED_CONTINUOUS_SUPPORT_NOT_IMPLEMENTED_FOR_THIS_TASK'),
                    'exact_full_moments':state(reason='NOT_COMPUTED_FROM_TRUNCATED_TRAIN_PCA')})
                del pca,training,evaluation
                assert tree_bytes([folder])<=4194304
            outcomes={}
            for anchor,blocks in oof.items():
                assert len(blocks)==310 and {r['observation_id'] for r in blocks}==set(ids)
                model=score_oof(blocks,'prediction',target='reference_value')
                null=score_oof(blocks,'null_prediction',target='reference_value')
                rm=model['value']['rmse'];rn=null['value']['rmse']
                skill=state(1-rm['value']/rn['value']) if rm['status']==rn['status']=='computed' and rn['value']>0 else state(reason='ZERO_OR_UNDEFINED_TRAINING_NULL_RMSE')
                per_context=[]
                for f in p['identities']['outer_folds']['folds']:
                    selected=[r for r in blocks if r['observation_id'] in f['validation_sample_ids']]
                    per_context.append({'fold_id':f['fold_id'],'scores':score_oof(selected,'prediction',target='reference_value')})
                outcomes[anchor]={'model':model,'null':null,'S':skill,'per_context':per_context,'OOF':blocks}
            assert models==104 and pca_count==4
            return {'protocol':p['protocol'],'plan_id':p['plan_id'],'outcomes':outcomes,'lineage':lineage,
                'diagnostics':diagnostics,'native_model_fits':models,'PCA_fits':pca_count,
                'retained_target_accessed':False,'unknown_physical_assay_dependencies':True,
                'independent_generalization':False,'H1_H5_changed':False,
                'observed_peak_bytes':peak[0],'wall_seconds':time.monotonic()-started}
        finally:done.set();thread.join(timeout=2)
    receipt,value=c.scheduler.run(contract,'P3',plan,compute)
    assert value is not None, 'PILOT_STAGE_FAILED_NO_AUTOMATIC_RETRY'
    artifact=c.scheduler.evidence/receipt['artifact']
    c.save('tablet-pilot-results.json',{'artifact_path':str(artifact),'artifact_sha256':digest(artifact),'receipt':receipt})
    c.preservation();print('ALPHA17_APPROVED_TABLET_PILOT_FINISHED; RESULTS_PROTECTED')


if __name__=='__main__':
    try:main()
    except Exception as error:
        try:Context().save('tablet-pilot-failure.json',{'type':type(error).__name__,'detail':str(error)})
        except Exception:pass
        print('ALPHA17_TABLET_PILOT_REFUSED; DETAILS_REMAIN_LOCAL');raise SystemExit(2) from None
