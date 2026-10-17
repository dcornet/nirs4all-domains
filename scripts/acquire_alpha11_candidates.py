"""Original open crop/litter files, bounded and cached by public Datasets API."""
import json
from pathlib import Path
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint


def main():
    root=Path('.audit/alpha11')
    policy=json.loads(Path('configs/bank/storage-policy-alpha11.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',root/'scratch',root/'evidence',Path.cwd(),policy)
    for name,files,upper in [('crops',['BNL_2015glasshouse_SVC_Averaged_Interpolated_Spectra.csv','BNL_2015glasshouse_leaf_traits.csv'],4500000),
                             ('litter',['intact_spec.csv','ground_spec.csv','metadata_fields.csv'],13000000)]:
        meta=root/'source'/(name+'.json');data=json.loads(meta.read_text())['result']
        if data['license_id'] not in ['odc-by','cc-by']:raise ValueError('SOURCE_RIGHTS_CHANGED')
        selected=[r for r in data['resources'] if r['name'] in files]
        if len(selected)!=len(files):raise ValueError('ORIGINAL_RESOURCES_MISSING')
        contract={'task':{'task_id':fingerprint(['alpha11',name,'original-acquisition'])},'metadata_sha256':digest(meta),
                  'runner_sha256':digest(__file__),'protocol':'domains.alpha11.original_admission.v0.1'}
        plan={'inputs':[{'sha256':fingerprint([r['url'] for r in selected]),'bytes':upper}], 'scratch_bytes':4096,
              'evidence_bytes':16384,'expected_fits':0,'expected_permutations':0,'uncertainty':'Provider cache reuse; upper byte bound, no extraction or numerical fitting.'}
        def acquire(folder):
            from nirs4all_datasets._acquire import retrieve_raw
            route={'id':'original-v1','provider':'ecosis','method':'raw_retrieve','access':'open','locator':'https://data.ecosis.org/dataset/'+data['id'],
                   'resources':[{'id':r['id'],'role':'raw','required':True,'selector':{'kind':'direct_url','value':r['url']},
                    'file_name':r['name'],'format':'csv','unpack':{'archive':False,'members':[]}} for r in selected]}
            result=retrieve_raw({'dataset_id':'alpha11-'+name,'route':route},{'cache_dir':str((root/'datasets-cache').resolve()),
                                'timeout_secs':90,'max_total_bytes':upper})
            if not result['ok']:raise ValueError(result)
            return {'provider':'Datasets 0.3.11 retrieve_raw','license_id':data['license_id'],
                    'files':[{'name':Path(r['path']).name,'path':Path(r['path']).resolve().relative_to(Path.cwd()).as_posix(),
                              'sha256':digest(r['path']),'bytes':Path(r['path']).stat().st_size} for r in result['resources']],
                    'model_fits':0,'test_target_accessed':False}
        receipt,value=store.run(contract,'P1',plan,acquire)
        if value is None:raise RuntimeError(receipt)
        atomic_json(root/(name+'-origin.json'),value)
        print(json.dumps({'candidate':name,'receipt_status':receipt['status'],'cache_hit':receipt['cache_hit'],**value}),flush=True)


if __name__=='__main__':main()
