"""Full-source X-only extension and prospectively planned conditional stability."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import time
from alpha13_common import ROOT,PUBLIC,run,publish
from measure_alpha12_phase import windows_peak
from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.bank import schema_check
from nirs4all_domains.dependence import state
from nirs4all_domains.native_profile_stream import NativeProfileStream
from nirs4all_domains.power_checkpoint import recover_prefix,save_prefix
from nirs4all_domains.stability_power import balanced_panel,schedule,project_draw,decision_summary
from nirs4all_domains.storage import atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import represent,compact_profile,compare_partition,neighborhood_agreement


def read(path):return json.loads(Path(path).read_text())


def reference(entry,rep):
    base=Path('docs/benchmarks/alpha12') if entry.get('reused_alpha12_reference') else PUBLIC
    path=base/'profiles'/(entry['dataset_id']+'.'+rep+'.json');value=read(path)
    assert value['status']=='computed'
    return path,value['value']


def raw_source(entry,locators):
    local=locators[entry['dataset_id']];path=Path(local['matrix']);assert digest(path)==entry['input_csv_sha256']
    raw=spectral_request(path,entry['source_id'],entry['identity_evidence']);raw['axis_unit']=entry['source_dimensions']['axis_unit']
    assert fingerprint(raw['axis'])==entry['axis_sha256'] and fingerprint(raw['observation_ids'])==entry['observation_ids_sha256']
    assert fingerprint(local['components'])==entry['component_map_sha256']
    return raw,local['components']


def plan_for(entry,ids,units,revised):
    result={}
    for rep in revised['representations']:
        path,ref=reference(entry,rep)
        for fraction in revised['fractions']:
            key=rep+'.'+str(fraction);draws=schedule(ids,units,fraction,60,revised['real_resampling_seed'])
            panels=[balanced_panel(ids,s['value']['labels'],draws) if s['status']=='computed' else state(reason='REFERENCE_PARTITION_UNAVAILABLE') for s in ref['cluster_settings']]
            result[key]={'reference_sha256':digest(path),'selected_ids_sha256':fingerprint([d['observation_ids'] for d in draws]),
                'panel_sha256':fingerprint(panels),'panels':panels,'draws':draws,
                'planned_feasible_settings':[p['status']=='computed' and p['value']['planned_feasible'] for p in panels]}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['profiles','plan','stability']);args=parser.parse_args()
    inputs=read(PUBLIC/'real-input-freeze.json');revised=read(PUBLIC/'revised-design-freeze.json');locators=read(ROOT/'input-locators.json')
    assert inputs['revised_design_ref']['sha256']==digest(PUBLIC/'revised-design-freeze.json')
    assert revised['power_bridge_sha256']==digest('bridges/python/nirs4all_domains/stability_power.py')
    binary=Path('target/qualification/n4domains.exe').resolve()
    from n4m._ffi import library_path
    library=Path(library_path()).resolve()
    runtime={'runner_sha256':digest(__file__),'binary_sha256':digest(binary),'library_sha256':digest(library),
        'power_bridge_sha256':revised['power_bridge_sha256'],'geometry_bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py'),
        'native_stream_sha256':digest('bridges/python/nirs4all_domains/native_profile_stream.py')}
    if args.command=='profiles':
        records=[]
        with NativeProfileStream(binary,library) as stream:
            for entry in inputs['entries']:
                if entry.get('reused_alpha12_reference'):continue
                name=entry['dataset_id'];raw,_=raw_source(entry,locators);profiles={}
                for rep in ['raw','snv']:
                    contract={'task':{'task_id':fingerprint([name,'X','domains.unsupervised.v0.1','alpha13-extension'])},
                        'phase':'new-source-reference','real_input_freeze_id':inputs['freeze_id'],'source_sha256':entry['input_csv_sha256'],
                        'representation':rep,'query_design_sha256':fingerprint(entry['query_design']),**runtime}
                    def calculate(folder):
                        begin=time.perf_counter();value=stream.profile(represent(raw,rep),rep,design=entry['query_design'])
                        value=compact_profile(value,entry['query_design']);value['metadata_agreement']=entry['metadata_agreement']
                        value['scope']=entry['resampling_scope'];value['elapsed_seconds']=time.perf_counter()-begin
                        value.update(pca_fits=1,hdbscan_attempts=2,input_source_sha256=entry['input_csv_sha256'])
                        return state(value)
                    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':1048576,'expected_fits':3,'expected_permutations':0,
                        'uncertainty':'One full-population PCA/two HDBSCAN attempts; complete same-query full-axis/PCA neighborhoods; no target or stored scores.'}
                    store,r,value=run(contract,'P2',plan,calculate);publish(store,r,'profiles/'+name+'.'+rep+'.json');profiles[rep]=value['value']
                ids=raw['observation_ids'];partitions=[state(compare_partition(ids,profiles['raw']['cluster_settings'][i]['value']['labels'],ids,profiles['snv']['cluster_settings'][i]['value']['labels']))
                    if all(profiles[rep]['cluster_settings'][i]['status']=='computed' for rep in ['raw','snv']) else state(reason='PARTITION_UNAVAILABLE') for i in range(2)]
                records.append({'dataset_id':name,'source_id':entry['source_id'],'source_content_sha256':entry['input_csv_sha256'],
                    'identity_evidence':entry['identity_evidence'],'source_dimensions':entry['source_dimensions'],'original_numeric_equivalence':entry['original_numeric_equivalence'],
                    'profiles':{rep:{'path':(PUBLIC/'profiles'/(name+'.'+rep+'.json')).as_posix(),'sha256':digest(PUBLIC/'profiles'/(name+'.'+rep+'.json'))} for rep in profiles},
                    'representation_agreement':{'partitions':partitions,'full_axis_neighbors':neighborhood_agreement(profiles['raw']['neighborhoods']['value']['full_axis'],profiles['snv']['neighborhoods']['value']['full_axis'])},
                    'metadata_agreement':entry['metadata_agreement'],'test_target_accessed':False,'model_performance_used':False})
            peak=windows_peak(stream.process) if os.name=='nt' else None
        value={'protocol_version':'domains.unsupervised.v0.1','input_freeze_id':inputs['freeze_id'],'records':records,'new_pca_fits':4,'hdbscan_attempts':8,
            'native_cli_lifetime_peak_resident_bytes':peak,'target_accessed':False,'supervised_fits':0,'universal_shortcut_score':None}
        atomic_json(PUBLIC/'x-only-extension.json',value);print(json.dumps({'new_sources':len(records),'pca_fits':4,'native_peak_bytes':peak}));return
    if args.command=='plan':
        entries=[]
        for entry in inputs['entries']:
            if not entry['stability_selected']:continue
            raw,units=raw_source(entry,locators);plans=plan_for(entry,raw['observation_ids'],units,revised)
            entries.append({'dataset_id':entry['dataset_id'],'conditions':{k:{n:v for n,v in p.items() if n not in ['panels','draws']} for k,p in plans.items()}})
        value={'protocol_version':'domains.stability_power.v0.2','real_input_freeze_id':inputs['freeze_id'],'revised_design_freeze_id':revised['freeze_id'],
            'runner_sha256':digest(__file__),'entries':entries,'target_accessed':False,'model_performance_used':False}
        value['freeze_id']=fingerprint(value);path=PUBLIC/'real-exposure-freeze.json'
        if path.exists():assert read(path)==value
        atomic_json(path,value);print(json.dumps({'plan_freeze_id':value['freeze_id'],'eligible_conditions':sum(any(c['planned_feasible_settings']) for e in entries for c in e['conditions'].values())}));return
    exposure=read(PUBLIC/'real-exposure-freeze.json');assert exposure['runner_sha256']==digest(__file__)
    reports=[]
    with NativeProfileStream(binary,library) as stream:
        for entry in inputs['entries']:
            if not entry['stability_selected']:continue
            name=entry['dataset_id'];raw,units=raw_source(entry,locators);ids=raw['observation_ids'];plans=plan_for(entry,ids,units,revised)
            frozen_entry=next(e for e in exposure['entries'] if e['dataset_id']==name)
            assert frozen_entry['conditions']=={k:{n:v for n,v in p.items() if n not in ['panels','draws']} for k,p in plans.items()}
            conditions={};pca=0;hdb=0;classes=[]
            for rep in ['raw','snv']:
                transformed=represent(raw,rep);_,ref=reference(entry,rep)
                for fraction in revised['fractions']:
                    key=rep+'.'+str(fraction);planned=plans[key]
                    if not any(planned['planned_feasible_settings']):
                        conditions[key]=state(reason='PLANNED_PAIR_EXPOSURE_OR_NONTRIVIAL_PARTITION_SUPPORT_INADEQUATE',status='insufficient_information')
                        classes.extend(['insufficient_information']*2);continue
                    contract={'task':{'task_id':fingerprint([name,'X',revised['protocol_version']])},'phase':'real-conditional-stability',
                        'input_freeze_id':inputs['freeze_id'],'exposure_freeze_id':exposure['freeze_id'],'condition':key,
                        'source_sha256':entry['input_csv_sha256'],'component_map_sha256':entry['component_map_sha256'],
                        'reference_sha256':planned['reference_sha256'],'selected_ids_sha256':planned['selected_ids_sha256'],
                        'panel_sha256':planned['panel_sha256'],**runtime}
                    def calculate(folder):
                        records=recover_prefix(folder.parent,key,contract);reused=len(records);begin=time.perf_counter()
                        for number,draw in enumerate(planned['draws']):
                            if number<len(records):
                                assert records[number]['selected_ids_sha256']==fingerprint(draw['observation_ids']);continue
                            subset={**transformed,'observation_ids':draw['observation_ids'],'spectra':[transformed['spectra'][i] for i in draw['indices']]}
                            try:
                                native=stream.profile(subset,rep);record=project_draw(ids,ref,draw,native,planned['panels'],number)
                            except RuntimeError as error:
                                record={'draw':number,'status':'failed','reason':str(error),'selected_ids_sha256':fingerprint(draw['observation_ids']),'pca_fits':1,'hdbscan_attempts':0}
                            records.append(record);save_prefix(folder/('prefix-'+key+'.json'),contract,records)
                            if number%10==9:print(json.dumps({'dataset':name,'condition':key,'draws':number+1}),flush=True)
                        return {'records':records,'panels':planned['panels'],'reused_prefix_draws':reused,'elapsed_seconds':time.perf_counter()-begin,
                            'pca_fits':sum(r['pca_fits'] for r in records),'hdbscan_attempts':sum(r['hdbscan_attempts'] for r in records),'target_accessed':False}
                    plan={'inputs':[],'scratch_bytes':1048576,'evidence_bytes':1048576,'expected_fits':180,'expected_permutations':0,
                        'uncertainty':'60 whole-component draws, one PCA/two HDBSCAN attempts each; complete source/axes, compact checksummed prefixes, no stored X/scores.'}
                    store,r,batch=run(contract,'P3',plan,calculate);destination='stability-batches/'+name+'.'+key+'.json';publish(store,r,destination)
                    summary=decision_summary(ref,batch['records'],ids,entry['n_resampling_units'],planned['panels'],entry['resampling_scope'])
                    for s in summary['settings']:
                        if s['status']=='computed':
                            s['value'].pop('pair_panel');s['value'].pop('planned_panel');s['value']['pair_panel_ref']={'path':destination,'sha256':r['sha256']}
                            classes.append(s['value']['classification'])
                        else:classes.append('insufficient_information')
                    conditions[key]=state(summary);pca+=batch['pca_fits'];hdb+=batch['hdbscan_attempts']
            parameter=[]
            for rep in ['raw','snv']:
                _,ref=reference(entry,rep);a,b=ref['cluster_settings']
                parameter.append(compare_partition(ids,a['value']['labels'],ids,b['value']['labels'])['ari_including_noise'] if a['status']==b['status']=='computed' else state(reason='PARAMETER_PARTITION_UNAVAILABLE'))
            robust=classes==['robust_structure']*8 and all(p['status']=='computed' and p['value']>=.8 for p in parameter)
            overall=state('robust_structure' if robust else 'fragile_structure') if 'insufficient_information' not in classes and all(p['status']=='computed' for p in parameter) else state(reason='INADEQUATE_ALL_COMBINATION_SUPPORT',status='insufficient_information')
            value={'schema_version':1,'protocol_version':revised['protocol_version'],'dataset_id':name,'source_id':entry['source_id'],
                'source_content_sha256':entry['input_csv_sha256'],'resampling_design':{'input_freeze_id':inputs['freeze_id'],'exposure_freeze_id':exposure['freeze_id'],
                    'revised_design_freeze_id':revised['freeze_id'],'n_observations':len(ids),'n_resampling_units':entry['n_resampling_units'],
                    'unit_scope':entry['resampling_scope'],'parameter_ari':parameter,'per_setting_classifications':classes,'biological_sampling_uncertainty':False},
                'conditions':conditions,'overall_classification':overall,'resource_cost':{'resampling_pca_fits':pca,'hdbscan_attempts':hdb},
                'test_target_accessed':False,'universal_shortcut_score':None,'limitations':['Conditional algorithmic resampling, not biological generalization.',
                    'Supported grouping does not demonstrate shortcuts; missing support does not demonstrate safety.']}
            value=json.loads(json.dumps(value,allow_nan=False));value['record_id']=fingerprint(value);schema_check(value,'stability-power-result')
            path=PUBLIC/'stability'/(name+'.json');atomic_json(path,value);reports.append({'path':path.as_posix(),'sha256':digest(path),
                'dataset_id':name,'per_setting_classifications':classes,'overall_classification':overall,'pca_fits':pca,'hdbscan_attempts':hdb})
        peak=windows_peak(stream.process) if os.name=='nt' else None
    atomic_json(PUBLIC/'real-stability.json',{'protocol_version':revised['protocol_version'],'revised_design_freeze_id':revised['freeze_id'],
        'reports':reports,'pca_refits':sum(r['pca_fits'] for r in reports),'hdbscan_attempts':sum(r['hdbscan_attempts'] for r in reports),
        'classifications':dict(Counter(c for r in reports for c in r['per_setting_classifications'])),
        'native_cli_lifetime_peak_resident_bytes':peak,'target_accessed':False,'supervised_fits':0,'universal_shortcut_score':None})
    print(json.dumps({'sources':len(reports),'real_pca_refits':sum(r['pca_fits'] for r in reports),'native_peak_bytes':peak}))


if __name__=='__main__':main()
