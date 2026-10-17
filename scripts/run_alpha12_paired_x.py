"""Freeze/run one original-keyed same-object X-only preparation comparison."""
import argparse
import json
from pathlib import Path
import time
from run_alpha12_profiles import export
from nirs4all_domains.dependence import state
from nirs4all_domains.paired_x import read_litter_view,match_litter_views
from nirs4all_domains.storage import StageStore,atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import compact_profile,compare_partition,native_profile,neighborhood_agreement,query_design,represent

ROOT=Path('.audit/alpha12');PUBLIC=Path('docs/benchmarks/alpha12')
PROTOCOL='domains.alpha12.paired_x.v0.1'


def inputs():
    origin=json.loads(Path('.audit/alpha11/litter-origin.json').read_text())
    files=[next(f for f in origin['files'] if f['name']==name) for name in ['intact_spec.csv','ground_spec.csv']]
    assert origin['license_id']=='cc-by' and all(digest(f['path'])==f['sha256'] for f in files)
    parents=[read_litter_view(f['path'],'litter-original:'+f['name']) for f in files]
    views,proof=match_litter_views(*parents)
    assert proof['parent_observation_counts']==[322,321] and proof['n_matched']==321
    assert proof['left_only']==['GEN_1_BEPA_7'] and not proof['right_only']
    return files,views,proof


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['freeze','run']);args=parser.parse_args()
    files,views,proof=inputs()
    frozen={'protocol_version':PROTOCOL,'files':[{k:f[k] for k in ['name','bytes','sha256']} for f in files],
        'axis_sha256':fingerprint(views[0]['axis']),'paired_ids_sha256':fingerprint(views[0]['observation_ids']),
        'key_proof':proof,'protocol_sha256':digest('docs/ALPHA12_PAIRED_X_PROTOCOL.md'),
        'adapter_sha256':digest('bridges/python/nirs4all_domains/paired_x.py'),
        'input_population_scope':'321 explicitly keyed paired objects; intact full-source 322 remains a separate primary profile.',
        'target_cells_materialized':False,'selection_uses_model_performance':False}
    frozen['freeze_id']=fingerprint(frozen);path=PUBLIC/'paired-x-freeze.json'
    if args.command=='freeze':
        if path.exists() and json.loads(path.read_text())!=frozen:raise ValueError('PAIRED_X_FREEZE_CHANGED')
        atomic_json(path,frozen);print(json.dumps(proof));return
    assert json.loads(path.read_text())==frozen
    policy=json.loads(Path('configs/bank/storage-policy-alpha12.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
    binary=Path('target/debug/n4domains.exe').resolve()
    from n4m._ffi import library_path
    library=Path(library_path()).resolve();profiles={};receipts=[]
    task_id=fingerprint([frozen['freeze_id'],PROTOCOL])
    for view_name,view,file in zip(['intact','ground'],views,files,strict=True):
        profiles[view_name]={}
        for representation in ('raw','snv'):
            contract={'task':{'task_id':task_id},'phase':'paired-x-view','freeze_id':frozen['freeze_id'],
                'view':view_name,'representation':representation,'runner_sha256':digest(__file__),
                'bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py'),
                'adapter_sha256':frozen['adapter_sha256'],'binary_sha256':digest(binary),'library_sha256':digest(library)}
            def run(folder):
                start=time.perf_counter();q=represent(view,representation);design=query_design(q['observation_ids'],len(q['axis']))
                value=compact_profile(native_profile(q,representation,binary,library,design),design)
                value.update(source_population_scope=frozen['input_population_scope'],parent_observation_counts=proof['parent_observation_counts'],
                    physical_unit='original keyed litter sample bag, possibly composite leaves',
                    elapsed_seconds=time.perf_counter()-start,pca_fits=1,hdbscan_attempts=2)
                return value
            plan={'inputs':[{'path':file['path'],'sha256':file['sha256'],'bytes':file['bytes']}],
                'scratch_bytes':4096,'evidence_bytes':1048576,'expected_fits':3,'expected_permutations':0,
                'uncertainty':'One original paired view, native PCA and two HDBSCAN attempts; no target fields or model. 321 complete-axis paired objects; parent populations preserved.'}
            receipt,value=store.run(contract,'P2',plan,run)
            if value is None:raise RuntimeError(receipt)
            export(store,receipt,PUBLIC/'paired'/(view_name+'.'+representation+'.json'))
            profiles[view_name][representation]=value;receipts.append(receipt)
            print(json.dumps({'view':view_name,'representation':representation,'cache_hit':receipt['cache_hit'],'seconds':value['elapsed_seconds']}),flush=True)
    contract={'task':{'task_id':task_id},'phase':'paired-x-comparison','freeze_id':frozen['freeze_id'],
        'view_artifact_hashes':[r['sha256'] for r in receipts],'runner_sha256':digest(__file__),
        'bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py'),'library_sha256':digest(library)}
    def compare(folder):
        output={}
        for representation in ('raw','snv'):
            a,b=(profiles[k][representation] for k in ['intact','ground'])
            output[representation]={'pca':[v['pca'] for v in (a,b)],
                'partition_comparisons':[compare_partition(views[0]['observation_ids'],a['cluster_settings'][i]['value']['labels'],
                    views[1]['observation_ids'],b['cluster_settings'][i]['value']['labels']) for i in range(2)],
                'full_axis_neighbors':neighborhood_agreement(a['neighborhoods']['value']['full_axis'],b['neighborhoods']['value']['full_axis'])}
        return {'protocol_version':PROTOCOL,'freeze_id':frozen['freeze_id'],'key_proof':proof,'comparisons':output,
            'pca_fits':4,'hdbscan_attempts':8,'model_fits':0,'target_cells_materialized':False,
            'interpretation':'Same-object preparation differences under separately fitted descriptive representations; not new-object generalization or a train-fitted transfer test.',
            'historical_support_probe_ref':{'path':'docs/benchmarks/alpha11/transfer-geometry.json','sha256':digest('docs/benchmarks/alpha11/transfer-geometry.json')},
            'limitations':['Unknown tree/trap/assay closure prevents biological independence claims.',
                'Original full-precision CSV views and canonical float32 views have separate content identities.',
                'Historical retained-X support probe is post-response explanatory evidence with unchanged train-only fitted state.']}
    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':262144,'expected_fits':0,'expected_permutations':0,
        'uncertainty':'Native ARI and identity-neighbor comparisons on matched original IDs. No refits.'}
    receipt,value=store.run(contract,'P4',plan,compare)
    if value is None:raise RuntimeError(receipt)
    export(store,receipt,PUBLIC/'paired-x-comparison.json');atomic_json(ROOT/'paired-x-receipts.json',receipts+[receipt])


if __name__=='__main__':main()
