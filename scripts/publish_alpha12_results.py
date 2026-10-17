"""No-refit consolidation of the 42-entry unsupervised structural evidence matrix."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import pandas as pd

from run_alpha12_profiles import export
from nirs4all_domains.bank import schema_check
from nirs4all_domains.dependence import state
from nirs4all_domains.predictive import native_summary
from nirs4all_domains.storage import StageStore,atomic_json,digest,fingerprint
from nirs4all_domains.unsupervised import compare_partition,neighborhood_agreement

ROOT=Path('docs/benchmarks/alpha12');AUDIT=Path('.audit/alpha12')


def ref(path):
    return {'path':Path(path).as_posix(),'sha256':digest(path)}


def summarize(values):
    values=list(values)
    return state(native_summary(values)) if values else state(reason='NO_ELIGIBLE_SOURCE_VALUES')


def descriptor(profile,path):
    value=profile['value'];clusters=[]
    for setting in value['cluster_settings']:
        if setting['status']!='computed':clusters.append(setting);continue
        s=setting['value'];support=Counter(v for v in s['labels'] if v>=0)
        clusters.append(state({'min_cluster_size':s['min_cluster_size'],'min_samples':s['min_samples'],
            'n_clusters':s['n_clusters'],'noise_fraction':s['noise_fraction'],'membership_summary':s['membership_summary'],
            'cluster_observation_counts':sorted(support.values(),reverse=True),
            'clusters_below_one_percent_population':sum(n<.01*value['n_observations'] for n in support.values()),
            'scope':'Parameter-specific acquisition partition; no biological or nuisance interpretation.'}))
    neighborhoods={}
    for space,n in value['neighborhoods']['value'].items():
        neighborhoods[space]={k:n[k] for k in ['mode','n_query','n_reference','k','native_calls','distance_products',
            'rank_summaries','normalized_nearest_summary','relative_proximity','rank_last_over_first_distance',
            'neighbor_distance_dispersion','zero_nearest_distances','query_sensitivity']}
    return {'profile_ref':ref(path),'n_observations':value['n_observations'],'n_bands':value['n_bands'],
        'pca':value['pca'],'effective_dimension':value['effective_dimension'],'cluster_settings':clusters,
        'neighborhoods':neighborhoods,'provider':value['provider'],
        'scope':'Complete original declared source X and axis. Normalized distances describe this source/representation, not a universal physical scale.'}


def build(frozen,hierarchy):
    locations=json.loads((AUDIT/'input-locators.json').read_text())
    nodes={r['dataset_id']:r for r in hierarchy['nodes']};rows=[]
    for source in frozen['entries']:
        name=source['dataset_id'];profiles={};representations={};cost={};metadata={};ids=None
        for representation in ('raw','snv'):
            path=ROOT/'profiles'/(name+'.'+representation+'.json')
            if not path.exists():
                representations[representation]=state(reason=source['reason'] or 'REPRESENTATION_NOT_EXECUTED',status=source['status'] if source['status']!='computed' else 'unavailable')
                continue
            profile=json.loads(path.read_text())
            if profile['status']!='computed':representations[representation]=profile;continue
            profiles[representation]=profile['value'];representations[representation]=state(descriptor(profile,path))
            cost[representation]={'elapsed_seconds':profile['value']['elapsed_seconds'],
                'pca_representation_fits':profile['value']['pca_fits'],'hdbscan_attempts':profile['value']['hdbscan_attempts'],
                'scope':'Callback includes field transport, per-spectrum SNV where applicable, PCA, neighborhoods, clustering and metadata kernels.'}
            factors=profile['value']['metadata_agreement']
            if factors['status']=='computed':
                metadata[representation]={'profile_ref':ref(path),
                    'n_fields':len(factors['value']),'n_variable_fields':sum(v['status']=='computed' and v['value']['n_levels']>=2 for v in factors['value'].values()),
                    'high_cardinality_fields':[k for k,v in factors['value'].items() if v['status']=='computed' and v['value']['high_cardinality']],
                    'factor_summaries':{k:{p:v['value'][p] for p in ['n_levels','missing','ari_including_noise','pc_associations','provenance']} if v['status']=='computed' else v for k,v in factors['value'].items()}}
        agreement=state(reason='BOTH_REPRESENTATIONS_REQUIRED')
        if len(profiles)==2:
            ids=pd.read_csv(locations[name]['matrix'],sep=';',usecols=['observation_id'],dtype=str).observation_id.tolist()
            assert fingerprint(ids)==source['observation_ids_sha256']
            assert profiles['raw']['observation_ids_sha256']==profiles['snv']['observation_ids_sha256']
            assert profiles['raw']['axis_sha256']==profiles['snv']['axis_sha256']
            partitions=[]
            for setting in range(2):
                a,b=(profiles[r]['cluster_settings'][setting] for r in ('raw','snv'))
                partitions.append(state(compare_partition(ids,a['value']['labels'],ids,b['value']['labels']))
                    if a['status']==b['status']=='computed' else state(reason='PARTITION_UNAVAILABLE'))
            projection={}
            for representation,p in profiles.items():
                a,b=p['neighborhoods']['value']['full_axis'],p['neighborhoods']['value']['pca']
                ratios=[y[0]/x[0] for x,y in zip(a['distances'],b['distances'],strict=True) if x[0]>0]
                projection[representation]={'neighbor_identity_agreement':neighborhood_agreement(a,b),
                    'projected_nearest_over_full_nearest':summarize(ratios),
                    'scope':'Same queries; nearest objects can differ between spaces. This is not a matched-pair distance error or physical redundancy decision.'}
            agreement=state({'partitions':partitions,'full_axis_neighbors':neighborhood_agreement(
                profiles['raw']['neighborhoods']['value']['full_axis'],profiles['snv']['neighborhoods']['value']['full_axis']),
                'projection_vs_full_axis':projection,
                'scope':'Same observed objects and axes. Representation sensitivity does not identify chemistry, nuisance removal or model dependence.'})
        stability_paths=[ROOT/'stability'/(name+'.'+r+'.'+str(f)+'.json') for r in ('raw','snv') for f in frozen['fractions']]
        stability=state(reason='NOT_IN_PRESPECIFIED_STABILITY_SUBSET' if not source['stability_selected'] else 'PRESPECIFIED_STABILITY_NOT_COMPLETED')
        if all(p.exists() for p in stability_paths):
            if ids is None:raise ValueError('MATCHED_REFERENCE_REPRESENTATIONS_REQUIRED_FOR_STABILITY')
            reports=[json.loads(p.read_text()) for p in stability_paths]
            classes=[s['value']['classification'] for report in reports for s in report['settings'] if s['status']=='computed']
            parameter=[]
            for representation,p in profiles.items():
                a,b=p['cluster_settings']
                parameter.append(compare_partition(ids,a['value']['labels'],ids,b['value']['labels'])['ari_including_noise']
                    if a['status']==b['status']=='computed' else state(reason='PARAMETER_PARTITION_UNAVAILABLE'))
            robust=len(classes)==8 and all(c=='robust_structure' for c in classes) and len(parameter)==2 and all(p['status']=='computed' and p['value']>=.8 for p in parameter)
            classification='robust_structure' if robust else 'insufficient_information' if 'insufficient_information' in classes or len(classes)<8 else 'fragile_structure'
            stability=state({'classification':classification,'per_setting_classifications':classes,
                'summary_refs':[ref(p) for p in stability_paths],'parameter_ari':parameter,
                'pca_refits':sum(r['pca_fits'] for r in reports),'hdbscan_attempts':sum(r['hdbscan_attempts'] for r in reports),
                'unit_scope':source['resampling_scope'],'n_declared_units':source['n_resampling_units'],
                'biological_sampling_uncertainty':False,
                'scope':'Observed conditional algorithmic reproducibility under the frozen perturbations; not a biological source, batch or shortcut classification.'})
        row={'schema_version':1,'protocol_version':frozen['protocol_version'],'dataset_id':name,'source_id':source['source_id'],
            'catalog_content':source['catalog_content'],'source_dimensions':source['source_dimensions'],'identity_evidence':source['identity_evidence'],
            'population_relationship':nodes[name]['physical_population'],'representations':representations,
            'representation_agreement':agreement,'structural_stability':stability,
            'metadata_agreement':state(metadata) if metadata else state(reason='NO_ADMISSIBLE_METADATA_AGREEMENT'),
            'split_support':source['historical_split_support'],'resource_cost':cost,'baseline_ref':source['baseline_ref'],
            'test_target_accessed':False,'universal_shortcut_score':None,
            'limitations':['X structure, target association and predictive dependence are distinct evidence levels.',
                'Observations, source views, citations and biological populations have different denominators.',
                'Unknown identities, missing metadata and all-noise results do not establish low structural susceptibility.',
                source.get('original_axis_note','No numerical representation executed for this source.') ]}
        row['record_id']=fingerprint(row);schema_check(row,'unsupervised-evidence');rows.append(row)
    stats={}
    for representation in ('raw','snv'):
        eligible=[r['representations'][representation]['value'] for r in rows if r['representations'][representation]['status']=='computed']
        stats[representation]={'n_sources':len(eligible),
            'retained_variance_fraction':summarize(r['pca']['retained_variance_fraction'] for r in eligible),
            'pc1_fraction':summarize(r['pca']['pc1_fraction'] for r in eligible),
            'effective_dimension':summarize(r['effective_dimension']['value'] for r in eligible if r['effective_dimension']['status']=='computed'),
            'n_exact_effective_dimension':sum(r['effective_dimension']['status']=='computed' for r in eligible),
            'primary_cluster_count':summarize(r['cluster_settings'][0]['value']['n_clusters'] for r in eligible if r['cluster_settings'][0]['status']=='computed'),
            'primary_noise_fraction':summarize(r['cluster_settings'][0]['value']['noise_fraction'] for r in eligible if r['cluster_settings'][0]['status']=='computed'),
            'full_axis_modes':dict(Counter(r['neighborhoods']['full_axis']['mode'] for r in eligible)),
            'neighbor_distance_dispersion':{mode:summarize(r['neighborhoods']['full_axis']['neighbor_distance_dispersion']['coefficient_of_variation']['value']
                for r in eligible if r['neighborhoods']['full_axis']['mode']==mode and r['neighborhoods']['full_axis']['neighbor_distance_dispersion']['coefficient_of_variation']['status']=='computed')
                for mode in ('complete_source','query_subset')}}
    pairs=[r['representation_agreement']['value'] for r in rows if r['representation_agreement']['status']=='computed']
    stats['representation_pairs']={'n_sources':len(pairs),
        'primary_partition_ari':summarize(p['partitions'][0]['value']['ari_including_noise']['value'] for p in pairs if p['partitions'][0]['status']=='computed' and p['partitions'][0]['value']['ari_including_noise']['status']=='computed'),
        'full_axis_k8_set_overlap':summarize(p['full_axis_neighbors']['metrics'][-1]['set_overlap']['mean'] for p in pairs)}
    families={}
    for family in sorted({e['source_family'] for e in frozen['entries']}):
        names={e['dataset_id'] for e in frozen['entries'] if e['source_family']==family};selected=[r for r in rows if r['dataset_id'] in names]
        families[family]={'n_catalog_entries':len(selected),'n_raw_profiles':sum(r['representations']['raw']['status']=='computed' for r in selected),
            'raw_pc1_fraction':summarize(r['representations']['raw']['value']['pca']['pc1_fraction'] for r in selected if r['representations']['raw']['status']=='computed')}
    physical_groups=defaultdict(list)
    for row in rows:
        if row['population_relationship']['status']=='computed':
            physical_groups[row['population_relationship']['value']['namespace']].append({
                'dataset_id':row['dataset_id'],'representations':row['representations']})
    return {'schema_version':1,'protocol_version':frozen['protocol_version'],'freeze_id':frozen['freeze_id'],'entries':rows,
        'source_hierarchy_ref':ref(ROOT/'source-hierarchy.json'),'paired_contrast_ref':ref(ROOT/'paired-x-comparison.json'),
        'counts':{'catalog_entries':42,'raw':sum(r['representations']['raw']['status']=='computed' for r in rows),
            'snv':sum(r['representations']['snv']['status']=='computed' for r in rows),
            'resampled_sources':sum(r['structural_stability']['status']=='computed' for r in rows),
            'resampling_classifications':dict(Counter(r['structural_stability']['value']['classification'] for r in rows if r['structural_stability']['status']=='computed')),
            'variable_metadata_sources':sum(r['metadata_agreement']['status']=='computed' and r['metadata_agreement']['value'].get('raw',{}).get('n_variable_fields',0)>0 for r in rows)},
        'descriptive_distributions':stats,'family_strata':families,
        'verified_physical_namespace_strata':dict(physical_groups),
        'independent_study_level_distribution':state(reason='INDEPENDENT_STUDIES_AND_UNKNOWN_SOURCE_OVERLAP_NOT_IDENTIFIED; CITATIONS_ARE_NOT_SAMPLING_UNITS',status='not_identifiable'),
        'aggregation_scope':{'entry':'42 records, 39 admissible sources expected; not independent studies.',
            'source_view':'43 declared catalog sources include two simulated ChEMBL modalities; 42 primary source records.',
            'physical_population':'Two original physical-key namespaces directly rechecked; four historical physical-ownership admissions. Independent biological populations are not identified.',
            'study':'Cited-reference groups are provenance, not independently sampled studies; study-level prevalence unavailable.'},
        'test_target_accessed':False,'model_fits':0,'universal_shortcut_score':None}


def main():
    frozen=json.loads((ROOT/'input-freeze.json').read_text());hierarchy=json.loads((ROOT/'source-hierarchy.json').read_text())
    files=[*sorted((ROOT/'profiles').glob('*.json')),*sorted((ROOT/'stability').glob('*.json')),ROOT/'paired-x-comparison.json',ROOT/'source-hierarchy.json']
    contract={'task':{'task_id':fingerprint(['alpha12','public-unsupervised-matrix'])},'phase':'matrix-consolidation',
        'freeze_id':frozen['freeze_id'],'input_hashes':{p.as_posix():digest(p) for p in files},'writer_sha256':digest(__file__),
        'bridge_sha256':digest('bridges/python/nirs4all_domains/unsupervised.py')}
    policy=json.loads(Path('configs/bank/storage-policy-alpha12.json').read_text())
    store=StageStore('results/alpha9-perten-keyed/state',AUDIT/'scratch',AUDIT/'evidence',Path.cwd(),policy)
    plan={'inputs':[],'scratch_bytes':4096,'evidence_bytes':3145728,'expected_fits':0,'expected_permutations':0,
        'uncertainty':'No-refit native summaries/ARI over immutable reference/draw records; compact 42-entry matrix with links, no spectra or PCA scores.'}
    receipt,value=store.run(contract,'P4',plan,lambda folder:build(frozen,hierarchy))
    if value is None:raise RuntimeError(receipt)
    export(store,receipt,ROOT/'structural-matrix.json');atomic_json(AUDIT/'matrix-receipt.json',receipt)
    print(json.dumps(value['counts']))


if __name__=='__main__':main()
