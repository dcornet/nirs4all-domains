"""Publish measured controlled X-only mechanisms through the same public kernels."""
import json
from pathlib import Path
import time
from generate_unsupervised_fixtures import MECHANISMS,scenario
from run_alpha12_profiles import export
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import StageStore,digest,fingerprint,atomic_json
from nirs4all_domains.unsupervised import (compact_profile,compare_partition,component_draw,
    native_profile,neighborhood_agreement,query_design,represent,stability_summary)

ROOT=Path('.audit/alpha12');PUBLIC=Path('docs/benchmarks/alpha12')


def main():
    from n4m._ffi import library_path
    library=Path(library_path()).resolve();binary=Path('target/debug/n4domains.exe').resolve()
    policy=json.loads(Path('configs/bank/storage-policy-alpha12.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
    contract={'task':{'task_id':fingerprint(['alpha12','controlled-x-only'])},'protocol':'domains.unsupervised.v0.1',
        'runner_sha256':digest(__file__),'generator_sha256':digest('scripts/generate_unsupervised_fixtures.py'),
        'bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py'),
        'binary_sha256':digest(binary),'library_sha256':digest(library),
        'protocol_sha256':digest('docs/ALPHA12_UNSUPERVISED_PROTOCOL.md')}
    def run(folder):
        start=time.perf_counter();cases=[];pca_fits=0;hdbscan_attempts=0
        for name in MECHANISMS:
            for size in ((48,120,240) if name=='fragmentation' else (120,)):
                fixture=scenario(name,n=size);source=fixture['spectral'];ids=source['observation_ids'];profiles={}
                for representation in ('raw','snv'):
                    q=represent(source,representation);design=query_design(ids,len(q['axis']))
                    value=native_profile(q,representation,binary,library,design);pca_fits+=1;hdbscan_attempts+=2
                    profiles[representation]=compact_profile(value,design)
                raw,snv=profiles['raw'],profiles['snv']
                cases.append({'mechanism':name,'n':len(ids),'p':len(source['axis']),'source_sha256':fingerprint(source),
                    'identity_evidence':source['identity_evidence'],'n_declared_units':len(set(fixture['components'].values())),
                    'representations':{r:{'pca':v['pca'],'effective_dimension':v['effective_dimension'],
                        'clusters':[{k:x['value'][k] for k in ['n_clusters','noise_fraction','membership_summary']} if x['status']=='computed' else x for x in v['cluster_settings']],
                        'normalized_nearest':v['neighborhoods']['value']['full_axis']['normalized_nearest_summary'],
                        'proximity':v['neighborhoods']['value']['full_axis']['relative_proximity'],
                        'physical_duplicate_inference':state(reason='NO_PHYSICAL_INFERENCE_FROM_SPECTRAL_PROXIMITY')}
                        for r,v in profiles.items()},
                    'raw_snv_partition':compare_partition(ids,raw['cluster_settings'][0]['value']['labels'],ids,snv['cluster_settings'][0]['value']['labels']),
                    'raw_snv_neighbors':neighborhood_agreement(raw['neighborhoods']['value']['full_axis'],snv['neighborhoods']['value']['full_axis']),
                    'interpretation':'Known X generator; neither stable clusters nor spectral coincidence identify a biological nuisance or model reliance.'})
        reference_source=scenario('separated')['spectral'];ids=reference_source['observation_ids']
        reference=native_profile(reference_source,'raw',binary,library);pca_fits+=1;hdbscan_attempts+=2;draws=[]
        for number in range(20):
            draw=component_draw(ids,{s:s for s in ids},.8,number)
            q={**reference_source,'observation_ids':draw['observation_ids'],'spectra':[reference_source['spectra'][i] for i in draw['indices']]}
            value=native_profile(q,'raw',binary,library);pca_fits+=1;hdbscan_attempts+=2
            draws.append({'draw':number,'status':'computed','reason':None,'value':value,
                'selected_indices':draw['indices'],'n_selected_units':len(draw['selected_units'])})
        stability=stability_summary(reference,draws,ids,len(ids),'Simulated observation algorithmic stability; no biological sampling uncertainty.')
        assert all(s['value']['classification']=='robust_structure' for s in stability['settings'])
        return {'protocol_version':'domains.unsupervised.v0.1','cases':cases,'n_mechanisms':16,
            'separated_resampling_positive_control':stability,'pca_fits':pca_fits,'hdbscan_attempts':hdbscan_attempts,
            'elapsed_seconds':time.perf_counter()-start,'model_fits':0,'target_accessed':False,
            'limitations':['Controlled geometries qualify descriptor response, not prediction of generalization failure.',
                'Negative/all-noise/fragile results are retained; no real-source thresholds are retuned.']}
    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':1048576,'expected_fits':171,'expected_permutations':0,
        'uncertainty':'57 PCA and 114 HDBSCAN attempts on generated small X only; no models or acquisition. Compact summaries, no stored spectra.'}
    receipt,value=store.run(contract,'P2',plan,run)
    atomic_json(ROOT/'controls-receipt.json',receipt)
    if value is None:raise RuntimeError(receipt)
    export(store,receipt,PUBLIC/'controlled-mechanisms.json')
    print(json.dumps({'status':receipt['status'],'cache_hit':receipt['cache_hit'],'pca_fits':value['pca_fits'],'hdbscan_attempts':value['hdbscan_attempts'],'seconds':value['elapsed_seconds']}))


if __name__=='__main__':main()
