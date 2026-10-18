"""Selected flat-source X and explicit keys only; no MATLAB/reference decoding."""
import json
from pathlib import Path
import pandas as pd
from alpha13_common import ROOT,PUBLIC,run,publish
from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.keyed_source_x import read_keyed_x,verify_keyed_x
from nirs4all_domains.storage import digest,fingerprint


def main():
    source=Path('D:/R/R projects/DeLeTe_BACON/data/regression/TABLET/NIRdata_tablets.txt')
    leaf=Path('D:/VS projects/nirs_db_vf/standardized_datasets/ucph_tablet_nir')
    admission=json.loads((PUBLIC/'source-admissions.json').read_text())['admissions'][0]
    assert admission['specification']['dataset_id']=='ucph_tablet_nir' and admission['status']=='admitted_x_only'
    files=[source,leaf/'X.csv',leaf/'M.csv']
    contract={'task':{'task_id':fingerprint(['alpha13','tablet-original-observation-keys'])},'phase':'additional-source-key-audit',
        'source_hashes':{p.name:digest(p) for p in files},'runner_sha256':digest(__file__),
        'projection_bridge_sha256':digest('bridges/python/nirs4all_domains/keyed_source_x.py'),
        'protocol_sha256':digest('docs/ALPHA13_ORIGINAL_KEY_AUDIT_PROTOCOL.md'),'source_admission_id':admission['admission_id']}
    def audit(folder):
        header=pd.read_csv(source,sep=';',nrows=0).columns.tolist();axis_headers=header[4:]
        assert header[:4]==['Unnamed: 0','active (%w/w)','Type','Scale'] and len(axis_headers)==404
        original=read_keyed_x(source,header[0],axis_headers,'cm-1')
        canonical=spectral_request(leaf/'X.csv','X');canonical['axis_unit']='cm-1'
        keys=pd.read_csv(leaf/'M.csv',sep=';',usecols=['observation_id','source_sample_id'],dtype=str)
        assert not keys.observation_id.duplicated().any()
        mapping=dict(zip(keys.observation_id,keys.source_sample_id,strict=True))
        proof=verify_keyed_x(original,canonical,mapping)
        return {'protocol_version':'domains.alpha13.source_key_transport.v0.1','dataset_id':'ucph_tablet_nir',
            'original_x_correspondence':proof,'source_hashes':contract['source_hashes'],'source_kind':'Existing original UCPH flat-text cache, documented by canonical source script',
            'selected_original_columns':['original source key','404 spectral bands'],'excluded_columns':['active (%w/w)','Type','Scale'],
            'resampling_protocol_changed':False,'model_admission_changed':False,
            'reference_ownership':{'status':'unavailable','reason':'ORIGINAL_ASSAY_BATCH_AND_PHYSICAL_DEPENDENCY_OWNERSHIP_NOT_VERIFIED','value':None},
            'new_pca_fits':0,'supervised_fits':0,'test_target_accessed':False,
            'scope':'Additional source-key correspondence, after frozen observation-conditional resampling; no biological/assay independence is inferred.'}
    plan={'inputs':[{'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size} for p in files],
        'scratch_bytes':4096,'evidence_bytes':65536,'expected_fits':0,'expected_permutations':0,
        'uncertainty':'Pandas usecols materializes original key and bands only, plus canonical declared key metadata. Exact value/axis equality; no numerical model or target cells.'}
    store,receipt,value=run(contract,'P0',plan,audit);publish(store,receipt,'sources/tablet-original-key-audit.json')
    print(json.dumps(value['original_x_correspondence']))


if __name__=='__main__':main()
