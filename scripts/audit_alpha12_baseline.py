"""Read-only retrospective science audit; writes only new alpha.12 evidence."""
import json
from collections import Counter
from pathlib import Path
import subprocess

from nirs4all_domains.predictive import native_summary
from nirs4all_domains.storage import atomic_json, digest

ROOT = Path('docs/benchmarks/alpha12')


def summarize(values):
    values = list(values)
    return native_summary(values) if values else None


def main():
    baseline = 'e8385bf4aa3125d6f6ffadd5e63d080d14a02b44'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == baseline
    protected = json.loads(Path('docs/audit/alpha11-frozen-output-hashes.json').read_text())
    assert len(protected) == 224
    assert all(digest(p) == h for p, h in protected.items())
    tracked = subprocess.check_output(['git', 'ls-files', 'docs/benchmarks/alpha11', 'docs/audit', 'docs/ALPHA11*'], text=True).splitlines()
    protected.update({p: digest(p) for p in tracked})
    atomic_json('docs/audit/alpha12-frozen-output-hashes.json', protected)
    coverage = json.loads(Path('docs/benchmarks/alpha11/public-coverage.json').read_text())
    rows = []
    for entry in coverage['entries']:
        path = Path(entry['profile_ref']['path'])
        assert digest(path) == entry['profile_ref']['sha256']
        original = json.loads(path.read_text())
        if entry['dataset_id'].startswith('ecosis_tabletop'):
            profile = original['report']
        else:
            profile = original['structural_susceptibility']
        row = {'dataset_id': entry['dataset_id'], 'source_id': entry['source_id'],
               'source_dimensions': entry['source_dimensions'], 'identity': entry['identity_evidence'],
               'physical_evidence': entry.get('independent_unit_evidence'),
               'baseline_profile_ref': entry['profile_ref'], 'status': entry['levels']['X0']['status'],
               'reason': entry['levels']['X0']['reason']}
        if profile:
            n, p = profile['n_observations'], profile['n_bands']
            spectra = profile['x_structure']['value']
            settings = []
            for result in profile['cluster_settings']:
                if result['status'] != 'computed':
                    settings.append(result)
                    continue
                c = result['value']; support = Counter(v for v in c['labels'] if v >= 0)
                settings.append({'status': 'computed', 'min_cluster_size': c['min_cluster_size'],
                    'n_clusters': c['n_clusters'], 'noise_fraction': c['noise_fraction'],
                    'cluster_observation_counts': sorted(support.values(), reverse=True),
                    'clusters_below_one_percent_population': sum(v < .01*n for v in support.values()),
                    'clusters_per_100_observations': 100*len(support)/n,
                    'membership_summary': c['membership_summary']})
            row.update(n=n, p=p, raw_neighbor_products=n*n*p,
                query_128_products=min(128,n)*n*p,
                pca_retained_fraction=spectra['retained_variance_fraction'],
                omitted_variance_fraction=1-spectra['retained_variance_fraction'],
                effective_dimension=profile['effective_dimension'],
                full_trace_original_units=spectra['full_trace'], settings=settings,
                parameter_ari=profile['parameter_ari_including_noise'],
                raw_neighbors=profile['near_duplicate_proximity']['status'])
        rows.append(row)
    valid = [r for r in rows if r['status'] == 'computed']
    strata = []
    for lo, hi in [(0,250),(250,500),(500,1000),(1000,2000),(2000,1000000)]:
        selected = [r for r in valid if lo <= r['n'] < hi]
        strata.append({'n_range_left_closed': [lo,hi], 'catalog_entries':len(selected),
            'cluster_count':summarize(r['settings'][0]['n_clusters'] for r in selected),
            'clusters_per_100_observations':summarize(r['settings'][0]['clusters_per_100_observations'] for r in selected),
            'noise_fraction':summarize(r['settings'][0]['noise_fraction'] for r in selected)})
    result = {'protocol':'domains.alpha12.retrospective.v0.1', 'baseline_commit':baseline,
        'coverage_sha256':digest('docs/benchmarks/alpha11/public-coverage.json'),
        'n_catalog_entries':42, 'n_computed':len(valid), 'n_protected':len(protected),
        'entries':rows, 'sample_count_strata':strata,
        'parameter_ari':summarize(r['parameter_ari']['value'] for r in valid if r['parameter_ari']['status']=='computed'),
        'retained_variance_fraction':summarize(r['pca_retained_fraction'] for r in valid),
        'effective_dimension_available':sum(r['effective_dimension']['status']=='computed' for r in valid),
        'raw_exact_product_eligibility':{str(bound):sum(r['raw_neighbor_products']<=bound for r in valid)
            for bound in [250000000,500000000,750000000,1000000000]},
        'noise_over_40_percent':sum(r['settings'][0]['noise_fraction']>.4 for r in valid),
        'noise_over_80_percent':sum(r['settings'][0]['noise_fraction']>.8 for r in valid),
        'axis_unit_counts':dict(Counter(r['source_dimensions']['axis_unit'] for r in rows)),
        'identity_counts':dict(Counter(r['identity'] for r in rows)),
        'target_accessed':False,'model_fits':0,'pca_fits':0,
        'limitations':['Strata describe associations with N, not a causal sample-size effect.',
            'Parameter agreement is not sampling stability; no native fit is repeated.',
            'Summary-only distances cannot identify omitted-axis distances for matched neighbors.',
            'Trace and distances in different physical units are not pooled or ranked.',
            'Entry counts do not establish distinct physical populations; overlap remains separately audited.']}
    atomic_json(ROOT/'retrospective.json', result)
    print(json.dumps({k:result[k] for k in ['n_computed','n_protected','parameter_ari','retained_variance_fraction','raw_exact_product_eligibility','noise_over_40_percent','noise_over_80_percent']}))


if __name__ == '__main__':
    main()
