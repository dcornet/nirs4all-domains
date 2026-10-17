"""Pinned provenance hierarchy and declared overlap, without spectral fitting or Y."""
from collections import Counter,defaultdict
import json
import re
from pathlib import Path
import pandas as pd

from nirs4all_domains.dependence import state
from nirs4all_domains.storage import atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised_sources import relation

ROOT=Path('docs/benchmarks/alpha12')


def main():
    frozen=json.loads((ROOT/'input-freeze.json').read_text());locators=json.loads(Path('.audit/alpha12/input-locators.json').read_text())
    inventory=json.loads(Path('docs/audit/catalog-inventory-alpha8.json').read_text())
    catalog={e['dataset_id']:e for e in inventory['datasets'] if e['tier']=='public'}
    nodes=[];private=[];groups=defaultdict(list)
    verified_references={
        'cartilage_spectroscopy_scientificdata_nir':'10.1038/s41597-019-0170-y',
        'ecosis_intact_and_ground_leaf_litter_spectra_from_cedar_creek_reflectance_nirs':'10.1139/cjfr-2023-0280',
        'ecosis_leaf_spectra_structural_and_biochemical_leaf_traits_of_reflectance_nirs':'10.1093/jxb/erz061'}
    for entry in frozen['entries']:
        name=entry['dataset_id'];citations=[];original_package=None;source_keys=[];original_keys_verified=False
        key_field=None;metadata_sha=None;repeat_counts={};physical_namespace=None;missing_keys=None;signal_types=[]
        if name in locators:
            path=Path(locators[name]['metadata']);assert digest(path)==entry['metadata_sha256'];metadata_sha=digest(path)
            header=pd.read_csv(path,sep=';',nrows=0).columns.tolist()
            columns=[c for c in ['publication_doi','source_ID','source_sample_id','source_sample_name','sample_id','signal_type'] if c in header]
            frame=pd.read_csv(path,sep=';',usecols=columns,dtype=str).fillna('')
            if 'publication_doi' in frame:
                citations=sorted({v.rstrip('.)]') for s in frame.publication_doi for v in re.findall(r'10\.\d{4,9}/[^\s;,|]+',s)})
            if name in verified_references:citations=[verified_references[name]]
            if 'signal_type' in frame:signal_types=sorted({v for v in frame.signal_type if v})
            key_field=next((c for c in ['source_ID','source_sample_id','source_sample_name'] if c in frame),None)
            if key_field:source_keys=frame[key_field].tolist()
            card=path.parent/'dataset_card.json'
            if card.exists():original_package=json.loads(card.read_text(encoding='utf-8')).get('official_source',{}).get('package_id')
            if name.startswith('cartilage'):
                source_keys=frame['sample_id'].tolist();key_field='sample_id';original_keys_verified=True
                physical_namespace='figshare:7803845.v2:original-location'
            if 'litter' in name and key_field=='source_ID':
                origin=json.loads(Path('.audit/alpha11/litter-origin.json').read_text())
                file=next(f for f in origin['files'] if f['name']=='intact_spec.csv')
                assert digest(file['path'])==file['sha256']
                keys=pd.read_csv(file['path'],usecols=['ID'],dtype=str)['ID'].tolist()
                assert set(source_keys)==set(keys) and len(source_keys)==len(set(source_keys))
                original_keys_verified=True;physical_namespace='ecosis:85ca4a2e-0a61-4ef7-9e0f-ffa6ea1c2c22:litter-bag'
            if source_keys:
                missing_keys=sum(not s for s in source_keys);source_keys=[s for s in source_keys if s]
                repeat_counts=dict(Counter(Counter(source_keys).values()))
        for citation in citations:groups[citation].append(name)
        original_claim={'original_package_id':original_package,'cited_study_references':citations,
            'physical_namespace':physical_namespace,'original_keys_verified':original_keys_verified,'original_keys':source_keys}
        private.append(original_claim)
        nodes.append({'dataset_id':name,'source_view_id':name+':'+entry['source_id'],
            'all_declared_spectral_sources':catalog[name]['sources'],
            'catalog_content':entry['catalog_content'],'source_family':entry['source_family'],
            'original_package_id':original_package,'cited_study_references':citations,
            'study_reference_status':'original_source_audited' if name in verified_references else 'declared_or_missing',
            'physical_population':state({'namespace':physical_namespace,'scope':'source-defined physical objects, not independent biological groups'}) if physical_namespace else state(reason='ORIGINAL_POPULATION_CORRESPONDENCE_NOT_VERIFIED',status='not_identifiable'),
            'identity_evidence':entry['identity_evidence'],'metadata_sha256':metadata_sha,
            'declared_source_key_field':key_field,'declared_source_key_count':len(set(source_keys)),
            'missing_source_keys':missing_keys,
            'declared_source_key_set_sha256':fingerprint(sorted(set(source_keys))) if source_keys else None,
            'original_keys_verified':original_keys_verified,'acquisitions_per_declared_key_histogram':repeat_counts,
            'acquisition_context':state({'instrument':entry['source_dimensions']['instrument_name'],'modality':entry['source_dimensions']['modality'],
                'axis_unit':entry['source_dimensions']['axis_unit'],'declared_signal_types':signal_types,
                'intensity_amplitude_units':state(reason='FRACTION_PERCENT_OR_ABSORBANCE_CONVENTIONS_NOT_UNIFORMLY_ORIGINAL_SOURCE_QUALIFIED'),
                'scope':'Declared source descriptors; explanatory mechanism is not inferred from X.'}),
            'benchmark_task_scope':'X-only source profile; target tasks are separate historical or future evidence',
            'independent_biological_population_count':state(reason='NOT_IDENTIFIABLE_FROM_THIS_SOURCE_HIERARCHY')})
    edges=[]
    for i,a in enumerate(nodes):
        for j in range(i+1,len(nodes)):
            r=relation(private[i],private[j])
            if r['status'] not in ('computed','exploratory'):continue
            keys=set(private[i]['original_keys']) & set(private[j]['original_keys'])
            edges.append({'left':a['dataset_id'],'right':nodes[j]['dataset_id'],'relationship':r,
                'declared_source_key_overlap':{'count':len(keys),'sha256':fingerprint(sorted(keys)),
                    'scope':'Declared-key coincidence, not verified physical correspondence unless relationship says so.'}})
    result={'protocol_version':'domains.alpha12.source_hierarchy.v0.1','freeze_id':frozen['freeze_id'],
        'nodes':nodes,'relationships':edges,'cited_reference_groups':[{'reference':k,'entries':v} for k,v in sorted(groups.items())],
        'counts':{'catalog_entries':42,'primary_source_view_records':42,
            'all_declared_catalog_spectral_sources':sum(len(e['sources']) for e in catalog.values()),'cited_reference_groups':len(groups),
            'entries_with_audited_physical_unit_ownership':sum(e['identity_evidence']=='verified_physical_identity' for e in frozen['entries']),
            'physical_namespaces_with_directly_rechecked_original_keys':len({n['physical_population']['value']['namespace'] for n in nodes if n['physical_population']['status']=='computed'})},
        'distinct_independent_scientific_populations':state(reason='UNKNOWN_OVERLAP_AND_HIGHER_BIOLOGICAL_DEPENDENCIES; REFERENCE_COUNTS_ARE_NOT_INDEPENDENT_STUDY_COUNTS',status='not_identifiable'),
        'target_accessed':False,'model_fits':0,
        'limitations':['Different titles, files or DOIs do not establish population independence.',
            'Shared citations or source packages are conservative provenance groupings, not proof of shared specimens.',
            'Most original-key biological relationships remain unknown. Sources without metadata remain in the cohort.',
            'Litter ground preparation is an extra keyed same-object view, not an independent catalog entry or study.']}
    paired=ROOT/'paired-x-freeze.json'
    if paired.exists():
        proof=json.loads(paired.read_text())
        result['extra_original_preparation_views']=[{'source_view_id':'litter-original:ground_spec.csv',
            'physical_namespace':'ecosis:85ca4a2e-0a61-4ef7-9e0f-ffa6ea1c2c22:litter-bag',
            'n_original_objects':321,'n_verified_shared_objects_with_intact':321,
            'source_parent_intact_objects':322,'original_unpaired_key':proof['key_proof']['left_only'],
            'pairing_proof_ref':{'path':paired.as_posix(),'sha256':digest(paired)},
            'independent_new_population':False}]
    atomic_json(ROOT/'source-hierarchy.json',result)
    print(json.dumps(result['counts']))


if __name__=='__main__':main()
