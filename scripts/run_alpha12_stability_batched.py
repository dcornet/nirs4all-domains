"""Same frozen five remaining experiments; bounded checkpointed 20-draw stages."""
import json
from pathlib import Path
import time
from run_alpha12_profiles import export
from run_alpha12_stability import SENTINELS
from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import StageStore,atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import component_draw,native_profile,represent,stability_summary
from nirs4all_domains.unsupervised_checkpoint import recover_draw,checkpoint_draw

ROOT=Path('.audit/alpha12');PUBLIC=Path('docs/benchmarks/alpha12')


def main():
    frozen=json.loads((PUBLIC/'input-freeze.json').read_text());locators=json.loads((ROOT/'input-locators.json').read_text())
    review=json.loads((ROOT/'sentinel-cost-review.json').read_text())
    if not review['remaining_prespecified_cases_admitted'] or review['remaining_driver_sha256']!=digest(__file__):
        raise ValueError('MEASURED_SENTINEL_COST_REVIEW_REQUIRED')
    policy=json.loads(Path('configs/bank/storage-policy-alpha12.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
    binary=Path('target/debug/n4domains.exe').resolve()
    from n4m._ffi import library_path
    library=Path(library_path()).resolve()
    runtime={'runner_sha256':digest(__file__),'bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py'),
        'checkpoint_sha256':digest('bridges/python/nirs4all_domains/unsupervised_checkpoint.py'),
        'binary_sha256':digest(binary),'library_sha256':digest(library)}
    for entry in frozen['entries']:
        name=entry['dataset_id']
        if not entry['stability_selected'] or name in SENTINELS:continue
        local=locators[name];path=Path(local['matrix'])
        assert digest(path)==entry['input_csv_sha256'] and fingerprint(local['components'])==entry['component_map_sha256']
        raw=spectral_request(path,entry['source_id'],entry['identity_evidence']);raw['axis_unit']=entry['source_dimensions']['axis_unit'];ids=raw['observation_ids']
        assert fingerprint(ids)==entry['observation_ids_sha256']
        task_id=fingerprint([name,'X',frozen['protocol_version']])
        for representation in ('raw','snv'):
            reference_path=PUBLIC/'profiles'/(name+'.'+representation+'.json');reference=json.loads(reference_path.read_text())
            if reference['status']!='computed':raise ValueError('REFERENCE_REPRESENTATION_UNAVAILABLE')
            transformed=represent(raw,representation)
            for fraction in frozen['fractions']:
                selected=[component_draw(ids,local['components'],fraction,n,frozen['seed']) for n in range(frozen['draws_per_fraction'])]
                contract={'task':{'task_id':task_id},'freeze_id':frozen['freeze_id'],'phase':'structural-resampling-batch',
                    'transport_protocol':'domains.alpha12.batched_resume.v0.1','representation':representation,'fraction':fraction,
                    'input_csv_sha256':entry['input_csv_sha256'],'component_map_sha256':entry['component_map_sha256'],
                    'reference_sha256':digest(reference_path),'selected_indices_sha256':fingerprint([d['indices'] for d in selected]),**runtime}
                def run(folder):
                    draws=[];reused=0;start=time.perf_counter()
                    for number,draw in enumerate(selected):
                        draw_contract={**contract,'draw':number,'selected_indices_sha256':fingerprint(draw['indices'])}
                        result=recover_draw(folder.parent,number,draw_contract)
                        recovered=result is not None
                        if result is not None:reused+=1
                        else:
                            begin=time.perf_counter()
                            q={**transformed,'observation_ids':draw['observation_ids'],'spectra':[transformed['spectra'][i] for i in draw['indices']]}
                            try:
                                value=native_profile(q,representation,binary,library)
                                result=state({k:v for k,v in value.items() if k not in ('transport_only_scores','neighborhoods')})
                                result.update(pca_fits=1,hdbscan_attempts=2)
                            except RuntimeError as error:
                                if 'ZERO_SPECTRAL_VARIANCE' not in str(error):raise
                                result=state(reason=str(error),status='failed');result.update(pca_fits=1,hdbscan_attempts=0)
                            result.update(draw=number,selected_indices=draw['indices'],n_selected_units=len(draw['selected_units']),
                                selected_units_sha256=fingerprint(draw['selected_units']),elapsed_seconds=time.perf_counter()-begin)
                            checkpoint_draw(folder/('draw-'+str(number)+'.json'),draw_contract,result)
                        draws.append(result)
                        print(json.dumps({'dataset':name,'representation':representation,'fraction':fraction,'draw':number,
                            'status':result['status'],'partial_checkpoint_reused':recovered}),flush=True)
                    return {'draws':draws,'reused_partial_draws':reused,'elapsed_seconds':time.perf_counter()-start,
                        'unique_pca_fits':sum(d['pca_fits'] for d in draws),'unique_hdbscan_attempts':sum(d['hdbscan_attempts'] for d in draws),
                        'target_accessed':False,'model_fits':0}
                plan={'inputs':[{'path':str(path),'sha256':entry['input_csv_sha256'],'bytes':path.stat().st_size}],
                    'scratch_bytes':655360,'evidence_bytes':655360,'expected_fits':60,'expected_permutations':0,
                    'uncertainty':'20 frozen draws, each one PCA and two HDBSCAN attempts. Compact checksummed partial draw prefixes, no X storage. Identical science; one serial reservation.'}
                receipt,batch=store.run(contract,'P3',plan,run)
                if batch is None:raise RuntimeError(receipt)
                summary_contract={'task':{'task_id':task_id},'phase':'batched-structural-stability-summary',
                    'representation':representation,'fraction':fraction,'batch_sha256':receipt['sha256'],**runtime}
                def summarize(folder):
                    result=stability_summary(reference['value'],batch['draws'],ids,entry['n_resampling_units'],entry['resampling_scope'])
                    result.update({'protocol_version':frozen['protocol_version'],'dataset_id':name,'representation':representation,
                        'fraction':fraction,'batch_receipt':{'sha256':receipt['sha256'],'artifact':receipt['artifact']},
                        'reference_sha256':digest(reference_path),'pca_fits':batch['unique_pca_fits'],
                        'hdbscan_attempts':batch['unique_hdbscan_attempts'],'elapsed_seconds':sum(d['elapsed_seconds'] for d in batch['draws']),
                        'target_accessed':False})
                    return result
                summary_plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':262144,'expected_fits':0,'expected_permutations':0,
                    'uncertainty':'Native shared-support ARI and summary; prespecified sampled pair panel. No refits.'}
                summary_receipt,result=store.run(summary_contract,'P4',summary_plan,summarize)
                if result is None:raise RuntimeError(summary_receipt)
                export(store,summary_receipt,PUBLIC/'stability'/(name+'.'+representation+'.'+str(fraction)+'.json'))
                atomic_json(ROOT/'stability-batch-receipts'/(name+'.'+representation+'.'+str(fraction)+'.json'),
                    {'batch':receipt,'summary':summary_receipt})


if __name__=='__main__':main()
