"""Resumable serial full-source raw/SNV profiles; target tables are never opened."""
import argparse
import json
import os
from pathlib import Path
import time

import pandas as pd
from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import StageStore,atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import compact_profile,factor_profile,native_profile,represent

ROOT=Path('.audit/alpha12');PUBLIC=Path('docs/benchmarks/alpha12')


def export(store,receipt,destination):
    """New portable exports share immutable new-stage bytes; historical paths excluded."""
    origin=store.evidence/receipt['artifact'];destination=Path(destination)
    assert destination.is_relative_to(PUBLIC) and digest(origin)==receipt['sha256']
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        if digest(destination)!=receipt['sha256']:raise ValueError('EXISTING_PROFILE_CHANGED')
        return
    temporary=destination.with_name(destination.name+'.shared')
    if temporary.exists():
        if digest(temporary)!=receipt['sha256']:raise ValueError('INTERRUPTED_EXPORT_CONTENT_MISMATCH')
    else:os.link(origin,temporary)
    os.replace(temporary,destination)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only');args=parser.parse_args()
    frozen=json.loads((PUBLIC/'input-freeze.json').read_text());locators=json.loads((ROOT/'input-locators.json').read_text())
    assert frozen['freeze_id']==fingerprint({k:v for k,v in frozen.items() if k!='freeze_id'})
    policy=json.loads(Path('configs/bank/storage-policy-alpha12.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',ROOT/'scratch',ROOT/'evidence',Path.cwd(),policy)
    binary=Path('target/debug/n4domains.exe').resolve()
    from n4m._ffi import library_path
    library=Path(library_path()).resolve()
    for entry in frozen['entries']:
        name=entry['dataset_id']
        if entry['status']!='computed' or (args.only and args.only not in name):continue
        local=locators[name];matrix=Path(local['matrix']);metadata=Path(local['metadata'])
        assert digest(matrix)==entry['input_csv_sha256'] and digest(metadata)==entry['metadata_sha256']
        for representation in ('raw','snv'):
            contract={'task':{'task_id':fingerprint([name,'X',frozen['protocol_version']])},
                'freeze_id':frozen['freeze_id'],'input_csv_sha256':entry['input_csv_sha256'],
                'metadata_sha256':entry['metadata_sha256'],'representation':representation,
                'query_design_sha256':fingerprint(entry['query_design']),
                'runner_sha256':digest(__file__),'bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py'),
                'binary_sha256':digest(binary),'library_sha256':digest(library),'phase':'representation-reference'}
            plan={'inputs':[{'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size} for p in (matrix,metadata)],
                'scratch_bytes':4096,'evidence_bytes':1048576,'expected_fits':3,'expected_permutations':0,
                'uncertainty':'One complete-source PCA and two HDBSCAN attempts. Streamed X; <=750M full-axis products, unchanged <=250M per native provider call. Estimated combined peak memory <1.5 GiB; no OS quota.'}
            def run(folder):
                begin=time.perf_counter()
                original=spectral_request(matrix,entry['source_id'],entry['identity_evidence']);original['axis_unit']=entry['source_dimensions']['axis_unit']
                assert fingerprint(original['axis'])==entry['axis_sha256'] and fingerprint(original['observation_ids'])==entry['observation_ids_sha256']
                try: transformed=represent(original,representation)
                except ValueError as error:
                    return {'status':'unavailable','reason':str(error),'value':None,'pca_fits':0,'hdbscan_attempts':0,'elapsed_seconds':time.perf_counter()-begin}
                result=native_profile(transformed,representation,binary,library,entry['query_design'])
                fields=entry['available_metadata_fields']
                keyed=pd.read_csv(metadata,sep=';',usecols=['observation_id',*fields],dtype=str).fillna('').set_index('observation_id')
                factors={};primary=result['cluster_settings'][0]
                if primary['status']=='computed':
                    for field in fields:
                        values={s:(keyed.at[s,field] or None) for s in original['observation_ids']}
                        factors[field]=factor_profile(primary['value']['labels'],result['transport_only_scores'],values,original['observation_ids'],
                            {'field':field,'metadata_sha256':entry['metadata_sha256'],'join':'exact observation_id',
                             'semantics_independently_verified':name.startswith('cartilage') and field in ('joint_id','bone_type'),
                             'semantic_scope':'Original joint/bone correspondence audited; donor identity unknown.' if name.startswith('cartilage') else 'Declared original-source field; independent semantic validation not asserted.'})
                result=compact_profile(result,entry['query_design'])
                result['metadata_agreement']=state(factors) if factors else state(reason='NO_ELIGIBLE_METADATA_FACTOR_PARTITION')
                result['input_source_sha256']=entry['input_csv_sha256']
                result['scope']='Full declared source, all bands; descriptive X-only representation, not prospective train-reference evaluation.'
                result['elapsed_seconds']=time.perf_counter()-begin;result['pca_fits']=1;result['hdbscan_attempts']=2
                return state(result)
            receipt,result=store.run(contract,'P2',plan,run)
            log={'dataset':name,'representation':representation,'stage_status':receipt['status'],
                'reason':receipt['reason'],'cache_hit':receipt['cache_hit'],'duration_seconds':receipt.get('duration_seconds')}
            atomic_json(ROOT/'receipts'/(name+'.'+representation+'.json'),receipt)
            if result is not None:
                export(store,receipt,PUBLIC/'profiles'/(name+'.'+representation+'.json'))
                log['scientific_status']=result['status'];log['bytes']=receipt['bytes']
            print(json.dumps(log),flush=True)
            if result is None:raise RuntimeError(receipt['reason'])


if __name__=='__main__':main()
