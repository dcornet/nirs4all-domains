"""Complete catalog P0 plus original public-source metadata; no spectral reads."""
import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request
import yaml
from nirs4all_domains.storage import atomic_json,digest

ROOT=Path('.audit/alpha13');PUBLIC=Path('docs/benchmarks/alpha13')
PAGES={
    'ucph_rights':'https://ucphchemometrics.com/datasets/',
    'ucph_tablet':'https://ucphchemometrics.com/tablet/',
    'ucph_soil':'https://ucphchemometrics.com/soilnir/',
    'ohpl_description':'https://raw.githubusercontent.com/nanxstats/OHPL/master/DESCRIPTION',
    'ohpl_beer_docs':'https://raw.githubusercontent.com/nanxstats/OHPL/master/man/beer.Rd',
    'ohpl_soil_docs':'https://raw.githubusercontent.com/nanxstats/OHPL/master/man/soil.Rd',
    'ohpl_wheat_docs':'https://raw.githubusercontent.com/nanxstats/OHPL/master/man/wheat.Rd',
    'ossl_access':'https://docs.soilspectroscopy.org/db-access.html',
    'ossl_rights':'https://soilspectroscopy.org/introducing-the-open-soil-spectral-library/',
}


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            url=dict(attrs).get('href','')
            if url.startswith(('https://sid.erda.dk/','http://sid.erda.dk/')):self.links.append(url)


def main():
    source=ROOT/'source';source.mkdir(parents=True,exist_ok=True);pages={}
    for key,url in PAGES.items():
        path=source/(key+'.txt')
        if not path.exists():
            with urllib.request.urlopen(url,timeout=45) as response:
                data=response.read(1048577)
                if len(data)>1048576:raise ValueError('SOURCE_METADATA_BYTE_BOUND_EXCEEDED')
            path.write_bytes(data)
        text=path.read_text(encoding='utf-8');links=Links();links.feed(text)
        pages[key]={'url':url,'sha256':digest(path),'bytes':path.stat().st_size,
            'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'official_download_links':sorted(set(links.links)),'spectral_bytes_acquired':0}
        print(json.dumps({'source':key,'bytes':path.stat().st_size,'downloads':pages[key]['official_download_links']}),flush=True)
    assert 'available for public use' in (source/'ucph_rights.txt').read_text(encoding='utf-8')
    assert 'GPL' in (source/'ohpl_description.txt').read_text(encoding='utf-8')
    inventory=json.loads(Path('docs/audit/catalog-inventory-alpha8.json').read_text());assert len(inventory['datasets'])==164
    old=json.loads(Path('docs/benchmarks/alpha12/input-freeze.json').read_text());old_by_id={r['dataset_id']:r for r in old['entries']}
    rows=[]
    for e in inventory['datasets']:
        path=Path('.audit/datasets/catalog/datasets')/(e['dataset_id']+'.yaml');descriptor=yaml.safe_load(path.read_text(encoding='utf-8'))
        name=e['dataset_id'];sources=[]
        for s in e['sources']:
            modality=s['modality'];reviewed='MIR' if name.startswith('ossl_') and '_mir_' in name else modality
            sources.append({**s,'reviewed_modality':reviewed,'modality_conflict':reviewed!=modality,
                'dense_float64_bytes':s['n_observations']*s['n_variables']*8,
                'pca_full_population_work':s['n_observations']**2*min(20,s['n_observations']-1,s['n_variables']),
                'exact_census_distance_products':s['n_observations']**2*s['n_variables']})
        family='soil' if name.startswith(('ossl_','ohpl_soil','ecostress_soil')) else 'pharmaceutical' if 'tablet' in name or name.startswith('flanagan') else 'grain' if any(k in name for k in ['corn_','cgl_','perten_','ohpl_wheat']) else 'food' if name.startswith(('ohpl_beer','timeseries_')) else 'vegetation' if name.startswith(('ecosis_','grapevine_')) else 'spectral_library' if name.startswith(('ecostress_','openspecy','rruff','pnnl','plastic')) else 'biomedical' if name.startswith(('malaria_','cartilage_')) else 'simulated_molecular' if name.startswith('chembl') else 'unresolved'
        old_row=old_by_id.get(name);rights={'status':'unavailable','reason':'ORIGINAL_RIGHTS_NOT_YET_INDEPENDENTLY_RESOLVED','value':None}
        if old_row and old_row.get('rights'):rights=old_row['rights']
        candidate=name in ['ucph_tablet_nir','ohpl_soil_nir','ohpl_beer_nir','ohpl_wheat_nir']
        origins=[{k:v for k,v in origin.items() if k in ['kind','mode','access','title']}|
            ({'url':origin['locator']} if str(origin.get('locator','')).startswith(('https://','http://')) else
             {'locator_scope':'owner-local or maintainer-only locator; omitted from portable manifest'}) for origin in descriptor.get('origin_sources',[])]
        rows.append({'dataset_id':name,'catalog_tier':e['tier'],'catalog_license':e['license'],
            'catalog_content_version':e['content_version'],'catalog_content_hash':e['content_hash'],
            'descriptor_sha256_observed':digest(path),'pinned_inventory_descriptor_sha256':e['descriptor_sha256'],
            'family':family,'sources':sources,'target_descriptors':[{k:v for k,v in t.items() if k in ['name','type','unit','units','card_n','card_n_missing']} for t in e['targets']],
            'original_source_locators':origins,
            'candidate_for_deep_review':candidate,'previous_x_only_status':old_row['status'] if old_row else 'not_executed',
            'rights':rights,'rights_dimensions':{'access':'public_metadata_review' if candidate else 'not_newly_admitted',
                'local_analysis':'pending_exact_source_correspondence' if candidate else 'not_newly_admitted',
                'derived_statistics_publication':'pending_exact_source_correspondence' if candidate else 'not_newly_admitted',
                'raw_redistribution':'not_requested'},
            'study_population_relationship':{'status':'not_identifiable','reason':'CATALOG_VIEW_OR_PACKAGE_CITATION_IS_NOT_ORIGINAL_STUDY_INDEPENDENCE','value':None},
            'supervised_role':'exploratory_already_used' if name=='perten_cereals_nir' or name in ['ecosis_intact_and_ground_leaf_litter_spectra_from_cedar_creek_reflectance_nirs'] else 'not_admitted',
            'scientific_selection_uses_model_scores':False,
            'scope':'Descriptor-only review; private spectra and target cells not opened. Tier alone is not an original-rights decision.'})
    result={'baseline':'ebb1b9b8a45d01618931d846d059641701cac7da','catalog_revision':inventory['catalog_revision'],
        'entries':rows,'counts':{'catalog':164,'public':42,'private':122},'official_metadata_pages':pages,
        'source_access_does_not_automatically_establish_model_admission':True,'target_accessed':False,'spectral_bytes_acquired':0}
    atomic_json(PUBLIC/'source-diversity-inventory.json',result);atomic_json(ROOT/'source-pages.json',pages)


if __name__=='__main__':main()
