"""Unchanged alpha.13 B60 science, protected plans/prefixes/results; no export."""
import argparse
import hmac
import json
from pathlib import Path
import time

from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.dependence import state
from nirs4all_domains.privacy import PrivateStore,ScopedIdentities,authorize,acquire_private,fail,opaque_id,_no_reparse
from nirs4all_domains.private_batch import PrivateBatch
from nirs4all_domains.power_checkpoint import recover_prefix,save_prefix
from nirs4all_domains.stability_power import schedule,balanced_panel,project_draw,decision_summary
from nirs4all_domains.storage import atomic_json,digest,fingerprint,tree_bytes
from nirs4all_domains.unsupervised import represent,compare_partition
from nirs4all_domains.native_profile_stream import NativeProfileStream


def load_raw(store,source):
    authorize(source['admission'])
    _no_reparse(Path(source['matrix']).absolute())
    if acquire_private(source['admission'],lambda:digest(source['matrix']))!=source['source_sha256']:
        fail('PRIVATE_SOURCE_CONTENT_CHANGED')
    raw=acquire_private(source['admission'],lambda:spectral_request(source['matrix'],source['source_id'],'observation_identity_only'))
    raw['axis_unit']=source['axis_unit']
    if [len(raw['observation_ids']),len(raw['axis'])]!=source['shape']:fail('PRIVATE_COMPLETE_SOURCE_SHAPE_CHANGED')
    mapped=ScopedIdentities(store).map_view(source['study_scope'],source['population_scope'],raw['observation_ids'],
        {s:s for s in raw['observation_ids']},{s:'descriptive' for s in raw['observation_ids']},view_scope=source['source_receipt_id'])
    raw['observation_ids']=mapped['observation_ids'];raw['source_id']=source['source_receipt_id']
    return raw,mapped['components']


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['plan','run']);args=parser.parse_args()
    cfg=json.loads(Path('.audit/alpha14/private-root.json').read_text());store=PrivateStore(cfg['root'],Path.cwd())
    envelope=json.loads((store.root/'execution-freeze.json').read_text());freeze=envelope['freeze']
    assert hmac.compare_digest(envelope['authentication'],store.authenticate(freeze))
    from n4m._ffi import library_path
    batch=PrivateBatch(store,state_root=Path('results/alpha9-perten-keyed/state'),workspace=Path.cwd(),
        policy=json.loads(Path('configs/bank/storage-policy-alpha14.json').read_text()),
        approval=json.loads(Path('.audit/alpha14/budget-approval.json').read_text()),
        binary=Path('.audit/alpha13/executed-alpha13-cli.exe'),library=Path(library_path()),controller_sha256=digest(__file__))
    if batch.runtime['binary_sha256']!='0edf388a0e7facfad2d19a426938b56b2675a5c1b2bb822b8570fe48cba2e3c2' or batch.runtime['library_sha256']!='096bae41ffc5e4f6ec8d73b0ca43f0cec83f66dda806b2d43b2d893ba07db164':
        fail('QUALIFIED_NATIVE_RUNTIME_CHANGED')
    revised=json.loads(Path(freeze['power_design_ref']['path']).read_text())
    assert digest(freeze['power_design_ref']['path'])==freeze['power_design_ref']['sha256']
    assert revised['power_bridge_sha256']==digest('bridges/python/nirs4all_domains/stability_power.py')
    plan_path=store.root/'deep-exposure-freeze.v2.json'
    if args.command=='plan':
        if plan_path.exists():fail('IMMUTABLE_PRIVATE_EXPOSURE_FREEZE_EXISTS')
        entries=[]
        for source in freeze['sources']:
            if not source['deep_selected']:continue
            try:reference=store.get(source['evidence_receipt_id'])['payload']
            except Exception:
                entries.append({'source_receipt_id':source['source_receipt_id'],'status':'unavailable','reason':'FROZEN_REFERENCE_PROFILE_NOT_COMPUTED'});continue
            raw,units=load_raw(store,source);ids=raw['observation_ids'];plans={}
            for rep in ['raw','snv']:
                ref=reference['representations'][rep]
                for fraction in revised['fractions']:
                    draws=schedule(ids,units,fraction,60,revised['real_resampling_seed'])
                    panels=[balanced_panel(ids,s['value']['labels'],draws) if s['status']=='computed' else state(reason='REFERENCE_PARTITION_UNAVAILABLE') for s in ref['cluster_settings']]
                    plans[rep+'.'+str(fraction)]={'panels':panels,'draws':draws,
                        'planned_feasible_settings':[p['status']=='computed' and p['value']['planned_feasible'] for p in panels]}
            entries.append({'source_receipt_id':source['source_receipt_id'],'status':'planned','reason':None,
                'reference_receipt':source['evidence_receipt_id'],'reference_sha256':fingerprint(reference),
                'ids_sha256':fingerprint(ids),'components_sha256':fingerprint(units),'plans':plans})
        value={'visibility':'local_private','protocol':'domains.stability_power.v0.2','receipt_id':opaque_id(),
            'input_freeze_receipt':freeze['receipt_id'],'entries':entries,'runtime':batch.runtime,
            'power_bridge_sha256':revised['power_bridge_sha256'],'target_accessed':False,'model_performance_used':False}
        original_plan=json.loads((store.root/'deep-exposure-freeze.json').read_text())['plan']
        assert original_plan['entries']==entries,'EXPOSURE_CHANGED_DURING_METADATA_ONLY_CORRECTION'
        value['supersedes_no_fit_plan_receipt']=original_plan['receipt_id']
        atomic_json(plan_path,{'plan':value,'authentication':store.authenticate(value)})
        print(json.dumps({'status':'private_exposure_design_frozen','public_export_created':False}));return
    envelope=json.loads(plan_path.read_text());plan=envelope['plan']
    assert hmac.compare_digest(envelope['authentication'],store.authenticate(plan))
    assert plan['runtime']==batch.runtime and plan['input_freeze_receipt']==freeze['receipt_id']
    records=[];started=time.perf_counter()
    with NativeProfileStream(batch.binary,batch.library) as stream:
        for planned in plan['entries']:
            if planned['status']!='planned':records.append(planned);continue
            source=next(s for s in freeze['sources'] if s['source_receipt_id']==planned['source_receipt_id'])
            reference=store.get(source['evidence_receipt_id'])['payload'];assert fingerprint(reference)==planned['reference_sha256']
            raw,units=load_raw(store,source);ids=raw['observation_ids']
            assert fingerprint(ids)==planned['ids_sha256'] and fingerprint(units)==planned['components_sha256']
            conditions={};classes=[];fits=0;attempts=0
            for rep in ['raw','snv']:
                transformed=represent(raw,rep);ref=reference['representations'][rep]
                for fraction in revised['fractions']:
                    key=rep+'.'+str(fraction);exposure=planned['plans'][key]
                    if not any(exposure['planned_feasible_settings']):
                        conditions[key]=state(reason='PLANNED_PAIR_EXPOSURE_OR_PARTITION_SUPPORT_INADEQUATE',status='insufficient_information')
                        classes.extend(['insufficient_information']*2);continue
                    secret_contract={'source_receipt':source['source_receipt_id'],'source_sha256':source['source_sha256'],
                        'input_freeze_receipt':freeze['receipt_id'],'exposure_receipt':plan['receipt_id'],
                        'reference_sha256':planned['reference_sha256'],'condition':key,
                        'exposure_sha256':fingerprint(exposure),'runtime':batch.runtime,'power_bridge_sha256':plan['power_bridge_sha256']}
                    contract={'task':{'task_id':store.authenticate(['deep-task',source['source_receipt_id'],key])},
                        'private_contract_receipt':store.authenticate(secret_contract),'visibility':'local_private',
                        'protocol':'domains.stability_power.v0.2'}
                    def calculate(folder):
                        draws=recover_prefix(folder.parent,key,secret_contract);reused=len(draws)
                        for number,draw in enumerate(exposure['draws']):
                            if number<len(draws):
                                assert draws[number]['selected_ids_sha256']==fingerprint(draw['observation_ids']);continue
                            subset={**transformed,'observation_ids':draw['observation_ids'],
                                    'spectra':[transformed['spectra'][i] for i in draw['indices']]}
                            try:
                                native=stream.profile(subset,rep)
                                record=project_draw(ids,ref,draw,native,exposure['panels'],number)
                            except RuntimeError:
                                record={'draw':number,'status':'failed','reason':'PRIVATE_NATIVE_REFIT_FAILED',
                                    'selected_ids_sha256':fingerprint(draw['observation_ids']),'pca_fits':1,'hdbscan_attempts':0}
                            draws.append(record);save_prefix(folder/('prefix-'+key+'.json'),secret_contract,draws)
                        return {'visibility':'local_private','records':draws,'panels':exposure['panels'],'reused_prefix_draws':reused,
                            'pca_fits':sum(r['pca_fits'] for r in draws),'hdbscan_attempts':sum(r['hdbscan_attempts'] for r in draws),'target_accessed':False}
                    costs={'inputs':[],'scratch_bytes':1048576,'evidence_bytes':2097152,'expected_fits':180,'expected_permutations':0,
                        'uncertainty':'Frozen B60; unchanged native PCA/HDBSCAN; protected checked prefixes; no X/scores saved.'}
                    ledger=json.loads((batch.scheduler.root/'journal.json').read_text())
                    old=ledger['runs'].get(fingerprint(contract)+':P3')
                    if not (old and old['status']=='computed') and ledger['reserved_campaign_bytes']-batch.approval['previous_campaign_reserved']+3145728>batch.approval['new_reservation_envelope']:
                        fail('PRIVATE_NEW_RESERVATION_ENVELOPE_EXCEEDED')
                    if tree_bytes([Path.cwd(),store.root,*source['other_participating_files']])+3145728>batch.policy['workspace_max_bytes']:
                        fail('PRIVATE_COMBINED_STORAGE_LIMIT')
                    receipt,value=batch.scheduler.run(contract,'P3',costs,calculate)
                    if value is None:fail('PRIVATE_STABILITY_STAGE_NOT_COMPUTED')
                    summary=decision_summary(ref,value['records'],ids,len(set(units.values())),exposure['panels'],
                        'Observation-conditional algorithmic stability; original biological/reference dependencies unresolved.')
                    for setting in summary['settings']:
                        classes.append(setting['value']['classification'] if setting['status']=='computed' else 'insufficient_information')
                    conditions[key]=state(summary);fits+=value['pca_fits'];attempts+=value['hdbscan_attempts']
            parameter=[]
            for rep in ['raw','snv']:
                a,b=reference['representations'][rep]['cluster_settings']
                parameter.append(compare_partition(ids,a['value']['labels'],ids,b['value']['labels'])['ari_including_noise']
                    if a['status']==b['status']=='computed' else state(reason='PARAMETER_PARTITION_UNAVAILABLE'))
            robust=classes==['robust_structure']*8 and all(p['status']=='computed' and p['value']>=.8 for p in parameter)
            overall=state('robust_structure' if robust else 'fragile_structure') if 'insufficient_information' not in classes and all(p['status']=='computed' for p in parameter) else state(reason='INADEQUATE_ALL_COMBINATION_SUPPORT',status='insufficient_information')
            result={'source_receipt_id':source['source_receipt_id'],'visibility':'local_private','conditions':conditions,
                'per_setting_classifications':classes,'parameter_ari':parameter,'overall_classification':overall,
                'pca_refits':fits,'hdbscan_attempts':attempts,'test_target_accessed':False,'biological_sampling_uncertainty':False}
            path=store.root/'stability'/ (source['source_receipt_id']+'.json');atomic_json(path,result)
            records.append({'source_receipt_id':source['source_receipt_id'],'status':'computed','reason':None,'local_path':str(path),
                'sha256':digest(path),'pca_refits':fits,'hdbscan_attempts':attempts})
            atomic_json(store.root/'stability-execution.json',{'visibility':'local_private','input_freeze_receipt':freeze['receipt_id'],
                'exposure_receipt':plan['receipt_id'],'records':records,'runtime':batch.runtime,'wall_seconds':time.perf_counter()-started,
                'public_export_created':False,'target_accessed':False})
    atomic_json(store.root/'stability-execution.json',{'visibility':'local_private','input_freeze_receipt':freeze['receipt_id'],
        'exposure_receipt':plan['receipt_id'],'records':records,'runtime':batch.runtime,'wall_seconds':time.perf_counter()-started,
        'public_export_created':False,'target_accessed':False})
    print(json.dumps({'status':'private_stability_execution_finished','details':'protected local evidence root','public_export_created':False}))


if __name__=='__main__':
    try:main()
    except Exception:
        print(json.dumps({'status':'refused','reason':'PRIVATE_STABILITY_OPERATION_FAILED'}));raise SystemExit(2)
