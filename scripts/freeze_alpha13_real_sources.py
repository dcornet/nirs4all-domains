"""Metadata/header audit, rights-gated canonical X admission, no target reads/fits."""
import io
import json
from pathlib import Path
import zipfile
from alpha13_common import ROOT,PUBLIC,run,publish
from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import atomic_json,digest,fingerprint,tree_bytes
from nirs4all_domains.unsupervised import query_design
from nirs4all_domains.x_admission import authorize_x_source

NAMES=['ucph_tablet_nir','ohpl_soil_nir']
LEAF=Path('D:/VS projects/nirs_db_vf/standardized_datasets')


def main():
    from scipy.io import whosmat
    catalog=json.loads(Path('docs/audit/catalog-inventory-alpha8.json').read_text());by_id={r['dataset_id']:r for r in catalog['datasets']}
    original={'ucph_tablet_nir':('tablet','https://ucphchemometrics.com/tablet/','Dyrby et al. 2002, Applied Spectroscopy 56(5), 579-585'),
        'ohpl_soil_nir':('soil','https://ucphchemometrics.com/soilnir/','Rinnan and Rinnan 2007, Soil Biology & Biochemistry 39, 1664-1673')}
    paths={key:ROOT/'datasets-cache'/('alpha13-original-'+key)/'raw/ucph-original-v1'/filename
        for key,filename in [('tablet','Tablets.zip'),('soil','NIR Soil.zip')]}
    inputs=[{'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size} for p in paths.values()]
    contract={'task':{'task_id':fingerprint(['alpha13','source-header-review'])},'phase':'source-header-review',
        'source_hashes':{k:digest(p) for k,p in paths.items()},'runner_sha256':digest(__file__)}
    def headers(folder):
        records={}
        for key,path in paths.items():
            with zipfile.ZipFile(path) as z:
                record={'archive_sha256':digest(path),'archive_bytes':path.stat().st_size,'members':[],
                    'target_cells_decoded':0,'skipped_platform_resource_forks':[]}
                for info in z.infolist():
                    if info.filename.startswith('__MACOSX/') or Path(info.filename).name.startswith('._'):
                        record['skipped_platform_resource_forks'].append(info.filename);continue
                    entry={'name':info.filename,'bytes':info.file_size}
                    if info.filename=='NIRsoil.mat':entry['variables']=whosmat(io.BytesIO(z.read(info)))
                    if info.filename=='Tablets_matlab.zip':
                        with zipfile.ZipFile(io.BytesIO(z.read(info))) as inner:
                            raw=inner.read('NIRdata_tablets.MAT');entry['nir_mat_sha256']=__import__('hashlib').sha256(raw).hexdigest()
                            entry['nir_variables']=whosmat(io.BytesIO(raw));entry['matrix_projection']='not decoded: spectral and reference columns share Matrix'
                    record['members'].append(entry)
                records[key]=record
        return {'archives':records,'native_cache_unique_bytes':tree_bytes([ROOT/'datasets-cache']),
            'cache_accounting_review':'Native Datasets also extracted nested ZIP members. Reserve an additional conservative 8 MiB inside the existing campaign envelope for this observed cache expansion.',
            'previous_header_failure':'MacOS resource fork misidentified as MAT; original failed receipt preserved. No target cells were decoded.',
            'full_soil_object_read':'not performed: automatic review rejected potential target materialization; no retry of that action',
            'target_accessed':False,'new_pca_fits':0}
    plan={'inputs':inputs,'scratch_bytes':8*1024*1024,'evidence_bytes':131072,'expected_fits':0,'expected_permutations':0,
        'uncertainty':'Headers only. Extra reservation conservatively covers native cache expansion not included in the first compressed-download estimate.'}
    store,r,header=run(contract,'P0',plan,headers);publish(store,r,'sources/header-audit.json')
    old=json.loads(Path('docs/benchmarks/alpha12/input-freeze.json').read_text());old_local=json.loads(Path('.audit/alpha12/input-locators.json').read_text())
    entries=[];locators={};admissions=[]
    for name in NAMES:
        key,url,citation=original[name];leaf=LEAF/name;card=leaf/'dataset_card.json';script=leaf/'source_to_standard.py';manifest=leaf/'raw_manifest.csv'
        card_value=json.loads(card.read_text(encoding='utf-8'));text=script.read_text(encoding='utf-8')
        assert name in text and 'X.csv' in text
        lineage=card_value['official_source']['urls']
        if key=='tablet':assert url in lineage
        else:
            assert 'soil.rda' in ' '.join(lineage)
            assert 'Rinnan' in (ROOT/'source/ohpl_soil_docs.txt').read_text(encoding='utf-8')
        basis=['https://ucphchemometrics.com/datasets/','sha256:'+digest(ROOT/'source/ucph_rights.txt'),url]
        if key=='soil':basis+=['https://github.com/nanxstats/OHPL','sha256:'+digest(ROOT/'source/ohpl_description.txt'),'sha256:'+digest(ROOT/'source/ohpl_soil_docs.txt')]
        specification={'dataset_id':name,'content_version':by_id[name]['content_version'],'source_id':'X','catalog_tier':by_id[name]['tier'],
            'original_source_url':url,'provenance_urls':sorted(set([url,*lineage])),
            'permissions':{d:{'status':'allowed' if d!='redistribute_raw' else 'unknown','evidence':basis if d!='redistribute_raw' else []}
                for d in ['access','local_analysis','publish_statistics','redistribute_raw']},
            'metadata_hashes':{'card':digest(card),'conversion_script':digest(script),'manifest':digest(manifest),'original_archive':digest(paths[key])},
            'identity_scope':'observation_conditional'}
        admission=authorize_x_source(specification) # Rights gate precedes X opening.
        path=leaf/'X.csv';source=by_id[name]['sources'][0]
        raw=spectral_request(path,'X','observation_identity_only');raw['axis_unit']=source['axis_unit']
        ids=raw['observation_ids'];n=len(ids);p=len(raw['axis']);assert (n,p)==(source['n_observations'],source['n_variables'])
        components={s:s for s in ids};scope='Canonical observation-conditional algorithmic resampling; original specimen/reference correspondence not verified.'
        entry={'dataset_id':name,'source_id':'X','catalog_content':{'version':by_id[name]['content_version'],'content_hash':by_id[name]['content_hash'],
            'descriptor_sha256':by_id[name]['descriptor_sha256']},'source_dimensions':source,'identity_evidence':'observation_identity_only',
            'input_csv_sha256':digest(path),'input_bytes':path.stat().st_size,'axis_sha256':fingerprint(raw['axis']),
            'observation_ids_sha256':fingerprint(ids),'component_map_sha256':fingerprint(components),'n_resampling_units':n,
            'resampling_scope':scope,'query_design':query_design(ids,p),'x_admission_id':admission['admission_id'],
            'original_study_reference':citation,'original_source_url':url,'original_numeric_equivalence':admission['numeric_original_equivalence'],
            'physical_reference_closure':admission['supervised_admission'],'metadata_agreement':state(reason='NO_INDEPENDENT_ORIGINAL_KEYED_FACTOR_JOIN_QUALIFIED'),
            'stability_selected':key=='tablet'}
        admissions.append(admission);entries.append(entry);locators[name]={'matrix':str(path.resolve()),'components':components}
    for source in old['entries']:
        name=source['dataset_id']
        if 'biotron' not in name and not name.startswith('cartilage'):continue
        local=old_local[name];path=Path(local['matrix']);assert digest(path)==source['input_csv_sha256']
        entry={k:source[k] for k in ['dataset_id','source_id','catalog_content','source_dimensions','identity_evidence','input_csv_sha256','axis_sha256','observation_ids_sha256','component_map_sha256','n_resampling_units','resampling_scope','query_design']}
        entry.update(input_bytes=path.stat().st_size,stability_selected=True,reused_alpha12_reference=True,
            original_entry_ref={'path':'docs/benchmarks/alpha12/input-freeze.json','sha256':digest('docs/benchmarks/alpha12/input-freeze.json')})
        entries.append(entry);locators[name]={'matrix':local['matrix'],'components':local['components']}
    revised=PUBLIC/'revised-design-freeze.json'
    value={'protocol_version':'domains.alpha13.real_inputs.v0.1','revised_design_ref':{'path':revised.as_posix(),'sha256':digest(revised)},
        'source_protocol_sha256':digest('docs/ALPHA13_SOURCE_X_PROTOCOL.md'),'source_admission_bridge_sha256':digest('bridges/python/nirs4all_domains/x_admission.py'),
        'entries':entries,'stability_selection_rule':'Biotron, complete-location Cartilage, then first rights-admitted original UCPH tablet canonical view. Soil adds X-only geometry.',
        'test_target_accessed':False,'model_performance_used':False,'new_reference_pca_upper':4,'real_stability_pca_upper':720}
    value['freeze_id']=fingerprint(value);path=PUBLIC/'real-input-freeze.json'
    if path.exists():assert json.loads(path.read_text())==value
    atomic_json(path,value);atomic_json(ROOT/'input-locators.json',locators)
    atomic_json(PUBLIC/'source-admissions.json',{'protocol_version':'domains.x_source_admission.v0.1','admissions':admissions,'target_accessed':False,
        'original_study_candidates':2,'admitted_confirmation_studies':0,'numeric_original_equivalence_verified':False,'header_audit_sha256':r['sha256']})
    print(json.dumps({'freeze_id':value['freeze_id'],'new_x_sources':2,'stability_sources':sum(e['stability_selected'] for e in entries),'targets_opened':0}))


if __name__=='__main__':main()
