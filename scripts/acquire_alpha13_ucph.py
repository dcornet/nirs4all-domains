"""Rights-scoped original archives through Datasets; headers only, no target cells."""
import io
import json
from pathlib import Path
import zipfile
from alpha13_common import ROOT,PUBLIC,run,publish
from nirs4all_domains.storage import atomic_json,digest,fingerprint

SOURCES=[('tablet','ucph_tablet_nir','https://ucphchemometrics.com/tablet/',
    'https://sid.erda.dk/share_redirect/HbpPvIEvTg/Tablets.zip','Tablets.zip',3822359),
    ('soil','ohpl_soil_nir','https://ucphchemometrics.com/soilnir/',
    'https://sid.erda.dk/share_redirect/cFmELMw2C6/NIR%20Soil.zip','NIR Soil.zip',431935)]


def main():
    from nirs4all_datasets._acquire import retrieve_raw
    from scipy.io import whosmat
    rights=ROOT/'source/ucph_rights.txt'
    assert 'available for public use' in rights.read_text(encoding='utf-8')
    for key,dataset,page,url,name,size in SOURCES:
        source={'dataset_id':dataset,'source_page':page,'download_url':url,'archive_name':name,'expected_bytes':size,
            'rights_basis':{'url':'https://ucphchemometrics.com/datasets/','observed_page_sha256':digest(rights),
                'scope':'Original downloadable UCPH material, local analysis and attributed nonreconstructive statistics; no raw redistribution.'}}
        contract={'task':{'task_id':fingerprint(['alpha13',dataset,'original-acquisition'])},'phase':'original-public-acquisition',
            'source':source,'runner_sha256':digest(__file__),'protocol_version':'domains.alpha13.source_admission.v0.1'}
        plan={'inputs':[{'sha256':fingerprint([url,size]),'bytes':size}],'scratch_bytes':65536,'evidence_bytes':32768,
            'expected_fits':0,'expected_permutations':0,'uncertainty':'Pinned official listing size; byte/ZIP-header inspection only, no decoded target or X matrices. No official checksum supplied.'}
        def acquire(folder):
            route={'id':'ucph-original-v1','provider':'http','method':'raw_retrieve','access':'open','locator':page,
                'resources':[{'id':'archive','role':'raw','required':True,'selector':{'kind':'direct_url','value':url},
                    'file_name':name,'format':'zip','size':size,'unpack':{'archive':False,'members':[]}}]}
            result=retrieve_raw({'dataset_id':'alpha13-original-'+key,'route':route},
                {'cache_dir':str((ROOT/'datasets-cache').resolve()),'timeout_secs':90,'max_total_bytes':size})
            if not result['ok']:raise ValueError(result)
            resource,=result['resources'];path=Path(resource['path']);assert path.stat().st_size==size
            members=[]
            with zipfile.ZipFile(path) as archive:
                assert sum(i.file_size for i in archive.infolist())<24*1024*1024
                for item in archive.infolist():
                    entry={'name':item.filename,'uncompressed_bytes':item.file_size,'compressed_bytes':item.compress_size}
                    if item.filename.lower().endswith('.mat'):
                        entry['top_level_variables']=[{'name':n,'shape':list(shape),'matlab_class':kind} for n,shape,kind in whosmat(io.BytesIO(archive.read(item))) ]
                    members.append(entry)
            return {'source':source,'relative_path':path.resolve().relative_to(Path.cwd()).as_posix(),'sha256':digest(path),
                'bytes':size,'provider':'Datasets 0.3.11 retrieve_raw','official_checksum_available':False,'members':members,
                'decoded_target_cells':0,'test_target_accessed':False,'model_fits':0}
        store,receipt,value=run(contract,'P1',plan,acquire)
        publish(store,receipt,'sources/'+key+'-archive.json');atomic_json(ROOT/(key+'-origin.json'),value)
        print(json.dumps({'dataset':dataset,'cache_hit':receipt['cache_hit'],'members':value['members']}),flush=True)


if __name__=='__main__':main()
