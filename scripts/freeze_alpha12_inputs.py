"""Freeze X, declared metadata and source ownership only; never open Y tables."""
import argparse
import json
from pathlib import Path

import pandas as pd
from nirs4all_domains.adaptive import spectral_request
from nirs4all_domains.storage import atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import query_design

PUBLIC=Path('docs/benchmarks/alpha12')
FIELDS=('species','genus','family','site','date','source_plot','source_individual',
        'source_Room_Temp','source_leaf_position','source_pot_medium','joint_id','bone_type')
SELECTION=(
 'ecosis_2008_university_of_wisconsin_biotron_fresh_leaf_spectra_reflectance_nirs',
 'ecosis_ngee_arctic_2017_canopy_spectral_reflectance_seward_pen_reflectance_nirs',
 'ecosis_seasonal_measurements_of_photosynthesis_and_leaf_traits_reflectance_nirs',
 'ecosis_tabletop_leaf_drydowns_to_relate_leaf_spectra_and_leaf_reflectance_nirs',
 'ecosis_ground_leaf_cabo_spectra_from_herbarium_project_reflectance_nirs',
 'ecosis_fresh_leaf_cabo_spectra_from_herbarium_project_reflectance_nirs',
 'cartilage_spectroscopy_scientificdata_nir')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--leaf-root',type=Path,required=True);args=parser.parse_args()
    root=Path('.audit/alpha12');approval=json.loads((root/'budget-approval.json').read_text())
    assert approval['workspace_ceiling']==13873678017
    coverage=json.loads(Path('docs/benchmarks/alpha11/public-coverage.json').read_text())
    inventory=json.loads(Path('docs/audit/catalog-inventory-alpha8.json').read_text())
    catalog={r['dataset_id']:r for r in inventory['datasets'] if r['tier']=='public'}
    entries=[];locators={}
    newly_open={
        'ecosis_leaf_spectra_of_4_plant_species_from_belgian_dune_grass_reflectance_nirs':('belgian','odc-odbl'),
        'ecosis_leaf_spectra_of_boreal_tree_species_from_alberta_potted_reflectance_nirs':('alberta','cc-by-sa')}
    for old in coverage['entries']:
        name=old['dataset_id'];item=catalog[name];source=item['sources'][0]
        row={'dataset_id':name,'source_id':source['source_id'],
            'catalog_content':{'version':item['content_version'],'content_hash':item['content_hash'],'descriptor_sha256':item['descriptor_sha256']},
            'source_dimensions':source,'identity_evidence':old['identity_evidence'],
            'baseline_ref':old['profile_ref'],'stability_selected':name in SELECTION,
            'historical_split_support':old['levels']['X1'],
            'source_family':'simulated_molecular' if name.startswith('chembl') else 'mosquito' if name.startswith('malaria') else 'cartilage' if name.startswith('cartilage') else 'vegetation',
            'status':'unavailable','reason':old['levels']['X0']['reason']}
        original=json.loads(Path(old['profile_ref']['path']).read_text())
        rights=original.get('rights')
        if name in newly_open:
            key,license_id=newly_open[name];metadata=root/'source'/(key+'.json')
            response=json.loads(metadata.read_text())['result'];assert response['license_id']==license_id
            card=json.loads((args.leaf_root/name/'dataset_card.json').read_text(encoding='utf-8'))
            assert card['official_source']['package_id']==response['id']
            rights={'status':'computed','reason':None,'value':{'license_id':license_id,'package_id':response['id'],
                'metadata_sha256':digest(metadata),'source_url':'https://data.ecosis.org/dataset/'+response['id'],
                'attribution':response['author'],'scope':'No spectra redistribution; attributed nonreconstructive structural summaries. Original terms remain attached.'}}
        row['rights']=rights
        if name.startswith('chembl'):
            row.update(status='ineligible',reason='SIMULATED_MIR_RAMAN_OUTSIDE_PHYSICAL_NIRS_COHORT; FULL_MATRIX_AND_PCA_WORK_BUDGET_EXCEEDED')
        if old['levels']['X0']['status']=='computed' or name in newly_open:
            leaf=args.leaf_root/name;path=leaf/('X.csv' if source['source_id']=='X' else source['source_id']+'.csv')
            request=spectral_request(path,source['source_id'],old['identity_evidence']);request['axis_unit']=source['axis_unit']
            ids=request['observation_ids'];n=len(ids);p=len(request['axis'])
            if (n,p)!=(source['n_observations'],source['n_variables']):raise ValueError('FROZEN_CATALOG_SHAPE_CHANGED:'+name)
            if n*p>10000000 or n*n*min(20,p,n-1)>250000000 or p*p*min(20,p,n-1)>250000000:
                row.update(status='unavailable',reason='FULL_POPULATION_NATIVE_GEOMETRY_BUDGET_EXCEEDED');entries.append(row);continue
            design=query_design(ids,p)
            header=pd.read_csv(leaf/'M.csv',sep=';',nrows=0).columns.tolist()
            selected=['observation_id']+[f for f in FIELDS if f in header]
            # Only declared metadata and keys are materialized; Y.csv is never opened.
            metadata=pd.read_csv(leaf/'M.csv',sep=';',usecols=selected+(['sample_id'] if 'sample_id' in header else []),dtype=str).fillna('')
            if metadata.observation_id.duplicated().any() or set(metadata.observation_id)!=set(ids):raise ValueError('KEYED_METADATA_SOURCE_MISMATCH:'+name)
            keyed=metadata.set_index('observation_id')
            components={s:s for s in ids};scope='Observation-level algorithmic subsampling; not biological sampling uncertainty.'
            physical_proof=None
            if name.startswith('cartilage'):
                proof=Path('docs/benchmarks/alpha10/cartilage-admission.json')
                admitted=json.loads(proof.read_text())['original_to_derived']['spectral_membership']['value']
                assert admitted['locations_exact_float32_multiset_match']==869 and not admitted['mismatched_location_keys']
                components={s:keyed.at[s,'sample_id'] for s in ids}
                assert len(set(components.values()))==869 and all(components.values())
                scope='Whole original-audited physical-location blocks; all acquisitions retained. Conditional on five declared joints; not donor/biological uncertainty.'
                physical_proof={'path':proof.as_posix(),'sha256':digest(proof)}
            row.update(status='computed',reason=None,input_csv_sha256=digest(path),metadata_sha256=digest(leaf/'M.csv'),
                axis_sha256=fingerprint(request['axis']),observation_ids_sha256=fingerprint(ids),
                query_design=design,n_resampling_units=len(set(components.values())),resampling_scope=scope,
                component_map_sha256=fingerprint(components),physical_component_proof=physical_proof,
                available_metadata_fields=[f for f in FIELDS if f in keyed],
                original_axis_note='Declared CSV axis retained exactly; Cartilage derived labels round original wavelengths to two decimals.' if name.startswith('cartilage') else 'Declared complete source axis retained exactly.')
            locators[name]={'matrix':str(path.resolve()),'metadata':str((leaf/'M.csv').resolve()),'components':components}
            print(json.dumps({'dataset':name,'n':n,'p':p,'query_mode':design['mode'],'query_n':design['n_query'],'stability':row['stability_selected']}),flush=True)
        entries.append(row)
    frozen={'protocol_version':'domains.unsupervised.v0.1','baseline':'e8385bf4aa3125d6f6ffadd5e63d080d14a02b44',
        'source_catalog_revision':inventory['catalog_revision'],'entries':entries,'stability_subset':list(SELECTION),
        'fractions':[.6,.8],'draws_per_fraction':20,'seed':12031,'protocol_sha256':digest('docs/ALPHA12_UNSUPERVISED_PROTOCOL.md'),
        'hypotheses_sha256':digest('docs/ALPHA12_HYPOTHESIS_REGISTER.md'),'source_reaudit_ref':{'path':(PUBLIC/'source-reaudit.json').as_posix(),'sha256':digest(PUBLIC/'source-reaudit.json')},
        'target_accessed':False,'model_performance_used':False}
    frozen['freeze_id']=fingerprint(frozen)
    destination=PUBLIC/'input-freeze.json'
    if destination.exists() and json.loads(destination.read_text())!=frozen:raise ValueError('INPUT_FREEZE_ALREADY_EXISTS_WITH_DIFFERENT_CONTENT')
    atomic_json(destination,frozen);atomic_json(root/'input-locators.json',locators)
    print(json.dumps({'freeze_id':frozen['freeze_id'],'eligible':sum(r['status']=='computed' for r in entries),'public_entries':len(entries)}))


if __name__=='__main__':main()
