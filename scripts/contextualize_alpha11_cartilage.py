"""Original-audited joint labels versus descriptive X groups; no target or donor fit."""
import hashlib
import json
from pathlib import Path
from nirs4all_domains.adaptive import partition_agreement
from nirs4all_domains.bank import file_plan
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint


def main():
    import pandas as pd
    name='cartilage_spectroscopy_scientificdata_nir';root=Path('.audit/alpha11');public=Path('docs/benchmarks/alpha11')
    leaf=Path(r'D:\VS projects\nirs_db_vf\standardized_datasets')/name
    record=json.loads((public/'public'/(name+'.json')).read_text());profile=record['structural_susceptibility']
    contract={'task':{'task_id':fingerprint([name,'X','domains.adaptive_structure.v0.1'])},'protocol':'domains.alpha11.cartilage_x_metadata.v0.1',
              'input_profile_sha256':fingerprint(profile),'metadata_sha256':digest(leaf/'M.csv'),'runner_sha256':digest(__file__),
              'original_key_proof_sha256':digest('docs/benchmarks/alpha10/cartilage-admission.json')}
    def run(folder):
        ids=pd.read_csv(leaf/'X.csv',sep=';',usecols=['observation_id'],dtype=str).observation_id.tolist()
        if hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()!=profile['observation_ids_sha256']:raise ValueError('SCOPED_X_ID_ORDER_CHANGED')
        frame=pd.read_csv(leaf/'M.csv',sep=';',dtype=str).set_index('observation_id')
        if frame.index.duplicated().any() or set(frame.index)!=set(ids):raise ValueError('KEYED_METADATA_REQUIRED')
        fields={}
        labels=list(map(str,profile['cluster_settings'][0]['value']['labels']))
        for field in ['joint_id','bone_type']:
            values=[frame.at[s,field] for s in ids]
            fields[field]={'matched_observations':len(ids),'missing':0,'n_declared_levels':len(set(values)),
                           'ari_including_hdbscan_noise':partition_agreement(labels,values),
                           'metadata_source':'Derived M original-key correspondence audited in alpha10; joint identity is not donor identity'}
        return {'fields':fields,'scope':'2605 acquisitions, not independent biological samples; no target/assay/donor inference',
                'model_admission':'pending donor and assay ownership','test_target_accessed':False}
    policy=json.loads(Path('configs/bank/storage-policy-alpha11.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',root/'scratch',root/'evidence',Path.cwd(),policy)
    receipt,result=store.run(contract,'P2',file_plan(leaf/'M.csv',4096,32768),run)
    if result is None:raise RuntimeError(receipt)
    atomic_json(public/'metadata'/(name+'.json'),result);print(json.dumps({'status':receipt['status'],'cache_hit':receipt['cache_hit']}))


if __name__=='__main__':main()
