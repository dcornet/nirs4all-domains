"""Keyed metadata agreement and original crop XY; never infer labels from clusters."""
import csv
import argparse
import hashlib
import json
from pathlib import Path
import time

from nirs4all_domains.adaptive import association, partition_agreement
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint

ROOT=Path('.audit/alpha11');PUBLIC=Path('docs/benchmarks/alpha11')
LEAVES=Path(r'D:\VS projects\nirs_db_vf\standardized_datasets')


def main():
    import pandas as pd
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--crop-only',action='store_true');args=parser.parse_args()
    policy=json.loads(Path('configs/bank/storage-policy-alpha11.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
    for path in sorted((PUBLIC/'public').glob('*.json')):
        if args.crop_only:break
        original=json.loads(path.read_text());name=original['dataset_id'];profile=original['structural_susceptibility']
        if name.startswith('ecosis_tabletop'):
            followup=json.loads((PUBLIC/'pddl-followup.json').read_text());profile=followup['report']
        if not profile or not name.startswith('ecosis'):continue
        matrix=LEAVES/name/'X.csv';meta=LEAVES/name/'M.csv'
        contract={'task':{'task_id':fingerprint([name,'X','domains.adaptive_structure.v0.1'])},'protocol':'domains.alpha11.metadata_agreement.v0.1',
            'input_profile_sha256':fingerprint(profile),'matrix_sha256':digest(matrix),'metadata_sha256':digest(meta),
            'runner_sha256':digest(__file__),'adapter_sha256':digest('bridges/python/nirs4all_domains/adaptive.py')}
        plan={'inputs':[{'path':str(meta.resolve()),'sha256':digest(meta),'bytes':meta.stat().st_size}],
              'scratch_bytes':4096,'evidence_bytes':65536,'expected_fits':0,'expected_permutations':0,
              'uncertainty':'Native ARI only; original-source metadata semantics remain declared, not independently verified.'}
        def run(folder):
            began=time.perf_counter()
            ids=pd.read_csv(matrix,sep=';',usecols=['observation_id'],dtype=str).observation_id.tolist()
            if hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()!=profile['observation_ids_sha256']:
                raise ValueError('X_LABEL_OBSERVATION_ORDER_DIGEST_DIFFERS')
            m=pd.read_csv(meta,sep=';',dtype=str).fillna('')
            if m.observation_id.duplicated().any() or set(m.observation_id)!=set(ids):raise ValueError('METADATA_EXACT_KEY_SET_REQUIRED')
            keyed=m.set_index('observation_id');primary=profile['cluster_settings'][0]
            if primary['status']!='computed':return {'status':'unavailable','reason':'X_PARTITION_UNAVAILABLE','value':None}
            labels=primary['value']['labels'];fields={}
            for field in ['species','genus','family','site','date','source_plot','source_individual','source_Room_Temp','source_leaf_position','source_pot_medium']:
                if field not in keyed:continue
                selected=[(label,keyed.at[s,field]) for s,label in zip(ids,labels,strict=True) if keyed.at[s,field]]
                levels={r[1] for r in selected}
                if len(levels)<2:continue
                fields[field]={'matched_observations':len(selected),'missing':len(ids)-len(selected),'n_declared_levels':len(levels),
                    'ari_including_hdbscan_noise':partition_agreement([str(r[0]) for r in selected],[r[1] for r in selected]),
                    'metadata_source':'keyed derived M.csv, declared source field; original semantic correspondence not independently established'}
            return {'profile_sha256':fingerprint(profile),'metadata_sha256':digest(meta),'fields':fields,'elapsed_seconds':time.perf_counter()-began,
                'scope':'descriptive agreement with declared metadata; no target or model; cluster stability unqualified in broad screen',
                'test_target_accessed':False}
        receipt,result=store.run(contract,'P2',plan,run)
        if result is None:raise RuntimeError(receipt)
        atomic_json(PUBLIC/'metadata'/(name+'.json'),result)
        print(json.dumps({'metadata':name,'fields':len(result.get('fields',{})),'cache_hit':receipt['cache_hit']}),flush=True)
    name='ecosis_leaf_spectra_structural_and_biochemical_leaf_traits_of_reflectance_nirs'
    origin=json.loads((ROOT/'crops-origin.json').read_text())
    for f in origin['files']:
        if digest(f['path'])!=f['sha256']:raise ValueError('CROP_ORIGINAL_SOURCE_CHANGED')
    contract={'task':{'task_id':fingerprint([name,'X','domains.adaptive_structure.v0.1'])},'protocol':'domains.alpha11.crop_association.v0.1',
              'original':origin,'runner_sha256':digest(__file__),
              'derived_x_sha256':digest(LEAVES/name/'X.csv'),'derived_metadata_sha256':digest(LEAVES/name/'M.csv'),
              'x_profile_sha256':digest(PUBLIC/'public'/(name+'.json'))}
    def crop(folder):
        import numpy as np
        files={f['name']:Path(f['path']) for f in origin['files']}
        with files['BNL_2015glasshouse_leaf_traits.csv'].open() as f:target={r['sample_id']:r for r in csv.DictReader(f)}
        with files['BNL_2015glasshouse_SVC_Averaged_Interpolated_Spectra.csv'].open() as f:
            reader=csv.DictReader(f);axis=[c for c in reader.fieldnames if c.isdigit()];spectra={r['sample_id']:r for r in reader}
        m=pd.read_csv(LEAVES/name/'M.csv',sep=';',dtype=str).fillna('').set_index('observation_id')
        x=pd.read_csv(LEAVES/name/'X.csv',sep=';').set_index('observation_id')
        if set(m.sample_id)!=set(spectra) or len(m)!=len(spectra) or set(x.index)!=set(m.index):raise ValueError('CROP_ORIGINAL_KEY_SET_DIFFERS')
        for obs in x.index:
            key=m.at[obs,'sample_id']
            if not np.array_equal(np.asarray([spectra[key][c] for c in axis],dtype='float32'),x.loc[obs].to_numpy(dtype='float32')):
                raise ValueError('CROP_ORIGINAL_X_FLOAT32_PARITY_FAILED')
        profile=json.loads((PUBLIC/'public'/(name+'.json')).read_text())['structural_susceptibility']
        labels=profile['cluster_settings'][0]['value']['labels'];ids=list(x.index)
        if hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()!=profile['observation_ids_sha256']:
            raise ValueError('CROP_X_LABEL_OBSERVATION_ORDER_DIFFERS')
        selected=[(label,target[m.at[obs,'sample_id']]['N_pc_dry'],m.at[obs,'species']) for obs,label in zip(ids,labels,strict=True)
                  if target[m.at[obs,'sample_id']]['N_pc_dry'] not in ['NA','','NaN']]
        return {'source_id':'X','target':'N_pc_dry','unit':'source nitrogen dry-mass percent','n_spectra':len(spectra),'n_original_trait_rows':len(target),
            'trait_only_keys':sorted(set(target)-set(spectra)),'n_matched_finite_targets':len(selected),'source_hashes':{f['name']:f['sha256'] for f in origin['files']},
            'original_x_keyed_float32_parity':True,'x_partition_target_association':association([str(r[0]) for r in selected],[float(r[1]) for r in selected]),
            'metadata_species_target_association':association([r[2] for r in selected],[float(r[1]) for r in selected]),
            'model_admission':state(reason='ORIGINAL_LEAF_TO_PLANT_AND_ASSAY_BATCH_MAPS_UNAVAILABLE'),
            'scope':'descriptive full permitted source population, no prospective or OOF inference; no retained split is designated for this task',
            'test_target_accessed':False,'reference':'10.1093/jxb/erz061; paper describes repeated leaf sampling over time; sample_id is a leaf, not a verified plant key'}
    plan={'inputs':[{'path':f['path'],'sha256':f['sha256'],'bytes':f['bytes']} for f in origin['files']],
        'scratch_bytes':4096,'evidence_bytes':65536,'expected_fits':0,'expected_permutations':0,'uncertainty':'Native descriptive association on original leaf-keyed nitrogen only.'}
    receipt,result=store.run(contract,'P2',plan,crop)
    if result is None:raise RuntimeError(receipt)
    atomic_json(PUBLIC/'crop-association.json',result)
    print(json.dumps({'crops':'computed','n_matched':result['n_matched_finite_targets'],'model':result['model_admission']['reason']}))


if __name__=='__main__':main()
