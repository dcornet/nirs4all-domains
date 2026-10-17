"""Portable finite/schema/identity/evidence checks, plus available local preservation."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

from nirs4all_domains.adaptive import partition_agreement
from nirs4all_domains.bank import schema_check
from nirs4all_domains.registry import verify_storage
from nirs4all_domains.storage import digest,fingerprint

ROOT=Path('docs/benchmarks/alpha12')
STATES={'computed','exploratory','insufficient_information','not_identifiable','unavailable','ineligible','failed','inconclusive'}


def finite(value):
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('NONFINITE_STRUCTURAL_VALUE')
    if isinstance(value,dict):
        if {'status','reason','value'}<=set(value):
            assert value['status'] in STATES
            if value['status'] in ('computed','exploratory'):
                assert value['value'] is not None and value['reason'] is None
            else:assert value['value'] is None and bool(value['reason'])
        for key,item in value.items():
            assert key not in {'spectra','transport_only_scores','loadings','Y_test','y_test','Y','y'}
            if key in ('target_accessed','test_target_accessed','target_cells_materialized','model_performance_used','selection_uses_model_performance'):assert item is False
            finite(item)
    elif isinstance(value,list):
        for item in value:finite(item)


def profile_check(value,n,p):
    assert value['n_observations']==n and value['n_bands']==p
    assert value['provider']['version']=='1.3.6+abi.2.19.0' and value['provider']['abi']=='2.19.0'
    assert not value['test_target_accessed']
    assert value['predictive_dependence']['status']=='unavailable'
    assert value['pca']['full_trace']>0 and 0<value['pca']['retained_variance_fraction']<=1+1e-8
    assert len(value['pca']['eigenvalues'])<=min(20,n-1,p)
    if value['effective_dimension']['status']=='computed':
        assert 1-1e-8<=value['effective_dimension']['value']<=min(n-1,p)+1e-8
    for size,setting in zip((8,12),value['cluster_settings'],strict=True):
        if setting['status']!='computed':continue
        s=setting['value'];labels=s['labels'];assert len(labels)==n
        assert s['min_cluster_size']==size and s['min_samples']==4
        assert all(isinstance(v,int) and v>=-1 for v in labels)
        assert s['n_clusters']==len({v for v in labels if v>=0})
        assert abs(s['noise_fraction']-labels.count(-1)/n)<1e-14
    for space,neighbors in value['neighborhoods']['value'].items():
        q=neighbors['n_query'];k=neighbors['k'];assert neighbors['n_reference']==n and k==min(8,n-1)
        assert q==len(neighbors['query_ids'])==len(set(neighbors['query_ids']))
        assert neighbors['mode']==('complete_source' if q==n else 'query_subset')
        assert neighbors['reference_population_preserved'] and not neighbors['approximate']
        width=p if space=='full_axis' else len(value['pca']['eigenvalues'])
        assert neighbors['distance_products']==q*n*width<=750000000
        assert len(neighbors['distances'])==len(neighbors['reference_indices'])==len(neighbors['query_indices'])==q
        for source_index,indices,distances in zip(neighbors['query_indices'],neighbors['reference_indices'],neighbors['distances'],strict=True):
            assert len(indices)==len(distances)==k and source_index not in indices
            assert len(set(indices))==k and all(0<=i<n for i in indices)
            assert all(d>=0 and math.isfinite(d) for d in distances)
            assert list(zip(distances,indices))==sorted(zip(distances,indices))
        assert len(neighbors['relative_proximity'])==7
        assert all(0<=r['n_query_with_neighbor']<=q and r['n_query']==q and r['fraction']==r['n_query_with_neighbor']/q for r in neighbors['relative_proximity'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--require-manifest',action='store_true');args=parser.parse_args()
    frozen=json.loads((ROOT/'input-freeze.json').read_text());assert frozen['freeze_id']==fingerprint({k:v for k,v in frozen.items() if k!='freeze_id'})
    matrix=json.loads((ROOT/'structural-matrix.json').read_text());assert matrix['freeze_id']==frozen['freeze_id']
    by_id={r['dataset_id']:r for r in frozen['entries']};assert len(by_id)==42
    assert len(matrix['entries'])==42 and {r['dataset_id'] for r in matrix['entries']}==set(by_id)
    modes=Counter();raw=0;snv=0;stability=0
    for row in matrix['entries']:
        schema_check(row,'unsupervised-evidence');assert row['record_id']==fingerprint({k:v for k,v in row.items() if k!='record_id'})
        frozen_row=by_id[row['dataset_id']];assert row['catalog_content']==frozen_row['catalog_content']
        assert digest(row['baseline_ref']['path'])==row['baseline_ref']['sha256']
        profiles={}
        for representation,state in row['representations'].items():
            if state['status']!='computed':continue
            path=state['value']['profile_ref'];assert digest(path['path'])==path['sha256']
            value=json.loads(Path(path['path']).read_text())
            assert value['status']=='computed';value=value['value'];profiles[representation]=value
            n,p=frozen_row['source_dimensions']['n_observations'],frozen_row['source_dimensions']['n_variables'];profile_check(value,n,p)
            assert value['query_design']==frozen_row['query_design']
            assert value['input_source_sha256']==frozen_row['input_csv_sha256']
            if representation=='raw':raw+=1;modes[value['query_design']['mode']]+=1
            else:snv+=1
        if len(profiles)==2:
            a,b=profiles['raw'],profiles['snv'];assert a['observation_ids_sha256']==b['observation_ids_sha256'] and a['axis_sha256']==b['axis_sha256']
            for index,agreement in enumerate(row['representation_agreement']['value']['partitions']):
                if agreement['status']=='computed' and agreement['value']['ari_including_noise']['status']=='computed':
                    expected=agreement['value']['ari_including_noise']['value']
                    actual=partition_agreement(a['cluster_settings'][index]['value']['labels'],b['cluster_settings'][index]['value']['labels'])
                    assert actual['status']=='computed' and abs(actual['value']-expected)<=1e-12
        if row['structural_stability']['status']=='computed':
            stability+=1;value=row['structural_stability']['value'];assert value['pca_refits']==80 and value['hdbscan_attempts']==160
            assert not value['biological_sampling_uncertainty']
            for reference in value['summary_refs']:
                assert digest(reference['path'])==reference['sha256'];report=json.loads(Path(reference['path']).read_text())
                assert report['n_reference_observations']==frozen_row['source_dimensions']['n_observations']
                for setting in report['settings']:
                    if setting['status']!='computed':continue
                    s=setting['value'];assert s['attempted_draws']==20 and len(s['draws'])==20
                    assert {d['draw'] for d in s['draws']}==set(range(20))
                    for kind,pairs in s['pair_panel'].items():
                        assert kind in ('within','between') and len(pairs)<=128
                        assert all(0<=d['same_nonnoise_cluster']<=d['exposures']<=20 for d in pairs)
    assert (raw,snv,stability)==(39,39,7)
    assert modes==Counter({'complete_source':22,'query_subset':17})
    assert matrix['counts']['raw']==raw and matrix['counts']['snv']==snv and matrix['counts']['resampled_sources']==stability
    paired=json.loads((ROOT/'paired-x-comparison.json').read_text());assert paired['key_proof']['n_matched']==321
    assert paired['key_proof']['parent_observation_counts']==[322,321] and paired['key_proof']['left_only']==['GEN_1_BEPA_7']
    assert paired['model_fits']==0 and not paired['target_cells_materialized']
    controlled=json.loads((ROOT/'controlled-mechanisms.json').read_text());assert controlled['n_mechanisms']==16 and len(controlled['cases'])==18
    assert controlled['pca_fits']==57 and controlled['hdbscan_attempts']==114
    assert digest('docs/ALPHA12_UNSUPERVISED_PROTOCOL.md')==frozen['protocol_sha256']
    assert digest('docs/ALPHA12_HYPOTHESIS_REGISTER.md')==frozen['hypotheses_sha256']
    execution=ROOT/'execution-contracts.json'
    if args.require_manifest:assert execution.exists()
    if execution.exists():
        proof=json.loads(execution.read_text())
        assert all(digest(p)==h for p,h in proof['source_hashes'].items())
        assert (proof['real_pca_fits'],proof['real_hdbscan_attempts'],proof['real_supervised_model_fits'])==(642,1284,0)
        assert (proof['controlled_pca_fits'],proof['controlled_hdbscan_attempts'])==(57,114)
        contracts=proof['records'];assert len({r['execution_id'] for r in contracts})==len(contracts)
        phases=Counter(r['phase'] for r in contracts)
        assert phases['representation-reference']==78 and phases['structural-resampling']==160
        assert phases['structural-resampling-batch']==20 and phases['paired-x-view']==4
        assert all(r['contract']['bridge_sha256']==digest('bridges/python/nirs4all_domains/unsupervised.py') for r in contracts)
        assert json.loads((ROOT/'findings.json').read_text())['matrix_sha256']==digest(ROOT/'structural-matrix.json')
    verified=0;protected=json.loads(Path('docs/audit/alpha12-frozen-output-hashes.json').read_text());assert len(protected)==371
    portable=json.loads(Path('docs/audit/alpha12-portable-preservation.json').read_text())
    assert portable['baseline_commit']==frozen['baseline']
    for path,expected in protected.items():
        if Path(path).exists():
            actual=digest(path)
            if actual!=expected:
                variant=portable['newline_only_variants'][path]
                assert variant['local_snapshot_sha256']==expected and actual==variant['repository_blob_sha256']
            verified+=1
        elif not path.startswith('results/'):raise ValueError('MISSING_PROTECTED_PORTABLE_ARTIFACT:'+path)
    for path in ROOT.rglob('*.json'):
        data=path.read_text(encoding='utf-8');finite(json.loads(data))
        assert not re.search(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]',data),path
    manifest=ROOT/'storage.json'
    if args.require_manifest:assert manifest.exists()
    if manifest.exists():
        stored=json.loads(manifest.read_text());schema_check(stored,'storage-manifest');verify_storage(stored,ROOT)
    print(json.dumps({'public_entries':42,'raw':raw,'snv':snv,'exact_complete_source_neighbors':modes['complete_source'],
        'query_subset_neighbors':modes['query_subset'],'resampled_sources':stability,'protected_present_verified':verified,
        'full_local_preservation_map':len(protected),'native_reported_ari_verified':True,'manifest_verified':manifest.exists()}))


if __name__=='__main__':main()
