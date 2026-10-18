"""Bounded original EcoSIS metadata audit only; never retrieves source resources.

Original license evidence can establish source rights; it does not settle
canonical correspondence, extra contracts or scientific population independence.
No status is automatically upgraded to executable or publicly publishable.
"""
import json
from pathlib import Path
import urllib.parse
import urllib.request

from nirs4all_domains.privacy import PrivateStore, opaque_id
from nirs4all_domains.storage import atomic_json,digest


def main():
    config=json.loads(Path('.audit/alpha14/private-root.json').read_text())
    store=PrivateStore(config['root'],Path.cwd());root=store.root/'source-rights';root.mkdir(exist_ok=True)
    pinned=json.loads(Path('docs/benchmarks/alpha13/source-diversity-inventory.json').read_text())
    records=[]
    for e in pinned['entries']:
        if e['catalog_tier']!='private' or not e['dataset_id'].startswith('ecosis_'):continue
        # Receipt filenames disclose no source identifiers. Restartable locator
        # mapping is kept only inside this protected metadata root.
        index=root/'metadata-locators.json'
        locators=json.loads(index.read_text()) if index.exists() else {}
        name=e['dataset_id'];receipt=locators.setdefault(name,opaque_id())
        atomic_json(index,locators);path=root/(receipt+'.json')
        urls=[x['url'] for x in e['original_source_locators'] if x.get('url','').startswith('https://data.ecosis.org/dataset/')]
        if len(urls)!=1:
            records.append({'receipt_id':receipt,'dataset_id':name,'status':'unavailable','reason':'EXACT_ORIGINAL_PACKAGE_LOCATOR_REQUIRED'});continue
        slug=urls[0].rstrip('/').rsplit('/',1)[-1]
        endpoint='https://data.ecosis.org/api/3/action/package_show?'+urllib.parse.urlencode({'id':slug})
        if not path.exists():
            try:
                with urllib.request.urlopen(endpoint,timeout=30) as response:data=response.read(262145)
                if len(data)>262144:raise ValueError('metadata bound')
                value=json.loads(data)
                if value.get('success') is not True:raise ValueError('metadata response')
                atomic_json(path,value)
            except Exception:
                records.append({'receipt_id':receipt,'dataset_id':name,'status':'unavailable','reason':'ORIGINAL_METADATA_NOT_RETRIEVED'});continue
        original=json.loads(path.read_text())['result']
        license_id=original.get('license_id')
        # Only describes what the primary source currently states. These are
        # leads for local admission review, never a blanket cache authorization.
        records.append({'receipt_id':receipt,'dataset_id':name,'status':'reviewed','original_metadata_url':endpoint,
            'original_package_id':original.get('id'),'original_package_name':original.get('name'),
            'license_id':license_id,'license_title':original.get('license_title'),
            'author':original.get('author'),'maintainer':original.get('maintainer'),
            'metadata_sha256':digest(path),'source_dimensions_preserved_from_pinned_inventory':True,
            'open_license_lead':license_id in ['cc-by','cc-by-sa','cc-zero','odc-by','odc-odbl','odc-pddl'],
            'extra_contracts_review':'pending','canonical_correspondence_review':'pending',
            'access_analysis_admitted':False,'aggregate_publication_approved':False,'resource_files_retrieved':0})
    result={'visibility':'local_private','protocol':'domains.alpha14.original_rights_review.v0.1',
        'records':records,'metadata_entries_reviewed':len(records),'source_bytes_retrieved':0,'new_scientific_fits':0}
    atomic_json(root/'rights-review.json',{'audit':result,'authentication':store.authenticate(result)})
    print(json.dumps({'original_metadata_candidates_reviewed':len(records),'new_scientific_fits':0,
                      'source_bytes_retrieved':0,'public_export_created':False}))


if __name__=='__main__':main()
