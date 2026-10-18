"""Finite identity-design audit, simulation and frozen historical exposure replay."""
from collections import Counter
import json
from pathlib import Path
import time
import pandas as pd
from alpha13_common import ROOT,PUBLIC,run,publish
from nirs4all_domains.predictive import native_summary
from nirs4all_domains.storage import atomic_json,digest,fingerprint
from nirs4all_domains.stability_power import balanced_panel,expected_exposure,exposure_masks,schedule


def fixtures():
    def source(name,sizes,labels,intrinsic=None):
        ids=[f'{name}:{i:03}' for i in range(sum(sizes))];units={};offset=0
        for g,n in enumerate(sizes):
            for s in ids[offset:offset+n]:units[s]=f'physical:{g:03}'
            offset+=n
        return {'name':name,'ids':ids,'components':units,'labels':labels,'intrinsic_blocker':intrinsic}
    yield source('singletons_balanced',[1]*120,[i//40 for i in range(120)])
    yield source('small_satellite',[1]*120,[0]*112+[1]*8)
    yield source('whole_repeated_acquisitions',[4]*30,[i//40 for i in range(120)])
    yield source('unequal_components',[1]*10+[4]*10+[7]*10,[i//40 for i in range(120)])
    yield source('dominant_component',[91]+[1]*29,[i//40 for i in range(120)],'ROW_SUPPORT_IS_NOT_AVAILABLE_ON_90_PERCENT_OF_DRAWS_IN_THE_DESIGN')
    yield source('too_few_components',[10]*12,[i//40 for i in range(120)],'FEWER_THAN_20_COMPONENTS')
    yield source('all_noise',[1]*120,[-1]*120,'NO_NONTRIVIAL_REFERENCE_PARTITION')
    yield source('one_group',[1]*120,[0]*120,'NO_NONTRIVIAL_REFERENCE_PARTITION')


def historical():
    frozen=json.loads(Path('docs/benchmarks/alpha12/input-freeze.json').read_text())
    locators=json.loads(Path('.audit/alpha12/input-locators.json').read_text());rows=[]
    for source in frozen['entries']:
        if not source['stability_selected']:continue
        name=source['dataset_id'];ids=pd.read_csv(locators[name]['matrix'],sep=';',usecols=['observation_id'],dtype=str).observation_id.tolist()
        assert fingerprint(ids)==source['observation_ids_sha256'];components=locators[name]['components']
        for fraction in frozen['fractions']:
            draws=schedule(ids,components,fraction,20,frozen['seed']);masks,_=exposure_masks(ids,draws)
            for rep in ['raw','snv']:
                path=Path('docs/benchmarks/alpha12/stability')/(name+'.'+rep+'.'+str(fraction)+'.json')
                old=json.loads(path.read_text())
                for setting in old['settings']:
                    if setting['status']!='computed':continue
                    value=setting['value'];pairs=[p for v in value['pair_panel'].values() for p in v]
                    assert value['successful_draws']==20
                    for pair in pairs:
                        a,b=(ids[i] for i in pair['indices'])
                        assert pair['exposures']==(masks[a]&masks[b]).bit_count()
                    rows.append({'dataset_id':name,'representation':rep,'fraction':fraction,'min_cluster_size':value['min_cluster_size'],
                        'old_classification':value['classification'],'old_pair_support':value['gates']['pair_support'],
                        'pair_count':len(pairs),'effective_exposures':native_summary(p['exposures'] for p in pairs) if pairs else None,
                        'exact_planned_to_observed_exposure_replay':True,'reference_sha256':digest(path)})
    return {'baseline':'ebb1b9b8a45d01618931d846d059641701cac7da','rows':rows,
        'n_settings':len(rows),'failed_pair_support':sum(not r['old_pair_support'] for r in rows),
        'new_pca_fits':0,'new_clustering_fits':0,'target_accessed':False,
        'scope':'Read-only exact identity exposure replay; original classifications and quality thresholds unchanged.'}


def main():
    contract={'task':{'task_id':fingerprint(['alpha13','power-design-audit'])},'phase':'identity-design-audit',
        'protocol_version':'domains.stability_power.v0.1','protocol_sha256':digest('docs/ALPHA13_STABILITY_POWER_PROTOCOL.md'),
        'runner_sha256':digest(__file__),'power_bridge_sha256':digest('bridges/python/nirs4all_domains/stability_power.py'),
        'candidates':[20,40,60,80],'fractions':[.6,.8],'simulation_designs':128,'seed_base':13101,
        'fixtures_sha256':fingerprint(list(fixtures())),'test_target_accessed':False}
    def calculate(folder):
        start=time.perf_counter();rows=[]
        for fixture in fixtures():
            for fraction in contract['fractions']:
                for b in contract['candidates']:
                    feasible=[];eligible=[];coverage=[]
                    for repetition in range(contract['simulation_designs']):
                        draws=schedule(fixture['ids'],fixture['components'],fraction,b,contract['seed_base']+repetition)
                        panel=balanced_panel(fixture['ids'],fixture['labels'],draws)
                        assert panel['status']=='computed'
                        p=panel['value'];feasible.append(float(p['planned_feasible'] and not fixture['intrinsic_blocker']))
                        eligible.append(p['row_eligible_draws']/b)
                        coverage.append(min((c['candidate_coverage'] for c in p['coverage']),default=0.))
                    row={'fixture':fixture['name'],'fraction':fraction,'draws':b,'n_simulated_designs':len(feasible),
                        'intrinsic_blocker':fixture['intrinsic_blocker'],'feasible_designs':int(sum(feasible)),
                        'feasibility_fraction':sum(feasible)/len(feasible),'row_eligible_fraction':native_summary(eligible),
                        'minimum_cluster_candidate_coverage':native_summary(coverage),
                        'analytical_expectation':expected_exposure(fixture['ids'],fixture['components'],fraction,b)}
                    rows.append(row);print(json.dumps({k:row[k] for k in ['fixture','fraction','draws','feasible_designs','n_simulated_designs']}),flush=True)
        chosen=next((b for b in contract['candidates'] if all(r['feasibility_fraction']>=.95 for r in rows if r['draws']==b and r['intrinsic_blocker'] is None)),None)
        return {'protocol_version':'domains.stability_power.v0.1','contract':contract,'rows':rows,'selected_draw_count':chosen,
            'selection_rule':'Smallest prespecified B with at least 95 percent observed feasibility on every intrinsically eligible fixture/fraction.',
            'elapsed_seconds':time.perf_counter()-start,'new_pca_fits':0,'new_clustering_fits':0,'target_accessed':False,
            'uncertainty_scope':'Conditional identity simulation rates, 128 designs per cell; not a 95 percent probability guarantee or biological uncertainty.'}
    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':524288,'expected_fits':0,'expected_permutations':0,
        'uncertainty':'Only finite component identities/exposure counts and native summary; no spectral input or numerical fit.'}
    store,receipt,value=run(contract,'P0',plan,calculate);publish(store,receipt,'design-power.json');atomic_json(ROOT/'design-power-receipt.json',receipt)
    historical_contract={'task':contract['task'],'phase':'alpha12-exposure-replay','runner_sha256':digest(__file__),
        'source_manifest_sha256':digest('docs/benchmarks/alpha12/storage.json'),'power_bridge_sha256':contract['power_bridge_sha256']}
    plan['evidence_bytes']=131072
    store,r,v=run(historical_contract,'P0',plan,lambda folder:historical());publish(store,r,'alpha12-exposure-retrospective.json')
    print(json.dumps({'selected_draw_count':value['selected_draw_count'],'historical_settings_verified':v['n_settings']}))


if __name__=='__main__':main()
