"""Prespecified whole-unit/observation subsampling, with per-draw checkpoints."""
import argparse
import json
from pathlib import Path
import time
from run_alpha12_profiles import export
from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import StageStore,atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import component_draw,native_profile,represent,stability_summary

ROOT=Path('.audit/alpha12');PUBLIC=Path('docs/benchmarks/alpha12')
SENTINELS=('ecosis_2008_university_of_wisconsin_biotron_fresh_leaf_spectra_reflectance_nirs','cartilage_spectroscopy_scientificdata_nir')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=['sentinel','rest'],required=True);args=parser.parse_args()
    frozen=json.loads((PUBLIC/'input-freeze.json').read_text());locators=json.loads((ROOT/'input-locators.json').read_text())
    policy=json.loads(Path('configs/bank/storage-policy-alpha12.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
    binary=Path('target/debug/n4domains.exe').resolve()
    from n4m._ffi import library_path
    library=Path(library_path()).resolve();runner_sha=digest(__file__)
    if args.phase=='rest':
        review=json.loads((ROOT/'sentinel-cost-review.json').read_text())
        if not review['remaining_prespecified_cases_admitted'] or review['runner_sha256']!=runner_sha:
            raise ValueError('MEASURED_SENTINEL_COST_REVIEW_REQUIRED')
    selected=[e for e in frozen['entries'] if e['stability_selected'] and ((e['dataset_id'] in SENTINELS)==(args.phase=='sentinel'))]
    if args.phase=='sentinel':selected.sort(key=lambda e:SENTINELS.index(e['dataset_id']))
    for entry in selected:
        name=entry['dataset_id'];local=locators[name];path=Path(local['matrix'])
        if digest(path)!=entry['input_csv_sha256']:raise ValueError('FROZEN_X_CHANGED')
        if fingerprint(local['components'])!=entry['component_map_sha256']:raise ValueError('RESAMPLING_UNIT_MAP_CHANGED')
        raw=spectral_request(path,entry['source_id'],entry['identity_evidence']);raw['axis_unit']=entry['source_dimensions']['axis_unit'];ids=raw['observation_ids']
        if fingerprint(ids)!=entry['observation_ids_sha256']:raise ValueError('OBSERVATION_SCOPE_CHANGED')
        task_id=fingerprint([name,'X',frozen['protocol_version']])
        for representation in ('raw','snv'):
            base_path=PUBLIC/'profiles'/(name+'.'+representation+'.json')
            reference=json.loads(base_path.read_text())
            if reference['status']!='computed':raise ValueError('REFERENCE_REPRESENTATION_UNAVAILABLE')
            transformed=represent(raw,representation)
            for fraction in frozen['fractions']:
                draws=[];receipts=[]
                for number in range(frozen['draws_per_fraction']):
                    draw=component_draw(ids,local['components'],fraction,number,frozen['seed'])
                    contract={'task':{'task_id':task_id},'freeze_id':frozen['freeze_id'],'phase':'structural-resampling',
                        'representation':representation,'fraction':fraction,'draw':number,
                        'selected_indices_sha256':fingerprint(draw['indices']),'component_map_sha256':entry['component_map_sha256'],
                        'input_csv_sha256':entry['input_csv_sha256'],'reference_sha256':digest(base_path),
                        'runner_sha256':runner_sha,'bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py'),
                        'binary_sha256':digest(binary),'library_sha256':digest(library)}
                    def run(folder):
                        start=time.perf_counter()
                        q={**transformed,'observation_ids':draw['observation_ids'],'spectra':[transformed['spectra'][i] for i in draw['indices']]}
                        try:
                            value=native_profile(q,representation,binary,library)
                            result=state({k:v for k,v in value.items() if k not in ('transport_only_scores','neighborhoods')})
                            result.update(pca_fits=1,hdbscan_attempts=2)
                        except RuntimeError as error:
                            if 'ZERO_SPECTRAL_VARIANCE' not in str(error):raise
                            result=state(reason=str(error),status='failed');result.update(pca_fits=1,hdbscan_attempts=0)
                        result.update(draw=number,selected_indices=draw['indices'],n_selected_units=len(draw['selected_units']),
                            selected_units_sha256=fingerprint(draw['selected_units']),elapsed_seconds=time.perf_counter()-start)
                        return result
                    plan={'inputs':[{'path':str(path),'sha256':entry['input_csv_sha256'],'bytes':path.stat().st_size}],
                        'scratch_bytes':4096,'evidence_bytes':65536,'expected_fits':3,'expected_permutations':0,
                        'uncertainty':'One complete-selected-unit PCA refit, two native HDBSCAN attempts, no neighborhoods or models. Existing entire source cache retained; no X copies stored.'}
                    receipt,value=store.run(contract,'P3',plan,run)
                    if value is None:raise RuntimeError(receipt)
                    draws.append(value);receipts.append({'execution_id':receipt['execution_id'],'sha256':receipt['sha256'],
                        'artifact':receipt['artifact'],'cache_hit':receipt['cache_hit'],'seconds':receipt['duration_seconds']})
                    print(json.dumps({'dataset':name,'representation':representation,'fraction':fraction,'draw':number,
                        'status':value['status'],'cache_hit':receipt['cache_hit'],'bytes':receipt['bytes']}),flush=True)
                summary_contract={'task':{'task_id':task_id},'phase':'structural-stability-summary','representation':representation,
                    'fraction':fraction,'draw_artifact_hashes':[r['sha256'] for r in receipts],
                    'reference_sha256':digest(base_path),'runner_sha256':runner_sha,
                    'bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py'),'library_sha256':digest(library)}
                def summarize(folder):
                    value=stability_summary(reference['value'],draws,ids,entry['n_resampling_units'],entry['resampling_scope'])
                    value.update({'protocol_version':frozen['protocol_version'],'dataset_id':name,'representation':representation,
                        'fraction':fraction,'draw_receipts':receipts,'reference_sha256':digest(base_path),
                        'pca_fits':sum(d['pca_fits'] for d in draws),'hdbscan_attempts':sum(d['hdbscan_attempts'] for d in draws),
                        'elapsed_seconds':sum(d['elapsed_seconds'] for d in draws),'target_accessed':False})
                    return value
                plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':262144,'expected_fits':0,'expected_permutations':0,
                    'uncertainty':'Native shared-support ARI and summaries; bounded prespecified pair-panel bookkeeping. No refits.'}
                receipt,value=store.run(summary_contract,'P4',plan,summarize)
                if value is None:raise RuntimeError(receipt)
                export(store,receipt,PUBLIC/'stability'/(name+'.'+representation+'.'+str(fraction)+'.json'))
                atomic_json(ROOT/'stability-receipts'/(name+'.'+representation+'.'+str(fraction)+'.json'),receipt)


if __name__=='__main__':main()
