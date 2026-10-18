"""Frozen native-X and oracle qualification; compact restartable prefixes."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random
import time
from alpha13_common import ROOT,PUBLIC,run,publish,native_runtime
from generate_unsupervised_fixtures import MECHANISMS,scenario
from nirs4all_domains.dependence import state
from nirs4all_domains.power_checkpoint import recover_prefix,save_prefix
from nirs4all_domains.stability_power import (QUALITY,balanced_panel,decision_summary,project_draw,schedule)
from nirs4all_domains.storage import atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import compare_partition,native_profile,represent

DEEP=['separated','thin_manifold','overlapping','density_imbalance','satellites',
    'high_dimensional_noise','snv_erased','snv_enhanced','known_acquisitions']
SEEDS=[13031,13033,13037]


def oracle(ids,labels):
    return {'cluster_settings':[state({'labels':labels,'n_clusters':len(set(labels)-{-1}),'noise_fraction':labels.count(-1)/len(labels),
        'min_cluster_size':size,'membership_summary':{'count':len(ids),'min':1.,'max':1.,'mean':1.,'sd':0.,'q25':1.,'median':1.,'q75':1.}}) for size in [8,12]]}


def freeze():
    design=json.loads((PUBLIC/'design-power.json').read_text());assert design['selected_draw_count'] in [20,40,60,80]
    value={'calibration_protocol':'domains.stability_power.v0.1','candidate_revised_protocol':'domains.stability_power.v0.2',
        'design_power_sha256':digest(PUBLIC/'design-power.json'),'protocol_sha256':digest('docs/ALPHA13_STABILITY_POWER_PROTOCOL.md'),
        'power_bridge_sha256':digest('bridges/python/nirs4all_domains/stability_power.py'),
        'generator_sha256':digest('scripts/generate_unsupervised_fixtures.py'),'deep_mechanisms':DEEP,'all_mechanisms':list(MECHANISMS),
        'draw_count':design['selected_draw_count'],'fractions':[.6,.8],'representations':['raw','snv'],'perturbation_seeds':SEEDS,
        'quality_thresholds':QUALITY,'n_generated_observations':120,'native_reference_pca_fits':18,
        'native_draw_pca_fits':len(DEEP)*len(SEEDS)*4*design['selected_draw_count'],
        'original_20_draw_comparison':'Same new-design prefix, no duplicate fitting; not reclassification of historical alpha.12 records.',
        'target_accessed':False,'model_performance_used':False}
    value['freeze_id']=fingerprint(value);path=PUBLIC/'calibration-freeze.json'
    if path.exists():assert json.loads(path.read_text())==value
    atomic_json(path,value);return value


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['freeze','run']);args=p.parse_args();frozen=freeze()
    if args.command=='freeze':print(json.dumps({'freeze_id':frozen['freeze_id'],'draw_count':frozen['draw_count']}));return
    binary,library,runtime=native_runtime();runtime.update(runner_sha256=digest(__file__),
        checkpoint_sha256=digest('bridges/python/nirs4all_domains/power_checkpoint.py'))
    all_summaries=[];receipts=[]
    for mechanism in DEEP:
        fixture=scenario(mechanism);source=fixture['spectral'];ids=source['observation_ids'];units=fixture['components']
        task_id=fingerprint(['alpha13','native-calibration',mechanism]);representations={r:represent(source,r) for r in ['raw','snv']}
        reference_contract={'task':{'task_id':task_id},'phase':'controlled-reference','freeze_id':frozen['freeze_id'],
            'mechanism':mechanism,'source_sha256':fingerprint(source),**runtime}
        def reference_fit(folder):
            output={};begin=time.perf_counter()
            for rep,q in representations.items():
                profile=native_profile(q,rep,binary,library)
                output[rep]={k:v for k,v in profile.items() if k!='transport_only_scores'}
            return {'representations':output,'pca_fits':2,'hdbscan_attempts':4,'elapsed_seconds':time.perf_counter()-begin,'target_accessed':False}
        plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':98304,'expected_fits':6,'expected_permutations':0,
            'uncertainty':'Two native descriptive PCA fits and four HDBSCAN attempts on a frozen small X generator; no Y/model.'}
        store,receipt,reference=run(reference_contract,'P2',plan,reference_fit);publish(store,receipt,'controls/'+mechanism+'.reference.json');receipts.append(receipt)
        for seed in SEEDS:
            planned={rep+'.'+str(f):schedule(ids,units,f,frozen['draw_count'],seed) for rep in representations for f in frozen['fractions']}
            panels={key:[balanced_panel(ids,s['value']['labels'],draws) if s['status']=='computed' else state(reason='REFERENCE_UNAVAILABLE')
                for s in reference['representations'][key.split('.')[0]]['cluster_settings']] for key,draws in planned.items()}
            contract={'task':{'task_id':task_id},'phase':'controlled-resampling','mechanism':mechanism,'perturbation_seed':seed,
                'freeze_id':frozen['freeze_id'],'reference_sha256':receipt['sha256'],
                'selected_ids_sha256':fingerprint({k:[d['observation_ids'] for d in v] for k,v in planned.items()}),
                'panel_sha256':fingerprint(panels),**runtime}
            def calculate(folder):
                conditions={};new_fits=0;reused=0;begin=time.perf_counter()
                for key,draws in planned.items():
                    rep=key.split('.')[0];reference_profile=reference['representations'][rep]
                    prefix_contract={**contract,'condition':key};records=recover_prefix(folder.parent,key,prefix_contract)
                    if len(records)>len(draws):raise ValueError('PREFIX_EXCEEDS_FROZEN_DESIGN')
                    for record,draw in zip(records,draws):
                        assert record['selected_ids_sha256']==fingerprint(draw['observation_ids'])
                    reused+=len(records)
                    for number in range(len(records),len(draws)):
                        draw=draws[number];q=representations[rep];subset={**q,'observation_ids':draw['observation_ids'],
                            'spectra':[q['spectra'][i] for i in draw['indices']]};started=time.perf_counter()
                        try:
                            value=native_profile(subset,rep,binary,library)
                            record=project_draw(ids,reference_profile,draw,value,panels[key],number)
                        except RuntimeError as error:
                            record={'draw':number,'status':'failed','reason':str(error),'selected_ids_sha256':fingerprint(draw['observation_ids']),
                                'pca_fits':1,'hdbscan_attempts':0}
                        record['elapsed_seconds']=time.perf_counter()-started;records.append(record);new_fits+=1
                        save_prefix(folder/('prefix-'+key+'.json'),prefix_contract,records)
                        if number%10==9:print(json.dumps({'mechanism':mechanism,'seed':seed,'condition':key,'draws_completed':number+1}),flush=True)
                    conditions[key]={'records':records,'panels':panels[key]}
                return {'conditions':conditions,'pca_fits':sum(r['pca_fits'] for v in conditions.values() for r in v['records']),
                    'hdbscan_attempts':sum(r['hdbscan_attempts'] for v in conditions.values() for r in v['records']),
                    'new_pca_fits_this_attempt':new_fits,'reused_prefix_draws':reused,'elapsed_seconds':time.perf_counter()-begin,'target_accessed':False}
            plan={'inputs':[],'scratch_bytes':524288,'evidence_bytes':524288,'expected_fits':12*frozen['draw_count'],'expected_permutations':0,
                'uncertainty':'Four fixed representation/fraction conditions; one PCA and two HDBSCAN attempts per draw, compact exact prefix restart, no X/scores persisted.'}
            store,r,batch=run(contract,'P3',plan,calculate);publish(store,r,'controls/'+mechanism+'.'+str(seed)+'.json');receipts.append(r)
            for key,c in batch['conditions'].items():
                rep=key.split('.')[0];summary=decision_summary(reference['representations'][rep],c['records'],ids,len(set(units.values())),c['panels'],
                    'Controlled fixed X; repeated perturbation designs, not biological or independent-generative replication.')
                for s in summary['settings']:
                    if s['status']=='computed':
                        s['value']['pair_panel_ref']={'path':'controls/'+mechanism+'.'+str(seed)+'.json','sha256':r['sha256']}
                        s['value'].pop('pair_panel');s['value'].pop('planned_panel')
                all_summaries.append({'mechanism':mechanism,'seed':seed,'condition':key,'summary':summary})
        print(json.dumps({'mechanism_completed':mechanism}),flush=True)
    # Oracle decision errors are defined independently of natural-X taxonomies.
    ids=[f'oracle:{i:03}' for i in range(120)];labels=[i//40 for i in range(120)];units={s:s for s in ids};reference=oracle(ids,labels)
    oracle_rows=[]
    for seed in SEEDS:
        for f in frozen['fractions']:
            draws=schedule(ids,units,f,frozen['draw_count'],seed);panels=[balanced_panel(ids,labels,draws)]*2
            for truth in ['stable','unstable','missing']:
                records=[]
                for number,draw in enumerate(draws):
                    if truth=='missing' and number%2:
                        records.append({'draw':number,'status':'failed','reason':'CONTROLLED_MISSING_COMPARISON'});continue
                    selected=[labels[ids.index(s)] for s in draw['observation_ids']]
                    if truth=='unstable':random.Random(seed+number).shuffle(selected)
                    records.append(project_draw(ids,reference,draw,oracle(draw['observation_ids'],selected),panels,number))
                report=decision_summary(reference,records,ids,120,panels,'Oracle decision truth, not an X-generating population claim.')
                classes=[s['value']['classification'] for s in report['settings']]
                oracle_rows.append({'truth':truth,'seed':seed,'fraction':f,'classifications':classes,
                    'false_robust':sum(c=='robust_structure' for c in classes) if truth=='unstable' else None,
                    'false_fragile':sum(c=='fragile_structure' for c in classes) if truth=='stable' else None,
                    'inconclusive':classes.count('insufficient_information')})
    final_contract={'task':{'task_id':fingerprint(['alpha13','calibration-summary'])},'phase':'controlled-calibration-summary',
        'freeze_id':frozen['freeze_id'],'input_hashes':[r['sha256'] for r in receipts],**runtime}
    def consolidate(folder):
        return {'freeze_id':frozen['freeze_id'],'protocol_version':'domains.stability_power.v0.1','native_summaries':all_summaries,
            'oracle_decisions':oracle_rows,'oracle_false_robust':sum(r['false_robust'] or 0 for r in oracle_rows),
            'oracle_false_fragile':sum(r['false_fragile'] or 0 for r in oracle_rows),
            'native_classifications':dict(Counter(s['value']['classification'] for r in all_summaries for s in r['summary']['settings'] if s['status']=='computed')),
            'native_pca_fits':frozen['native_reference_pca_fits']+frozen['native_draw_pca_fits'],
            'native_hdbscan_attempts':2*(frozen['native_reference_pca_fits']+frozen['native_draw_pca_fits']),
            'original_16_mechanisms_ref':{'path':'docs/benchmarks/alpha12/controlled-mechanisms.json','sha256':digest('docs/benchmarks/alpha12/controlled-mechanisms.json')},
            'limits':['Nine deep native mechanisms, fixed generator X seed; three perturbation seeds are conditional designs.',
                'Natural continuum/noise robustness is not automatically a false discrete-population finding.',
                'Oracle false-decision rates do not estimate real-bank prevalence or predictive fragility.'],
            'target_accessed':False,'model_fits':0}
    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':2097152,'expected_fits':0,'expected_permutations':0,'uncertainty':'Native ARI oracle checks and no-refit summary over exact completed controlled experiments.'}
    store,r,v=run(final_contract,'P4',plan,consolidate);publish(store,r,'controlled-calibration.json');atomic_json(ROOT/'calibration-receipts.json',receipts+[r])
    print(json.dumps({'pca_fits':v['native_pca_fits'],'hdbscan_attempts':v['native_hdbscan_attempts'],'false_robust':v['oracle_false_robust'],'false_fragile':v['oracle_false_fragile']}))


if __name__=='__main__':main()
